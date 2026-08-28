from __future__ import annotations

import unittest

from scripts.lib import final_editorial


def semantic_option_key(value: str) -> str:
    implementation = getattr(final_editorial, "semantic_option_key", lambda candidate: candidate)
    return implementation(value)


def semantic_option_collision_count(questions: list[dict[str, object]]) -> int:
    implementation = getattr(
        final_editorial,
        "semantic_option_collision_count",
        lambda _: -1,
    )
    return implementation(questions)


class SemanticOptionTests(unittest.TestCase):
    def test_groups_cross_language_and_transliteration_aliases(self):
        alias_groups = (
            ("Jerusalén", "Jerusalem"),
            ("Abed-nego", "Abednego"),
            ("Mesac", "Mesach"),
            ("Sadrac", "Sadrach"),
        )

        for left, right in alias_groups:
            with self.subTest(left=left, right=right):
                self.assertEqual(semantic_option_key(left), semantic_option_key(right))

    def test_keeps_distinct_biblical_entities_separate(self):
        self.assertNotEqual(semantic_option_key("Jerusalén"), semantic_option_key("Judá"))
        self.assertNotEqual(semantic_option_key("Sadrac"), semantic_option_key("Mesac"))

    def test_counts_questions_with_semantically_duplicate_options(self):
        questions = [
            {"options": ["Jerusalén", "Jerusalem", "Judá", "Babilonia"]},
            {"options": ["Sadrac", "Mesac", "Abed-nego", "Daniel"]},
        ]

        self.assertEqual(semantic_option_collision_count(questions), 1)


if __name__ == "__main__":
    unittest.main()
