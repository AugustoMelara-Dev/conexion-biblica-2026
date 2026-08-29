"""Pruebas para las compuertas de auditoría del banco autorizado por IA."""

from __future__ import annotations

import unittest
from typing import Any

from scripts.lib.authored_bank_audit import (
    audit_authored_bank,
    content_hash,
)
from scripts.test_authored_question import valid_authored_question


def false_question(mutation: dict[str, Any] | None = None) -> dict[str, Any]:
    row = valid_authored_question()
    row["id"] = "DAN1-AUTH-0002"
    row["family"] = "true_false"
    row["question"] = "Ciro el persa sitió Jerusalén en el tercer año del reinado de Joacim."
    row["options"] = ["Verdadero", "Falso"]
    row["correct_option"] = 1
    row["correct_answer"] = "Falso"
    row["accepted_answers"] = ["Falso"]
    row["false_mutation"] = mutation or {
        "changed_fields": ["person"],
        "local": True,
        "original": "Nabucodonosor",
        "replacement": "Ciro",
    }
    return row


class AuthoredBankAuditTests(unittest.TestCase):
    def test_clean_bank_returns_zero_violations(self) -> None:
        rows = [valid_authored_question(), false_question()]
        audit = audit_authored_bank(rows)
        for category, items in audit.items():
            self.assertEqual(items, [], f"Violaciones encontradas en {category}: {items}")

    def test_rejects_duplicate_prompts(self) -> None:
        q1 = valid_authored_question()
        q2 = valid_authored_question()
        q2["id"] = "DAN1-AUTH-0003"
        audit = audit_authored_bank([q1, q2])
        self.assertIn(q2["id"], audit["duplicate_prompts"])

    def test_rejects_normalized_duplicate_prompts(self) -> None:
        q1 = valid_authored_question()
        q2 = valid_authored_question()
        q2["id"] = "DAN1-AUTH-0003"
        q2["question"] = "¿Quién sitió a Jerusalén en el tercer año del reinado de Joacim?!"
        audit = audit_authored_bank([q1, q2])
        self.assertIn(q2["id"], audit["normalized_duplicate_prompts"])

    def test_rejects_cross_passage_false_statement(self) -> None:
        row = false_question(mutation={"changed_fields": ["source_ref"], "local": False, "original": "Dan 1", "replacement": "Dan 2"})
        audit = audit_authored_bank([row])
        self.assertIn(row["id"], audit["cross_passage_false_mutations"])

    def test_rejects_source_location_prompt(self) -> None:
        row = valid_authored_question()
        row["question"] = "Según Daniel 1:1, ¿quién fue a Jerusalén?"
        audit = audit_authored_bank([row])
        self.assertIn(row["id"], audit["source_location_prompts"])

    def test_content_hash_is_deterministic_and_changes_with_content(self) -> None:
        q1 = valid_authored_question()
        h1 = content_hash(q1)
        h2 = content_hash(q1)
        self.assertEqual(h1, h2)
        q1["explanation"] = "Explicación modificada."
        h3 = content_hash(q1)
        self.assertNotEqual(h1, h3)


if __name__ == "__main__":
    unittest.main()
