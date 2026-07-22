from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_escalation_service
from app.auth.dependencies import get_current_user, require_roles
from app.models.enums import EscalationStatus, UserRole
from app.models.user import User
from app.schemas.escalation import (
    EscalationActionRequest,
    EscalationActionResponse,
    EscalationAssignRequest,
    EscalationDetailResponse,
    EscalationHumanReplyRequest,
    EscalationListResponse,
    EscalationQueueResponse,
)
from app.services.escalation_service import (
    EscalationNotFound,
    EscalationPermissionDenied,
    EscalationService,
    EscalationServiceError,
)

router = APIRouter(tags=["Escalations"])


@router.get(
    "/escalations",
    response_model=EscalationListResponse,
    summary="List escalation cases",
)
def list_escalations(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
    status_filter: Optional[EscalationStatus] = None,
) -> EscalationListResponse:
    try:
        statuses = (status_filter,) if status_filter is not None else None
        queue = service.list_escalations(
            organization_id=current_user.organization_id,
            statuses=statuses,
        )
        return EscalationListResponse(items=queue.items)
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/escalations/{escalation_id}",
    response_model=EscalationDetailResponse,
    summary="Get escalation details",
)
def get_escalation(
    escalation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationDetailResponse:
    try:
        return service.get_escalation(
            organization_id=current_user.organization_id,
            escalation_id=escalation_id,
            current_user=current_user,
        )
    except EscalationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/escalations/{escalation_id}/assign",
    response_model=EscalationActionResponse,
    summary="Assign or reassign an escalation",
)
def assign_escalation(
    escalation_id: UUID,
    payload: EscalationAssignRequest,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT)),
    ],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationActionResponse:
    try:
        return service.assign_escalation(
            organization_id=current_user.organization_id,
            escalation_id=escalation_id,
            assignee_user_id=payload.assignee_user_id,
            actor=current_user,
            notes=payload.notes,
            priority=payload.priority,
        )
    except EscalationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except EscalationPermissionDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/escalations/{escalation_id}/transfer",
    response_model=EscalationActionResponse,
    summary="Transfer an escalation",
)
def transfer_escalation(
    escalation_id: UUID,
    payload: EscalationAssignRequest,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT)),
    ],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationActionResponse:
    try:
        return service.transfer_escalation(
            organization_id=current_user.organization_id,
            escalation_id=escalation_id,
            assignee_user_id=payload.assignee_user_id,
            actor=current_user,
            notes=payload.notes,
        )
    except EscalationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except EscalationPermissionDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/escalations/{escalation_id}/accept",
    response_model=EscalationActionResponse,
    summary="Accept an escalation and pause AI",
)
def accept_escalation(
    escalation_id: UUID,
    payload: EscalationActionRequest,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT)),
    ],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationActionResponse:
    try:
        return service.accept_escalation(
            organization_id=current_user.organization_id,
            escalation_id=escalation_id,
            actor=current_user,
            notes=payload.notes,
        )
    except EscalationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except EscalationPermissionDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/escalations/{escalation_id}/reply",
    response_model=EscalationActionResponse,
    summary="Record a human reply and continue takeover",
)
def add_human_reply(
    escalation_id: UUID,
    payload: EscalationHumanReplyRequest,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT)),
    ],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationActionResponse:
    try:
        return service.add_human_reply(
            organization_id=current_user.organization_id,
            escalation_id=escalation_id,
            actor=current_user,
            payload=payload,
        )
    except EscalationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except EscalationPermissionDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/escalations/{escalation_id}/resolve",
    response_model=EscalationActionResponse,
    summary="Resolve an escalation",
)
def resolve_escalation(
    escalation_id: UUID,
    payload: EscalationActionRequest,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT)),
    ],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationActionResponse:
    try:
        return service.resolve_escalation(
            organization_id=current_user.organization_id,
            escalation_id=escalation_id,
            actor=current_user,
            notes=payload.notes,
        )
    except EscalationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/escalations/{escalation_id}/close",
    response_model=EscalationActionResponse,
    summary="Close an escalation",
)
def close_escalation(
    escalation_id: UUID,
    payload: EscalationActionRequest,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT)),
    ],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationActionResponse:
    try:
        return service.close_escalation(
            organization_id=current_user.organization_id,
            escalation_id=escalation_id,
            actor=current_user,
            notes=payload.notes,
        )
    except EscalationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/dashboard/queue",
    response_model=EscalationQueueResponse,
    summary="Get active human queue",
)
def get_dashboard_queue(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[EscalationService, Depends(get_escalation_service)],
) -> EscalationQueueResponse:
    try:
        return service.get_dashboard_queue(current_user.organization_id)
    except EscalationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
