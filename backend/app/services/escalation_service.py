from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from loguru import logger

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.enums import (
    AgentType,
    ConversationStatus,
    EscalationActionType,
    EscalationPriority,
    EscalationStatus,
    UserRole,
    WorkflowStage,
)
from app.models.escalation import EscalationAuditEvent, EscalationCase
from app.models.user import User
from app.repositories.conversation_repository import (
    ConversationRepository,
)
from app.repositories.escalation_repository import (
    EscalationRepository,
)
from app.repositories.user_repository import UserRepository, UserRepositoryError
from app.schemas.ai import AIResponse
from app.schemas.escalation import (
    EscalationActionResponse,
    EscalationAssistBundle,
    EscalationDecisionResponse,
    EscalationDetailResponse,
    EscalationHumanReplyRequest,
    EscalationQueueItem,
    EscalationQueueResponse,
)
from app.services.knowledge_service import KnowledgeService, KnowledgeServiceError


@dataclass(frozen=True)
class EscalationEvaluationResult:
    decision: EscalationDecisionResponse
    case: Optional[EscalationCase]


class EscalationServiceError(Exception):
    """Raised when HITL operations fail."""


class EscalationNotFound(EscalationServiceError):
    """Raised when an escalation case cannot be found."""


class EscalationPermissionDenied(EscalationServiceError):
    """Raised when an escalation action is not permitted."""


