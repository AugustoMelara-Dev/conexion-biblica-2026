"""Paquetes de fuente legibles para autoría competitiva."""

from __future__ import annotations

from typing import Any

SEMANTIC_HINT_KEYS = (
    "characters",
    "speakers",
    "recipients",
    "actions",
    "objects",
    "numbers",
    "periods",
    "years",
    "places",
    "rivers",
    "provinces",
    "lands",
    "directions",
    "causes",
    "consequences",
    "purposes",
    "lists",
    "sequences",
    "contrasts",
    "quotations",
    "applications",
    "comparisons",
    "descriptions",
    "cited_bible_references",
)


def _text(unit: dict[str, Any]) -> str:
    return str(unit.get("full_text") or unit.get("exact_text") or "").strip()


def _unit_code(unit: dict[str, Any]) -> str:
    prefix = "DAN" if unit["work"] == "Daniel" else "PR"
    return f"{prefix}{unit['chapter']}"


def build_source_packets(
    inventory: dict[str, Any],
    exclusions: dict[str, str],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    units = inventory["units"]
    packets: dict[str, list[dict[str, Any]]] = {}
    excluded: list[dict[str, str]] = []
    for index, unit in enumerate(units):
        source_unit_id = unit["source_unit_id"]
        if source_unit_id in exclusions:
            excluded.append(
                {
                    "source_unit_id": source_unit_id,
                    "source_ref": unit["reference"],
                    "reason": exclusions[source_unit_id],
                }
            )
            continue

        previous = units[index - 1] if index > 0 else None
        following = units[index + 1] if index + 1 < len(units) else None
        same_section = lambda candidate: bool(
            candidate
            and candidate["work"] == unit["work"]
            and candidate["chapter"] == unit["chapter"]
        )
        code = _unit_code(unit)
        packets.setdefault(code, []).append(
            {
                "source_unit_id": source_unit_id,
                "work": unit["work"],
                "chapter": unit["chapter"],
                "source_ref": unit["reference"],
                "source_quote": _text(unit),
                "parent_context": unit.get("parent_text"),
                "context_before": _text(previous) if same_section(previous) else None,
                "context_after": _text(following) if same_section(following) else None,
                "semantic_hints": {
                    key: unit[key]
                    for key in SEMANTIC_HINT_KEYS
                    if unit.get(key)
                },
            }
        )
    return packets, excluded
