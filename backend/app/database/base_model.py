from datetime import datetime
from uuid import UUID as PyUUID
from uuid import uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class BaseModel(Base):
    """
    Abstract base model.

    Every database table in Converra AI inherits from this class.
    """

    __abstract__ = True

    id: Mapped[PyUUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
