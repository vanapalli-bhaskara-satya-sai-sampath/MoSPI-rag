import logging
import os
from pathlib import Path

import pandas as pd
import sqlite3

logger = logging.getLogger(__name__)


def get_db_path(output_dir: Path | None = None) -> Path:
    output_dir = Path(output_dir) if output_dir else Path(os.getenv("MOSPI_OUTPUT_DIR", Path(__file__).resolve().parents[1] / "pipeline_output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / "pipeline.sqlite3"


def init_database(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            record_id TEXT PRIMARY KEY,
            source_type TEXT,
            source_path TEXT,
            title TEXT,
            date TEXT,
            summary TEXT,
            category TEXT,
            text TEXT,
            content_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            record_id TEXT,
            source_path TEXT,
            source_type TEXT,
            chunk_index INTEGER,
            chunk_text TEXT,
            token_count INTEGER,
            content_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def store_records(records_df: pd.DataFrame, chunks_df: pd.DataFrame, db_path: Path | None = None) -> dict:
    db_path = get_db_path(db_path)
    conn = init_database(db_path)
    try:
        if not records_df.empty:
            records_df.to_sql("records", conn, if_exists="replace", index=False)
        else:
            conn.execute("DELETE FROM records")
        if not chunks_df.empty:
            chunks_df.to_sql("chunks", conn, if_exists="replace", index=False)
        else:
            conn.execute("DELETE FROM chunks")
        conn.commit()
        return {"database_path": str(db_path), "records_inserted": int(len(records_df)), "chunks_inserted": int(len(chunks_df))}
    finally:
        conn.close()
