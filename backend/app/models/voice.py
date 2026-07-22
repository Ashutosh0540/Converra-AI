from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base_model import BaseModel
from app.models.enums import AgentType, ConversationStatus, WorkflowStage


class VoiceSession(BaseModel):
    __tablename__ = "voice_sessions"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active_agent: Mapped[Optional[AgentType]] = mapped_column(
        SAEnum(AgentType, name="voice_agent_type"),
        nullable=True,
    )
    workflow_stage: Mapped[WorkflowStage] = mapped_column(
        SAEnum(WorkflowStage, name="voice_workflow_stage"),
        nullable=False,
        default=WorkflowStage.ROUTING,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus, name="voice_session_status"),
        nullable=False,
        default=ConversationStatus.ACTIVE,
    )
    transcript: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    memory_snapshot: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )
    current_transcript: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class VoiceTranscript(BaseModel):
    __tablename__ = "voice_transcripts"

    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("voice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    partial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    agent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
