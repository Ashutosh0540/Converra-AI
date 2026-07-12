from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.organization import Organization


class OrganizationRepositoryError(Exception):
    """Raised when a database operation in OrganizationRepository fails."""


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, organization: Organization) -> Organization:
        try:
            self.session.add(organization)
            self.session.commit()
            self.session.refresh(organization)
            return organization
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OrganizationRepositoryError(
                "Failed to create organization."
            ) from exc

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        try:
            statement = select(Organization).where(
                Organization.id == organization_id
            )
            return self.session.scalars(statement).first()
        except SQLAlchemyError as exc:
            raise OrganizationRepositoryError(
                "Failed to fetch organization by id."
            ) from exc

    def get_all(self) -> list[Organization]:
        try:
            statement = select(Organization)
            return list(self.session.scalars(statement).all())
        except SQLAlchemyError as exc:
            raise OrganizationRepositoryError(
                "Failed to fetch organizations."
            ) from exc

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

            self.session.commit()
            self.session.refresh(organization)
            return organization
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OrganizationRepositoryError(
                "Failed to update organization."
            ) from exc

    def delete(self, organization_id: UUID) -> bool:
        try:
            organization = self.get_by_id(organization_id)
            if organization is None:
                return False

            self.session.delete(organization)
            self.session.commit()
            return True
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OrganizationRepositoryError(
                "Failed to delete organization."
            ) from exc