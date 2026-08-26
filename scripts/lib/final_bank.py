"""Contratos canónicos del Banco Maestro Único — Final 2026."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


BANK_ID = "BANCO_UNICO_CONEXION_BIBLICA_2026"
DISPLAY_NAME = "Banco Maestro Único — Final 2026"
SCHEMA_VERSION = "7.0"
QUESTION_FAMILIES = (
    "single_choice_direct",
    "fill_choice",
    "true_false",
    "single_choice_contextual",
)


def _option_count(family: str) -> int | None:
    if family == "true_false":
        return 2
    if family in QUESTION_FAMILIES:
        return 4
    return None


def validate_gold_bank(questions: Iterable[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for question in questions:
        question_id = str(question.get("id", "missing-id"))
        family = str(question.get("family", ""))
        options = question.get("options")
        if family not in QUESTION_FAMILIES:
            errors.append(f"{question_id}:invalid_family")
        expected_count = _option_count(family)
        if not isinstance(options, list) or len(options) != expected_count:
            errors.append(f"{question_id}:invalid_option_count")
        if question.get("bank_id") != BANK_ID:
            errors.append(f"{question_id}:invalid_bank_id")
        if question.get("final_editorial_status") != "GOLD":
            errors.append(f"{question_id}:not_gold")
    return errors


def validate_coverage(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "uncovered_source_units",
        "fact_without_gold_question",
        "unmapped_source_units",
    ):
        value = int(manifest.get(key, 0))
        if value:
            errors.append(f"{key}={value}")
    for unit in manifest.get("units", []):
        source_unit_id = str(unit.get("source_unit_id", "missing-unit"))
        if not unit.get("fact_ids"):
            errors.append(f"{source_unit_id}:missing_fact_ids")
        if not unit.get("gold_question_ids"):
            errors.append(f"{source_unit_id}:missing_gold_questions")
        if unit.get("coverage_status") != "covered":
            errors.append(f"{source_unit_id}:not_covered")
    return errors


def validate_source_inventory(units: Iterable[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for unit in units:
        source_unit_id = str(unit.get("source_unit_id", "missing-unit"))
        if not str(unit.get("full_text") or unit.get("exact_text") or "").strip():
            errors.append(f"{source_unit_id}:missing_text")
        if not unit.get("fact_ids"):
            errors.append(f"{source_unit_id}:missing_fact_ids")
    return errors
