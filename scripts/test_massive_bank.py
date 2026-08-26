import unittest

from scripts.lib.massive_bank import (
    AtomicFact,
    BANK_TARGETS,
    MassiveQuestion,
    validate_massive_bank,
)
from scripts.lib.massive_generator import (
    SourceUnit,
    _candidate_spans,
    _select_facts_for_chapter,
    extract_all_daniel_verses,
    extract_pr_units,
    generate_questions_for_specs,
)

import fitz


def question(**overrides):
    values = {
        "id": "DAN1-0001",
        "fact_id": "DAN1-V1-F01",
        "variant_id": "DAN1-V1-F01-DIRECT-01",
        "template_id": "contextual-direct-v1",
        "bank": "DANIEL1-12",
        "chapter": "DAN1",
        "verse_or_page": "Daniel 1:1",
        "source_span": "vino Nabucodonosor, rey de Babilonia, a Jerusalén",
        "type": "multiple_choice",
        "difficulty": "hard",
        "topic": "cautiverio",
        "context_anchor": "En el tercer año del reinado de Joacim",
        "question": "Según Daniel 1:1, ¿qué rey vino a Jerusalén?",
        "options": ["Nabucodonosor", "Belsasar", "Darío", "Ciro"],
        "correct_answer": "Nabucodonosor",
        "accepted_answers": ["Nabucodonosor"],
        "answer_mode": "exact_text",
        "explanation": "Daniel 1:1 identifica a Nabucodonosor.",
        "why_distractors_fail": {
            "Belsasar": "Aparece en otra escena.",
            "Darío": "Aparece en otra escena.",
            "Ciro": "Aparece en otra escena.",
        },
        "source_quote": "vino Nabucodonosor, rey de Babilonia, a Jerusalén",
        "trap_type": "true_elsewhere",
        "blind_final_pool": False,
        "validation_status": "verified",
    }
    values.update(overrides)
    return MassiveQuestion(**values)


class MassiveBankContractTests(unittest.TestCase):
    def test_atomic_fact_keeps_source_relation_and_neighbors(self):
        fact = AtomicFact(
            fact_id="DAN1-V1-F01",
            bank="DANIEL1-12",
            chapter="DAN1",
            verse_or_page="Daniel 1:1",
            source_span="vino Nabucodonosor, rey de Babilonia, a Jerusalén",
            subject="Nabucodonosor",
            action="vino",
            object="a Jerusalén",
            context="tercer año de Joacim",
            relation_type="action",
            importance="high",
            nearby_fact_ids=("DAN1-V2-F01",),
        )
        self.assertEqual(fact.nearby_fact_ids, ("DAN1-V2-F01",))
        self.assertEqual(fact.source_span, "vino Nabucodonosor, rey de Babilonia, a Jerusalén")

    def test_validator_rejects_duplicate_variant_and_missing_quote(self):
        duplicate = question(id="DAN1-0002", source_quote="")
        errors = validate_massive_bank(
            [question(), duplicate],
            expected_total=2,
            expected_chapters={"DAN1": 2},
            enforce_distribution=False,
        )
        self.assertIn("duplicate variant_id: DAN1-V1-F01-DIRECT-01", errors)
        self.assertIn("DAN1-0002: missing source_quote", errors)

    def test_validator_enforces_exact_bank_distributions_and_blind_pool(self):
        self.assertEqual(BANK_TARGETS["DANIEL1-12"]["total"], 8000)
        self.assertEqual(BANK_TARGETS["PR39-44"]["total"], 6000)
        errors = validate_massive_bank(
            [question()],
            expected_total=8000,
            expected_chapters=BANK_TARGETS["DANIEL1-12"]["chapters"],
            enforce_distribution=True,
        )
        self.assertTrue(any("total" in error for error in errors))
        self.assertTrue(any("blind pool" in error for error in errors))


class PdfExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = fitz.open("MaterialConexionBiblica (1).pdf")

    @classmethod
    def tearDownClass(cls):
        cls.document.close()

    def test_extracts_every_verse_from_daniel_one_through_twelve(self):
        verses = extract_all_daniel_verses(self.document)
        expected_last = {
            1: 21,
            2: 49,
            3: 30,
            4: 37,
            5: 31,
            6: 28,
            7: 28,
            8: 27,
            9: 27,
            10: 21,
            11: 45,
            12: 13,
        }
        self.assertEqual(
            {chapter: len(items) for chapter, items in verses.items()},
            expected_last,
        )
        self.assertIn("Nabucodonosor", verses[1][1][1])
        self.assertIn("libro de la verdad", verses[10][21][1].lower())

    def test_extracts_pr_pages_27_through_59_with_chapter_labels(self):
        units = extract_pr_units(self.document)
        self.assertEqual({unit.page for unit in units}, set(range(27, 60)))
        self.assertEqual({unit.chapter for unit in units}, {"PR39", "PR40", "PR41", "PR42", "PR43", "PR44"})
        self.assertTrue(any("verdadero objeto de la vida" in unit.text.lower() for unit in units if unit.page == 59))


class QuestionGenerationTests(unittest.TestCase):
    def test_candidate_spans_do_not_turn_broken_parenthetical_references_into_answers(self):
        candidates = _candidate_spans(
            "Daniel prefirió perder la vida antes que renunciar a su voluntad” (Daniel 1:9) del oficial."
        )
        answers = [candidate[2] for candidate in candidates]

        self.assertFalse(any("(" in answer or ")" in answer or "”" in answer for answer in answers))
        self.assertNotIn("9", answers)

    def test_fact_selection_spans_the_entire_chapter_when_locators_exceed_quota(self):
        facts = [
            AtomicFact(
                fact_id=f"DAN1-V{index:02d}-F01",
                bank="DANIEL1-12",
                chapter="DAN1",
                verse_or_page=f"Daniel 1:{index}",
                source_span=f"Detalle verificable número {index}",
                subject="Detalle",
                action="identifica",
                object=str(index),
                context=f"Daniel 1:{index}",
                relation_type="detail",
                importance="high",
                nearby_fact_ids=(),
                answer=str(index),
                category="number",
                topic="cobertura",
                sequence=index,
            )
            for index in range(1, 11)
        ]

        selected = _select_facts_for_chapter(facts, target=24)

        self.assertEqual(len(selected), 4)
        self.assertEqual(selected[0].verse_or_page, "Daniel 1:1")
        self.assertEqual(selected[-1].verse_or_page, "Daniel 1:10")

    def test_generates_distinct_variants_with_exact_small_quotas(self):
        texts = [
            "Daniel respondió al rey y pidió tiempo para mostrar la interpretación.",
            "Arioc llevó prontamente a Daniel delante del rey Nabucodonosor.",
            "Ananías, Misael y Azarías pidieron misericordias al Dios del cielo.",
            "El misterio fue revelado a Daniel en visión de noche.",
            "Daniel bendijo al Dios del cielo por la sabiduría y el poder.",
            "Nabucodonosor reconoció que el Dios de Daniel revela los misterios.",
        ]
        units = [
            SourceUnit(
                bank="DANIEL1-12",
                chapter="DAN2",
                page=5,
                locator=f"V{index:02d}-S01",
                source_ref=f"PDF p.5, Daniel 2:{index}",
                topic="oración e interpretación",
                sequence=index,
                text=text,
            )
            for index, text in enumerate(texts, 1)
        ]
        questions, facts, _ = generate_questions_for_specs(
            units,
            bank="DANIEL1-12",
            chapter_targets={"DAN2": 20},
        )
        self.assertEqual(len(questions), 20)
        self.assertGreaterEqual(min(sum(q.fact_id == fact.fact_id for q in questions) for fact in facts), 4)
        self.assertEqual(len({q.variant_id for q in questions}), 20)
        self.assertEqual(sum(q.type == "true_false" for q in questions), 5)
        self.assertEqual(sum(q.type == "fill_blank" for q in questions), 6)
        self.assertEqual(sum(q.type == "multiple_choice" for q in questions), 9)
        self.assertGreaterEqual(sum(q.blind_final_pool for q in questions), 3)
        sequence_questions = [q for q in questions if q.trap_type == "order_sequence"]
        self.assertGreaterEqual(len(sequence_questions), 1)
        self.assertTrue(all("→" in option for q in sequence_questions for option in q.options))


if __name__ == "__main__":
    unittest.main()
