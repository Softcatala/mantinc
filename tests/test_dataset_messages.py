from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_dataset import build_rows, validate_rows
from scripts.catalan_drift_eval import _messages


class ConversationDatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_rows()
        cls.conversation_rows = [row for row in cls.rows if row.get("conversation")]

    def test_conversations_end_with_assistant_and_roles_alternate(self) -> None:
        self.assertEqual(len(self.conversation_rows), 160)
        for row in self.conversation_rows:
            with self.subTest(row=row["id"]):
                roles = [turn["role"] for turn in row["conversation"]]
                self.assertEqual(roles[-1], "assistant")
                self.assertTrue(all(left != right for left, right in zip(roles, roles[1:])))

    def test_messages_end_with_prompt_as_the_only_user_copy(self) -> None:
        for row in self.conversation_rows:
            with self.subTest(row=row["id"]):
                messages = _messages(row)
                self.assertIsNotNone(messages)
                self.assertEqual(messages[-1], {"role": "user", "content": row["prompt"].strip()})
                self.assertEqual(
                    sum(message["content"] == row["prompt"].strip() for message in messages),
                    1,
                )
                self.assertNotIn("system", [message["role"] for message in messages])

    def test_validation_rejects_a_user_final_conversation(self) -> None:
        rows = deepcopy(self.rows)
        row = next(row for row in rows if row.get("conversation"))
        row["conversation"].append({"role": "user", "content": "Torn final invàlid"})

        with self.assertRaisesRegex(ValueError, "conversation must end with assistant"):
            validate_rows(rows)


if __name__ == "__main__":
    unittest.main()
