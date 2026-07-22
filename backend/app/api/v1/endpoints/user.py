from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_user_service
from app.auth.dependencies import get_current_user, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    UserCreate,
    UserLogin,
    UserResponse,
    UserToken,
    UserUpdate,
)
from app.services.user_service import (
    InactiveUser,
    InvalidCredentials,
    InvalidRefreshToken,
    OrganizationNotFound,
    UserAlreadyExists,
    UserNotFound,
    UserService,
    UserServiceError,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
def register_user(
    payload: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    try:
        return service.create_user(
            organization_id=payload.organization_id,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except UserAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except OrganizationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=UserToken, summary="Log in a user")
def login_user(
    payload: UserLogin,
    service: Annotated[UserService, Depends(get_user_service)],
) -> dict[str, str]:
    try:
        user = service.authenticate_user(payload.email, payload.password)
        return service.create_token_pair(user)
    except (InvalidCredentials, InactiveUser) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/refresh", response_model=UserToken, summary="Refresh tokens")
def refresh_user_token(
    payload: RefreshTokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> dict[str, str]:
    try:
        return service.refresh_access_token(payload.refresh_token)
    except (InvalidRefreshToken, InactiveUser, UserNotFound) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/me", response_model=UserResponse, summary="Get current user")
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List organization users",
)
def list_users(
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> list[User]:
    try:
        return service.list_users(current_user.organization_id)
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user",
)
def get_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    try:
        user = service.get_user(user_id)
        if not _can_access_user(current_user, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return user
    except UserNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    try:
        user = service.get_user(user_id)
        if not _is_same_organization(current_user, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        if current_user.role == UserRole.MANAGER and user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return service.update_user(
            user_id=user_id,
            updates=payload.model_dump(exclude_unset=True),
        )
    except UserNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UserAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except OrganizationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (InactiveUser, UserServiceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
def delete_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    try:
        user = service.get_user(user_id)
        if not _is_same_organization(current_user, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        service.delete_user(user_id)
    except UserNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


def _is_same_organization(current_user: User, target_user: User) -> bool:
    return current_user.organization_id == target_user.organization_id


def _can_access_user(current_user: User, target_user: User) -> bool:
    if current_user.id == target_user.id:
        return True
    if current_user.role in {UserRole.ADMIN, UserRole.MANAGER}:
        return _is_same_organization(current_user, target_user)

    return False
