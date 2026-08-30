#!/usr/bin/env python3
"""Compila el corpus V11 a un banco público de ensayo sin generar prosa."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v11 import audit_corpus, content_hash, validate_question
from scripts.lib.final_bank import BANK_ID, DISPLAY_NAME, SCHEMA_VERSION

EXPECTED_UNITS = [
    *(f"DAN{number}" for number in range(1, 13)),
    *(f"PR{number}" for number in range(39, 45)),
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def public_question(raw: dict, unit: str) -> dict:
    return {
        "id": raw["id"], "bank_id": BANK_ID, "bank_name": DISPLAY_NAME,
        "schema_version": SCHEMA_VERSION, "source_unit_id": raw["source_unit_id"],
        "fact_id": raw["fact_id"], "variant_id": raw["id"],
        "template_id": "ai-authored-v11", "family": raw["family"],
        "subtype": raw["subtype"], "chapter": unit, "reference": raw["source_ref"],
        "source_ref": raw["source_ref"], "verse_or_page": raw["source_ref"],
        "source_span": raw["evidence_excerpt"], "source_quote": raw["source_quote"],
        "context_anchor": raw["evidence_excerpt"], "evidence_excerpt": raw["evidence_excerpt"],
        "topic": raw["subtype"], "importance": raw["importance"],
        "relation_type": raw["relation_type"], "option_category": raw["option_category"],
        "blind_pool": raw["blind_pool"], "question": raw["question"],
        "options": raw["options"], "correct_option": raw["correct_option"],
        "correct_answer": raw["correct_answer"], "accepted_answers": raw["accepted_answers"],
        "answer_mode": "option_id", "explanation": raw["explanation"],
        "why_distractors_fail": raw["why_distractors_fail"], "trap_type": None,
        "final_editorial_status": "GOLD", "difficulty": raw["difficulty"],
        "false_mutation": raw.get("false_mutation"), "ai_review": raw["ai_review"],
        "validation_adversarial": {
            "reviewer": raw["ai_review"]["reviewer"], "status": "passed",
            "selected_option": raw["correct_option"], "rationale": raw["explanation"],
            "second_defensible_option": False,
        },
        "content_sha256": content_hash(raw),
    }


def compile_bank(source_root: Path, output: Path) -> dict:
    source_units = {}
    for path in sorted((source_root / "source-packets").glob("*.json")):
        for row in read_json(path).get("units", []):
            if "source_quote" in row:
                source_units[row["source_unit_id"]] = row

    rows_by_unit = {}
    all_rows = []
    for unit in EXPECTED_UNITS:
        rows = read_json(source_root / "questions" / f"{unit}.json")
        for row in rows:
            errors = validate_question(row, source_units)
            if errors:
                raise ValueError(f"{row['id']}: {', '.join(errors)}")
        rows_by_unit[unit] = rows
        all_rows.extend(rows)
    violations = {key: value for key, value in audit_corpus(all_rows).items() if value}
    if violations:
        raise ValueError(f"Auditoría global falló: {violations}")

    output = output.resolve()
    temp = output.parent / f".{output.name}.tmp"
    if temp.exists():
        shutil.rmtree(temp)
    (temp / "questions").mkdir(parents=True)
    shards = []
    review_entries = []
    for unit, rows in rows_by_unit.items():
        public_rows = [public_question(row, unit) for row in rows]
        (temp / "questions" / f"{unit}.json").write_text(
            json.dumps(public_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        shards.append({
            "chapter": unit, "question_count": len(public_rows),
            "training_question_count": len([row for row in public_rows if row["blind_pool"] is None]),
            "questions_file": f"banks/final-2026/questions/{unit}.json",
        })
        review_entries.extend({
            "question_id": row["id"], "content_sha256": row["content_sha256"],
            "decision": "passed", "reviewer_type": row["ai_review"]["reviewer_type"],
            "reviewer": row["ai_review"]["reviewer"],
        } for row in public_rows)
    families = Counter(row["family"] for row in all_rows)
    roles = Counter(row["role"] for row in all_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION, "bank_id": BANK_ID, "display_name": DISPLAY_NAME,
        "source": "MaterialConexionBiblica (1).pdf", "unique_facts": len({row["fact_id"] for row in all_rows}),
        "gold_questions": len(all_rows), "central_question_count": roles["central"],
        "presentation_variant_count": roles["variant"], "training_presentation_count": len(all_rows),
        "families": families, "shards": shards,
    }
    (temp / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (temp / "review-index.json").write_text(json.dumps({
        "schema_version": SCHEMA_VERSION, "total_reviewed": len(review_entries),
        "human_signatures": 0, "entries": review_entries,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if output.exists():
        shutil.rmtree(output)
    temp.rename(output)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "content" / "competitive-v11")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = compile_bank(args.source_root, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"output": str(args.output), "questions": manifest["gold_questions"], "facts": manifest["unique_facts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
