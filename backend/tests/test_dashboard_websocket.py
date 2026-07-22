from app.auth.security import hash_password
from app.models.enums import UserRole
from app.models.organization import Organization
from app.models.user import User


def test_dashboard_websocket_authenticates_and_emits_refresh_heartbeat(
    client, db_session
):
    organization = Organization(
        name="Dashboard Org",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()
    user = User(
        organization_id=organization.id,
        full_name="Dashboard Admin",
        email="dashboard@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    login = client.post(
        "/api/v1/users/login",
        json={"email": "dashboard@example.com", "password": "strong-password"},
    )
    token = login.json()["access_token"]
    with client.websocket_connect(f"/ws/dashboard?token={token}") as websocket:
        event = websocket.receive_json()
        assert event["type"] == "dashboard_sync"
