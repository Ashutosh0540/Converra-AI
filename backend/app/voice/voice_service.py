from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, List, Optional
from uuid import UUID, uuid4

from loguru import logger

from app.models.conversation import Conversation
from app.models.enums import AgentType, ConversationStatus, WorkflowStage
from app.models.user import User
from app.models.voice import VoiceSession, VoiceTranscript
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.voice_repository import VoiceRepository
from app.schemas.ai import AIResponse, OrchestrationRequest
from app.schemas.voice import (
    VoiceHistoryResponse,
    VoiceSessionEndResponse,
    VoiceSessionListItem,
    VoiceSessionStartResponse,
)
from app.services.orchestration_service import AgentOrchestratorService
from app.voice.speech_to_text import SpeechToTextService, TranscriptionResult
from app.voice.text_to_speech import SpeechChunk, TextToSpeechService
from app.voice.voice_manager import VoiceManager
from app.voice.voice_session import VoiceSessionContext


@dataclass
class VoiceTurnResult:
    transcript: str
    transcription: TranscriptionResult
    ai_response: AIResponse
    audio_chunks: List[bytes]
    transcription_latency_ms: float
    llm_latency_ms: float
    tts_latency_ms: float
    total_latency_ms: float


class VoiceServiceError(Exception):
    """Raised when voice processing fails."""


class VoiceSessionNotFound(VoiceServiceError):
    """Raised when a voice session cannot be found."""


