from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base_model import BaseModel
from app.models.enums import EscalationActionType, EscalationPriority, EscalationStatus


class EscalationCase(BaseModel):
    __tablename__ = "escalation_cases"

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
    customer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_agent_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    escalation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority: Mapped[EscalationPriority] = mapped_column(
        SAEnum(EscalationPriority, name="escalation_priority"),
        nullable=False,
        default=EscalationPriority.MEDIUM,
    )
    status: Mapped[EscalationStatus] = mapped_column(
        SAEnum(EscalationStatus, name="escalation_status"),
        nullable=False,
        default=EscalationStatus.PENDING,
    )
    source_channel: Mapped[str] = mapped_column(
        String(20), nullable=False, default="chat"
    )
    source_agent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    human_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_confidence_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    retrieved_sources: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )
    guardrail_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    escalation_decision: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    customer_context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class EscalationAuditEvent(BaseModel):
    __tablename__ = "escalation_audit_events"

    escalation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("escalation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[Optional[UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[EscalationActionType] = mapped_column(
        SAEnum(EscalationActionType, name="escalation_action_type"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    before_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    after_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    extra_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
