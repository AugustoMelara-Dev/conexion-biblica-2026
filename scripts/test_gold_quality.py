import unittest

from scripts.lib.gold_quality import (
    EditorialStatus,
    audit_question,
    grammatical_signature,
    fill_anchor_is_sufficient,
    normalize_reference,
    partition_blind_facts,
)


def question(**overrides):
    base = {
        "id": "DAN7-0001",
        "fact_id": "DAN7-V09-S03-F01",
        "variant_id": "DAN7-V09-S03-F01-MC-1",
        "template_id": "mc-contextual-v1",
        "chapter": "DAN7",
        "verse_or_page": "16, Daniel 7:9",
        "type": "multiple_choice",
        "difficulty": "hard",
        "question": "Según Daniel 7:9, ¿con qué se compara el pelo del Anciano de días?",
        "options": ["Lana limpia", "Nieve", "Bronce bruñido", "Fuego"],
        "correct_answer": "Lana limpia",
        "source_span": "el pelo de su cabeza, como lana limpia",
        "source_quote": "el pelo de su cabeza, como lana limpia",
        "explanation": "Daniel 7:9 compara el pelo con lana limpia.",
        "why_distractors_fail": {
            "Nieve": "El vestido era blanco como la nieve.",
            "Bronce bruñido": "Corresponde a Daniel 10.",
            "Fuego": "Describe el trono, no el pelo.",
        },
    }
    base.update(overrides)
    return base


class GoldQualityTests(unittest.TestCase):
    def test_normalizes_pdf_page_prefix_out_of_bible_reference(self):
        self.assertEqual(normalize_reference("16, Daniel 7:9"), "Daniel 7:9")

    def test_preserves_pr_chapter_page_and_paragraph(self):
        self.assertEqual(
            normalize_reference("47, PR43, párrafo 2"),
            "PR43, p. 47, párrafo 2",
        )
        self.assertEqual(
            normalize_reference("PR43, p. 47, párrafo 2"),
            "PR43, p. 47, párrafo 2",
        )

    def test_quarantines_lexical_sequence_template(self):
        decision = audit_question(
            question(
                template_id="mc-sequence-v1",
                question="Ordene Joacim, Nabucodonosor, Señor.",
            )
        )
        self.assertEqual(decision.status, EditorialStatus.QUARANTINE)
        self.assertIn("lexical_sequence", decision.rejection_reasons)

    def test_quarantines_generated_false_true_false_substitution(self):
        decision = audit_question(
            question(
                type="true_false",
                template_id="tf-single-detail-v1",
                correct_answer="Falso",
                question="Daniel tuvo ⟦Arioc⟧ en toda visión y sueños.",
                options=["Verdadero", "Falso"],
            )
        )
        self.assertEqual(decision.status, EditorialStatus.QUARANTINE)
        self.assertIn("unsafe_false_substitution", decision.rejection_reasons)

    def test_quarantines_when_quote_does_not_support_answer(self):
        decision = audit_question(question(source_quote="El Juez se sentó"))
        self.assertEqual(decision.status, EditorialStatus.QUARANTINE)
        self.assertIn("unsupported_answer", decision.rejection_reasons)

    def test_gold_requires_score_of_at_least_85_and_no_rejection(self):
        decision = audit_question(question())
        self.assertEqual(decision.status, EditorialStatus.GOLD)
        self.assertGreaterEqual(decision.score, 85)
        self.assertEqual(decision.normalized_reference, "Daniel 7:9")

    def test_blind_partitions_are_disjoint_and_keep_emergency_separate(self):
        pools = partition_blind_facts([f"DAN7-F{i:03d}" for i in range(30)])
        a, b, emergency = map(set, (pools["A"], pools["B"], pools["emergency"]))
        self.assertFalse(a & b or a & emergency or b & emergency)
        self.assertEqual(len(a | b | emergency), 30)

    def test_grammatical_signature_separates_nominal_and_verbal_fragments(self):
        self.assertNotEqual(
            grammatical_signature("rey del norte", frozenset({"phrase_singular"})),
            grammatical_signature("estaban de parte", frozenset({"phrase_singular"})),
        )
        self.assertNotEqual(
            grammatical_signature("hacerse fuerte", frozenset({"phrase_singular"})),
            grammatical_signature("tomará el reino", frozenset({"phrase_singular"})),
        )
        self.assertNotEqual(
            grammatical_signature("rey del norte", frozenset({"phrase_singular"})),
            grammatical_signature("hija por mujer", frozenset({"phrase_singular"})),
        )

    def test_fill_anchor_requires_context_on_both_sides(self):
        self.assertFalse(
            fill_anchor_is_sufficient("relaciones que existen entre las naciones.", "relaciones")
        )
        self.assertTrue(
            fill_anchor_is_sufficient(
                "Todo lo anterior permite comprender las relaciones que existen entre las naciones hoy.",
                "relaciones",
            )
        )

    def test_large_blind_reserve_guarantees_two_hundred_fact_simulations(self):
        pools = partition_blind_facts([f"DAN7-F{i:03d}" for i in range(250)])
        self.assertEqual(len(pools["A"]), 100)
        self.assertEqual(len(pools["B"]), 100)
        self.assertEqual(len(pools["emergency"]), 50)


if __name__ == "__main__":
    unittest.main()
