import logging
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer

from rag.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Wrapper around SentenceTransformers embeddings."""

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> np.ndarray:
        vector = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(vector, dtype=np.float32).reshape(1, -1)

    def embed_documents(self, texts: Iterable[str]) -> np.ndarray:
        vectors = self.model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32)
