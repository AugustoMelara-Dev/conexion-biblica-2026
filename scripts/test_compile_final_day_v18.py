from __future__ import annotations

import unittest

from scripts.compile_final_day_v18 import adjudicate_item


def stored(question_id: str = "Q-1", answer: str = "B") -> dict:
    return {
        "id": question_id,
        "chapter": "PR39",
        "question": "Según Profetas y Reyes, ¿qué afirma la fuente?",
        "options": ["A", "B", "C", "D"],
        "correct_option": 1,
        "correct_answer": answer,
        "source_unit_id": "PR39-U1",
        "source_ref": "PR39, p. 27",
        "source_quote": "La fuente afirma B.",
        "fact_id": "F-1",
    }


def dossier() -> dict:
    return {
        "audit_run_id": "run",
        "question_id": "Q-1",
        "question": "Según Profetas y Reyes, ¿qué afirma la fuente?",
        "options": ["D", "B", "A", "C"],
        "source_unit_id": "PR39-U1",
        "source_ref": "PR39, p. 27",
        "pdf_page": 27,
        "exact_quote": "La fuente afirma B.",
        "nearby_context": "Contexto.",
        "material": "Profetas y Reyes",
        "chapter": "PR39",
    }


def sol(decision: str = "ACCEPT_COVERAGE", selected: str = "B") -> dict:
    return {
        "question_id": "Q-1",
        "selected_option_index": 1,
        "selected_option_text": selected,
        "exact_supporting_phrase": "afirma B",
        "stem_fully_supported": True,
        "one_unambiguous_answer": True,
        "second_defensible_option": False,
        "second_defensible_text": None,
        "source_boundary": "PR_ONLY",
        "option_analysis": [
            {"text": text, "verdict": "CORRECT" if text == "B" else "FALSE_BY_SOURCE", "source_ref": "PR39, p. 27", "exact_reason": "Razón específica"}
            for text in ["D", "B", "A", "C"]
        ],
        "answer_length_giveaway": False,
        "grammar_giveaway": False,
        "precision_giveaway": False,
        "duplicate_or_superficial_variant": False,
        "real_difficulty": "MEDIUM" if decision == "ACCEPT_COVERAGE" else "HARD",
        "decision": decision,
        "specific_reason": "Respaldo inequívoco.",
        "model": "GPT-5.6 Sol",
        "reasoning_effort": "medium",
        "agent_id": "/root/auditor",
        "conversation_id": "/root/auditor",
    }


def blind(selected: str = "B", plausible: int = 2) -> dict:
    return {
        "question_id": "Q-1",
        "selected_option_index": 2,
        "selected_option_text": selected,
        "confidence_0_100": 90,
        "second_option_index": 0,
        "second_option_text": "A",
        "initially_plausible_options_count": plausible,
        "solved_by": "KNOWLEDGE",
        "clues_detected": [],
        "apparent_difficulty": "HARD",
        "specific_reason": "Sin ambigüedad.",
        "model": "GPT-5.6 Luna",
        "reasoning_effort": "max",
        "agent_id": "/root/blind",
        "conversation_id": "/root/blind",
        "recommendation": "ACCEPT",
    }


class AdjudicationTests(unittest.TestCase):
    def test_accepts_coverage_only_when_all_three_answers_match(self) -> None:
        result = adjudicate_item(stored(), dossier(), sol(), blind())
        self.assertEqual(result["audit_status"], "VERIFIED_COVERAGE_SOL")
        self.assertEqual(result["selected_answer"], "B")

    def test_answer_mismatch_is_not_silently_corrected(self) -> None:
        result = adjudicate_item(stored(answer="C"), dossier(), sol(), blind())
        self.assertEqual(result["audit_status"], "ANSWER_MISMATCH")
        self.assertIn("stored", result["blocking_reasons"])

    def test_blind_disagreement_withholds_promotion(self) -> None:
        result = adjudicate_item(stored(), dossier(), sol(), blind(selected="A"))
        self.assertEqual(result["audit_status"], "REWRITE_REQUIRED")
        self.assertIn("blind", result["blocking_reasons"])

    def test_competitive_requires_two_plausible_options_and_no_clues(self) -> None:
        result = adjudicate_item(
            stored(), dossier(), sol("ACCEPT_COMPETITIVE"), blind(plausible=1)
        )
        self.assertEqual(result["audit_status"], "REWRITE_REQUIRED")
        self.assertIn("competitive_blind_quality", result["blocking_reasons"])

    def test_rewrite_decision_cannot_be_promoted(self) -> None:
        result = adjudicate_item(stored(), dossier(), sol("REWRITE"), blind())
        self.assertEqual(result["audit_status"], "REWRITE_REQUIRED")

    def test_fake_or_non_independent_blind_cannot_be_promoted(self) -> None:
        invalid = blind()
        invalid["model"] = "fake"
        invalid["reasoning_effort"] = "low"
        invalid["conversation_id"] = "/root/auditor"
        result = adjudicate_item(stored(), dossier(), sol(), invalid)
        self.assertEqual(result["audit_status"], "INVALID_OUTPUT")
        self.assertIn("blind_authority", result["blocking_reasons"])

    def test_blind_rewrite_recommendation_requires_rewrite(self) -> None:
        rewrite = blind()
        rewrite["recommendation"] = "REWRITE"
        result = adjudicate_item(stored(), dossier(), sol(), rewrite)
        self.assertEqual(result["audit_status"], "REWRITE_REQUIRED")
        self.assertIn("blind_quality", result["blocking_reasons"])

    def test_same_agent_with_different_conversation_is_not_independent(self) -> None:
        invalid = blind()
        invalid["agent_id"] = "/root/auditor"
        invalid["conversation_id"] = "/root/another-turn"
        result = adjudicate_item(stored(), dossier(), sol(), invalid)
        self.assertEqual(result["audit_status"], "INVALID_OUTPUT")
        self.assertIn("blind_authority", result["blocking_reasons"])

    def test_post_review_mutation_is_rejected(self) -> None:
        changed = dossier()
        changed["question"] = "Según Profetas y Reyes, texto mutado"
        result = adjudicate_item(stored(), changed, sol(), blind())
        self.assertEqual(result["audit_status"], "INVALID_OUTPUT")
        self.assertIn("content_mutation", result["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
