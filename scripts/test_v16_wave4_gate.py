#!/usr/bin/env python3
"""Contract tests for the Wave 4 R2 competitive gate."""

import unittest

from scripts import evaluate_v16_wave4_and_pilot2 as evaluator


class Wave4CompetitiveGateTests(unittest.TestCase):
    def test_exposes_a_pure_classifier(self):
        self.assertTrue(
            hasattr(evaluator, "classify_wave4_candidate"),
            "Wave 4 needs a pure fail-closed classifier before promotion",
        )

    def candidate(self, difficulty="HARD", plausible=2):
        question = {
            "correct_answer": "La respuesta canónica",
            "options": ["Distractor", "La respuesta canónica", "Otro", "Otro más"],
            "correct_option": 1,
        }
        review_a = {
            "selected_option_text": "La respuesta canónica",
            "recommendation": "ACCEPT",
            "length_or_precision_giveaway": False,
            "solved_by": "KNOWLEDGE",
            "initially_plausible_options_count": plausible,
            "real_difficulty": difficulty,
        }
        review_b = {
            "selected_option_text": "La respuesta canónica",
            "decision": "ACCEPT",
            "second_defensible_option": False,
            "semantic_category_check": "EXCELLENT",
            "novelty_check": True,
        }
        return question, review_a, review_b

    def test_clean_hard_candidate_is_competitive(self):
        self.assertEqual(
            evaluator.classify_wave4_candidate(*self.candidate()),
            "R2_COMPETITIVE_ACCEPT",
        )

    def test_clean_easy_candidate_is_coverage_not_competitive(self):
        self.assertEqual(
            evaluator.classify_wave4_candidate(*self.candidate(difficulty="EASY")),
            "R2_COVERAGE_ACCEPT",
        )

    def test_fewer_than_two_plausible_options_is_coverage_not_competitive(self):
        self.assertEqual(
            evaluator.classify_wave4_candidate(*self.candidate(plausible=1)),
            "R2_COVERAGE_ACCEPT",
        )

    def test_answer_text_mismatch_is_rejected(self):
        question, review_a, review_b = self.candidate()
        review_b["selected_option_text"] = "Distractor"
        self.assertEqual(
            evaluator.classify_wave4_candidate(question, review_a, review_b),
            "R2_REJECT",
        )

    def test_semantically_weak_candidate_is_rejected(self):
        question, review_a, review_b = self.candidate()
        review_b["semantic_category_check"] = "WEAK"
        self.assertEqual(
            evaluator.classify_wave4_candidate(question, review_a, review_b),
            "R2_REJECT",
        )

    def test_non_novel_candidate_is_rejected(self):
        question, review_a, review_b = self.candidate()
        review_b["novelty_check"] = False
        self.assertEqual(
            evaluator.classify_wave4_candidate(question, review_a, review_b),
            "R2_REJECT",
        )

    def test_prompt_already_in_public_bank_is_rejected(self):
        question, review_a, review_b = self.candidate()
        self.assertEqual(
            evaluator.classify_wave4_candidate(
                question,
                review_a,
                review_b,
                existing_question_texts={evaluator.normalize_text(question.get("question", ""))},
            ),
            "R2_REJECT",
        )


if __name__ == "__main__":
    unittest.main()
