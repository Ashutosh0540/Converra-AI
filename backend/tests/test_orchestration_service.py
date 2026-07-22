from __future__ import annotations

import pytest

from app.models.conversation import ConversationSummary
from app.models.enums import AgentType, ConversationStatus, UserRole
from app.models.organization import Organization
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.ai import OrchestrationRequest
from app.services.knowledge_types import VectorSearchResult
from app.services.orchestration_service import AgentOrchestratorService


class FakeKnowledgeService:
    def __init__(self, results_by_query: dict[str, list[VectorSearchResult]]) -> None:
        self.results_by_query = results_by_query

    def search(self, organization_id, query, top_k, filters=None):  # noqa: ANN001
        del organization_id, top_k, filters
        for key, results in self.results_by_query.items():
            if key.lower() in query.lower():
                return results
        return []


def _create_org_user(db_session):
    organization = Organization(
        name="Converra",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()
    user = User(
        organization_id=organization.id,
        full_name="Operator One",
        email="operator@example.com",
        password_hash="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return organization, user


@pytest.mark.asyncio()
async def test_orchestrator_routes_faq_lead_schedule_and_summary(db_session):
    organization, user = _create_org_user(db_session)
    faq_results = [
        VectorSearchResult(
            text="Reset passwords from the profile settings page.",
            score=0.91,
            metadata={
                "document_id": "doc-1",
                "document": "handbook.pdf",
                "page": 4,
                "chunk_number": 2,
                "source": "handbook.pdf",
            },
        )
    ]
    service = AgentOrchestratorService(
        ConversationRepository(db_session),
        FakeKnowledgeService({"password": faq_results}),
    )

    faq_response = await service.process_message(
        user,
        OrchestrationRequest(message="How do I reset my password?"),
    )
    assert faq_response.agent == AgentType.FAQ
    assert faq_response.citations[0].source == "handbook.pdf"

    conversation = service.get_conversation(faq_response.conversation_id)
    assert conversation.active_agent == AgentType.FAQ
    assert len(conversation.memory) == 2

    lead_response = await service.process_message(
        user,
        OrchestrationRequest(
            conversation_id=faq_response.conversation_id,
            message=(
                "My name is Ada Lovelace, budget is $5000, timeline next month, "
                "interested in enterprise support."
            ),
        ),
    )
    assert lead_response.agent == AgentType.LEAD
    assert lead_response.structured_data["lead"]["budget"] == "$5000"

    schedule_response = await service.process_message(
        user,
        OrchestrationRequest(
            conversation_id=faq_response.conversation_id,
            message=(
                "Book a meeting next Tuesday at 2 pm IST for product demo. "
                "Email ada@example.com."
            ),
        ),
    )
    assert schedule_response.agent == AgentType.SCHEDULING
    assert (
        schedule_response.structured_data["booking_request"]["contact_email"]
        == "ada@example.com"
    )

    summary_response = await service.process_message(
        user,
        OrchestrationRequest(
            conversation_id=faq_response.conversation_id,
            message="Thanks, bye",
            close_conversation=True,
        ),
    )
    assert summary_response.agent == AgentType.SUMMARY
    assert summary_response.status == ConversationStatus.CLOSED

    summaries = db_session.query(ConversationSummary).all()
    assert len(summaries) == 1
    assert "lead qualification" in summaries[0].summary


@pytest.mark.asyncio()
async def test_orchestrator_escalates_on_missing_knowledge(db_session):
    _, user = _create_org_user(db_session)
    service = AgentOrchestratorService(
        ConversationRepository(db_session),
        FakeKnowledgeService({}),
    )

    response = await service.process_message(
        user,
        OrchestrationRequest(message="Tell me about your medical advice policy."),
    )

    assert response.agent == AgentType.ESCALATION
    assert response.status == ConversationStatus.ESCALATED
    assert response.escalation_state["reason"]
