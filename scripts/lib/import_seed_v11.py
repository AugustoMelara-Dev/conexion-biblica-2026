"""Importación sin reautoría del banco competitivo de producción."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from scripts.lib.competitive_v11 import content_hash, validate_question


def _family_for_variant(parent_family: str, variant: Mapping[str, Any]) -> str:
    options = variant.get("options")
    if isinstance(options, list) and set(options) == {"Verdadero", "Falso"}:
        return "true_false"
    if "____" in str(variant.get("question") or ""):
        return "fill_choice"
    if parent_family == "single_choice_contextual":
        return parent_family
    return "single_choice_direct"


def _authored_row(
    raw: Mapping[str, Any],
    *,
    role: str,
    family: str,
    parent: Mapping[str, Any],
    ai_review: Mapping[str, Any],
    false_mutation_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    correct_answer = str(raw["correct_answer"])
    return {
        "id": raw["id"],
        "source_unit_id": parent["source_unit_id"],
        "fact_id": parent["fact_id"],
        "role": role,
        "family": family,
        "subtype": parent["subtype"],
        "question": raw["question"],
        "options": list(raw["options"]),
        "correct_option": raw["correct_option"],
        "correct_answer": correct_answer,
        "accepted_answers": list(raw["accepted_answers"]),
        "explanation": raw["explanation"],
        "why_distractors_fail": dict(raw["why_distractors_fail"]),
        "source_ref": parent["source_ref"],
        "source_quote": parent["source_quote"],
        "evidence_excerpt": parent["evidence_excerpt"],
        "difficulty": parent["difficulty"],
        "importance": parent["importance"],
        "relation_type": parent["relation_type"],
        "option_category": parent["option_category"],
        "false_mutation": (
            dict(false_mutation_override)
            if false_mutation_override is not None
            else raw.get("false_mutation")
        ),
        "blank_span": correct_answer if family == "fill_choice" else None,
        "significance": (
            "Expresión relevante conservada desde el banco competitivo de producción."
            if family == "fill_choice"
            else None
        ),
        "variant_justification": None,
        "blind_pool": raw.get("blind_pool", parent.get("blind_pool")),
        "ai_review": {
            "status": ai_review["status"],
            "reviewer_type": ai_review["reviewer_type"],
            "reviewer": ai_review["reviewer"],
        },
        **(
            {"answer_support_term": raw["answer_support_term"]}
            if raw.get("answer_support_term")
            else {}
        ),
    }


def import_seed(
    unit_code: str,
    raw_questions: Sequence[Mapping[str, Any]],
    source_units: Mapping[str, Mapping[str, Any]],
    *,
    false_mutation_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    editorial_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    false_mutation_overrides = false_mutation_overrides or {}
    editorial_overrides = editorial_overrides or {}
    authored: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    for parent in raw_questions:
        adversarial = parent.get("validation_adversarial")
        if (
            not isinstance(adversarial, Mapping)
            or adversarial.get("status") != "passed"
            or adversarial.get("second_defensible_option") is not False
        ):
            raise ValueError(f"{parent.get('id')}: revisión adversarial inválida")
        central_override = editorial_overrides.get(str(parent["id"]), {})
        central_input = {
            **parent,
            **{
                key: central_override[key]
                for key in ("question", "answer_support_term")
                if key in central_override
            },
        }
        central = _authored_row(
            central_input,
            role="central",
            family=str(parent["family"]),
            parent=parent,
            ai_review=parent["ai_review"],
            false_mutation_override=false_mutation_overrides.get(str(parent["id"])),
        )
        central_errors = validate_question(central, source_units)
        if central_errors:
            raise ValueError(f"{central['id']}: {', '.join(central_errors)}")
        authored.append(central)
        reviews.append(
            {
                "question_id": central["id"],
                "content_sha256": content_hash(central),
                "source_content_sha256": parent["content_sha256"],
                "decision": (
                    "corrected_during_v11_import"
                    if central_override
                    else "inherited_verified_production"
                ),
                "reviewer_type": "ai_semantic_audit",
                "reviewer": adversarial["reviewer"],
            }
        )

        for variant in parent.get("presentation_variants", []):
            variant_review = variant.get("review")
            if (
                not isinstance(variant_review, Mapping)
                or variant_review.get("status") != "passed"
                or variant_review.get("second_defensible_option") is not False
            ):
                raise ValueError(f"{variant.get('id')}: revisión de variante inválida")
            family = _family_for_variant(str(parent["family"]), variant)
            variant_with_metadata = dict(variant)
            variant_override = editorial_overrides.get(str(variant["id"]), {})
            for key in ("question", "answer_support_term"):
                if key in variant_override:
                    variant_with_metadata[key] = variant_override[key]
            if (
                family == "true_false"
                and variant.get("correct_answer") == "Falso"
                and not variant.get("false_mutation")
            ):
                variant_with_metadata["false_mutation"] = false_mutation_overrides.get(
                    str(variant.get("id"))
                )
            authored_variant = _authored_row(
                variant_with_metadata,
                role="variant",
                family=family,
                parent=parent,
                ai_review=variant_review,
                false_mutation_override=false_mutation_overrides.get(
                    str(variant["id"])
                ),
            )
            variant_errors = validate_question(authored_variant, source_units)
            if variant_errors:
                raise ValueError(
                    f"{authored_variant['id']}: {', '.join(variant_errors)}"
                )
            authored.append(authored_variant)
            reviews.append(
                {
                    "question_id": authored_variant["id"],
                    "content_sha256": content_hash(authored_variant),
                    "source_content_sha256": variant["content_sha256"],
                    "decision": (
                        "corrected_during_v11_import"
                        if variant_override
                        else "inherited_verified_production"
                    ),
                    "reviewer_type": variant_review["reviewer_type"],
                    "reviewer": variant_review["reviewer"],
                }
            )
    return authored, reviews
