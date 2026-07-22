from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lm_eval_tasks.catalan_drift.utils import forbidden_hits, process_results


class ForbiddenHitsTest(unittest.TestCase):
    def test_detects_case_insensitive_whole_term(self) -> None:
        hits = forbidden_hits("Cal evitar el Support Macro en la resposta.", ["support macro"])

        self.assertEqual(hits, ["support macro"])

    def test_ignores_terms_inside_words(self) -> None:
        hits = forbidden_hits("El pressupost està pendent.", ["press"])

        self.assertEqual(hits, [])

    def test_empty_terms_are_ignored(self) -> None:
        hits = forbidden_hits("Text de prova.", ["", "prova"])

        self.assertEqual(hits, ["prova"])

    def test_global_catalan_markers_are_forbidden(self) -> None:
        for marker in ("ASUNTO", "SUBJECT", "Aquí tienes"):
            with self.subTest(marker=marker):
                result = process_results(
                    {"target_lang": "ca", "category": "test"},
                    [f"{marker}: text de prova en català."],
                )

                self.assertEqual(result["forbidden_fail"], 1.0)
                self.assertEqual(result["drift_pass"], 0.0)

    def test_global_catalan_markers_do_not_apply_to_other_targets(self) -> None:
        result = process_results(
            {"target_lang": "es", "category": "test"},
            ["ASUNTO: texto de prueba en español."],
        )

        self.assertEqual(result["forbidden_fail"], 0.0)


if __name__ == "__main__":
    unittest.main()
