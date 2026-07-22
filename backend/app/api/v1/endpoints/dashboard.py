from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket

from app.api.dependencies import get_user_service
from app.auth.exceptions import AuthenticationError
from app.auth.jwt import verify_access_token
from app.services.user_service import InactiveUser, UserNotFound, UserService

router = APIRouter(tags=["Dashboard"])


@router.websocket("/ws/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Provide authenticated dashboard connection health and refresh heartbeats."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        _authenticate(token, user_service)
    except AuthenticationError:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    try:
        while True:
            await websocket.send_json(
                {"type": "dashboard_sync", "message": "Dashboard data refreshed."}
            )
            await asyncio.sleep(15)
    except Exception:
        await websocket.close()


def _authenticate(token: str, user_service: UserService) -> None:
    payload = verify_access_token(token)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthenticationError("Token subject is invalid.")
    try:
        user = user_service.get_user(UUID(subject))
    except (ValueError, UserNotFound, InactiveUser) as exc:
        raise AuthenticationError("Could not validate credentials.") from exc
    if not user.is_active:
        raise AuthenticationError("User account is inactive.")
