from __future__ import annotations

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_knowledge_service
from app.auth.dependencies import get_current_user, require_roles
from app.core.config import settings
from app.models.enums import UserRole
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeCitation,
    KnowledgeDocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)
from app.services.knowledge_service import (
    KnowledgeDocumentNotFound,
    KnowledgeService,
    KnowledgeServiceError,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post(
    "/upload",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a knowledge document",
)
async def upload_knowledge_document(
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT)),
    ],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    file: UploadFile = File(...),
) -> KnowledgeDocument:
    filename = file.filename or "uploaded-document"
    extension = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
    if extension not in {"pdf", "docx", "txt", "md", "markdown"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported document type. Upload PDF, DOCX, TXT, or Markdown.",
        )
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the configured size limit.",
        )
    try:
        return service.upload_document(
            current_user=current_user,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
    except KnowledgeServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=List[KnowledgeDocumentResponse],
    summary="List knowledge documents",
)
def list_knowledge_documents(
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    ],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> List[KnowledgeDocument]:
    try:
        return service.list_documents(current_user.organization_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a knowledge document",
)
def delete_knowledge_document(
    document_id: UUID,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
    ],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> None:
    try:
        service.delete_document(
            organization_id=current_user.organization_id,
            document_id=document_id,
        )
    except KnowledgeDocumentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except KnowledgeServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search organization knowledge",
)
def search_knowledge(
    payload: KnowledgeSearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> KnowledgeSearchResponse:
    try:
        results = service.search(
            organization_id=current_user.organization_id,
            query=payload.query,
            top_k=payload.top_k,
            filters=payload.filters,
        )
        return KnowledgeSearchResponse(
            query=payload.query,
            results=[
                KnowledgeSearchResult(
                    text=result.text,
                    score=result.score,
                    metadata=result.metadata,
                    citation=KnowledgeCitation(
                        document_id=str(result.metadata["document_id"]),
                        document=str(result.metadata["document"]),
                        page=int(result.metadata["page"]),
                        chunk_number=int(result.metadata["chunk_number"]),
                        source=str(result.metadata["source"]),
                    ),
                )
                for result in results
            ],
        )
    except KnowledgeServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
