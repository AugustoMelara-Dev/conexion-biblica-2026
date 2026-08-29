"""Pruebas de contrato para preguntas canónicas autorizadas por IA."""

from __future__ import annotations

import unittest
from typing import Any

from scripts.lib.authored_question import (
    ALLOWED_SUBTYPES,
    REQUIRED_KEYS,
    load_authored_unit,
    validate_authored_question,
)


def valid_authored_question() -> dict[str, Any]:
    return {
        "id": "DAN1-AUTH-0001",
        "source_unit_id": "DAN1-V001",
        "fact_id": "DAN1-V001-F01",
        "family": "single_choice_direct",
        "subtype": "factual_recall",
        "question": "¿Quién sitió a Jerusalén en el tercer año del reinado de Joacim?",
        "options": [
            "Nabucodonosor, rey de Babilonia",
            "Ciro, rey de Persia",
            "Belsasar, rey de los caldeos",
            "Darío el medo",
        ],
        "correct_option": 0,
        "correct_answer": "Nabucodonosor, rey de Babilonia",
        "accepted_answers": ["Nabucodonosor, rey de Babilonia"],
        "explanation": "En el tercer año de Joacim, vino Nabucodonosor y sitió Jerusalén.",
        "why_distractors_fail": {
            "Ciro, rey de Persia": "Reinó en una época posterior.",
            "Belsasar, rey de los caldeos": "Gobernó al final del imperio babilónico.",
            "Darío el medo": "Gobernó tras la caída de Babilonia.",
        },
        "source_ref": "Daniel 1:1",
        "source_quote": "En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió.",
        "evidence_excerpt": "vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió",
        "difficulty": "medium",
        "importance": "high",
        "relation_type": "event_participant",
        "option_category": "person",
        "false_mutation": None,
        "blind_pool": None,
        "ai_review": {
            "status": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": "test-reviewer",
        },
    }


class AuthoredQuestionContractTests(unittest.TestCase):
    def test_accepts_natural_grounded_prompt(self) -> None:
        row = valid_authored_question()
        self.assertEqual(validate_authored_question(row), [])

    def test_rejects_source_location_prompt(self) -> None:
        row = valid_authored_question()
        row["question"] = "Según Daniel 1:1, ¿quién sitió Jerusalén?"
        self.assertIn("DAN1-AUTH-0001:source_location_prompt", validate_authored_question(row))

        row["question"] = "De acuerdo con el versículo 1, ¿quién sitió Jerusalén?"
        self.assertIn("DAN1-AUTH-0001:source_location_prompt", validate_authored_question(row))

    def test_rejects_missing_evidence(self) -> None:
        row = valid_authored_question()
        row["evidence_excerpt"] = ""
        self.assertIn("DAN1-AUTH-0001:missing_evidence", validate_authored_question(row))

    def test_rejects_answer_not_supported(self) -> None:
        row = valid_authored_question()
        row["correct_answer"] = "Alejandro Magno"
        row["options"][0] = "Alejandro Magno"
        self.assertIn("DAN1-AUTH-0001:answer_not_supported", validate_authored_question(row))

    def test_rejects_invalid_option_count(self) -> None:
        row = valid_authored_question()
        row["options"] = ["Nabucodonosor, rey de Babilonia", "Ciro, rey de Persia"]
        self.assertIn("DAN1-AUTH-0001:invalid_option_count", validate_authored_question(row))

    def test_rejects_duplicate_options(self) -> None:
        row = valid_authored_question()
        row["options"] = [
            "Nabucodonosor, rey de Babilonia",
            "Nabucodonosor, rey de Babilonia",
            "Ciro, rey de Persia",
            "Darío el medo",
        ]
        self.assertIn("DAN1-AUTH-0001:duplicate_options", validate_authored_question(row))

    def test_rejects_answer_index_mismatch(self) -> None:
        row = valid_authored_question()
        row["correct_option"] = 1
        self.assertIn("DAN1-AUTH-0001:answer_index_mismatch", validate_authored_question(row))

    def test_rejects_missing_subtype(self) -> None:
        row = valid_authored_question()
        row["subtype"] = "unsupported_subtype"
        self.assertIn("DAN1-AUTH-0001:invalid_subtype", validate_authored_question(row))

    def test_rejects_missing_ai_review(self) -> None:
        row = valid_authored_question()
        row["ai_review"] = None
        self.assertIn("DAN1-AUTH-0001:missing_ai_review", validate_authored_question(row))

    def test_rejects_human_signature_claim(self) -> None:
        row = valid_authored_question()
        row["ai_review"]["reviewer_type"] = "human_verified"
        self.assertIn("DAN1-AUTH-0001:human_signature_claim", validate_authored_question(row))


class AuthoredUnitAcceptanceTests(unittest.TestCase):
    def test_dan1_pilot_has_351_distinct_competitive_questions(self) -> None:
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        path = root / "content" / "final-2026-authored" / "questions" / "DAN1.json"
        rows = load_authored_unit(path)
        self.assertEqual(len(rows), 351)
        ids = {r["id"] for r in rows}
        self.assertEqual(len(ids), 351)
        subtypes = {r["subtype"] for r in rows}
        for expected in (
            "factual_recall",
            "speaker_addressee",
            "cause_consequence",
            "narrative_order",
            "identification",
            "relationship",
            "text_recall",
        ):
            self.assertIn(expected, subtypes)
        for r in rows:
            errs = validate_authored_question(r)
            self.assertEqual(errs, [], f"Errores en {r.get('id')}: {errs}")


if __name__ == "__main__":
    unittest.main()
