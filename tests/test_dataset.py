from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_dataset import build_rows


class DatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_rows()

    def test_expected_category_counts(self) -> None:
        self.assertEqual(
            Counter(row["category"] for row in self.rows),
            Counter(
                {
                    "monolingual": 60,
                    "crosslingual_basic": 60,
                    "multi_turn": 60,
                    "crosslingual_advanced": 60,
                    "rag_context": 60,
                }
            ),
        )

    def test_rows_do_not_contain_labels(self) -> None:
        self.assertTrue(all("labels" not in row for row in self.rows))

    def test_rows_do_not_contain_forbidden_terms(self) -> None:
        self.assertTrue(all("forbidden_terms" not in row for row in self.rows))

    def test_advanced_distribution_preserves_coverage(self) -> None:
        advanced = [row for row in self.rows if row["category"] == "crosslingual_advanced"]
        languages = Counter(row["source_lang"] for row in advanced)
        self.assertLessEqual(abs(languages["es-ca"] - languages["en-ca"]), 4)
        self.assertEqual(set(row["persona"] for row in advanced), {"administracio", "pime", "usuari_final"})
        source_workflows = {
            row["workflow"] for row in self.rows if row["category"] == "multi_turn"
        }
        self.assertEqual(set(row["workflow"] for row in advanced), source_workflows)

    def test_build_is_deterministic(self) -> None:
        self.assertEqual(self.rows, build_rows())


if __name__ == "__main__":
    unittest.main()
