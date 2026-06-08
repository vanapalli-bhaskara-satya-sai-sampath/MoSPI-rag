import unittest
from pathlib import Path

from rag.ingest import discover_corpus_paths
from rag.prompt import build_prompt


class RagTests(unittest.TestCase):
    def test_discover_corpus_paths_returns_existing_sources(self) -> None:
        paths = discover_corpus_paths()
        self.assertTrue(any(path.name == "processed_records.csv" for path in paths))

    def test_prompt_template_builds_expected_messages(self) -> None:
        messages = build_prompt("What is the index?", "sample context")
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Answer strictly from the provided context.", messages[0]["content"])
        self.assertIn("What is the index?", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