class EscalationService:
    def __init__(
        self,
        escalation_repository: EscalationRepository,
        conversation_repository: ConversationRepository,
        user_repository: UserRepository,
        knowledge_service: KnowledgeService,
    ) -> None:
        self.escalation_repository = escalation_repository
        self.conversation_repository = conversation_repository
        self.user_repository = user_repository
        self.knowledge_service = knowledge_service

    def evaluate_ai_response(
        self,
        current_user: User,
        conversation: Conversation,
        ai_response: AIResponse,
        guardrail_result: Dict[str, Any],
        source_channel: str,
    ) -> EscalationEvaluationResult:
        if conversation.human_mode:
            decision = EscalationDecisionResponse(
                should_escalate=False,
                reason="Conversation is currently in human mode.",
                priority=self._priority_from_name(settings.hitl_default_priority),
                source="human_mode",
                confidence_score=ai_response.confidence,
            )
            return EscalationEvaluationResult(decision=decision, case=None)

        decision = self._build_decision(
            ai_response=ai_response,
            guardrail_result=guardrail_result,
            conversation=conversation,
        )
        case = None
        if decision.should_escalate:
            case = self._create_or_update_case(
                current_user=current_user,
                conversation=conversation,
                ai_response=ai_response,
                decision=decision,
                guardrail_result=guardrail_result,
                source_channel=source_channel,
            )
        else:
            self._record_ai_recommendation(
                conversation=conversation,
                ai_response=ai_response,
                decision=decision,
            )

        return EscalationEvaluationResult(decision=decision, case=case)

    def list_escalations(
        self,
        organization_id: UUID,
        statuses: Optional[Sequence[EscalationStatus]] = None,
    ) -> EscalationQueueResponse:
        cases = self.escalation_repository.list_cases(
            organization_id, statuses=statuses
        )
        return EscalationQueueResponse(
            items=[self._queue_item_from_case(case) for case in cases],
        )

    def get_escalation(
        self,
        organization_id: UUID,
        escalation_id: UUID,
        current_user: User,
    ) -> EscalationDetailResponse:
        case = self._get_case_or_raise(escalation_id, organization_id)
        assist_bundle = self._build_assist_bundle(case, current_user)
        return EscalationDetailResponse(
            escalation=self._queue_item_from_case(case),
            audit_trail=self.list_audit_events(case.id),
            assist_bundle=assist_bundle,
        )

    def list_audit_events(
        self,
        escalation_id: UUID,
    ) -> List:
        return self.escalation_repository.list_audit_events(escalation_id)

    def assign_escalation(
        self,
        organization_id: UUID,
        escalation_id: UUID,
        assignee_user_id: UUID,
        actor: User,
        notes: Optional[str] = None,
        priority: Optional[EscalationPriority] = None,
    ) -> EscalationActionResponse:
        case = self._get_case_or_raise(escalation_id, organization_id)
        assignee = self._get_user_or_raise(assignee_user_id, organization_id)
        before_state = self._case_snapshot(case)
        previous_assignee = case.assigned_agent_id
        case.assigned_agent_id = assignee.id
        case.assigned_at = case.assigned_at or datetime.now(timezone.utc)
        case.status = EscalationStatus.ASSIGNED
        case.last_activity_at = datetime.now(timezone.utc)
        if priority is not None:
            case.priority = priority
        self.escalation_repository.update_case(case)
        self._update_conversation_assignment(
            case.conversation_id, assignee.id, human_mode=False
        )
        self._record_audit(
            escalation=case,
            actor=actor,
            action=(
                EscalationActionType.REASSIGNED
                if previous_assignee
                else EscalationActionType.ASSIGNED
            ),
            notes=notes,
            before_state=before_state,
            after_state=self._case_snapshot(case),
            extra_metadata={"assignee": assignee.full_name},
        )
        return EscalationActionResponse(
            escalation_id=case.id,
            status=case.status,
            assigned_agent_id=case.assigned_agent_id,
            human_mode=case.human_mode,
            message=f"Escalation assigned to {assignee.full_name}.",
        )

    def transfer_escalation(
        self,
        organization_id: UUID,
        escalation_id: UUID,
        assignee_user_id: UUID,
        actor: User,
        notes: Optional[str] = None,
    ) -> EscalationActionResponse:
        case = self._get_case_or_raise(escalation_id, organization_id)
        assignee = self._get_user_or_raise(assignee_user_id, organization_id)
        before_state = self._case_snapshot(case)
        case.assigned_agent_id = assignee.id
        case.assigned_at = datetime.now(timezone.utc)
        case.status = EscalationStatus.ASSIGNED
        case.human_mode = False
        case.last_activity_at = datetime.now(timezone.utc)
        self.escalation_repository.update_case(case)
        self._update_conversation_assignment(
            case.conversation_id,
            assignee.id,
            human_mode=False,
        )
        self._record_audit(
            escalation=case,
            actor=actor,
            action=EscalationActionType.TRANSFERRED,
            notes=notes,
            before_state=before_state,
            after_state=self._case_snapshot(case),
            extra_metadata={"assignee": assignee.full_name},
        )
        return EscalationActionResponse(
            escalation_id=case.id,
            status=case.status,
            assigned_agent_id=case.assigned_agent_id,
            human_mode=case.human_mode,
            message=f"Escalation transferred to {assignee.full_name}.",
        )

    def accept_escalation(
        self,
        organization_id: UUID,
        escalation_id: UUID,
        actor: User,
        notes: Optional[str] = None,
    ) -> EscalationActionResponse:
        case = self._get_case_or_raise(escalation_id, organization_id)
        if case.assigned_agent_id is not None and case.assigned_agent_id != actor.id:
            raise EscalationPermissionDenied(
                "Only the assigned operator can accept this escalation."
            )
        before_state = self._case_snapshot(case)
        case.assigned_agent_id = actor.id
        case.assigned_at = case.assigned_at or datetime.now(timezone.utc)
        case.accepted_at = datetime.now(timezone.utc)
        case.status = EscalationStatus.ACCEPTED
        case.human_mode = True
        case.last_activity_at = datetime.now(timezone.utc)
        self.escalation_repository.update_case(case)
        self._update_conversation_assignment(
            case.conversation_id, actor.id, human_mode=True
        )
        self._record_audit(
            escalation=case,
            actor=actor,
            action=EscalationActionType.ACCEPTED,
            notes=notes,
            before_state=before_state,
            after_state=self._case_snapshot(case),
        )
        return EscalationActionResponse(
            escalation_id=case.id,
            status=case.status,
            assigned_agent_id=case.assigned_agent_id,
            human_mode=case.human_mode,
            message="Escalation accepted. AI is paused.",
        )

    def add_human_reply(
        self,
        organization_id: UUID,
        escalation_id: UUID,
        actor: User,
        payload: EscalationHumanReplyRequest,
    ) -> EscalationActionResponse:
        """Persist an operator reply; delivery remains an explicit channel concern."""
        case = self._get_case_or_raise(escalation_id, organization_id)
        if case.assigned_agent_id is not None and case.assigned_agent_id != actor.id:
            raise EscalationPermissionDenied(
                "Only the assigned operator can reply to this escalation."
            )
        if case.status in {EscalationStatus.RESOLVED, EscalationStatus.CLOSED}:
            raise EscalationServiceError(
                "A resolved or closed escalation cannot receive replies."
            )

        before_state = self._case_snapshot(case)
        conversation = self._get_conversation_or_raise(case.conversation_id)
        conversation.memory = list(conversation.memory)
        conversation.memory.append(
            {
                "role": "human",
                "content": payload.message,
                "actor_user_id": str(actor.id),
                "channel": payload.source_channel,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        conversation.human_mode = True
        conversation.human_assignee_id = actor.id
        conversation.human_mode_started_at = (
            conversation.human_mode_started_at or datetime.now(timezone.utc)
        )
        self.conversation_repository.update(conversation)

        case.assigned_agent_id = actor.id
        case.assigned_at = case.assigned_at or datetime.now(timezone.utc)
        case.accepted_at = case.accepted_at or datetime.now(timezone.utc)
        case.status = EscalationStatus.IN_PROGRESS
        case.human_mode = True
        case.last_activity_at = datetime.now(timezone.utc)
        self.escalation_repository.update_case(case)
        self._record_audit(
            escalation=case,
            actor=actor,
            action=EscalationActionType.OVERRIDE,
            notes="Human operator reply recorded.",
            before_state=before_state,
            after_state=self._case_snapshot(case),
            extra_metadata={
                "message": payload.message,
                "source_channel": payload.source_channel,
            },
        )
        logger.info("Human reply recorded for escalation {}", case.id)
        return EscalationActionResponse(
            escalation_id=case.id,
            status=case.status,
            assigned_agent_id=case.assigned_agent_id,
            human_mode=case.human_mode,
            message="Human reply recorded; AI remains paused.",
        )

    def resolve_escalation(
        self,
        organization_id: UUID,
        escalation_id: UUID,
        actor: User,
        notes: Optional[str] = None,
    ) -> EscalationActionResponse:
        case = self._get_case_or_raise(escalation_id, organization_id)
        before_state = self._case_snapshot(case)
        case.status = EscalationStatus.RESOLVED
        case.resolved_at = datetime.now(timezone.utc)
        case.human_mode = False
        case.last_activity_at = datetime.now(timezone.utc)
        self.escalation_repository.update_case(case)
        self._update_conversation_assignment(
            case.conversation_id, None, human_mode=False
        )
        self._record_audit(
            escalation=case,
            actor=actor,
            action=EscalationActionType.RESOLVED,
            notes=notes,
            before_state=before_state,
            after_state=self._case_snapshot(case),
        )
        return EscalationActionResponse(
            escalation_id=case.id,
            status=case.status,
            assigned_agent_id=case.assigned_agent_id,
            human_mode=case.human_mode,
            message="Escalation resolved.",
        )

    def close_escalation(
        self,
        organization_id: UUID,
        escalation_id: UUID,
        actor: User,
        notes: Optional[str] = None,
    ) -> EscalationActionResponse:
        case = self._get_case_or_raise(escalation_id, organization_id)
        before_state = self._case_snapshot(case)
        case.status = EscalationStatus.CLOSED
        case.closed_at = datetime.now(timezone.utc)
        case.human_mode = False
        case.last_activity_at = datetime.now(timezone.utc)
        self.escalation_repository.update_case(case)
        conversation = self._get_conversation_or_raise(case.conversation_id)
        conversation.status = ConversationStatus.CLOSED
        conversation.workflow_stage = WorkflowStage.CLOSED
        conversation.human_mode = False
        conversation.human_assignee_id = None
        conversation.ended_at = datetime.now(timezone.utc)
        self.conversation_repository.update(conversation)
        self._record_audit(
            escalation=case,
            actor=actor,
            action=EscalationActionType.CLOSED,
            notes=notes,
            before_state=before_state,
            after_state=self._case_snapshot(case),
        )
        return EscalationActionResponse(
            escalation_id=case.id,
            status=case.status,
            assigned_agent_id=case.assigned_agent_id,
            human_mode=case.human_mode,
            message="Escalation closed and archived.",
        )

    def get_dashboard_queue(
        self,
        organization_id: UUID,
    ) -> EscalationQueueResponse:
        return self.list_escalations(
            organization_id,
            statuses=(
                EscalationStatus.PENDING,
                EscalationStatus.ASSIGNED,
                EscalationStatus.ACCEPTED,
                EscalationStatus.IN_PROGRESS,
            ),
        )

    def _create_or_update_case(
        self,
        current_user: User,
        conversation: Conversation,
        ai_response: AIResponse,
        decision: EscalationDecisionResponse,
        guardrail_result: Dict[str, Any],
        source_channel: str,
    ) -> EscalationCase:
        existing = self.escalation_repository.get_case_by_conversation(conversation.id)
        if existing is not None and existing.status not in {
            EscalationStatus.CLOSED,
            EscalationStatus.RESOLVED,
        }:
            case = existing
            before_state = self._case_snapshot(case)
            case.escalation_reason = decision.reason
            case.confidence_score = decision.confidence_score
            case.priority = decision.priority
            case.status = EscalationStatus.PENDING
            case.human_mode = False
            case.source_channel = source_channel
            case.source_agent = ai_response.agent.value
            case.ai_confidence_snapshot = {
                "confidence": ai_response.confidence,
                "guardrail_result": guardrail_result,
                "escalation_decision": decision.model_dump(mode="json"),
            }
            case.retrieved_sources = [
                citation.model_dump(mode="json")
                for citation in ai_response.retrieved_sources
            ]
            case.guardrail_result = dict(guardrail_result)
            case.escalation_decision = decision.model_dump(mode="json")
            case.customer_context = self._customer_context(current_user)
            case.last_activity_at = datetime.now(timezone.utc)
            self.escalation_repository.update_case(case)
            self._record_audit(
                escalation=case,
                actor=current_user,
                action=EscalationActionType.OVERRIDE,
                notes="Escalation refreshed from new AI decision.",
                before_state=before_state,
                after_state=self._case_snapshot(case),
            )
            return case

        case = EscalationCase(
            conversation_id=conversation.id,
            organization_id=conversation.organization_id,
            customer_id=current_user.id,
            customer_name=current_user.full_name,
            customer_email=current_user.email,
            assigned_agent_id=None,
            escalation_reason=decision.reason,
            confidence_score=decision.confidence_score,
            priority=decision.priority,
            status=EscalationStatus.PENDING,
            source_channel=source_channel,
            source_agent=ai_response.agent.value,
            human_mode=False,
            ai_confidence_snapshot={
                "confidence": ai_response.confidence,
                "guardrail_result": guardrail_result,
                "escalation_decision": decision.model_dump(mode="json"),
            },
            retrieved_sources=[
                citation.model_dump(mode="json")
                for citation in ai_response.retrieved_sources
            ],
            guardrail_result=dict(guardrail_result),
            escalation_decision=decision.model_dump(mode="json"),
            customer_context=self._customer_context(current_user),
            assigned_at=None,
            accepted_at=None,
            resolved_at=None,
            closed_at=None,
            last_activity_at=datetime.now(timezone.utc),
        )
        created = self.escalation_repository.create_case(case)
        self._update_conversation_escalation(conversation, created, decision)
        self._record_audit(
            escalation=created,
            actor=current_user,
            action=EscalationActionType.CREATED,
            notes=decision.reason,
            before_state={},
            after_state=self._case_snapshot(created),
        )
        self._record_ai_recommendation(
            conversation=conversation,
            ai_response=ai_response,
            decision=decision,
        )
        logger.warning(
            "Escalation created for conversation {} with reason {}",
            conversation.id,
            decision.reason,
        )
        return created

    def _build_decision(
        self,
        ai_response: AIResponse,
        guardrail_result: Dict[str, Any],
        conversation: Conversation,
    ) -> EscalationDecisionResponse:
        guardrail_reason = str(guardrail_result.get("reason") or "").strip()
        guardrail_escalation = bool(guardrail_result.get("escalation_required"))
        should_escalate = False
        source = "confidence"
        reason = "Confidence is below the escalation threshold."
        priority = self._priority_from_name(settings.hitl_default_priority)

        if guardrail_escalation:
            should_escalate = True
            source = "guardrail"
            reason = guardrail_reason or "Guardrail escalation was requested."
            priority = EscalationPriority.HIGH

        elif ai_response.confidence < settings.hitl_low_confidence_threshold:
            should_escalate = True
            source = "confidence"
            priority = EscalationPriority.MEDIUM

        elif not ai_response.retrieved_sources and ai_response.agent == AgentType.FAQ:
            should_escalate = True
            source = "retrieval"
            reason = "No relevant RAG context was found."
            priority = EscalationPriority.MEDIUM

        elif conversation.failure_count >= settings.hitl_repeated_failure_threshold:
            should_escalate = True
            source = "repeated_failure"
            reason = "Repeated failed responses require human support."
            priority = EscalationPriority.HIGH

        elif ai_response.escalation_state.get("reason"):
            should_escalate = True
            source = str(ai_response.escalation_state.get("source") or "orchestrator")
            reason = str(ai_response.escalation_state.get("reason"))
            priority = self._priority_from_name(
                str(
                    ai_response.escalation_state.get("priority")
                    or settings.hitl_default_priority
                )
            )

        if ai_response.guardrail_result:
            guardrail_reason = str(
                ai_response.guardrail_result.get("reason") or ""
            ).strip()
            if ai_response.guardrail_result.get("escalation_required"):
                should_escalate = True
                source = "guardrail"
                reason = guardrail_reason or reason
                priority = EscalationPriority.HIGH

        return EscalationDecisionResponse(
            should_escalate=should_escalate,
            reason=reason,
            priority=priority,
            source=source,
            confidence_score=ai_response.confidence,
        )

    def _update_conversation_escalation(
        self,
        conversation: Conversation,
        escalation: EscalationCase,
        decision: EscalationDecisionResponse,
    ) -> None:
        conversation.status = ConversationStatus.ESCALATED
        conversation.workflow_stage = WorkflowStage.ESCALATED
        conversation.active_agent = AgentType.ESCALATION
        conversation.escalation_state = decision.model_dump(mode="json")
        conversation.human_mode = False
        conversation.human_assignee_id = escalation.assigned_agent_id
        conversation.human_mode_started_at = None
        conversation.failure_count += 1
        self.conversation_repository.update(conversation)

    def _update_conversation_assignment(
        self,
        conversation_id: UUID,
        assignee_id: Optional[UUID],
        human_mode: bool,
    ) -> None:
        conversation = self._get_conversation_or_raise(conversation_id)
        conversation.human_assignee_id = assignee_id
        conversation.human_mode = human_mode
        if human_mode:
            conversation.human_mode_started_at = datetime.now(timezone.utc)
        else:
            conversation.human_mode_started_at = None
        self.conversation_repository.update(conversation)

    def _record_ai_recommendation(
        self,
        conversation: Conversation,
        ai_response: AIResponse,
        decision: EscalationDecisionResponse,
    ) -> None:
        try:
            logger.info(
                "AI recommendation for conversation {} decision={} confidence={}",
                conversation.id,
                decision.should_escalate,
                ai_response.confidence,
            )
        except Exception:
            pass

    def _build_assist_bundle(
        self,
        escalation: EscalationCase,
        current_user: User,
    ) -> EscalationAssistBundle:
        conversation = self._get_conversation_or_raise(escalation.conversation_id)
        recent_history = conversation.memory[-8:]
        latest_customer_message = self._latest_customer_message(conversation)
        knowledge_articles: List[Dict[str, Any]] = []
        if latest_customer_message:
            try:
                results = self.knowledge_service.search(
                    organization_id=escalation.organization_id,
                    query=latest_customer_message,
                    top_k=3,
                )
                knowledge_articles = [
                    {
                        "text": result.text,
                        "score": result.score,
                        "citation": self._citation_from_metadata(result.metadata),
                    }
                    for result in results
                ]
            except KnowledgeServiceError:
                knowledge_articles = []

        summary = self._compose_history_summary(conversation)
        suggested_reply = self._suggest_reply(conversation, escalation)
        suggested_next_actions = self._suggest_next_actions(escalation)

        self._record_audit(
            escalation=escalation,
            actor=current_user,
            action=EscalationActionType.AI_RECOMMENDATION,
            notes="AI assist bundle generated.",
            before_state=self._case_snapshot(escalation),
            after_state=self._case_snapshot(escalation),
            extra_metadata={
                "assist": True,
                "summary": summary,
                "suggested_reply": suggested_reply,
                "knowledge_articles": knowledge_articles,
                "suggested_next_actions": suggested_next_actions,
            },
        )
        return EscalationAssistBundle(
            summary=summary,
            suggested_reply=suggested_reply,
            knowledge_articles=knowledge_articles,
            previous_history=recent_history,
            suggested_next_actions=suggested_next_actions,
        )

    def _suggest_reply(
        self,
        conversation: Conversation,
        escalation: EscalationCase,
    ) -> str:
        if escalation.escalation_reason:
            return f"Thanks for your patience. A human specialist is reviewing: {escalation.escalation_reason}"

        if conversation.lead_information:
            return "I'm reviewing the lead details now and will follow up with a clear next step."

        return (
            "I'm looking into this and will respond with the next best action shortly."
        )

    @staticmethod
    def _suggest_next_actions(escalation: EscalationCase) -> List[str]:
        actions = ["Review the escalation context", "Respond to the customer"]
        if escalation.priority in {
            EscalationPriority.HIGH,
            EscalationPriority.CRITICAL,
        }:
            actions.insert(0, "Handle this case urgently")
        if escalation.status == EscalationStatus.PENDING:
            actions.append("Assign an operator")
        if escalation.human_mode:
            actions.append("Continue the live conversation")
        return actions

    @staticmethod
    def _compose_history_summary(conversation: Conversation) -> str:
        recent = conversation.memory[-6:]
        if not recent:
            return "No prior conversation history is available."
        return " ".join(
            f"{item.get('role')}: {item.get('content')}"
            for item in recent
            if item.get("content")
        )[:360]

    @staticmethod
    def _latest_customer_message(conversation: Conversation) -> Optional[str]:
        for item in reversed(conversation.memory):
            if item.get("role") == "user" and item.get("content"):
                return str(item.get("content"))
        return None

    def _queue_item_from_case(self, case: EscalationCase) -> EscalationQueueItem:
        assigned_agent = None
        if case.assigned_agent_id is not None:
            try:
                assignee = self.user_repository.get_by_id(case.assigned_agent_id)
                if assignee is not None:
                    assigned_agent = assignee.full_name
            except UserRepositoryError:
                assigned_agent = None

        return EscalationQueueItem(
            id=case.id,
            conversation_id=case.conversation_id,
            organization_id=case.organization_id,
            customer=case.customer_name,
            customer_id=case.customer_id,
            assigned_agent=assigned_agent,
            assigned_agent_id=case.assigned_agent_id,
            escalation_reason=case.escalation_reason,
            confidence_score=case.confidence_score,
            timestamp=case.created_at,
            priority=case.priority,
            status=case.status,
            source_channel=case.source_channel,
            source_agent=case.source_agent,
            human_mode=case.human_mode,
        )

    def _record_audit(
        self,
        escalation: EscalationCase,
        actor: Optional[User],
        action: EscalationActionType,
        notes: Optional[str],
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = EscalationAuditEvent(
            escalation_id=escalation.id,
            organization_id=escalation.organization_id,
            actor_user_id=actor.id if actor is not None else None,
            action=action,
            notes=notes,
            before_state=before_state,
            after_state=after_state,
            extra_metadata=extra_metadata or {},
        )
        self.escalation_repository.add_audit_event(event)

    def _get_case_or_raise(
        self, escalation_id: UUID, organization_id: UUID
    ) -> EscalationCase:
        case = self.escalation_repository.get_case_by_id(escalation_id)
        if case is None or case.organization_id != organization_id:
            raise EscalationNotFound(f"Escalation '{escalation_id}' was not found.")
        return case

    def _get_conversation_or_raise(self, conversation_id: UUID) -> Conversation:
        conversation = self.conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise EscalationNotFound(f"Conversation '{conversation_id}' was not found.")
        return conversation

    def _get_user_or_raise(self, user_id: UUID, organization_id: UUID) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None or user.organization_id != organization_id:
            raise EscalationNotFound(f"User '{user_id}' was not found.")
        if user.role not in {UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT}:
            raise EscalationPermissionDenied(
                "Escalations can only be assigned to operators."
            )
        return user

    @staticmethod
    def _customer_context(user: User) -> Dict[str, Any]:
        return {
            "customer_id": str(user.id),
            "name": user.full_name,
            "email": user.email,
            "role": user.role.value,
            "organization_id": str(user.organization_id),
        }

    @staticmethod
    def _citation_from_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "document_id": str(metadata.get("document_id", "")),
            "document": str(metadata.get("document", "")),
            "page": int(metadata.get("page", 1)),
            "chunk_number": int(metadata.get("chunk_number", 0)),
            "source": str(metadata.get("source", "")),
        }

    @staticmethod
    def _case_snapshot(case: EscalationCase) -> Dict[str, Any]:
        return {
            "status": case.status.value,
            "priority": case.priority.value,
            "assigned_agent_id": (
                str(case.assigned_agent_id) if case.assigned_agent_id else None
            ),
            "human_mode": case.human_mode,
            "last_activity_at": (
                case.last_activity_at.isoformat() if case.last_activity_at else None
            ),
        }

    @staticmethod
    def _priority_from_name(priority: str) -> EscalationPriority:
        normalized = priority.upper().strip()
        try:
            return EscalationPriority[normalized]
        except KeyError:
            return EscalationPriority.MEDIUM
