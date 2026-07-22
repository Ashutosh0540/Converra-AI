from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import settings
from app.services.knowledge_types import TextChunk, VectorSearchResult


class VectorStoreError(Exception):
    """Raised when vector store operations fail."""


class ChromaVectorStore:
    def __init__(self, persist_path: Optional[str] = None) -> None:
        self.persist_path = persist_path or settings.chroma_path
        self._client = None

    def add_chunks(
        self,
        organization_id: UUID,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
    ) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise VectorStoreError("Chunk and embedding counts do not match.")

        try:
            collection = self._get_collection(organization_id)
            collection.add(
                ids=[self._chunk_id(chunk) for chunk in chunks],
                documents=[chunk.text for chunk in chunks],
                embeddings=embeddings,
                metadatas=[chunk.metadata for chunk in chunks],
            )
        except Exception as exc:
            raise VectorStoreError("Failed to store knowledge chunks.") from exc

    def similarity_search(
        self,
        organization_id: UUID,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        try:
            collection = self._get_collection(organization_id)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters,
                include=["documents", "metadatas", "distances"],
            )
            return self._map_results(results)
        except Exception as exc:
            raise VectorStoreError("Failed to search knowledge chunks.") from exc

    def delete_document(self, organization_id: UUID, document_id: UUID) -> None:
        try:
            collection = self._get_collection(organization_id)
            collection.delete(where={"document_id": str(document_id)})
        except Exception as exc:
            raise VectorStoreError("Failed to delete knowledge chunks.") from exc

    def _get_client(self):
        if self._client is None:
            try:
                import chromadb
            except ImportError as exc:
                raise VectorStoreError("ChromaDB dependency is missing.") from exc

            self._client = chromadb.PersistentClient(path=self.persist_path)

        return self._client

    def _get_collection(self, organization_id: UUID):
        return self._get_client().get_or_create_collection(
            name=self._collection_name(organization_id),
            metadata={"organization_id": str(organization_id)},
        )

    @staticmethod
    def _collection_name(organization_id: UUID) -> str:
        return f"org_{str(organization_id).replace('-', '_')}"

    @staticmethod
    def _chunk_id(chunk: TextChunk) -> str:
        return f"{chunk.metadata['document_id']}:" f"{chunk.metadata['chunk_number']}"

    @staticmethod
    def _map_results(results: Dict[str, Any]) -> List[VectorSearchResult]:
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        mapped_results: List[VectorSearchResult] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            score = 1.0 / (1.0 + float(distance))
            mapped_results.append(
                VectorSearchResult(
                    text=text,
                    score=score,
                    metadata=metadata or {},
                )
            )

        return mapped_results
