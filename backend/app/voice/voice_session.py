from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.enums import AgentType, WorkflowStage


@dataclass
class VoiceSessionContext:
    session_id: UUID
    conversation_id: UUID
    organization_id: UUID
    active_user_id: UUID
    current_agent: Optional[AgentType] = None
    workflow_stage: WorkflowStage = WorkflowStage.ROUTING
    transcript: List[Dict[str, Any]] = field(default_factory=list)
    memory: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True
