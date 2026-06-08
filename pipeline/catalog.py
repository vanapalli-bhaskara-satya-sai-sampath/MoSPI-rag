import json
import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def ensure_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_catalog(records_df: pd.DataFrame, chunks_df: pd.DataFrame, output_dir: Path, quality_report: dict) -> dict:
    output_dir = ensure_output_dir(output_dir)
    catalog = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "record_count": int(len(records_df)),
        "chunk_count": int(len(chunks_df)),
        "quality_report": quality_report,
        "outputs": {
            "processed_records_csv": str((output_dir / "processed_records.csv").resolve()),
            "cleaned_records_parquet": str((output_dir / "cleaned_records.parquet").resolve()),
            "catalog_json": str((output_dir / "catalog.json").resolve()),
            "quality_report_json": str((output_dir / "data_quality_report.json").resolve()),
            "database_sqlite": str((output_dir / "pipeline.sqlite3").resolve()),
        },
    }
    (output_dir / "catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return catalog


def export_records_csv(records_df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir = ensure_output_dir(output_dir)
    path = output_dir / "processed_records.csv"
    records_df.to_csv(path, index=False)
    return path


def export_records_parquet(records_df: pd.DataFrame, output_dir: Path) -> Path:
    output_dir = ensure_output_dir(output_dir)
    path = output_dir / "cleaned_records.parquet"
    records_df.to_parquet(path, index=False)
    return path


def write_quality_report(quality_report: dict, output_dir: Path) -> Path:
    output_dir = ensure_output_dir(output_dir)
    path = output_dir / "data_quality_report.json"
    path.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")
    return path
