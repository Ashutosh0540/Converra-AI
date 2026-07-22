from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID


@dataclass(frozen=True)
class ParsedSection:
    text: str
    page: int


@dataclass(frozen=True)
class TextChunk:
    text: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class VectorSearchResult:
    text: str
    score: float
    metadata: Dict[str, Any]


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: List[str]) -> List[List[float]]: ...

    def embed_query(self, text: str) -> List[float]: ...


class VectorStore(Protocol):
    def add_chunks(
        self,
        organization_id: UUID,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
    ) -> None: ...

    def similarity_search(
        self,
        organization_id: UUID,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]: ...

    def delete_document(self, organization_id: UUID, document_id: UUID) -> None: ...
