from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base_model import BaseModel
from app.models.enums import AgentType, ConversationStatus, WorkflowStage


class Conversation(BaseModel):
    __tablename__ = "conversations"

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
    workflow_stage: Mapped[WorkflowStage] = mapped_column(
        SAEnum(WorkflowStage, name="workflow_stage"),
        nullable=False,
        default=WorkflowStage.ROUTING,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus, name="conversation_status"),
        nullable=False,
        default=ConversationStatus.ACTIVE,
    )
    active_agent: Mapped[Optional[AgentType]] = mapped_column(
        SAEnum(AgentType, name="agent_type"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    memory: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    retrieved_documents: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    lead_information: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    booking_request: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    escalation_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    failure_count: Mapped[int] = mapped_column(nullable=False, default=0)
    human_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    human_assignee_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    human_mode_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ConversationSummary(BaseModel):
    __tablename__ = "conversation_summaries"

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
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
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
