from __future__ import annotations

from typing import Any
from uuid import UUID

from app.models.organization import Organization
from app.repositories.organization_repository import (
    OrganizationRepository,
    OrganizationRepositoryError,
)


class OrganizationServiceError(Exception):
    """Base error raised by OrganizationService."""


class OrganizationAlreadyExistsError(OrganizationServiceError):
    """Raised when an organization name already exists."""


class OrganizationNotFoundError(OrganizationServiceError):
    """Raised when an organization cannot be found."""


class OrganizationService:
    def __init__(self, repository: OrganizationRepository) -> None:
        self.repository = repository

    def create_organization(
        self,
        name: str,
        industry: str,
        subscription_plan: str = "free",
    ) -> Organization:
        try:
            if self.repository.exists_by_name(name):
                raise OrganizationAlreadyExistsError(
                    f"Organization with name '{name}' already exists."
                )

            organization = Organization(
                name=name,
                industry=industry,
                subscription_plan=subscription_plan,
            )
            return self.repository.create(organization)
        except OrganizationRepositoryError as exc:
            raise OrganizationServiceError("Failed to create organization.") from exc

    def get_organization(self, organization_id: UUID) -> Organization | None:
        try:
            return self.repository.get_by_id(organization_id)
        except OrganizationRepositoryError as exc:
            raise OrganizationServiceError("Failed to fetch organization.") from exc

    def list_organizations(self) -> list[Organization]:
        try:
            return self.repository.get_all()
        except OrganizationRepositoryError as exc:
            raise OrganizationServiceError("Failed to list organizations.") from exc

    def update_organization(
        self,
        organization_id: UUID,
        updates: dict[str, Any],
    ) -> Organization:
        try:
            current_organization = self.repository.get_by_id(organization_id)
            if current_organization is None:
                raise OrganizationNotFoundError(
                    f"Organization '{organization_id}' was not found."
                )

            normalized_updates = dict(updates)
            normalized_updates.pop("id", None)

            new_name = normalized_updates.get("name")
            if new_name is not None and new_name != current_organization.name:
                if self.repository.exists_by_name(new_name):
                    raise OrganizationAlreadyExistsError(
                        f"Organization with name '{new_name}' already exists."
                    )

            updated_organization = self.repository.update(
                organization_id,
                normalized_updates,
            )
            if updated_organization is None:
                raise OrganizationNotFoundError(
                    f"Organization '{organization_id}' was not found."
                )

            return updated_organization
        except OrganizationRepositoryError as exc:
            raise OrganizationServiceError("Failed to update organization.") from exc

    def delete_organization(self, organization_id: UUID) -> bool:
        try:
            deleted = self.repository.delete(organization_id)
            if not deleted:
                raise OrganizationNotFoundError(
                    f"Organization '{organization_id}' was not found."
                )

            return True
        except OrganizationRepositoryError as exc:
            raise OrganizationServiceError("Failed to delete organization.") from exc
