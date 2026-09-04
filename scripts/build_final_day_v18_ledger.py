"""Build the canonical V18 source ledger from the verified OCR cache.

The builder is deliberately deterministic.  It only extracts source units,
links existing question identifiers, and reports mechanical comparisons.  It
does not author questions or adjudicate answers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


EXPECTED_SOURCE_SHA256 = (
    "0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3"
)
LEDGER_SCHEMA_VERSION = "final-day-v18-source-ledger-1.0"
ALLOWED_COVERAGE = {
    "COVERED",
    "COVERED_MERGED",
    "NEEDS_QUESTION",
    "NON_ATOMIC",
    "REFERENCE_ONLY",
    "AMBIGUOUS_SOURCE",
}

# This is an observed OCR label in the verified cache, not a correction.  The
# canonical unit remains addressable by its Daniel verse identity, while its
# evidence is explicitly flagged as ambiguous.
KNOWN_OCR_AMBIGUITIES: dict[str, str] = {
    "DAN5-V018": (
        "OCR página 13 muestra el marcador de versículo como «8»; no se "
        "corrige automáticamente a «18»."
    ),
}

# The review evidence is intentionally explicit and partial.  These are the
# PDF pages rendered and inspected during this task; every other heuristic
# classification remains flagged for a later visual/editorial check.
VISUAL_REVIEWED_PDF_PAGES = [3, 13, 27, 33, 59]
VISUAL_REVIEWED_SAMPLES = [
    {
        "pdf_page": 3,
        "source_unit_id": "DAN1-V014",
        "finding": "La lectura OCR difiere de la palabra visible en el PDF; queda AMBIGUOUS_SOURCE.",
    },
    {
        "pdf_page": 13,
        "source_unit_id": "DAN5-V018",
        "finding": "El marcador OCR observado es «8»; no se corrige automáticamente a «18».",
    },
    {
        "pdf_page": 27,
        "source_unit_id": "PR39-P027-P002-S002",
        "finding": "La lectura OCR de una palabra difiere de la palabra visible; queda AMBIGUOUS_SOURCE.",
    },
    {
        "pdf_page": 33,
        "source_unit_id": "PR40-P033-P001-S001",
        "finding": "Muestra de transición de maquetación PR; no se promueve una corrección textual.",
    },
    {
        "pdf_page": 59,
        "source_unit_id": "PR44-P059-P001-S001",
        "finding": "Muestra de cierre PR; se conserva el texto extraído sin inferencias.",
    },
]

REFERENCE_BOOKS = (
    "Daniel",
    "Isaías",
    "Jeremías",
    "Ezequiel",
    "Mateo",
    "Salmos",
    "Miqueas",
    "Joel",
    "Hechos",
    "Deuteronomio",
    "Proverbios",
    "Apocalipsis",
)
_REFERENCE_BOOK_PATTERN = "(?:" + "|".join(map(re.escape, REFERENCE_BOOKS)) + ")"
_REFERENCE_NUMBER_PATTERN = r"\d+(?::\d+(?:[-–]\d+)?)?(?:[-–]\d+)?"
REFERENCE_ONLY_RE = re.compile(
    rf"^{_REFERENCE_BOOK_PATTERN}\s+{_REFERENCE_NUMBER_PATTERN}"
    rf"(?:\s*[,;]\s*(?:{_REFERENCE_BOOK_PATTERN}\s+)?{_REFERENCE_NUMBER_PATTERN})*"
    rf"\s*[.;]?$",
    re.IGNORECASE,
)

# ``source_inventory`` deliberately uses punctuation for stable extraction;
# this small classifier prevents one known anaphoric fragment from becoming a
# fresh authoring target.  It is a classification signal, never a text repair.
ANAPHORIC_FRAGMENT_COMPACT = {"yasilohicieron"}

CSV_COLUMNS = [
    "source_unit_id",
    "work",
    "chapter",
    "verse_or_page",
    "pdf_page",
    "exact_quote",
    "nearby_context",
    "atomic_facts",
    "atomic_fact_count",
    "atomic_fact_records",
    "current_question_ids",
    "presentation_count",
    "distinct_cognitive_operations",
    "coverage_status",
    "coverage_basis",
    "coverage_scope",
    "semantic_coverage_verified",
    "explanation",
    "historical_fact_ids",
    "historical_fact_count",
    "ocr_support",
    "ocr_issue",
    "context_boundary",
    "review_flags",
    "requires_visual_review",
    "visual_review_status",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalise_for_match(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", without_marks.lower())


def _normalise_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _is_reference_only(text: str) -> bool:
    """Return true only when a source item consists entirely of references."""

    return bool(REFERENCE_ONLY_RE.fullmatch(_normalise_space(text)))


def _is_anaphoric_fragment(text: str) -> bool:
    """Identify a short, context-dependent fragment without rewriting it."""

    return _normalise_for_match(text) in ANAPHORIC_FRAGMENT_COMPACT


def _split_atomic_facts(source: Mapping[str, Any]) -> list[str]:
    """Expose stable fact children without pretending punctuation is semantics.

    ``source_inventory`` already provides sentence-like clauses.  PR sometimes
    leaves two independent clauses joined by a semicolon and a lower-case
    conjunction; split only that reproducible shape and flag the result for
    visual review.  The parent source-unit ID remains stable for existing bank
    links, while each child receives a deterministic ``-Fnn`` ID.
    """

    canonical = str(source.get("full_text") or source.get("exact_text") or "").strip()
    candidates = source.get("meaningful_clauses") or [canonical]
    facts: list[str] = []
    for candidate in candidates:
        value = _normalise_space(str(candidate))
        if not value:
            continue
        conjunction = (
            r"(?:[A-ZÁÉÍÓÚÜÑ]|y\b|e\b|pero\b|aunque\b|sin\s+embargo\b|"
            r"por\s+tanto\b|así\b)"
        )
        pieces = re.split(
            rf"(?<=;”)\s+(?=“\s*{conjunction})|;\s+(?={conjunction})",
            value,
            flags=re.IGNORECASE,
        )
        for piece in pieces:
            normalized = _normalise_space(piece)
            if normalized and normalized not in facts:
                facts.append(normalized)
    return facts or [canonical]


def _fact_question_ids(
    rows: Sequence[Mapping[str, Any]],
    source_unit_id: str,
    fact_index: int,
    fact_count: int,
) -> list[str]:
    """Link a child only when the existing fact ID carries the same suffix.

    Most PR IDs and the original Daniel IDs use ``<source>-Fnn``.  V11 IDs
    carry an additional historical marker and are intentionally not treated as
    fact-level proof.  The parent still records all source-unit links.
    """

    if fact_count == 1:
        return sorted(str(row["id"]) for row in rows if row.get("id"))
    expected_suffix = f"-F{fact_index:02d}"
    result = []
    for row in rows:
        fact_id = str(row.get("fact_id") or "")
        if (
            fact_id.startswith(source_unit_id + "-")
            and fact_id.endswith(expected_suffix)
            and row.get("id")
        ):
            result.append(str(row["id"]))
    return sorted(set(result))


def _as_path(value: str | Path) -> Path:
    return value if isinstance(value, Path) else Path(value)


def _stable_path(path: Path, repository_root: Path) -> str:
    """Serialize repository paths without embedding a checkout-specific root."""

    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError:
        return path.name


def load_verified_source(
    pdf_path: str | Path,
    ocr_cache_path: str | Path,
) -> tuple[dict[str, Any], int]:
    """Load and verify the PDF/cache identity before any extraction."""

    pdf = _as_path(pdf_path)
    cache_path = _as_path(ocr_cache_path)
    if not pdf.exists():
        raise FileNotFoundError(f"No existe la fuente PDF: {pdf}")
    if not cache_path.exists():
        raise FileNotFoundError(f"No existe la caché OCR: {cache_path}")

    pdf_sha256 = _sha256(pdf)
    if pdf_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            "PDF no coincide con SHA-256 canónico: "
            f"esperado={EXPECTED_SOURCE_SHA256} actual={pdf_sha256}"
        )

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Caché OCR JSON inválida: {cache_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("La caché OCR debe ser un objeto JSON")
    if payload.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            "Caché OCR no coincide con SHA-256 canónico: "
            f"esperado={EXPECTED_SOURCE_SHA256} actual={payload.get('source_sha256')!r}"
        )
    pages = payload.get("pages")
    if not isinstance(pages, dict) or not pages:
        raise ValueError("La caché OCR no contiene un mapa de páginas")
    if any(not str(page).isdigit() or not isinstance(text, str) for page, text in pages.items()):
        raise ValueError("La caché OCR contiene páginas o texto inválidos")

    try:
        import fitz

        with fitz.open(pdf) as document:
            page_count = document.page_count
    except ImportError as exc:
        raise RuntimeError("PyMuPDF (fitz) es necesario para contar páginas") from exc
    if page_count != 60:
        raise ValueError(f"La fuente PDF debe tener 60 páginas; se hallaron {page_count}")
    return payload, page_count


def _extract_source_units(
    pdf_path: Path,
    pages: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Use the repository's stable segmentation while retaining OCR evidence.

    ``source_inventory`` supplies only stable verse/paragraph boundaries and
    source-unit IDs.  Its text is derived from the verified PDF and repaired
    only with the supplied same-source OCR cache; OCR support is checked again
    below and never silently promoted when it disagrees.
    """

    try:
        import fitz
        from scripts.lib.source_inventory import (
            extract_daniel_inventory,
            extract_pr_inventory,
        )
    except ImportError as exc:
        raise RuntimeError(
            "No se pudo cargar la segmentación canónica de source_inventory"
        ) from exc

    with fitz.open(pdf_path) as document:
        daniel_units, daniel_issues = extract_daniel_inventory(document, dict(pages))
        pr_units, pr_issues = extract_pr_inventory(document, dict(pages))
    units = daniel_units + pr_units
    if len(units) != 1031:
        raise ValueError(f"Se esperaban 1031 unidades fuente; se hallaron {len(units)}")
    issues_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in daniel_issues + pr_issues:
        source_unit_id = issue.get("source_unit_id")
        if source_unit_id:
            issues_by_unit[str(source_unit_id)].append(dict(issue))
    for unit in units:
        unit["_source_inventory_issues"] = issues_by_unit.get(
            str(unit["source_unit_id"]), []
        )
    return units


