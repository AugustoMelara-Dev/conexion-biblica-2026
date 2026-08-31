"""Author/reviewer separation and atomic release gate for competitive v13.

Accepted author inputs are either the canonical envelope or a legacy-friendly
array whose rows carry ``author: {id, model}``.  All emitted artifacts use the
canonical envelope; author identity never enters a blind review packet.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from scripts.lib.competitive_v11 import audit_corpus, normalize_prompt, validate_question


AUTHORED_SCHEMA = "competitive-v13-authored/v1"
BLIND_SCHEMA = "competitive-v13-blind-review/v1"
REVIEW_SCHEMA = "competitive-v13-semantic-review/v1"
APPLIED_SCHEMA = "competitive-v13-reviewed-release/v1"

FAMILIES = {
    "single_choice_direct",
    "single_choice_contextual",
    "fill_choice",
    "true_false",
}
AUTHOR_REQUIRED = {
    "id",
    "source_unit_id",
    "fact_id",
    "family",
    "subtype",
    "question",
    "options",
    "correct_option",
    "accepted_answers",
    "explanation",
    "why_distractors_fail",
    "evidence_excerpt",
    "difficulty",
    "importance",
    "relation_type",
    "option_category",
    "false_mutation",
    "blank_span",
    "significance",
    "variant_justification",
}
FORBIDDEN_AUTHOR_FIELDS = {
    "review",
    "ai_review",
    "reviewer",
    "blind_pool",
    "blind_packet",
    "source_ref",
    "source_quote",
    "correct_answer",
    "content_sha256",
}
BLIND_VISIBLE_FIELDS = (
    "id",
    "source_unit_id",
    "fact_id",
    "family",
    "subtype",
    "question",
    "options",
    "evidence_excerpt",
    "difficulty",
    "importance",
    "relation_type",
    "option_category",
    "variant_justification",
)
CONTEXTUAL_SUBTYPES = {
    "cause_consequence",
    "narrative_order",
    "relationship",
    "comparison",
    "principle",
    "cross_source_integration",
}
GENERIC_PROMPT_PREAMBLE = re.compile(
    r"^(?:pregunta(?:\s+\d+)?|elige\s+la\s+(?:opcion|respuesta)\s+correcta|"
    r"selecciona\s+la\s+respuesta\s+correcta|responde\s+correctamente)\b"
)
EDITORIAL_PREAMBLE = re.compile(
    r"^(?:elige|identifica|decide|determina|verifica|reconstruye|recupera|"
    r"compara|contrasta|examina|juzga|localiza|comprueba|atiende|fija|separa)\b"
)


class ContractError(ValueError):
    """Raised before any release artifact is mutated."""


def canonical_hash(value: object, *, omitted: Sequence[str] = ()) -> str:
    if isinstance(value, Mapping):
        value = {key: item for key, item in value.items() if key not in set(omitted)}
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def keyed_hash(value: object, *, binding_key: bytes) -> str:
    if len(binding_key) < 32:
        raise ContractError("blind binding key must contain at least 32 bytes")
    return hmac.new(
        binding_key,
        canonical_hash(value).encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def authored_content_hash(row: Mapping[str, Any]) -> str:
    return canonical_hash(row, omitted=("author", "role"))


def blind_packet_hash(packet: Mapping[str, Any]) -> str:
    return canonical_hash(packet, omitted=("packet_sha256",))


def review_decision_hash(
    decision: Mapping[str, Any],
    *,
    reviewer: object,
    blind_packet_sha256: str,
) -> str:
    """Bind a decision to both reviewer identity and the exact blind packet."""

    return canonical_hash(
        {
            "decision": {
                key: value for key, value in decision.items() if key != "review_sha256"
            },
            "reviewer": reviewer,
            "blind_packet_sha256": blind_packet_sha256,
        }
    )


def blind_batch_id(batch: Mapping[str, Any], *, binding_key: bytes) -> str:
    if len(binding_key) < 32:
        raise ContractError("blind binding key must contain at least 32 bytes")
    hashes = [authored_content_hash(row) for row in batch.get("questions", [])]
    binding = canonical_hash(
        {
            "author": batch.get("author"),
            "source_sha256": batch.get("source_sha256"),
            "questions": hashes,
        }
    ).encode("utf-8")
    commitment = hmac.new(binding_key, binding, hashlib.sha256).hexdigest()
    public_binding = {
        "authorship_commitment": commitment,
        "source_sha256": batch.get("source_sha256"),
        "questions": hashes,
    }
    return f"blind-{canonical_hash(public_binding)[:20]}"


def _author_id(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        return str(value.get("id") or "").strip()
    return ""


def _contains_replacement_character(value: object) -> bool:
    if isinstance(value, str):
        return any(
            marker in value
            for marker in ("\ufffd", "\ufeff", "Ã", "Â", "â€", "ðŸ", "ï»¿", "ï¿½")
        )
    if isinstance(value, Mapping):
        return any(_contains_replacement_character(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_replacement_character(item) for item in value)
    return False


def base_fact_sources(
    questions: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Return the canonical fact→source mapping, rejecting an inconsistent base."""

    mapping: dict[str, str] = {}
    for row in questions:
        fact_id = str(row.get("fact_id") or "")
        source_unit_id = str(row.get("source_unit_id") or "")
        if not fact_id or not source_unit_id:
            raise ContractError("base question missing fact_id/source_unit_id")
        previous = mapping.setdefault(fact_id, source_unit_id)
        if previous != source_unit_id:
            raise ContractError(f"base fact maps to multiple sources: {fact_id}")
    return mapping


