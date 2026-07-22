from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_orchestrator_service
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import (
    AIResponse,
    ConversationListItem,
    EscalationRequest,
    EscalationResponse,
    LeadQualificationRequest,
    LeadQualificationResponse,
    OrchestrationRequest,
    SchedulingRequest,
    SchedulingResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.orchestration_service import (
    AgentOrchestratorService,
    ConversationNotFound,
    OrchestrationServiceError,
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get(
    "/conversations",
    response_model=List[ConversationListItem],
    summary="List organization conversations",
)
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentOrchestratorService, Depends(get_orchestrator_service)],
) -> List[ConversationListItem]:
    try:
        return await service.list_conversations(current_user.organization_id)
    except OrchestrationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/chat", response_model=AIResponse, summary="Route a conversation")
async def chat(
    payload: OrchestrationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentOrchestratorService, Depends(get_orchestrator_service)],
) -> AIResponse:
    try:
        return await service.process_message(current_user, payload)
    except ConversationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrchestrationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/summary", response_model=SummaryResponse, summary="Summarize a conversation"
)
async def summary(
    payload: SummaryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentOrchestratorService, Depends(get_orchestrator_service)],
) -> SummaryResponse:
    try:
        conversation = service.get_conversation(payload.conversation_id)
        if conversation.organization_id != current_user.organization_id:
            raise ConversationNotFound(
                f"Conversation '{payload.conversation_id}' was not found."
            )
        return await service.generate_summary(conversation, current_user)
    except ConversationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrchestrationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/escalate", response_model=EscalationResponse, summary="Escalate a conversation"
)
async def escalate(
    payload: EscalationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentOrchestratorService, Depends(get_orchestrator_service)],
) -> EscalationResponse:
    try:
        return await service.escalate(
            current_user=current_user,
            conversation_id=payload.conversation_id,
            reason=payload.reason,
            message=payload.message,
        )
    except ConversationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrchestrationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/qualify",
    response_model=LeadQualificationResponse,
    summary="Run lead qualification",
)
async def qualify(
    payload: LeadQualificationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentOrchestratorService, Depends(get_orchestrator_service)],
) -> LeadQualificationResponse:
    try:
        return await service.run_lead_qualification(
            current_user=current_user,
            conversation_id=payload.conversation_id,
            message=payload.message,
        )
    except ConversationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrchestrationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/schedule", response_model=SchedulingResponse, summary="Run scheduling")
async def schedule(
    payload: SchedulingRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentOrchestratorService, Depends(get_orchestrator_service)],
) -> SchedulingResponse:
    try:
        return await service.run_scheduling(
            current_user=current_user,
            conversation_id=payload.conversation_id,
            message=payload.message,
        )
    except ConversationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrchestrationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