def _ocr_support(
    canonical_text: str,
    page: int,
    pages: Mapping[str, str],
) -> tuple[bool, str | None]:
    """Check whether a unit's normalized text occurs in nearby OCR pages."""

    page_keys = [str(page)]
    # A paragraph can continue at the top of the next page.  Two pages are
    # sufficient for the source segmentation used by this repository.
    for next_page in (page + 1, page + 2):
        if str(next_page) in pages:
            page_keys.append(str(next_page))
    raw = "\n".join(pages[key] for key in page_keys)
    if _normalise_for_match(canonical_text) in _normalise_for_match(raw):
        return True, None
    return (
        False,
        "La cita normalizada no aparece completa en el OCR de las páginas "
        + ", ".join(page_keys)
        + "; se conserva la cita canónica y se requiere revisión visual.",
    )


def _load_current_questions(
    root: Path,
    unit_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[str]]:
    manifest_path = root / "public" / "banks" / "final-2026" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No existe el manifest actual: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    questions: list[dict[str, Any]] = []
    for shard in manifest.get("shards", []):
        relative = shard.get("questions_file")
        if not isinstance(relative, str):
            raise ValueError("Shard sin questions_file válido")
        path = root / "public" / relative
        if not path.exists():
            raise FileNotFoundError(f"No existe shard actual: {path}")
        rows = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError(f"Shard no es una lista JSON: {path}")
        questions.extend(row for row in rows if isinstance(row, dict))

    by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unmapped_question_ids: list[str] = []
    for index, row in enumerate(questions):
        source_unit_id = row.get("source_unit_id")
        question_id = row.get("id")
        question_label = str(question_id) if question_id else f"<row-{index + 1:04d}>"
        if isinstance(source_unit_id, str) and source_unit_id in unit_ids:
            by_unit[source_unit_id].append(row)
        else:
            unmapped_question_ids.append(question_label)
    return questions, by_unit, sorted(unmapped_question_ids)


