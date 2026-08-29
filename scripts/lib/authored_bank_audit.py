"""Módulo de auditoría estricta y compuertas de calidad para el banco autorizado."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from scripts.lib.authored_question import (
    ALLOWED_SUBTYPES,
    PROHIBITED_PROMPT_PATTERNS,
    _norm,
)

EXPECTED_UNITS = (
    "DAN1", "DAN2", "DAN3", "DAN4", "DAN5", "DAN6",
    "DAN7", "DAN8", "DAN9", "DAN10", "DAN11", "DAN12",
    "PR39", "PR40", "PR41", "PR42", "PR43", "PR44",
)

BLANK_PATTERN = re.compile(r"_{3,}")


def content_hash(question: Mapping[str, Any]) -> str:
    canonical = {
        "id": question.get("id"),
        "question": question.get("question"),
        "options": question.get("options"),
        "correct_option": question.get("correct_option"),
        "correct_answer": question.get("correct_answer"),
        "explanation": question.get("explanation"),
        "why_distractors_fail": question.get("why_distractors_fail"),
        "source_ref": question.get("source_ref"),
        "source_quote": question.get("source_quote"),
        "evidence_excerpt": question.get("evidence_excerpt"),
        "difficulty": question.get("difficulty"),
        "subtype": question.get("subtype"),
        "false_mutation": question.get("false_mutation"),
    }
    dumped = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def audit_authored_bank(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    violations: dict[str, list[str]] = {
        "duplicate_ids": [],
        "duplicate_prompts": [],
        "normalized_duplicate_prompts": [],
        "source_location_prompts": [],
        "missing_evidence": [],
        "answer_leaks": [],
        "cross_passage_false_mutations": [],
        "nonparallel_distractors": [],
        "two_defensible_options": [],
        "trivial_completion_blanks": [],
        "invalid_subtypes": [],
        "invalid_ai_reviews": [],
        "unsupported_answers": [],
    }

    seen_ids: set[str] = set()
    seen_prompts: set[str] = set()
    seen_norm_prompts: dict[str, str] = {}

    for row in rows:
        qid = str(row.get("id") or "UNKNOWN_ID")
        prompt = str(row.get("question") or "").strip()
        norm_p = _norm(prompt)

        # ID uniqueness
        if qid in seen_ids:
            violations["duplicate_ids"].append(qid)
        seen_ids.add(qid)

        # Exact prompt uniqueness
        if prompt in seen_prompts:
            violations["duplicate_prompts"].append(qid)
        seen_prompts.add(prompt)

        # Normalized prompt uniqueness
        if norm_p in seen_norm_prompts:
            violations["normalized_duplicate_prompts"].append(qid)
        else:
            seen_norm_prompts[norm_p] = qid

        # Source location prompt prohibition
        for pat in PROHIBITED_PROMPT_PATTERNS:
            if pat.search(prompt):
                violations["source_location_prompts"].append(qid)
                break

        # Evidence
        evidence = str(row.get("evidence_excerpt") or "").strip()
        if not evidence:
            violations["missing_evidence"].append(qid)

        # Answer leaks into prompt
        correct_ans = str(row.get("correct_answer") or "").strip()
        family = str(row.get("family") or "").strip()
        if family != "true_false" and len(correct_ans) > 4:
            norm_ans = _norm(correct_ans)
            # If the full non-trivial answer appears verbatim inside the prompt (excluding fill blanks)
            if family != "fill_choice" and len(norm_ans.split()) > 1 and norm_ans in norm_p:
                violations["answer_leaks"].append(qid)

        # Completion blank checks
        if family == "fill_choice":
            if not BLANK_PATTERN.search(prompt) and "____" not in prompt:
                violations["trivial_completion_blanks"].append(qid)

        # False statement mutation check
        if family == "true_false" and correct_ans == "Falso":
            mutation = row.get("false_mutation")
            if not isinstance(mutation, dict) or not mutation.get("local", False):
                violations["cross_passage_false_mutations"].append(qid)
            elif not mutation.get("changed_fields"):
                violations["cross_passage_false_mutations"].append(qid)

        # Subtype
        subtype = str(row.get("subtype") or "").strip()
        if subtype not in ALLOWED_SUBTYPES:
            violations["invalid_subtypes"].append(qid)

        # AI review
        ai_review = row.get("ai_review")
        if not isinstance(ai_review, dict) or ai_review.get("status") != "passed":
            violations["invalid_ai_reviews"].append(qid)
        elif "human" in str(ai_review.get("reviewer_type", "")).lower():
            violations["invalid_ai_reviews"].append(qid)

        # Support in quote
        source_quote = str(row.get("source_quote") or "").strip()
        if family != "true_false":
            norm_ans = _norm(correct_ans)
            norm_quote = _norm(source_quote)
            norm_ev = _norm(evidence)
            ans_tokens = set(norm_ans.split()) - {"de", "la", "el", "los", "las", "en", "un", "una", "y", "a", "del", "al"}
            quote_tokens = set(norm_quote.split()) | set(norm_ev.split())
            if ans_tokens and not (ans_tokens & quote_tokens) and norm_ans not in norm_quote and norm_ans not in norm_ev:
                violations["unsupported_answers"].append(qid)

    return violations
