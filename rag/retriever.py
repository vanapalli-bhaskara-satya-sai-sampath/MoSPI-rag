import logging
import math
from typing import Any

import numpy as np

from rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieval wrapper with similarity and MMR modes."""

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    def similarity_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        return self.vector_store.search(query, top_k=top_k)

    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Return normalized retrieval results with text, title, and URL."""
        chunks = self.similarity_search(query, top_k=top_k)
        return [
            {
                "text": item.get("chunk_text", ""),
                "title": item.get("title") or item.get("document_title") or "Untitled",
                "url": item.get("url", ""),
                "metadata": item,
            }
            for item in chunks
        ]

    def mmr_search(self, query: str, top_k: int, fetch_k: int) -> list[dict[str, Any]]:
        if not self.vector_store.index and not self.vector_store.load():
            raise RuntimeError("FAISS index is not available. Run /ingest first.")

        query_vector = self.vector_store.embedding_client.embed_text(query)
        distances, indices = self.vector_store.index.search(query_vector, min(fetch_k, len(self.vector_store.metadata)))
        candidates = [dict(self.vector_store.metadata[int(idx)]) for idx in indices[0] if idx >= 0 and idx < len(self.vector_store.metadata)]

        if not candidates:
            return []

        embeddings = np.asarray([self.vector_store.embedding_client.embed_text(item["chunk_text"])[0] for item in candidates], dtype=np.float32)
        query_emb = query_vector.astype(np.float32)
        sim_scores = np.dot(embeddings, query_emb.T).reshape(-1)
        selected: list[int] = []
        selected_scores: list[float] = []
        lambda_param = 0.55

        while len(selected) < min(top_k, len(candidates)):
            best_idx = -1
            best_score = -math.inf
            for idx, candidate in enumerate(candidates):
                if idx in selected:
                    continue
                max_similarity = 0.0
                if selected:
                    selected_vectors = embeddings[np.asarray(selected)]
                    similarity = np.dot(embeddings[idx], selected_vectors.T)
                    max_similarity = float(np.max(similarity))
                score = lambda_param * sim_scores[idx] - (1.0 - lambda_param) * max_similarity
                if score > best_score:
                    best_score = score
                    best_idx = idx
            if best_idx == -1:
                break
            selected.append(best_idx)
            selected_scores.append(best_score)

        return [candidates[idx] for idx in selected]
