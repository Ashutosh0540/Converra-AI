from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.enums import DocumentStatus, UserRole
from app.models.organization import Organization
from app.models.user import User
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.document_parser import DocumentParser
from app.services.knowledge_service import KnowledgeService
from app.services.knowledge_types import TextChunk, VectorSearchResult
from app.services.text_splitter import RecursiveCharacterTextSplitter


class FakeEmbeddingProvider:
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[float(len(text)), 1.0] for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return [float(len(text)), 1.0]


class FakeVectorStore:
    def __init__(self) -> None:
        self.chunks: Dict[UUID, List[TextChunk]] = {}

    def add_chunks(
        self,
        organization_id: UUID,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
    ) -> None:
        self.chunks.setdefault(organization_id, []).extend(chunks)

    def similarity_search(
        self,
        organization_id: UUID,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        results: List[VectorSearchResult] = []
        for chunk in self.chunks.get(organization_id, []):
            if filters and any(
                chunk.metadata.get(key) != value for key, value in filters.items()
            ):
                continue
            results.append(
                VectorSearchResult(
                    text=chunk.text,
                    score=0.99,
                    metadata=chunk.metadata,
                )
            )

        return results[:top_k]

    def delete_document(self, organization_id: UUID, document_id: UUID) -> None:
        self.chunks[organization_id] = [
            chunk
            for chunk in self.chunks.get(organization_id, [])
            if chunk.metadata["document_id"] != str(document_id)
        ]


def test_upload_document_chunks_embeds_and_stores_metadata(db_session):
    organization = Organization(
        name="Converra",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()
    user = User(
        organization_id=organization.id,
        full_name="Knowledge User",
        email="knowledge@example.com",
        password_hash="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    vector_store = FakeVectorStore()
    service = KnowledgeService(
        repository=KnowledgeRepository(db_session),
        parser=DocumentParser(),
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=vector_store,
        splitter=RecursiveCharacterTextSplitter(chunk_size=80, chunk_overlap=10),
    )

    document = service.upload_document(
        current_user=user,
        filename="handbook.txt",
        content_type="text/plain",
        content=(
            b"Converra knowledge platform supports retrieval with citations. "
            b"Every chunk keeps document, page, source, and chunk number."
        ),
    )

    assert document.status == DocumentStatus.READY
    assert document.chunk_count > 0
    assert document.file_size > 0
    stored_chunks = vector_store.chunks[organization.id]
    assert stored_chunks[0].metadata["document"] == "handbook.txt"
    assert stored_chunks[0].metadata["page"] == 1
    assert stored_chunks[0].metadata["chunk_number"] == 1

    results = service.search(
        organization_id=organization.id,
        query="retrieval citations",
        top_k=3,
        filters={"document_id": str(document.id)},
    )

    assert results
    assert results[0].metadata["source"] == "handbook.txt"

    service.delete_document(organization.id, document.id)

    assert vector_store.chunks[organization.id] == []
