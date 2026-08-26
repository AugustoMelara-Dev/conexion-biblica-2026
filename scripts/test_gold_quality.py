import unittest
from collections import Counter
from pathlib import Path

from scripts.lib.gold_quality import (
    MANDATORY_CHAPTER_TYPE_MINIMUMS,
    MANDATORY_TYPE_TOTALS,
    EditorialStatus,
    audit_question,
    build_consolidation_bank,
    grammatical_signature,
    fill_anchor_is_sufficient,
    mandatory_mix_errors,
    make_editorial_true_false,
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
    def test_mandatory_contract_requires_five_thousand_and_all_three_types(self):
        self.assertEqual(MANDATORY_TYPE_TOTALS, {
            "fill_blank": 1500,
            "true_false": 1250,
            "multiple_choice": 2250,
        })
        self.assertEqual(sum(MANDATORY_TYPE_TOTALS.values()), 5000)
        for chapter in ("DAN7", "DAN8", "DAN9", "DAN11", "PR43", "PR44"):
            self.assertEqual(MANDATORY_CHAPTER_TYPE_MINIMUMS[chapter], {
                "fill_blank": 100,
                "true_false": 80,
                "multiple_choice": 170,
            })

    def test_editorial_false_statement_changes_one_plausible_detail(self):
        fact = {
            "fact_id": "DAN8-V04-F01",
            "bank": "DANIEL1-12",
            "chapter": "DAN8",
            "verse_or_page": "Daniel 8:4",
            "source_span": "Vi que el carnero hería con los cuernos al poniente, al norte y al sur.",
            "answer": "sur",
            "category": "word_singular",
            "topic": "direcciones del carnero",
        }
        distractor = {
            "fact_id": "DAN8-V09-F01",
            "verse_or_page": "Daniel 8:9",
            "answer": "oriente",
            "category": "word_singular",
        }

        result = make_editorial_true_false(fact, distractor, truth=False, question_id="DAN8-GOLD-0001")

        self.assertEqual(result["correct_answer"], "Falso")
        self.assertEqual(result["incorrect_detail"], "oriente")
        self.assertEqual(result["correction"], fact["source_span"])
        self.assertIn("poniente, al norte y al oriente", result["statement"])
        self.assertEqual(result["question"].count("oriente"), 1)

    def test_generated_bank_meets_every_mandatory_quota(self):
        result = build_consolidation_bank(Path.cwd())
        selected = result["selected"]

        self.assertEqual(mandatory_mix_errors(selected), [])
        self.assertEqual(Counter(row["type"] for row in selected), Counter(MANDATORY_TYPE_TOTALS))

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
