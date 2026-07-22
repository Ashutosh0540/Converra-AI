from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepositoryError(Exception):
    """Raised when a refresh token database operation fails."""


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RefreshTokenRepositoryError(
                "Failed to persist refresh token changes."
            ) from exc

    def create(self, refresh_token: RefreshToken) -> RefreshToken:
        try:
            self.db.add(refresh_token)
            self._commit()
            self.db.refresh(refresh_token)
            return refresh_token
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RefreshTokenRepositoryError(
                "Failed to create refresh token."
            ) from exc

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        try:
            statement = select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RefreshTokenRepositoryError("Failed to fetch refresh token.") from exc

    def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        try:
            self._commit()
            self.db.refresh(refresh_token)
            return refresh_token
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RefreshTokenRepositoryError(
                "Failed to revoke refresh token."
            ) from exc

    def revoke_user_tokens(self, user_id: UUID) -> None:
        try:
            statement = select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            revoked_at = datetime.now(timezone.utc)
            for refresh_token in self.db.scalars(statement).all():
                refresh_token.revoked_at = revoked_at
            self._commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RefreshTokenRepositoryError(
                "Failed to revoke user refresh tokens."
            ) from exc
