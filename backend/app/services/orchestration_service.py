from __future__ import annotations

import re
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger

from app.core.config import settings
from app.models.conversation import Conversation, ConversationSummary
from app.models.enums import (
    AgentType,
    ConversationStatus,
    WorkflowStage,
)
from app.models.user import User
from app.repositories.conversation_repository import (
    ConversationRepository,
    ConversationRepositoryError,
)
from app.schemas.ai import (
    AIResponse,
    EscalationResponse,
    LeadCapture,
    LeadQualificationResponse,
    OrchestrationRequest,
    SchedulingCapture,
    SchedulingResponse,
    SummaryResponse,
)
from app.schemas.knowledge import KnowledgeCitation
from app.services.escalation_service import EscalationService
from app.services.guardrails import GuardrailDecision, GuardrailService
from app.services.knowledge_service import KnowledgeService, KnowledgeServiceError
from app.services.llm_provider import LLMProvider, LLMProviderError, get_llm_provider


class OrchestrationServiceError(Exception):
    """Raised when orchestration fails."""


class ConversationNotFound(OrchestrationServiceError):
    """Raised when a conversation cannot be found."""


class AgentOrchestratorService:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        knowledge_service: KnowledgeService,
        escalation_service: Optional[EscalationService] = None,
        guardrail_service: Optional[GuardrailService] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        self.conversation_repository = conversation_repository
        self.knowledge_service = knowledge_service
        self.escalation_service = escalation_service
        self.guardrail_service = guardrail_service or GuardrailService()
        self.llm_provider = llm_provider or get_llm_provider()

    async def process_message(
        self,
        current_user: User,
        payload: OrchestrationRequest,
    ) -> AIResponse:
        conversation = self._get_or_create_conversation(current_user, payload)
        if conversation.human_mode:
            return self._human_mode_response(conversation)

        conversation.workflow_stage = WorkflowStage.ROUTING
        self._append_memory(conversation, "user", payload.message)

        guardrail_decision = self.guardrail_service.check_input(payload.message)
        if not guardrail_decision.allowed:
            conversation.failure_count += 1
            conversation.escalation_state = self._build_escalation_state(
                reason=guardrail_decision.reason or "Unsafe request",
                priority="high",
                source="guardrail",
            )
            conversation.status = ConversationStatus.ESCALATED
            conversation.active_agent = AgentType.ESCALATION
            conversation.workflow_stage = WorkflowStage.ESCALATED
            self.conversation_repository.update(conversation)
            logger.warning(
                "Orchestration blocked unsafe message for conversation {}",
                conversation.id,
            )
            response = self._escalation_to_ai_response(
                self._build_escalation_response(
                    conversation=conversation,
                    reason=guardrail_decision.reason or "Unsafe request",
                    priority="high",
                ),
                conversation=conversation,
            )
            review = self._review_escalation(
                current_user=current_user,
                conversation=conversation,
                response=response,
                guardrail_decision=guardrail_decision,
                source_channel=payload.source_channel,
            )
            final_response = review or response
            self._append_memory(conversation, "assistant", final_response.message)
            self.conversation_repository.update(conversation)
            return final_response

        response: AIResponse
        if payload.close_conversation:
            summary_text = await self._store_and_close_summary(
                conversation,
                current_user,
            )
            response = AIResponse(
                conversation_id=conversation.id,
                agent=AgentType.SUMMARY,
                status=ConversationStatus.CLOSED,
                workflow_stage=WorkflowStage.CLOSED,
                message=summary_text,
                confidence=1.0,
                citations=[],
                retrieved_sources=[],
                guardrail_result=asdict(guardrail_decision),
                escalation_decision={},
                structured_data={"summary": summary_text},
                escalation_state={},
            )
        else:
            if conversation.failure_count >= settings.orchestration_failure_threshold:
                escalation = self._escalate_conversation(
                    conversation=conversation,
                    reason="Repeated failures require human escalation.",
                    priority="high",
                )
                response = self._escalation_to_ai_response(
                    escalation,
                    conversation=conversation,
                )
            else:
                intent = self._classify_intent(conversation, payload.message)
                conversation.active_agent = intent

                if intent == AgentType.FAQ:
                    response = await self._run_faq_agent(conversation, payload.message)
                elif intent == AgentType.LEAD:
                    response = await self._run_lead_agent(
                        conversation,
                        payload.message,
                    )
                elif intent == AgentType.SCHEDULING:
                    response = await self._run_scheduling_agent(
                        conversation,
                        payload.message,
                    )
                elif intent == AgentType.SUMMARY:
                    summary_text = await self._store_and_close_summary(
                        conversation,
                        current_user,
                    )
                    response = AIResponse(
                        conversation_id=conversation.id,
                        agent=AgentType.SUMMARY,
                        status=ConversationStatus.CLOSED,
                        workflow_stage=WorkflowStage.CLOSED,
                        message=summary_text,
                        confidence=1.0,
                        citations=[],
                        retrieved_sources=[],
                        guardrail_result=asdict(guardrail_decision),
                        escalation_decision={},
                        structured_data={"summary": summary_text},
                        escalation_state={},
                    )
                else:
                    escalation = self._escalate_conversation(
                        conversation=conversation,
                        reason="No reliable route or relevant knowledge was found.",
                        priority="medium",
                    )
                    response = self._escalation_to_ai_response(
                        escalation,
                        conversation=conversation,
                    )

        review = self._review_escalation(
            current_user=current_user,
            conversation=conversation,
            response=response,
            guardrail_decision=guardrail_decision,
            source_channel=payload.source_channel,
        )
        final_response = review or response
        if final_response.agent != AgentType.SUMMARY:
            self._append_memory(conversation, "assistant", final_response.message)
        self.conversation_repository.update(conversation)
        return final_response

    async def generate_summary(
        self,
        conversation: Conversation,
        current_user: User,
    ) -> SummaryResponse:
        summary_text = await self._store_and_close_summary(conversation, current_user)
        return SummaryResponse(
            conversation_id=conversation.id,
            summary=summary_text,
            stored=True,
        )

    async def run_lead_qualification(
        self,
        current_user: User,
        conversation_id: UUID,
        message: str,
    ) -> LeadQualificationResponse:
        conversation = self._get_conversation_or_raise(conversation_id)
        if conversation.organization_id != current_user.organization_id:
            raise ConversationNotFound(
                f"Conversation '{conversation_id}' was not found."
            )
        self._append_memory(conversation, "user", message)
        lead = self._extract_lead_capture(conversation, message)
        conversation.active_agent = AgentType.LEAD
        conversation.lead_information = lead.model_dump()
        conversation.workflow_stage = WorkflowStage.EXECUTION
        self.conversation_repository.update(conversation)
        return LeadQualificationResponse(
            conversation_id=conversation.id,
            agent=AgentType.LEAD,
            lead=lead,
            confidence=self._confidence_from_capture(lead.missing_fields, 4),
            message=self._lead_follow_up_message(lead),
        )

    async def run_scheduling(
        self,
        current_user: User,
        conversation_id: UUID,
        message: str,
    ) -> SchedulingResponse:
        conversation = self._get_conversation_or_raise(conversation_id)
        if conversation.organization_id != current_user.organization_id:
            raise ConversationNotFound(
                f"Conversation '{conversation_id}' was not found."
            )
        self._append_memory(conversation, "user", message)
        booking = self._extract_booking_request(conversation, message)
        conversation.active_agent = AgentType.SCHEDULING
        conversation.booking_request = booking.model_dump()
        conversation.workflow_stage = WorkflowStage.EXECUTION
        self.conversation_repository.update(conversation)
        return SchedulingResponse(
            conversation_id=conversation.id,
            agent=AgentType.SCHEDULING,
            booking_request=booking,
            confidence=self._confidence_from_capture(booking.missing_fields, 6),
            message=self._scheduling_follow_up_message(booking),
        )

    async def escalate(
        self,
        current_user: User,
        conversation_id: UUID,
        reason: Optional[str] = None,
        message: Optional[str] = None,
    ) -> EscalationResponse:
        conversation = self._get_conversation_or_raise(conversation_id)
        if conversation.organization_id != current_user.organization_id:
            raise ConversationNotFound(
                f"Conversation '{conversation_id}' was not found."
            )
        escalation_reason = reason or message or "Conversation escalated to human."
        response = self._escalate_conversation(
            conversation=conversation,
            reason=escalation_reason,
            priority="high",
        )
        self.conversation_repository.update(conversation)
        return response

    async def list_conversations(
        self,
        organization_id: UUID,
    ) -> List[Conversation]:
        try:
            return self.conversation_repository.list_by_organization(organization_id)
        except ConversationRepositoryError as exc:
            raise OrchestrationServiceError("Failed to list conversations.") from exc

    def get_conversation(self, conversation_id: UUID) -> Conversation:
        return self._get_conversation_or_raise(conversation_id)

    def start_conversation(self, current_user: User) -> Conversation:
        conversation = Conversation(
            id=uuid4(),
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            workflow_stage=WorkflowStage.ROUTING,
            status=ConversationStatus.ACTIVE,
            active_agent=None,
        )
        return self.conversation_repository.create(conversation)

    def close_conversation(self, conversation: Conversation) -> Conversation:
        conversation.status = ConversationStatus.CLOSED
        conversation.workflow_stage = WorkflowStage.CLOSED
        conversation.ended_at = datetime.now(timezone.utc)
        return self.conversation_repository.update(conversation)

    def _get_or_create_conversation(
        self,
        current_user: User,
        payload: OrchestrationRequest,
    ) -> Conversation:
        if payload.conversation_id is None:
            return self.start_conversation(current_user)

        conversation = self._get_conversation_or_raise(payload.conversation_id)
        if conversation.organization_id != current_user.organization_id:
            raise ConversationNotFound(
                f"Conversation '{payload.conversation_id}' was not found."
            )

        return conversation

    def _get_conversation_or_raise(self, conversation_id: UUID) -> Conversation:
        try:
            conversation = self.conversation_repository.get_by_id(conversation_id)
            if conversation is None:
                raise ConversationNotFound(
                    f"Conversation '{conversation_id}' was not found."
                )
            return conversation
        except ConversationRepositoryError as exc:
            raise OrchestrationServiceError("Failed to fetch conversation.") from exc

    def _classify_intent(
        self,
        conversation: Conversation,
        message: str,
    ) -> AgentType:
        if self._is_summary_request(message):
            return AgentType.SUMMARY
        if self._is_scheduling_request(message):
            return AgentType.SCHEDULING
        if self._is_lead_request(message):
            return AgentType.LEAD

        try:
            results = self.knowledge_service.search(
                organization_id=conversation.organization_id,
                query=message,
                top_k=3,
            )
        except KnowledgeServiceError:
            return AgentType.ESCALATION

        if results:
            conversation.retrieved_documents = [result.metadata for result in results]
            return AgentType.FAQ

        return AgentType.ESCALATION

    async def _run_faq_agent(
        self,
        conversation: Conversation,
        message: str,
    ) -> AIResponse:
        try:
            results = self.knowledge_service.search(
                organization_id=conversation.organization_id,
                query=message,
                top_k=3,
            )
        except KnowledgeServiceError:
            results = []

        if not results:
            conversation.failure_count += 1
            return self._escalation_to_ai_response(
                self._escalate_conversation(
                    conversation=conversation,
                    reason="No relevant knowledge was found.",
                    priority="medium",
                ),
                conversation=conversation,
            )

        citations = [self._citation_from_result(result) for result in results]
        conversation.retrieved_documents = [result.metadata for result in results]
        answer = await self._compose_faq_answer(message, results)
        confidence = min(1.0, 0.5 + 0.15 * len(results))
        if confidence < settings.hitl_low_confidence_threshold:
            conversation.failure_count += 1
            return self._escalation_to_ai_response(
                self._escalate_conversation(
                    conversation=conversation,
                    reason="FAQ confidence is too low.",
                    priority="medium",
                ),
                conversation=conversation,
            )
        conversation.failure_count = 0
        conversation.workflow_stage = WorkflowStage.VALIDATION
        return AIResponse(
            conversation_id=conversation.id,
            agent=AgentType.FAQ,
            status=ConversationStatus.ACTIVE,
            workflow_stage=WorkflowStage.VALIDATION,
            message=answer,
            confidence=confidence,
            citations=citations,
            retrieved_sources=citations,
            guardrail_result={},
            escalation_decision={},
            structured_data={},
            escalation_state={},
        )

    async def _run_lead_agent(
        self,
        conversation: Conversation,
        message: str,
    ) -> AIResponse:
        lead = self._extract_lead_capture(conversation, message)
        conversation.lead_information = lead.model_dump()
        conversation.workflow_stage = WorkflowStage.EXECUTION
        confidence = self._confidence_from_capture(lead.missing_fields, 4)
        if confidence < 0.35:
            conversation.failure_count += 1
            return self._escalation_to_ai_response(
                self._escalate_conversation(
                    conversation=conversation,
                    reason="Lead qualification confidence is too low.",
                    priority="medium",
                ),
                conversation=conversation,
            )

        return AIResponse(
            conversation_id=conversation.id,
            agent=AgentType.LEAD,
            status=ConversationStatus.ACTIVE,
            workflow_stage=WorkflowStage.EXECUTION,
            message=self._lead_follow_up_message(lead),
            confidence=confidence,
            citations=[],
            retrieved_sources=[],
            guardrail_result={},
            escalation_decision={},
            structured_data={"lead": lead.model_dump()},
            escalation_state={},
        )

    async def _run_scheduling_agent(
        self,
        conversation: Conversation,
        message: str,
    ) -> AIResponse:
        booking = self._extract_booking_request(conversation, message)
        conversation.booking_request = booking.model_dump()
        conversation.workflow_stage = WorkflowStage.EXECUTION
        confidence = self._confidence_from_capture(booking.missing_fields, 6)
        if confidence < 0.35:
            conversation.failure_count += 1
            return self._escalation_to_ai_response(
                self._escalate_conversation(
                    conversation=conversation,
                    reason="Scheduling confidence is too low.",
                    priority="medium",
                ),
                conversation=conversation,
            )

        return AIResponse(
            conversation_id=conversation.id,
            agent=AgentType.SCHEDULING,
            status=ConversationStatus.ACTIVE,
            workflow_stage=WorkflowStage.EXECUTION,
            message=self._scheduling_follow_up_message(booking),
            confidence=confidence,
            citations=[],
            retrieved_sources=[],
            guardrail_result={},
            escalation_decision={},
            structured_data={"booking_request": booking.model_dump()},
            escalation_state={},
        )

    def _escalate_conversation(
        self,
        conversation: Conversation,
        reason: str,
        priority: str,
    ) -> EscalationResponse:
        conversation.status = ConversationStatus.ESCALATED
        conversation.workflow_stage = WorkflowStage.ESCALATED
        conversation.active_agent = AgentType.ESCALATION
        conversation.escalation_state = self._build_escalation_state(
            reason=reason,
            priority=priority,
            source="orchestrator",
        )
        conversation.failure_count += 1
        return self._build_escalation_response(conversation, reason, priority)

    def _build_escalation_response(
        self,
        conversation: Conversation,
        reason: str,
        priority: str,
    ) -> EscalationResponse:
        return EscalationResponse(
            conversation_id=conversation.id,
            reason=reason,
            priority=priority,
            status=conversation.status,
        )

    def _escalation_to_ai_response(
        self,
        escalation: EscalationResponse,
        conversation: Optional[Conversation] = None,
    ) -> AIResponse:
        if conversation is None:
            conversation = self._get_conversation_or_raise(escalation.conversation_id)
        return AIResponse(
            conversation_id=escalation.conversation_id,
            agent=AgentType.ESCALATION,
            status=escalation.status,
            workflow_stage=WorkflowStage.ESCALATED,
            message=escalation.reason,
            confidence=0.0,
            citations=[],
            retrieved_sources=[],
            guardrail_result={},
            escalation_decision=conversation.escalation_state or {},
            structured_data={},
            escalation_state=conversation.escalation_state or {},
        )

    def _review_escalation(
        self,
        current_user: User,
        conversation: Conversation,
        response: AIResponse,
        guardrail_decision: GuardrailDecision,
        source_channel: str,
    ) -> Optional[AIResponse]:
        if self.escalation_service is None:
            return None

        review = self.escalation_service.evaluate_ai_response(
            current_user=current_user,
            conversation=conversation,
            ai_response=response,
            guardrail_result=asdict(guardrail_decision),
            source_channel=source_channel,
        )
        if review.decision.should_escalate and review.case is not None:
            escalation_state = review.case.escalation_decision or {}
            return AIResponse(
                conversation_id=review.case.conversation_id,
                agent=AgentType.ESCALATION,
                status=ConversationStatus.ESCALATED,
                workflow_stage=WorkflowStage.ESCALATED,
                message=review.case.escalation_reason,
                confidence=0.0,
                citations=[],
                retrieved_sources=[],
                guardrail_result=asdict(guardrail_decision),
                escalation_decision=escalation_state,
                structured_data={
                    "escalation_id": str(review.case.id),
                    "priority": review.case.priority.value,
                    "status": review.case.status.value,
                },
                escalation_state=escalation_state,
            )

        return None

    @staticmethod
    def _human_mode_response(conversation: Conversation) -> AIResponse:
        return AIResponse(
            conversation_id=conversation.id,
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

    async def _compose_faq_answer(
        self,
        message: str,
        results: List[Any],
    ) -> str:
        if self.llm_provider.__class__.__name__ == "RuleBasedLLMProvider":
            source_lines = [
                f"[{index}] {result.text.strip()}"
                for index, result in enumerate(results, start=1)
            ]
            return (
                "Based on the knowledge base, here is the relevant information:\n"
                + "\n".join(source_lines)
            )

        prompt = self._faq_prompt(message, results)
        try:
            return await self.llm_provider.complete(
                prompt=prompt,
                system_prompt=(
                    "You are the FAQ agent. Answer only from the supplied "
                    "knowledge snippets and cite the sources."
                ),
            )
        except LLMProviderError as exc:
            logger.warning("FAQ generation fell back to retrieval text: {}", exc)
            return self._compose_retrieval_fallback(results)

    async def _summarize_conversation(self, conversation: Conversation) -> str:
        if self.llm_provider.__class__.__name__ == "RuleBasedLLMProvider":
            return self._compose_summary_fallback(conversation)

        prompt = self._summary_prompt(conversation)
        try:
            return await self.llm_provider.complete(
                prompt=prompt,
                system_prompt=(
                    "You are the conversation summary agent. Produce a concise "
                    "summary of the conversation."
                ),
            )
        except LLMProviderError as exc:
            logger.warning("Summary generation fell back to heuristic text: {}", exc)
            return self._compose_summary_fallback(conversation)

    async def _store_and_close_summary(
        self,
        conversation: Conversation,
        current_user: User,
    ) -> str:
        conversation.workflow_stage = WorkflowStage.MEMORY_UPDATE
        summary_text = await self._summarize_conversation(conversation)
        summary = ConversationSummary(
            conversation_id=conversation.id,
            organization_id=conversation.organization_id,
            user_id=current_user.id,
            summary=summary_text,
            source_agent=AgentType.SUMMARY.value,
            is_final=True,
        )
        conversation.status = ConversationStatus.CLOSED
        conversation.ended_at = datetime.now(timezone.utc)
        conversation.active_agent = AgentType.SUMMARY
        conversation.workflow_stage = WorkflowStage.CLOSED
        self._append_memory(conversation, "assistant", summary_text)
        self.conversation_repository.add_summary(summary)
        self.conversation_repository.update(conversation)
        logger.info("Generated summary for conversation {}", conversation.id)
        return summary_text

    def _compose_retrieval_fallback(self, results: List[Any]) -> str:
        lines = [
            f"- {result.text.strip()} (source: {result.metadata.get('source')})"
            for result in results
        ]
        return "Based on the knowledge base:\n" + "\n".join(lines)

    def _compose_summary_fallback(self, conversation: Conversation) -> str:
        recent_messages = conversation.memory[-6:]
        message_count = len(
            [item for item in conversation.memory if item.get("role") == "user"]
        )
        topics = []
        if conversation.lead_information:
            topics.append("lead qualification")
        if conversation.booking_request:
            topics.append("scheduling")
        if conversation.retrieved_documents:
            topics.append("knowledge retrieval")
        if conversation.escalation_state:
            topics.append("escalation")

        topic_text = ", ".join(topics) if topics else "general support"
        recent_text = " ".join(
            entry.get("content", "")
            for entry in recent_messages
            if entry.get("content")
        )
        return (
            f"Conversation covered {topic_text}. "
            f"It included {message_count} user messages. "
            f"Recent context: {recent_text[:220].strip()}"
        ).strip()

    def _faq_prompt(self, message: str, results: List[Any]) -> str:
        snippets = []
        for index, result in enumerate(results, start=1):
            snippets.append(
                f"Source {index}: {result.metadata.get('source')} | "
                f"Page {result.metadata.get('page')} | "
                f"Chunk {result.metadata.get('chunk_number')}\n"
                f"{result.text}"
            )
        return f"Question: {message}\n\n" "Knowledge snippets:\n" + "\n\n".join(
            snippets
        )

    def _summary_prompt(self, conversation: Conversation) -> str:
        memory_text = "\n".join(
            f"{entry.get('role')}: {entry.get('content')}"
            for entry in conversation.memory
        )
        return (
            "Summarize the conversation in 3 sentences or fewer.\n"
            f"Lead information: {conversation.lead_information}\n"
            f"Booking request: {conversation.booking_request}\n"
            f"Escalation: {conversation.escalation_state}\n"
            f"History:\n{memory_text}"
        )

    def _append_memory(
        self,
        conversation: Conversation,
        role: str,
        content: str,
    ) -> None:
        conversation.memory = list(conversation.memory)
        conversation.memory.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _extract_lead_capture(
        self,
        conversation: Conversation,
        message: str,
    ) -> LeadCapture:
        existing = dict(conversation.lead_information or {})
        name = self._first_match(
            message,
            [
                r"\bmy name is ([A-Za-z][A-Za-z\s'-]{1,80})",
                r"\bi am ([A-Za-z][A-Za-z\s'-]{1,80})",
                r"\bthis is ([A-Za-z][A-Za-z\s'-]{1,80})",
            ],
        ) or existing.get("name")
        budget = self._first_match(
            message,
            [
                r"\b(?:budget|budget is|spend|spending|around)\s*(?:is\s*)?([\$€£]?\d[\d,\.]*\s*(?:k|m)?(?:\s*(?:per\s+month|monthly|annually|per\s+year))?)",
                r"\b([\$€£]\d[\d,\.]*\s*(?:k|m)?)",
            ],
        ) or existing.get("budget")
        timeline = self._first_match(
            message,
            [
                r"\b(?:timeline|timing|in)\s*([A-Za-z0-9\s\-]+)",
                r"\b(next week|next month|this week|this month|in \d+\s+(?:days|weeks|months))",
            ],
        ) or existing.get("timeline")
        interest = self._first_match(
            message,
            [
                r"\binterested in ([A-Za-z0-9\s\-&,/]+)",
                r"\blooking for ([A-Za-z0-9\s\-&,/]+)",
            ],
        ) or existing.get("interest")

        lead = LeadCapture(
            name=self._clean_capture_value(name),
            budget=self._clean_capture_value(budget),
            timeline=self._clean_capture_value(timeline),
            interest=self._clean_capture_value(interest),
            missing_fields=self._missing_fields(
                {
                    "name": name,
                    "budget": budget,
                    "timeline": timeline,
                    "interest": interest,
                }
            ),
        )
        return lead

    def _extract_booking_request(
        self,
        conversation: Conversation,
        message: str,
    ) -> SchedulingCapture:
        existing = dict(conversation.booking_request or {})
        name = self._first_match(
            message,
            [
                r"\bmy name is ([A-Za-z][A-Za-z\s'-]{1,80})",
                r"\bi am ([A-Za-z][A-Za-z\s'-]{1,80})",
            ],
        ) or existing.get("name")
        date = self._first_match(
            message,
            [
                r"\b(?:on|for)\s+((?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?)",
                r"\b(today|tomorrow|next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))",
            ],
        ) or existing.get("appointment_date")
        time = self._first_match(
            message,
            [
                r"\b(?:at|around)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))",
                r"\b(\d{1,2}:\d{2})",
            ],
        ) or existing.get("appointment_time")
        timezone_value = self._first_match(
            message,
            [
                r"\b(UTC[+\-]\d{1,2})\b",
                r"\b(IST|PST|PDT|MST|MDT|CST|CDT|EST|EDT)\b",
            ],
        ) or existing.get("timezone")
        email = self._first_match(
            message,
            [r"([A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+)"],
        ) or existing.get("contact_email")
        phone = self._first_match(
            message,
            [r"(\+?\d[\d\s().-]{7,}\d)"],
        ) or existing.get("contact_phone")
        purpose = self._first_match(
            message,
            [
                r"\b(?:for|about|regarding)\s+([A-Za-z0-9\s\-&,/]+)",
            ],
        ) or existing.get("purpose")

        booking = SchedulingCapture(
            name=self._clean_capture_value(name),
            appointment_date=self._clean_capture_value(date),
            appointment_time=self._clean_capture_value(time),
            timezone=self._clean_capture_value(timezone_value),
            contact_email=self._clean_capture_value(email),
            contact_phone=self._clean_capture_value(phone),
            purpose=self._clean_capture_value(purpose),
            missing_fields=self._missing_fields(
                {
                    "name": name,
                    "appointment_date": date,
                    "appointment_time": time,
                    "timezone": timezone_value,
                    "contact_email": email,
                    "purpose": purpose,
                }
            ),
        )
        return booking

    @staticmethod
    def _confidence_from_capture(
        missing_fields: List[str],
        total_fields: int,
    ) -> float:
        captured = max(total_fields - len(missing_fields), 0)
        return round(captured / float(total_fields), 2)

    @staticmethod
    def _lead_follow_up_message(lead: LeadCapture) -> str:
        if lead.missing_fields:
            return "I still need: " + ", ".join(lead.missing_fields) + "."
        return "Lead information captured successfully."

    @staticmethod
    def _scheduling_follow_up_message(booking: SchedulingCapture) -> str:
        if booking.missing_fields:
            return "I still need: " + ", ".join(booking.missing_fields) + "."
        return "Booking request captured successfully."

    @staticmethod
    def _citation_from_result(result: Any) -> KnowledgeCitation:
        return KnowledgeCitation(
            document_id=str(result.metadata["document_id"]),
            document=str(result.metadata["document"]),
            page=int(result.metadata["page"]),
            chunk_number=int(result.metadata["chunk_number"]),
            source=str(result.metadata["source"]),
        )

    @staticmethod
    def _build_escalation_state(
        reason: str,
        priority: str,
        source: str,
    ) -> Dict[str, Any]:
        return {
            "reason": reason,
            "priority": priority,
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _missing_fields(values: Dict[str, Optional[str]]) -> List[str]:
        return [field for field, value in values.items() if not value]

    @staticmethod
    def _clean_capture_value(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        return value.strip().strip(".,;:")

    @staticmethod
    def _first_match(message: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if match:
                if match.groups():
                    return match.group(1)
                return match.group(0)
        return None

    @staticmethod
    def _is_lead_request(message: str) -> bool:
        lowered = message.lower()
        return any(
            keyword in lowered
            for keyword in ("budget", "pricing", "price", "quote", "cost", "demo")
        )

    @staticmethod
    def _is_scheduling_request(message: str) -> bool:
        lowered = message.lower()
        return any(
            keyword in lowered
            for keyword in ("appointment", "schedule", "meeting", "book", "demo")
        )

    @staticmethod
    def _is_summary_request(message: str) -> bool:
        lowered = message.lower()
        return any(keyword in lowered for keyword in ("bye", "thanks", "close", "end"))