def base_presentations(
    questions: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    """Expose only existing public presentation text needed for blind comparison."""

    result: dict[str, list[dict[str, str]]] = {}
    seen: set[tuple[str, str]] = set()
    for row in questions:
        fact_id = str(row.get("fact_id") or "")
        question = str(row.get("question") or "").strip()
        key = (fact_id, normalize_prompt(question))
        if not fact_id or not question or key in seen:
            continue
        seen.add(key)
        result.setdefault(fact_id, []).append(
            {
                "question": question,
                "family": str(row.get("family") or ""),
                "subtype": str(row.get("subtype") or ""),
            }
        )
    return result


def repetitive_prompt_preambles(prompts: Sequence[object]) -> list[str]:
    """Return templated imperative prefixes repeated four or more times."""

    prefixes: list[str] = []
    for prompt in prompts:
        raw = str(prompt or "")
        prefix, separator, _ = raw.partition(":")
        normalized = normalize_prompt(prefix)
        if separator and len(normalized) <= 24 * 6 and EDITORIAL_PREAMBLE.match(normalized):
            prefixes.append(normalized)
    return sorted(prefix for prefix, count in Counter(prefixes).items() if count >= 4)


def normalize_authored_input(
    value: object,
    *,
    batch_id: str | None = None,
    source_sha256: str | None = None,
) -> dict[str, Any]:
    """Normalize canonical envelopes and per-row-author arrays.

    Array inputs require one common non-empty author id.  Missing ``role`` is
    normalized to ``variant``; an explicitly different role is preserved so
    validation can reject it rather than silently changing author intent.
    """

    def normalize_row(row: Mapping[str, Any], *, remove_author: bool) -> dict[str, Any]:
        normalized = deepcopy(dict(row))
        if remove_author:
            normalized.pop("author", None)
        normalized.setdefault("role", "variant")
        for key in ("difficulty", "importance"):
            if isinstance(normalized.get(key), str):
                normalized[key] = normalized[key].lower()
        if normalized.get("family") == "selection":
            subtype = str(normalized.get("subtype") or "").lower()
            contextual = subtype == "contextual" or subtype in CONTEXTUAL_SUBTYPES
            normalized["family"] = (
                "single_choice_contextual" if contextual else "single_choice_direct"
            )
            if subtype == "direct":
                normalized["subtype"] = "factual_recall"
            elif subtype == "contextual":
                normalized["subtype"] = "relationship"
        return normalized

    if isinstance(value, Mapping):
        document = deepcopy(dict(value))
        questions = document.get("questions")
        if isinstance(questions, list):
            row_authors = [
                row.get("author")
                for row in questions
                if isinstance(row, Mapping) and row.get("author") is not None
            ]
            if row_authors:
                if (
                    len(row_authors) != len(questions)
                    or len({canonical_hash(author) for author in row_authors}) != 1
                    or _author_id(document.get("author")) != _author_id(row_authors[0])
                ):
                    raise ContractError("envelope and per-row author identities must agree")
                document["author"] = deepcopy(row_authors[0])
            document["questions"] = [
                normalize_row(row, remove_author=bool(row_authors))
                if isinstance(row, Mapping)
                else deepcopy(row)
                for row in questions
            ]
        return document
    if not isinstance(value, list):
        raise ContractError("authored input must be an envelope or an array")
    if not value:
        raise ContractError("authored array must not be empty")
    author_values = [row.get("author") for row in value if isinstance(row, Mapping)]
    author_hashes = {canonical_hash(author) for author in author_values}
    if (
        len(author_values) != len(value)
        or len(author_hashes) != 1
        or not _author_id(author_values[0] if author_values else None)
    ):
        raise ContractError("authored array must have one common author.id")
    author = deepcopy(author_values[0])
    questions: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, Mapping):
            raise ContractError("authored array rows must be mappings")
        questions.append(normalize_row(row, remove_author=True))
    return {
        "schema_version": AUTHORED_SCHEMA,
        "release": 2,
        "batch_id": batch_id or f"r2-{canonical_hash(value)[:16]}",
        "author": author,
        "source_sha256": source_sha256 or "unspecified",
        "questions": questions,
    }


