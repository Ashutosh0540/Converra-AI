from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(max_length=255)
    industry: str = Field(max_length=100)
    subscription_plan: str = Field(default="free")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=100)
    subscription_plan: Optional[str] = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    industry: str
    subscription_plan: str
    created_at: datetime
    updated_at: datetime
