from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationSummary


class ConversationRepositoryError(Exception):
    """Raised when a conversation database operation fails."""


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ConversationRepositoryError(
                "Failed to persist conversation changes."
            ) from exc

    def create(self, conversation: Conversation) -> Conversation:
        try:
            self.db.add(conversation)
            self._commit()
            self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ConversationRepositoryError("Failed to create conversation.") from exc

    def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        try:
            statement = select(Conversation).where(Conversation.id == conversation_id)
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ConversationRepositoryError("Failed to fetch conversation.") from exc

    def update(self, conversation: Conversation) -> Conversation:
        try:
            self._commit()
            self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ConversationRepositoryError("Failed to update conversation.") from exc

    def list_by_organization(self, organization_id: UUID) -> List[Conversation]:
        try:
            statement = (
                select(Conversation)
                .where(Conversation.organization_id == organization_id)
                .order_by(Conversation.started_at.desc())
            )
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ConversationRepositoryError("Failed to list conversations.") from exc

    def add_summary(self, summary: ConversationSummary) -> ConversationSummary:
        try:
            self.db.add(summary)
            self._commit()
            self.db.refresh(summary)
            return summary
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ConversationRepositoryError(
                "Failed to create conversation summary."
            ) from exc

    def list_summaries(
        self,
        conversation_id: UUID,
    ) -> List[ConversationSummary]:
        try:
            statement = (
                select(ConversationSummary)
                .where(ConversationSummary.conversation_id == conversation_id)
                .order_by(ConversationSummary.created_at.desc())
            )
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise ConversationRepositoryError(
                "Failed to list conversation summaries."
            ) from exc
