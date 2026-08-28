from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.final_editorial import (
    DIVINE_NAMES,
    EDITORIALLY_EXCLUDED_SOURCE_UNITS,
    MAX_CHAPTER_FACTS_PER_ANSWER,
    MAX_GLOBAL_FACTS_PER_ANSWER,
    _norm,
    _complete_statement_text,
    _contextual_word_role,
    _is_bible_reference_number,
    _negate_exact_action_statement,
    _word_role,
    option_signature,
)
from scripts.lib.contextual_roles import (
    GENERIC_CONTEXTUAL_FRAGMENT,
    contains_normalized_phrase,
    render_contextual_identity,
    render_contextual_question,
)


BANK = ROOT / "public" / "banks" / "final-2026"
PDF = ROOT / "MaterialConexionBiblica (1).pdf"
BLANK = re.compile(r"_{4,}")
BROKEN_TEXT = re.compile(r"\ufffd|\(cid:\d+\)|\x00")
DUPLICATED_WORD = re.compile(r"\b([\wáéíóúüñ]+)\s+\1\b", re.IGNORECASE)
DANGLING_CONNECTOR = re.compile(
    r"\b(?:y|o|de|del|en|con|por|para|que|como|a|al)$", re.IGNORECASE
)
LOCATION_ANSWER = re.compile(
    r"^(?:Daniel \d+:\d+|PR\d+, p\. \d+(?:, párrafo \d+)?)$"
)
LOCATION_PROMPT = re.compile(
    r"\ben (?:qué|cuál) (?:referencia|versículo|página|párrafo)\b",
    re.IGNORECASE,
)
REQUIRED_FIELDS = {
    "id", "fact_id", "variant_id", "template_id", "bank_id", "chapter",
    "reference", "source_unit_id", "source_quote", "family", "difficulty",
    "question", "options", "correct_option", "correct_answer", "explanation",
    "why_distractors_fail", "final_editorial_status",
}
FAMILIES = {
    "single_choice_direct",
    "fill_choice",
    "true_false",
    "single_choice_contextual",
}


def fail(errors: list[str], question_id: str, code: str) -> None:
    errors.append(f"{question_id}:{code}")


