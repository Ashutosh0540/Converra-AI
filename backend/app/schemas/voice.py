from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AgentType, ConversationStatus, WorkflowStage


class VoiceSessionStartRequest(BaseModel):
    session_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None


class VoiceSessionStartResponse(BaseModel):
    session_id: UUID
    conversation_id: UUID
    websocket_url: str
    status: ConversationStatus
    active_agent: Optional[AgentType] = None
    workflow_stage: WorkflowStage


class VoiceSessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    active_agent: Optional[AgentType] = None
    workflow_stage: WorkflowStage
    status: ConversationStatus
    is_active: bool
    connection_count: int
    last_seen_at: Optional[datetime] = None
    created_at: datetime


class VoiceSessionEndRequest(BaseModel):
    session_id: UUID


class VoiceSessionEndResponse(BaseModel):
    session_id: UUID
    conversation_id: UUID
    status: ConversationStatus
    ended_at: datetime


class VoiceTranscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    content: str
    partial: bool
    agent: Optional[str] = None
    extra_metadata: Dict[str, Any]
    created_at: datetime


class VoiceHistoryResponse(BaseModel):
    session_id: UUID
    conversation_id: UUID
    transcript: List[VoiceTranscriptResponse]


class VoiceWebSocketMessage(BaseModel):
    type: str = Field(min_length=1)
    session_id: Optional[UUID] = None
    audio_base64: Optional[str] = None
    text: Optional[str] = None
    is_final: bool = False
    close_conversation: bool = False


class VoiceWebSocketEvent(BaseModel):
    type: str
    session_id: UUID
    payload: Dict[str, Any] = Field(default_factory=dict)
