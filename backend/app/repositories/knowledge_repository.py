from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument


class KnowledgeRepositoryError(Exception):
    """Raised when a knowledge document database operation fails."""


class KnowledgeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise KnowledgeRepositoryError(
                "Failed to persist knowledge document changes."
            ) from exc

    def create(self, document: KnowledgeDocument) -> KnowledgeDocument:
        try:
            self.db.add(document)
            self._commit()
            self.db.refresh(document)
            return document
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise KnowledgeRepositoryError(
                "Failed to create knowledge document."
            ) from exc

    def get_by_id(self, document_id: UUID) -> Optional[KnowledgeDocument]:
        try:
            statement = select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id
            )
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise KnowledgeRepositoryError(
                "Failed to fetch knowledge document."
            ) from exc

    def list_by_organization(
        self,
        organization_id: UUID,
    ) -> List[KnowledgeDocument]:
        try:
            statement = (
                select(KnowledgeDocument)
                .where(KnowledgeDocument.organization_id == organization_id)
                .order_by(KnowledgeDocument.upload_time.desc())
            )
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise KnowledgeRepositoryError(
                "Failed to list knowledge documents."
            ) from exc

    def update(self, document: KnowledgeDocument) -> KnowledgeDocument:
        try:
            self._commit()
            self.db.refresh(document)
            return document
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise KnowledgeRepositoryError(
                "Failed to update knowledge document."
            ) from exc

    def delete(self, document: KnowledgeDocument) -> None:
        try:
            self.db.delete(document)
            self._commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise KnowledgeRepositoryError(
                "Failed to delete knowledge document."
            ) from exc