class VoiceService:
    def __init__(
        self,
        voice_repository: VoiceRepository,
        conversation_repository: ConversationRepository,
        orchestrator: AgentOrchestratorService,
        speech_to_text: Optional[SpeechToTextService] = None,
        text_to_speech: Optional[TextToSpeechService] = None,
        manager: Optional[VoiceManager] = None,
    ) -> None:
        self.voice_repository = voice_repository
        self.conversation_repository = conversation_repository
        self.orchestrator = orchestrator
        self.speech_to_text = speech_to_text or SpeechToTextService()
        self.text_to_speech = text_to_speech or TextToSpeechService()
        self.manager = manager or VoiceManager()

    async def start_session(
        self,
        current_user: User,
        conversation_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
    ) -> VoiceSessionStartResponse:
        if session_id is not None:
            session = self.voice_repository.get_session(session_id)
            if (
                session is not None
                and session.organization_id == current_user.organization_id
            ):
                await self._register_runtime_state(session)
                return self._session_response(session)

        conversation = self._resolve_conversation(current_user, conversation_id)
        session = VoiceSession(
            id=uuid4(),
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            active_user_id=current_user.id,
            conversation_id=conversation.id,
            active_agent=conversation.active_agent,
            workflow_stage=conversation.workflow_stage,
            status=conversation.status,
            transcript=[],
            memory_snapshot=list(conversation.memory),
            current_transcript="",
            is_active=True,
            connection_count=1,
            last_seen_at=datetime.now(timezone.utc),
        )
        persisted = self.voice_repository.create_session(session)
        await self._register_runtime_state(persisted)
        logger.info("Voice session {} started", persisted.id)
        return self._session_response(persisted)

    async def end_session(
        self,
        current_user: User,
        session_id: UUID,
    ) -> VoiceSessionEndResponse:
        session = self._get_session_or_raise(session_id, current_user.organization_id)
        session.status = ConversationStatus.CLOSED
        session.workflow_stage = WorkflowStage.CLOSED
        session.is_active = False
        ended = self.voice_repository.close_session(session)
        conversation = self.conversation_repository.get_by_id(ended.conversation_id)
        if (
            conversation is not None
            and conversation.status != ConversationStatus.CLOSED
        ):
            conversation = self.orchestrator.close_conversation(conversation)

        await self.manager.remove(session_id)
        self.speech_to_text.reset_buffer(session_id)
        logger.info("Voice session {} ended", ended.id)
        return VoiceSessionEndResponse(
            session_id=ended.id,
            conversation_id=ended.conversation_id,
            status=ended.status,
            ended_at=ended.ended_at or datetime.now(timezone.utc),
        )

    async def history(
        self,
        current_user: User,
        session_id: UUID,
    ) -> VoiceHistoryResponse:
        session = self._get_session_or_raise(session_id, current_user.organization_id)
        transcripts = self.voice_repository.list_transcripts(session.id)
        return VoiceHistoryResponse(
            session_id=session.id,
            conversation_id=session.conversation_id,
            transcript=transcripts,
        )

    async def list_sessions(self, current_user: User) -> List[VoiceSessionListItem]:
        sessions = self.voice_repository.list_sessions(current_user.organization_id)
        return [VoiceSessionListItem.model_validate(session) for session in sessions]

    async def process_voice_input(
        self,
        current_user: User,
        session_id: UUID,
        audio_base64: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        text: Optional[str] = None,
        is_final: bool = False,
        close_conversation: bool = False,
    ) -> VoiceTurnResult:
        session = self._get_session_or_raise(session_id, current_user.organization_id)
        state = await self._register_runtime_state(session)
        await self.manager.cancel_reply(session.id)
        conversation = self.conversation_repository.get_by_id(session.conversation_id)

        transcription_started = datetime.now(timezone.utc)
        transcription = await self.speech_to_text.transcribe_chunk(
            session_id=session.id,
            audio_base64=audio_base64,
            audio_bytes=audio_bytes,
            text=text,
            is_final=is_final,
        )
        transcription_latency_ms = self._elapsed_ms(transcription_started)

        session.current_transcript = transcription.text
        session.last_seen_at = datetime.now(timezone.utc)
        session.connection_count = max(1, session.connection_count)
        self._append_transcript(
            session=session,
            role="user",
            content=transcription.text,
            partial=not transcription.is_final,
            agent=session.active_agent.value if session.active_agent else None,
        )
        self.voice_repository.update_session(session)

        state.session.current_agent = session.active_agent
        state.session.workflow_stage = session.workflow_stage
        state.session.transcript = list(session.transcript)
        state.session.memory = list(session.memory_snapshot)

        if conversation is not None and conversation.human_mode:
            ai_response = AIResponse(
                conversation_id=session.conversation_id,
                agent=AgentType.ESCALATION,
                status=ConversationStatus.ESCALATED,
                workflow_stage=WorkflowStage.ESCALATED,
                message="This conversation is being handled by a human operator.",
                confidence=0.0,
                citations=[],
                retrieved_sources=[],
                guardrail_result={
                    "allowed": True,
                    "reason": "Conversation is in human mode.",
                },
                escalation_decision=conversation.escalation_state or {},
                structured_data={"human_mode": True},
                escalation_state=conversation.escalation_state or {},
            )
            return VoiceTurnResult(
                transcript=transcription.text,
                transcription=transcription,
                ai_response=ai_response,
                audio_chunks=[],
                transcription_latency_ms=transcription_latency_ms,
                llm_latency_ms=0.0,
                tts_latency_ms=0.0,
                total_latency_ms=transcription_latency_ms,
            )

        if not transcription.is_final:
            return VoiceTurnResult(
                transcript=transcription.text,
                transcription=transcription,
                ai_response=AIResponse(
                    conversation_id=session.conversation_id,
                    agent=session.active_agent or AgentType.FAQ,
                    status=session.status,
                    workflow_stage=session.workflow_stage,
                    message=transcription.text,
                    confidence=transcription.confidence,
                    citations=[],
                    structured_data={},
                    escalation_state={},
                ),
                audio_chunks=[],
                transcription_latency_ms=transcription_latency_ms,
                llm_latency_ms=0.0,
                tts_latency_ms=0.0,
                total_latency_ms=transcription_latency_ms,
            )

        llm_started = datetime.now(timezone.utc)
        response = await self.orchestrator.process_message(
            current_user,
            OrchestrationRequest(
                conversation_id=session.conversation_id,
                message=transcription.text,
                close_conversation=close_conversation,
                source_channel="voice",
            ),
        )
        llm_latency_ms = self._elapsed_ms(llm_started)

        self._append_transcript(
            session=session,
            role="assistant",
            content=response.message,
            partial=False,
            agent=response.agent.value,
        )
        conversation = self.conversation_repository.get_by_id(session.conversation_id)
        if conversation is not None:
            session.memory_snapshot = list(conversation.memory)
            session.active_agent = response.agent
            session.workflow_stage = response.workflow_stage
            session.status = response.status
            session.current_transcript = response.message
        self.voice_repository.update_session(session)

        tts_started = datetime.now(timezone.utc)
        audio_chunks: List[bytes] = []
        async for speech_chunk in self.text_to_speech.synthesize_stream(
            response.message
        ):
            audio_chunks.append(speech_chunk.audio_bytes)
        tts_latency_ms = self._elapsed_ms(tts_started)

        total_latency_ms = self._elapsed_ms(transcription_started)
        logger.info(
            "Voice turn completed for session {} in {} ms",
            session.id,
            round(total_latency_ms, 2),
        )
        return VoiceTurnResult(
            transcript=transcription.text,
            transcription=transcription,
            ai_response=response,
            audio_chunks=audio_chunks,
            transcription_latency_ms=transcription_latency_ms,
            llm_latency_ms=llm_latency_ms,
            tts_latency_ms=tts_latency_ms,
            total_latency_ms=total_latency_ms,
        )

    async def stream_tts(self, text: str) -> AsyncGenerator[SpeechChunk, None]:
        async for chunk in self.text_to_speech.synthesize_stream(text):
            yield chunk

    async def get_runtime_state(
        self,
        session_id: UUID,
    ) -> Optional[Any]:
        return await self.manager.get(session_id)

    def _resolve_conversation(
        self,
        current_user: User,
        conversation_id: Optional[UUID],
    ) -> Conversation:
        if conversation_id is not None:
            conversation = self.conversation_repository.get_by_id(conversation_id)
            if (
                conversation is None
                or conversation.organization_id != current_user.organization_id
            ):
                raise VoiceSessionNotFound(
                    f"Conversation '{conversation_id}' was not found."
                )
            return conversation

        return self.orchestrator.start_conversation(current_user)

    def _get_session_or_raise(
        self,
        session_id: UUID,
        organization_id: UUID,
    ) -> VoiceSession:
        session = self.voice_repository.get_session(session_id)
        if session is None or session.organization_id != organization_id:
            raise VoiceSessionNotFound(f"Voice session '{session_id}' was not found.")
        return session

    async def _register_runtime_state(self, session: VoiceSession):
        state = VoiceSessionContext(
            session_id=session.id,
            conversation_id=session.conversation_id,
            organization_id=session.organization_id,
            active_user_id=session.active_user_id,
            current_agent=session.active_agent,
            workflow_stage=session.workflow_stage,
            transcript=list(session.transcript),
            memory=list(session.memory_snapshot),
            active=session.is_active,
        )
        return await self.manager.register(state)

    def _session_response(self, session: VoiceSession) -> VoiceSessionStartResponse:
        return VoiceSessionStartResponse(
            session_id=session.id,
            conversation_id=session.conversation_id,
            websocket_url=f"/ws/voice?session_id={session.id}",
            status=session.status,
            active_agent=session.active_agent,
            workflow_stage=session.workflow_stage,
        )

    def _append_transcript(
        self,
        session: VoiceSession,
        role: str,
        content: str,
        partial: bool,
        agent: Optional[str],
    ) -> None:
        transcript_entry = VoiceTranscript(
            session_id=session.id,
            organization_id=session.organization_id,
            user_id=session.active_user_id,
            role=role,
            content=content,
            partial=partial,
            agent=agent,
            extra_metadata={
                "conversation_id": str(session.conversation_id),
                "workflow_stage": session.workflow_stage.value,
            },
        )
        session.transcript = list(session.transcript)
        session.transcript.append(
            {
                "role": role,
                "content": content,
                "partial": partial,
                "agent": agent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.voice_repository.add_transcript(transcript_entry)

    @staticmethod
    def _elapsed_ms(started_at: datetime) -> float:
        return round(
            (datetime.now(timezone.utc) - started_at).total_seconds() * 1000.0,
            2,
        )
