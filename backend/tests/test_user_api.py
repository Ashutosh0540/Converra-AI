from app.auth.security import hash_password
from app.models.enums import UserRole
from app.models.organization import Organization
from app.models.user import User


def test_register_login_me_and_refresh_flow(client, db_session):
    organization = Organization(
        name="Converra",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)

    register_response = client.post(
        "/api/v1/users/register",
        json={
            "organization_id": str(organization.id),
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "strong-password",
            "role": "ADMIN",
        },
    )

    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == "ada@example.com"
    assert "password_hash" not in registered_user

    login_response = client.post(
        "/api/v1/users/login",
        json={
            "email": "ada@example.com",
            "password": "strong-password",
        },
    )

    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["id"] == registered_user["id"]

    refresh_response = client.post(
        "/api/v1/users/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    refreshed_tokens = refresh_response.json()
    assert refreshed_tokens["access_token"]
    assert refreshed_tokens["refresh_token"] != tokens["refresh_token"]

    reused_refresh_response = client.post(
        "/api/v1/users/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert reused_refresh_response.status_code == 401


def test_rbac_allows_admin_and_blocks_viewer(client, db_session):
    organization = Organization(
        name="Converra",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()

    admin = User(
        organization_id=organization.id,
        full_name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    viewer = User(
        organization_id=organization.id,
        full_name="Viewer User",
        email="viewer@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add_all([admin, viewer])
    db_session.commit()

    admin_login = client.post(
        "/api/v1/users/login",
        json={
            "email": "admin@example.com",
            "password": "strong-password",
        },
    )
    viewer_login = client.post(
        "/api/v1/users/login",
        json={
            "email": "viewer@example.com",
            "password": "strong-password",
        },
    )

    admin_token = admin_login.json()["access_token"]
    viewer_token = viewer_login.json()["access_token"]

    admin_list_response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    viewer_list_response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert admin_list_response.status_code == 200
    assert len(admin_list_response.json()) == 2
    assert viewer_list_response.status_code == 403


def test_admin_can_update_and_delete_user(client, db_session):
    organization = Organization(
        name="Converra",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()

    admin = User(
        organization_id=organization.id,
        full_name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    agent = User(
        organization_id=organization.id,
        full_name="Agent User",
        email="agent@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.AGENT,
        is_active=True,
    )
    db_session.add_all([admin, agent])
    db_session.commit()
    db_session.refresh(agent)

    login_response = client.post(
        "/api/v1/users/login",
        json={
            "email": "admin@example.com",
            "password": "strong-password",
        },
    )
    token = login_response.json()["access_token"]

    update_response = client.put(
        f"/api/v1/users/{agent.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Agent", "role": "MANAGER"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Updated Agent"
    assert update_response.json()["role"] == "MANAGER"

    delete_response = client.delete(
        f"/api/v1/users/{agent.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204
