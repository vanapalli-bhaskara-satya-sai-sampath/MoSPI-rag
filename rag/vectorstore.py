import logging
import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from rag.config import FAISS_INDEX_PATH, METADATA_PATH, VECTORSTORE_DIR
from rag.embeddings import EmbeddingClient

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-backed vector store with metadata persistence."""

    def __init__(self, index_path: Path = FAISS_INDEX_PATH, metadata_path: Path = METADATA_PATH) -> None:
        self.index_path = index_path
        self.metadata_path = metadata_path
        VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
        self.embedding_client = EmbeddingClient()
        self.index: faiss.Index | None = None
        self.metadata: list[dict[str, Any]] = []

    def build(self, chunks: list[dict[str, Any]]) -> None:
        logger.info("Building FAISS index for %d chunks", len(chunks))
        texts = [chunk.get("chunk_text", "") for chunk in chunks]
        embeds = self.embedding_client.embed_documents(texts)
        dimension = embeds.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeds)
        self.metadata = chunks
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "wb") as handle:
            pickle.dump(self.metadata, handle)

    def load(self) -> bool:
        if not self.index_path.exists() or not self.metadata_path.exists():
            return False
        self.index = faiss.read_index(str(self.index_path))
        with open(self.metadata_path, "rb") as handle:
            self.metadata = pickle.load(handle)
        return True

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.index is None and not self.load():
            raise RuntimeError("FAISS index is not available. Run /ingest first.")
        query_vector = self.embedding_client.embed_text(query)
        distances, indices = self.index.search(query_vector, min(top_k, len(self.metadata)))
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            item = dict(self.metadata[int(idx)])
            item["score"] = float(distance)
            results.append(item)
        return results
