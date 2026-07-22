from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.auth.exceptions import ExpiredTokenError, InvalidTokenError
from app.core.config import settings


def _get_jwt_secret() -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT secret is not configured.")

    return settings.jwt_secret


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expire_delta = expires_delta or timedelta(
        minutes=settings.access_token_expiration_minutes
    )
    expire = datetime.now(timezone.utc) + expire_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if additional_claims is not None:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        _get_jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )


def verify_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("Access token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Access token is invalid.") from exc
