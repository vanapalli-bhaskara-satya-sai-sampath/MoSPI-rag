import hashlib
import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Iterable

import pandas as pd
import pdfplumber
import requests

logger = logging.getLogger(__name__)


def get_paths(base_dir: Path | None = None) -> dict:
    base_dir = Path(base_dir) if base_dir else Path(os.getenv("MOSPI_DATA_ROOT", Path(__file__).resolve().parents[1] / "data"))
    return {
        "base": base_dir,
        "json": Path(os.getenv("MOSPI_RAW_JSON_DIR", base_dir / "raw" / "json")),
        "text": Path(os.getenv("MOSPI_RAW_TEXT_DIR", base_dir / "raw" / "text")),
        "tables": Path(os.getenv("MOSPI_RAW_TABLES_DIR", base_dir / "raw" / "tables")),
        "output": Path(os.getenv("MOSPI_OUTPUT_DIR", Path(__file__).resolve().parents[1] / "pipeline_output")),
    }


def normalize_whitespace(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_date(value: object) -> str:
    if value in (None, ""):
        return ""
    try:
        return pd.to_datetime(value, errors="coerce").strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def calculate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_pdf_text(pdf_url: str) -> str:
    """Fetch and extract text from a PDF URL, returning normalized plain text."""
    try:
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        with pdfplumber.open(BytesIO(response.content)) as pdf:
            text_chunks = [page.extract_text() or "" for page in pdf.pages]
        return normalize_whitespace("\n\n".join(text_chunks))
    except Exception as exc:
        logger.warning("PDF extraction failed for %s: %s", pdf_url, exc)
        return ""


def load_json_records(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    for file_path in sorted(path.glob("*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                items = payload
            else:
                items = [payload]
            for item in items:
                text = normalize_whitespace(item.get("text") or item.get("content") or "")
                if not text and item.get("pdf_url"):
                    text = extract_pdf_text(item["pdf_url"])
                if not text:
                    text = normalize_whitespace(item.get("summary") or item.get("description") or "")
                records.append({
                    "source_type": "json",
                    "source_path": str(file_path),
                    "title": normalize_whitespace(item.get("title") or file_path.stem),
                    "url": normalize_whitespace(item.get("url") or item.get("pdf_url") or ""),
                    "date": normalize_date(item.get("date") or item.get("published_at") or ""),
                    "summary": normalize_whitespace(item.get("summary") or item.get("description") or ""),
                    "category": normalize_whitespace(item.get("category") or item.get("topic") or ""),
                    "text": text,
                    "content_hash": calculate_hash(text or json.dumps(item, sort_keys=True)),
                })
        except Exception as exc:
            logger.warning("Skipping invalid JSON file %s: %s", file_path, exc)
    return records


def load_text_records(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    for file_path in sorted(path.glob("*.txt")):
        try:
            text = normalize_whitespace(file_path.read_text(encoding="utf-8"))
            records.append({
                "source_type": "text",
                "source_path": str(file_path),
                "title": normalize_whitespace(file_path.stem),
                "url": "",
                "date": "",
                "summary": "",
                "category": "",
                "text": text,
                "content_hash": calculate_hash(text),
            })
        except Exception as exc:
            logger.warning("Skipping invalid text file %s: %s", file_path, exc)
    return records


def load_table_records(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    for file_path in sorted(path.glob("*.csv")):
        try:
            frame = pd.read_csv(file_path)
            if frame.empty:
                continue
            table_text = frame.astype(str).fillna("").to_csv(index=False)
            records.append({
                "source_type": "table",
                "source_path": str(file_path),
                "title": normalize_whitespace(file_path.stem),
                "url": "",
                "date": "",
                "summary": "",
                "category": "",
                "text": normalize_whitespace(table_text),
                "content_hash": calculate_hash(table_text),
            })
        except Exception as exc:
            logger.warning("Skipping invalid table file %s: %s", file_path, exc)
    return records


def validate_and_dedupe(records: Iterable[dict]) -> tuple[pd.DataFrame, dict]:
    frame = pd.DataFrame(list(records))
    if frame.empty:
        return frame, {"total_input_records": 0, "duplicates_removed": 0, "valid_records": 0}

    expected_columns = ["source_type", "source_path", "title", "url", "date", "summary", "category", "text", "content_hash"]
    frame = frame.reindex(columns=expected_columns + [col for col in frame.columns if col not in expected_columns], fill_value="")
    frame = frame.copy()
    frame["title"] = frame["title"].fillna("").apply(normalize_whitespace)
    frame["summary"] = frame["summary"].fillna("").apply(normalize_whitespace)
    frame["category"] = frame["category"].fillna("").apply(normalize_whitespace)
    frame["text"] = frame["text"].fillna("").apply(normalize_whitespace)
    frame["date"] = frame["date"].fillna("").apply(normalize_date)
    frame["content_hash"] = frame.apply(lambda row: row["content_hash"] or calculate_hash(row["text"] or ""), axis=1)

    duplicates = frame.duplicated(subset=["content_hash"], keep="first")
    deduped = frame.loc[~duplicates].copy()
    deduped["record_id"] = deduped["content_hash"].astype(str).str[:12]
    stats = {
        "total_input_records": int(len(frame)),
        "duplicates_removed": int(duplicates.sum()),
        "valid_records": int(len(deduped)),
    }
    return deduped, stats


def collect_records(paths: dict | None = None) -> tuple[pd.DataFrame, dict]:
    paths = paths or get_paths()
    records = []
    records.extend(load_json_records(paths["json"]))
    records.extend(load_text_records(paths["text"]))
    records.extend(load_table_records(paths["tables"]))
    return validate_and_dedupe(records)
