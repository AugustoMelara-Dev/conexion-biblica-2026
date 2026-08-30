"""Compila prosa ya redactada por IA al contrato V11; no genera enunciados."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from scripts.lib.competitive_v11 import content_hash, validate_question


def compile_authored_batch(
    authored_inputs: Sequence[Mapping[str, Any]],
    source_units: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    questions: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    for authored in authored_inputs:
        source_unit_id = str(authored["source_unit_id"])
        source = source_units[source_unit_id]
        options = list(authored["options"])
        correct_option = int(authored["correct_option"])
        correct_answer = str(options[correct_option])
        family = str(authored["family"])
        review = authored["review"]
        question = {
            "id": authored["id"],
            "source_unit_id": source_unit_id,
            "fact_id": authored["fact_id"],
            "role": "central",
            "family": family,
            "subtype": authored["subtype"],
            "question": authored["question"],
            "options": options,
            "correct_option": correct_option,
            "correct_answer": correct_answer,
            "accepted_answers": list(authored.get("accepted_answers", [correct_answer])),
            "explanation": authored["explanation"],
            "why_distractors_fail": dict(authored["why_distractors_fail"]),
            "source_ref": source["source_ref"],
            "source_quote": source["source_quote"],
            "evidence_excerpt": source["source_quote"],
            "difficulty": authored["difficulty"],
            "importance": authored["importance"],
            "relation_type": authored["relation_type"],
            "option_category": authored["option_category"],
            "false_mutation": authored.get("false_mutation"),
            "blank_span": correct_answer if family == "fill_choice" else None,
            "significance": authored.get("significance") if family == "fill_choice" else None,
            "variant_justification": None,
            "blind_pool": authored.get("blind_pool"),
            "ai_review": {
                "status": "passed",
                "reviewer_type": "ai_semantic_audit",
                "reviewer": review["reviewer"],
            },
        }
        errors = validate_question(question, source_units)
        if errors:
            raise ValueError(f"{question['id']}: {', '.join(errors)}")
        questions.append(question)
        reviews.append(
            {
                "question_id": question["id"],
                "content_sha256": content_hash(question),
                "decision": "ai_authored_and_semantically_reviewed",
                "reviewer_type": "ai_semantic_audit",
                "reviewer": review["reviewer"],
                "reasons": [review["rationale"]],
                "second_defensible_option": False,
            }
        )
    return questions, reviews
