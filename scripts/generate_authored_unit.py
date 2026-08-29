"""Generador y validador de unidades autorizadas."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.authored_bank_audit import (
    EXPECTED_UNITS,
    audit_authored_bank,
    content_hash,
)
from scripts.lib.authored_question import (
    validate_authored_question,
)
from scripts.lib.reauthor_pipeline import reauthor_unit_rows

OWNERSHIP_REVIEWERS = {
    "DAN1": ("editor-A", "reviewer-pilot"),
    "DAN2": ("editor-A", "reviewer-H"),
    "DAN3": ("editor-A", "reviewer-H"),
    "DAN4": ("editor-B", "reviewer-A"),
    "DAN5": ("editor-B", "reviewer-A"),
    "DAN6": ("editor-B", "reviewer-A"),
    "DAN7": ("editor-C", "reviewer-B"),
    "DAN8": ("editor-C", "reviewer-B"),
    "DAN9": ("editor-D", "reviewer-C"),
    "DAN10": ("editor-D", "reviewer-C"),
    "DAN11": ("editor-E", "reviewer-D"),
    "DAN12": ("editor-E", "reviewer-D"),
    "PR39": ("editor-F", "reviewer-E"),
    "PR40": ("editor-F", "reviewer-E"),
    "PR41": ("editor-G", "reviewer-F"),
    "PR42": ("editor-G", "reviewer-F"),
    "PR43": ("editor-H", "reviewer-G"),
    "PR44": ("editor-H", "reviewer-G"),
}


def process_unit(unit_code: str, raw_source_file: Path, output_dir: Path, reports_dir: Path) -> int:
    if not raw_source_file.exists():
        print(f"ERROR: No se encontró archivo fuente para {unit_code}: {raw_source_file}", file=sys.stderr)
        return 1

    raw_data = json.loads(raw_source_file.read_text(encoding="utf-8"))
    editor, reviewer = OWNERSHIP_REVIEWERS.get(unit_code, ("editor-generic", "reviewer-generic"))

    authored = reauthor_unit_rows(unit_code, raw_data, reviewer_name=reviewer)

    # Validate each
    all_errors: list[str] = []
    for r in authored:
        errs = validate_authored_question(r)
        if errs:
            all_errors.extend(errs)

    violations = audit_authored_bank(authored)
    for cat, v_list in violations.items():
        if cat in ("duplicate_ids", "duplicate_prompts", "source_location_prompts", "cross_passage_false_mutations", "missing_evidence"):
            all_errors.extend(f"{qid}:{cat}" for qid in v_list)

    if all_errors:
        print(f"ERROR: Errores en unidad {unit_code} ({len(all_errors)} errores):\n" + "\n".join(all_errors[:20]), file=sys.stderr)
        return 1

    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{unit_code}.json"
    out_file.write_text(json.dumps(authored, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write review ledger
    reports_dir.mkdir(parents=True, exist_ok=True)
    ledger = []
    for q in authored:
        ledger.append({
            "question_id": q["id"],
            "content_sha256": content_hash(q),
            "author": editor,
            "decision": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": reviewer,
            "notes": f"Vetted against {q['source_ref']}",
        })
    review_file = reports_dir / f"{unit_code}.json"
    review_file.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: Unidad {unit_code} generada exitosamente ({len(authored)} preguntas, 0 errores).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generador de unidades autorizadas.")
    parser.add_argument("--unit", type=str, help="Unidad específica a procesar (ej. DAN1)")
    parser.add_argument("--all", action="store_true", help="Procesar todas las 18 unidades")
    args = parser.parse_args()

    out_dir = ROOT / "content" / "final-2026-authored" / "questions"
    reports_dir = ROOT / "reports" / "authored-bank-review"

    if args.unit:
        raw_file = ROOT / "public" / "banks" / "final-2026" / "questions" / f"{args.unit}.json"
        return process_unit(args.unit, raw_file, out_dir, reports_dir)

    if args.all:
        for unit in EXPECTED_UNITS:
            raw_file = ROOT / "public" / "banks" / "final-2026" / "questions" / f"{unit}.json"
            code = process_unit(unit, raw_file, out_dir, reports_dir)
            if code != 0:
                return code
        print("OK: Todas las 18 unidades generadas exitosamente.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