def _historical_fact_records(master_path: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    if not master_path.exists():
        return {"available": False, "path": str(master_path)}, {}
    payload = json.loads(master_path.read_text(encoding="utf-8"))
    rows = payload.get("questions") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Banco Maestro no contiene questions como lista")
    records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field in ("FULL_FACT_IDS", "PARTIAL_FACT_IDS", "INCIDENTAL_FACT_IDS"):
            ids = row.get(field) or []
            if not isinstance(ids, list):
                continue
            for fact_id in ids:
                if isinstance(fact_id, str) and fact_id:
                    records[fact_id].append(row)
    declared = (
        payload.get("metadata", {})
        .get("inputs_congelados", {})
        .get("FACT_total")
    )
    return {
        "available": True,
        "path": str(master_path),
        "question_count": len(rows),
        "declared_fact_count": declared,
    }, records


def _page_range_from_source(value: str) -> set[int]:
    matches = re.search(r"\bp{1,2}\.\s*(\d+)(?:\s*[-–]\s*(\d+))?", value, re.IGNORECASE)
    if not matches:
        return set()
    first = int(matches.group(1))
    last = int(matches.group(2) or first)
    return set(range(first, last + 1))


def _map_historical_facts(
    fact_records: Mapping[str, Sequence[Mapping[str, Any]]],
    units: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, set[str]], list[str]]:
    """Map only IDs with an unambiguous structural source-unit match."""

    unit_ids = {str(unit["source_unit_id"]) for unit in units}
    by_unit: dict[str, set[str]] = defaultdict(set)
    unmapped: list[str] = []
    for fact_id, rows in sorted(fact_records.items()):
        match = re.fullmatch(r"FACT-D(\d+)-V(\d+)-\d+", fact_id)
        if match:
            source_unit_id = f"DAN{int(match.group(1))}-V{int(match.group(2)):03d}"
            if source_unit_id in unit_ids:
                by_unit[source_unit_id].add(fact_id)
            else:
                unmapped.append(fact_id)
            continue

        match = re.fullmatch(r"FACT-PR(\d+)-P(\d+)-(\d+)", fact_id)
        if not match:
            unmapped.append(fact_id)
            continue
        chapter, paragraph, proposition = map(int, match.groups())
        candidate_ids: set[str] = set()
        for row in rows:
            pages = _page_range_from_source(str(row.get("fuente", "")))
            if not pages:
                continue
            for unit in units:
                if (
                    unit.get("work") == "Profetas y Reyes"
                    and int(unit.get("chapter", -1)) == chapter
                    and int(unit.get("page", -1)) in pages
                    and int(unit.get("paragraph", -1)) == paragraph
                    and int(unit.get("proposition", -1)) == proposition
                ):
                    candidate_ids.add(str(unit["source_unit_id"]))
        if len(candidate_ids) == 1:
            by_unit[next(iter(candidate_ids))].add(fact_id)
        else:
            unmapped.append(fact_id)
    return by_unit, sorted(unmapped)


