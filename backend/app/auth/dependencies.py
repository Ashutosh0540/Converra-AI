from __future__ import annotations

from typing import Annotated, Callable, Optional
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies import get_user_service
from app.auth.exceptions import (
    AuthenticationError,
    ForbiddenError,
    MissingTokenError,
    UnauthorizedError,
)
from app.auth.jwt import verify_access_token
from app.models.enums import UserRole
from app.models.user import User
from app.services.user_service import InactiveUser, UserNotFound, UserService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise MissingTokenError("Access token is required.")

    token = credentials.credentials
    try:
        payload = verify_access_token(token)
    except AuthenticationError as exc:
        raise UnauthorizedError("Could not validate credentials.") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise UnauthorizedError("Token subject is invalid.")

    try:
        user = user_service.get_user(UUID(subject))
        if not user.is_active:
            raise InactiveUser("User account is inactive.")
    except (ValueError, UserNotFound, InactiveUser) as exc:
        raise UnauthorizedError("Could not validate credentials.") from exc

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    def role_dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError("Insufficient permissions.")

        return current_user

    return role_dependency
