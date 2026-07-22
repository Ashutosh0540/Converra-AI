from __future__ import annotations

from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User


class UserRepositoryError(Exception):
    """Raised when a database operation in UserRepository fails."""


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise UserRepositoryError("Failed to persist user changes.") from exc

    def _rollback_and_raise(self, message: str, exc: Exception) -> None:
        self.db.rollback()
        raise UserRepositoryError(message) from exc

    def create(self, user: User) -> User:
        try:
            self.db.add(user)
            self._commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as exc:
            self._rollback_and_raise("Failed to create user.", exc)

    def get_by_id(self, user_id: UUID) -> User | None:
        try:
            statement = select(User).where(User.id == user_id)
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise UserRepositoryError("Failed to fetch user by id.") from exc

    def get_by_email(self, email: str) -> User | None:
        try:
            statement = select(User).where(User.email == email)
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise UserRepositoryError("Failed to fetch user by email.") from exc

    def list_by_organization(self, organization_id: UUID) -> list[User]:
        try:
            statement = select(User).where(User.organization_id == organization_id)
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise UserRepositoryError("Failed to list users by organization.") from exc

    def update(self, user: User) -> User:
        try:
            self._commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as exc:
            self._rollback_and_raise("Failed to update user.", exc)

    def delete(self, user: User) -> None:
        try:
            self.db.delete(user)
            self._commit()
        except SQLAlchemyError as exc:
            self._rollback_and_raise("Failed to delete user.", exc)

    def exists_by_email(self, email: str) -> bool:
        try:
            statement = select(exists().where(User.email == email))
            return bool(self.db.scalar(statement))
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise UserRepositoryError(
                "Failed to check if user exists by email."
            ) from exc

    def organization_exists(self, organization_id: UUID) -> bool:
        try:
            statement = select(exists().where(Organization.id == organization_id))
            return bool(self.db.scalar(statement))
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise UserRepositoryError(
                "Failed to check if organization exists."
            ) from exc
