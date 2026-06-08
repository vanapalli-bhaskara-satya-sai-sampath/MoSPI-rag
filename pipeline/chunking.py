import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def tokenize(text: str) -> list[str]:
    return text.split()


def chunk_text(text: str, chunk_size_tokens: int = 900, chunk_overlap_tokens: int = 150) -> list[str]:
    tokens = tokenize(text)
    if not tokens:
        return []
    chunks = []
    step = max(1, chunk_size_tokens - chunk_overlap_tokens)
    for start in range(0, len(tokens), step):
        end = min(start + chunk_size_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        if not chunk_tokens:
            continue
        chunks.append(" ".join(chunk_tokens))
        if end == len(tokens):
            break
    return chunks


def build_chunks(records_df: pd.DataFrame, chunk_size_tokens: int | None = None, chunk_overlap_tokens: int | None = None) -> pd.DataFrame:
    chunk_size_tokens = int(chunk_size_tokens or os.getenv("MOSPI_CHUNK_SIZE_TOKENS", "900"))
    chunk_overlap_tokens = int(chunk_overlap_tokens or os.getenv("MOSPI_CHUNK_OVERLAP_TOKENS", "150"))

    chunk_rows = []
    for _, row in records_df.iterrows():
        chunks = chunk_text(row.get("text", ""), chunk_size_tokens=chunk_size_tokens, chunk_overlap_tokens=chunk_overlap_tokens)
        for idx, chunk in enumerate(chunks):
            chunk_rows.append({
                "record_id": row.get("record_id", ""),
                "chunk_id": f"{row.get('record_id', 'record')}-chunk-{idx}",
                "source_path": row.get("source_path", ""),
                "source_type": row.get("source_type", ""),
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "summary": row.get("summary", ""),
                "category": row.get("category", ""),
                "chunk_index": idx,
                "chunk_text": chunk,
                "token_count": len(tokenize(chunk)),
                "content_hash": row.get("content_hash", ""),
            })
    return pd.DataFrame(chunk_rows)
