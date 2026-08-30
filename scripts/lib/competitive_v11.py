"""Contrato editorial estricto del corpus competitivo V11."""

from __future__ import annotations

import re
import unicodedata
import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

SOURCE_LOCATION_PATTERNS = (
    re.compile(
        r"^\s*según\s+(?:daniel\b|pr\s*\d+\b|profetas\s+y\s+reyes\b|(?:el|la)\s+(?:párrafo|capítulo|versículo|página)\b)",
        re.IGNORECASE,
    ),
    re.compile(r"\bsegún\s+(?:el\s+)?(?:párrafo|capítulo|versículo|página)\b", re.IGNORECASE),
    re.compile(r"\bde\s+acuerdo\s+con\s+(?:el\s+)?(?:párrafo|capítulo|versículo|página)\b", re.IGNORECASE),
    re.compile(r"\ben\s+(?:qué|cuál)\s+(?:párrafo|capítulo|versículo|página|referencia)\b", re.IGNORECASE),
)

REQUIRED_KEYS = {
    "id",
    "source_unit_id",
    "fact_id",
    "role",
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
    "false_mutation",
    "blank_span",
    "significance",
    "variant_justification",
    "blind_pool",
    "ai_review",
}
ALLOWED_FAMILIES = {
    "single_choice_direct",
    "single_choice_contextual",
    "fill_choice",
    "true_false",
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
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "expert"}
ALLOWED_ROLES = {"central", "variant"}
ALLOWED_BLIND_POOLS = {None, "A", "B", "emergency"}
RELEASE_BLIND_REQUIREMENTS = {
    "A": {
        "fact_count": 100,
        "families": {"selection": 45, "fill_choice": 30, "true_false": 25},
    },
    "B": {
        "fact_count": 100,
        "families": {"selection": 45, "fill_choice": 30, "true_false": 25},
    },
    "emergency": {
        "fact_count": 50,
        "families": {"selection": 23, "fill_choice": 15, "true_false": 12},
    },
}
TRIVIAL_BLANKS = {
    "a",
    "al",
    "con",
    "de",
    "del",
    "el",
    "en",
    "la",
    "las",
    "lo",
    "los",
    "o",
    "por",
    "que",
    "se",
    "su",
    "sus",
    "un",
    "una",
    "y",
}
SUPPORT_STOPWORDS = TRIVIAL_BLANKS | {"para", "como", "fue", "era"}
MUTATION_FUNCTION_WORDS = SUPPORT_STOPWORDS | {
    "le",
    "les",
    "me",
    "mi",
    "nos",
    "te",
}


def normalize_prompt(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text))
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^\w\s]", " ", without_marks.lower()).split())


