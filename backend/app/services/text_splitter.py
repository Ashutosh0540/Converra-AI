from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from app.services.knowledge_types import ParsedSection, TextChunk


class TextSplitterError(Exception):
    """Raised when text splitter configuration is invalid."""


class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise TextSplitterError("Chunk size must be greater than zero.")
        if chunk_overlap < 0:
            raise TextSplitterError("Chunk overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise TextSplitterError("Chunk overlap must be smaller than chunk size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def split_sections(
        self,
        sections: List[ParsedSection],
        document_id: UUID,
        organization_id: UUID,
        filename: str,
        source: str,
    ) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        chunk_number = 1
        for section in sections:
            for text in self._split_text(section.text):
                metadata: Dict[str, Any] = {
                    "document_id": str(document_id),
                    "organization_id": str(organization_id),
                    "document": filename,
                    "filename": filename,
                    "page": section.page,
                    "chunk_number": chunk_number,
                    "source": source,
                }
                chunks.append(TextChunk(text=text, metadata=metadata))
                chunk_number += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        normalized_text = " ".join(text.split())
        if not normalized_text:
            return []
        if len(normalized_text) <= self.chunk_size:
            return [normalized_text]

        chunks: List[str] = []
        start = 0
        while start < len(normalized_text):
            end = min(start + self.chunk_size, len(normalized_text))
            chunk = self._best_chunk(normalized_text[start:end])
            if not chunk:
                break

            chunks.append(chunk)
            if end >= len(normalized_text):
                break

            start += max(len(chunk) - self.chunk_overlap, 1)

        return chunks

    def _best_chunk(self, text: str) -> str:
        if len(text) <= self.chunk_size and text == text.rstrip():
            return text.strip()

        for separator in self.separators:
            if separator == "":
                return text[: self.chunk_size].strip()

            index = text.rfind(separator)
            if index > 0:
                return text[: index + len(separator)].strip()

        return text[: self.chunk_size].strip()
