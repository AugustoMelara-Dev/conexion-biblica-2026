from __future__ import annotations

import unittest

from scripts.lib import final_editorial


class FalseMutationSafetyTests(unittest.TestCase):
    def test_negation_moves_before_a_two_clitic_sequence(self):
        statement = "A mí, Daniel, se me turbó el espíritu hasta lo más hondo."
        self.assertEqual(
            final_editorial._negate_exact_action_statement(statement, "turbó"),
            "A mí, Daniel, no se me turbó el espíritu hasta lo más hondo.",
        )

    def test_detects_a_single_number_word_inside_a_compound_cardinal(self):
        fact = {
            "category": "number",
            "answer": "treinta",
            "context": "llegue a mil trescientos treinta y cinco días",
        }

        self.assertTrue(final_editorial._number_answer_is_compound_component(fact))

    def test_keeps_an_independent_number_eligible(self):
        fact = {
            "category": "number",
            "answer": "dos",
            "context": "vio a otros dos que estaban en pie",
        }

        self.assertFalse(final_editorial._number_answer_is_compound_component(fact))


if __name__ == "__main__":
    unittest.main()
