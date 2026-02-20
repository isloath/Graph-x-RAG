from __future__ import annotations

import hashlib
import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding service with local fallback when model loading/inference fails.

    This keeps ingestion/search endpoints alive in constrained environments.
    """

    def __init__(self, model_name: str, fallback_dim: int = 384) -> None:
        self.model_name = model_name
        self.fallback_dim = fallback_dim
        self.model: SentenceTransformer | None = None
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as exc:
            logger.warning("Failed to load embedding model '%s'. Falling back to hash embeddings: %s", model_name, exc)

    def _fallback_embed_one(self, text: str) -> list[float]:
        # Deterministic, dependency-free fallback vector.
        vec = [0.0] * self.fallback_dim
        if not text:
            return vec
        words = text.lower().split()
        for token in words:
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            vec[h % self.fallback_dim] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    async def embed(self, text: str) -> list[float]:
        if self.model is not None:
            try:
                return self.model.encode(text, normalize_embeddings=True).tolist()
            except Exception as exc:
                logger.warning("Embedding inference failed, using fallback: %s", exc)
        return self._fallback_embed_one(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.model is not None:
            try:
                return self.model.encode(texts, normalize_embeddings=True).tolist()
            except Exception as exc:
                logger.warning("Batch embedding inference failed, using fallback: %s", exc)
        return [self._fallback_embed_one(t) for t in texts]