def _compile_candidate(
    authored: Mapping[str, Any],
    source: Mapping[str, Any],
    *,
    reviewer: str,
    review_sha256: str,
    keep_blind_null: bool = True,
) -> dict[str, Any]:
    row = deepcopy(dict(authored))
    row["role"] = "variant"
    row["correct_answer"] = row["options"][row["correct_option"]]
    row["source_ref"] = source.get("source_ref")
    row["source_quote"] = source.get("source_quote")
    row["blind_pool"] = None
    row["ai_review"] = {
        "status": "passed",
        "reviewer_type": "ai_semantic_audit",
        "protocol": "independent_semantic_review_v13",
        "reviewer": reviewer,
        "review_sha256": review_sha256,
    }
    if not keep_blind_null:
        row.pop("blind_pool", None)
    return row


def validate_authored_batch(
    batch: Mapping[str, Any] | object,
    source_units: Mapping[str, Mapping[str, Any]],
    *,
    expected_source_sha256: str | None = None,
    expected_fact_sources: Mapping[str, str] | None = None,
    existing_presentations: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
) -> list[str]:
    if not isinstance(batch, Mapping):
        return ["batch: expected mapping"]
    errors: list[str] = []
    if batch.get("schema_version") != AUTHORED_SCHEMA:
        errors.append(f"schema_version: expected {AUTHORED_SCHEMA!r}")
    if batch.get("release") != 2:
        errors.append("release: expected 2")
    for key in ("batch_id", "source_sha256"):
        if not isinstance(batch.get(key), str) or not batch.get(key).strip():
            errors.append(f"{key}: expected non-empty string")
    if (
        expected_source_sha256 is not None
        and batch.get("source_sha256") != expected_source_sha256
    ):
        errors.append("source_sha256_mismatch")
    if not _author_id(batch.get("author")):
        errors.append("author: expected non-empty identity")
    questions = batch.get("questions")
    if not isinstance(questions, list) or not questions:
        return [*errors, "questions: expected non-empty list"]

    ids: list[str] = []
    prompts: list[str] = []
    facts: list[str] = []
    for index, row in enumerate(questions):
        prefix = f"questions[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{prefix}: expected mapping")
            continue
        forbidden = sorted(FORBIDDEN_AUTHOR_FIELDS.intersection(row))
        if forbidden:
            if any(key in row for key in ("review", "ai_review", "reviewer")):
                errors.append(f"{prefix}.embedded_review_forbidden")
            errors.extend(f"{prefix}.{key}: forbidden" for key in forbidden)
        missing = sorted(AUTHOR_REQUIRED - set(row))
        errors.extend(f"{prefix}.{key}: missing" for key in missing)
        if _contains_replacement_character(row):
            errors.append(f"{prefix}.replacement_character")
        normalized_prompt = normalize_prompt(str(row.get("question") or ""))
        if GENERIC_PROMPT_PREAMBLE.match(normalized_prompt):
            errors.append(f"{prefix}.generic_prompt_preamble")
        if missing:
            continue
        if row.get("role", "variant") != "variant":
            errors.append(f"{prefix}.role: expected 'variant'")
        if row.get("difficulty") not in {"hard", "expert"}:
            errors.append(f"{prefix}.difficulty: expected hard or expert")
        if row.get("family") not in FAMILIES:
            errors.append(f"{prefix}.family: invalid")
        source_id = str(row.get("source_unit_id") or "")
        fact_id = str(row.get("fact_id") or "")
        if expected_fact_sources is not None:
            expected_source = expected_fact_sources.get(fact_id)
            if expected_source is None:
                errors.append(f"{prefix}.fact_id: not in public base")
            elif expected_source != source_id:
                errors.append(f"{prefix}.fact_source_mismatch")
        if existing_presentations is not None:
            existing_prompts = {
                normalize_prompt(str(item.get("question") or ""))
                for item in existing_presentations.get(fact_id, ())
            }
            if normalized_prompt and normalized_prompt in existing_prompts:
                errors.append(f"{prefix}.existing_prompt_reused")
        source = source_units.get(source_id)
        if source is None:
            errors.append(f"{prefix}.source_unit_id: unknown {source_id!r}")
            continue
        try:
            candidate = _compile_candidate(
                row, source, reviewer="pending-independent-review", review_sha256="pending"
            )
        except (IndexError, KeyError, TypeError):
            errors.append(f"{prefix}.correct_option: invalid")
            continue
        semantic_errors = validate_question(candidate, source_units)
        errors.extend(f"{prefix}.{error}" for error in semantic_errors)
        ids.append(str(row.get("id") or ""))
        prompts.append(normalize_prompt(str(row.get("question") or "")))
        facts.append(str(row.get("fact_id") or ""))
    for label, values in (("id", ids), ("prompt", prompts), ("fact_id", facts)):
        for value, count in Counter(values).items():
            if value and count > 1:
                errors.append(f"questions.duplicate_{label}:{value}")
    errors.extend(
        f"questions.repetitive_prompt_preamble:{prefix}"
        for prefix in repetitive_prompt_preambles(
            row.get("question") for row in questions if isinstance(row, Mapping)
        )
    )
    return errors


