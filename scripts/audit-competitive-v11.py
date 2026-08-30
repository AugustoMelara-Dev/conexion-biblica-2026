#!/usr/bin/env python3
"""Audita contenido, evidencia, duplicados y hashes del corpus competitivo V11."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v11 import audit_corpus, content_hash, validate_question


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "questions",
    )
    parser.add_argument("--unit")
    parser.add_argument("--changed-only", action="store_true")
    args = parser.parse_args()
    content_root = args.source.parent

    source_units = {}
    for path in sorted((content_root / "source-packets").glob("*.json")):
        packet = read_json(path)
        for row in packet.get("units", []):
            if "source_quote" in row:
                source_units[row["source_unit_id"]] = row

    question_paths = (
        [args.source / f"{args.unit}.json"]
        if args.unit
        else sorted(args.source.glob("*.json"))
    )
    questions = [row for path in question_paths for row in read_json(path)]
    if args.changed_only:
        questions = [row for row in questions if "-V11-" in row["id"]]

    errors = {}
    for row in questions:
        row_errors = validate_question(row, source_units)
        if row_errors:
            errors[row["id"]] = row_errors
    corpus_violations = {
        key: rows for key, rows in audit_corpus(questions).items() if rows
    }

    review_paths = (
        [content_root / "reviews" / f"{args.unit}.json"]
        if args.unit
        else sorted((content_root / "reviews").glob("*.json"))
    )
    reviews = [row for path in review_paths for row in read_json(path)]
    review_by_id = {row["question_id"]: row for row in reviews}
    missing_reviews = [row["id"] for row in questions if row["id"] not in review_by_id]
    stale_reviews = [
        row["id"]
        for row in questions
        if row["id"] in review_by_id
        and review_by_id[row["id"]]["content_sha256"] != content_hash(row)
    ]

    family_counts = Counter(
        "selection" if row["family"].startswith("single_choice") else row["family"]
        for row in questions
    )
    result = {
        "questions": len(questions),
        "unique_facts": len({row["fact_id"] for row in questions}),
        "families": family_counts,
        "errors": errors,
        "corpus_violations": corpus_violations,
        "missing_reviews": missing_reviews,
        "stale_reviews": stale_reviews,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors or corpus_violations or missing_reviews or stale_reviews else 0


if __name__ == "__main__":
    raise SystemExit(main())
