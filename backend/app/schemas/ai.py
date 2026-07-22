from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AgentType, ConversationStatus, WorkflowStage
from app.schemas.knowledge import KnowledgeCitation


class OrchestrationRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str = Field(min_length=1)
    close_conversation: bool = False
    source_channel: str = "chat"


class LeadCapture(BaseModel):
    name: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    interest: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)


class SchedulingCapture(BaseModel):
    name: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    timezone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    purpose: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)


class AIResponse(BaseModel):
    conversation_id: UUID
    agent: AgentType
    status: ConversationStatus
    workflow_stage: WorkflowStage
    message: str
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[KnowledgeCitation] = Field(default_factory=list)
    retrieved_sources: List[KnowledgeCitation] = Field(default_factory=list)
    guardrail_result: Dict[str, Any] = Field(default_factory=dict)
    escalation_decision: Dict[str, Any] = Field(default_factory=dict)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    escalation_state: Dict[str, Any] = Field(default_factory=dict)


class ConversationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    status: ConversationStatus
    workflow_stage: WorkflowStage
    active_agent: Optional[AgentType] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    memory: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_state: Dict[str, Any] = Field(default_factory=dict)
    human_mode: bool = False
    human_assignee_id: Optional[UUID] = None


class SummaryRequest(BaseModel):
    conversation_id: UUID


class SummaryResponse(BaseModel):
    conversation_id: UUID
    summary: str
    stored: bool = True


class EscalationRequest(BaseModel):
    conversation_id: UUID
    reason: Optional[str] = None
    message: Optional[str] = None


class EscalationResponse(BaseModel):
    conversation_id: UUID
    reason: str
    priority: str
    status: ConversationStatus


class LeadQualificationRequest(BaseModel):
    conversation_id: UUID
    message: str = Field(min_length=1)


class LeadQualificationResponse(BaseModel):
    conversation_id: UUID
    agent: AgentType
    lead: LeadCapture
    confidence: float = Field(ge=0.0, le=1.0)
    message: str


class SchedulingRequest(BaseModel):
    conversation_id: UUID
    message: str = Field(min_length=1)


class SchedulingResponse(BaseModel):
    conversation_id: UUID
    agent: AgentType
    booking_request: SchedulingCapture
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
