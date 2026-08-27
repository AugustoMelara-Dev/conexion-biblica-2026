"""Inventario independiente de `MaterialConexionBiblica (1).pdf`.

El texto embebido conserva la segmentación pero pierde algunos glifos acentuados.
Solo esos tokens dañados se restauran usando el OCR español de la misma página.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import fitz

from scripts.lib.massive_generator import (
    DANIEL_LAST_VERSE,
    extract_all_daniel_verses,
    normalize_space,
)


TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ�0-9]+(?:-[A-Za-zÁÉÍÓÚÜÑáéíóúüñ�0-9]+)?")

KNOWN_CHARACTERS = {
    "Abed-nego", "Abiú", "Ananías", "Anciano de días", "Arioc", "Asuero",
    "Azarías", "Belsasar", "Beltsasar", "Ciro", "Daniel", "Darío", "Gabriel",
    "Hijo del Hombre", "Joacim", "Melsar", "Mesac", "Miguel", "Misael",
    "Nabucodonosor", "Nadab", "Sadrac",
}
KNOWN_PLACES = {
    "Amón", "Babilonia", "Egipto", "Elam", "Etiopía", "Grecia", "Jerusalén",
    "Judá", "Libia", "Media", "Moab", "Persia", "Quitim", "Sinar", "Susa",
    "Israel", "Roma", "Sión", "Canaán", "Caldea", "Judea",
}
KNOWN_RIVERS = {"Éufrates", "Hidekel", "Quebar", "Chebar", "Ulai"}
DIRECTIONS = {"norte", "sur", "oriente", "occidente", "poniente"}
NUMBER_WORDS = {
    "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
    "diez", "once", "doce", "trece", "veinte", "treinta", "cuarenta", "cincuenta",
    "sesenta", "setenta", "ciento", "ciento veinte", "mil", "millones",
}
ACTION_WORDS = {
    "acusó", "adoró", "bendijo", "contestó", "declaró", "dijo", "entregó", "escribió",
    "habló", "hizo", "interpretó", "levantó", "mandó", "miraba", "ordenó", "oró",
    "preguntó", "recibió", "respondió", "salió", "tuvo", "vio", "volvió",
}


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _context_score(source_tokens: list[str], index: int, ocr_tokens: list[str], candidate: int) -> float:
    source_before = [_norm(value) for value in source_tokens[max(0, index - 4):index] if "�" not in value]
    source_after = [_norm(value) for value in source_tokens[index + 1:index + 5] if "�" not in value]
    ocr_before = [_norm(value) for value in ocr_tokens[max(0, candidate - 6):candidate] if not value.isdigit()]
    ocr_after = [_norm(value) for value in ocr_tokens[candidate + 1:candidate + 7] if not value.isdigit()]
    before = SequenceMatcher(None, source_before, ocr_before[-len(source_before):]).ratio() if source_before else 0
    after = SequenceMatcher(None, source_after, ocr_after[:len(source_after)]).ratio() if source_after else 0
    return before + after


def restore_corrupted_glyphs(embedded_text: str, ocr_text: str) -> tuple[str, list[dict[str, Any]]]:
    """Restaura exclusivamente tokens que contienen U+FFFD.

    Devuelve incidencias no resueltas; nunca altera tokens sanos del PDF.
    """

    if "�" not in embedded_text:
        return normalize_space(embedded_text), []
    source_matches = list(TOKEN_RE.finditer(embedded_text))
    source_tokens = [match.group() for match in source_matches]
    ocr_tokens = TOKEN_RE.findall(ocr_text)
    replacements: list[tuple[int, int, str]] = []
    issues: list[dict[str, Any]] = []
    for index, match in enumerate(source_matches):
        damaged = match.group()
        if "�" not in damaged:
            continue
        wildcard = re.compile(
            "^" + re.escape(damaged).replace("�", ".") + "$", re.IGNORECASE
        )
        candidates = [position for position, token in enumerate(ocr_tokens) if wildcard.match(token)]
        if candidates:
            scored = sorted(
                ((_context_score(source_tokens, index, ocr_tokens, position), position) for position in candidates),
                reverse=True,
            )
            best_score = scored[0][0]
            best_tokens = {
                ocr_tokens[position]
                for score, position in scored
                if abs(score - best_score) < 0.0001
            }
            if len(best_tokens) == 1:
                replacements.append((match.start(), match.end(), best_tokens.pop()))
                continue
        issues.append(
            {
                "damaged_token": damaged,
                "context": normalize_space(embedded_text[max(0, match.start() - 50):match.end() + 50]),
                "candidates": sorted({ocr_tokens[position] for position in candidates}),
                "status": "unresolved",
            }
        )
    restored = embedded_text
    for start, end, value in reversed(replacements):
        restored = f"{restored[:start]}{value}{restored[end:]}"
    return normalize_space(restored), issues


def _split_propositions(text: str) -> list[str]:
    normalized = normalize_space(text)
    raw = re.split(r"(?<=[.!?])(?:[”’\"»])?\s+|\s*;\s+(?=[A-ZÁÉÍÓÚÜÑ])", normalized)
    propositions = [item.strip() for item in raw if len(item.strip().split()) >= 4]
    return propositions or [normalized]


def _matches(text: str, values: set[str]) -> list[str]:
    return sorted(value for value in values if re.search(rf"\b{re.escape(value)}\b", text, re.IGNORECASE))


def _phrases(text: str, markers: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for proposition in _split_propositions(text):
        if any(re.search(rf"\b{re.escape(marker)}\b", proposition, re.IGNORECASE) for marker in markers):
            result.append(proposition)
    return result


def _metadata(text: str) -> dict[str, Any]:
    tokens = TOKEN_RE.findall(text)
    numbers = sorted({token for token in tokens if token.isdigit() or _norm(token) in NUMBER_WORDS})
    actions = sorted({token for token in tokens if token in ACTION_WORDS or re.search(r"(?:ó|aron|ieron|aba|ían)$", token)})
    quotes = [next(value for value in match if value) for match in re.findall(r"“([^”]+)”|«([^»]+)»|\"([^\"]+)\"", text)]
    return {
        "characters": _matches(text, KNOWN_CHARACTERS),
        "speakers": [],
        "recipients": [],
        "actions": actions,
        "objects": [],
        "numbers": numbers,
        "periods": _phrases(text, ("días", "años", "tiempo", "semana", "semanas")),
        "years": _phrases(text, ("año", "años")),
        "places": _matches(text, KNOWN_PLACES),
        "rivers": _matches(text, KNOWN_RIVERS),
        "provinces": _phrases(text, ("provincia", "provincias")),
        "lands": _phrases(text, ("tierra", "tierras")),
        "directions": _matches(text, DIRECTIONS),
        "causes": _phrases(text, ("porque", "por cuanto", "puesto que", "a causa")),
        "consequences": _phrases(text, ("por tanto", "entonces", "así", "de modo")),
        "purposes": _phrases(text, ("para", "a fin de")),
        "lists": [item for item in _split_propositions(text) if item.count(",") >= 2],
        "sequences": _phrases(text, ("antes", "después", "entonces", "luego", "al cabo")),
        "contrasts": _phrases(text, ("pero", "aunque", "sin embargo", "no obstante")),
        "quotations": quotes,
    }


def extract_daniel_inventory(
    document: fitz.Document, ocr_pages: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    verses = extract_all_daniel_verses(document)
    units: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for chapter in range(1, 13):
        assert len(verses[chapter]) == DANIEL_LAST_VERSE[chapter]
        for verse, (page, embedded) in verses[chapter].items():
            restored, unresolved = restore_corrupted_glyphs(embedded, ocr_pages[str(page)])
            # El texto embebido pega una marca de nota al final de Daniel 1:21.
            # No forma parte del versículo ni puede convertirse en un hecho.
            restored = re.sub(r"(?<=[.!?])\d{1,3}$", "", restored)
            source_unit_id = f"DAN{chapter}-V{verse:03d}"
            issues.extend({**issue, "source_unit_id": source_unit_id, "page": page} for issue in unresolved)
            units.append(
                {
                    "source_unit_id": source_unit_id,
                    "work": "Daniel",
                    "chapter": chapter,
                    "verse": verse,
                    "page": page,
                    "reference": f"Daniel {chapter}:{verse}",
                    "full_text": restored,
                    "meaningful_clauses": _split_propositions(restored),
                    **_metadata(restored),
                    "fact_ids": [],
                }
            )
    return units, issues


def _pr_chapter(page: int) -> int:
    if page <= 32:
        return 39
    if page <= 37:
        return 40
    if page <= 42:
        return 41
    if page <= 46:
        return 42
    if page <= 54:
        return 43
    return 44


def extract_pr_inventory(
    document: fitz.Document, ocr_pages: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    units: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for page in range(27, 60):
        paragraph_number = 0
        for block in document[page - 1].get_text("blocks"):
            if block[1] < 85 or re.fullmatch(r"\s*\d{2,3}\s*", block[4]):
                continue
            block_text = re.sub(r"\n\s*\d{2,3}\s*$", "", block[4])
            for raw_paragraph in re.split(r"\n\s*\n", block_text):
                embedded = normalize_space(raw_paragraph)
                if len(embedded.split()) < 7:
                    continue
                paragraph_number += 1
                restored, unresolved = restore_corrupted_glyphs(embedded, ocr_pages[str(page)])
                propositions = _split_propositions(restored)
                for proposition_number, proposition in enumerate(propositions, 1):
                    source_unit_id = (
                        f"PR{_pr_chapter(page)}-P{page:03d}-"
                        f"P{paragraph_number:03d}-S{proposition_number:03d}"
                    )
                    related = [
                        {**issue, "source_unit_id": source_unit_id, "page": page}
                        for issue in unresolved
                        if issue["damaged_token"] in proposition or "�" in proposition
                    ]
                    issues.extend(related)
                    units.append(
                        {
                            "source_unit_id": source_unit_id,
                            "work": "Profetas y Reyes",
                            "chapter": _pr_chapter(page),
                            "page": page,
                            "paragraph": paragraph_number,
                            "proposition": proposition_number,
                            "reference": f"PR{_pr_chapter(page)}, p. {page}, párrafo {paragraph_number}",
                            "parent_text": restored,
                            "exact_text": proposition,
                            "meaningful_clauses": [proposition],
                            **_metadata(proposition),
                            "applications": _phrases(proposition, ("debemos", "pueden", "necesitamos", "iglesia")),
                            "comparisons": _phrases(proposition, ("como", "así como", "más que")),
                            "descriptions": [proposition],
                            "cited_bible_references": re.findall(
                                r"\b(?:Daniel|Isaías|Jeremías|Ezequiel|Mateo|Salmos|Miqueas|Joel|Hechos|Deuteronomio|Proverbios|Apocalipsis)\s+\d+(?::\d+(?:[-–]\d+)?)?",
                                proposition,
                            ),
                            "fact_ids": [],
                        }
                    )
    return units, issues


def build_source_inventory(
    pdf_path: str | Path, ocr_pages: dict[str, str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    with fitz.open(pdf_path) as document:
        daniel_units, daniel_issues = extract_daniel_inventory(document, ocr_pages)
        pr_units, pr_issues = extract_pr_inventory(document, ocr_pages)
    issues = daniel_issues + pr_issues
    inventory = {
        "schema_version": "7.0",
        "source_file": Path(pdf_path).name,
        "daniel_verses": len(daniel_units),
        "pr_propositions": len(pr_units),
        "source_units": len(daniel_units) + len(pr_units),
        "units": daniel_units + pr_units,
    }
    issue_report = {
        "schema_version": "7.0",
        "source_file": Path(pdf_path).name,
        "extraction_method": "texto embebido segmentado + restauración de glifos U+FFFD mediante OCR visual español",
        "documented_corrections": [
            {
                "reference": "Daniel 5:18",
                "issue": "el mapa de texto de la página muestra 8 entre los versículos 17 y 19",
                "resolution": "se restaura 18 por continuidad visual de la numeración",
            }
        ],
        "unresolved_count": len(issues),
        "issues": issues,
    }
    return inventory, issue_report