def build_blind_review_packet(
    batch: Mapping[str, Any],
    source_units: Mapping[str, Mapping[str, Any]],
    *,
    binding_key: bytes,
    expected_source_sha256: str | None = None,
    base_questions: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    fact_sources = base_fact_sources(base_questions) if base_questions else None
    presentations = base_presentations(base_questions) if base_questions else None
    errors = validate_authored_batch(
        batch,
        source_units,
        expected_source_sha256=expected_source_sha256,
        expected_fact_sources=fact_sources,
        existing_presentations=presentations,
    )
    if errors:
        raise ContractError("invalid authored batch: " + "; ".join(errors))
    questions: list[dict[str, Any]] = []
    for authored in batch["questions"]:
        source = source_units[authored["source_unit_id"]]
        visible = {key: deepcopy(authored[key]) for key in BLIND_VISIBLE_FIELDS}
        visible.update(
            {
                "authored_content_sha256": authored_content_hash(authored),
                "source_ref": source["source_ref"],
                "source_quote": source["source_quote"],
                "parent_context": source.get("parent_context"),
                "existing_presentations": deepcopy(
                    (presentations or {}).get(authored["fact_id"], [])
                ),
            }
        )
        questions.append(visible)
    packet: dict[str, Any] = {
        "schema_version": BLIND_SCHEMA,
        "release": 2,
        "blind_batch_id": blind_batch_id(batch, binding_key=binding_key),
        "source_sha256": batch["source_sha256"],
        "questions": questions,
    }
    packet["packet_sha256"] = blind_packet_hash(packet)
    return packet


def validate_review(
    batch: Mapping[str, Any],
    packet: Mapping[str, Any],
    review: Mapping[str, Any] | object,
    *,
    binding_key: bytes,
) -> list[str]:
    if not isinstance(review, Mapping):
        return ["review: expected mapping"]
    errors: list[str] = []
    if review.get("schema_version") != REVIEW_SCHEMA:
        errors.append(f"schema_version: expected {REVIEW_SCHEMA!r}")
    reviewer = _author_id(review.get("reviewer"))
    if not reviewer:
        errors.append("reviewer: expected non-empty identity")
    if reviewer and reviewer == _author_id(batch.get("author")):
        errors.append("reviewer_must_differ_from_author")
    if review.get("blind_batch_id") != packet.get("blind_batch_id"):
        errors.append("blind_batch_id_mismatch")
    if packet.get("blind_batch_id") != blind_batch_id(
        batch, binding_key=binding_key
    ):
        errors.append("blind_batch_authorship_binding_mismatch")
    if packet.get("packet_sha256") != blind_packet_hash(packet):
        errors.append("blind_packet_sha256_invalid")
    if review.get("blind_packet_sha256") != packet.get("packet_sha256"):
        errors.append("blind_packet_sha256_mismatch")

    authored_by_id = {row.get("id"): row for row in batch.get("questions", [])}
    decisions = review.get("decisions")
    if not isinstance(decisions, list):
        return [*errors, "decisions: expected list"]
    decision_ids = [row.get("question_id") for row in decisions if isinstance(row, Mapping)]
    if Counter(decision_ids) != Counter(authored_by_id.keys()):
        errors.append("decisions_must_cover_each_authored_question_once")
    for index, decision in enumerate(decisions):
        prefix = f"decisions[{index}]"
        if not isinstance(decision, Mapping):
            errors.append(f"{prefix}: expected mapping")
            continue
        authored = authored_by_id.get(decision.get("question_id"))
        if authored is None:
            errors.append(f"{prefix}.question_id: unknown")
            continue
        if decision.get("authored_content_sha256") != authored_content_hash(authored):
            errors.append(f"{prefix}.authored_content_sha256_mismatch")
        if decision.get("review_sha256") != review_decision_hash(
            decision,
            reviewer=review.get("reviewer"),
            blind_packet_sha256=str(review.get("blind_packet_sha256") or ""),
        ):
            errors.append(f"{prefix}.review_sha256_mismatch")
        status = decision.get("decision")
        if status not in {"approved", "rejected"}:
            errors.append(f"{prefix}.decision: expected approved or rejected")
        option = decision.get("adjudicated_option")
        if isinstance(option, bool) or not isinstance(option, int) or not 0 <= option < len(authored["options"]):
            errors.append(f"{prefix}.adjudicated_option: invalid")
        elif option != authored.get("correct_option"):
            errors.append(f"{prefix}.adjudicated_option_mismatch")
        ambiguity = decision.get("second_defensible_option")
        if not isinstance(ambiguity, bool):
            errors.append(f"{prefix}.second_defensible_option: expected boolean")
        elif status == "approved" and ambiguity is not False:
            errors.append(f"{prefix}.second_defensible_option: expected false")
        for key in ("rationale", "source_alignment_reason"):
            if not isinstance(decision.get(key), str) or not decision.get(key).strip():
                errors.append(f"{prefix}.{key}: expected reason")
    return errors


def compile_reviewed_batch(
    batch: Mapping[str, Any],
    packet: Mapping[str, Any],
    review: Mapping[str, Any],
    source_units: Mapping[str, Mapping[str, Any]],
    *,
    binding_key: bytes,
    expected_source_sha256: str | None = None,
    base_questions: Sequence[Mapping[str, Any]] = (),
) -> dict[str, list[dict[str, Any]]]:
    fact_sources = base_fact_sources(base_questions) if base_questions else None
    presentations = base_presentations(base_questions) if base_questions else None
    authored_errors = validate_authored_batch(
        batch,
        source_units,
        expected_source_sha256=expected_source_sha256,
        expected_fact_sources=fact_sources,
        existing_presentations=presentations,
    )
    if authored_errors:
        raise ContractError("invalid authored batch: " + "; ".join(authored_errors))
    expected_packet = build_blind_review_packet(
        batch,
        source_units,
        binding_key=binding_key,
        expected_source_sha256=expected_source_sha256
        , base_questions=base_questions
    )
    if packet != expected_packet:
        raise ContractError("blind packet does not match authored content")
    review_errors = validate_review(
        batch, packet, review, binding_key=binding_key
    )
    if review_errors:
        raise ContractError("invalid review: " + "; ".join(review_errors))
    authored_by_id = {row["id"]: row for row in batch["questions"]}
    approved: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for decision in review["decisions"]:
        authored = authored_by_id[decision["question_id"]]
        if decision["decision"] != "approved":
            pending.append(
                {
                    "question_id": decision["question_id"],
                    "authored_content_sha256": decision["authored_content_sha256"],
                    "decision": "rejected",
                    "review_sha256": decision["review_sha256"],
                    "rationale": decision["rationale"],
                }
            )
            continue
        source = source_units[authored["source_unit_id"]]
        candidate = _compile_candidate(
            authored,
            source,
            reviewer=_author_id(review["reviewer"]),
            review_sha256=decision["review_sha256"],
            keep_blind_null=True,
        )
        semantic_errors = validate_question(candidate, source_units)
        if semantic_errors:
            raise ContractError(
                f"compiled question {candidate['id']} invalid: {semantic_errors}"
            )
        candidate.pop("blind_pool", None)
        approved.append(candidate)
    return {"approved": approved, "pending": pending}


def apply_reviewed_release_atomic(
    triples: Sequence[tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]],
    source_units: Mapping[str, Mapping[str, Any]],
    output: Path,
    *,
    binding_key: bytes,
    base_questions: Sequence[Mapping[str, Any]] = (),
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate the complete release and replace one output file atomically."""

    approved: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    for batch, packet, review in triples:
        compiled = compile_reviewed_batch(
            batch,
            packet,
            review,
            source_units,
            binding_key=binding_key,
            expected_source_sha256=expected_source_sha256,
            base_questions=base_questions,
        )
        approved.extend(compiled["approved"])
        pending.extend(compiled["pending"])
        batches.append(
            {
                "batch_id": batch["batch_id"],
                "blind_packet_sha256": packet["packet_sha256"],
                "reviewer": _author_id(review["reviewer"]),
                "approved": len(compiled["approved"]),
                "pending": len(compiled["pending"]),
            }
        )
    audit_rows = [*base_questions, *approved]
    approved_facts = [str(row.get("fact_id") or "") for row in approved]
    duplicate_facts = sorted(
        fact_id for fact_id, count in Counter(approved_facts).items() if fact_id and count > 1
    )
    if duplicate_facts:
        raise ContractError(f"duplicate Release 2 fact_ids: {duplicate_facts}")
    violations = {key: value for key, value in audit_corpus(audit_rows).items() if value}
    if violations:
        raise ContractError(f"corpus audit failed: {violations}")
    if any("blind" in key for row in approved for key in row):
        raise ContractError("approved release contains blind metadata")
    result: dict[str, Any] = {
        "schema_version": APPLIED_SCHEMA,
        "release": 2,
        "batches": batches,
        "approved": approved,
        "pending": pending,
    }
    result["release_sha256"] = canonical_hash(result)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return result