def _operations(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    values: set[str] = set()
    for row in rows:
        # subtype is the closest existing mechanical representation of the
        # cognitive operation; the other fields preserve useful distinctions
        # when subtype is absent, without deciding editorial quality.
        value = row.get("subtype") or row.get("topic") or row.get("family")
        if value:
            values.add(str(value))
    return sorted(values)


def _unit_reference(unit: Mapping[str, Any]) -> str:
    if unit.get("work") == "Daniel":
        return str(unit.get("reference") or f"Daniel {unit['chapter']}:{unit['verse']}")
    return str(unit.get("reference") or f"PR{unit['chapter']}, p. {unit['page']}")


def _build_units(
    source_units: Sequence[Mapping[str, Any]],
    pages: Mapping[str, str],
    by_current_unit: Mapping[str, Sequence[Mapping[str, Any]]],
    historical_by_unit: Mapping[str, set[str]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, source in enumerate(source_units):
        source_unit_id = str(source["source_unit_id"])
        canonical_text = str(source.get("full_text") or source.get("exact_text") or "").strip()
        page = int(source.get("page"))
        current_rows = list(by_current_unit.get(source_unit_id, []))
        current_ids = sorted(
            str(row["id"])
            for row in current_rows
            if row.get("id")
        )
        historical_ids = sorted(historical_by_unit.get(source_unit_id, set()))
        support, issue = _ocr_support(canonical_text, page, pages)
        if source_unit_id in KNOWN_OCR_AMBIGUITIES:
            support = False
            issue = KNOWN_OCR_AMBIGUITIES[source_unit_id]
        source_inventory_issues = list(source.get("_source_inventory_issues") or [])
        if source_inventory_issues:
            support = False
            issue = (
                "La segmentación canónica dejó glifos OCR sin restaurar; "
                "se requiere revisión visual antes de usar la cita."
            )

        atomic_facts = _split_atomic_facts(source)
        reference_only = _is_reference_only(canonical_text)
        anaphoric_fragment = _is_anaphoric_fragment(canonical_text)
        review_flags: list[str] = []
        if len(atomic_facts) > 1:
            review_flags.append("ATOMIC_SPLIT_HEURISTIC")
        if reference_only:
            review_flags.append("REFERENCE_ONLY_HEURISTIC")
        if anaphoric_fragment:
            review_flags.append("NON_ATOMIC_ANAPHORA_HEURISTIC")
        if source_unit_id in KNOWN_OCR_AMBIGUITIES:
            review_flags.append("OCR_MARKER_CONFLICT")
        if not support:
            review_flags.append("OCR_SUPPORT_MISSING")
        if source_inventory_issues:
            review_flags.append("OCR_GLYPH_RESTORATION_UNRESOLVED")
        if "�" in canonical_text:
            review_flags.append("OCR_REPLACEMENT_GLYPH")

        previous = source_units[index - 1] if index else None
        following = source_units[index + 1] if index + 1 < len(source_units) else None

        def same_editorial_boundary(candidate: Mapping[str, Any] | None) -> bool:
            return bool(
                candidate
                and candidate.get("work") == source.get("work")
                and int(candidate.get("chapter", -1)) == int(source.get("chapter", -2))
            )

        previous_same = same_editorial_boundary(previous)
        following_same = same_editorial_boundary(following)
        previous_text = ""
        following_text = ""
        if previous_same and previous:
            previous_text = str(previous.get("full_text") or previous.get("exact_text") or "").strip()
        if following_same and following:
            following_text = str(following.get("full_text") or following.get("exact_text") or "").strip()
        nearby_parts = []
        if previous_text:
            nearby_parts.append(f"Anterior: {previous_text}")
        if following_text:
            nearby_parts.append(f"Posterior: {following_text}")
        nearby_context = " ".join(nearby_parts)

        if previous is not None and not previous_same:
            context_boundary = (
                "WORK"
                if previous.get("work") != source.get("work")
                else "CHAPTER"
            )
        elif following is not None and not following_same:
            context_boundary = (
                "WORK"
                if following.get("work") != source.get("work")
                else "CHAPTER"
            )
        elif previous is None:
            context_boundary = "DOCUMENT_START"
        elif following is None:
            context_boundary = "DOCUMENT_END"
        else:
            context_boundary = "UNIT"

        atomic_fact_records: list[dict[str, Any]] = []
        for fact_index, fact_text in enumerate(atomic_facts, 1):
            fact_question_ids = _fact_question_ids(
                current_rows,
                source_unit_id,
                fact_index,
                len(atomic_facts),
            )
            if not support:
                fact_status = "AMBIGUOUS_SOURCE"
                fact_basis = "OCR_SUPPORT_MISSING"
            elif reference_only:
                fact_status = "REFERENCE_ONLY"
                fact_basis = "REFERENCE_ONLY_HEURISTIC"
            elif anaphoric_fragment:
                fact_status = "NON_ATOMIC"
                fact_basis = "ANAPHORIC_FRAGMENT_HEURISTIC"
            elif fact_question_ids:
                fact_status = "COVERED"
                fact_basis = "FACT_ID_SUFFIX_AND_SOURCE_UNIT"
            elif current_ids:
                fact_status = "COVERED_MERGED"
                fact_basis = "SOURCE_UNIT_ID_LINK_ONLY"
            else:
                fact_status = "NEEDS_QUESTION"
                fact_basis = "NO_CURRENT_SOURCE_UNIT_LINK"
            atomic_fact_records.append(
                {
                    "atomic_fact_id": f"{source_unit_id}-F{fact_index:02d}",
                    "parent_source_unit_id": source_unit_id,
                    "text": fact_text,
                    "is_atomic": not (reference_only or anaphoric_fragment),
                    "current_question_ids": fact_question_ids,
                    "coverage_status": fact_status,
                    "coverage_basis": fact_basis,
                    "coverage_scope": "ATOMIC_FACT",
                    "semantic_coverage_verified": False,
                }
            )

        if not support:
            status = "AMBIGUOUS_SOURCE"
            explanation = (
                f"La unidad tiene {len(current_ids)} presentación(es) actual(es), "
                "pero su cita no coincide completamente con el OCR verificado. "
                "Se conserva la cita canónica y no se corrige el OCR automáticamente. "
                + (issue or "Requiere revisión visual.")
            )
            coverage_basis = "OCR_SUPPORT_MISSING"
        elif reference_only:
            status = "REFERENCE_ONLY"
            explanation = (
                "El fragmento contiene únicamente referencias bíblicas, sin una "
                "proposición textual autosuficiente; no es un hueco de autoría. "
                "La clasificación es heurística y requiere revisión visual."
            )
            coverage_basis = "REFERENCE_ONLY_HEURISTIC"
        elif anaphoric_fragment:
            status = "NON_ATOMIC"
            explanation = (
                "El fragmento es anafórico y depende del contexto anterior; no se "
                "trata como unidad preguntable independiente. La clasificación "
                "es heurística y requiere revisión visual."
            )
            coverage_basis = "ANAPHORIC_FRAGMENT_HEURISTIC"
        elif len(atomic_facts) > 1:
            status = "COVERED_MERGED" if current_ids else "NON_ATOMIC"
            explanation = (
                f"La unidad padre contiene {len(atomic_facts)} hechos atómicos "
                "expuestos como hijos estables. Las presentaciones se enlazan al "
                "source_unit_id padre; ese enlace no constituye verificación "
                "semántica por hecho y requiere revisión visual."
            )
            coverage_basis = (
                "SOURCE_UNIT_ID_LINK_ONLY" if current_ids else "ATOMIC_SPLIT_HEURISTIC"
            )
        elif not current_ids:
            status = "NEEDS_QUESTION"
            explanation = (
                "Unidad textual autosuficiente sin preguntas actuales vinculadas "
                "mecánicamente por source_unit_id; requiere una pregunta nueva, "
                "sin inferir cobertura desde inventarios históricos."
            )
            coverage_basis = "NO_CURRENT_SOURCE_UNIT_LINK"
        else:
            status = "COVERED"
            explanation = (
                f"Unidad respaldada por la fuente verificada con {len(current_ids)} "
                "presentación(es) actual(es) vinculada(s) por source_unit_id. "
                "Es evidencia de enlace de fuente, no verificación semántica de "
                "la pregunta ni de cada distractor."
            )
            coverage_basis = "SOURCE_UNIT_ID_LINK_ONLY"

        visual_review_status = "REVIEW_REQUIRED" if review_flags else "NOT_REQUIRED"

        row: dict[str, Any] = {
            "source_unit_id": source_unit_id,
            "work": str(source.get("work")),
            "chapter": int(source.get("chapter")),
            "verse_or_page": _unit_reference(source),
            "pdf_page": page,
            "exact_quote": canonical_text,
            "nearby_context": nearby_context,
            "atomic_facts": atomic_facts,
            "atomic_fact_count": len(atomic_facts),
            "atomic_fact_records": atomic_fact_records,
            "current_question_ids": current_ids,
            "presentation_count": len(current_ids),
            "distinct_cognitive_operations": _operations(current_rows),
            "coverage_status": status,
            "coverage_basis": coverage_basis,
            "coverage_scope": "SOURCE_UNIT",
            "semantic_coverage_verified": False,
            "explanation": explanation,
            "historical_fact_ids": historical_ids,
            "historical_fact_count": len(historical_ids),
            "ocr_support": support,
            "ocr_issue": issue,
            "context_boundary": context_boundary,
            "review_flags": review_flags,
            "requires_visual_review": bool(review_flags),
            "visual_review_status": visual_review_status,
        }
        result.append(row)
    return result


def _chapter_key(unit: Mapping[str, Any]) -> str:
    if unit["work"] == "Daniel":
        return f"DAN{int(unit['chapter'])}"
    return f"PR{int(unit['chapter'])}"


def build_ledger(
    root: str | Path | None = None,
    *,
    pdf_path: str | Path | None = None,
    ocr_cache_path: str | Path | None = None,
    master_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build and validate the in-memory V18 ledger."""

    repository_root = _as_path(root or Path(__file__).resolve().parents[1]).resolve()
    pdf = _as_path(pdf_path or repository_root / "MaterialConexionBiblica (1).pdf")
    cache = _as_path(
        ocr_cache_path
        or repository_root / "scripts" / "source-cache" / "final-v7" / "ocr-pages.json"
    )
    master = _as_path(master_path or repository_root / "Banco_Maestro_CB2026.json")
    source_payload, pdf_page_count = load_verified_source(pdf, cache)
    pages = source_payload["pages"]
    source_units = _extract_source_units(pdf, pages)
    unresolved_source_inventory_issues = sum(
        len(unit.get("_source_inventory_issues") or []) for unit in source_units
    )
    unit_ids = {str(unit["source_unit_id"]) for unit in source_units}
    questions, by_current_unit, unmapped_question_ids = _load_current_questions(
        repository_root, unit_ids
    )
    master_meta, fact_records = _historical_fact_records(master)
    historical_by_unit, unmapped_historical_ids = _map_historical_facts(
        fact_records, source_units
    )
    master_meta["path"] = _stable_path(master, repository_root)
    units = _build_units(
        source_units,
        pages,
        by_current_unit,
        historical_by_unit,
    )

    status_counts = Counter(str(unit["coverage_status"]) for unit in units)
    atomic_status_counts = Counter(
        str(child["coverage_status"])
        for unit in units
        for child in unit["atomic_fact_records"]
    )
    units_by_id = {str(unit["source_unit_id"]): unit for unit in units}
    visual_flagged_unit_count = sum(
        bool(unit.get("requires_visual_review")) for unit in units
    )
    visual_reviewed_sample_count = len(VISUAL_REVIEWED_SAMPLES)
    visual_reviewed_flagged_sample_count = sum(
        bool(units_by_id.get(str(sample["source_unit_id"]), {}).get("requires_visual_review"))
        for sample in VISUAL_REVIEWED_SAMPLES
    )
    chapter_counts: dict[str, dict[str, int]] = {}
    for unit in units:
        chapter = _chapter_key(unit)
        bucket = chapter_counts.setdefault(
            chapter,
            {
                "source_units": 0,
                "covered": 0,
                "covered_merged": 0,
                "needs_question": 0,
                "reference_only": 0,
                "non_atomic": 0,
                "ambiguous": 0,
            },
        )
        bucket["source_units"] += 1
        if unit["coverage_status"] == "COVERED":
            bucket["covered"] += 1
        elif unit["coverage_status"] == "COVERED_MERGED":
            bucket["covered_merged"] += 1
        elif unit["coverage_status"] == "NEEDS_QUESTION":
            bucket["needs_question"] += 1
        elif unit["coverage_status"] == "REFERENCE_ONLY":
            bucket["reference_only"] += 1
        elif unit["coverage_status"] == "NON_ATOMIC":
            bucket["non_atomic"] += 1
        elif unit["coverage_status"] == "AMBIGUOUS_SOURCE":
            bucket["ambiguous"] += 1

    current_fact_ids = sorted(
        {
            str(row.get("fact_id"))
            for row in questions
            if row.get("fact_id")
        }
    )
    mapped_question_count = sum(len(rows) for rows in by_current_unit.values())
    historical_fact_ids = sorted(fact_records)
    historical_by_chapter = Counter()
    for fact_id in historical_fact_ids:
        match = re.match(r"FACT-(D\d+|PR\d+)-", fact_id)
        if match:
            historical_by_chapter[match.group(1)] += 1

    ledger: dict[str, Any] = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "source_file": pdf.name,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "pdf_page_count": pdf_page_count,
        "ocr_cache": {
            "path": _stable_path(cache, repository_root),
            "source_sha256": source_payload["source_sha256"],
            "cache_sha256": _sha256(cache),
            "page_count": len(pages),
            "pages": sorted(int(page) for page in pages),
        },
        "counts": {
            "source_units": len(units),
            "daniel_verses": sum(unit["work"] == "Daniel" for unit in units),
            "pr_propositions": sum(unit["work"] == "Profetas y Reyes" for unit in units),
            "covered_source_units": sum(
                unit["coverage_status"] in {"COVERED", "COVERED_MERGED"}
                for unit in units
            ),
            "needs_question": status_counts["NEEDS_QUESTION"],
            "ambiguous_source": status_counts["AMBIGUOUS_SOURCE"],
            "reference_only": status_counts["REFERENCE_ONLY"],
            "non_atomic": status_counts["NON_ATOMIC"],
            "covered_merged": status_counts["COVERED_MERGED"],
            "atomic_facts": sum(len(unit["atomic_facts"]) for unit in units),
            "atomic_facts_linked_by_fact_id": atomic_status_counts["COVERED"],
            "atomic_facts_linked_only_by_source_unit": atomic_status_counts[
                "COVERED_MERGED"
            ],
            "current_questions": len(questions),
            "current_fact_ids": len(current_fact_ids),
        },
        "coverage_status_counts": dict(sorted(status_counts.items())),
        "atomic_fact_status_counts": dict(sorted(atomic_status_counts.items())),
        "coverage_semantics": {
            "semantic_coverage_verified": False,
            "COVERED": "SOURCE_UNIT_ID_LINK_ONLY",
            "COVERED_MERGED": "SOURCE_UNIT_ID_LINK_ONLY_WITH_ATOMIC_CHILDREN",
            "fact_level_link": "FACT_ID_SUFFIX_AND_SOURCE_UNIT_WHEN_EXACT",
            "note": (
                "Ningún estado COVERED equivale a una auditoría semántica; "
                "los dictámenes de preguntas y distractores son un carril aparte."
            ),
        },
        "coverage_by_chapter": dict(sorted(chapter_counts.items())),
        "source_inventory_evidence": {
            "extractor": "scripts/lib/source_inventory.py",
            "segmentation_policy": (
                "STABLE_SOURCE_UNIT_IDS_WITH_PUNCTUATION_HEURISTIC; "
                "MULTI_FACT_CHILDREN_REQUIRE_VISUAL_REVIEW"
            ),
            "restoration_policy": "OCR_GLYPH_ONLY_UNRESOLVED_REMAINS_AMBIGUOUS",
            "unresolved_issue_count": unresolved_source_inventory_issues,
        },
        "comparison": {
            "current_bank": {
                "manifest": "public/banks/final-2026/manifest.json",
                "question_count": len(questions),
                "mapped_question_count": mapped_question_count,
                "unmapped_question_count": len(unmapped_question_ids),
                "mapped_source_unit_count": len(by_current_unit),
                "linked_source_unit_count": len(by_current_unit),
                "covered_source_units": sum(bool(rows) for rows in by_current_unit.values()),
                "semantic_coverage_verified_source_unit_count": sum(
                    bool(rows) and bool(unit.get("semantic_coverage_verified"))
                    for unit in units
                    for rows in [by_current_unit.get(str(unit["source_unit_id"]), [])]
                ),
                "uncovered_source_unit_count": sum(
                    not bool(by_current_unit.get(source_unit_id))
                    for source_unit_id in unit_ids
                ),
                "fact_id_count": len(current_fact_ids),
                "unmapped_question_ids": unmapped_question_ids,
                "by_chapter": dict(
                    sorted(
                        Counter(
                            str(row.get("chapter"))
                            for row in questions
                            if row.get("chapter")
                        ).items()
                    )
                ),
            },
            "historical_master": {
                **master_meta,
                "fact_count": len(historical_fact_ids),
                "fact_id_count": len(historical_fact_ids),
                "daniel_fact_count": sum(
                    fact_id.startswith("FACT-D") for fact_id in historical_fact_ids
                ),
                "pr_fact_count": sum(
                    fact_id.startswith("FACT-PR") for fact_id in historical_fact_ids
                ),
                "mapped_fact_count": sum(len(ids) for ids in historical_by_unit.values()),
                "unmapped_fact_count": len(unmapped_historical_ids),
                "unmapped_fact_ids": unmapped_historical_ids,
                "by_chapter": dict(sorted(historical_by_chapter.items())),
                "comparison_note": (
                    "El conteo se deriva de IDs únicos FULL/PARTIAL/INCIDENTAL; no se "
                    "asume que el inventario histórico sea exhaustivo ni se usa para "
                    "declarar cobertura del PDF."
                ),
            },
        },
        "visual_review": {
            "status": "PARTIAL",
            "method": (
                "Se inspeccionaron visualmente las páginas PDF declaradas en "
                "reviewed_pdf_pages; el resto de clasificaciones heurísticas "
                "conserva un flag REVIEW_REQUIRED."
            ),
            "reviewed_pdf_pages": VISUAL_REVIEWED_PDF_PAGES,
            "reviewed_samples": VISUAL_REVIEWED_SAMPLES,
            "total_sample_count": visual_reviewed_sample_count,
            "reviewed_flagged_sample_count": visual_reviewed_flagged_sample_count,
            "flagged_unit_count": visual_flagged_unit_count,
            "unreviewed_flagged_unit_count": max(
                0,
                visual_flagged_unit_count - visual_reviewed_flagged_sample_count,
            ),
        },
        "units": units,
    }
    validate_ledger(ledger)
    return ledger


def validate_ledger(ledger: Mapping[str, Any]) -> None:
    """Raise a useful error for malformed ledger artifacts."""

    errors: list[str] = []
    if ledger.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        errors.append("source_sha256")
    if ledger.get("pdf_page_count") != 60:
        errors.append("pdf_page_count")
    units = ledger.get("units")
    if not isinstance(units, list):
        errors.append("units_not_list")
        units = []
    seen: set[str] = set()
    seen_atomic_fact_ids: set[str] = set()
    for index, unit in enumerate(units):
        if not isinstance(unit, Mapping):
            errors.append(f"unit_{index}_not_object")
            continue
        source_unit_id = unit.get("source_unit_id")
        if not source_unit_id or source_unit_id in seen:
            errors.append(f"unit_{index}_duplicate_or_missing_id")
        seen.add(str(source_unit_id))
        if unit.get("coverage_status") not in ALLOWED_COVERAGE:
            errors.append(f"unit_{source_unit_id}_invalid_status")
        if not isinstance(unit.get("pdf_page"), int) or unit["pdf_page"] < 1:
            errors.append(f"unit_{source_unit_id}_invalid_page")
        if not isinstance(unit.get("exact_quote"), str) or not unit["exact_quote"].strip():
            errors.append(f"unit_{source_unit_id}_missing_quote")
        if unit.get("presentation_count") != len(unit.get("current_question_ids", [])):
            errors.append(f"unit_{source_unit_id}_presentation_count")
        current_question_ids = unit.get("current_question_ids")
        if (
            not isinstance(current_question_ids, list)
            or any(not isinstance(question_id, str) or not question_id for question_id in current_question_ids)
            or len(set(current_question_ids)) != len(current_question_ids)
        ):
            errors.append(f"unit_{source_unit_id}_current_question_ids")
        atomic_facts = unit.get("atomic_facts")
        atomic_records = unit.get("atomic_fact_records")
        if not isinstance(atomic_facts, list) or not atomic_facts:
            errors.append(f"unit_{source_unit_id}_missing_atomic_facts")
        if not isinstance(atomic_records, list) or len(atomic_records) != len(atomic_facts or []):
            errors.append(f"unit_{source_unit_id}_atomic_record_count")
        if unit.get("atomic_fact_count") != len(atomic_facts or []):
            errors.append(f"unit_{source_unit_id}_atomic_fact_count")
        if isinstance(atomic_facts, list) and isinstance(atomic_records, list):
            record_texts = [child.get("text") if isinstance(child, Mapping) else None for child in atomic_records]
            if atomic_facts != record_texts:
                errors.append(f"unit_{source_unit_id}_atomic_fact_texts")
            child_statuses = [
                child.get("coverage_status")
                for child in atomic_records
                if isinstance(child, Mapping)
            ]
            if child_statuses and all(status == "AMBIGUOUS_SOURCE" for status in child_statuses):
                expected_parent_status = "AMBIGUOUS_SOURCE"
            elif child_statuses and all(status == "REFERENCE_ONLY" for status in child_statuses):
                expected_parent_status = "REFERENCE_ONLY"
            elif child_statuses and all(status == "NON_ATOMIC" for status in child_statuses):
                expected_parent_status = "NON_ATOMIC"
            elif len(atomic_facts) > 1:
                expected_parent_status = "COVERED_MERGED" if current_question_ids else "NON_ATOMIC"
            else:
                expected_parent_status = "COVERED" if current_question_ids else "NEEDS_QUESTION"
            if unit.get("coverage_status") != expected_parent_status:
                errors.append(f"unit_{source_unit_id}_parent_status")
            allowed_child_statuses = {
                "AMBIGUOUS_SOURCE": {"AMBIGUOUS_SOURCE"},
                "REFERENCE_ONLY": {"REFERENCE_ONLY"},
                "COVERED": {"COVERED"},
                "COVERED_MERGED": {"COVERED", "COVERED_MERGED"},
                "NEEDS_QUESTION": {"NEEDS_QUESTION"},
                "NON_ATOMIC": {"NEEDS_QUESTION"} if len(atomic_facts) > 1 else {"NON_ATOMIC"},
            }[expected_parent_status]
            if any(status not in allowed_child_statuses for status in child_statuses):
                errors.append(f"unit_{source_unit_id}_mixed_child_status")
            expected_parent_basis = {
                "AMBIGUOUS_SOURCE": "OCR_SUPPORT_MISSING",
                "REFERENCE_ONLY": "REFERENCE_ONLY_HEURISTIC",
                "COVERED": "SOURCE_UNIT_ID_LINK_ONLY",
                "COVERED_MERGED": "SOURCE_UNIT_ID_LINK_ONLY",
                "NEEDS_QUESTION": "NO_CURRENT_SOURCE_UNIT_LINK",
                "NON_ATOMIC": (
                    "ATOMIC_SPLIT_HEURISTIC"
                    if len(atomic_facts) > 1
                    else "ANAPHORIC_FRAGMENT_HEURISTIC"
                ),
            }[expected_parent_status]
            if unit.get("coverage_basis") != expected_parent_basis:
                errors.append(f"unit_{source_unit_id}_parent_coverage_basis")
        if unit.get("coverage_basis") not in {
            "SOURCE_UNIT_ID_LINK_ONLY",
            "OCR_SUPPORT_MISSING",
            "REFERENCE_ONLY_HEURISTIC",
            "ANAPHORIC_FRAGMENT_HEURISTIC",
            "ATOMIC_SPLIT_HEURISTIC",
            "NO_CURRENT_SOURCE_UNIT_LINK",
        }:
            errors.append(f"unit_{source_unit_id}_invalid_coverage_basis")
        if unit.get("coverage_scope") != "SOURCE_UNIT":
            errors.append(f"unit_{source_unit_id}_invalid_coverage_scope")
        if unit.get("semantic_coverage_verified") is not False:
            errors.append(f"unit_{source_unit_id}_semantic_flag")
        if not isinstance(unit.get("review_flags"), list):
            errors.append(f"unit_{source_unit_id}_review_flags")
        if not isinstance(unit.get("requires_visual_review"), bool):
            errors.append(f"unit_{source_unit_id}_visual_review_flag")
        if not isinstance(unit.get("context_boundary"), str):
            errors.append(f"unit_{source_unit_id}_context_boundary")
        previous_position = -1
        for child_index, child in enumerate(atomic_records if isinstance(atomic_records, list) else [], start=1):
            if not isinstance(child, Mapping):
                errors.append(f"unit_{source_unit_id}_atomic_record_object")
                continue
            if child.get("coverage_status") not in ALLOWED_COVERAGE:
                errors.append(f"unit_{source_unit_id}_atomic_invalid_status")
            child_question_ids = child.get("current_question_ids")
            if (
                not isinstance(child_question_ids, list)
                or any(not isinstance(question_id, str) or not question_id for question_id in child_question_ids)
                or len(set(child_question_ids)) != len(child_question_ids)
                or any(question_id not in set(current_question_ids or []) for question_id in child_question_ids)
            ):
                errors.append(f"unit_{source_unit_id}_atomic_question_ids")
                child_question_ids = []
            child_status = child.get("coverage_status")
            expected_child_basis = {
                "AMBIGUOUS_SOURCE": "OCR_SUPPORT_MISSING",
                "REFERENCE_ONLY": "REFERENCE_ONLY_HEURISTIC",
                "NON_ATOMIC": "ANAPHORIC_FRAGMENT_HEURISTIC",
                "COVERED": "FACT_ID_SUFFIX_AND_SOURCE_UNIT",
                "COVERED_MERGED": "SOURCE_UNIT_ID_LINK_ONLY",
                "NEEDS_QUESTION": "NO_CURRENT_SOURCE_UNIT_LINK",
            }.get(child_status)
            if child.get("coverage_basis") != expected_child_basis:
                errors.append(f"unit_{source_unit_id}_atomic_coverage_basis")
            if child_status == "COVERED" and not child_question_ids:
                errors.append(f"unit_{source_unit_id}_covered_without_link")
            if child_status == "COVERED_MERGED" and (child_question_ids or not current_question_ids):
                errors.append(f"unit_{source_unit_id}_merged_link_invariant")
            if child_status == "NEEDS_QUESTION" and (child_question_ids or current_question_ids):
                errors.append(f"unit_{source_unit_id}_needs_question_link_invariant")
            atomic_fact_id = str(child.get("atomic_fact_id") or "")
            if atomic_fact_id in seen_atomic_fact_ids and atomic_fact_id:
                errors.append(f"unit_{source_unit_id}_atomic_fact_id_duplicate")
            if atomic_fact_id:
                seen_atomic_fact_ids.add(atomic_fact_id)
            if not atomic_fact_id:
                errors.append(f"unit_{source_unit_id}_atomic_missing_identity")
            elif atomic_fact_id != f"{source_unit_id}-F{child_index:02d}":
                errors.append(f"unit_{source_unit_id}_atomic_identity_sequence")
            child_text = child.get("text")
            if not isinstance(child_text, str) or not child_text.strip():
                errors.append(f"unit_{source_unit_id}_atomic_text_empty")
            elif _normalise_for_match(child_text) not in _normalise_for_match(
                str(unit.get("exact_quote") or "")
            ):
                errors.append(f"unit_{source_unit_id}_atomic_text_not_in_quote")
            else:
                normalized_quote = _normalise_for_match(str(unit.get("exact_quote") or ""))
                normalized_child = _normalise_for_match(child_text)
                position = normalized_quote.find(normalized_child, previous_position + 1)
                if position < 0:
                    errors.append(f"unit_{source_unit_id}_atomic_text_order")
                else:
                    previous_position = position
                if len(_split_atomic_facts({"full_text": child_text})) != 1:
                    errors.append(f"unit_{source_unit_id}_atomic_text_splittable")
            if child.get("parent_source_unit_id") != source_unit_id:
                errors.append(f"unit_{source_unit_id}_atomic_parent")
            if child.get("coverage_scope") != "ATOMIC_FACT":
                errors.append(f"unit_{source_unit_id}_atomic_scope")
            if not isinstance(child.get("is_atomic"), bool):
                errors.append(f"unit_{source_unit_id}_atomic_flag")
            elif child["is_atomic"] != (child_status not in {"REFERENCE_ONLY", "NON_ATOMIC"}):
                errors.append(f"unit_{source_unit_id}_atomic_flag_value")
            if child.get("semantic_coverage_verified") is not False:
                errors.append(f"unit_{source_unit_id}_atomic_semantic_flag")
    coverage_semantics = ledger.get("coverage_semantics")
    if not isinstance(coverage_semantics, Mapping):
        errors.append("coverage_semantics_missing")
    elif coverage_semantics.get("semantic_coverage_verified") is not False:
        errors.append("coverage_semantics_must_be_false")
    visual_review = ledger.get("visual_review")
    if not isinstance(visual_review, Mapping):
        errors.append("visual_review_missing")
    elif visual_review.get("status") != "PARTIAL":
        errors.append("visual_review_status")
    elif (
        visual_review.get("total_sample_count")
        != len(visual_review.get("reviewed_samples") or [])
    ):
        errors.append("visual_review_sample_count")
    elif (
        not isinstance(visual_review.get("flagged_unit_count"), int)
        or not isinstance(visual_review.get("reviewed_flagged_sample_count"), int)
        or visual_review.get("unreviewed_flagged_unit_count")
        != visual_review.get("flagged_unit_count")
        - visual_review.get("reviewed_flagged_sample_count")
    ):
        errors.append("visual_review_flagged_count")
    source_evidence = ledger.get("source_inventory_evidence")
    if not isinstance(source_evidence, Mapping):
        errors.append("source_inventory_evidence_missing")
    if errors:
        raise ValueError("Ledger inválido: " + ", ".join(errors[:20]))


def _csv_value(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return ""
    return str(value)


def _md_cell(value: Any) -> str:
    text = _csv_value(value).replace("\n", " ").replace("|", "\\|")
    return text


def write_outputs(ledger: Mapping[str, Any], output_dir: str | Path) -> tuple[Path, Path, Path]:
    destination = _as_path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "source-ledger.json"
    csv_path = destination / "source-ledger.csv"
    md_path = destination / "source-ledger.md"

    json_path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for unit in ledger["units"]:
            writer.writerow({column: _csv_value(unit.get(column)) for column in CSV_COLUMNS})

    lines = [
        "# Source ledger V18",
        "",
        "Ledger canónico de unidades textuales construido desde la caché OCR "
        "verificada contra el PDF oficial.",
        "",
        "> `COVERED` y `COVERED_MERGED` indican un enlace mecánico por "
        "`source_unit_id`; no son un dictamen semántico Sol ni validan "
        "respuestas/distractores.",
        "",
        f"- Fuente: `{ledger['source_file']}`",
        f"- SHA-256: `{ledger['source_sha256']}`",
        f"- Páginas PDF: **{ledger['pdf_page_count']}**",
        f"- Unidades: **{ledger['counts']['source_units']}** "
        f"({ledger['counts']['daniel_verses']} Daniel; "
        f"{ledger['counts']['pr_propositions']} Profetas y Reyes)",
        "",
        "## Counts",
        "",
        "| Estado | Unidades |",
        "| --- | ---: |",
    ]
    for status, count in sorted(ledger["coverage_status_counts"].items()):
        lines.append(f"| {status} | {count} |")
    lines.extend(
        [
            "",
            "## Comparación mecánica",
            "",
            f"- Banco actual: {ledger['comparison']['current_bank']['question_count']} "
            f"preguntas; {ledger['comparison']['current_bank']['mapped_question_count']} "
            f"mapeadas y {ledger['comparison']['current_bank']['unmapped_question_count']} "
            "sin source_unit_id utilizable.",
            f"- Unidades con enlace actual: {ledger['comparison']['current_bank']['linked_source_unit_count']}; "
            f"unidades con verificación semántica registrada: "
            f"{ledger['comparison']['current_bank']['semantic_coverage_verified_source_unit_count']}.",
            f"- Banco Maestro: {ledger['comparison']['historical_master']['fact_count']} "
            "IDs FACT únicos derivados; los no mapeables se conservan en el reporte.",
            f"- Revisión visual: estado **{ledger['visual_review']['status']}**; "
            f"páginas inspeccionadas: {', '.join(map(str, ledger['visual_review']['reviewed_pdf_pages']))}; "
            f"unidades con flags aún no revisadas: "
            f"{ledger['visual_review']['unreviewed_flagged_unit_count']}.",
            "",
            "## Units",
            "",
            "| ID | Obra | Capítulo | Página PDF | Presentaciones | Estado | Revisión | Cita |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for unit in ledger["units"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(unit["source_unit_id"]),
                    _md_cell(unit["work"]),
                    _md_cell(unit["chapter"]),
                    _md_cell(unit["pdf_page"]),
                    _md_cell(unit["presentation_count"]),
                    _md_cell(unit["coverage_status"]),
                    _md_cell(unit["visual_review_status"]),
                    _md_cell(unit["exact_quote"]),
                ]
            )
            + " |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, csv_path, md_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Construye el ledger de fuente V18")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--ocr-cache", type=Path)
    parser.add_argument("--master", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        ledger = build_ledger(
            args.root,
            pdf_path=args.pdf,
            ocr_cache_path=args.ocr_cache,
            master_path=args.master,
        )
        output_dir = args.output_dir or args.root / "content" / "final-day-v18"
        paths = write_outputs(ledger, output_dir)
    except (FileNotFoundError, RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    summary = {
        "source_units": ledger["counts"]["source_units"],
        "coverage_status_counts": ledger["coverage_status_counts"],
        "current_questions": ledger["comparison"]["current_bank"]["question_count"],
        "historical_fact_ids": ledger["comparison"]["historical_master"]["fact_id_count"],
        "outputs": [str(path) for path in paths],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
