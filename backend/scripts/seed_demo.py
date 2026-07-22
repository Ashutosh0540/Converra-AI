"""Create idempotent local demo records; run from the backend directory."""

from __future__ import annotations

from datetime import datetime, timezone

from app.auth.security import hash_password
from app.database.session import SessionLocal
from app.models.conversation import Conversation
from app.models.enums import (
    AgentType,
    ConversationStatus,
    DocumentStatus,
    UserRole,
    WorkflowStage,
)
from app.models.knowledge_document import KnowledgeDocument
from app.models.organization import Organization
from app.models.user import User
from app.models.voice import VoiceSession


def main() -> None:
    db = SessionLocal()
    try:
        organization = db.query(Organization).filter_by(name="Converra Demo").first()
        if organization is None:
            organization = Organization(
                name="Converra Demo",
                industry="Technology",
                subscription_plan="enterprise",
            )
            db.add(organization)
            db.flush()

        user = db.query(User).filter_by(email="admin@demo.converra.ai").first()
        if user is None:
            user = User(
                organization_id=organization.id,
                full_name="Demo Administrator",
                email="admin@demo.converra.ai",
                password_hash=hash_password("ChangeMe!123"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)
            db.flush()

        conversation = (
            db.query(Conversation).filter_by(organization_id=organization.id).first()
        )
        if conversation is None:
            conversation = Conversation(
                organization_id=organization.id,
                user_id=user.id,
                active_agent=AgentType.FAQ,
                status=ConversationStatus.ACTIVE,
                workflow_stage=WorkflowStage.VALIDATION,
                memory=[
                    {
                        "role": "user",
                        "content": "How does Converra protect customer data?",
                    },
                    {
                        "role": "assistant",
                        "content": "I can retrieve the approved security guidance for you.",
                    },
                ],
            )
            db.add(conversation)
            db.flush()

        if (
            db.query(KnowledgeDocument)
            .filter_by(
                organization_id=organization.id, filename="demo-security-overview.md"
            )
            .first()
            is None
        ):
            db.add(
                KnowledgeDocument(
                    organization_id=organization.id,
                    uploader_id=user.id,
                    filename="demo-security-overview.md",
                    content_type="text/markdown",
                    file_size=0,
                    source="demo-seed",
                    status=DocumentStatus.READY,
                    chunk_count=0,
                )
            )

        if (
            db.query(VoiceSession).filter_by(conversation_id=conversation.id).first()
            is None
        ):
            db.add(
                VoiceSession(
                    organization_id=organization.id,
                    user_id=user.id,
                    active_user_id=user.id,
                    conversation_id=conversation.id,
                    active_agent=AgentType.FAQ,
                    workflow_stage=WorkflowStage.VALIDATION,
                    status=ConversationStatus.ACTIVE,
                    transcript=[
                        {
                            "role": "user",
                            "content": "Can you explain the platform?",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ],
                    memory_snapshot=list(conversation.memory),
                    current_transcript="Can you explain the platform?",
                    is_active=True,
                    connection_count=0,
                )
            )
        db.commit()
        print("Demo data created. Login: admin@demo.converra.ai / ChangeMe!123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
