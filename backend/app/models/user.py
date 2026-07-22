from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_model import BaseModel
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument
    from app.models.organization import Organization
    from app.models.refresh_token import RefreshToken


class User(BaseModel):
    __tablename__ = "users"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        index=True,
        unique=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.AGENT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship(back_populates="users")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    knowledge_documents: Mapped[List["KnowledgeDocument"]] = relationship(
        back_populates="uploader",
        cascade="all, delete-orphan",
    )
