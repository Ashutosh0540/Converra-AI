from uuid import uuid4

import pytest

from app.auth.security import verify_password
from app.models.enums import UserRole
from app.models.organization import Organization
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import (
    InvalidCredentials,
    UserAlreadyExists,
    UserNotFound,
    UserService,
)


def test_create_user_hashes_password(db_session):
    organization = Organization(
        name="Acme",
        industry="Technology",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)

    service = UserService(
        UserRepository(db_session),
        RefreshTokenRepository(db_session),
    )

    user = service.create_user(
        organization_id=organization.id,
        full_name="Ada Lovelace",
        email="ada@example.com",
        password="strong-password",
        role=UserRole.ADMIN,
    )

    assert user.password_hash != "strong-password"
    assert verify_password("strong-password", user.password_hash)


def test_create_user_rejects_duplicate_email(db_session):
    organization = Organization(
        name="Acme",
        industry="Technology",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    service = UserService(
        UserRepository(db_session),
        RefreshTokenRepository(db_session),
    )
    service.create_user(
        organization_id=organization.id,
        full_name="Ada Lovelace",
        email="ada@example.com",
        password="strong-password",
    )

    with pytest.raises(UserAlreadyExists):
        service.create_user(
            organization_id=organization.id,
            full_name="Grace Hopper",
            email="ada@example.com",
            password="another-password",
        )


def test_authenticate_user_rejects_bad_password(db_session):
    organization = Organization(
        name="Acme",
        industry="Technology",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    service = UserService(
        UserRepository(db_session),
        RefreshTokenRepository(db_session),
    )
    service.create_user(
        organization_id=organization.id,
        full_name="Ada Lovelace",
        email="ada@example.com",
        password="strong-password",
    )

    with pytest.raises(InvalidCredentials):
        service.authenticate_user("ada@example.com", "wrong-password")


def test_get_user_raises_for_missing_user(db_session):
    service = UserService(
        UserRepository(db_session),
        RefreshTokenRepository(db_session),
    )

    with pytest.raises(UserNotFound):
        service.get_user(uuid4())
