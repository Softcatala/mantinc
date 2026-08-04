from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lm_eval_tasks.catalan_drift.utils import process_results


def fake_fasttext(text: str) -> tuple[str, float]:
    lowered = text.casefold()
    if "pedido" in lowered or "retrasado" in lowered:
        return "es", 0.99
    return "ca", 0.99


def medium_confidence_false_positive(text: str) -> tuple[str, float]:
    if "especialista no estava disponible" in text.casefold():
        return "es", 0.708
    return "ca", 0.99


def one_bullet_false_positive(text: str) -> tuple[str, float]:
    if "cita confirmada" in text.casefold():
        return "es", 0.795
    return "ca", 0.99


class CatalanDriftChecksTest(unittest.TestCase):
    def test_legacy_forbidden_terms_are_ignored(self) -> None:
        with mock.patch(
            "lm_eval_tasks.catalan_drift.utils._predict_fasttext",
            return_value=("ca", 0.99),
        ):
            result = process_results(
                {
                    "target_lang": "ca",
                    "category": "test",
                    "forbidden_terms": ["support macro"],
                },
                ["Cal revisar el support macro i explicar-ho en català."],
            )

        self.assertNotIn("forbidden_fail", result)
        self.assertEqual(result["drift_pass"], 1.0)

    def test_segment_language_ratio_can_fail_response(self) -> None:
        response = (
            "Aquest text català manté una resposta completa amb informació clara "
            "i ordenada per al client.\n\n"
            "El pedido queda retrasado sin fecha nueva."
        )

        with mock.patch(
            "lm_eval_tasks.catalan_drift.utils._predict_fasttext",
            side_effect=fake_fasttext,
        ):
            result = process_results({"target_lang": "ca", "category": "test"}, [response])

        self.assertEqual(result["language_fail"], 1.0)
        self.assertEqual(result["drift_pass"], 0.0)

    def test_medium_confidence_romance_confusion_does_not_fail(self) -> None:
        response = (
            "Aquesta reclamació està redactada en català i manté una estructura formal "
            "amb cronologia, impacte i petició concreta.\n\n"
            "En arribar al centre, se'm va informar que l'especialista no estava "
            "disponible i que la visita no es podia dur a terme."
        )

        with mock.patch(
            "lm_eval_tasks.catalan_drift.utils._predict_fasttext",
            side_effect=medium_confidence_false_positive,
        ):
            result = process_results({"target_lang": "ca", "category": "test"}, [response])

        self.assertEqual(result["language_fail"], 0.0)
        self.assertEqual(result["drift_pass"], 1.0)

    def test_one_misclassified_catalan_bullet_does_not_fail_response(self) -> None:
        response = (
            "El punt de vacunació habitual es trasllada temporalment a un centre "
            "alternatiu. Les cites ja confirmades es mantenen, però s'atendran a la "
            "nova ubicació, que disposarà d'horari ampliat i personal de suport. "
            "Hi ha opcions de transport públic properes i personal disponible per "
            "orientar les persones usuàries durant el canvi temporal.\n\n"
            "- Comproveu l'adreça del centre alternatiu abans de desplaçar-vos-hi.\n"
            "- Arribeu amb antelació i porteu la documentació necessària.\n"
            "- Si teniu una cita confirmada, no cal que en demaneu una de nova.\n"
            "- Tingueu en compte possibles retards durant el període d'adaptació.\n"
            "- Si necessiteu ajuda per arribar-hi, contacteu amb el servei d'atenció."
        )

        with mock.patch(
            "lm_eval_tasks.catalan_drift.utils._predict_fasttext",
            side_effect=one_bullet_false_positive,
        ):
            result = process_results({"target_lang": "ca", "category": "test"}, [response])

        self.assertEqual(result["language_fail"], 0.0)
        self.assertEqual(result["drift_pass"], 1.0)

    def test_short_foreign_quote_does_not_fail(self) -> None:
        response = " ".join(["paraula"] * 80) + "\n\nHola amigo."

        with mock.patch(
            "lm_eval_tasks.catalan_drift.utils._predict_fasttext",
            side_effect=fake_fasttext,
        ):
            result = process_results({"target_lang": "ca", "category": "test"}, [response])

        self.assertEqual(result["language_fail"], 0.0)
        self.assertEqual(result["drift_pass"], 1.0)

    def test_short_labeled_catalan_template_does_not_fail(self) -> None:
        lines = [
            "ASSUMPTE: Retard del lliurament",
            "SITUACIÓ: Estoc insuficient",
            "RISC: Penalització contractual",
            "ACCIÓ: Comanda urgent",
            "SEGÜENT PAS: Trucada dilluns",
        ]

        for separator in ("\n", "\n\n"):
            with self.subTest(separator=repr(separator)):
                with mock.patch(
                    "lm_eval_tasks.catalan_drift.utils._predict_fasttext",
                    return_value=("ca", 0.99),
                ) as predict:
                    result = process_results(
                        {"target_lang": "ca", "category": "test"},
                        [separator.join(lines)],
                    )

                self.assertEqual(result["language_fail"], 0.0)
                self.assertEqual(result["drift_pass"], 1.0)
                predict.assert_called_once()

    def test_detector_exception_is_not_silent_pass(self) -> None:
        with mock.patch(
            "lm_eval_tasks.catalan_drift.utils._predict_fasttext",
            side_effect=RuntimeError("detector exploded"),
        ):
            result = process_results(
                {"target_lang": "ca", "category": "test"},
                ["Aquesta resposta sembla catalana i hauria de requerir detector."],
            )

        self.assertEqual(result["language_fail"], 1.0)
        self.assertEqual(result["drift_pass"], 0.0)


if __name__ == "__main__":
    unittest.main()
