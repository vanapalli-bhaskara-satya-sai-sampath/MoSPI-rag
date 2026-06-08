import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.chunking import build_chunks, chunk_text
from pipeline.validation import collect_records, get_paths, load_json_records, validate_and_dedupe


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="mospi-pipeline-")
        self.data_root = Path(self.temp_dir) / "data"
        (self.data_root / "raw" / "json").mkdir(parents=True)
        (self.data_root / "raw" / "text").mkdir(parents=True)
        (self.data_root / "raw" / "tables").mkdir(parents=True)
        (self.data_root / "raw" / "json" / "sample.json").write_text(
            '{"title": "Sample", "text": "alpha beta gamma alpha beta gamma", "date": "2024-01-05", "summary": "Example record"}',
            encoding="utf-8",
        )
        (self.data_root / "raw" / "text" / "sample.txt").write_text("one two three", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_and_dedupe(self) -> None:
        records = [
            {"title": "A", "text": "foo bar", "date": "2024-01-05", "content_hash": "x"},
            {"title": "A", "text": "foo bar", "date": "2024-01-05", "content_hash": "x"},
        ]
        frame, stats = validate_and_dedupe(records)
        self.assertEqual(len(frame), 1)
        self.assertEqual(stats["duplicates_removed"], 1)

    def test_chunking_generates_chunks(self) -> None:
        text = "alpha " * 1000
        chunks = chunk_text(text, chunk_size_tokens=900, chunk_overlap_tokens=150)
        self.assertTrue(len(chunks) >= 1)

    def test_collect_records_from_temp_data(self) -> None:
        os.environ["MOSPI_DATA_ROOT"] = str(self.data_root)
        frame, stats = collect_records(get_paths(self.data_root))
        self.assertGreaterEqual(len(frame), 2)
        self.assertGreaterEqual(stats["valid_records"], 2)

    def test_load_json_records_prefers_extracted_pdf_text(self) -> None:
        temp_root = Path(self.temp_dir) / "pdf_case"
        json_dir = temp_root / "raw" / "json"
        json_dir.mkdir(parents=True)
        (json_dir / "doc.json").write_text(
            '{"title": "Vision Document", "summary": "title only", "pdf_url": "https://example.test/doc.pdf"}',
            encoding="utf-8",
        )

        with patch("pipeline.validation.extract_pdf_text", return_value="real extracted pdf text") as mocked_extract:
            records = load_json_records(json_dir)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["text"], "real extracted pdf text")
        mocked_extract.assert_called_once_with("https://example.test/doc.pdf")


if __name__ == "__main__":
    unittest.main()
