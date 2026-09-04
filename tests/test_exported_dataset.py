import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from scripts.catalan_drift_eval import DEFAULT_PROMPTS, export_lm_eval

with tempfile.TemporaryDirectory() as directory:
    output = Path(directory) / "catalan_drift.jsonl"
    export_lm_eval(
        argparse.Namespace(
            prompts=[str(ROOT / prompt) for prompt in DEFAULT_PROMPTS], output=output
        )
    )
    ROWS = [json.loads(line) for line in output.read_text().splitlines()]
COMMON = {"category", "id", "persona", "prompt", "source_lang", "target_lang", "workflow"}
EXTRA = {
    "monolingual": set(),
    "crosslingual_basic": set(),
    "multi_turn": {"messages"},
    "crosslingual_advanced": {"messages"},
    "rag_context": {"retrieved_context", "user_prompt"},
}


class ExportedDatasetTest(unittest.TestCase):
    def test_expected_columns_are_not_missing(self):
        for row in ROWS:
            self.assertFalse((COMMON | EXTRA[row["category"]]) - row.keys(), row["id"])

    def test_no_unexpected_columns_are_added(self):
        for row in ROWS:
            self.assertFalse(row.keys() - (COMMON | EXTRA[row["category"]]), row["id"])
