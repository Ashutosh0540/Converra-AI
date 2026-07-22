from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import List

from app.services.knowledge_types import ParsedSection


class DocumentParsingError(Exception):
    """Raised when a knowledge document cannot be parsed."""


class DocumentParser:
    supported_extensions = {".pdf", ".docx", ".txt", ".md", ".markdown"}

    def parse(self, filename: str, content: bytes) -> List[ParsedSection]:
        extension = Path(filename).suffix.lower()
        if extension not in self.supported_extensions:
            raise DocumentParsingError(
                "Unsupported file type. Supported formats: PDF, DOCX, TXT, MD."
            )

        if extension == ".pdf":
            return self._parse_pdf(content)
        if extension == ".docx":
            return self._parse_docx(content)

        return self._parse_text(content)

    def _parse_pdf(self, content: bytes) -> List[ParsedSection]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise DocumentParsingError("PDF parsing dependency is missing.") from exc

        try:
            reader = PdfReader(BytesIO(content))
            sections: List[ParsedSection] = []
            for index, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    sections.append(ParsedSection(text=text, page=index))
            return sections
        except Exception as exc:
            raise DocumentParsingError("Failed to parse PDF document.") from exc

    def _parse_docx(self, content: bytes) -> List[ParsedSection]:
        try:
            from docx import Document
        except ImportError as exc:
            raise DocumentParsingError("DOCX parsing dependency is missing.") from exc

        try:
            document = Document(BytesIO(content))
            text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            )
            return [ParsedSection(text=text, page=1)] if text.strip() else []
        except Exception as exc:
            raise DocumentParsingError("Failed to parse DOCX document.") from exc

    def _parse_text(self, content: bytes) -> List[ParsedSection]:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentParsingError("Text document must be UTF-8 encoded.") from exc

        return [ParsedSection(text=text, page=1)] if text.strip() else []
