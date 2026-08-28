from __future__ import annotations

import unittest

from scripts.lib.contextual_roles import (
    derive_contextual_role,
    mask_context_answer,
    render_contextual_identity,
    render_contextual_question,
)


def fact(**overrides):
    base = {
        "answer": "Daniel",
        "category": "person",
        "context": "Entonces el rey dijo a Daniel que respondiera.",
        "reference": "Daniel 2:16",
        "relation_type": "person",
        "relation_prompt": None,
        "_slot_signature": "person:proper",
    }
    return {**base, **overrides}


class ContextualRoleTests(unittest.TestCase):
    def test_classifies_explicit_and_syntactic_roles(self):
        self.assertEqual(derive_contextual_role(fact()), "recipient")
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="Jerusalén",
                    category="place",
                    context="vino a Jerusalén y la sitió",
                    _slot_signature="place:proper",
                )
            ),
            "destination",
        )
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="tres",
                    category="number",
                    context="durante tres años",
                    _slot_signature="number:number",
                )
            ),
            "duration",
        )
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="la maldición",
                    category="phrase",
                    relation_type="consequence",
                    relation_prompt="¿Qué consecuencia cayó sobre Israel?",
                    context="cayó sobre nosotros la maldición",
                )
            ),
            "consequence",
        )

    def test_masks_only_the_answer_and_never_leaks_it(self):
        row = fact(answer="Daniel", context="Daniel respondió al rey.")
        self.assertEqual(mask_context_answer(row), "[…] respondió al rey.")
        self.assertNotIn("Daniel", mask_context_answer(row))

    def test_renders_role_aware_question_without_generic_copy(self):
        question, role, evidence = render_contextual_question(fact())
        self.assertEqual(role, "recipient")
        self.assertIn("¿a quién", question)
        self.assertIn("[…]", evidence)
        self.assertNotIn("corresponde específicamente a esta escena", question)
        self.assertNotIn("Daniel", question)

    def test_renders_contextual_identity_with_one_answer_occurrence(self):
        statement, role, evidence = render_contextual_identity(fact())
        self.assertEqual(role, "recipient")
        self.assertIn("Daniel", statement)
        self.assertTrue(statement.startswith("en la escena"))
        self.assertEqual(statement.count("Daniel"), 1)
        self.assertNotIn("Daniel", evidence)
        self.assertNotIn("se menciona", statement.casefold())
        self.assertNotIn("se emplea", statement.casefold())

    def test_uses_conservative_category_fallbacks(self):
        question, role, _ = render_contextual_question(
            fact(
                answer="sabiduría",
                category="term",
                context="recibió sabiduría",
                _slot_signature=None,
            )
        )
        self.assertEqual(role, "concept")
        self.assertIn("concepto", question.casefold())

    def test_rejects_multiple_exact_answer_occurrences(self):
        with self.assertRaisesRegex(ValueError, "context_answer_count"):
            mask_context_answer(fact(context="Daniel habló con Daniel"))

    def test_balances_source_dialogue_quotes_inside_rendered_evidence(self):
        row = fact(context="Y el rey dijo: «Daniel respondió sin temor")
        question, _, evidence = render_contextual_question(row)
        statement, _, identity_evidence = render_contextual_identity(row)
        self.assertNotIn("«", evidence)
        self.assertNotIn("»", evidence)
        self.assertEqual(question.count("«"), question.count("»"))
        self.assertEqual(statement.count("«"), statement.count("»"))
        self.assertEqual(evidence, identity_evidence)

    def test_classifies_term_roles_from_local_syntax_when_signature_is_generic(self):
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="puestos",
                    category="term",
                    context="fueron puestos unos tronos",
                    _slot_signature="term:generic_nominal",
                )
            ),
            "predicate",
        )
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="impíamente",
                    category="term",
                    context="hemos actuado impíamente, hemos sido rebeldes",
                    _slot_signature="term:generic_nominal",
                )
            ),
            "modifier",
        )
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="tardes",
                    category="term",
                    context="la visión de las tardes y mañanas",
                    _slot_signature="term:generic_nominal",
                )
            ),
            "connector_object",
        )


if __name__ == "__main__":
    unittest.main()
