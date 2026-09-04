"""Prepara dosieres editoriales V18 y pares ciegos sin resolver preguntas.

El preparador solo transforma preguntas existentes y unidades de fuente. No
transporta la respuesta almacenada ni metadata de revisiones anteriores. La
localización de página se acepta únicamente cuando está explícita en la fuente
o puede localizarse de forma reproducible en el OCR canónico.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Iterator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUESTION_DIR = ROOT / "public" / "banks" / "final-2026" / "questions"
DEFAULT_SOURCE_DIR = ROOT / "content" / "competitive-v11" / "source-packets"
DEFAULT_OCR_PATH = ROOT / "scripts" / "source-cache" / "final-v7" / "ocr-pages.json"
DEFAULT_DOSSIER_DIR = ROOT / ".work" / "final-day-v18" / "dossiers"
DEFAULT_BLIND_DIR = ROOT / ".work" / "final-day-v18" / "blind"
DEFAULT_AUDIT_RUN_ID = "v18-priority-audit"
EXPECTED_SOURCE_SHA256 = (
    "0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3"
)

PRIORITY_ORDER = (
    *(f"PR{chapter}" for chapter in range(39, 45)),
    *(f"DAN{chapter}" for chapter in range(7, 13)),
    *(f"DAN{chapter}" for chapter in range(1, 7)),
)
PRIORITY_RANK = {chapter: index for index, chapter in enumerate(PRIORITY_ORDER)}

SAFE_FIRST_RUN_ID = "v18-safe-first"
SAFE_FIRST_PR_DELIMITER = "Según Profetas y Reyes"
SAFE_FIRST_PRIORITY_ORDER = (
    *(f"PR{chapter}" for chapter in range(39, 45)),
    "DAN9",
    "DAN12",
    "DAN7",
    "DAN8",
    "DAN10",
    "DAN11",
)
SAFE_FIRST_PRIORITY_RANK = {
    chapter: index for index, chapter in enumerate(SAFE_FIRST_PRIORITY_ORDER)
}

# These are the explicit personal-zone terms from the V18 specification. They
# are used only as deterministic source/question text markers; no answer,
# difficulty, or review metadata participates in selection.
PERSONAL_ZONE_MARKERS: dict[str, tuple[str, ...]] = {
    "DAN7": (
        "Anciano de días",
        "hijo de hombre",
        "dominio",
        "gloria y reino",
        "cuatro bestias",
        "cuernos",
        "juicio",
    ),
    "DAN8": (
        "Susa",
        "río Ulai",
        "carnero",
        "macho cabrío",
        "Media y Persia",
        "Grecia",
        "Gabriel",
    ),
    "DAN9": (
        "setenta años",
        "setenta semanas",
        "siete semanas",
        "sesenta y dos semanas",
        "reconstrucción",
        "Mesías Príncipe",
        "después de las sesenta y dos semanas",
        "pacto",
        "ciudad y santuario",
    ),
    "DAN10": (
        "tercer año de Ciro",
        "tres semanas",
        "Hidekel",
        "príncipe de Persia",
        "veintiún días",
        "Miguel",
        "varón vestido de lino",
    ),
    "DAN11": (
        "norte y sur",
        "secuencias",
        "santuario",
        "abominación desoladora",
        "lisonjas",
        "dios de las fortalezas",
        "monte glorioso",
        "direcciones y orden",
    ),
    "DAN12": (
        "Miguel, el gran príncipe",
        "Miguel",
        "tiempo de angustia",
        "resurrección",
        "sellar el libro",
        "1,290",
        "1,335",
        "heredad de Daniel",
    ),
}

DOSSIER_ITEM_FIELDS = frozenset(
    {
        "audit_run_id",
        "question_id",
        "question",
        "options",
        "source_unit_id",
        "source_ref",
        "pdf_page",
        "exact_quote",
        "nearby_context",
        "material",
        "chapter",
    }
)
BLIND_ITEM_FIELDS = frozenset(
    {"audit_run_id", "question_id", "question", "options"}
)

# Estos nombres cubren respuestas, resultados y metadata de calidad que no
# deben cruzar la frontera hacia un dossier V18. Los items emitidos se
# construyen por selección explícita, de modo que esta lista también sirve a
# los validadores y a los consumidores posteriores.
PROHIBITED_FIELDS = frozenset(
    {
        "correct_option",
        "correct_answer",
        "accepted_answers",
        "answer",
        "selected_option_index",
        "selected_option_text",
        "blind_result",
        "blind_results",
        "stage_a_result",
        "stage_b_result",
        "decision",
        "tier",
        "difficulty",
        "recommendation",
        "results",
        "review",
        "reviews",
        "ai_review",
        "validation_adversarial",
        "final_editorial_status",
        "explanation",
        "why_distractors_fail",
        "fact_id",
        "variant_id",
    }
)

_PAGE_IN_REFERENCE = re.compile(r"\bp\.\s*(\d+)", re.IGNORECASE)
_CHAPTER_FROM_SOURCE_ID = re.compile(r"^(PR|DAN)(\d+)(?:[-_]|$)", re.IGNORECASE)
_TEXT_TOKEN = re.compile(r"[\w]+", re.UNICODE)


def _canonical_bytes(value: Any) -> bytes:
    """Return bytes stable across processes and filesystem locations."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _atomic_write_json(path: Path, value: Any) -> None:
    _validate_generated_payload(path, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(
        json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    )
    os.replace(temporary, path)


def _validate_generated_payload(path: Path, value: Any) -> None:
    """Reject malformed generated payloads before their temporary file is published."""

    if not isinstance(value, dict):
        raise ValueError(f"payload no es un objeto: {path.name}")
    name = path.name
    schema = value.get("schema_version")
    if name.startswith("batch-"):
        if schema not in {
            "final-day-v18-audit-dossier-1.0",
            "final-day-v18-blind-pair-1.0",
        }:
            raise ValueError(f"schema de batch inválido: {path.name}")
        if not _nonempty_string(value.get("audit_run_id")):
            raise ValueError(f"batch sin audit_run_id: {path.name}")
        if not _nonempty_string(value.get("batch_id")):
            raise ValueError(f"batch sin batch_id: {path.name}")
        items = value.get("items")
        expected = BLIND_ITEM_FIELDS if schema.endswith("blind-pair-1.0") else DOSSIER_ITEM_FIELDS
        if not isinstance(items, list) or any(not _valid_item(item, expected) for item in items):
            raise ValueError(f"items de batch inválidos: {path.name}")
    elif name == "invalid-items.json":
        if schema != "final-day-v18-invalid-items-1.0":
            raise ValueError("schema de invalid-items inválido")
        if (
            not _nonempty_string(value.get("audit_run_id"))
            or not isinstance(value.get("items"), list)
            or any(not _valid_invalid_item(item) for item in value["items"])
        ):
            raise ValueError("invalid-items incompleto")
    elif name == "manifest.json":
        if schema != "final-day-v18-dossier-manifest-1.0":
            raise ValueError("schema de manifest inválido")
        required = {
            "audit_run_id",
            "selection_mode",
            "priority_order",
            "batch_min",
            "batch_max",
            "selected_count",
            "valid_count",
            "batched_count",
            "batch_count",
            "batch_sizes",
            "input_question_count",
            "excluded_count",
            "selected_invalid_count",
            "invalid_count",
            "out_of_batch_count",
            "outside_priority_count",
            "question_errors",
            "source_errors",
            "source_sha256",
            "ocr_path",
            "ocr_status",
            "ocr_source_sha256",
            "batches",
            "blind_batches",
            "invalid_items_file",
            "invalid_items_sha256",
        }
        if not required.issubset(value) or not _nonempty_string(value.get("audit_run_id")):
            raise ValueError("manifest incompleto")


def _staging_run_dirs(
    dossier_parent: Path,
    blind_parent: Path,
    run_id: str,
) -> tuple[Path, Path, Path, Path]:
    """Create hidden staging directories and return (staged, targets) in pairs."""

    dossier_parent.mkdir(parents=True, exist_ok=True)
    blind_parent.mkdir(parents=True, exist_ok=True)
    dossier_target = dossier_parent / run_id
    blind_target = blind_parent / run_id
    dossier_stage = Path(
        tempfile.mkdtemp(prefix=f".{run_id}.staging-", dir=str(dossier_parent))
    )
    try:
        blind_stage = Path(
            tempfile.mkdtemp(prefix=f".{run_id}.staging-", dir=str(blind_parent))
        )
    except Exception:
        shutil.rmtree(dossier_stage, ignore_errors=True)
        raise
    return dossier_stage, blind_stage, dossier_target, blind_target


def _empty_sibling_path(parent: Path, prefix: str) -> Path:
    temporary = Path(tempfile.mkdtemp(prefix=prefix, dir=str(parent)))
    temporary.rmdir()
    return temporary


def _publish_staged_pair(
    dossier_stage: Path,
    blind_stage: Path,
    dossier_target: Path,
    blind_target: Path,
) -> None:
    """Publish a validated pair behind a transaction marker.

    The two directory renames cannot be one filesystem syscall.  Every V18
    consumer treats the marker as a hard failure, so no supported reader can
    observe or compile the intermediate half-published state.
    """

    pairs = (
        (dossier_stage, dossier_target),
        (blind_stage, blind_target),
    )
    backups: list[tuple[Path, Path | None]] = []
    published: list[Path] = []
    common_parent = Path(os.path.commonpath([dossier_target.parent, blind_target.parent]))
    marker = common_parent / f".{dossier_target.name}.publishing"
    marker.write_text("V18_PAIR_PUBLICATION_IN_PROGRESS\n", encoding="utf-8")
    try:
        for stage, target in pairs:
            if target.exists():
                backup = _empty_sibling_path(target.parent, f".{target.name}.backup-")
                os.replace(target, backup)
                backups.append((target, backup))
            else:
                backups.append((target, None))
        for stage, target in pairs:
            os.replace(stage, target)
            published.append(target)
    except Exception:
        for target in reversed(published):
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
        for target, backup in reversed(backups):
            if backup is not None and backup.exists():
                os.replace(backup, target)
        raise
    finally:
        for _, backup in backups:
            if backup is not None and backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
        for stage, _ in pairs:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
        marker.unlink(missing_ok=True)


def _nonempty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if not value.strip():
        return None
    return value


def _valid_invalid_item(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    if set(item) - {"status", "reason", "question_id"}:
        return False
    if item.get("status") not in {"INVALID_OUTPUT", "OUT_OF_BATCH", "EXCLUDED"}:
        return False
    if _nonempty_string(item.get("reason")) is None:
        return False
    question_id = item.get("question_id")
    return question_id is None or _nonempty_string(question_id) is not None


def _positive_page(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        page = int(value.strip())
        return page if page > 0 else None
    return None


def _normalise_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.split())


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows_from_payload(payload: Any, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    return []


def _load_question_records(question_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in sorted(question_dir.glob("*.json"), key=lambda item: item.name):
        try:
            payload = _load_json(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: no se pudo leer JSON ({exc})")
            continue
        rows = _rows_from_payload(payload, ("questions", "items"))
        if not rows and payload not in ([], {}):
            errors.append(f"{path.name}: no contiene una lista de preguntas")
            continue
        for index, row in enumerate(rows):
            if isinstance(row, dict):
                records.append(
                    {
                        "row": row,
                        "file": path.name,
                        "index": index,
                    }
                )
            else:
                errors.append(f"{path.name}[{index}]: la pregunta no es un objeto")
    return records, errors


def _load_source_units(source_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    units: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []
    for path in sorted(source_dir.glob("*.json"), key=lambda item: item.name):
        if path.name.lower() in {"excluded-units.json", "manifest.json"}:
            continue
        try:
            payload = _load_json(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: no se pudo leer JSON ({exc})")
            continue
        declared_hash = payload.get("source_sha256") if isinstance(payload, dict) else None
        if declared_hash != EXPECTED_SOURCE_SHA256:
            errors.append(
                f"{path.name}: source_sha256 ausente o no coincide con la fuente canónica"
            )
            continue
        rows = _rows_from_payload(payload, ("units", "source_units", "items"))
        if not rows and payload not in ([], {}):
            errors.append(f"{path.name}: no contiene unidades de fuente")
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{path.name}[{index}]: la unidad no es un objeto")
                continue
            source_id = _nonempty_string(row.get("source_unit_id"))
            if source_id is None:
                errors.append(f"{path.name}[{index}]: falta source_unit_id")
                continue
            units.setdefault(source_id, []).append(row)
    return units, errors


def _load_ocr_pages_with_status(
    ocr_path: Path | None,
) -> tuple[dict[int, str], dict[str, Any]]:
    trace: dict[str, Any] = {
        "ocr_path": str(Path(ocr_path).resolve()) if ocr_path is not None else None,
        "ocr_status": "NOT_REQUESTED" if ocr_path is None else "MISSING",
        "ocr_source_sha256": None,
    }
    if ocr_path is None or not ocr_path.exists():
        return {}, trace
    try:
        payload = _load_json(ocr_path)
    except (OSError, ValueError):
        trace["ocr_status"] = "INVALID_JSON"
        return {}, trace
    if not isinstance(payload, dict):
        trace["ocr_status"] = "INVALID_SCHEMA"
        return {}, trace
    declared_hash = payload.get("source_sha256")
    trace["ocr_source_sha256"] = declared_hash
    if declared_hash != EXPECTED_SOURCE_SHA256:
        trace["ocr_status"] = "INVALID_HASH"
        return {}, trace
    pages = payload.get("pages")
    if not isinstance(pages, dict):
        trace["ocr_status"] = "INVALID_SCHEMA"
        return {}, trace
    loaded: dict[int, str] = {}
    for raw_page, text in pages.items():
        page = _positive_page(raw_page)
        if page is None or not isinstance(text, str) or not text.strip():
            trace["ocr_status"] = "INVALID_SCHEMA"
            return {}, trace
        loaded[page] = _normalise_text(text)
    if not loaded:
        trace["ocr_status"] = "INVALID_SCHEMA"
        return {}, trace
    trace["ocr_status"] = "VALID"
    return loaded, trace


def _load_ocr_pages(ocr_path: Path | None) -> dict[int, str]:
    return _load_ocr_pages_with_status(ocr_path)[0]


def _matching_pages(needle: Any, pages: dict[int, str]) -> set[int]:
    if not isinstance(needle, str) or not needle.strip():
        return set()
    normalized = _normalise_text(needle)
    return {page for page, text in pages.items() if normalized in text}


def _text_tokens(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    ).lower()
    return _TEXT_TOKEN.findall(normalized)


def _tokens_match(source_token: str, page_token: str) -> bool:
    if source_token == page_token:
        return True
    if not page_token.endswith(source_token):
        return False
    prefix = page_token[: -len(source_token)]
    # OCR in this source inserts a quote marker or a page/verse glyph into
    # the first token (for example ``irey`` or ``13clamaba``). Accept only a
    # very short, visibly non-editorial prefix; words with genuine prefixes
    # such as ``desde`` do not pass this condition.
    return len(prefix) <= 2 and (
        prefix.isdigit() or all(character in "hie" for character in prefix)
    )


def _fuzzy_quote_page(source_quote: Any, pages: dict[int, str]) -> int | None:
    """Find the page where the source quote starts despite OCR punctuation.

    The score is the longest contiguous prefix of source-quote tokens found in
    a page. Requiring a unique best prefix prevents choosing a page merely
    because it contains a few common words, while still handling OCR quote
    marks, line breaks and a source unit that continues onto the next page.
    """

    quote_tokens = _text_tokens(source_quote)
    if len(quote_tokens) < 3:
        return None
    scored: list[tuple[int, int]] = []
    for page, text in pages.items():
        page_tokens = _text_tokens(text)
        best = 0
        for start, token in enumerate(page_tokens):
            if not _tokens_match(quote_tokens[0], token):
                continue
            length = 0
            while (
                length < len(quote_tokens)
                and start + length < len(page_tokens)
                and _tokens_match(quote_tokens[length], page_tokens[start + length])
            ):
                length += 1
            best = max(best, length)
        if best:
            scored.append((best, page))
    if not scored:
        return None
    highest = max(score for score, _ in scored)
    # A complete quote is strong evidence. For a quote spanning pages, a
    # majority prefix still identifies its start page without guessing from a
    # chapter-to-page table.
    threshold = max(3, min(8, (len(quote_tokens) + 1) // 2))
    winners = [page for score, page in scored if score == highest and score >= threshold]
    return winners[0] if len(winners) == 1 else None


def _reference_page(source_ref: str | None) -> int | None:
    if source_ref is None:
        return None
    match = _PAGE_IN_REFERENCE.search(source_ref)
    return _positive_page(match.group(1)) if match else None


def _resolve_pdf_page(source: dict[str, Any], ocr_pages: dict[int, str]) -> int | None:
    """Resolve a page only from explicit metadata or reproducible text hits."""

    for field in ("pdf_page", "pdf_page_number", "source_page", "page"):
        page = _positive_page(source.get(field))
        if page is not None:
            return page

    source_ref = _nonempty_string(source.get("source_ref"))
    reference_page = _reference_page(source_ref)
    exact_pages = _matching_pages(source.get("source_quote"), ocr_pages)
    if len(exact_pages) == 1:
        page = next(iter(exact_pages))
        if reference_page is None or page == reference_page:
            return page

    context_pages: set[int] = set()
    for field in ("context_before", "context_after"):
        context_pages.update(_matching_pages(source.get(field), ocr_pages))
    if reference_page is not None and reference_page in context_pages:
        return reference_page
    if len(context_pages) == 1:
        return next(iter(context_pages))

    fuzzy_page = _fuzzy_quote_page(source.get("source_quote"), ocr_pages)
    if fuzzy_page is not None and (reference_page is None or fuzzy_page == reference_page):
        return fuzzy_page

    # A printed page in a Profetas y Reyes reference is explicit source
    # metadata. If OCR is unavailable, preserve that explicit locator; no page
    # is invented for Daniel references, which do not carry one.
    if reference_page is not None and not ocr_pages:
        return reference_page
    return None


def _nearby_context(source: dict[str, Any]) -> str | None:
    pieces = [
        value
        for field in ("context_before", "context_after")
        if (value := _nonempty_string(source.get(field))) is not None
    ]
    if not pieces:
        parent = _nonempty_string(source.get("parent_context"))
        return parent
    return "\n".join(pieces)


def _chapter_code(row: dict[str, Any], source_id: str | None, file_name: str) -> str | int | None:
    chapter = row.get("chapter")
    if isinstance(chapter, str) and chapter.strip():
        return chapter
    if isinstance(chapter, int) and chapter > 0:
        return chapter
    if source_id is not None:
        match = _CHAPTER_FROM_SOURCE_ID.match(source_id)
        if match:
            return f"{match.group(1).upper()}{int(match.group(2))}"
    stem = Path(file_name).stem.upper()
    return stem if stem in PRIORITY_RANK else None


def _priority_code(row: dict[str, Any], file_name: str) -> str | None:
    chapter = row.get("chapter")
    if isinstance(chapter, str) and chapter.strip().upper() in PRIORITY_RANK:
        return chapter.strip().upper()
    source_id = _nonempty_string(row.get("source_unit_id"))
    if source_id is not None:
        match = _CHAPTER_FROM_SOURCE_ID.match(source_id)
        if match:
            code = f"{match.group(1).upper()}{int(match.group(2))}"
            if code in PRIORITY_RANK:
                return code
    stem = Path(file_name).stem.upper()
    return stem if stem in PRIORITY_RANK else None


def _question_id(row: dict[str, Any]) -> str | None:
    for field in ("question_id", "id"):
        value = _nonempty_string(row.get(field))
        if value is not None:
            return value
    return None


def _permuted_options(options: list[str], seed: str) -> list[str]:
    keyed = [
        (
            hashlib.sha256(f"{seed}:{index}".encode("utf-8")).hexdigest(),
            index,
            option,
        )
        for index, option in enumerate(options)
    ]
    keyed.sort(key=lambda value: (value[0], value[1]))
    return [option for _, _, option in keyed]


def _different_order(options: list[str], seed: str, reference: list[str]) -> list[str]:
    candidate = _permuted_options(options, seed)
    if len(candidate) > 1 and candidate == reference:
        candidate = candidate[1:] + candidate[:1]
    return candidate


def _quote_source_id(
    row: dict[str, Any], source_map: dict[str, list[dict[str, Any]]]
) -> str | None:
    """Return a source id only for a unique, exact quote join."""

    question_quote = _nonempty_string(row.get("source_quote"))
    if question_quote is None:
        return None
    normalized_quote = _normalise_text(question_quote)
    quote_matches = [
        candidate_id
        for candidate_id, candidate_rows in source_map.items()
        if len(candidate_rows) == 1
        and (
            candidate_quote := _nonempty_string(candidate_rows[0].get("source_quote"))
        ) is not None
        and _normalise_text(candidate_quote) == normalized_quote
    ]
    return quote_matches[0] if len(quote_matches) == 1 else None


def _searchable_text(*values: Any) -> str:
    return " ".join(
        " ".join(_text_tokens(value))
        for value in values
        if isinstance(value, str)
    )


def _personal_zone_score(
    row: dict[str, Any],
    chapter: str,
    source_map: dict[str, list[dict[str, Any]]],
) -> int:
    """Score only explicit question/source markers from the V18 zone list."""

    source_id = _nonempty_string(row.get("source_unit_id")) or _quote_source_id(
        row, source_map
    )
    source = source_map.get(source_id, [{}])[0] if source_id is not None else {}
    searchable = _searchable_text(
        row.get("question"),
        row.get("source_ref"),
        row.get("reference"),
        row.get("verse_or_page"),
        row.get("source_quote"),
        source.get("source_ref"),
        source.get("source_quote"),
    )
    return sum(
        1
        for marker in PERSONAL_ZONE_MARKERS.get(chapter, ())
        if marker and " ".join(_text_tokens(marker)) in searchable
    )


def _build_dossier_item(
    row: dict[str, Any],
    source_map: dict[str, list[dict[str, Any]]],
    ocr_pages: dict[int, str],
    audit_run_id: str,
    *,
    allow_quote_source_match: bool = False,
) -> tuple[dict[str, Any] | None, str | None]:
    question_id = _question_id(row)
    if question_id is None:
        return None, "falta question_id/id"
    question = _nonempty_string(row.get("question"))
    if question is None:
        return None, "falta question"
    options = row.get("options")
    if not isinstance(options, list) or len(options) < 2:
        return None, "options debe contener al menos dos opciones"
    if any(_nonempty_string(option) is None for option in options):
        return None, "options contiene un valor vacío o no textual"
    option_values = list(options)
    if len(set(option_values)) != len(option_values):
        return None, "options contiene duplicados"

    source_id = _nonempty_string(row.get("source_unit_id"))
    if source_id is None and allow_quote_source_match:
        # A small subset of existing rows omits source_unit_id but carries an
        # exact source_quote copied from the canonical packet. A unique exact
        # quote is a traceable mechanical join, not a default or an answer
        # inference; ambiguous/missing quotes remain invalid.
        source_id = _quote_source_id(row, source_map)
    if source_id is None:
        return None, "falta source_unit_id"
    source_rows = source_map.get(source_id, [])
    if len(source_rows) != 1:
        return None, "source_unit_id no tiene una unidad de fuente única"
    source = source_rows[0]

    source_ref = _nonempty_string(source.get("source_ref"))
    exact_quote = _nonempty_string(source.get("source_quote"))
    nearby_context = _nearby_context(source)
    material = _nonempty_string(source.get("work"))
    chapter = _chapter_code(row, source_id, "")
    pdf_page = _resolve_pdf_page(source, ocr_pages)
    missing = [
        field
        for field, value in (
            ("source_ref", source_ref),
            ("pdf_page", pdf_page),
            ("exact_quote", exact_quote),
            ("nearby_context", nearby_context),
            ("material", material),
            ("chapter", chapter),
        )
        if value is None or (isinstance(value, str) and not value.strip())
    ]
    if missing:
        return None, f"fuente trazable incompleta: falta {', '.join(missing)}"

    # The output is rebuilt field-by-field. In particular, no answer-bearing
    # value from ``row`` is copied or used to choose an option.
    item = {
        "audit_run_id": audit_run_id,
        "question_id": question_id,
        "question": question,
        "options": _permuted_options(option_values, f"{audit_run_id}:dossier:{question_id}"),
        "source_unit_id": source_id,
        "source_ref": source_ref,
        "pdf_page": pdf_page,
        "exact_quote": exact_quote,
        "nearby_context": nearby_context,
        "material": material,
        "chapter": chapter,
    }
    return item, None


def _batch_sizes(count: int, minimum: int, maximum: int) -> list[int]:
    if count <= 0:
        return []
    if minimum <= 0 or maximum < minimum:
        raise ValueError("rango de lote inválido")
    for batch_count in range(1, count + 1):
        if batch_count * minimum <= count <= batch_count * maximum:
            base, remainder = divmod(count, batch_count)
            return [base + (index < remainder) for index in range(batch_count)]
    return []


def _safe_run_id(audit_run_id: str) -> str:
    value = _nonempty_string(audit_run_id)
    if value is None or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError("audit_run_id debe ser un nombre de ejecución simple")
    return value


def _clear_generated_files(run_dir: Path) -> None:
    if not run_dir.exists():
        return
    for path in run_dir.glob("batch-*.json"):
        if path.is_file():
            path.unlink()
    for name in ("invalid-items.json", "manifest.json"):
        path = run_dir / name
        if path.is_file():
            path.unlink()


def _invalid_entry(question_id: str | None, reason: str, status: str = "INVALID_OUTPUT") -> dict[str, str]:
    entry: dict[str, str] = {"status": status, "reason": reason}
    if question_id is not None:
        entry["question_id"] = question_id
    return entry


def _prepare_dossiers_impl(
    question_dir: Path = DEFAULT_QUESTION_DIR,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    dossier_dir: Path = DEFAULT_DOSSIER_DIR,
    blind_dir: Path = DEFAULT_BLIND_DIR,
    audit_run_id: str = DEFAULT_AUDIT_RUN_ID,
    *,
    ocr_path: Path | None = DEFAULT_OCR_PATH,
    min_batch_size: int = 15,
    max_batch_size: int = 20,
) -> dict[str, Any]:
    """Prepare deterministic dossier/blind batches and return a summary."""

    run_id = _safe_run_id(audit_run_id)
    if not (15 <= min_batch_size <= max_batch_size <= 20):
        raise ValueError("los lotes V18 deben quedar entre 15 y 20 ítems")
    question_dir = Path(question_dir)
    source_dir = Path(source_dir)
    dossier_stage, blind_stage, dossier_target, blind_target = _staging_run_dirs(
        Path(dossier_dir), Path(blind_dir), run_id
    )
    dossier_run_dir = dossier_stage
    blind_run_dir = blind_stage

    question_records, question_errors = _load_question_records(question_dir)
    source_map, source_errors = _load_source_units(source_dir)
    ocr_pages, ocr_trace = _load_ocr_pages_with_status(
        Path(ocr_path) if ocr_path is not None else None
    )

    prioritized: list[dict[str, Any]] = []
    invalid_items: list[dict[str, str]] = [
        _invalid_entry(None, error) for error in question_errors
    ]
    outside_priority = 0
    pr_without_delimiter_count = 0
    for record in question_records:
        row = record["row"]
        priority = _priority_code(row, record["file"])
        if priority is None:
            outside_priority += 1
            invalid_items.append(
                _invalid_entry(
                    _question_id(row),
                    "fuera de la prioridad V18 (no se incluyó en lotes)",
                )
            )
            continue
        if priority.startswith("PR") and SAFE_FIRST_PR_DELIMITER not in str(row.get("question") or ""):
            outside_priority += 1
            pr_without_delimiter_count += 1
            invalid_items.append(
                _invalid_entry(
                    _question_id(row),
                    f"PR excluida: falta delimitador {SAFE_FIRST_PR_DELIMITER!r}",
                )
            )
            continue
        prioritized.append(
            {
                **record,
                "priority": priority,
                "sort_id": _question_id(row) or f"~{record['file']}:{record['index']:08d}",
            }
        )
    prioritized.sort(
        key=lambda record: (
            PRIORITY_RANK[record["priority"]],
            record["sort_id"],
            record["file"],
            record["index"],
        )
    )

    id_counts: dict[str, int] = {}
    for record in prioritized:
        question_id = _question_id(record["row"])
        if question_id is not None:
            id_counts[question_id] = id_counts.get(question_id, 0) + 1

    valid_items: list[dict[str, Any]] = []
    for record in prioritized:
        row = record["row"]
        question_id = _question_id(row)
        if question_id is not None and id_counts[question_id] > 1:
            item, reason = None, "question_id duplicado"
        else:
            item, reason = _build_dossier_item(
                row,
                source_map,
                ocr_pages,
                run_id,
            )
        if item is None:
            invalid_items.append(_invalid_entry(question_id, reason or "INVALID_OUTPUT"))
        else:
            valid_items.append(item)

    sizes = _batch_sizes(len(valid_items), min_batch_size, max_batch_size)
    batched_count = sum(sizes)
    out_of_batch_items = valid_items[batched_count:]
    if out_of_batch_items:
        for item in out_of_batch_items:
            invalid_items.append(
                _invalid_entry(
                    item["question_id"],
                    f"fuera del lote: no existe partición entre {min_batch_size} y {max_batch_size}",
                    status="OUT_OF_BATCH",
                )
            )

    batch_records: list[dict[str, Any]] = []
    blind_records: list[dict[str, Any]] = []
    offset = 0
    for batch_index, size in enumerate(sizes, start=1):
        batch_name = f"batch-{batch_index:03d}.json"
        batch_items = valid_items[offset : offset + size]
        offset += size
        dossier_payload = {
            "schema_version": "final-day-v18-audit-dossier-1.0",
            "audit_run_id": run_id,
            "batch_id": batch_name[:-5],
            "items": batch_items,
        }
        blind_items = []
        for item in batch_items:
            blind_items.append(
                {
                    "audit_run_id": run_id,
                    "question_id": item["question_id"],
                    "question": item["question"],
                    "options": _different_order(
                        item["options"],
                        f"{run_id}:blind:{item['question_id']}",
                        item["options"],
                    ),
                }
            )
        blind_payload = {
            "schema_version": "final-day-v18-blind-pair-1.0",
            "audit_run_id": run_id,
            "batch_id": batch_name[:-5],
            "items": blind_items,
        }
        _atomic_write_json(dossier_run_dir / batch_name, dossier_payload)
        _atomic_write_json(blind_run_dir / batch_name, blind_payload)
        batch_records.append(
            {
                "batch_id": batch_name[:-5],
                "file": batch_name,
                "item_count": len(batch_items),
                "content_sha256": _sha256(dossier_payload),
            }
        )
        blind_records.append(
            {
                "batch_id": batch_name[:-5],
                "file": batch_name,
                "item_count": len(blind_items),
                "content_sha256": _sha256(blind_payload),
            }
        )

    invalid_payload = {
        "schema_version": "final-day-v18-invalid-items-1.0",
        "audit_run_id": run_id,
        "items": invalid_items,
    }
    _atomic_write_json(dossier_run_dir / "invalid-items.json", invalid_payload)

    manifest = {
        "schema_version": "final-day-v18-dossier-manifest-1.0",
        "audit_run_id": run_id,
        "selection_mode": "priority",
        "priority_order": list(PRIORITY_ORDER),
        "batch_min": min_batch_size,
        "batch_max": max_batch_size,
        "selected_count": len(prioritized),
        "valid_count": len(valid_items),
        "batched_count": batched_count,
        "invalid_count": sum(
            1 for item in invalid_items if item["status"] == "INVALID_OUTPUT"
        ),
        "out_of_batch_count": sum(
            1 for item in invalid_items if item["status"] == "OUT_OF_BATCH"
        ),
        "outside_priority_count": outside_priority,
        "pr_without_delimiter_count": pr_without_delimiter_count,
        "batch_count": len(batch_records),
        "batch_sizes": sizes,
        "question_errors": question_errors,
        "source_errors": source_errors,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        **ocr_trace,
        "input_question_count": len(question_records) + len(question_errors),
        "excluded_count": outside_priority + len(question_errors),
        "selected_invalid_count": max(
            0,
            sum(1 for item in invalid_items if item["status"] == "INVALID_OUTPUT")
            - outside_priority
            - len(question_errors),
        ),
        "batches": batch_records,
        "blind_batches": blind_records,
        "invalid_items_file": "invalid-items.json",
        "invalid_items_sha256": _sha256(invalid_payload),
    }
    _atomic_write_json(dossier_run_dir / "manifest.json", manifest)

    if not verify_artifacts(dossier_run_dir, blind_run_dir):
        raise RuntimeError("artefactos V18 inválidos en staging; no se publicaron")
    _publish_staged_pair(
        dossier_run_dir,
        blind_run_dir,
        dossier_target,
        blind_target,
    )

    return {
        "audit_run_id": run_id,
        "selected_count": len(prioritized),
        "valid_count": len(valid_items),
        "batched_count": batched_count,
        "invalid_count": manifest["invalid_count"],
        "out_of_batch_count": manifest["out_of_batch_count"],
        "outside_priority_count": outside_priority,
        "batch_count": len(batch_records),
        "batch_sizes": sizes,
        "dossier_dir": str(dossier_target),
        "blind_dir": str(blind_target),
    }


def _cleanup_staging_runs(parent: Path, run_id: str) -> None:
    for path in parent.glob(f".{run_id}.staging-*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def prepare_dossiers(
    question_dir: Path = DEFAULT_QUESTION_DIR,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    dossier_dir: Path = DEFAULT_DOSSIER_DIR,
    blind_dir: Path = DEFAULT_BLIND_DIR,
    audit_run_id: str = DEFAULT_AUDIT_RUN_ID,
    *,
    ocr_path: Path | None = DEFAULT_OCR_PATH,
    min_batch_size: int = 15,
    max_batch_size: int = 20,
) -> dict[str, Any]:
    """Prepare a priority run and clean hidden staging on any failed write."""

    try:
        return _prepare_dossiers_impl(
            question_dir=question_dir,
            source_dir=source_dir,
            dossier_dir=dossier_dir,
            blind_dir=blind_dir,
            audit_run_id=audit_run_id,
            ocr_path=ocr_path,
            min_batch_size=min_batch_size,
            max_batch_size=max_batch_size,
        )
    except Exception:
        run_id = _safe_run_id(audit_run_id)
        _cleanup_staging_runs(Path(dossier_dir), run_id)
        _cleanup_staging_runs(Path(blind_dir), run_id)
        raise


def _write_batch_pair(
    items: list[dict[str, Any]],
    run_id: str,
    dossier_run_dir: Path,
    blind_run_dir: Path,
    *,
    min_batch_size: int,
    max_batch_size: int,
    invalid_items: list[dict[str, str]],
    priority_order: list[str],
    question_errors: list[str],
    source_errors: list[str],
    outside_priority_count: int,
    manifest_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit a complete generated run into already-created staging directories."""

    if not (15 <= min_batch_size <= max_batch_size <= 20):
        raise ValueError("los lotes V18 deben quedar entre 15 y 20 ítems")
    sizes = _batch_sizes(len(items), min_batch_size, max_batch_size)
    if sum(sizes) != len(items) or any(
        size < min_batch_size or size > max_batch_size for size in sizes
    ):
        raise ValueError("no existe una partición válida de lotes V18")

    batch_records: list[dict[str, Any]] = []
    blind_records: list[dict[str, Any]] = []
    offset = 0
    for batch_index, size in enumerate(sizes, start=1):
        batch_name = f"batch-{batch_index:03d}.json"
        batch_items = items[offset : offset + size]
        offset += size
        dossier_payload = {
            "schema_version": "final-day-v18-audit-dossier-1.0",
            "audit_run_id": run_id,
            "batch_id": batch_name[:-5],
            "items": batch_items,
        }
        blind_items = [
            {
                "audit_run_id": run_id,
                "question_id": item["question_id"],
                "question": item["question"],
                "options": _different_order(
                    item["options"],
                    f"{run_id}:blind:{item['question_id']}",
                    item["options"],
                ),
            }
            for item in batch_items
        ]
        blind_payload = {
            "schema_version": "final-day-v18-blind-pair-1.0",
            "audit_run_id": run_id,
            "batch_id": batch_name[:-5],
            "items": blind_items,
        }
        _atomic_write_json(dossier_run_dir / batch_name, dossier_payload)
        _atomic_write_json(blind_run_dir / batch_name, blind_payload)
        batch_records.append(
            {
                "batch_id": batch_name[:-5],
                "file": batch_name,
                "item_count": len(batch_items),
                "content_sha256": _sha256(dossier_payload),
            }
        )
        blind_records.append(
            {
                "batch_id": batch_name[:-5],
                "file": batch_name,
                "item_count": len(blind_items),
                "content_sha256": _sha256(blind_payload),
            }
        )

    invalid_payload = {
        "schema_version": "final-day-v18-invalid-items-1.0",
        "audit_run_id": run_id,
        "items": invalid_items,
    }
    _atomic_write_json(dossier_run_dir / "invalid-items.json", invalid_payload)
    manifest: dict[str, Any] = {
        "schema_version": "final-day-v18-dossier-manifest-1.0",
        "audit_run_id": run_id,
        "selection_mode": "priority",
        "priority_order": priority_order,
        "batch_min": min_batch_size,
        "batch_max": max_batch_size,
        "selected_count": len(items),
        "valid_count": len(items),
        "batched_count": sum(sizes),
        "invalid_count": sum(
            1 for item in invalid_items if item["status"] == "INVALID_OUTPUT"
        ),
        "out_of_batch_count": sum(
            1 for item in invalid_items if item["status"] == "OUT_OF_BATCH"
        ),
        "outside_priority_count": outside_priority_count,
        "batch_count": len(batch_records),
        "batch_sizes": sizes,
        "question_errors": question_errors,
        "source_errors": source_errors,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "input_question_count": len(items),
        "excluded_count": 0,
        "selected_invalid_count": 0,
        "batches": batch_records,
        "blind_batches": blind_records,
        "invalid_items_file": "invalid-items.json",
        "invalid_items_sha256": _sha256(invalid_payload),
    }
    if manifest_extra:
        manifest.update(manifest_extra)
    _atomic_write_json(dossier_run_dir / "manifest.json", manifest)
    return manifest


def _safe_first_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(record.get("personal_score", 0)),
        SAFE_FIRST_PRIORITY_RANK[record["priority"]],
        record["sort_id"],
        record["file"],
        record["index"],
    )


def _safe_first_daniel_selection(
    candidates: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    """Select priority personal-zone Daniel records deterministically."""

    selected: list[dict[str, Any]] = []
    # Alternate the two specifically requested chapters while both have
    # personal-zone candidates; this prevents a large DAN9 pool from starving
    # DAN12 without inventing a quota or using answer metadata.
    pools: dict[str, list[dict[str, Any]]] = {}
    for chapter in ("DAN9", "DAN12"):
        pools[chapter] = sorted(
            [record for record in candidates if record["priority"] == chapter and record["personal_score"] > 0],
            key=_safe_first_sort_key,
        )
    while len(selected) < limit and any(pools.values()):
        progressed = False
        for chapter in ("DAN9", "DAN12"):
            if pools[chapter] and len(selected) < limit:
                selected.append(pools[chapter].pop(0))
                progressed = True
        if not progressed:
            break

    chosen_ids = {record["sort_id"] for record in selected}
    remainder = sorted(
        [record for record in candidates if record["sort_id"] not in chosen_ids],
        key=_safe_first_sort_key,
    )
    selected.extend(remainder[: max(0, limit - len(selected))])
    return selected[:limit]


def _safe_first_pr_selection(
    candidates: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    """Round-robin PR39–44 so the fixed safe lane is chapter-distributed."""

    pools: dict[str, list[dict[str, Any]]] = {}
    for chapter in (f"PR{number}" for number in range(39, 45)):
        pools[chapter] = sorted(
            [record for record in candidates if record["priority"] == chapter],
            key=lambda record: (
                record["sort_id"],
                record["file"],
                record["index"],
            ),
        )
    selected: list[dict[str, Any]] = []
    while len(selected) < limit and any(pools.values()):
        progressed = False
        for chapter in (f"PR{number}" for number in range(39, 45)):
            if pools[chapter] and len(selected) < limit:
                selected.append(pools[chapter].pop(0))
                progressed = True
        if not progressed:
            break
    return selected[:limit]


def prepare_safe_first_dossiers(
    question_dir: Path = DEFAULT_QUESTION_DIR,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    dossier_dir: Path = DEFAULT_DOSSIER_DIR,
    blind_dir: Path = DEFAULT_BLIND_DIR,
    audit_run_id: str = SAFE_FIRST_RUN_ID,
    *,
    ocr_path: Path | None = DEFAULT_OCR_PATH,
) -> dict[str, Any]:
    """Prepare exactly four 20-item safe-first dossier/blind batches.

    This lane is intentionally independent from ``v18-priority-audit``. It
    selects only existing PR39–44 stems containing the exact source delimiter,
    then Daniel 7–12 records with traceable source, prioritising personal-zone
    text markers and alternating DAN9/DAN12 where available.
    """

    run_id = _safe_run_id(audit_run_id)
    if run_id != SAFE_FIRST_RUN_ID:
        raise ValueError(f"safe-first requiere audit_run_id={SAFE_FIRST_RUN_ID!r}")
    question_dir = Path(question_dir)
    source_dir = Path(source_dir)
    question_records, question_errors = _load_question_records(question_dir)
    source_map, source_errors = _load_source_units(source_dir)
    ocr_pages, ocr_trace = _load_ocr_pages_with_status(
        Path(ocr_path) if ocr_path is not None else None
    )

    eligible: list[dict[str, Any]] = []
    invalid_items: list[dict[str, str]] = [
        _invalid_entry(None, error) for error in question_errors
    ]
    outside_priority_count = 0
    outside_scope_count = 0
    pr_without_delimiter_count = 0
    safe_pr_chapters = {f"PR{number}" for number in range(39, 45)}
    safe_daniel_chapters = {"DAN9", "DAN12"}
    for record in question_records:
        row = record["row"]
        chapter = _priority_code(row, record["file"])
        if chapter is None:
            outside_priority_count += 1
            outside_scope_count += 1
            invalid_items.append(
                _invalid_entry(
                    _question_id(row),
                    "excluida de safe-first: fuera de la prioridad V18",
                    status="EXCLUDED",
                )
            )
            continue
        question = _nonempty_string(row.get("question"))
        is_pr = chapter in safe_pr_chapters
        is_daniel = chapter in safe_daniel_chapters
        if is_pr and question is not None and SAFE_FIRST_PR_DELIMITER in question:
            eligible.append(
                {
                    **record,
                    "priority": chapter,
                    "sort_id": _question_id(row) or f"~{record['file']}:{record['index']:08d}",
                    "lane": "PR",
                }
            )
        elif is_pr:
            pr_without_delimiter_count += 1
            invalid_items.append(
                _invalid_entry(
                    _question_id(row),
                    f"excluida de safe-first: falta delimitador {SAFE_FIRST_PR_DELIMITER!r}",
                    status="EXCLUDED",
                )
            )
        elif is_daniel:
            eligible.append(
                {
                    **record,
                    "priority": chapter,
                    "sort_id": _question_id(row) or f"~{record['file']}:{record['index']:08d}",
                    "lane": "DANIEL",
                }
            )
        else:
            outside_scope_count += 1
            invalid_items.append(
                _invalid_entry(
                    _question_id(row),
                    "excluida de safe-first: capítulo fuera de PR39–44/DAN9/DAN12",
                    status="EXCLUDED",
                )
            )

    id_counts: dict[str, int] = {}
    for record in eligible:
        question_id = _question_id(record["row"])
        if question_id is not None:
            id_counts[question_id] = id_counts.get(question_id, 0) + 1

    valid_records: list[dict[str, Any]] = []
    for record in eligible:
        row = record["row"]
        question_id = _question_id(row)
        if question_id is not None and id_counts[question_id] > 1:
            item, reason = None, "question_id duplicado"
        else:
            item, reason = _build_dossier_item(
                row,
                source_map,
                ocr_pages,
                run_id,
                allow_quote_source_match=True,
            )
        if item is None:
            invalid_items.append(_invalid_entry(question_id, reason or "INVALID_OUTPUT"))
            continue
        record = {
            **record,
            "item": item,
            "personal_score": (
                _personal_zone_score(row, record["priority"], source_map)
                if record["lane"] == "DANIEL"
                else 0
            ),
        }
        valid_records.append(record)

    pr_records = sorted(
        [record for record in valid_records if record["lane"] == "PR"],
        key=lambda record: (
            SAFE_FIRST_PRIORITY_RANK[record["priority"]],
            record["sort_id"],
            record["file"],
            record["index"],
        ),
    )
    daniel_records = [record for record in valid_records if record["lane"] == "DANIEL"]
    selected_pr = _safe_first_pr_selection(pr_records, 60)
    if len(daniel_records) < 20:
        raise ValueError(
            "safe-first no puede completar 20 preguntas trazables de DAN9/12 "
            f"(disponibles DAN9/12={len(daniel_records)})"
        )
    selected_daniel = _safe_first_daniel_selection(daniel_records, 20)
    if len(selected_pr) != 60 or len(selected_daniel) != 20:
        raise ValueError(
            "safe-first no puede completar 60 PR delimitadas y 20 DAN9/12 "
            f"(disponibles PR={len(pr_records)}, DAN9/12={len(daniel_records)})"
        )
    selected_records = selected_pr + selected_daniel
    selected_items = [record["item"] for record in selected_records]
    selected_ids = {item["question_id"] for item in selected_items}
    for record in valid_records:
        if record["item"]["question_id"] not in selected_ids:
            invalid_items.append(
                _invalid_entry(
                    record["item"]["question_id"],
                    "excluida de safe-first: candidata válida no seleccionada en el cupo 60/20",
                    status="EXCLUDED",
                )
            )
    if len({item["question_id"] for item in selected_items}) != 80:
        raise ValueError("safe-first produjo question_id duplicado")

    dossier_stage, blind_stage, dossier_target, blind_target = _staging_run_dirs(
        Path(dossier_dir), Path(blind_dir), run_id
    )
    try:
        manifest = _write_batch_pair(
            selected_items,
            run_id,
            dossier_stage,
            blind_stage,
            min_batch_size=20,
            max_batch_size=20,
            invalid_items=invalid_items,
            priority_order=list(SAFE_FIRST_PRIORITY_ORDER),
            question_errors=question_errors,
            source_errors=source_errors,
            # Safe-first's declared scope is narrower than the priority source
            # universe: every record outside PR39–44/DAN9/DAN12 belongs in
            # the explicit outside-scope accounting, while the separate
            # unknown-priority count preserves the subset that could not be
            # classified at all.
            outside_priority_count=outside_scope_count,
            manifest_extra={
                "selection_mode": "safe-first",
                "selected_invalid_count": 0,
                "safe_first_pr_delimiter": SAFE_FIRST_PR_DELIMITER,
                "safe_first_pr_count": len(selected_pr),
                "safe_first_daniel_count": len(selected_daniel),
                "safe_first_candidate_count": len(eligible),
                "safe_first_valid_candidate_count": len(valid_records),
                "safe_first_invalid_candidate_count": len(eligible) - len(valid_records),
                "safe_first_unselected_candidate_count": len(valid_records) - len(selected_items),
                "safe_first_excluded_count": len(question_records) + len(question_errors) - len(selected_items),
                "input_question_count": len(question_records) + len(question_errors),
                "excluded_count": len(question_records) + len(question_errors) - len(selected_items),
                "outside_scope_count": outside_scope_count,
                "unknown_priority_count": outside_priority_count,
                "pr_without_delimiter_count": pr_without_delimiter_count,
                "question_error_count": len(question_errors),
                "safe_first_daniel_priority": ["DAN9", "DAN12"],
                **ocr_trace,
            },
        )
        if not verify_artifacts(dossier_stage, blind_stage):
            raise RuntimeError("artefactos safe-first inválidos en staging; no se publicaron")
        _publish_staged_pair(dossier_stage, blind_stage, dossier_target, blind_target)
    except Exception:
        if dossier_stage.exists():
            shutil.rmtree(dossier_stage, ignore_errors=True)
        if blind_stage.exists():
            shutil.rmtree(blind_stage, ignore_errors=True)
        raise

    return {
        "audit_run_id": run_id,
        "selected_count": len(selected_items),
        "valid_count": len(selected_items),
        "batched_count": manifest["batched_count"],
        "invalid_count": manifest["invalid_count"],
        "out_of_batch_count": manifest["out_of_batch_count"],
        "outside_priority_count": manifest["outside_priority_count"],
        "unknown_priority_count": manifest["unknown_priority_count"],
        "batch_count": manifest["batch_count"],
        "batch_sizes": manifest["batch_sizes"],
        "pr_count": len(selected_pr),
        "daniel_count": len(selected_daniel),
        "excluded_count": manifest["excluded_count"],
        "outside_scope_count": manifest["outside_scope_count"],
        "pr_without_delimiter_count": manifest["pr_without_delimiter_count"],
        "ocr_path": manifest["ocr_path"],
        "ocr_status": manifest["ocr_status"],
        "dossier_dir": str(dossier_target),
        "blind_dir": str(blind_target),
    }


def _valid_item(item: Any, expected_fields: frozenset[str]) -> bool:
    if not (
        isinstance(item, dict)
        and set(item) == expected_fields
        and not PROHIBITED_FIELDS.intersection(item)
        and isinstance(item.get("options"), list)
        and len(item["options"]) >= 2
        and len(set(item["options"])) == len(item["options"])
        and _nonempty_string(item.get("audit_run_id")) is not None
        and _nonempty_string(item.get("question_id")) is not None
        and _nonempty_string(item.get("question")) is not None
        and all(_nonempty_string(option) is not None for option in item["options"])
    ):
        return False
    if expected_fields != DOSSIER_ITEM_FIELDS:
        return True
    if any(
        _nonempty_string(item.get(field)) is None
        for field in (
            "source_unit_id",
            "source_ref",
            "exact_quote",
            "nearby_context",
            "material",
        )
    ):
        return False
    chapter = item.get("chapter")
    if not (
        _nonempty_string(chapter) is not None
        or (
            isinstance(chapter, int)
            and not isinstance(chapter, bool)
            and chapter > 0
        )
    ):
        return False
    return _positive_page(item.get("pdf_page")) is not None


def verify_artifacts(
    dossier_run_dir: Path,
    blind_run_dir: Path | None = None,
) -> bool:
    """Verify manifest hashes and the dossier/blind field boundaries."""

    try:
        dossier_run_dir = Path(dossier_run_dir)
        resolved_blind_dir = (
            Path(blind_run_dir)
            if blind_run_dir is not None
            else dossier_run_dir.parent.parent / "blind" / dossier_run_dir.name
        )
        common_parent = Path(
            os.path.commonpath([dossier_run_dir.parent, resolved_blind_dir.parent])
        )
        if (common_parent / f".{dossier_run_dir.name}.publishing").exists():
            return False
        manifest = _load_json(dossier_run_dir / "manifest.json")
        if not isinstance(manifest, dict):
            return False
        if manifest.get("schema_version") != "final-day-v18-dossier-manifest-1.0":
            return False
        run_id = _nonempty_string(manifest.get("audit_run_id"))
        if run_id is None:
            return False
        batch_min = manifest.get("batch_min")
        batch_max = manifest.get("batch_max")
        if (
            not isinstance(batch_min, int)
            or isinstance(batch_min, bool)
            or not isinstance(batch_max, int)
            or isinstance(batch_max, bool)
            or not (15 <= batch_min <= batch_max <= 20)
            or manifest.get("source_sha256") != EXPECTED_SOURCE_SHA256
        ):
            return False
        ocr_status = manifest.get("ocr_status")
        if ocr_status not in {
            "VALID",
            "MISSING",
            "INVALID_JSON",
            "INVALID_SCHEMA",
            "INVALID_HASH",
            "NOT_REQUESTED",
        }:
            return False
        ocr_path = manifest.get("ocr_path")
        if ocr_path is not None:
            if _nonempty_string(ocr_path) is None or not Path(ocr_path).is_absolute():
                return False
        ocr_hash = manifest.get("ocr_source_sha256")
        if ocr_hash is not None and _nonempty_string(ocr_hash) is None:
            return False
        if ocr_status == "VALID":
            if ocr_path is None or ocr_hash != EXPECTED_SOURCE_SHA256:
                return False
            actual_pages, actual_trace = _load_ocr_pages_with_status(Path(ocr_path))
            if (
                not actual_pages
                or actual_trace.get("ocr_status") != "VALID"
                or actual_trace.get("ocr_source_sha256") != ocr_hash
                or actual_trace.get("ocr_path") != ocr_path
            ):
                return False
        elif ocr_status == "NOT_REQUESTED":
            if ocr_path is not None or ocr_hash is not None:
                return False
        elif ocr_status in {"MISSING", "INVALID_JSON"}:
            if ocr_path is None or ocr_hash is not None:
                return False
        elif ocr_status in {"INVALID_SCHEMA", "INVALID_HASH"}:
            if ocr_path is None:
                return False
            if ocr_status == "INVALID_HASH" and ocr_hash == EXPECTED_SOURCE_SHA256:
                return False
        if not isinstance(manifest.get("question_errors"), list) or not all(
            isinstance(error, str) and error.strip()
            for error in manifest["question_errors"]
        ):
            return False
        if not isinstance(manifest.get("source_errors"), list) or not all(
            isinstance(error, str) and error.strip()
            for error in manifest["source_errors"]
        ):
            return False
        batches = manifest.get("batches")
        blind_batches = manifest.get("blind_batches")
        if not isinstance(batches, list) or not isinstance(blind_batches, list):
            return False
        if len(batches) != len(blind_batches):
            return False
        if (
            not isinstance(manifest.get("batch_count"), int)
            or isinstance(manifest.get("batch_count"), bool)
            or manifest["batch_count"] < 0
            or manifest["batch_count"] != len(batches)
        ):
            return False
        manifest_sizes = manifest.get("batch_sizes")
        if not isinstance(manifest_sizes, list) or len(manifest_sizes) != len(batches):
            return False
        if any(
            not isinstance(size, int)
            or isinstance(size, bool)
            or not (batch_min <= size <= batch_max)
            for size in manifest_sizes
        ):
            return False
        blind_run_dir = resolved_blind_dir
        expected_batch_files = {
            f"batch-{batch_index:03d}.json"
            for batch_index in range(1, len(batches) + 1)
        }
        if (
            {
                path.name
                for path in dossier_run_dir.glob("batch-*.json")
                if path.is_file()
            }
            != expected_batch_files
            or {
                path.name
                for path in blind_run_dir.glob("batch-*.json")
                if path.is_file()
            }
            != expected_batch_files
        ):
            return False

        dossier_ids: list[str] = []
        blind_ids: list[str] = []
        for batch_index, (dossier_record, blind_record) in enumerate(
            zip(batches, blind_batches), start=1
        ):
            if not isinstance(dossier_record, dict) or not isinstance(blind_record, dict):
                return False
            expected_batch_id = f"batch-{batch_index:03d}"
            if (
                dossier_record.get("batch_id") != expected_batch_id
                or blind_record.get("batch_id") != expected_batch_id
                or dossier_record.get("file") != f"{expected_batch_id}.json"
                or blind_record.get("file") != f"{expected_batch_id}.json"
                or dossier_record.get("item_count") != blind_record.get("item_count")
                or dossier_record.get("item_count") != manifest_sizes[batch_index - 1]
            ):
                return False
            if (
                not isinstance(dossier_record.get("item_count"), int)
                or not (
                    batch_min
                    <= dossier_record["item_count"]
                    <= batch_max
                    and 15 <= dossier_record["item_count"] <= 20
                )
            ):
                return False
            dossier_file = dossier_run_dir / dossier_record["file"]
            blind_file = blind_run_dir / blind_record["file"]
            dossier_payload = _load_json(dossier_file)
            blind_payload = _load_json(blind_file)
            if not isinstance(dossier_payload, dict) or not isinstance(blind_payload, dict):
                return False
            if _sha256(dossier_payload) != dossier_record.get("content_sha256"):
                return False
            if _sha256(blind_payload) != blind_record.get("content_sha256"):
                return False
            if dossier_payload.get("schema_version") != "final-day-v18-audit-dossier-1.0":
                return False
            if blind_payload.get("schema_version") != "final-day-v18-blind-pair-1.0":
                return False
            if dossier_payload.get("audit_run_id") != run_id:
                return False
            if blind_payload.get("audit_run_id") != run_id:
                return False
            if dossier_payload.get("batch_id") != expected_batch_id:
                return False
            if blind_payload.get("batch_id") != expected_batch_id:
                return False
            dossier_items = dossier_payload.get("items")
            blind_items = blind_payload.get("items")
            if not isinstance(dossier_items, list) or not isinstance(blind_items, list):
                return False
            if len(dossier_items) != len(blind_items):
                return False
            if len(dossier_items) != dossier_record["item_count"]:
                return False
            for dossier_item, blind_item in zip(dossier_items, blind_items):
                if not _valid_item(dossier_item, DOSSIER_ITEM_FIELDS):
                    return False
                if not _valid_item(blind_item, BLIND_ITEM_FIELDS):
                    return False
                if dossier_item["audit_run_id"] != run_id or blind_item["audit_run_id"] != run_id:
                    return False
                if dossier_item["question_id"] != blind_item["question_id"]:
                    return False
                if dossier_item["question"] != blind_item["question"]:
                    return False
                if (
                    str(dossier_item.get("chapter", "")).startswith("PR")
                    and SAFE_FIRST_PR_DELIMITER not in dossier_item["question"]
                ):
                    return False
                if sorted(dossier_item["options"]) != sorted(blind_item["options"]):
                    return False
                if len(dossier_item["options"]) > 1 and dossier_item["options"] == blind_item["options"]:
                    return False
                dossier_ids.append(dossier_item["question_id"])
                blind_ids.append(blind_item["question_id"])

        if dossier_ids != blind_ids or len(set(dossier_ids)) != len(dossier_ids):
            return False
        if manifest.get("batched_count") != len(dossier_ids):
            return False
        if not isinstance(manifest.get("valid_count"), int) or manifest["valid_count"] < len(dossier_ids):
            return False
        if not isinstance(manifest.get("selected_count"), int) or manifest["selected_count"] < manifest["valid_count"]:
            return False
        invalid_file = dossier_run_dir / manifest.get("invalid_items_file", "invalid-items.json")
        invalid_payload = _load_json(invalid_file)
        if not isinstance(invalid_payload, dict):
            return False
        if invalid_payload.get("schema_version") != "final-day-v18-invalid-items-1.0":
            return False
        if (
            invalid_payload.get("audit_run_id") != run_id
            or not isinstance(invalid_payload.get("items"), list)
            or any(not _valid_invalid_item(item) for item in invalid_payload["items"])
        ):
            return False
        if _sha256(invalid_payload) != manifest.get("invalid_items_sha256"):
            return False
        invalid_items = invalid_payload["items"]
        invalid_count = sum(item.get("status") == "INVALID_OUTPUT" for item in invalid_items if isinstance(item, dict))
        out_of_batch_count = sum(item.get("status") == "OUT_OF_BATCH" for item in invalid_items if isinstance(item, dict))
        excluded_entry_count = sum(item.get("status") == "EXCLUDED" for item in invalid_items if isinstance(item, dict))
        if manifest.get("invalid_count") != invalid_count or manifest.get("out_of_batch_count") != out_of_batch_count:
            return False
        accounting_fields = (
            "input_question_count",
            "excluded_count",
            "selected_invalid_count",
            "selected_count",
            "valid_count",
            "batched_count",
            "invalid_count",
            "out_of_batch_count",
            "outside_priority_count",
        )
        if any(
            not isinstance(manifest.get(field), int)
            or isinstance(manifest.get(field), bool)
            or manifest[field] < 0
            for field in accounting_fields
        ):
            return False
        if manifest["valid_count"] != manifest["batched_count"] + manifest["out_of_batch_count"]:
            return False
        selection_mode = manifest.get("selection_mode")
        if selection_mode == "priority":
            if manifest["input_question_count"] != manifest["selected_count"] + manifest["excluded_count"]:
                return False
            if manifest["excluded_count"] != manifest["outside_priority_count"] + len(manifest["question_errors"]):
                return False
            if manifest["selected_count"] != manifest["valid_count"] + manifest["selected_invalid_count"]:
                return False
            if manifest["invalid_count"] != manifest["selected_invalid_count"] + manifest["excluded_count"]:
                return False
        elif selection_mode == "safe-first":
            safe_fields = (
                "safe_first_pr_count",
                "safe_first_daniel_count",
                "safe_first_candidate_count",
                "safe_first_valid_candidate_count",
                "safe_first_invalid_candidate_count",
                "safe_first_unselected_candidate_count",
                "safe_first_excluded_count",
                "outside_scope_count",
                "unknown_priority_count",
                "pr_without_delimiter_count",
                "question_error_count",
            )
            if any(
                not isinstance(manifest.get(field), int)
                or isinstance(manifest.get(field), bool)
                or manifest[field] < 0
                for field in safe_fields
            ):
                return False
            if manifest["input_question_count"] != manifest["selected_count"] + manifest["excluded_count"]:
                return False
            if manifest["excluded_count"] != manifest["safe_first_excluded_count"]:
                return False
            if manifest["outside_priority_count"] != manifest["outside_scope_count"]:
                return False
            if manifest["unknown_priority_count"] > manifest["outside_scope_count"]:
                return False
            if manifest["selected_count"] != manifest["safe_first_pr_count"] + manifest["safe_first_daniel_count"]:
                return False
            if manifest["safe_first_pr_count"] != 60 or manifest["safe_first_daniel_count"] != 20:
                return False
            if manifest["safe_first_candidate_count"] != manifest["safe_first_valid_candidate_count"] + manifest["safe_first_invalid_candidate_count"]:
                return False
            if manifest["safe_first_unselected_candidate_count"] != manifest["safe_first_valid_candidate_count"] - manifest["selected_count"]:
                return False
            if manifest["invalid_count"] != manifest["safe_first_invalid_candidate_count"] + manifest["question_error_count"]:
                return False
            if manifest["excluded_count"] != (
                manifest["pr_without_delimiter_count"]
                + manifest["outside_scope_count"]
                + manifest["safe_first_unselected_candidate_count"]
                + manifest["safe_first_invalid_candidate_count"]
                + manifest["question_error_count"]
            ):
                return False
            if excluded_entry_count != (
                manifest["pr_without_delimiter_count"]
                + manifest["outside_scope_count"]
                + manifest["safe_first_unselected_candidate_count"]
            ):
                return False
        else:
            return False
        return True
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question-dir", type=Path, default=DEFAULT_QUESTION_DIR)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--dossier-dir", type=Path, default=DEFAULT_DOSSIER_DIR)
    parser.add_argument("--blind-dir", type=Path, default=DEFAULT_BLIND_DIR)
    parser.add_argument("--ocr", type=Path, default=DEFAULT_OCR_PATH)
    parser.add_argument("--audit-run-id", default=DEFAULT_AUDIT_RUN_ID)
    parser.add_argument("--min-batch-size", type=int, default=15)
    parser.add_argument("--max-batch-size", type=int, default=20)
    parser.add_argument(
        "--safe-first",
        action="store_true",
        help="generar únicamente la selección v18-safe-first de 4 lotes de 20",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.safe_first:
        result = prepare_safe_first_dossiers(
            question_dir=args.question_dir,
            source_dir=args.source_dir,
            dossier_dir=args.dossier_dir,
            blind_dir=args.blind_dir,
            audit_run_id=SAFE_FIRST_RUN_ID,
            ocr_path=args.ocr,
        )
    else:
        result = prepare_dossiers(
            question_dir=args.question_dir,
            source_dir=args.source_dir,
            dossier_dir=args.dossier_dir,
            blind_dir=args.blind_dir,
            audit_run_id=args.audit_run_id,
            ocr_path=args.ocr,
            min_batch_size=args.min_batch_size,
            max_batch_size=args.max_batch_size,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
