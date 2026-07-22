from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    uploader_id: UUID
    filename: str
    content_type: str
    file_size: int
    source: str
    status: DocumentStatus
    upload_time: datetime
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=25)
    filters: Optional[Dict[str, Any]] = None


class KnowledgeCitation(BaseModel):
    document_id: str
    document: str
    page: int
    chunk_number: int
    source: str


class KnowledgeSearchResult(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]
    citation: KnowledgeCitation


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[KnowledgeSearchResult]
