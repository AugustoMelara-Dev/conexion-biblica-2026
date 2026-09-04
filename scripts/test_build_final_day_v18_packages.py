from __future__ import annotations

import unittest

from scripts.build_final_day_v18_packages import build_packages


def record(question_id: str, chapter: str, status: str, fact_id: str | None = None) -> dict:
    return {
        "question_id": question_id,
        "chapter": chapter,
        "fact_id": fact_id or f"F-{question_id}",
        "source_unit_id": f"U-{question_id}",
        "selected_answer": "Respuesta",
        "audit_status": status,
        "blocking_reasons": [],
        "sol_model": "GPT-5.6 Sol",
        "sol_reasoning_effort": "medium",
        "sol_conversation_id": "/root/sol",
        "blind_model": "GPT-5.6 Luna",
        "blind_reasoning_effort": "max",
        "blind_conversation_id": "/root/blind",
    }


class PackageBuilderTests(unittest.TestCase):
    def test_only_verified_questions_enter_packages(self) -> None:
        result = build_packages(
            [
                record("PR-1", "PR39", "VERIFIED_COVERAGE_SOL"),
                record("D-1", "DAN9", "VERIFIED_COMPETITIVE_SOL"),
                record("BAD", "PR40", "REWRITE_REQUIRED"),
            ]
        )
        self.assertEqual(set(result["packages"]["ULTIMO_DIA_COBERTURA_1000"]["question_ids"]), {"PR-1", "D-1"})
        self.assertEqual(result["packages"]["ULTIMO_DIA_ADVERSARIAL_300"]["question_ids"], ["D-1"])
        self.assertEqual(result["packages"]["REPARACION_PERSONAL"]["question_ids"], ["D-1"])

    def test_conflicting_audits_fail_closed(self) -> None:
        result = build_packages(
            [
                record("Q", "PR39", "VERIFIED_COVERAGE_SOL"),
                record("Q", "PR39", "REWRITE_REQUIRED"),
            ]
        )
        self.assertNotIn("Q", result["packages"]["ULTIMO_DIA_COBERTURA_1000"]["question_ids"])
        self.assertEqual(result["conflicts"], ["Q"])

    def test_coverage_prefers_distinct_facts(self) -> None:
        result = build_packages(
            [
                record("Q1", "PR39", "VERIFIED_COVERAGE_SOL", "F1"),
                record("Q2", "PR39", "VERIFIED_COVERAGE_SOL", "F1"),
                record("Q3", "DAN12", "VERIFIED_COVERAGE_SOL", "F2"),
            ]
        )
        self.assertEqual(
            result["packages"]["ULTIMO_DIA_COBERTURA_1000"]["question_ids"],
            ["Q1", "Q3", "Q2"],
        )

    def test_minimal_fabricated_verified_record_is_not_packaged(self) -> None:
        result = build_packages(
            [{"question_id": "FAKE", "chapter": "PR39", "audit_status": "VERIFIED_COMPETITIVE_SOL"}]
        )
        self.assertEqual(result["verified_question_count"], 0)
        self.assertIn("FAKE", result["invalid_records"])

    def test_same_status_with_contradictory_evidence_is_a_conflict(self) -> None:
        first = record("Q", "PR39", "VERIFIED_COVERAGE_SOL", "F1")
        second = {**first, "selected_answer": "Otra respuesta"}
        result = build_packages([first, second])
        self.assertEqual(result["verified_question_count"], 0)
        self.assertEqual(result["conflicts"], ["Q"])

    def test_verified_record_with_blocker_is_not_packaged(self) -> None:
        blocked = {**record("Q", "PR39", "VERIFIED_COVERAGE_SOL"), "blocking_reasons": ["mutation"]}
        result = build_packages([blocked])
        self.assertEqual(result["verified_question_count"], 0)
        self.assertEqual(result["invalid_records"], ["Q"])

    def test_output_is_independent_of_input_order(self) -> None:
        rows = [
            record("B", "DAN12", "VERIFIED_COVERAGE_SOL"),
            record("A", "PR39", "VERIFIED_COMPETITIVE_SOL"),
        ]
        self.assertEqual(build_packages(rows), build_packages(reversed(rows)))


if __name__ == "__main__":
    unittest.main()
