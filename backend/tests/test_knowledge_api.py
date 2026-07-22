from typing import Any, Dict, List, Optional
from uuid import UUID

from app.api.dependencies import get_knowledge_service
from app.auth.security import hash_password
from app.models.enums import UserRole
from app.models.organization import Organization
from app.models.user import User
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.document_parser import DocumentParser
from app.services.knowledge_service import KnowledgeService
from app.services.knowledge_types import TextChunk, VectorSearchResult
from app.services.text_splitter import RecursiveCharacterTextSplitter


class FakeEmbeddingProvider:
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[1.0, float(index)] for index, _ in enumerate(texts, start=1)]

    def embed_query(self, text: str) -> List[float]:
        return [1.0, float(len(text))]


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
                    score=0.95,
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


def test_knowledge_upload_search_list_and_delete(client, db_session):
    organization = Organization(
        name="Converra",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()
    admin = User(
        organization_id=organization.id,
        full_name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    vector_store = FakeVectorStore()

    def override_knowledge_service():
        return KnowledgeService(
            repository=KnowledgeRepository(db_session),
            parser=DocumentParser(),
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=vector_store,
            splitter=RecursiveCharacterTextSplitter(
                chunk_size=80,
                chunk_overlap=10,
            ),
        )

    client.app.dependency_overrides[get_knowledge_service] = override_knowledge_service

    login_response = client.post(
        "/api/v1/users/login",
        json={
            "email": "admin@example.com",
            "password": "strong-password",
        },
    )
    token = login_response.json()["access_token"]

    upload_response = client.post(
        "/api/v1/knowledge/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "playbook.txt",
                (
                    b"Enterprise knowledge retrieval keeps citations available "
                    b"to the answering agent."
                ),
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201
    document = upload_response.json()
    assert document["status"] == "READY"
    assert document["chunk_count"] > 0

    list_response = client.get(
        "/api/v1/knowledge",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == document["id"]

    search_response = client.post(
        "/api/v1/knowledge/search",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "citations", "top_k": 2},
    )

    assert search_response.status_code == 200
    search_result = search_response.json()["results"][0]
    assert search_result["citation"]["document"] == "playbook.txt"
    assert search_result["citation"]["page"] == 1
    assert search_result["citation"]["chunk_number"] == 1
    assert search_result["citation"]["source"] == "playbook.txt"

    delete_response = client.delete(
        f"/api/v1/knowledge/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204


def test_viewer_cannot_upload_knowledge(client, db_session):
    organization = Organization(
        name="Converra",
        industry="AI",
        subscription_plan="enterprise",
    )
    db_session.add(organization)
    db_session.flush()
    viewer = User(
        organization_id=organization.id,
        full_name="Viewer User",
        email="viewer@example.com",
        password_hash=hash_password("strong-password"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(viewer)
    db_session.commit()

    login_response = client.post(
        "/api/v1/users/login",
        json={
            "email": "viewer@example.com",
            "password": "strong-password",
        },
    )
    token = login_response.json()["access_token"]

    upload_response = client.post(
        "/api/v1/knowledge/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("blocked.txt", b"blocked", "text/plain")},
    )

    assert upload_response.status_code == 403
