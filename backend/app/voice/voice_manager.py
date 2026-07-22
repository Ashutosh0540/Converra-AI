from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID

from app.voice.voice_session import VoiceSessionContext


@dataclass
class VoiceConnectionState:
    session: VoiceSessionContext
    reply_task: Optional[asyncio.Task] = None
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class VoiceManager:
    def __init__(self) -> None:
        self._connections: Dict[UUID, VoiceConnectionState] = {}
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def register(self, session: VoiceSessionContext) -> VoiceConnectionState:
        async with self._get_lock():
            state = self._connections.get(session.session_id)
            if state is None:
                state = VoiceConnectionState(session=session)
                self._connections[session.session_id] = state
            else:
                state.session = session
            return state

    async def get(self, session_id: UUID) -> Optional[VoiceConnectionState]:
        async with self._get_lock():
            return self._connections.get(session_id)

    async def remove(self, session_id: UUID) -> None:
        async with self._get_lock():
            self._connections.pop(session_id, None)

    async def cancel_reply(self, session_id: UUID) -> None:
        state = await self.get(session_id)
        if state and state.reply_task and not state.reply_task.done():
            state.reply_task.cancel()
            try:
                await state.reply_task
            except asyncio.CancelledError:
                pass
