from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.voice import VoiceSession, VoiceTranscript


class VoiceRepositoryError(Exception):
    """Raised when a voice persistence operation fails."""


class VoiceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to persist voice changes.") from exc

    def create_session(self, session: VoiceSession) -> VoiceSession:
        try:
            self.db.add(session)
            self._commit()
            self.db.refresh(session)
            return session
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to create voice session.") from exc

    def get_session(self, session_id: UUID) -> Optional[VoiceSession]:
        try:
            statement = select(VoiceSession).where(VoiceSession.id == session_id)
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to fetch voice session.") from exc

    def list_sessions(self, organization_id: UUID) -> List[VoiceSession]:
        try:
            statement = (
                select(VoiceSession)
                .where(VoiceSession.organization_id == organization_id)
                .order_by(VoiceSession.last_seen_at.desc())
            )
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to list voice sessions.") from exc

    def update_session(self, session: VoiceSession) -> VoiceSession:
        try:
            session.last_seen_at = datetime.now(timezone.utc)
            self._commit()
            self.db.refresh(session)
            return session
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to update voice session.") from exc

    def close_session(self, session: VoiceSession) -> VoiceSession:
        try:
            session.is_active = False
            session.ended_at = datetime.now(timezone.utc)
            self._commit()
            self.db.refresh(session)
            return session
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to close voice session.") from exc

    def add_transcript(self, transcript: VoiceTranscript) -> VoiceTranscript:
        try:
            self.db.add(transcript)
            self._commit()
            self.db.refresh(transcript)
            return transcript
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to create voice transcript.") from exc

    def list_transcripts(self, session_id: UUID) -> List[VoiceTranscript]:
        try:
            statement = (
                select(VoiceTranscript)
                .where(VoiceTranscript.session_id == session_id)
                .order_by(VoiceTranscript.created_at.asc())
            )
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise VoiceRepositoryError("Failed to list voice transcripts.") from exc
