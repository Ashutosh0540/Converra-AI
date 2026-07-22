from __future__ import annotations

import hashlib
import math
from typing import List, Optional

from app.core.config import settings


class EmbeddingProviderError(Exception):
    """Raised when embeddings cannot be generated."""


class DeterministicEmbeddingProvider:
    """Lightweight local embedding provider for development and tests."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        tokens = [token for token in text.lower().split() if token]
        if not tokens:
            tokens = [text.lower()]

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or settings.embedding_model_name
        self._model = None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._encode([text])[0]

    def _encode(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        try:
            model = self._get_model()
            embeddings = model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return [embedding.tolist() for embedding in embeddings]
        except Exception as exc:
            raise EmbeddingProviderError("Failed to generate embeddings.") from exc

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise EmbeddingProviderError(
                    "Sentence Transformers dependency is missing."
                ) from exc

            self._model = SentenceTransformer(self.model_name)

        return self._model


def create_embedding_provider():
    provider = settings.embedding_provider.lower()
    if provider in {"deterministic", "local", "hash"}:
        return DeterministicEmbeddingProvider()
    if provider in {"sentence_transformers", "sentence-transformers", "ml"}:
        return SentenceTransformerEmbeddingProvider()
    raise EmbeddingProviderError(f"Unsupported embedding provider '{provider}'.")
