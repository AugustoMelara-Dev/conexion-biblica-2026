from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "public" / "banks" / "final-2026"
PDF = ROOT / "MaterialConexionBiblica (1).pdf"
BLANK = re.compile(r"_{4,}")
BROKEN_TEXT = re.compile(r"\ufffd|\(cid:\d+\)|\x00")
DUPLICATED_WORD = re.compile(r"\b([\wáéíóúüñ]+)\s+\1\b", re.IGNORECASE)
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
    errors: list[str] = []
    ids: set[str] = set()
    variants: set[str] = set()
    normalized_questions: set[str] = set()
    families_by_fact: dict[str, set[str]] = defaultdict(set)

    pdf_hash = hashlib.sha256(PDF.read_bytes()).hexdigest()
    if pdf_hash != manifest["source_sha256"]:
        errors.append("manifest:pdf_hash_mismatch")

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
        if question["reference"] != fact["reference"]:
            fail(errors, qid, "reference_mismatch")

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
            if question.get("statement", "") not in question["question"]:
                fail(errors, qid, "statement_not_visible")
            if question["correct_answer"] == "Verdadero":
                if question.get("statement") != fact["context"]:
                    fail(errors, qid, "true_statement_not_exact_source")
            else:
                if question.get("corrected_statement") != fact["context"]:
                    fail(errors, qid, "false_correction_not_exact_source")
                if not question.get("incorrect_detail") or not question.get("correction"):
                    fail(errors, qid, "false_missing_precise_correction")
                elif question["correction"] != fact["answer"]:
                    fail(errors, qid, "false_correction_answer_mismatch")
        else:
            if blank_count != 1:
                fail(errors, qid, "invalid_blank_count")
            if question["correct_answer"] != fact["answer"]:
                fail(errors, qid, "answer_fact_mismatch")
            if question["correct_answer"] not in question["source_quote"]:
                fail(errors, qid, "answer_not_in_source")
            if family == "single_choice_contextual":
                if question.get("trap_type") != "true_in_other_context":
                    fail(errors, qid, "missing_contextual_trap")
                if set(question["why_distractors_fail"]) != (
                    set(options) - {question["correct_answer"]}
                ):
                    fail(errors, qid, "incomplete_distractor_explanations")

        normalized = re.sub(r"\W+", " ", question["question"].casefold()).strip()
        if normalized in normalized_questions:
            fail(errors, qid, "duplicate_visible_question")
        normalized_questions.add(normalized)
        if BROKEN_TEXT.search(question["question"] + question["explanation"]):
            fail(errors, qid, "broken_text_marker")
        if DUPLICATED_WORD.search(question["question"]):
            fail(errors, qid, "duplicated_adjacent_word")
        for status_field in (
            "validation_generator", "validation_schema", "validation_source",
            "validation_language", "validation_adversarial",
        ):
            if question.get(status_field, {}).get("status") != "passed":
                fail(errors, qid, f"{status_field}_not_passed")

    for fact_id in facts_by_id:
        if families_by_fact.get(fact_id) != FAMILIES:
            errors.append(f"{fact_id}:missing_family_variant")

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
