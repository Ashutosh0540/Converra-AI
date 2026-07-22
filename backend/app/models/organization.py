from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument
    from app.models.user import User


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_plan: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="free",
    )
    users: Mapped[List["User"]] = relationship(back_populates="organization")
    knowledge_documents: Mapped[List["KnowledgeDocument"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )
