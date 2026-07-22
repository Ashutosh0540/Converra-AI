from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EscalationActionType, EscalationPriority, EscalationStatus


class EscalationAssignRequest(BaseModel):
    assignee_user_id: UUID
    notes: Optional[str] = None
    priority: Optional[EscalationPriority] = None


class EscalationActionRequest(BaseModel):
    notes: Optional[str] = None


class EscalationHumanReplyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    source_channel: str = Field(default="chat", min_length=1, max_length=20)


class EscalationActionResponse(BaseModel):
    escalation_id: UUID
    status: EscalationStatus
    assigned_agent_id: Optional[UUID] = None
    human_mode: bool = False
    message: str


class EscalationQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    organization_id: UUID
    customer: str
    customer_id: UUID
    assigned_agent: Optional[str] = None
    assigned_agent_id: Optional[UUID] = None
    escalation_reason: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    priority: EscalationPriority
    status: EscalationStatus
    source_channel: str
    source_agent: Optional[str] = None
    human_mode: bool = False


class EscalationAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    escalation_id: UUID
    organization_id: UUID
    actor_user_id: Optional[UUID] = None
    action: EscalationActionType
    notes: Optional[str] = None
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    extra_metadata: Dict[str, Any]
    created_at: datetime


class EscalationAssistBundle(BaseModel):
    summary: str
    suggested_reply: str
    knowledge_articles: List[Dict[str, Any]] = Field(default_factory=list)
    previous_history: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_next_actions: List[str] = Field(default_factory=list)


class EscalationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escalation: EscalationQueueItem
    audit_trail: List[EscalationAuditEventResponse] = Field(default_factory=list)
    assist_bundle: EscalationAssistBundle


class EscalationQueueResponse(BaseModel):
    items: List[EscalationQueueItem]


class EscalationListResponse(BaseModel):
    items: List[EscalationQueueItem]


class EscalationDecisionResponse(BaseModel):
    should_escalate: bool
    reason: str
    priority: EscalationPriority
    source: str
    confidence_score: float = Field(ge=0.0, le=1.0)
