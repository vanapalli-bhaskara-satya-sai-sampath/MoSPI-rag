import argparse
import logging
import os
from pathlib import Path

from .catalog import build_catalog, export_records_csv, export_records_parquet, write_quality_report
from .chunking import build_chunks
from .database import get_db_path, store_records
from .validation import collect_records, get_paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def generate_quality_report(records_df, stats: dict, chunks_df) -> dict:
    null_counts = records_df.isna().sum().to_dict() if not records_df.empty else {}
    return {
        "total_input_records": int(stats.get("total_input_records", 0)),
        "duplicates_removed": int(stats.get("duplicates_removed", 0)),
        "valid_records": int(stats.get("valid_records", 0)),
        "chunk_count": int(len(chunks_df)),
        "null_counts": null_counts,
        "output_directory": os.getenv("MOSPI_OUTPUT_DIR", str((Path(__file__).resolve().parents[1] / "pipeline_output"))),
        "database_path": str(get_db_path()),
    }


def run_pipeline(paths=None, chunk_size_tokens=None, chunk_overlap_tokens=None) -> dict:
    paths = paths or get_paths()
    output_dir = Path(os.getenv("MOSPI_OUTPUT_DIR", Path(__file__).resolve().parents[1] / "pipeline_output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    records_df, stats = collect_records(paths)
    chunks_df = build_chunks(records_df, chunk_size_tokens=chunk_size_tokens, chunk_overlap_tokens=chunk_overlap_tokens)
    quality_report = generate_quality_report(records_df, stats, chunks_df)

    export_records_csv(records_df, output_dir)
    export_records_parquet(records_df, output_dir)
    write_quality_report(quality_report, output_dir)
    build_catalog(records_df, chunks_df, output_dir, quality_report)
    store_result = store_records(records_df, chunks_df, output_dir)

    logger.info("Pipeline completed: %s", {"records": int(len(records_df)), "chunks": int(len(chunks_df)), "database": store_result})
    return {"records_df": records_df, "chunks_df": chunks_df, "quality_report": quality_report, "storage": store_result}


def main() -> None:
    parser = argparse.ArgumentParser(description="MoSPI RAG pipeline")
    parser.add_argument("--data-root", default=os.getenv("MOSPI_DATA_ROOT"), help="Root directory for raw data")
    parser.add_argument("--output-dir", default=os.getenv("MOSPI_OUTPUT_DIR"), help="Output directory for artifacts")
    parser.add_argument("--chunk-size", type=int, default=int(os.getenv("MOSPI_CHUNK_SIZE_TOKENS", "900")))
    parser.add_argument("--chunk-overlap", type=int, default=int(os.getenv("MOSPI_CHUNK_OVERLAP_TOKENS", "150")))
    args = parser.parse_args()

    if args.data_root:
        os.environ["MOSPI_DATA_ROOT"] = args.data_root
    if args.output_dir:
        os.environ["MOSPI_OUTPUT_DIR"] = args.output_dir

    result = run_pipeline(chunk_size_tokens=args.chunk_size, chunk_overlap_tokens=args.chunk_overlap)
    print({"records": int(len(result["records_df"])), "chunks": int(len(result["chunks_df"])), "quality_report": result["quality_report"]})


if __name__ == "__main__":
    main()
