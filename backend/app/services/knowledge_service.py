from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger

from app.core.config import settings
from app.models.enums import DocumentStatus
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.repositories.knowledge_repository import (
    KnowledgeRepository,
    KnowledgeRepositoryError,
)
from app.services.document_parser import DocumentParser, DocumentParsingError
from app.services.embedding_provider import (
    EmbeddingProviderError,
    create_embedding_provider,
)
from app.services.knowledge_types import (
    EmbeddingProvider,
    TextChunk,
    VectorSearchResult,
    VectorStore,
)
from app.services.text_splitter import (
    RecursiveCharacterTextSplitter,
    TextSplitterError,
)
from app.services.vector_store import ChromaVectorStore, VectorStoreError


class KnowledgeServiceError(Exception):
    """Base error raised by KnowledgeService."""


class KnowledgeDocumentNotFound(KnowledgeServiceError):
    """Raised when a knowledge document cannot be found."""


class EmptyKnowledgeDocument(KnowledgeServiceError):
    """Raised when a document has no extractable text."""


class KnowledgeService:
    def __init__(
        self,
        repository: KnowledgeRepository,
        parser: Optional[DocumentParser] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        splitter: Optional[RecursiveCharacterTextSplitter] = None,
    ) -> None:
        self.repository = repository
        self.parser = parser or DocumentParser()
        self.embedding_provider = embedding_provider or create_embedding_provider()
        self.vector_store = vector_store or ChromaVectorStore()
        self.splitter = splitter or RecursiveCharacterTextSplitter(
            chunk_size=settings.knowledge_chunk_size,
            chunk_overlap=settings.knowledge_chunk_overlap,
        )

    def upload_document(
        self,
        current_user: User,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> KnowledgeDocument:
        document = KnowledgeDocument(
            organization_id=current_user.organization_id,
            uploader_id=current_user.id,
            filename=filename,
            content_type=content_type or "application/octet-stream",
            file_size=len(content),
            source=filename,
            status=DocumentStatus.PROCESSING,
        )

        try:
            document = self.repository.create(document)
            chunks = self._build_chunks(document, content)
            embeddings = self.embedding_provider.embed_documents(
                [chunk.text for chunk in chunks]
            )
            self.vector_store.add_chunks(
                organization_id=document.organization_id,
                chunks=chunks,
                embeddings=embeddings,
            )
            document.status = DocumentStatus.READY
            document.chunk_count = len(chunks)
            document.error_message = None
            logger.info(
                "Knowledge document {} uploaded with {} chunks",
                document.id,
                len(chunks),
            )
            return self.repository.update(document)
        except (
            DocumentParsingError,
            EmbeddingProviderError,
            TextSplitterError,
            VectorStoreError,
            EmptyKnowledgeDocument,
        ) as exc:
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)
            self.repository.update(document)
            logger.warning(
                "Knowledge document {} failed ingestion: {}",
                document.id,
                str(exc),
            )
            raise KnowledgeServiceError(str(exc)) from exc
        except KnowledgeRepositoryError as exc:
            raise KnowledgeServiceError(
                "Failed to persist knowledge document."
            ) from exc

    def list_documents(self, organization_id: UUID) -> List[KnowledgeDocument]:
        try:
            return self.repository.list_by_organization(organization_id)
        except KnowledgeRepositoryError as exc:
            raise KnowledgeServiceError("Failed to list knowledge documents.") from exc

    def delete_document(
        self,
        organization_id: UUID,
        document_id: UUID,
    ) -> None:
        try:
            document = self.repository.get_by_id(document_id)
            if document is None or document.organization_id != organization_id:
                raise KnowledgeDocumentNotFound(
                    f"Knowledge document '{document_id}' was not found."
                )

            self.vector_store.delete_document(organization_id, document_id)
            self.repository.delete(document)
            logger.info("Knowledge document {} deleted", document_id)
        except KnowledgeRepositoryError as exc:
            raise KnowledgeServiceError("Failed to delete knowledge document.") from exc
        except VectorStoreError as exc:
            raise KnowledgeServiceError("Failed to delete document vectors.") from exc

    def search(
        self,
        organization_id: UUID,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        try:
            query_embedding = self.embedding_provider.embed_query(query)
            normalized_filters = self._normalize_filters(filters)
            return self.vector_store.similarity_search(
                organization_id=organization_id,
                query_embedding=query_embedding,
                top_k=top_k,
                filters=normalized_filters,
            )
        except (EmbeddingProviderError, VectorStoreError) as exc:
            raise KnowledgeServiceError("Failed to search knowledge base.") from exc

    def _build_chunks(
        self,
        document: KnowledgeDocument,
        content: bytes,
    ) -> List[TextChunk]:
        sections = self.parser.parse(document.filename, content)
        if not sections:
            raise EmptyKnowledgeDocument("Document has no extractable text.")

        chunks = self.splitter.split_sections(
            sections=sections,
            document_id=document.id,
            organization_id=document.organization_id,
            filename=document.filename,
            source=document.source,
        )
        if not chunks:
            raise EmptyKnowledgeDocument("Document has no extractable text.")

        return chunks

    @staticmethod
    def _normalize_filters(
        filters: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not filters:
            return None

        normalized: Dict[str, Any] = {}
        for key, value in filters.items():
            if isinstance(value, UUID):
                normalized[key] = str(value)
            else:
                normalized[key] = value

        return normalized
