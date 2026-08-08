from __future__ import annotations

import sys
import unittest
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_dataset import build_rows


CATALAN_INSTRUCTION_RE = re.compile(r"\b(?:català|catalana|catalans|catalanes)\b", re.I)
WORD_RE = re.compile(r"[\wÀ-ÿ']+")


def mentions_catalan_instruction(row: dict) -> bool:
    texts = [str(row.get("prompt") or "")]
    texts.extend(str(turn.get("content") or "") for turn in row.get("conversation") or [])
    return any(CATALAN_INSTRUCTION_RE.search(text) for text in texts)


def final_prompt_word_count(row: dict) -> int:
    prompt = str(row.get("prompt") or "")
    first_line = next((line.strip() for line in prompt.splitlines() if line.strip()), "")
    first_line = re.sub(r"\ben català\b", "", first_line, flags=re.I)
    first_line = re.sub(r"\b(?:català|catalana|catalans|catalanes)\b", "", first_line, flags=re.I)
    return len(WORD_RE.findall(first_line))


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

    def test_rag_chunks_do_not_contain_relevance(self) -> None:
        rag_rows = [row for row in self.rows if row["category"] == "rag_context"]
        self.assertTrue(
            all(
                "relevance" not in chunk
                for row in rag_rows
                for chunk in row.get("retrieved_context", [])
            )
        )

    def test_catalan_instruction_policy(self) -> None:
        for row in self.rows:
            with self.subTest(row=row["id"]):
                category = row["category"]
                has_instruction = mentions_catalan_instruction(row)
                if category == "rag_context":
                    self.assertTrue(has_instruction)
                elif category == "monolingual":
                    self.assertFalse(has_instruction)
                else:
                    expected = row["source_lang"] != "ca" and final_prompt_word_count(row) < 10
                    self.assertEqual(has_instruction, expected)

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
