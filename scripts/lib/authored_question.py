"""Contrato y validador de preguntas autorizadas por IA."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REQUIRED_KEYS = {
    "id",
    "source_unit_id",
    "fact_id",
    "family",
    "subtype",
    "question",
    "options",
    "correct_option",
    "correct_answer",
    "accepted_answers",
    "explanation",
    "why_distractors_fail",
    "source_ref",
    "source_quote",
    "evidence_excerpt",
    "difficulty",
    "importance",
    "relation_type",
    "option_category",
    "blind_pool",
    "ai_review",
}

ALLOWED_SUBTYPES = {
    "factual_recall",
    "speaker_addressee",
    "cause_consequence",
    "narrative_order",
    "identification",
    "relationship",
    "text_recall",
    "comparison",
    "symbol_interpretation",
    "prophetic_detail",
    "principle",
    "cross_source_integration",
}

PROHIBITED_PROMPT_PATTERNS = (
    re.compile(r"^\s*según\s+(?:daniel|pr|profetas\s+y\s+reyes)", re.IGNORECASE),
    re.compile(r"según\s+(?:el\s+)?(?:párrafo|capítulo|versículo|página)", re.IGNORECASE),
    re.compile(r"de\s+acuerdo\s+con\s+el\s+(?:versículo|capítulo|párrafo|página)", re.IGNORECASE),
    re.compile(r"\ben\s+(?:qué|cuál)\s+(?:versículo|capítulo|página|párrafo|referencia)\b", re.IGNORECASE),
    re.compile(r"\bsegún\s+la\s+página\b", re.IGNORECASE),
)


def _norm(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text))
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^\w\s]", " ", without_marks.lower())
    return " ".join(cleaned.split())


def validate_authored_question(row: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    question_id = str(row.get("id") or "UNKNOWN_ID").strip()

    missing_keys = REQUIRED_KEYS - set(row.keys())
    if missing_keys:
        for key in sorted(missing_keys):
            errors.append(f"{question_id}:missing_key_{key}")
        return errors

    prompt = str(row.get("question") or "").strip()
    if not prompt:
        errors.append(f"{question_id}:empty_prompt")
    else:
        for pat in PROHIBITED_PROMPT_PATTERNS:
            if pat.search(prompt):
                errors.append(f"{question_id}:source_location_prompt")
                break

    family = str(row.get("family") or "").strip()
    options = row.get("options")
    if not isinstance(options, list):
        errors.append(f"{question_id}:invalid_options_type")
        return errors

    expected_option_count = 2 if family == "true_false" else 4
    if len(options) != expected_option_count:
        errors.append(f"{question_id}:invalid_option_count")

    norm_opts = [_norm(opt) for opt in options]
    if len(set(norm_opts)) != len(options):
        errors.append(f"{question_id}:duplicate_options")

    correct_option = row.get("correct_option")
    if not isinstance(correct_option, int) or correct_option < 0 or correct_option >= len(options):
        errors.append(f"{question_id}:invalid_correct_option_index")
    else:
        correct_answer = row.get("correct_answer")
        if options[correct_option] != correct_answer:
            errors.append(f"{question_id}:answer_index_mismatch")

    subtype = str(row.get("subtype") or "").strip()
    if subtype not in ALLOWED_SUBTYPES:
        errors.append(f"{question_id}:invalid_subtype")

    evidence = str(row.get("evidence_excerpt") or "").strip()
    if not evidence:
        errors.append(f"{question_id}:missing_evidence")

    source_quote = str(row.get("source_quote") or "").strip()
    if not source_quote:
        errors.append(f"{question_id}:missing_source_quote")

    correct_ans_str = str(row.get("correct_answer") or "").strip()
    if family == "true_false":
        if correct_ans_str not in ("Verdadero", "Falso"):
            errors.append(f"{question_id}:invalid_true_false_answer")
        if correct_ans_str == "Falso":
            mutation = row.get("false_mutation")
            if not isinstance(mutation, dict):
                errors.append(f"{question_id}:missing_false_mutation")
            else:
                if not mutation.get("local", False):
                    errors.append(f"{question_id}:cross_passage_false_mutation")
                if not mutation.get("changed_fields"):
                    errors.append(f"{question_id}:empty_changed_fields")
    else:
        norm_ans = _norm(correct_ans_str)
        norm_quote = _norm(source_quote)
        norm_evidence = _norm(evidence)
        # Check support: normalized answer words should overlap or be found in quote or evidence
        ans_tokens = set(norm_ans.split()) - {"de", "la", "el", "los", "las", "en", "un", "una", "y", "a", "del", "al"}
        quote_tokens = set(norm_quote.split()) | set(norm_evidence.split())
        if ans_tokens and not (ans_tokens & quote_tokens) and norm_ans not in norm_quote and norm_ans not in norm_evidence:
            errors.append(f"{question_id}:answer_not_supported")

    ai_review = row.get("ai_review")
    if not isinstance(ai_review, dict):
        errors.append(f"{question_id}:missing_ai_review")
    else:
        if ai_review.get("status") != "passed":
            errors.append(f"{question_id}:ai_review_not_passed")
        reviewer_type = str(ai_review.get("reviewer_type") or "")
        if "human" in reviewer_type.lower():
            errors.append(f"{question_id}:human_signature_claim")
        elif reviewer_type != "ai_semantic_audit":
            errors.append(f"{question_id}:invalid_reviewer_type")
        if not str(ai_review.get("reviewer") or "").strip():
            errors.append(f"{question_id}:missing_reviewer_name")

    return errors


def load_authored_unit(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de unidad autorizada: {path}")
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, list):
        raise ValueError(f"El archivo {path} debe contener un arreglo JSON de preguntas")
    return raw_data
