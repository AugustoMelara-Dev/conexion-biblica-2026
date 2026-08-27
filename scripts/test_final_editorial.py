from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "public/banks/final-2026/source_inventory.json"


class FinalEditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.editorial = importlib.import_module("scripts.lib.final_editorial")
        except ModuleNotFoundError:
            cls.editorial = None
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        if cls.editorial is not None:
            cls.facts, cls.fact_rejected = cls.editorial.derive_atomic_facts(
                cls.inventory["units"]
            )
            cls.questions, cls.question_rejected = cls.editorial.generate_gold_questions(
                cls.facts
            )

    def require_editorial(self):
        self.assertIsNotNone(self.editorial, "falta scripts.lib.final_editorial")
        return self.editorial

    def test_derives_3000_facts_and_covers_every_source_unit(self) -> None:
        editorial = self.require_editorial()
        if editorial is None:
            return
        facts, rejected = self.facts, self.fact_rejected
        self.assertEqual(len(facts), 3000)
        self.assertGreater(rejected, 0)
        covered = {fact["source_unit_id"] for fact in facts}
        expected = {
            unit["source_unit_id"]
            for unit in self.inventory["units"]
            if unit["source_unit_id"] not in editorial.EDITORIALLY_EXCLUDED_SOURCE_UNITS
        }
        self.assertEqual(covered, expected)
        self.assertEqual(len({fact["fact_id"] for fact in facts}), 3000)
        self.assertEqual(
            Counter(fact["chapter"] for fact in facts),
            editorial.FACT_QUOTAS,
        )
        self.assertLessEqual(
            sum(fact["category"] == "phrase" for fact in facts),
            250,
        )
        self.assertGreaterEqual(
            sum(bool(fact.get("relation_prompt")) for fact in facts),
            40,
            "el banco ampliado debe incluir relaciones explícitas, no solo huecos léxicos",
        )
        self.assertTrue(all(fact["answer"] in fact["source_quote"] for fact in facts))
        self.assertTrue(
            all(
                fact["category"] != "phrase" or len(fact["answer"].split()) >= 2
                for fact in facts
            )
        )
        self.assertTrue(
            all(
                fact["category"] != "number"
                or len(fact["answer"].split()) == 1
                or editorial._word_role(fact["answer"].split()[0]) == "number"
                or any(
                    fact["answer"] == answer
                    for overrides in editorial.ADDITIONAL_EDITORIAL_OVERRIDES.values()
                    for answer, category in overrides
                    if category == "number"
                )
                for fact in facts
            ),
            "los períodos numéricos no deben incluir preposiciones o verbos ajenos al detalle",
        )
        non_actions = {
            "abundancia", "angustia", "ciencia", "frecuencia", "gloria",
            "gracia", "inteligencia", "justicia", "misericordia", "presencia",
            "profecía", "provincia", "sabiduría", "sentencia", "todavía",
            "victoria",
        }
        self.assertFalse(
            any(
                fact["category"] == "action"
                and fact["answer"].casefold() in non_actions
                for fact in facts
            ),
            "los sustantivos no pueden presentarse como acciones",
        )
        self.assertFalse(
            any(
                re.search(
                    r"[.!?]\d{1,3}$",
                    unit.get("full_text") or unit.get("exact_text", ""),
                )
                for unit in self.inventory["units"]
            )
        )
        self.assertFalse(
            any(fact["answer"] == "A los israelitas Moisés" for fact in facts)
        )
        dangling = {
            "a", "al", "con", "contra", "de", "del", "en", "entre",
            "hacia", "hasta", "para", "por", "que", "sin", "sobre", "y", "o",
        }
        self.assertFalse(
            any(fact["answer"].casefold().split()[-1] in dangling for fact in facts)
        )

    def test_named_entities_and_sentence_starters_are_not_mixed(self) -> None:
        facts_by_answer = {}
        for fact in self.facts:
            facts_by_answer.setdefault(fact["answer"], []).append(fact)

        self.assertTrue(
            any(
                fact["answer"] == "Aspenaz" and fact["category"] == "person"
                for fact in self.facts
            ),
            "Aspenaz debe clasificarse como persona, no como término genérico",
        )
        self.assertFalse(
            any(
                fact["answer"] in {"Nuestro", "Pasados", "Además", "Mediante"}
                for fact in self.facts
            ),
            "una mayúscula por inicio de oración no convierte la palabra en hecho competitivo",
        )
        self.assertFalse(
            any(
                fact["source_unit_id"] == "DAN1-V003"
                and fact["answer"] == "Israel"
                and fact["category"] == "place"
                for fact in self.facts
            ),
            "en «hijos de Israel», Israel no debe preguntarse como lugar",
        )
        self.assertFalse(
            any(
                fact["category"] == "person"
                and fact["answer"] in {"santo", "invisible", "anciano"}
                for fact in self.facts
            ),
            "adjetivos y sustantivos comunes en minúscula no son personajes",
        )
        pr39_spirit = [
            fact for fact in self.facts
            if fact["source_unit_id"] == "PR39-P030-P002-S002"
        ]
        self.assertTrue(any(fact["answer"] == "Espíritu Santo" for fact in pr39_spirit))
        self.assertFalse(any(fact["answer"] == "Santo" for fact in pr39_spirit))

    def test_atomic_facts_are_not_inflated_by_the_same_answer(self) -> None:
        answer_counts = Counter(
            self.editorial._norm(fact["answer"]) for fact in self.facts
        )
        self.assertLessEqual(
            max(answer_counts.values()),
            60,
            answer_counts.most_common(10),
        )
        for chapter in {fact["chapter"] for fact in self.facts}:
            chapter_counts = Counter(
                self.editorial._norm(fact["answer"])
                for fact in self.facts
                if fact["chapter"] == chapter
            )
            self.assertLessEqual(
                max(chapter_counts.values()),
                10,
                (chapter, chapter_counts.most_common(10)),
            )

        category_counts = Counter(fact["category"] for fact in self.facts)
        self.assertGreaterEqual(category_counts["person"], 150, category_counts)
        self.assertGreaterEqual(category_counts["place"], 60, category_counts)
        self.assertGreaterEqual(category_counts["number"], 80, category_counts)
        self.assertGreaterEqual(category_counts["action"], 350, category_counts)
        self.assertGreaterEqual(category_counts["term"], 350, category_counts)

    def test_context_does_not_split_an_abbreviated_verse_reference(self) -> None:
        editorial = self.require_editorial()
        if editorial is None:
            return
        text = (
            "Las palabras: “Tú eres aquella cabeza de oro” (Vers. 38), "
            "habían hecho una profunda impresión en la mente del gobernante."
        )
        self.assertEqual(editorial._context_for(text, "38"), text)

    def test_generates_12000_gold_questions_with_the_approved_mix(self) -> None:
        editorial = self.require_editorial()
        if editorial is None:
            return
        facts = self.facts
        questions, rejected = self.questions, self.question_rejected
        self.assertEqual(len(questions), 12000)
        self.assertGreater(rejected, 0)
        self.assertEqual(
            Counter(question["family"] for question in questions),
            {
                "single_choice_direct": 3000,
                "fill_choice": 3000,
                "true_false": 3000,
                "single_choice_contextual": 3000,
            },
        )
        self.assertEqual(
            Counter(question["difficulty"] for question in questions),
            {"easy": 600, "medium": 2400, "hard": 5400, "expert": 3600},
        )
        self.assertTrue(
            all(question["final_editorial_status"] == "GOLD" for question in questions)
        )
        self.assertTrue(
            all(question["bank_id"] == "BANCO_UNICO_CONEXION_BIBLICA_2026" for question in questions)
        )

    def test_difficulty_labels_follow_competitive_complexity(self) -> None:
        easy = [question for question in self.questions if question["difficulty"] == "easy"]
        expert = [question for question in self.questions if question["difficulty"] == "expert"]
        self.assertFalse(
            any(question["family"] == "single_choice_contextual" for question in easy),
            "una trampa contextual no puede etiquetarse como fácil",
        )
        self.assertFalse(
            any(
                question["family"] == "true_false"
                and question["correct_answer"] == "Falso"
                for question in easy
            ),
            "una alteración plausible no puede etiquetarse como fácil",
        )
        self.assertGreaterEqual(
            sum(question["family"] == "single_choice_contextual" for question in expert),
            1800,
            Counter(question["family"] for question in expert),
        )
        self.assertGreaterEqual(
            sum(question["family"] == "single_choice_direct" for question in expert),
            270,
        )
        self.assertGreaterEqual(
            sum(question["family"] == "true_false" for question in expert),
            210,
        )
        self.assertGreaterEqual(
            sum(
                question["family"] == "single_choice_direct"
                and question["blind_pool"] is None
                for question in expert
            ),
            100,
        )

    def test_blind_reserve_contains_fifteen_percent_of_facts_without_overlap(self) -> None:
        blind_by_fact = {}
        for question in self.questions:
            if question["blind_pool"]:
                blind_by_fact.setdefault(question["fact_id"], set()).add(
                    question["blind_pool"]
                )
        self.assertEqual(len(blind_by_fact), 450)
        self.assertTrue(all(len(pools) == 1 for pools in blind_by_fact.values()))
        self.assertEqual(
            Counter(next(iter(pools)) for pools in blind_by_fact.values()),
            {"A": 150, "B": 150, "emergency": 150},
        )

    def test_each_family_has_only_one_answer_and_compatible_options(self) -> None:
        editorial = self.require_editorial()
        if editorial is None:
            return
        questions = self.questions
        for question in questions:
            expected_options = 2 if question["family"] == "true_false" else 4
            self.assertEqual(len(question["options"]), expected_options, question["id"])
            self.assertEqual(len(set(question["options"])), expected_options, question["id"])
            self.assertGreaterEqual(question["correct_option"], 0, question["id"])
            self.assertLess(question["correct_option"], expected_options, question["id"])
            self.assertEqual(
                question["correct_answer"],
                question["options"][question["correct_option"]],
                question["id"],
            )
            self.assertEqual(question["validation_adversarial"]["status"], "passed")
            self.assertEqual(
                question["validation_adversarial"]["selected_option"],
                question["correct_option"],
            )

    def test_each_family_obeys_its_visible_question_contract(self) -> None:
        blank = re.compile(r"_{4,}")
        for question in self.questions:
            blank_count = len(blank.findall(question["question"]))
            if question["family"] == "true_false":
                self.assertEqual(blank_count, 0, question["id"])
                self.assertIn(question["statement"], question["question"], question["id"])
                self.assertNotIn("completa la frase", question["question"], question["id"])
                self.assertNotIn("[…]", question["question"], question["id"])
                self.assertNotIn("expresión que ocupa", question["question"], question["id"])
                if question["option_category"] in {"phrase", "term"}:
                    self.assertEqual(question["correct_answer"], "Verdadero", question["id"])
                if (
                    question["correct_answer"] == "Falso"
                    and question["option_category"] == "action"
                ):
                    self.assertIn(
                        self.editorial._action_form(question["correction"]),
                        self.editorial.SAFE_FALSE_ACTION_FORMS,
                        question["id"],
                    )

            else:
                expected_blanks = 0 if question["family"] == "single_choice_contextual" else 1
                self.assertEqual(blank_count, expected_blanks, question["id"])
            if question["family"] == "fill_choice":
                self.assertTrue(question["question"].startswith("Complete "), question["id"])
            if question["family"] == "single_choice_contextual":
                self.assertEqual(question["trap_type"], "true_in_other_context", question["id"])
                self.assertEqual(len(question["why_distractors_fail"]), 3, question["id"])
                fact = next(
                    fact for fact in self.facts if fact["fact_id"] == question["fact_id"]
                )
                self.assertEqual(question["correct_answer"], fact["answer"], question["id"])
                self.assertEqual(len(set(question["options"])), 4, question["id"])
                self.assertFalse(
                    any(
                        re.fullmatch(
                            r"Daniel \d+:\d+|PR\d+, p\. \d+(?:, párrafo \d+)?",
                            option,
                        )
                        for option in question["options"]
                    ),
                    question["id"],
                )

    def test_true_false_never_uses_focused_answer_reveal_templates(self) -> None:
        """V/F debe evaluar una afirmación completa, no regalar el detalle evaluado."""
        focused = [
            question["id"]
            for question in self.questions
            if question["family"] == "true_false"
            and question.get("focused_true_statement")
        ]
        self.assertEqual(focused, [])
        for question in self.questions:
            if question["family"] != "true_false":
                continue
            self.assertNotIn(
                "al evaluar específicamente",
                question["statement"].casefold(),
                question["id"],
            )

    def test_true_false_is_balanced_unique_and_uses_only_safe_false_details(self) -> None:
        """El equilibrio no puede depender de duplicados ni sustituciones abiertas."""
        self.assertIsNone(
            self.editorial._negate_exact_action_statement(
                "Compara luego nuestros rostros con los otros rostros.",
                "Compara",
            )
        )
        rows = [
            question for question in self.questions
            if question["family"] == "true_false"
        ]
        self.assertEqual(
            Counter(row["correct_answer"] for row in rows),
            {"Verdadero": 1500, "Falso": 1500},
        )
        self.assertEqual(len({row["question"] for row in rows}), 3000)
        rows_by_fact = {}
        for row in rows:
            rows_by_fact.setdefault(row["fact_id"], []).append(row)
        self.assertEqual(len(rows_by_fact), 1500)
        self.assertTrue(
            all(
                {row["correct_answer"] for row in fact_rows}
                == {"Verdadero", "Falso"}
                for fact_rows in rows_by_fact.values()
            )
        )
        for false_row in (row for row in rows if row["correct_answer"] == "Falso"):
            self.assertIn(
                false_row["option_category"],
                {"person", "place", "number", "action"},
                false_row["id"],
            )
            if (
                false_row["option_category"] == "action"
                and false_row["statement_mode"] == "exact_source"
            ):
                self.assertEqual(
                    false_row.get("false_mutation_kind"),
                    "negation",
                    false_row["id"],
                )
                self.assertTrue(
                    false_row["incorrect_detail"].casefold().startswith("no "),
                    false_row["id"],
                )
            if (
                false_row["option_category"] == "person"
                and self.editorial._norm(false_row["correction"])
                in self.editorial.DIVINE_NAMES
            ):
                self.assertEqual(
                    false_row["statement_mode"],
                    "atomic_presence",
                    false_row["id"],
                )

        self.assertFalse(
            any(
                fact["category"] == "action"
                and self.editorial._norm(fact["answer"]) == "triste"
                for fact in self.facts
            )
        )

    def test_known_broken_formulations_can_never_reenter_gold(self) -> None:
        broken_fragments = {
            "confusión púrpura",
            "se hizo enhiesta",
            "por tanto, fuese el sueño",
            "con fe, oraron por sabiduría y varón",
            "verdadero éxito de ellos mejor",
            "perdió llamar",
            "pasaba dar cuenta",
            "se selló aceleradamente al puesto",
            "el rostro hablaba un relámpago",
            "prosperó bien a darío",
        }
        visible_text = "\n".join(
            question["question"].casefold() for question in self.questions
        )
        for fragment in broken_fragments:
            self.assertNotIn(fragment, visible_text)

    def test_curated_pr_phrases_are_complete_meaningful_units(self) -> None:
        answers = {fact["answer"] for fact in self.facts}
        self.assertTrue(
            {
                "principio divino de cooperación",
                "facultades superiores del ser",
                "leyes inmutables",
                "una gran verdad al monarca babilónico",
                "libres para elegir a quien quieren servir",
                "último libro del Nuevo Testamento",
            }.issubset(answers)
        )
        self.assertTrue(
            {
                "divino de cooperación",
                "superiores del ser",
                "dependen de leyes",
                "gran verdad al monarca",
                "último libro",
            }.isdisjoint(answers)
        )

    def test_relation_candidates_keep_the_grammar_of_their_answer(self) -> None:
        self.assertEqual(
            self.editorial._relation_grammatical_category("sintiera", "action"),
            "verb",
        )

    def test_no_gold_question_asks_for_or_answers_with_source_location(self) -> None:
        location = re.compile(
            r"^(?:Daniel \d+:\d+|PR\d+, p\. \d+(?:, párrafo \d+)?)$"
        )
        location_prompt = re.compile(
            r"\ben (?:qué|cuál) (?:referencia|versículo|página|párrafo)\b",
            re.IGNORECASE,
        )
        for question in self.questions:
            self.assertFalse(location.fullmatch(question["correct_answer"]), question["id"])
            self.assertFalse(
                any(location.fullmatch(option) for option in question["options"]),
                question["id"],
            )
            self.assertNotRegex(question["question"], location_prompt, question["id"])

    def test_formulations_do_not_repeat_or_add_the_answer_inside_one_prompt(self) -> None:
        facts_by_id = {fact["fact_id"]: fact for fact in self.facts}
        for question in self.questions:
            if question["family"] == "true_false":
                self.assertNotIn("reproduce correctamente el detalle", question["question"], question["id"])
                self.assertEqual(
                    question["question"],
                    f"Verdadero o falso: {question['statement']}",
                    question["id"],
                )
                self.assertTrue(
                    question["statement"].startswith(
                        f"Según {question['reference']}, "
                    ),
                    question["id"],
                )
                self.assertNotIn("[…]", question["statement"], question["id"])
                self.assertNotRegex(
                    question["statement"],
                    r"[,;:]\s*$",
                    question["id"],
                )
            if question["family"] == "single_choice_contextual":
                fact_answer = facts_by_id[question["fact_id"]]["answer"]
                self.assertNotIn(f"«{fact_answer}»", question["question"], question["id"])
                self.assertNotIn("________", question["question"], question["id"])

    def test_gold_language_is_natural_and_schema_is_complete(self) -> None:
        editorial = self.require_editorial()
        if editorial is None:
            return
        required = {
            "source_ref",
            "source_span",
            "accepted_answers",
            "answer_mode",
            "why_distractors_fail",
        }
        for question in self.questions:
            self.assertTrue(required.issubset(question), question["id"])
            self.assertNotIn("[DETALLE]", question["question"], question["id"])
            self.assertNotIn("identifica correctamente el detalle descrito", question["question"], question["id"])
            self.assertNotIn("qué número o período", question["question"], question["id"])
            if question["family"] == "true_false":
                self.assertTrue(question["question"].startswith("Verdadero o falso: Según "), question["id"])
                continue
            signatures = [
                editorial.option_signature(option, question["option_category"])
                for option in question["options"]
            ]
            self.assertEqual(len(set(signatures)), 1, (question["id"], signatures, question["options"]))

        forbidden_fragments = {
            "poder se",
            "cuernos que yo",
            "favores y gran",
            "ejército y muchas",
            "rey confirmare pueda mudarse",
            "rey demanda es difícil",
            "cosa semejante a ningún",
            "tiempo algunos hombres caldeos",
            "dioses ni tampoco adoraremos",
            "dijo el rey a entendimiento",
            "de buen aspenaz",
        }
        used_options = {
            option.casefold()
            for question in self.questions
            for option in question["options"]
        }
        self.assertTrue(forbidden_fragments.isdisjoint(used_options))
        self.assertFalse(
            any(
                "puesto de mucha" in question["question"].casefold()
                and "puestas del sol" in {option.casefold() for option in question["options"]}
                for question in self.questions
            )
        )

    def test_distractor_signatures_do_not_mix_verbs_names_and_connectors(self) -> None:
        editorial = self.require_editorial()
        if editorial is None:
            return
        self.assertNotEqual(
            editorial.option_signature("leyeran", "action"),
            editorial.option_signature("oído", "action"),
        )
        self.assertNotEqual(
            editorial.option_signature("eres", "action"),
            editorial.option_signature("habló", "action"),
        )
        self.assertNotEqual(
            editorial.option_signature("eres", "action"),
            editorial.option_signature("tuvo", "action"),
        )
        self.assertNotEqual(
            editorial.option_signature("una proclamación para exaltar", "phrase"),
            editorial.option_signature("tiene derecho a interponerse", "phrase"),
        )

        false_questions = [
            question
            for question in self.questions
            if question["family"] == "true_false"
            and question["correct_answer"] == "Falso"
        ]
        self.assertTrue(
            all(
                editorial.option_signature(
                    question["incorrect_detail"], question["option_category"]
                )
                == editorial.option_signature(
                    question["correction"], question["option_category"]
                )
                for question in false_questions
                if question.get("false_mutation_kind") != "negation"
            ),
            "cada alteración falsa debe conservar la clase gramatical del detalle correcto",
        )
        self.assertNotEqual(
            editorial.option_signature("establecía", "action"),
            editorial.option_signature("permitiría", "action"),
        )
        self.assertNotEqual(
            editorial.option_signature("certificados", "term"),
            editorial.option_signature("provenientes", "term"),
        )
        self.assertNotEqual(
            editorial.option_signature("certificados", "term"),
            editorial.option_signature("controladas", "term"),
        )
        self.assertNotEqual(
            editorial.option_signature("certificados", "term"),
            editorial.option_signature("manifestarles", "term"),
        )
        self.assertNotEqual(
            editorial.option_signature("rápidamente", "term"),
            editorial.option_signature("valiente", "term"),
        )
        self.assertNotEqual(
            editorial.option_signature("valiente", "term"),
            editorial.option_signature("adelante", "term"),
        )
        self.assertNotEqual(
            editorial.option_signature("estatua", "term"),
            editorial.option_signature("negativa", "term"),
        )
        self.assertNotEqual(
            editorial.option_signature("hebreos", "term"),
            editorial.option_signature("podemos", "term"),
        )
        self.assertTrue(
            any(
                fact["answer"] == "creciste" and fact["category"] == "action"
                for fact in self.facts
            )
        )
        forbidden_answers = {
            "así", "ahora", "luego", "después", "también", "sólo", "aquí",
            "debajo", "ciertamente", "dondequiera",
            "eres", "es", "era", "eran", "estaba", "estaban", "estuve", "estuvo",
            "ser", "sido", "sea", "sean", "será", "serán", "fue", "fueron", "había",
            "hay", "hoy", "ayer", "mañana", "cuán", "cuánto", "cómo",
        }
        self.assertFalse(
            any(
                question["correct_answer"].casefold() in forbidden_answers
                for question in self.questions
                if question["family"] != "true_false"
            )
        )
        duplicated_connector = re.compile(
            r"\b(que|de|la|el|a|en|y|por|para|con|los|las)\s+\1\b",
            re.IGNORECASE,
        )
        self.assertFalse(
            any(
                duplicated_connector.search(question.get("statement", ""))
                for question in self.questions
                if question["family"] == "true_false"
            )
        )
        false_phrase_questions = [
            question
            for question in self.questions
            if question["family"] == "true_false"
            and question["correct_answer"] == "Falso"
            and question["option_category"] == "phrase"
        ]
        self.assertTrue(
            all(
                len(question["correction"].split())
                == len(question["incorrect_detail"].split())
                and sum(
                    original.casefold() != altered.casefold()
                    for original, altered in zip(
                        question["correction"].split(),
                        question["incorrect_detail"].split(),
                    )
                )
                == 1
                for question in false_phrase_questions
            )
        )
        self.assertTrue(
            all(
                editorial.option_signature(
                    question["incorrect_detail"], question["option_category"]
                )
                == editorial.option_signature(
                    question["correction"], question["option_category"]
                )
                for question in self.questions
                if question["family"] == "true_false"
                and question["correct_answer"] == "Falso"
                and question.get("false_mutation_kind") != "negation"
            )
        )

    def test_audit_and_coverage_gates_finish_at_zero(self) -> None:
        editorial = self.require_editorial()
        if editorial is None:
            return
        facts, questions = self.facts, self.questions
        coverage = editorial.build_coverage_manifest(
            self.inventory["units"], facts, questions
        )
        audit = editorial.audit_final_bank(facts, questions, coverage)
        self.assertEqual(coverage["uncovered_source_units"], 0)
        self.assertEqual(coverage["fact_without_gold_question"], 0)
        self.assertEqual(coverage["unmapped_source_units"], 0)
        for key in (
            "ambiguous_gold_questions",
            "unsupported_gold_answers",
            "duplicate_gold_questions",
            "lexical_sequence_questions",
            "broken_true_false",
            "invalid_references",
            "external_knowledge_questions",
            "answer_length_leaks",
            "source_location_questions",
            "orphan_numeric_source_fragments",
            "family_contract_violations",
            "unsafe_true_false_templates",
        ):
            self.assertEqual(audit[key], 0, key)

    def test_build_cli_writes_canonical_manifest_and_chapter_shards(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/build-final-bank.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest_path = ROOT / "public/banks/final-2026/manifest.json"
        self.assertTrue(manifest_path.exists(), "falta manifest.json")
        if not manifest_path.exists():
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["bank_id"], "BANCO_UNICO_CONEXION_BIBLICA_2026")
        self.assertEqual(manifest["gold_questions"], 12000)
        self.assertEqual(manifest["unique_facts"], 3000)
        self.assertEqual(
            manifest["blind_fact_pools"],
            {"A": 150, "B": 150, "emergency": 150},
        )
        self.assertEqual(len(manifest["shards"]), 18)
        self.assertTrue(
            all((ROOT / "public" / shard["questions_file"]).exists() for shard in manifest["shards"])
        )


if __name__ == "__main__":
    unittest.main()
