#!/usr/bin/env python3
"""Captura el banco activo de producción sin modificarlo."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.production_snapshot_v11 import import_production_snapshot
from scripts.lib.production_snapshot_v11 import fetch_url_bytes
from scripts.lib.competitive_v11 import audit_corpus
from scripts.lib.import_seed_v11 import import_seed


def load_source_units(source_packet_dir: Path) -> dict[str, dict]:
    units: dict[str, dict] = {}
    for path in sorted(source_packet_dir.glob("*.json")):
        if path.name == "excluded-units.json":
            continue
        packet = json.loads(path.read_text(encoding="utf-8"))
        for row in packet["units"]:
            units[row["source_unit_id"]] = row
    return units


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def import_verified_seed(
    snapshot: dict,
    destination_root: Path,
    source_packet_dir: Path,
    false_mutation_overrides: dict[str, dict],
    editorial_overrides: dict[str, dict],
) -> dict:
    source_units = load_source_units(source_packet_dir)
    if len(source_units) != 1024:
        raise ValueError(f"Se esperaban 1,024 unidades útiles; se cargaron {len(source_units)}")
    resource_hashes = {
        row["path"]: row["sha256"]
        for row in snapshot["resources"]
        if row["kind"] == "question_shard"
    }
    base_url = snapshot["base_url"].rstrip("/")
    temporary = destination_root / ".seed-import.tmp"
    if temporary.exists():
        shutil.rmtree(temporary)
    question_temp = temporary / "questions"
    review_temp = temporary / "reviews"
    question_temp.mkdir(parents=True)
    review_temp.mkdir(parents=True)

    all_questions = []
    all_reviews = []
    required_override_ids: set[str] = set()
    imported_ids: set[str] = set()
    for shard in snapshot["manifest"]["shards"]:
        unit_code = shard["chapter"]
        resource_path = shard["questions_file"].lstrip("/")
        raw_bytes = fetch_url_bytes(f"{base_url}/{resource_path}")
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()
        if actual_hash != resource_hashes.get(resource_path):
            raise ValueError(f"{unit_code}: el shard cambió desde el snapshot")
        raw_questions = json.loads(raw_bytes.decode("utf-8"))
        for parent in raw_questions:
            imported_ids.add(str(parent["id"]))
            for variant in parent.get("presentation_variants", []):
                imported_ids.add(str(variant["id"]))
                if (
                    variant.get("correct_answer") == "Falso"
                    and not variant.get("false_mutation")
                ):
                    required_override_ids.add(str(variant["id"]))
        authored, reviews = import_seed(
            unit_code,
            raw_questions,
            source_units,
            false_mutation_overrides=false_mutation_overrides,
            editorial_overrides=editorial_overrides,
        )
        write_json(question_temp / f"{unit_code}.json", authored)
        write_json(review_temp / f"{unit_code}.json", reviews)
        all_questions.extend(authored)
        all_reviews.extend(reviews)

    if not required_override_ids.issubset(false_mutation_overrides):
        missing = sorted(required_override_ids - set(false_mutation_overrides))
        raise ValueError(f"Faltan mutaciones editoriales explícitas: {missing}")
    unused = sorted(set(false_mutation_overrides) - imported_ids)
    if unused:
        raise ValueError(f"El ledger contiene identificadores inexistentes: {unused}")
    unused_corrections = sorted(set(editorial_overrides) - imported_ids)
    if unused_corrections:
        raise ValueError(
            f"El ledger editorial contiene identificadores inexistentes: {unused_corrections}"
        )

    violations = audit_corpus(all_questions)
    active_violations = {key: rows for key, rows in violations.items() if rows}
    if active_violations:
        raise ValueError(f"La semilla incumple el contrato: {active_violations}")

    counts = Counter(row["role"] for row in all_questions)
    summary = {
        "schema_version": "11.0-authored-seed",
        "central_question_count": counts["central"],
        "presentation_variant_count": counts["variant"],
        "training_presentation_count": len(all_questions),
        "unique_facts": len({row["fact_id"] for row in all_questions}),
        "reviews": len(all_reviews),
        "units": len(snapshot["manifest"]["shards"]),
    }
    expected = snapshot["counts"]
    for key in (
        "central_question_count",
        "presentation_variant_count",
        "training_presentation_count",
    ):
        if summary[key] != expected[key]:
            raise ValueError(f"Conteo dispar en {key}: {summary[key]} != {expected[key]}")
    write_json(temporary / "seed-manifest.json", summary)

    questions_out = destination_root / "questions"
    reviews_out = destination_root / "reviews"
    if questions_out.exists():
        shutil.rmtree(questions_out)
    if reviews_out.exists():
        shutil.rmtree(reviews_out)
    question_temp.rename(questions_out)
    review_temp.rename(reviews_out)
    shutil.move(str(temporary / "seed-manifest.json"), destination_root / "seed-manifest.json")
    temporary.rmdir()
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="https://conexion-biblica-2026.vercel.app",
    )
    parser.add_argument(
        "--seed-root",
        type=Path,
        default=ROOT / "content" / "competitive-v11",
    )
    parser.add_argument(
        "--source-packets",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "source-packets",
    )
    parser.add_argument(
        "--false-mutations",
        type=Path,
        default=ROOT
        / "content"
        / "competitive-v11"
        / "import-false-mutations.json",
    )
    parser.add_argument(
        "--editorial-corrections",
        type=Path,
        default=ROOT
        / "content"
        / "competitive-v11"
        / "import-editorial-corrections.json",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "baseline-production.json",
    )
    args = parser.parse_args()

    try:
        snapshot = import_production_snapshot(
            args.base_url,
            args.destination,
        )
        false_mutation_overrides = json.loads(
            args.false_mutations.read_text(encoding="utf-8")
        )["mutations"]
        editorial_overrides = json.loads(
            args.editorial_corrections.read_text(encoding="utf-8")
        )["corrections"]
        seed_summary = import_verified_seed(
            snapshot,
            args.seed_root,
            args.source_packets,
            false_mutation_overrides,
            editorial_overrides,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                **snapshot["counts"],
                "destination": str(args.destination),
                "resources": len(snapshot["resources"]),
                "seed": seed_summary,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
