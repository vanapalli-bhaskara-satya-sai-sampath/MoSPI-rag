import json
import logging
from pathlib import Path

import pandas as pd

from pipeline.chunking import build_chunks
from rag.config import DATA_DIR, PROCESSED_DIR
from rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


def discover_corpus_paths() -> list[Path]:
    candidates = [
        PROCESSED_DIR / "processed_records.csv",
        PROCESSED_DIR / "chunks.parquet",
        Path("pipeline_output") / "processed_records.csv",
        Path("pipeline_output_final") / "processed_records.csv",
        Path("pipeline_output_run") / "processed_records.csv",
        Path("pipeline_output_smoke") / "processed_records.csv",
    ]
    return [path for path in candidates if path.exists()]


def load_chunks() -> list[dict]:
    chunk_path = PROCESSED_DIR / "chunks.parquet"
    csv_path = None
    for candidate in discover_corpus_paths():
        if candidate.name == "processed_records.csv":
            csv_path = candidate
            break

    if chunk_path.exists():
        chunks_df = pd.read_parquet(chunk_path)
        needs_refresh = (
            not {"title", "url", "chunk_text"}.issubset(chunks_df.columns)
            or chunks_df["title"].fillna("").astype(str).eq("").all()
            or chunks_df["url"].fillna("").astype(str).eq("").all()
            or chunks_df["chunk_text"].fillna("").astype(str).str.len().lt(50).all()
        )
        if csv_path and chunk_path.exists() and chunk_path.stat().st_mtime < csv_path.stat().st_mtime:
            needs_refresh = True
        if not needs_refresh:
            return chunks_df.fillna("").to_dict("records")
        logger.info("Refreshing stale chunk dataset at %s because the source corpus or metadata changed.", chunk_path)

    for candidate in discover_corpus_paths():
        if candidate.name == "processed_records.csv":
            csv_path = candidate
            break
    if csv_path is None:
        raise FileNotFoundError("No processed corpus found. Expected data/processed/processed_records.csv or pipeline_output_*/*.csv")

    records_df = pd.read_csv(csv_path)
    if "text" not in records_df.columns:
        raise ValueError("Processed records must contain a 'text' column for chunking.")
    chunks_df = build_chunks(records_df)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    chunks_df.to_parquet(chunk_path, index=False)
    return chunks_df.fillna("").to_dict("records")


def rebuild_index() -> dict:
    chunks = load_chunks()
    vector_store = VectorStore()
    vector_store.build(chunks)
    return {"status": "success", "chunks": len(chunks)}
