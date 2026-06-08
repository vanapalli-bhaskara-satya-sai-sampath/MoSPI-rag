import sqlite3
from pathlib import Path

DB_PATH = Path("scraper_data.sqlite3")


def connect(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            date TEXT,
            summary TEXT,
            category TEXT,
            pdf_url TEXT,
            hash TEXT,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_url TEXT,
            local_path TEXT,
            sha256 TEXT,
            mime_type TEXT
        )
        """
    )
    conn.commit()


def upsert_document(conn: sqlite3.Connection, payload: dict) -> None:
    conn.execute(
        """
        INSERT INTO documents (url, title, date, summary, category, pdf_url, hash, source)
        VALUES (:url, :title, :date, :summary, :category, :pdf_url, :hash, :source)
        ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            date=excluded.date,
            summary=excluded.summary,
            category=excluded.category,
            pdf_url=excluded.pdf_url,
            hash=excluded.hash,
            source=excluded.source
        """,
        payload,
    )
    conn.commit()


def count_documents(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