def main() -> int:
    manifest = json.loads((BANK / "manifest.json").read_text(encoding="utf-8"))
    inventory = json.loads((BANK / "source_inventory.json").read_text(encoding="utf-8"))
    facts = json.loads((BANK / "fact_inventory.json").read_text(encoding="utf-8"))
    questions = []
    for shard in manifest["shards"]:
        questions.extend(
            json.loads((ROOT / "public" / shard["questions_file"]).read_text(encoding="utf-8"))
        )

    units_by_id = {unit["source_unit_id"]: unit for unit in inventory["units"]}
    facts_by_id = {fact["fact_id"]: fact for fact in facts}
    exact_statements_by_reference: dict[str, set[str]] = defaultdict(set)
    for inventory_fact in facts:
        for source_text in (
            inventory_fact["context"],
            inventory_fact["source_quote"],
        ):
            if source_text.count(inventory_fact["answer"]) == 1:
                exact_statements_by_reference[inventory_fact["reference"]].add(
                    _complete_statement_text(source_text)
                )
    errors: list[str] = []
    ids: set[str] = set()
    variants: set[str] = set()
    normalized_questions: set[str] = set()
    families_by_fact: dict[str, set[str]] = defaultdict(set)

    pdf_hash = hashlib.sha256(PDF.read_bytes()).hexdigest()
    if pdf_hash != manifest["source_sha256"]:
        errors.append("manifest:pdf_hash_mismatch")

    pr_texts = [
        unit["exact_text"]
        for unit in inventory["units"]
        if unit["work"] == "Profetas y Reyes"
    ]
    if not any("Entre los hijos de Israel" in text for text in pr_texts):
        errors.append("inventory:missing_top_of_page_content")
    if not any(
        "y con las bestias del campo será tu morada" in text for text in pr_texts
    ):
        errors.append("inventory:cross_page_paragraph_not_joined")
    for unit in inventory["units"]:
        source_text = (unit.get("full_text") or unit.get("exact_text", "")).strip()
        if DANGLING_CONNECTOR.search(source_text.strip(" ”’\"»")):
            errors.append(f"{unit['source_unit_id']}:dangling_source_fragment")
        if unit["work"] == "Profetas y Reyes" and re.search(
            rf"(?:^|\s){unit['page'] + 76}(?:\s|$)", source_text
        ):
            errors.append(f"{unit['source_unit_id']}:printed_page_number_in_source")

    for question in questions:
        qid = question.get("id", "<missing-id>")
        missing = REQUIRED_FIELDS.difference(question)
        if missing:
            fail(errors, qid, "missing_fields=" + ",".join(sorted(missing)))
            continue
        if qid in ids:
            fail(errors, qid, "duplicate_id")
        ids.add(qid)
        variant_id = question["variant_id"]
        if variant_id in variants:
            fail(errors, qid, "duplicate_variant_id")
        variants.add(variant_id)

        family = question["family"]
        fact_id = question["fact_id"]
        source_unit_id = question["source_unit_id"]
        families_by_fact[fact_id].add(family)
        if family not in FAMILIES:
            fail(errors, qid, "invalid_family")
        if question["final_editorial_status"] != "GOLD":
            fail(errors, qid, "not_gold")
        if source_unit_id not in units_by_id:
            fail(errors, qid, "missing_source_unit")
            continue
        if fact_id not in facts_by_id:
            fail(errors, qid, "missing_fact")
            continue

        unit = units_by_id[source_unit_id]
        fact = facts_by_id[fact_id]
        unit_text = unit.get("full_text") or unit.get("exact_text", "")
        if fact["source_unit_id"] != source_unit_id:
            fail(errors, qid, "fact_source_unit_mismatch")
        if question["source_quote"] != fact["source_quote"]:
            fail(errors, qid, "question_fact_quote_mismatch")
        if fact["source_quote"] not in unit_text:
            fail(errors, qid, "quote_not_in_source_unit")
        if fact["source_quote"].count(fact["answer"]) != 1:
            fail(errors, qid, "answer_not_unique_in_source_quote")
        if question["reference"] != fact["reference"]:
            fail(errors, qid, "reference_mismatch")
        if len(fact["context"]) > 420:
            fail(errors, qid, "context_text_wall")
        if len(question["question"]) > 580:
            fail(errors, qid, "question_text_wall")
        if any(
            weak in question["question"]
            for weak in (
                "el texto emplea la forma verbal",
                "entre los números o períodos expresados",
                "entre los lugares o direcciones mencionados",
                "entre los personajes o seres nombrados",
            )
        ):
            fail(errors, qid, "weak_metalinguistic_prompt")
        if "««" in question["question"] or "«»" in question["question"]:
            fail(errors, qid, "duplicated_or_empty_quote")

        options = question["options"]
        expected_options = 2 if family == "true_false" else 4
        if len(options) != expected_options or len(set(options)) != expected_options:
            fail(errors, qid, "invalid_options")
        correct_option = question["correct_option"]
        if not isinstance(correct_option, int) or not 0 <= correct_option < len(options):
            fail(errors, qid, "invalid_correct_option")
        elif options[correct_option] != question["correct_answer"]:
            fail(errors, qid, "answer_index_mismatch")

        blank_count = len(BLANK.findall(question["question"]))
        if family == "true_false":
            if blank_count or options != ["Verdadero", "Falso"]:
                fail(errors, qid, "broken_true_false_contract")
            if question.get("focused_true_statement") or (
                "al evaluar específicamente" in question.get("statement", "").casefold()
            ):
                fail(errors, qid, "unsafe_true_false_template")
            if question["correct_answer"] == "Falso" and fact["category"] not in {
                "person", "place", "number", "action"
            }:
                fail(errors, qid, "unsafe_false_category")
            if question.get("statement", "") not in question["question"]:
                fail(errors, qid, "statement_not_visible")
            if question["question"] != f"Verdadero o falso: {question.get('statement', '')}":
                fail(errors, qid, "true_false_added_template_text")
            if (
                question["statement"].count("«") != question["statement"].count("»")
                or question["statement"].count("“") != question["statement"].count("”")
            ):
                fail(errors, qid, "unbalanced_true_false_quotes")
            exact_source_texts = {
                _complete_statement_text(fact["context"]),
                _complete_statement_text(fact["source_quote"]),
            }
            statement_mode = question.get("statement_mode")
            truth_source_statement = question.get("truth_source_statement")
            if statement_mode == "exact_source":
                if truth_source_statement not in exact_source_texts:
                    fail(errors, qid, "invalid_exact_true_false_source")
            elif statement_mode == "contextual_identity":
                expected_identity, expected_role, expected_evidence = (
                    render_contextual_identity(fact)
                )
                if question["correct_answer"] != "Verdadero":
                    fail(errors, qid, "contextual_identity_not_true")
                if truth_source_statement != expected_identity:
                    fail(errors, qid, "invalid_contextual_identity_statement")
                if question.get("contextual_role") != expected_role:
                    fail(errors, qid, "contextual_identity_role_mismatch")
                if question.get("context_evidence") != expected_evidence:
                    fail(errors, qid, "contextual_identity_evidence_mismatch")
                if contains_normalized_phrase(
                    str(question.get("context_evidence") or ""),
                    str(question.get("asserted_detail") or ""),
                ):
                    fail(errors, qid, "context_evidence_leak")
            else:
                fail(errors, qid, "missing_true_false_statement_mode")
            expected_true_statement = (
                f"Según {question['reference']}, {truth_source_statement}"
            )
            if question["correct_answer"] == "Verdadero":
                if question.get("statement") != expected_true_statement:
                    fail(errors, qid, "true_statement_not_exact_source")
            else:
                if question.get("corrected_statement") != expected_true_statement:
                    fail(errors, qid, "false_correction_not_exact_source")
                if not question.get("incorrect_detail") or not question.get("correction"):
                    fail(errors, qid, "false_missing_precise_correction")
                elif question["correction"] != fact["answer"]:
                    fail(errors, qid, "false_correction_answer_mismatch")
                mutation_kind = question.get("false_mutation_kind")
                if mutation_kind == "negation":
                    expected_negated = _negate_exact_action_statement(
                        truth_source_statement, fact["answer"]
                    )
                    if fact["category"] != "action" or statement_mode != "exact_source":
                        fail(errors, qid, "invalid_negation_category_or_mode")
                    if question["incorrect_detail"].casefold() != f"no {fact['answer'].lower()}":
                        fail(errors, qid, "invalid_negation_detail")
                    if expected_negated is None or question.get("statement") != (
                        f"Según {question['reference']}, {expected_negated}"
                    ):
                        fail(errors, qid, "invalid_controlled_negation")
                elif mutation_kind == "cross_reference_statement":
                    replacement_ref = question.get("replacement_source_ref")
                    if not replacement_ref or replacement_ref == question["reference"]:
                        fail(errors, qid, "invalid_cross_reference_source")
                    if question.get("statement") == expected_true_statement:
                        fail(errors, qid, "cross_reference_repeats_target_source")
                    expected_foreign_statements = {
                        f"Según {question['reference']}, {statement}"
                        for statement in exact_statements_by_reference.get(
                            replacement_ref, set()
                        )
                    }
                    if question.get("statement") not in expected_foreign_statements:
                        fail(errors, qid, "cross_reference_statement_not_source_exact")
                    if question.get("trap_type") != "true_in_other_context":
                        fail(errors, qid, "missing_cross_reference_trap")
                    if _norm(question["incorrect_detail"]) not in _norm(
                        question.get("statement", "")
                    ):
                        fail(errors, qid, "cross_reference_detail_missing_from_statement")
                    if option_signature(
                        question["incorrect_detail"], fact["category"]
                    ) != option_signature(question["correction"], fact["category"]):
                        fail(errors, qid, "false_grammatical_signature_mismatch")
                else:
                    if mutation_kind != "closed_category_substitution":
                        fail(errors, qid, "missing_false_mutation_kind")
                    if option_signature(
                        question["incorrect_detail"], fact["category"]
                    ) != option_signature(question["correction"], fact["category"]):
                        fail(errors, qid, "false_grammatical_signature_mismatch")
                if fact["category"] == "person" and statement_mode == "exact_source" and (
                    (_norm(question["incorrect_detail"]) in DIVINE_NAMES)
                    != (_norm(question["correction"]) in DIVINE_NAMES)
                ):
                    fail(errors, qid, "false_divine_human_swap")
                incorrect_norm = _norm(question["incorrect_detail"])
                source_norm = _norm(question["source_quote"])
                if f" {incorrect_norm} " in f" {source_norm} ":
                    fail(errors, qid, "false_detail_also_in_source")
                if question["option_category"] == "term" and (
                    question.get("replacement_slot_signature")
                    != question.get("correct_slot_signature")
                ):
                    fail(errors, qid, "false_term_slot_signature_mismatch")
                if not question.get("replacement_source_ref"):
                    fail(errors, qid, "false_replacement_missing_source_reference")
        elif family == "single_choice_contextual":
            if blank_count:
                fail(errors, qid, "contextual_question_contains_blank")
            if question["correct_answer"] != fact["answer"]:
                fail(errors, qid, "contextual_answer_fact_mismatch")
            if question["correct_answer"] not in question["source_quote"]:
                fail(errors, qid, "contextual_answer_not_in_source")
            if f"«{fact['answer']}»" in question["question"]:
                fail(errors, qid, "contextual_prompt_reveals_answer")
            if question.get("trap_type") != "true_in_other_context":
                fail(errors, qid, "missing_contextual_trap")
            expected_question, expected_role, expected_evidence = (
                render_contextual_question(fact)
            )
            if GENERIC_CONTEXTUAL_FRAGMENT in _norm(question["question"]):
                fail(errors, qid, "generic_contextual_prompt")
            if question["question"] != expected_question:
                fail(errors, qid, "contextual_question_mismatch")
            if question.get("contextual_role") != expected_role:
                fail(errors, qid, "contextual_role_mismatch")
            if question.get("context_evidence") != expected_evidence:
                fail(errors, qid, "context_evidence_mismatch")
            if contains_normalized_phrase(
                str(question.get("context_evidence") or ""),
                str(question["correct_answer"]),
            ):
                fail(errors, qid, "context_evidence_leak")
            if set(question["why_distractors_fail"]) != (
                set(options) - {question["correct_answer"]}
            ):
                fail(errors, qid, "incomplete_distractor_explanations")
        else:
            if blank_count != 1:
                fail(errors, qid, "invalid_blank_count")
            if question["correct_answer"] != fact["answer"]:
                fail(errors, qid, "answer_fact_mismatch")
            if question["correct_answer"] not in question["source_quote"]:
                fail(errors, qid, "answer_not_in_source")
            if question["option_category"] == "term":
                slot_signatures = question.get("option_slot_signatures", [])
                if len(slot_signatures) != 4 or len(set(slot_signatures)) != 1:
                    fail(errors, qid, "distractor_slot_signature_mismatch")
                signatures = [option_signature(option, "term") for option in options]
                if len(set(signatures)) != 1:
                    fail(errors, qid, "distractor_term_morphology_mismatch")
            else:
                signatures = [
                    option_signature(option, question["option_category"])
                    for option in options
                ]
                if len(set(signatures)) != 1:
                    fail(errors, qid, "distractor_grammatical_signature_mismatch")
            if question["option_category"] != "place" and any(
                option[:1].isupper() != question["correct_answer"][:1].isupper()
                for option in options
                if option and question["correct_answer"]
            ):
                fail(errors, qid, "distractor_initial_case_mismatch")

        normalized = re.sub(r"\W+", " ", question["question"].casefold()).strip()
        if LOCATION_ANSWER.fullmatch(str(question["correct_answer"]).strip()) or any(
            LOCATION_ANSWER.fullmatch(str(option).strip()) for option in options
        ):
            fail(errors, qid, "source_location_used_as_answer")
        if LOCATION_PROMPT.search(question["question"]):
            fail(errors, qid, "source_location_requested")
        if normalized in normalized_questions:
            fail(errors, qid, "duplicate_visible_question")
        normalized_questions.add(normalized)
        if BROKEN_TEXT.search(question["question"] + question["explanation"]):
            fail(errors, qid, "broken_text_marker")
        if any(
            prefix in question["question"]
            for prefix in (
                "Atendiendo al contexto exacto",
                "Sin trasladar datos de otra escena",
                "Para distinguir este detalle de otros cercanos",
                "reproduce correctamente el detalle",
            )
        ):
            fail(errors, qid, "synthetic_prompt_prefix")
        if DUPLICATED_WORD.search(question["question"]):
            fail(errors, qid, "duplicated_adjacent_word")
        for status_field in (
            "validation_generator", "validation_schema", "validation_source",
            "validation_language", "validation_adversarial",
        ):
            if question.get(status_field, {}).get("status") != "passed":
                fail(errors, qid, f"{status_field}_not_passed")

    universal_families = {
        "single_choice_direct", "fill_choice", "single_choice_contextual"
    }
    true_false_by_fact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for question in questions:
        if question["family"] == "true_false":
            true_false_by_fact[question["fact_id"]].append(question)
    for fact_id in facts_by_id:
        fact_families = families_by_fact.get(fact_id, set())
        if not universal_families.issubset(fact_families):
            errors.append(f"{fact_id}:missing_universal_family_variant")
        tf_rows = true_false_by_fact.get(fact_id, [])
        if tf_rows and (
            len(tf_rows) != 2
            or {row["correct_answer"] for row in tf_rows} != {"Verdadero", "Falso"}
        ):
            errors.append(f"{fact_id}:invalid_true_false_pair")
    if len(true_false_by_fact) != 1500:
        errors.append("facts:invalid_true_false_fact_count")

    global_answer_counts = Counter(_norm(fact["answer"]) for fact in facts)
    if global_answer_counts and max(global_answer_counts.values()) > MAX_GLOBAL_FACTS_PER_ANSWER:
        errors.append("facts:global_answer_repetition_cap_exceeded")
    for chapter in {fact["chapter"] for fact in facts}:
        chapter_counts = Counter(
            _norm(fact["answer"])
            for fact in facts
            if fact["chapter"] == chapter
        )
        if chapter_counts and max(chapter_counts.values()) > MAX_CHAPTER_FACTS_PER_ANSWER:
            errors.append(f"{chapter}:answer_repetition_cap_exceeded")

    category_counts = Counter(fact["category"] for fact in facts)
    dangling_answer_words = {
        "a", "al", "con", "contra", "de", "del", "en", "entre", "hacia",
        "hasta", "para", "por", "que", "sin", "sobre", "y", "o",
    }
    for fact in facts:
        if fact["answer"].casefold().split()[-1] in dangling_answer_words:
            errors.append(f"{fact['fact_id']}:dangling_answer_connector")
        if (
            fact["category"] == "action"
            and _contextual_word_role(
                fact["source_quote"],
                fact["source_quote"].index(fact["answer"]),
                fact["source_quote"].index(fact["answer"]) + len(fact["answer"]),
            ) != "verb"
        ):
            errors.append(f"{fact['fact_id']}:nonverb_labeled_as_action")
        if fact["answer"].isdigit():
            start = fact["source_quote"].index(fact["answer"])
            if _is_bible_reference_number(
                fact["source_quote"], start, start + len(fact["answer"])
            ):
                errors.append(f"{fact['fact_id']}:isolated_bible_reference_number")
    for category, minimum in {
        "person": 150,
        "place": 60,
        "number": 80,
        "action": 350,
        "term": 350,
    }.items():
        if category_counts[category] < minimum:
            errors.append(f"facts:insufficient_{category}_coverage")

    easy_questions = [question for question in questions if question["difficulty"] == "easy"]
    if any(question["family"] == "single_choice_contextual" for question in easy_questions):
        errors.append("difficulty:contextual_marked_easy")
    if any(
        question["family"] == "true_false" and question["correct_answer"] == "Falso"
        for question in easy_questions
    ):
        errors.append("difficulty:false_statement_marked_easy")
    expert_contextual = sum(
        question["difficulty"] == "expert"
        and question["family"] == "single_choice_contextual"
        for question in questions
    )
    if expert_contextual < 1800:
        errors.append("difficulty:insufficient_expert_contextual_questions")
    for family, minimum in {"single_choice_direct": 270, "true_false": 210}.items():
        if sum(
            question["difficulty"] == "expert" and question["family"] == family
            for question in questions
        ) < minimum:
            errors.append(f"difficulty:insufficient_expert_{family}")
    if sum(
        question["difficulty"] == "expert"
        and question["family"] == "single_choice_direct"
        and question["blind_pool"] is None
        for question in questions
    ) < 100:
        errors.append("difficulty:insufficient_visible_expert_single_choice_direct")

    coverage = json.loads((BANK / "coverage_manifest.json").read_text(encoding="utf-8"))
    excluded_ids = {
        unit["source_unit_id"]
        for unit in coverage["units"]
        if unit["coverage_status"] == "excluded_low_value"
    }
    if excluded_ids != set(EDITORIALLY_EXCLUDED_SOURCE_UNITS):
        errors.append("coverage:excluded_source_units_mismatch")

    declared = sum(shard["question_count"] for shard in manifest["shards"])
    if len(questions) != manifest["gold_questions"] or len(questions) != declared:
        errors.append("manifest:question_total_mismatch")
    if len(facts) != manifest["unique_facts"]:
        errors.append("manifest:fact_total_mismatch")
    if len(units_by_id) != manifest["source_units"]:
        errors.append("manifest:source_unit_total_mismatch")

    summary = {
        "pdf_sha256_matches": pdf_hash == manifest["source_sha256"],
        "source_units": len(units_by_id),
        "facts": len(facts),
        "questions": len(questions),
        "families": Counter(q["family"] for q in questions),
        "difficulty": Counter(q["difficulty"] for q in questions),
        "fact_categories": category_counts,
        "max_global_fact_answer_repetition": max(global_answer_counts.values()),
        "excluded_low_value_source_units": len(excluded_ids),
        "true_false_answers": Counter(
            q["correct_answer"] for q in questions if q["family"] == "true_false"
        ),
        "chapters": Counter(q["chapter"] for q in questions),
        "errors": len(errors),
        "error_examples": errors[:50],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=dict))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
