from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organization_service import (
    OrganizationAlreadyExistsError,
    OrganizationNotFoundError,
    OrganizationService,
    OrganizationServiceError,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def get_organization_repository(
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationRepository:
    return OrganizationRepository(db)


def get_organization_service(
    repository: Annotated[
        OrganizationRepository,
        Depends(get_organization_repository),
    ],
) -> OrganizationService:
    return OrganizationService(repository)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    payload: OrganizationCreate,
    service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> Organization:
    try:
        return service.create_organization(
            name=payload.name,
            industry=payload.industry,
            subscription_plan=payload.subscription_plan,
        )
    except OrganizationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except OrganizationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> list[Organization]:
    try:
        return service.list_organizations()
    except OrganizationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: UUID,
    service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> Organization:
    try:
        organization = service.get_organization(organization_id)
        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found.",
            )

        return organization
    except OrganizationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.put("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> Organization:
    try:
        updated_organization = service.update_organization(
            organization_id=organization_id,
            updates=payload.model_dump(exclude_unset=True),
        )
        return updated_organization
    except OrganizationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrganizationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except OrganizationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: UUID,
    service: Annotated[
        OrganizationService,
        Depends(get_organization_service),
    ],
) -> None:
    try:
        service.delete_organization(organization_id)
    except OrganizationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except OrganizationServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
