#!/usr/bin/env python3
"""Aplica una asignación ciega versionada sin modificar contenido editorial."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTENT_ROOT = ROOT / "content" / "competitive-v11"
DEFAULT_MANIFEST = DEFAULT_CONTENT_ROOT / "blind-assignment-v11.json"
POOLS = ("A", "B", "emergency")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v11 import content_hash


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def encode_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def encode_compact_rows(rows: list[dict]) -> bytes:
    body = ",\n".join(
        "  " + json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        for row in rows
    )
    return f"[\n{body}\n]\n".encode("utf-8")


def family_group(family: str) -> str:
    if family.startswith("single_choice"):
        return "selection"
    if family in {"fill_choice", "true_false"}:
        return family
    raise ValueError(f"familia no soportada: {family}")


def validate_manifest(manifest: dict[str, Any]) -> dict[str, str]:
    if manifest.get("schema_version") != "1.0":
        raise ValueError("schema_version de asignación debe ser 1.0")
    pools = manifest.get("pools")
    if not isinstance(pools, dict) or set(pools) != set(POOLS):
        raise ValueError("pools debe definir exactamente A, B y emergency")
    requirements = manifest.get("requirements")
    if not isinstance(requirements, dict) or set(requirements) != set(POOLS):
        raise ValueError("requirements debe definir exactamente A, B y emergency")

    assignment: dict[str, str] = {}
    for pool in POOLS:
        ids = pools[pool]
        if not isinstance(ids, list) or any(not isinstance(value, str) or not value for value in ids):
            raise ValueError(f"pools.{pool} debe ser una lista de IDs no vacíos")
        expected = requirements[pool]
        if expected.get("count") != len(ids):
            raise ValueError(f"conteo declarado incorrecto para pool {pool}")
        for question_id in ids:
            if question_id in assignment:
                raise ValueError(f"ID asignado a más de un pool: {question_id}")
            assignment[question_id] = pool
    return assignment


def tracked_authored_paths(
    content_root: Path, excluded_globs: list[str], approved_names: list[str]
) -> list[Path]:
    authored_root = content_root / "authored-batches"
    paths = [
        path
        for path in sorted(authored_root.glob("*.json"))
        if not any(fnmatch.fnmatch(path.name, pattern) for pattern in excluded_globs)
    ]
    if content_root.resolve() != DEFAULT_CONTENT_ROOT.resolve():
        return paths

    tracked = subprocess.run(
        ["git", "ls-files", "content/competitive-v11/authored-batches/*.json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    tracked_resolved = {(ROOT / value).resolve() for value in tracked}
    approved_resolved: set[Path] = set()
    for name in approved_names:
        if Path(name).name != name or not name.endswith(".json"):
            raise ValueError(f"nombre de authored-batch aprobado inválido: {name}")
        approved_path = (authored_root / name).resolve()
        if not approved_path.is_file():
            raise ValueError(f"authored-batch aprobado ausente: {name}")
        approved_resolved.add(approved_path)
    return [
        path
        for path in paths
        if path.resolve() in tracked_resolved or path.resolve() in approved_resolved
    ]


def collect_rows(paths: list[Path], id_key: str) -> tuple[dict[str, list[tuple[Path, dict]]], dict[Path, list[dict]]]:
    by_id: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    documents: dict[Path, list[dict]] = {}
    for path in paths:
        rows = read_json(path)
        if not isinstance(rows, list):
            raise ValueError(f"{path}: se esperaba una lista JSON")
        documents[path] = rows
        for row in rows:
            if not isinstance(row, dict) or id_key not in row:
                raise ValueError(f"{path}: registro sin {id_key}")
            by_id[str(row[id_key])].append((path, row))
    return by_id, documents


def without_blind_pool(rows: list[dict]) -> list[dict]:
    return [
        {key: value for key, value in row.items() if key != "blind_pool"}
        for row in rows
    ]


def collect_authored_rows(
    paths: list[Path], content_root: Path, approved_names: set[str]
) -> tuple[
    dict[str, list[tuple[Path, dict]]],
    dict[Path, list[dict]],
    dict[Path, str],
]:
    by_id: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    documents: dict[Path, list[dict]] = {}
    sources: dict[Path, str] = {}
    for path in paths:
        current_text = path.read_text(encoding="utf-8")
        current_rows = json.loads(current_text)
        source_text = current_text
        source_rows = current_rows
        if content_root.resolve() == DEFAULT_CONTENT_ROOT.resolve():
            relative = path.relative_to(ROOT).as_posix()
            result = subprocess.run(
                ["git", "show", f"HEAD:{relative}"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                encoding="utf-8",
            )
            if result.returncode == 0:
                source_text = result.stdout
                source_rows = json.loads(source_text)
                if without_blind_pool(current_rows) != without_blind_pool(source_rows):
                    raise ValueError(f"{path}: cambios authored ajenos a blind_pool; se rehúsa sobrescribir")
            elif path.name not in approved_names:
                raise ValueError(f"{path}: authored-batch no rastreado ni aprobado")
        if not isinstance(source_rows, list):
            raise ValueError(f"{path}: se esperaba una lista JSON")
        documents[path] = source_rows
        sources[path] = source_text
        for row in source_rows:
            if not isinstance(row, dict) or "id" not in row:
                raise ValueError(f"{path}: registro sin id")
            by_id[str(row["id"])].append((path, row))
    return by_id, documents, sources


def render_authored_assignment(source_text: str, assignment: dict[str, str]) -> bytes:
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
        desired_pool = assignment.get(str(row["id"]))
        existing_pool = row.get("blind_pool")
        if existing_pool is not None and existing_pool != desired_pool:
            raise ValueError(f"blind_pool previo inesperado en authored {row['id']}")
        if desired_pool is not None and "blind_pool" not in row:
            closing = len(fragment) - 1
            if fragment[closing] != "}":
                raise ValueError(f"objeto authored mal delimitado: {row['id']}")
            if "\n" in fragment:
                content_end = closing
                while content_end > 0 and fragment[content_end - 1].isspace():
                    content_end -= 1
                field_indent = "    "
                for line in fragment.splitlines()[1:]:
                    stripped = line.lstrip()
                    if stripped.startswith('"'):
                        field_indent = line[: len(line) - len(stripped)]
                        break
                fragment = (
                    fragment[:content_end]
                    + ",\n"
                    + field_indent
                    + json.dumps("blind_pool")
                    + ": "
                    + json.dumps(desired_pool)
                    + fragment[content_end:]
                )
            else:
                fragment = fragment[:-1] + ',"blind_pool":' + json.dumps(desired_pool) + "}"
        pieces.append(fragment)
        copied_until = end
        cursor = end
        while cursor < len(source_text) and source_text[cursor].isspace():
            cursor += 1
        if cursor < len(source_text) and source_text[cursor] == ",":
            pieces.append(source_text[copied_until : cursor + 1])
            copied_until = cursor + 1
            cursor += 1
            continue
    return "".join(pieces).encode("utf-8")


def validate_local_release_evidence(
    manifest: dict[str, Any], assignment_ids: set[str], content_root: Path
) -> None:
    if content_root.resolve() != DEFAULT_CONTENT_ROOT.resolve():
        return
    evidence = manifest.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("falta evidencia local de no exposición")
    if evidence.get("production_question_id_overlap") != 0:
        raise ValueError("la evidencia declara solape con producción")
    if evidence.get("public_local_question_id_overlap") != 0:
        raise ValueError("la evidencia declara solape con el banco público local")

    public_root = ROOT / "public" / "banks" / "final-2026" / "questions"
    public_ids: set[str] = set()
    for path in sorted(public_root.glob("*.json")):
        rows = read_json(path)
        public_ids.update(str(row.get("id")) for row in rows if isinstance(row, dict))
    overlap = sorted(assignment_ids & public_ids)
    if overlap:
        raise ValueError(f"IDs ya expuestos en banco público local: {overlap}")

    snapshot_rel = evidence.get("production_snapshot")
    snapshot = ROOT / str(snapshot_rel)
    if not snapshot.is_file():
        raise ValueError("no existe el snapshot local de producción declarado")
    snapshot_text = snapshot.read_text(encoding="utf-8")
    leaked = sorted(question_id for question_id in assignment_ids if question_id in snapshot_text)
    if leaked:
        raise ValueError(f"IDs presentes en snapshot local de producción: {leaked}")


def build_write_plan(manifest: dict[str, Any], content_root: Path) -> tuple[dict[Path, bytes], dict[str, Any]]:
    assignment = validate_manifest(manifest)
    assignment_ids = set(assignment)
    excluded = manifest.get("excluded_authored_batch_globs", ["wave-blind-*.json"])
    if not isinstance(excluded, list) or any(not isinstance(value, str) for value in excluded):
        raise ValueError("excluded_authored_batch_globs inválido")

    approved_names = manifest.get("approved_authored_batches", [])
    if not isinstance(approved_names, list) or any(not isinstance(value, str) for value in approved_names):
        raise ValueError("approved_authored_batches inválido")
    question_paths = sorted((content_root / "questions").glob("*.json"))
    review_paths = sorted((content_root / "reviews").glob("*.json"))
    authored_paths = tracked_authored_paths(content_root, excluded, approved_names)
    questions, question_docs = collect_rows(question_paths, "id")
    reviews, review_docs = collect_rows(review_paths, "question_id")
    authored, authored_docs, authored_sources = collect_authored_rows(
        authored_paths, content_root, set(approved_names)
    )

    for question_id in sorted(assignment_ids):
        if len(questions.get(question_id, [])) != 1:
            raise ValueError(f"pregunta ausente o ambigua: {question_id}")
        if len(reviews.get(question_id, [])) != 1:
            raise ValueError(f"review ausente o ambiguo: {question_id}")
        if len(authored.get(question_id, [])) != 1:
            raise ValueError(f"origen authored ambiguo o ausente: {question_id}")

    all_question_rows = [row for rows in question_docs.values() for row in rows]
    facts = Counter(str(row["fact_id"]) for row in all_question_rows)
    selected_rows = [questions[question_id][0][1] for question_id in assignment]
    selected_fact_ids = [str(row["fact_id"]) for row in selected_rows]
    if len(selected_fact_ids) != len(set(selected_fact_ids)):
        raise ValueError("la asignación contiene fact_id repetidos")
    repeated_presentations = sorted(fact_id for fact_id in selected_fact_ids if facts[fact_id] != 1)
    if repeated_presentations:
        raise ValueError(f"cada hecho ciego debe tener una sola presentación: {repeated_presentations}")

    requirements = manifest["requirements"]
    computed: dict[str, dict[str, Any]] = {}
    for pool in POOLS:
        pool_rows = [questions[question_id][0][1] for question_id in manifest["pools"][pool]]
        families = Counter(family_group(str(row["family"])) for row in pool_rows)
        normalized = {family: families[family] for family in ("selection", "fill_choice", "true_false")}
        expected_families = requirements[pool].get("families")
        if normalized != expected_families:
            raise ValueError(f"mezcla de familias incorrecta para {pool}: {normalized} != {expected_families}")
        computed[pool] = {"count": len(pool_rows), "families": normalized}

    validate_local_release_evidence(manifest, assignment_ids, content_root)

    changed_question_ids: set[str] = set()
    for row in all_question_rows:
        desired_pool = assignment.get(str(row["id"]))
        if row.get("blind_pool") != desired_pool:
            row["blind_pool"] = desired_pool
            changed_question_ids.add(str(row["id"]))
    for question_id in changed_question_ids:
        review_row = reviews[question_id][0][1]
        review_row["content_sha256"] = content_hash(questions[question_id][0][1])

    plan = {
        **{path: encode_json(value) for path, value in question_docs.items()},
        **{path: encode_json(value) for path, value in review_docs.items()},
        **{
            path: render_authored_assignment(authored_sources[path], assignment)
            for path in authored_docs
        },
    }
    return (plan, {"assigned": len(assignment), "pools": computed})


def write_plan_atomically(plan: dict[Path, bytes]) -> None:
    changed = {path: payload for path, payload in plan.items() if not path.exists() or path.read_bytes() != payload}
    temporary_paths: list[Path] = []
    try:
        for path, payload in changed.items():
            temporary = path.with_suffix(path.suffix + ".blind.tmp")
            temporary.write_bytes(payload)
            temporary_paths.append(temporary)
        for path in changed:
            os.replace(path.with_suffix(path.suffix + ".blind.tmp"), path)
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--content-root", type=Path, default=DEFAULT_CONTENT_ROOT)
    args = parser.parse_args()
    try:
        manifest = read_json(args.manifest)
        plan, report = build_write_plan(manifest, args.content_root)
        write_plan_atomically(plan)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
