#!/usr/bin/env python3
"""Promueve de forma aditiva las presentaciones ciegas V10 al banco de entrenamiento."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTENT_ROOT = ROOT / "content" / "competitive-v11"
DEFAULT_ASSIGNMENT = DEFAULT_CONTENT_ROOT / "blind-assignment-v11.json"
DEFAULT_REGISTRY = DEFAULT_CONTENT_ROOT / "promoted-blind-v10.json"
POOLS = ("A", "B", "emergency")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v11 import content_hash


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def encode_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load_documents(directory: Path, id_key: str) -> tuple[dict[str, tuple[Path, dict]], dict[Path, list[dict]]]:
    occurrences: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    documents: dict[Path, list[dict]] = {}
    for path in sorted(directory.glob("*.json")):
        rows = read_json(path)
        if not isinstance(rows, list):
            raise ValueError(f"{path}: se esperaba una lista JSON")
        documents[path] = rows
        for row in rows:
            if not isinstance(row, dict) or id_key not in row:
                raise ValueError(f"{path}: registro sin {id_key}")
            occurrences[str(row[id_key])].append((path, row))
    duplicates = sorted(key for key, values in occurrences.items() if len(values) != 1)
    if duplicates:
        raise ValueError(f"IDs ambiguos en {directory}: {duplicates}")
    return ({key: values[0] for key, values in occurrences.items()}, documents)


def assignment_index(assignment: Mapping[str, Any]) -> dict[str, str]:
    if assignment.get("schema_version") != "1.0":
        raise ValueError("schema_version de asignación debe ser 1.0")
    pools = assignment.get("pools")
    if not isinstance(pools, dict) or set(pools) != set(POOLS):
        raise ValueError("pools debe definir exactamente A, B y emergency")
    expected: dict[str, str] = {}
    for pool in POOLS:
        ids = pools[pool]
        if not isinstance(ids, list) or any(not isinstance(value, str) or not value for value in ids):
            raise ValueError(f"pools.{pool} debe ser una lista de IDs no vacíos")
        for question_id in ids:
            if question_id in expected:
                raise ValueError(f"ID asignado a más de un pool: {question_id}")
            expected[question_id] = pool
    return expected


def without_blind_pool(rows: list[dict]) -> list[dict]:
    return [{key: value for key, value in row.items() if key != "blind_pool"} for row in rows]


def assert_authored_safe(path: Path, current_rows: list[dict], content_root: Path) -> None:
    if content_root.resolve() != DEFAULT_CONTENT_ROOT.resolve():
        return
    relative = path.resolve().relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise ValueError(f"{path}: authored-batch no rastreado; se rehúsa sobrescribir")
    head_rows = json.loads(result.stdout)
    if without_blind_pool(current_rows) != without_blind_pool(head_rows):
        raise ValueError(f"{path}: cambios authored ajenos a blind_pool; se rehúsa sobrescribir")


def remove_blind_pool_from_fragment(fragment: str, question_id: str, original_pool: str) -> str:
    encoded_pool = re.escape(json.dumps(original_pool))
    patterns = (
        rf',\s*"blind_pool"\s*:\s*{encoded_pool}(?=\s*\}})',
        rf'"blind_pool"\s*:\s*{encoded_pool}\s*,\s*',
    )
    for pattern in patterns:
        updated, count = re.subn(pattern, "", fragment, count=1)
        if count == 1:
            return updated
    row = json.loads(fragment)
    if row.get("blind_pool") is None:
        return fragment
    raise ValueError(f"blind_pool authored inesperado para {question_id}")


def render_authored_promotion(source_text: str, expected: Mapping[str, str]) -> bytes:
    decoder = json.JSONDecoder()
    cursor = source_text.find("[") + 1
    if cursor <= 0:
        raise ValueError("authored-batch sin arreglo superior")
    pieces: list[str] = []
    copied_until = 0
    while True:
        while cursor < len(source_text) and source_text[cursor].isspace():
            cursor += 1
        if cursor < len(source_text) and source_text[cursor] == "]":
            pieces.append(source_text[copied_until:])
            break
        pieces.append(source_text[copied_until:cursor])
        row, end = decoder.raw_decode(source_text, cursor)
        if not isinstance(row, dict) or "id" not in row:
            raise ValueError("registro authored inválido")
        fragment = source_text[cursor:end]
        question_id = str(row["id"])
        if question_id in expected:
            existing_pool = row.get("blind_pool")
            if existing_pool not in {expected[question_id], None}:
                raise ValueError(f"blind_pool authored inesperado para {question_id}")
            if existing_pool is not None:
                fragment = remove_blind_pool_from_fragment(fragment, question_id, expected[question_id])
        pieces.append(fragment)
        copied_until = end
        cursor = end
        while cursor < len(source_text) and source_text[cursor].isspace():
            cursor += 1
        if cursor < len(source_text) and source_text[cursor] == ",":
            pieces.append(source_text[copied_until : cursor + 1])
            copied_until = cursor + 1
            cursor += 1
    return "".join(pieces).encode("utf-8")


def authored_write_plan(content_root: Path, expected: Mapping[str, str]) -> dict[Path, bytes]:
    hits: dict[str, list[Path]] = defaultdict(list)
    sources: dict[Path, str] = {}
    for path in sorted((content_root / "authored-batches").glob("*.json")):
        source_text = path.read_text(encoding="utf-8")
        rows = json.loads(source_text)
        if not isinstance(rows, list):
            continue
        matching = [str(row["id"]) for row in rows if isinstance(row, dict) and str(row.get("id")) in expected]
        if not matching:
            continue
        assert_authored_safe(path, rows, content_root)
        sources[path] = source_text
        for question_id in matching:
            hits[question_id].append(path)
    invalid = sorted(question_id for question_id in expected if len(hits.get(question_id, [])) != 1)
    if invalid:
        raise ValueError(f"origen authored ambiguo o ausente: {invalid}")
    return {path: render_authored_promotion(source, expected) for path, source in sources.items()}


def source_units(content_root: Path) -> dict[str, dict]:
    index: dict[str, dict] = {}
    source_root = content_root / "source-packets"
    if not source_root.is_dir():
        return index
    for path in sorted(source_root.glob("*.json")):
        document = read_json(path)
        for row in document.get("units", []):
            index[str(row["source_unit_id"])] = row
    return index


def registry_row(row: Mapping[str, Any], original_pool: str, sources: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    source = sources.get(str(row["source_unit_id"]), {})
    material = row.get("material", source.get("work"))
    chapter = row.get("chapter", source.get("chapter"))
    if material is None or chapter is None:
        raise ValueError(f"material o capítulo ausente para {row['id']}")
    return {
        "question_id": row["id"],
        "fact_id": row["fact_id"],
        "original_pool": original_pool,
        "source_unit_id": row["source_unit_id"],
        "family": row["family"],
        "material": material,
        "chapter": chapter,
        "promoted_content_sha256": content_hash(row),
    }


def durable_write(path: Path, payload: bytes) -> None:
    with path.open("wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def recover_transaction(journal_path: Path) -> None:
    journal = read_json(journal_path)
    entries = journal.get("entries")
    if journal.get("contract") != "competitive-v11-promotion-transaction-v1" or not isinstance(entries, list):
        raise ValueError(f"journal de promoción inválido: {journal_path}")
    restore_temporaries: list[Path] = []
    try:
        for entry in entries:
            path = Path(entry["path"])
            backup = Path(entry["backup"])
            if entry["existed"]:
                if not backup.is_file():
                    raise OSError(f"backup de recuperación ausente: {backup}")
                restore = path.with_suffix(path.suffix + ".promotion.restore.tmp")
                durable_write(restore, backup.read_bytes())
                restore_temporaries.append(restore)
                os.replace(restore, path)
            else:
                path.unlink(missing_ok=True)
        journal_path.unlink()
        for entry in entries:
            Path(entry["backup"]).unlink(missing_ok=True)
            Path(entry["temporary"]).unlink(missing_ok=True)
    finally:
        for restore in restore_temporaries:
            restore.unlink(missing_ok=True)


def write_all_atomically(plan: Mapping[Path, bytes]) -> None:
    changed = {path: payload for path, payload in plan.items() if not path.exists() or path.read_bytes() != payload}
    if not changed:
        return
    transaction_root = Path(os.path.commonpath([str(path.parent.resolve()) for path in changed]))
    journal_path = transaction_root / ".blind-promotion-transaction.json"
    if journal_path.exists():
        recover_transaction(journal_path)

    entries: list[dict[str, Any]] = []
    journal_installed = False
    try:
        for path, payload in changed.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".promotion.tmp")
            backup = path.with_suffix(path.suffix + ".promotion.bak")
            temporary.unlink(missing_ok=True)
            backup.unlink(missing_ok=True)
            durable_write(temporary, payload)
            existed = path.exists()
            if existed:
                durable_write(backup, path.read_bytes())
            entries.append(
                {
                    "path": str(path.resolve()),
                    "temporary": str(temporary.resolve()),
                    "backup": str(backup.resolve()),
                    "existed": existed,
                }
            )
        journal_temporary = journal_path.with_suffix(journal_path.suffix + ".tmp")
        durable_write(
            journal_temporary,
            encode_json(
                {
                    "contract": "competitive-v11-promotion-transaction-v1",
                    "phase": "replacing",
                    "entries": entries,
                }
            ),
        )
        os.replace(journal_temporary, journal_path)
        journal_installed = True
        for entry in entries:
            os.replace(entry["temporary"], entry["path"])
        journal_path.unlink()
        journal_installed = False
        for entry in entries:
            Path(entry["backup"]).unlink(missing_ok=True)
    finally:
        if journal_installed:
            recover_transaction(journal_path)
        else:
            journal_path.with_suffix(journal_path.suffix + ".tmp").unlink(missing_ok=True)
            for entry in entries:
                Path(entry["temporary"]).unlink(missing_ok=True)
                Path(entry["backup"]).unlink(missing_ok=True)


def promote(content_root: Path, assignment_path: Path, registry_path: Path) -> dict[str, Any]:
    assignment = read_json(assignment_path)
    expected = assignment_index(assignment)
    questions, question_docs = load_documents(content_root / "questions", "id")
    reviews, review_docs = load_documents(content_root / "reviews", "question_id")
    if content_root.resolve() == DEFAULT_CONTENT_ROOT.resolve() and len(expected) != 250:
        raise ValueError("promotion requires exactly 250 unique presentations and facts")
    missing_questions = sorted(set(expected) - set(questions))
    missing_reviews = sorted(set(expected) - set(reviews))
    if missing_questions or missing_reviews:
        raise ValueError(f"preguntas o reviews ausentes: questions={missing_questions}, reviews={missing_reviews}")
    if len({questions[qid][1]["fact_id"] for qid in expected}) != len(expected):
        raise ValueError("promotion requires exactly 250 unique presentations and facts")

    authored_plan = authored_write_plan(content_root, expected)
    touched_questions: set[Path] = set()
    touched_reviews: set[Path] = set()
    registry_rows: list[dict[str, Any]] = []
    sources = source_units(content_root)
    for question_id, original_pool in sorted(expected.items()):
        question_path, row = questions[question_id]
        if row.get("blind_pool") not in {original_pool, None}:
            raise ValueError(f"unexpected blind_pool for {question_id}")
        row["blind_pool"] = None
        row["ai_review"] = {
            **row["ai_review"],
            "status": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": "gpt-5.6-sol-v10-blind-promotion",
        }
        review_path, review = reviews[question_id]
        review["content_sha256"] = content_hash(row)
        touched_questions.add(question_path)
        touched_reviews.add(review_path)
        registry_rows.append(registry_row(row, original_pool, sources))

    registry = {
        "contract": "competitive-v11-promoted-blind-v1",
        "presentation_count": len(expected),
        "fact_count": len({row["fact_id"] for row in registry_rows}),
        "presentations": registry_rows,
    }
    plan = {
        **authored_plan,
        **{path: encode_json(question_docs[path]) for path in touched_questions},
        **{path: encode_json(review_docs[path]) for path in touched_reviews},
        registry_path: encode_json(registry),
    }
    write_all_atomically(plan)
    all_questions = [row for rows in question_docs.values() for row in rows]
    return {
        "promoted_presentations": len(expected),
        "promoted_facts": len({row["fact_id"] for row in registry_rows}),
        "public_presentations": len(all_questions),
        "public_facts": len({row["fact_id"] for row in all_questions}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content-root", type=Path, default=DEFAULT_CONTENT_ROOT)
    parser.add_argument("--assignment", type=Path, default=DEFAULT_ASSIGNMENT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    try:
        report = promote(args.content_root, args.assignment, args.registry)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
