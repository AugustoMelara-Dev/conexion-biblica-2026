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

    def test_distinguishes_territorial_titles_from_movement_origins(self):
        title_fact = fact(
            answer="Judá",
            category="place",
            context="Joacim, rey de Judá, gobernaba en Jerusalén.",
            _slot_signature="place:proper",
        )
        origin_fact = fact(
            answer="Babilonia",
            category="place",
            context="El mensajero salió de Babilonia rumbo a Jerusalén.",
            _slot_signature="place:proper",
        )

        title_question, title_role, _ = render_contextual_question(title_fact)
        self.assertEqual(title_role, "territorial_title")
        self.assertIn("título territorial", title_question)
        self.assertIn("presente en", title_question)
        self.assertEqual(derive_contextual_role(origin_fact), "origin")

    def test_does_not_treat_every_de_relation_as_an_origin(self):
        relation_fact = fact(
            answer="Ufaz",
            category="place",
            context="ceñida su cintura con oro de Ufaz",
            _slot_signature="place:proper",
        )

        question, role, _ = render_contextual_question(relation_fact)
        self.assertEqual(role, "geographic_relation")
        self.assertIn("relación geográfica", question)

    def test_requires_actual_movement_before_calling_a_place_a_destination(self):
        oriented_place = fact(
            answer="Jerusalén",
            category="place",
            context="las ventanas de su habitación daban a Jerusalén",
            _slot_signature="place:proper",
        )
        moved_place = fact(
            answer="Babilonia",
            category="place",
            context="los cautivos fueron llevados a Babilonia",
            _slot_signature="place:proper",
        )

        self.assertEqual(derive_contextual_role(oriented_place), "geographic_relation")
        self.assertEqual(derive_contextual_role(moved_place), "destination")

    def test_uses_neutral_geographic_copy_for_unmarked_places(self):
        place_fact = fact(
            answer="Babilonia",
            category="place",
            context="¿No es ésta la gran Babilonia que yo edifiqué?",
            _slot_signature="place:proper",
        )

        question, role, _ = render_contextual_question(place_fact)
        self.assertEqual(role, "location")
        self.assertIn("detalle geográfico", question)
        self.assertNotIn("relación espacial", question)

    def test_names_collective_entities_without_calling_them_characters(self):
        entity_fact = fact(
            answer="Israel",
            context="que trajera de los hijos de Israel",
        )

        question, role, _ = render_contextual_question(entity_fact)
        self.assertEqual(role, "named_entity")
        self.assertIn("nombre o designación", question)
        self.assertNotIn("personaje", question)

    def test_describes_action_answers_as_verbal_forms(self):
        action_fact = fact(
            answer="hubiera",
            category="action",
            context="muchachos en quienes no hubiera tacha alguna",
            _slot_signature="action:verb",
        )

        question, role, _ = render_contextual_question(action_fact)
        self.assertEqual(role, "action")
        self.assertIn("forma verbal", question)

    def test_uses_grammatically_safe_copy_for_mixed_predicates(self):
        predicate_fact = fact(
            answer="conmigo",
            category="term",
            context="los hombres que estaban conmigo",
            _slot_signature="term:adjective",
        )

        question, role, _ = render_contextual_question(predicate_fact)
        self.assertEqual(role, "predicate")
        self.assertIn("término", question)
        self.assertNotIn("cualidad o estado", question)

    def test_classifies_ordinal_terms_as_order(self):
        ordinal_fact = fact(
            answer="tercer",
            category="term",
            context="En el tercer año del reinado",
            _slot_signature="term:adjective",
        )

        self.assertEqual(derive_contextual_role(ordinal_fact), "order")

    def test_identity_count_uses_whole_phrases_not_substrings(self):
        action_fact = fact(
            answer="ver",
            category="action",
            context="Me parecía ver en medio de la tierra un árbol.",
            _slot_signature="action:verb",
        )

        try:
            statement, role, _ = render_contextual_identity(action_fact)
        except ValueError as error:
            self.fail(f"la subcadena 'ver' en 'verbal' no debe contar: {error}")
        self.assertEqual(role, "action")
        self.assertIn("forma verbal", statement)
        self.assertTrue(statement.endswith("es «ver»."))

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
