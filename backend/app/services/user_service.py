from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from app.auth.jwt import create_access_token
from app.auth.security import hash_password, hash_token, verify_password
from app.core.config import settings
from app.models.enums import UserRole
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
    RefreshTokenRepositoryError,
)
from app.repositories.user_repository import UserRepository, UserRepositoryError


class UserServiceError(Exception):
    """Base error raised by UserService."""


class UserAlreadyExists(UserServiceError):
    """Raised when a user with the same email already exists."""


class UserNotFound(UserServiceError):
    """Raised when a user cannot be found."""


class OrganizationNotFound(UserServiceError):
    """Raised when a user's organization cannot be found."""


class InactiveUser(UserServiceError):
    """Raised when an operation tries to update an inactive user."""


class InvalidCredentials(UserServiceError):
    """Raised when login credentials are invalid."""


class InvalidRefreshToken(UserServiceError):
    """Raised when a refresh token cannot be used."""


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self.repository = repository
        self.refresh_token_repository = refresh_token_repository

    def _get_user_or_raise(self, user_id: UUID) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound(f"User '{user_id}' was not found.")
        return user

    def create_user(
        self,
        organization_id: UUID,
        full_name: str,
        email: str,
        password: str,
        role: UserRole | None = None,
        is_active: bool = True,
    ) -> User:
        try:
            if self.repository.exists_by_email(email):
                raise UserAlreadyExists(f"User with email '{email}' already exists.")
            if not self.repository.organization_exists(organization_id):
                raise OrganizationNotFound(
                    f"Organization '{organization_id}' was not found."
                )

            user = User(
                organization_id=organization_id,
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                role=role or UserRole.AGENT,
                is_active=is_active,
            )
            return self.repository.create(user)
        except UserRepositoryError as exc:
            raise UserServiceError("Failed to create user.") from exc

    def get_user(self, user_id: UUID) -> User:
        try:
            return self._get_user_or_raise(user_id)
        except UserRepositoryError as exc:
            raise UserServiceError("Failed to fetch user.") from exc

    def list_users(self, organization_id: UUID) -> list[User]:
        try:
            return self.repository.list_by_organization(organization_id)
        except UserRepositoryError as exc:
            raise UserServiceError("Failed to list users.") from exc

    def update_user(
        self,
        user_id: UUID,
        updates: dict[str, Any],
    ) -> User:
        try:
            user = self._get_user_or_raise(user_id)
            if not user.is_active:
                raise InactiveUser(
                    f"User '{user_id}' is inactive and cannot be updated."
                )

            normalized_updates = dict(updates)
            normalized_updates.pop("id", None)

            raw_password = normalized_updates.pop("password", None)
            normalized_updates.pop("password_hash", None)

            if raw_password is not None:
                user.password_hash = hash_password(str(raw_password))

            new_email = normalized_updates.get("email")
            if new_email is not None and new_email != user.email:
                if self.repository.exists_by_email(str(new_email)):
                    raise UserAlreadyExists(
                        f"User with email '{new_email}' already exists."
                    )

            new_organization_id = normalized_updates.get("organization_id")
            if new_organization_id is not None:
                if not self.repository.organization_exists(new_organization_id):
                    raise OrganizationNotFound(
                        f"Organization '{new_organization_id}' was not found."
                    )

            for field_name, field_value in normalized_updates.items():
                if hasattr(user, field_name):
                    setattr(user, field_name, field_value)

            return self.repository.update(user)
        except UserRepositoryError as exc:
            raise UserServiceError("Failed to update user.") from exc

    def delete_user(self, user_id: UUID) -> None:
        try:
            user = self._get_user_or_raise(user_id)
            self.repository.delete(user)
        except UserRepositoryError as exc:
            raise UserServiceError("Failed to delete user.") from exc

    def authenticate_user(self, email: str, password: str) -> User:
        try:
            user = self.repository.get_by_email(email)
            if user is None or not verify_password(password, user.password_hash):
                raise InvalidCredentials("Invalid email or password.")
            if not user.is_active:
                raise InactiveUser("User account is inactive.")

            user.last_login = datetime.now(timezone.utc)
            return self.repository.update(user)
        except UserRepositoryError as exc:
            raise UserServiceError("Failed to authenticate user.") from exc

    def create_token_pair(self, user: User) -> dict[str, str]:
        refresh_token = secrets.token_urlsafe(48)
        refresh_token_hash = hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expiration_days
        )

        try:
            self.refresh_token_repository.create(
                RefreshToken(
                    user_id=user.id,
                    token_hash=refresh_token_hash,
                    expires_at=expires_at,
                )
            )
        except RefreshTokenRepositoryError as exc:
            raise UserServiceError("Failed to create refresh token.") from exc

        return {
            "access_token": self._create_user_access_token(user),
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        refresh_token_hash = hash_token(refresh_token)
        try:
            stored_token = self.refresh_token_repository.get_by_hash(refresh_token_hash)
            if stored_token is None:
                raise InvalidRefreshToken("Refresh token is invalid.")
            if stored_token.revoked_at is not None:
                raise InvalidRefreshToken("Refresh token has been revoked.")
            if self._as_utc(stored_token.expires_at) <= datetime.now(timezone.utc):
                raise InvalidRefreshToken("Refresh token has expired.")

            user = self._get_user_or_raise(stored_token.user_id)
            if not user.is_active:
                raise InactiveUser("User account is inactive.")

            stored_token.revoked_at = datetime.now(timezone.utc)
            self.refresh_token_repository.revoke(stored_token)
            return self.create_token_pair(user)
        except (RefreshTokenRepositoryError, UserRepositoryError) as exc:
            raise UserServiceError("Failed to refresh token.") from exc

    def _create_user_access_token(self, user: User) -> str:
        return create_access_token(
            subject=str(user.id),
            additional_claims={
                "organization_id": str(user.organization_id),
                "role": user.role.value,
            },
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)
