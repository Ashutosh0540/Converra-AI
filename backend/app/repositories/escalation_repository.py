from __future__ import annotations

from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.enums import EscalationStatus
from app.models.escalation import EscalationAuditEvent, EscalationCase


class EscalationRepositoryError(Exception):
    """Raised when an escalation database operation fails."""


class EscalationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError(
                "Failed to persist escalation changes."
            ) from exc

    def create_case(self, escalation: EscalationCase) -> EscalationCase:
        try:
            self.db.add(escalation)
            self._commit()
            self.db.refresh(escalation)
            return escalation
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError(
                "Failed to create escalation case."
            ) from exc

    def get_case_by_id(self, escalation_id: UUID) -> Optional[EscalationCase]:
        try:
            statement = select(EscalationCase).where(EscalationCase.id == escalation_id)
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError("Failed to fetch escalation case.") from exc

    def get_case_by_conversation(
        self, conversation_id: UUID
    ) -> Optional[EscalationCase]:
        try:
            statement = select(EscalationCase).where(
                EscalationCase.conversation_id == conversation_id
            )
            return self.db.scalars(statement).first()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError("Failed to fetch escalation case.") from exc

    def list_cases(
        self,
        organization_id: UUID,
        statuses: Optional[Sequence[EscalationStatus]] = None,
    ) -> List[EscalationCase]:
        try:
            statement = select(EscalationCase).where(
                EscalationCase.organization_id == organization_id
            )
            if statuses:
                statement = statement.where(EscalationCase.status.in_(list(statuses)))
            statement = statement.order_by(EscalationCase.last_activity_at.desc())
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError("Failed to list escalation cases.") from exc

    def update_case(self, escalation: EscalationCase) -> EscalationCase:
        try:
            self._commit()
            self.db.refresh(escalation)
            return escalation
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError(
                "Failed to update escalation case."
            ) from exc

    def add_audit_event(self, event: EscalationAuditEvent) -> EscalationAuditEvent:
        try:
            self.db.add(event)
            self._commit()
            self.db.refresh(event)
            return event
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError(
                "Failed to create escalation audit event."
            ) from exc

    def list_audit_events(self, escalation_id: UUID) -> List[EscalationAuditEvent]:
        try:
            statement = (
                select(EscalationAuditEvent)
                .where(EscalationAuditEvent.escalation_id == escalation_id)
                .order_by(EscalationAuditEvent.created_at.asc())
            )
            return list(self.db.scalars(statement).all())
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EscalationRepositoryError(
                "Failed to list escalation audit events."
            ) from exc
