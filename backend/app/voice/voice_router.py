from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.api.dependencies import get_user_service, get_voice_service
from app.auth.dependencies import get_current_user
from app.auth.exceptions import AuthenticationError
from app.auth.jwt import verify_access_token
from app.models.user import User
from app.schemas.voice import (
    VoiceHistoryResponse,
    VoiceSessionEndRequest,
    VoiceSessionEndResponse,
    VoiceSessionListItem,
    VoiceSessionStartRequest,
    VoiceSessionStartResponse,
    VoiceWebSocketEvent,
    VoiceWebSocketMessage,
)
from app.services.user_service import InactiveUser, UserNotFound, UserService
from app.voice.audio_stream import encode_audio_base64
from app.voice.voice_service import (
    VoiceService,
    VoiceServiceError,
    VoiceSessionNotFound,
)

router = APIRouter(tags=["Voice"])


@router.get(
    "/voice/sessions",
    response_model=list[VoiceSessionListItem],
    summary="List organization voice sessions",
)
async def list_voice_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[VoiceService, Depends(get_voice_service)],
) -> list[VoiceSessionListItem]:
    try:
        return await service.list_sessions(current_user)
    except VoiceServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/voice/session/start",
    response_model=VoiceSessionStartResponse,
    summary="Start a voice session",
)
async def start_voice_session(
    payload: VoiceSessionStartRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[VoiceService, Depends(get_voice_service)],
) -> VoiceSessionStartResponse:
    try:
        return await service.start_session(
            current_user=current_user,
            conversation_id=payload.conversation_id,
            session_id=payload.session_id,
        )
    except VoiceSessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except VoiceServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/voice/session/end",
    response_model=VoiceSessionEndResponse,
    summary="End a voice session",
)
async def end_voice_session(
    payload: VoiceSessionEndRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[VoiceService, Depends(get_voice_service)],
) -> VoiceSessionEndResponse:
    try:
        return await service.end_session(
            current_user=current_user,
            session_id=payload.session_id,
        )
    except VoiceSessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except VoiceServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/voice/history",
    response_model=VoiceHistoryResponse,
    summary="List voice transcript history",
)
async def get_voice_history(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[VoiceService, Depends(get_voice_service)],
) -> VoiceHistoryResponse:
    try:
        return await service.history(current_user=current_user, session_id=session_id)
    except VoiceSessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except VoiceServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
    user_service: Annotated[UserService, Depends(get_user_service)],
    voice_service: Annotated[VoiceService, Depends(get_voice_service)],
) -> None:
    token = websocket.query_params.get("token")
    session_id_raw = websocket.query_params.get("session_id")
    conversation_id_raw = websocket.query_params.get("conversation_id")

    if not token:
        await websocket.close(code=4401)
        return

    try:
        current_user = _authenticate_websocket(token, user_service)
    except AuthenticationError:
        await websocket.close(code=4401)
        return
    await websocket.accept()

    try:
        session = await voice_service.start_session(
            current_user=current_user,
            conversation_id=UUID(conversation_id_raw) if conversation_id_raw else None,
            session_id=UUID(session_id_raw) if session_id_raw else None,
        )
        await websocket.send_json(
            VoiceWebSocketEvent(
                type="session_started",
                session_id=session.session_id,
                payload=session.model_dump(mode="json"),
            ).model_dump(mode="json")
        )

        while True:
            raw_message = await websocket.receive_json()
            message = VoiceWebSocketMessage.model_validate(raw_message)

            if (
                message.session_id is not None
                and message.session_id != session.session_id
            ):
                await websocket.send_json(
                    VoiceWebSocketEvent(
                        type="error",
                        session_id=session.session_id,
                        payload={"detail": "Session mismatch."},
                    ).model_dump(mode="json")
                )
                continue

            if message.type in {"interrupt", "barge_in"}:
                await voice_service.manager.cancel_reply(session.session_id)
                await websocket.send_json(
                    VoiceWebSocketEvent(
                        type="interrupted",
                        session_id=session.session_id,
                        payload={"status": "canceled"},
                    ).model_dump(mode="json")
                )
                continue

            if message.type == "end":
                end_response = await voice_service.end_session(
                    current_user=current_user,
                    session_id=session.session_id,
                )
                await websocket.send_json(
                    VoiceWebSocketEvent(
                        type="session_ended",
                        session_id=end_response.session_id,
                        payload=end_response.model_dump(mode="json"),
                    ).model_dump(mode="json")
                )
                await websocket.close()
                return

            if message.type not in {"audio", "transcript", "text"}:
                await websocket.send_json(
                    VoiceWebSocketEvent(
                        type="error",
                        session_id=session.session_id,
                        payload={
                            "detail": f"Unsupported message type '{message.type}'."
                        },
                    ).model_dump(mode="json")
                )
                continue

            await voice_service.manager.cancel_reply(session.session_id)
            await websocket.send_json(
                VoiceWebSocketEvent(
                    type=(
                        "transcript_partial"
                        if not message.is_final
                        else "transcript_final"
                    ),
                    session_id=session.session_id,
                    payload={"text": message.text or "", "is_final": message.is_final},
                ).model_dump(mode="json")
            )

            turn_result = await voice_service.process_voice_input(
                current_user=current_user,
                session_id=session.session_id,
                audio_base64=message.audio_base64,
                text=message.text,
                is_final=message.is_final,
                close_conversation=message.close_conversation,
            )
            if turn_result.ai_response.structured_data.get("human_mode"):
                await websocket.send_json(
                    VoiceWebSocketEvent(
                        type="human_takeover",
                        session_id=session.session_id,
                        payload={
                            "conversation_id": str(
                                turn_result.ai_response.conversation_id
                            ),
                            "status": "IN_PROGRESS",
                            "transcript": turn_result.transcript,
                        },
                    ).model_dump(mode="json")
                )
                continue
            await websocket.send_json(
                VoiceWebSocketEvent(
                    type="ai_response",
                    session_id=session.session_id,
                    payload={
                        "response": turn_result.ai_response.model_dump(mode="json"),
                        "latency": {
                            "transcription_ms": turn_result.transcription_latency_ms,
                            "llm_ms": turn_result.llm_latency_ms,
                            "tts_ms": turn_result.tts_latency_ms,
                            "total_ms": turn_result.total_latency_ms,
                        },
                    },
                ).model_dump(mode="json")
            )
            for index, audio_chunk in enumerate(turn_result.audio_chunks):
                await websocket.send_json(
                    VoiceWebSocketEvent(
                        type="audio_chunk",
                        session_id=session.session_id,
                        payload={
                            "chunk_index": index,
                            "audio_base64": encode_audio_base64(audio_chunk),
                            "is_final": index + 1 == len(turn_result.audio_chunks),
                        },
                    ).model_dump(mode="json")
                )
    except VoiceSessionNotFound as exc:
        await websocket.send_json(
            VoiceWebSocketEvent(
                type="error",
                session_id=(
                    session.session_id
                    if "session" in locals()
                    else UUID("00000000-0000-0000-0000-000000000000")
                ),
                payload={"detail": str(exc)},
            ).model_dump(mode="json")
        )
        await websocket.close(code=4404)
    except WebSocketDisconnect:
        if "session" in locals():
            await voice_service.manager.cancel_reply(session.session_id)
    except Exception as exc:  # pragma: no cover - websocket safety net
        await websocket.send_json(
            VoiceWebSocketEvent(
                type="error",
                session_id=(
                    session.session_id
                    if "session" in locals()
                    else UUID("00000000-0000-0000-0000-000000000000")
                ),
                payload={"detail": str(exc)},
            ).model_dump(mode="json")
        )
        await websocket.close(code=1011)


def _authenticate_websocket(token: str, user_service: UserService) -> User:
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

    return user
