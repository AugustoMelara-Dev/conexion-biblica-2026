#!/usr/bin/env python3
"""Integra lotes cuya prosa ya fue redactada; solo compila, valida y cuenta."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.author_batch_v11 import compile_authored_batch
from scripts.lib.competitive_v11 import audit_corpus


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "authored-batches",
    )
    parser.add_argument("--pattern", default="pilot-100-*.json")
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument(
        "--content-root",
        type=Path,
        default=ROOT / "content" / "competitive-v11",
    )
    args = parser.parse_args()

    source_units = {}
    unit_by_source = {}
    for path in sorted((args.content_root / "source-packets").glob("*.json")):
        packet = read_json(path)
        if "units" not in packet or "unit" not in packet:
            continue
        for source in packet["units"]:
            source_units[source["source_unit_id"]] = source
            unit_by_source[source["source_unit_id"]] = packet["unit"]

    authored_inputs = []
    batch_paths = sorted(args.batch_dir.glob(args.pattern))
    for path in batch_paths:
        authored_inputs.extend(read_json(path))
    questions, reviews = compile_authored_batch(authored_inputs, source_units)

    existing_by_unit = {}
    reviews_by_unit = {}
    existing_ids = set()
    all_existing = []
    for path in sorted((args.content_root / "questions").glob("*.json")):
        rows = read_json(path)
        existing_by_unit[path.stem] = rows
        existing_ids.update(row["id"] for row in rows)
        all_existing.extend(rows)
    authored_ids = {row["id"] for row in questions}
    duplicates = sorted(existing_ids.intersection(authored_ids))
    if duplicates and not args.replace_existing:
        raise ValueError(f"IDs del lote ya existen: {duplicates}")
    if args.replace_existing:
        for unit in existing_by_unit:
            existing_by_unit[unit] = [
                row for row in existing_by_unit[unit] if row["id"] not in authored_ids
            ]
            reviews_by_unit.setdefault(unit, [])
        all_existing = [row for row in all_existing if row["id"] not in authored_ids]
    for path in sorted((args.content_root / "reviews").glob("*.json")):
        reviews_by_unit[path.stem] = read_json(path)
    if args.replace_existing:
        for unit in reviews_by_unit:
            reviews_by_unit[unit] = [
                row
                for row in reviews_by_unit[unit]
                if row["question_id"] not in authored_ids
            ]

    questions_to_add = defaultdict(list)
    reviews_to_add = defaultdict(list)
    review_by_id = {row["question_id"]: row for row in reviews}
    for question in questions:
        unit = unit_by_source[question["source_unit_id"]]
        questions_to_add[unit].append(question)
        reviews_to_add[unit].append(review_by_id[question["id"]])

    combined = [*all_existing, *questions]
    violations = {key: value for key, value in audit_corpus(combined).items() if value}
    if violations:
        raise ValueError(f"El lote incumple la auditoría global: {violations}")

    for unit, additions in questions_to_add.items():
        write_json_atomic(
            args.content_root / "questions" / f"{unit}.json",
            [*existing_by_unit[unit], *additions],
        )
        write_json_atomic(
            args.content_root / "reviews" / f"{unit}.json",
            [*reviews_by_unit[unit], *reviews_to_add[unit]],
        )

    family_counts = Counter(
        "selection" if row["family"].startswith("single_choice") else row["family"]
        for row in questions
    )
    print(
        json.dumps(
            {
                "batches": len(batch_paths),
                "questions_added": len(questions),
                "families": family_counts,
                "units": Counter(unit_by_source[row["source_unit_id"]] for row in questions),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
