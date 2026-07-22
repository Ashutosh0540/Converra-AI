from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.escalation_repository import EscalationRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.repositories.voice_repository import VoiceRepository
from app.services.escalation_service import EscalationService
from app.services.knowledge_service import KnowledgeService
from app.services.orchestration_service import AgentOrchestratorService
from app.services.user_service import UserService
from app.voice.voice_manager import VoiceManager
from app.voice.voice_service import VoiceService


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repository(
    db: Annotated[Session, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)


def get_refresh_token_repository(
    db: Annotated[Session, Depends(get_db)],
) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_repository: Annotated[
        RefreshTokenRepository,
        Depends(get_refresh_token_repository),
    ],
) -> UserService:
    return UserService(user_repository, refresh_token_repository)


def get_knowledge_repository(
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeRepository:
    return KnowledgeRepository(db)


def get_knowledge_service(
    repository: Annotated[
        KnowledgeRepository,
        Depends(get_knowledge_repository),
    ],
) -> KnowledgeService:
    return KnowledgeService(repository)


def get_conversation_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ConversationRepository:
    return ConversationRepository(db)


def get_escalation_repository(
    db: Annotated[Session, Depends(get_db)],
) -> EscalationRepository:
    return EscalationRepository(db)


def get_escalation_service(
    escalation_repository: Annotated[
        EscalationRepository,
        Depends(get_escalation_repository),
    ],
    conversation_repository: Annotated[
        ConversationRepository,
        Depends(get_conversation_repository),
    ],
    user_repository: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
    knowledge_service: Annotated[
        KnowledgeService,
        Depends(get_knowledge_service),
    ],
) -> EscalationService:
    return EscalationService(
        escalation_repository=escalation_repository,
        conversation_repository=conversation_repository,
        user_repository=user_repository,
        knowledge_service=knowledge_service,
    )


def get_orchestrator_service(
    conversation_repository: Annotated[
        ConversationRepository,
        Depends(get_conversation_repository),
    ],
    knowledge_service: Annotated[
        KnowledgeService,
        Depends(get_knowledge_service),
    ],
    escalation_service: Annotated[
        EscalationService,
        Depends(get_escalation_service),
    ],
) -> AgentOrchestratorService:
    return AgentOrchestratorService(
        conversation_repository,
        knowledge_service,
        escalation_service=escalation_service,
    )


def get_voice_repository(
    db: Annotated[Session, Depends(get_db)],
) -> VoiceRepository:
    return VoiceRepository(db)


@lru_cache
def get_voice_manager() -> VoiceManager:
    return VoiceManager()


def get_voice_service(
    voice_repository: Annotated[
        VoiceRepository,
        Depends(get_voice_repository),
    ],
    conversation_repository: Annotated[
        ConversationRepository,
        Depends(get_conversation_repository),
    ],
    orchestrator_service: Annotated[
        AgentOrchestratorService,
        Depends(get_orchestrator_service),
    ],
    voice_manager: Annotated[VoiceManager, Depends(get_voice_manager)],
) -> VoiceService:
    return VoiceService(
        voice_repository=voice_repository,
        conversation_repository=conversation_repository,
        orchestrator=orchestrator_service,
        manager=voice_manager,
    )