def normalize_mutation_token(token: str) -> str:
    for suffix in ("nos", "los", "las", "les", "lo", "la", "le", "se", "me", "te"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def source_supports_answer_form(answer_form: object, normalized_source: str) -> bool:
    """Acepta una forma literal o una derivación española inequívoca y larga."""
    normalized_form = normalize_prompt(str(answer_form or ""))
    if not normalized_form:
        return False
    if normalized_form in normalized_source:
        return True
    answer_tokens = set(normalized_form.split()) - SUPPORT_STOPWORDS
    source_tokens = set(normalized_source.split()) - SUPPORT_STOPWORDS
    if answer_tokens.intersection(source_tokens):
        return True
    return any(
        len(answer_token) >= 8
        and len(source_token) >= 8
        and answer_token[:7] == source_token[:7]
        for answer_token in answer_tokens
        for source_token in source_tokens
    )


def content_hash(row: Mapping[str, Any]) -> str:
    canonical = {
        key: value
        for key, value in row.items()
        if key not in {"ai_review", "content_sha256"}
    }
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_question(
    row: Mapping[str, Any],
    source_units: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    missing_keys = REQUIRED_KEYS - set(row)
    errors.extend(f"missing_key_{key}" for key in sorted(missing_keys))
    if missing_keys:
        return errors

    for key in (
        "id",
        "source_unit_id",
        "fact_id",
        "question",
        "correct_answer",
        "explanation",
        "source_ref",
        "source_quote",
        "evidence_excerpt",
        "importance",
        "relation_type",
        "option_category",
    ):
        if not str(row.get(key) or "").strip():
            errors.append(f"empty_{key}")

    prompt = str(row.get("question") or "")
    if any(pattern.search(prompt) for pattern in SOURCE_LOCATION_PATTERNS):
        errors.append("source_location_prompt")

    source_unit_id = str(row.get("source_unit_id") or "")
    expected_source = source_units.get(source_unit_id)
    if expected_source is None:
        errors.append("unknown_source_unit")
    else:
        if str(row.get("source_ref")) != str(expected_source.get("source_ref")):
            errors.append("source_reference_mismatch")
        if str(row.get("source_quote")) != str(expected_source.get("source_quote")):
            errors.append("source_quote_mismatch")
        support_text = " ".join(
            str(expected_source.get(key) or "")
            for key in ("source_quote", "parent_context")
        )
        normalized_support = normalize_prompt(support_text)
        normalized_evidence = normalize_prompt(str(row.get("evidence_excerpt") or ""))
        if not normalized_evidence or normalized_evidence not in normalized_support:
            errors.append("evidence_not_in_source")

    family = str(row.get("family") or "")
    if family not in ALLOWED_FAMILIES:
        errors.append("invalid_family")
    if row.get("role") not in ALLOWED_ROLES:
        errors.append("invalid_role")
    if row.get("subtype") not in ALLOWED_SUBTYPES:
        errors.append("invalid_subtype")
    if row.get("difficulty") not in ALLOWED_DIFFICULTIES:
        errors.append("invalid_difficulty")
    if row.get("blind_pool") not in ALLOWED_BLIND_POOLS:
        errors.append("invalid_blind_pool")
    if row.get("blind_pool") is not None and row.get("role") != "central":
        errors.append("blind_variant_not_allowed")

    options = row.get("options")
    if not isinstance(options, list) or not all(
        isinstance(option, str) and option.strip() for option in options
    ):
        errors.append("invalid_options")
        options = []
    expected_options = 2 if family == "true_false" else 4
    if len(options) != expected_options:
        errors.append("invalid_option_count")
    normalized_options = [normalize_prompt(option) for option in options]
    if len(set(normalized_options)) != len(normalized_options):
        errors.append("duplicate_options")

    correct_option = row.get("correct_option")
    if (
        isinstance(correct_option, bool)
        or not isinstance(correct_option, int)
        or correct_option < 0
        or correct_option >= len(options)
    ):
        errors.append("invalid_correct_option")
    elif options[correct_option] != row.get("correct_answer"):
        errors.append("answer_index_mismatch")

    accepted_answers = row.get("accepted_answers")
    if not isinstance(accepted_answers, list) or normalize_prompt(
        str(row.get("correct_answer") or "")
    ) not in {normalize_prompt(answer) for answer in accepted_answers}:
        errors.append("correct_answer_not_accepted")

    if family != "true_false":
        normalized_answer = normalize_prompt(str(row.get("correct_answer") or ""))
        normalized_prompt = normalize_prompt(prompt)
        if normalized_answer and f" {normalized_answer} " in f" {normalized_prompt} ":
            errors.append("answer_leaked_in_prompt")
        distractor_ledger = row.get("why_distractors_fail")
        expected_distractors = {
            option for index, option in enumerate(options) if index != correct_option
        }
        if not isinstance(distractor_ledger, Mapping) or set(distractor_ledger) != expected_distractors:
            errors.append("incomplete_distractor_ledger")
        elif not all(str(reason).strip() for reason in distractor_ledger.values()):
            errors.append("empty_distractor_reason")

        normalized_source_quote = normalize_prompt(str(row.get("source_quote")))
        explicit_support = str(row.get("answer_support_term") or "").strip()
        if explicit_support and normalize_prompt(explicit_support) not in normalized_source_quote:
            errors.append("answer_support_term_not_in_source")
        answer_forms = [
            row.get("correct_answer"),
            *(row.get("accepted_answers") or []),
            explicit_support,
        ]
        supported_answer = any(
            source_supports_answer_form(answer_form, normalized_source_quote)
            for answer_form in answer_forms
        )
        if not supported_answer:
            errors.append("answer_not_supported")

    if family == "true_false" and row.get("correct_answer") not in {"Verdadero", "Falso"}:
        errors.append("invalid_true_false_answer")

    if family == "true_false" and row.get("correct_answer") == "Falso":
        mutation = row.get("false_mutation")
        if not isinstance(mutation, Mapping) or not mutation.get("local"):
            errors.append("cross_passage_falsehood")
        if isinstance(mutation, Mapping):
            changed_fields = mutation.get("changed_fields")
            if not isinstance(changed_fields, list) or len(changed_fields) != 1:
                errors.append("false_mutation_must_change_one_field")
            original = str(mutation.get("original") or "").strip()
            replacement = str(mutation.get("replacement") or "").strip()
            original_tokens = {
                normalize_mutation_token(token)
                for token in normalize_prompt(original).split()
                if token not in MUTATION_FUNCTION_WORDS
            }
            source_tokens = {
                normalize_mutation_token(token)
                for token in normalize_prompt(str(row.get("source_quote") or "")).split()
                if token not in MUTATION_FUNCTION_WORDS
            }
            overlap_ratio = (
                len(original_tokens.intersection(source_tokens)) / len(original_tokens)
                if original_tokens
                else 0
            )
            if overlap_ratio < 0.60:
                errors.append("false_mutation_original_not_in_source")
            if not replacement or normalize_prompt(original) == normalize_prompt(replacement):
                errors.append("invalid_false_mutation_replacement")
    elif family == "true_false" and row.get("false_mutation") is not None:
        errors.append("unexpected_false_mutation")

    if family == "fill_choice":
        if len(re.findall(r"_{4,}", prompt)) != 1:
            errors.append("invalid_completion_blank")
        blank_span = str(row.get("blank_span") or "").strip()
        if normalize_prompt(blank_span) != normalize_prompt(str(row.get("correct_answer") or "")):
            errors.append("blank_span_answer_mismatch")
        if (
            not str(row.get("significance") or "").strip()
            or normalize_prompt(blank_span) in TRIVIAL_BLANKS
        ):
            errors.append("trivial_completion_blank")
        normalized_quote = normalize_prompt(str(row.get("source_quote") or ""))
        supported_blank_forms = [
            blank_span,
            *(row.get("accepted_answers") or []),
            row.get("answer_support_term"),
        ]
        if not any(
            source_supports_answer_form(form, normalized_quote)
            for form in supported_blank_forms
        ):
            errors.append("blank_not_in_source")

    ai_review = row.get("ai_review")
    if not isinstance(ai_review, Mapping):
        errors.append("missing_ai_review")
    else:
        if ai_review.get("status") != "passed":
            errors.append("ai_review_not_passed")
        reviewer_type = str(ai_review.get("reviewer_type") or "")
        if "human" in reviewer_type.lower():
            errors.append("human_signature_claim")
        elif reviewer_type != "ai_semantic_audit":
            errors.append("invalid_reviewer_type")
        if not str(ai_review.get("reviewer") or "").strip():
            errors.append("missing_reviewer")
    return errors


def blind_family(family: object) -> str:
    value = str(family or "")
    return "selection" if value.startswith("single_choice") else value


def audit_corpus(
    rows: Sequence[Mapping[str, Any]],
    blind_requirements: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, list[str]]:
    duplicate_ids: list[str] = []
    duplicate_prompts: list[str] = []
    normalized_duplicate_prompts: list[str] = []
    seen_ids: set[str] = set()
    seen_prompts: set[str] = set()
    seen_normalized_prompts: set[str] = set()
    by_fact: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        question_id = str(row.get("id") or "UNKNOWN_ID")
        prompt = str(row.get("question") or "").strip()
        normalized = normalize_prompt(prompt)
        if question_id in seen_ids:
            duplicate_ids.append(question_id)
        if prompt in seen_prompts:
            duplicate_prompts.append(question_id)
        if normalized in seen_normalized_prompts:
            normalized_duplicate_prompts.append(question_id)
        seen_ids.add(question_id)
        seen_prompts.add(prompt)
        seen_normalized_prompts.add(normalized)
        by_fact[str(row.get("fact_id") or "")].append(row)
    unjustified = [
        str(row.get("id") or "UNKNOWN_ID")
        for fact_rows in by_fact.values()
        for row in fact_rows[2:]
        if not str(row.get("variant_justification") or "").strip()
    ]
    ownership_by_fact = {
        fact_id: {
            str(row.get("blind_pool")) if row.get("blind_pool") else "training"
            for row in fact_rows
        }
        for fact_id, fact_rows in by_fact.items()
    }
    mixed_fact_ownership = sorted(
        fact_id for fact_id, domains in ownership_by_fact.items() if len(domains) > 1
    )
    blind_pool_fact_collisions = sorted(
        fact_id
        for fact_id, domains in ownership_by_fact.items()
        if len(domains - {"training"}) > 1
    )
    blind_facts_with_multiple_presentations = sorted(
        fact_id
        for fact_id, fact_rows in by_fact.items()
        if any(row.get("blind_pool") for row in fact_rows) and len(fact_rows) != 1
    )
    requirement_violations: list[str] = []
    for pool, requirement in (blind_requirements or {}).items():
        pool_rows = [row for row in rows if row.get("blind_pool") == pool]
        actual_fact_count = len({str(row.get("fact_id") or "") for row in pool_rows})
        expected_fact_count = int(requirement.get("fact_count", 0))
        if actual_fact_count != expected_fact_count:
            requirement_violations.append(
                f"{pool}:fact_count:expected={expected_fact_count}:actual={actual_fact_count}"
            )
        actual_families = Counter(blind_family(row.get("family")) for row in pool_rows)
        for family, expected in requirement.get("families", {}).items():
            actual = actual_families[family]
            if actual != int(expected):
                requirement_violations.append(
                    f"{pool}:family:{family}:expected={expected}:actual={actual}"
                )
    return {
        "duplicate_ids": duplicate_ids,
        "duplicate_prompts": duplicate_prompts,
        "normalized_duplicate_prompts": normalized_duplicate_prompts,
        "unjustified_third_variants": unjustified,
        "mixed_fact_ownership": mixed_fact_ownership,
        "blind_pool_fact_collisions": blind_pool_fact_collisions,
        "blind_facts_with_multiple_presentations": blind_facts_with_multiple_presentations,
        "blind_pool_requirement_violations": requirement_violations,
    }
