"""Extracción conservadora de relaciones explícitas para el banco V8.

Este módulo no interpreta la fuente. Solo produce candidatos cuando la relación
y la respuesta están escritas en la misma unidad, con un ancla contextual que
permite una respuesta única.
"""

from __future__ import annotations

import re
from typing import Any


_WORD = r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9-]+"


def _source_text(unit: dict[str, Any]) -> str:
    return str(unit.get("full_text") or unit.get("exact_text") or "").strip()


def _candidate(
    unit: dict[str, Any],
    *,
    answer: str,
    question: str,
    relation_type: str,
    category: str,
    score: float,
) -> dict[str, Any] | None:
    quote = _source_text(unit)
    answer = answer.strip("  ,;:.¡!¿?\"“”«»")
    if not answer or not 1 <= len(answer.split()) <= 8 or quote.count(answer) != 1:
        return None
    return {
        "answer": answer,
        "question": question,
        "semantic_skill": relation_type,
        "relation_type": relation_type,
        "category": category,
        "score": score,
        "source_quote": quote,
        "source_unit_id": unit["source_unit_id"],
        "reference": unit["reference"],
    }


# Casos cuya relación es inequívoca pero cuya puntuación o sintaxis histórica
# hace que una expresión regular general sea menos segura. Cada respuesta es un
# tramo literal del PDF y queda cubierta por pruebas de regresión.
_CURATED: dict[str, list[dict[str, str | float]]] = {
    "DAN9-V011": [
        {
            "answer": "la maldición y el juramento",
            "question": (
                "Según Daniel 9:11, ¿qué cayó sobre Israel como consecuencia "
                "de que traspasó la Ley y se apartó para no obedecer?"
            ),
            "relation_type": "consequence",
            "category": "phrase",
            "score": 12.0,
        },
        {
            "answer": "contra Dios pecamos",
            "question": (
                "Según Daniel 9:11, ¿qué causa declara el texto para la caída "
                "de la maldición y el juramento sobre Israel?"
            ),
            "relation_type": "cause",
            "category": "phrase",
            "score": 11.5,
        },
    ],
    "DAN7-V026": [
        {
            "answer": "destruido y arruinado hasta el fin",
            "question": (
                "Según Daniel 7:26, ¿cuál es el propósito declarado de que al "
                "poder juzgado le quiten su dominio?"
            ),
            "relation_type": "purpose",
            "category": "phrase",
            "score": 12.0,
        }
    ],
    "DAN3-V026": [
        {
            "answer": "Nabucodonosor",
            "question": (
                "Según Daniel 3:26, ¿quién pronunció la orden «salid y venid» "
                "junto a la puerta del horno?"
            ),
            "relation_type": "speaker",
            "category": "person",
            "score": 12.0,
        },
        {
            "answer": "Sadrac, Mesac y Abed-nego, siervos del Dios Altísimo",
            "question": (
                "Según Daniel 3:26, ¿a quiénes dirigió Nabucodonosor la orden "
                "«salid y venid»?"
            ),
            "relation_type": "recipient",
            "category": "phrase",
            "score": 12.0,
        },
    ],
    "PR41-P038-P001-S001": [
        {
            "answer": "la parte que le tocaba desempeñar",
            "question": (
                "Según PR41, p. 38, párrafo 1, ¿qué debía comprender "
                "Nabucodonosor acerca de su papel en la historia del mundo?"
            ),
            "relation_type": "purpose",
            "category": "phrase",
            "score": 12.0,
        }
    ],
}


def _first_words(value: str, maximum: int = 8) -> str:
    matches = list(re.finditer(_WORD, value))
    if not matches:
        return ""
    selected = matches[:maximum]
    return value[selected[0].start():selected[-1].end()]


def _generic_purposes(unit: dict[str, Any]) -> list[dict[str, Any]]:
    text = _source_text(unit)
    reference = str(unit["reference"])
    rows: list[dict[str, Any]] = []
    for match in re.finditer(
        r"\bpara que\s+(?P<answer>[^,;.!?]{3,120})", text, re.IGNORECASE
    ):
        raw = match.group("answer").strip()
        # El auxiliar no es el contenido que se desea recuperar.
        raw = re.sub(r"^(?:sea|sean|fuera|fuesen)\s+", "", raw, flags=re.IGNORECASE)
        answer = _first_words(raw)
        row = _candidate(
            unit,
            answer=answer,
            question=(
                f"Según {reference}, ¿qué propósito declara explícitamente "
                "la expresión «para que» en esta escena?"
            ),
            relation_type="purpose",
            category="phrase" if len(answer.split()) > 1 else "action",
            score=8.0,
        )
        if row:
            rows.append(row)
    return rows


def _generic_causes(unit: dict[str, Any]) -> list[dict[str, Any]]:
    text = _source_text(unit)
    reference = str(unit["reference"])
    rows: list[dict[str, Any]] = []
    for match in re.finditer(
        r"\b(?:porque|por cuanto|puesto que)\s+(?P<answer>[^,;.!?]{3,120})",
        text,
        re.IGNORECASE,
    ):
        answer = _first_words(match.group("answer"))
        # Exigir sujeto o verbo reduce fragmentos editoriales sin autonomía.
        if len(answer.split()) < 2:
            continue
        before_words = re.findall(_WORD, text[:match.start()])[-12:]
        anchor = " ".join(before_words).strip()
        if not anchor:
            continue
        row = _candidate(
            unit,
            answer=answer,
            question=(
                f"Según {reference}, en la afirmación «{anchor}», ¿qué razón "
                "introduce explícitamente el conector causal?"
            ),
            relation_type="cause",
            category="phrase",
            score=7.5,
        )
        if row:
            rows.append(row)
    return rows


def _generic_consequences(unit: dict[str, Any]) -> list[dict[str, Any]]:
    text = _source_text(unit)
    reference = str(unit["reference"])
    rows: list[dict[str, Any]] = []
    for match in re.finditer(
        r"\b(?:por lo cual|por tanto|de modo que)\s+(?P<answer>[^,;.!?]{3,120})",
        text,
        re.IGNORECASE,
    ):
        answer = _first_words(match.group("answer"))
        if len(answer.split()) < 2:
            continue
        row = _candidate(
            unit,
            answer=answer,
            question=(
                f"Según {reference}, ¿qué consecuencia introduce explícitamente "
                "el conector de resultado en esta unidad?"
            ),
            relation_type="consequence",
            category="phrase",
            score=7.5,
        )
        if row:
            rows.append(row)
    return rows


def extract_relation_candidates(unit: dict[str, Any]) -> list[dict[str, Any]]:
    """Devuelve solo relaciones literales, breves y de respuesta única."""

    rows: list[dict[str, Any]] = []
    for raw in _CURATED.get(str(unit["source_unit_id"]), []):
        row = _candidate(unit, **raw)
        if row:
            rows.append(row)

    if str(unit["source_unit_id"]) not in _CURATED:
        rows.extend(_generic_purposes(unit))
        rows.extend(_generic_causes(unit))
        rows.extend(_generic_consequences(unit))

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        unique.setdefault((str(row["relation_type"]), str(row["answer"]).casefold()), row)
    return sorted(
        unique.values(),
        key=lambda row: (-float(row["score"]), str(row["relation_type"]), str(row["answer"])),
    )
