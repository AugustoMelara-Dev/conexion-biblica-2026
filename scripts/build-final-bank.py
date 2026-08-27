#!/usr/bin/env python3
"""Construye los artefactos canónicos V7 desde el PDF y su caché OCR local."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.source_inventory import build_source_inventory
from scripts.lib.final_bank import BANK_ID, DISPLAY_NAME, validate_coverage, validate_gold_bank
from scripts.lib.final_editorial import (
    audit_final_bank,
    build_coverage_manifest,
    derive_atomic_facts,
    generate_gold_questions,
)


PDF_PATH = ROOT / "MaterialConexionBiblica (1).pdf"
OCR_PATH = ROOT / "scripts/source-cache/final-v7/ocr-pages.json"
OUTPUT_DIR = ROOT / "public/banks/final-2026"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ocr = json.loads(OCR_PATH.read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(PDF_PATH.read_bytes()).hexdigest()
    if ocr["source_sha256"] != source_hash:
        raise SystemExit("La caché OCR no corresponde al PDF local")
    inventory, issues = build_source_inventory(PDF_PATH, ocr["pages"])
    if issues["unresolved_count"]:
        raise SystemExit(
            f"La extracción conserva {issues['unresolved_count']} incidencias sin resolver"
        )
    facts, fact_rejections = derive_atomic_facts(inventory["units"])
    questions, question_rejections = generate_gold_questions(facts)
    coverage = build_coverage_manifest(inventory["units"], facts, questions)
    audit = audit_final_bank(facts, questions, coverage)
    contract_errors = validate_gold_bank(questions) + validate_coverage(coverage)
    audit_error_keys = (
        "ambiguous_gold_questions",
        "unsupported_gold_answers",
        "duplicate_gold_questions",
        "lexical_sequence_questions",
        "broken_true_false",
        "invalid_references",
        "external_knowledge_questions",
        "answer_length_leaks",
    )
    if contract_errors or any(audit[key] for key in audit_error_keys):
        raise SystemExit(
            json.dumps(
                {
                    "contract_errors": contract_errors[:50],
                    "audit_errors": {key: audit[key] for key in audit_error_keys},
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    facts_by_unit: dict[str, list[str]] = defaultdict(list)
    for fact in facts:
        facts_by_unit[fact["source_unit_id"]].append(fact["fact_id"])
    for unit in inventory["units"]:
        unit["fact_ids"] = facts_by_unit[unit["source_unit_id"]]

    public_facts = [
        {key: value for key, value in fact.items() if not key.startswith("_")}
        for fact in facts
    ]
    questions_dir = OUTPUT_DIR / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)
    chapter_counts = Counter(question["chapter"] for question in questions)
    shards = []
    for chapter in sorted(chapter_counts, key=lambda value: (value.startswith("PR"), int(re.search(r"\d+", value).group()))):
        rows = [question for question in questions if question["chapter"] == chapter]
        file_name = f"banks/final-2026/questions/{chapter}.json"
        write_json(questions_dir / f"{chapter}.json", rows)
        shards.append(
            {
                "chapter": chapter,
                "question_count": len(rows),
                "training_question_count": sum(
                    question["blind_pool"] is None for question in rows
                ),
                "questions_file": file_name,
            }
        )

    audit.update(
        {
            "fact_candidates_rejected": fact_rejections,
            "question_candidates_rejected": question_rejections,
            "new_editorial_questions": len(questions),
            "silver_repaired": 0,
        }
    )
    manifest = {
        "schema_version": "7.0",
        "bank_id": BANK_ID,
        "display_name": DISPLAY_NAME,
        "source": PDF_PATH.name,
        "source_sha256": source_hash,
        "source_units": inventory["source_units"],
        "daniel_verses": inventory["daniel_verses"],
        "pr_paragraphs": len(
            {
                (unit["page"], unit["paragraph"])
                for unit in inventory["units"]
                if unit["work"] == "Profetas y Reyes"
            }
        ),
        "pr_propositions": inventory["pr_propositions"],
        "unique_facts": len(facts),
        "gold_questions": len(questions),
        "average_variants_per_fact": round(len(questions) / len(facts), 2),
        "families": dict(Counter(question["family"] for question in questions)),
        "difficulty": dict(Counter(question["difficulty"] for question in questions)),
        "blind_pools": dict(
            Counter(fact["blind_pool"] for fact in questions if fact["blind_pool"])
        ),
        "coverage": {
            key: coverage[key]
            for key in (
                "covered_source_units",
                "uncovered_source_units",
                "fact_without_gold_question",
                "unmapped_source_units",
            )
        },
        "shards": shards,
    }

    write_json(OUTPUT_DIR / "source_inventory.json", inventory)
    write_json(OUTPUT_DIR / "source_extraction_issues.json", issues)
    write_json(OUTPUT_DIR / "fact_inventory.json", public_facts)
    write_json(OUTPUT_DIR / "coverage_manifest.json", coverage)
    write_json(OUTPUT_DIR / "editorial_audit.json", audit)
    write_json(OUTPUT_DIR / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "daniel_verses": inventory["daniel_verses"],
                "pr_propositions": inventory["pr_propositions"],
                "source_units": inventory["source_units"],
                "unresolved": issues["unresolved_count"],
                "facts": len(facts),
                "gold_questions": len(questions),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
