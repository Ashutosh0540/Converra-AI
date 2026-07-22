from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.organization import Organization


class OrganizationRepositoryError(Exception):
    """Raised when a database operation in OrganizationRepository fails."""


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _commit(self) -> None:
        try:
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OrganizationRepositoryError(
                "Failed to persist organization changes."
            ) from exc

    def _rollback_and_raise(
        self,
        message: str,
        exc: Exception,
    ) -> None:
        self.session.rollback()
        raise OrganizationRepositoryError(message) from exc

    def create(self, organization: Organization) -> Organization:
        try:
            self.session.add(organization)
            self._commit()
            self.session.refresh(organization)
            return organization
        except SQLAlchemyError as exc:
            self._rollback_and_raise("Failed to create organization.", exc)

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        try:
            statement = select(Organization).where(Organization.id == organization_id)
            return self.session.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OrganizationRepositoryError(
                "Failed to fetch organization by id."
            ) from exc

    def get_all(self) -> list[Organization]:
        try:
            statement = select(Organization)
            return list(self.session.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OrganizationRepositoryError("Failed to fetch organizations.") from exc

    def update(
        self,
        organization_id: UUID,
        updates: dict[str, Any],
    ) -> Organization | None:
        try:
            organization = self.get_by_id(organization_id)
            if organization is None:
                return None

            for field_name, field_value in updates.items():
                if field_name != "id":
                    setattr(organization, field_name, field_value)

            self._commit()
            self.session.refresh(organization)
            return organization
        except SQLAlchemyError as exc:
            self._rollback_and_raise("Failed to update organization.", exc)

    def delete(self, organization_id: UUID) -> bool:
        try:
            organization = self.get_by_id(organization_id)
            if organization is None:
                return False

            self.session.delete(organization)
            self._commit()
            return True
        except SQLAlchemyError as exc:
            self._rollback_and_raise("Failed to delete organization.", exc)

    def exists_by_name(self, name: str) -> bool:
        try:
            statement = select(exists().where(Organization.name == name))
            return bool(self.session.scalar(statement))
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OrganizationRepositoryError(
                "Failed to check if organization exists by name."
            ) from exc
