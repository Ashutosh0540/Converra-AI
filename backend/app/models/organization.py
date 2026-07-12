from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base_model import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_plan: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="free",
    )