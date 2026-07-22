from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.conversation import Conversation
from app.models.enums import AgentType, ConversationStatus, WorkflowStage
from app.models.organization import Organization
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.voice_repository import VoiceRepository
from app.schemas.ai import AIResponse, OrchestrationRequest
from app.voice.speech_to_text import SpeechToTextService
from app.voice.text_to_speech import TextToSpeechService
from app.voice.voice_service import VoiceService


class FakeOrchestratorService:
    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self.conversation_repository = conversation_repository

    def start_conversation(self, current_user):
        conversation = Conversation(
            id=uuid4(),
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            workflow_stage=WorkflowStage.ROUTING,
            status=ConversationStatus.ACTIVE,
            active_agent=None,
        )
        return self.conversation_repository.create(conversation)

    async def process_message(self, current_user, payload: OrchestrationRequest):
        conversation = self.conversation_repository.get_by_id(payload.conversation_id)
        if conversation is None:
            conversation = self.start_conversation(current_user)

        conversation.memory = list(conversation.memory)
        conversation.memory.append({"role": "user", "content": payload.message})
        conversation.active_agent = AgentType.FAQ
        conversation.workflow_stage = WorkflowStage.EXECUTION
        if payload.close_conversation:
            conversation.status = ConversationStatus.CLOSED
            conversation.workflow_stage = WorkflowStage.CLOSED
        self.conversation_repository.update(conversation)

        return AIResponse(
            conversation_id=conversation.id,
            agent=AgentType.FAQ,
            status=conversation.status,
            workflow_stage=conversation.workflow_stage,
            message=f"Echo: {payload.message}",
            confidence=0.99,
            citations=[],
            structured_data={"echo": payload.message},
            escalation_state={},
        )

    def close_conversation(self, conversation):
        conversation.status = ConversationStatus.CLOSED
        conversation.workflow_stage = WorkflowStage.CLOSED
        return self.conversation_repository.update(conversation)


@pytest.fixture()
def voice_service(db_session):
    return VoiceService(
        voice_repository=VoiceRepository(db_session),
        conversation_repository=ConversationRepository(db_session),
        orchestrator=FakeOrchestratorService(ConversationRepository(db_session)),
        speech_to_text=SpeechToTextService(),
        text_to_speech=TextToSpeechService(),
    )


def test_speech_to_text_buffers_are_session_scoped():
    service = SpeechToTextService()

    import asyncio

    first = asyncio.run(
        service.transcribe_chunk(
            session_id=uuid4(),
            audio_bytes=b"hello ",
            is_final=False,
        )
    )
    second = asyncio.run(
        service.transcribe_chunk(
            session_id=uuid4(),
            audio_bytes=b"world",
            is_final=False,
        )
    )

    assert first.text == "hello"
    assert second.text == "world"


def test_voice_service_creates_session_and_history(db_session, client, voice_service):
    from app.api.dependencies import get_voice_service
    from app.auth.security import hash_password
    from app.models.enums import UserRole
    from app.models.organization import Organization
    from app.models.user import User

    organization = Organization(
        name="Voice Org",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()

    user = User(
        organization_id=organization.id,
        full_name="Voice Admin",
        email="voice-admin@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    def override_voice_service():
        return voice_service

    from app.main import app

    app.dependency_overrides[get_voice_service] = override_voice_service

    login_response = client.post(
        "/api/v1/users/login",
        json={"email": "voice-admin@example.com", "password": "strong-password"},
    )
    token = login_response.json()["access_token"]

    start_response = client.post(
        "/voice/session/start",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["session_id"]

    history_response = client.get(
        "/voice/history",
        headers={"Authorization": f"Bearer {token}"},
        params={"session_id": session_id},
    )
    assert history_response.status_code == 200
    assert history_response.json()["transcript"] == []

    end_response = client.post(
        "/voice/session/end",
        headers={"Authorization": f"Bearer {token}"},
        json={"session_id": session_id},
    )
    assert end_response.status_code == 200
    assert end_response.json()["status"] == "CLOSED"

    app.dependency_overrides.pop(get_voice_service, None)


def test_voice_takeover_preserves_transcript_and_suppresses_ai_audio(
    db_session,
    voice_service,
):
    from app.auth.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User

    organization = Organization(
        name="Voice Takeover Org",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()
    user = User(
        organization_id=organization.id,
        full_name="Voice Operator",
        email="voice-takeover@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    import asyncio

    started = asyncio.run(voice_service.start_session(user))
    conversation = voice_service.conversation_repository.get_by_id(
        started.conversation_id
    )
    assert conversation is not None
    conversation.human_mode = True
    voice_service.conversation_repository.update(conversation)

    result = asyncio.run(
        voice_service.process_voice_input(
            current_user=user,
            session_id=started.session_id,
            text="Can you hear me?",
            is_final=True,
        )
    )

    assert result.ai_response.structured_data["human_mode"] is True
    assert result.audio_chunks == []
    history = asyncio.run(voice_service.history(user, started.session_id))
    assert history.transcript[-1].content == "Can you hear me?"


def test_voice_websocket_streams_response(client, db_session, voice_service):
    from app.api.dependencies import get_voice_service
    from app.auth.security import hash_password
    from app.main import app
    from app.models.enums import UserRole
    from app.models.organization import Organization
    from app.models.user import User

    organization = Organization(
        name="Voice Org",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()

    user = User(
        organization_id=organization.id,
        full_name="Voice Admin",
        email="voice-ws@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    app.dependency_overrides[get_voice_service] = lambda: voice_service

    login_response = client.post(
        "/api/v1/users/login",
        json={"email": "voice-ws@example.com", "password": "strong-password"},
    )
    token = login_response.json()["access_token"]

    with client.websocket_connect(f"/ws/voice?token={token}") as websocket:
        session_started = websocket.receive_json()
        assert session_started["type"] == "session_started"
        session_id = session_started["payload"]["session_id"]

        websocket.send_json(
            {
                "type": "text",
                "session_id": session_id,
                "text": "hello there",
                "is_final": True,
            }
        )

        transcript_event = websocket.receive_json()
        assert transcript_event["type"] == "transcript_final"

        ai_event = websocket.receive_json()
        assert ai_event["type"] == "ai_response"
        assert ai_event["payload"]["response"]["message"] == "Echo: hello there"

        audio_event = websocket.receive_json()
        assert audio_event["type"] == "audio_chunk"
        assert audio_event["payload"]["audio_base64"]

        websocket.send_json({"type": "end", "session_id": session_id})
        while True:
            ended_event = websocket.receive_json()
            if ended_event["type"] == "session_ended":
                break

        assert ended_event["type"] == "session_ended"

    app.dependency_overrides.pop(get_voice_service, None)
