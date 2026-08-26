"""Contratos y validadores para los bancos masivos derivados del PDF local."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Iterable


BANK_TARGETS: dict[str, dict[str, Any]] = {
    "DANIEL1-12": {
        "total": 8000,
        "chapters": {
            "DAN1": 450,
            "DAN2": 650,
            "DAN3": 550,
            "DAN4": 650,
            "DAN5": 500,
            "DAN6": 500,
            "DAN7": 900,
            "DAN8": 900,
            "DAN9": 850,
            "DAN10": 550,
            "DAN11": 1050,
            "DAN12": 450,
        },
    },
    "PR39-44": {
        "total": 6000,
        "chapters": {
            "PR39": 750,
            "PR40": 850,
            "PR41": 750,
            "PR42": 850,
            "PR43": 1450,
            "PR44": 1350,
        },
    },
}

TYPE_RATIOS = {
    "true_false": 0.25,
    "fill_blank": 0.30,
    "multiple_choice": 0.45,
}

DIFFICULTY_RATIOS = {
    "easy": 0.05,
    "medium": 0.20,
    "hard": 0.45,
    "expert": 0.30,
}


@dataclass(frozen=True)
class AtomicFact:
    fact_id: str
    bank: str
    chapter: str
    verse_or_page: str
    source_span: str
    subject: str
    action: str
    object: str
    context: str
    relation_type: str
    importance: str
    nearby_fact_ids: tuple[str, ...] = ()
    topic: str = ""
    sequence: int = 0
    answer: str = ""
    category: str = "phrase"

    def as_record(self) -> dict[str, Any]:
        value = asdict(self)
        value["nearby_fact_ids"] = list(self.nearby_fact_ids)
        return value


@dataclass(frozen=True)
class MassiveQuestion:
    id: str
    fact_id: str
    variant_id: str
    template_id: str
    bank: str
    chapter: str
    verse_or_page: str
    source_span: str
    type: str
    difficulty: str
    topic: str
    context_anchor: str
    question: str
    options: list[str]
    correct_answer: str
    accepted_answers: list[str]
    answer_mode: str
    explanation: str
    why_distractors_fail: dict[str, str]
    source_quote: str
    trap_type: str | None
    blind_final_pool: bool
    validation_status: str
    correct_option: int | None = None
    incorrect_detail: str | None = None
    correction: str | None = None

    def as_record(self) -> dict[str, Any]:
        return asdict(self)


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def exact_quota(total: int, ratio: float) -> int:
    return int(round(total * ratio))


def _duplicates(values: Iterable[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def validate_massive_bank(
    questions: list[MassiveQuestion],
    *,
    expected_total: int,
    expected_chapters: dict[str, int],
    enforce_distribution: bool = True,
) -> list[str]:
    errors: list[str] = []
    if len(questions) != expected_total:
        errors.append(f"total: {len(questions)}/{expected_total}")

    for duplicate in _duplicates(question.id for question in questions):
        errors.append(f"duplicate id: {duplicate}")
    for duplicate in _duplicates(question.variant_id for question in questions):
        errors.append(f"duplicate variant_id: {duplicate}")

    normalized_questions = [normalized_text(question.question) for question in questions]
    for duplicate in _duplicates(normalized_questions):
        if duplicate:
            errors.append(f"duplicate question text: {duplicate[:100]}")

    chapter_counts = Counter(question.chapter for question in questions)
    for chapter, expected in expected_chapters.items():
        if chapter_counts[chapter] != expected:
            errors.append(f"chapter {chapter}: {chapter_counts[chapter]}/{expected}")

    for question in questions:
        prefix = question.id
        required = {
            "fact_id": question.fact_id,
            "variant_id": question.variant_id,
            "template_id": question.template_id,
            "verse_or_page": question.verse_or_page,
            "source_span": question.source_span,
            "topic": question.topic,
            "context_anchor": question.context_anchor,
            "question": question.question,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "source_quote": question.source_quote,
            "validation_status": question.validation_status,
        }
        for field, value in required.items():
            if not str(value).strip():
                errors.append(f"{prefix}: missing {field}")
        if question.validation_status != "verified":
            errors.append(f"{prefix}: not verified")
        if question.type not in TYPE_RATIOS:
            errors.append(f"{prefix}: unsupported type {question.type}")
        if question.difficulty not in DIFFICULTY_RATIOS:
            errors.append(f"{prefix}: unsupported difficulty {question.difficulty}")
        if len(question.options) not in (2, 4):
            errors.append(f"{prefix}: invalid option count {len(question.options)}")
        if len({normalized_text(option) for option in question.options}) != len(question.options):
            errors.append(f"{prefix}: duplicate options")
        matching = [
            index
            for index, option in enumerate(question.options)
            if normalized_text(option) == normalized_text(question.correct_answer)
        ]
        if len(matching) != 1:
            errors.append(f"{prefix}: correct answer occurs {len(matching)} times")
        if question.correct_option is not None and matching and question.correct_option != matching[0]:
            errors.append(f"{prefix}: incorrect correct_option")
        if question.type == "true_false" and question.options != ["Verdadero", "Falso"]:
            errors.append(f"{prefix}: invalid true/false options")
        if question.type != "true_false" and len(question.options) != 4:
            errors.append(f"{prefix}: non-TF question requires four options")

    if enforce_distribution:
        by_type = Counter(question.type for question in questions)
        by_difficulty = Counter(question.difficulty for question in questions)
        for label, ratio in TYPE_RATIOS.items():
            expected = exact_quota(expected_total, ratio)
            if by_type[label] != expected:
                errors.append(f"type {label}: {by_type[label]}/{expected}")
        for label, ratio in DIFFICULTY_RATIOS.items():
            expected = exact_quota(expected_total, ratio)
            if by_difficulty[label] != expected:
                errors.append(f"difficulty {label}: {by_difficulty[label]}/{expected}")
        blind = sum(question.blind_final_pool for question in questions)
        minimum_blind = math.ceil(expected_total * 0.15)
        if blind < minimum_blind:
            errors.append(f"blind pool: {blind}/{minimum_blind} minimum")
        mc_questions = [question for question in questions if question.type == "multiple_choice"]
        traps = sum(question.trap_type == "true_elsewhere" for question in mc_questions)
        if mc_questions:
            ratio = traps / len(mc_questions)
            if ratio < 0.35 or ratio > 0.45:
                errors.append(f"contextual MC traps: {ratio:.3f} outside 0.35-0.45")
    return errors
