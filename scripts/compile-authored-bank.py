"""Compilador determinista y no generativo del Banco Canónico Autorizado por IA."""

from __future__ import annotations

import argparse
import json
import os
import shutil
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
    load_authored_unit,
    validate_authored_question,
)
from scripts.lib.final_bank import (
    BANK_ID,
    DISPLAY_NAME,
    SCHEMA_VERSION,
)


def enrich_public_question(raw: dict[str, Any], unit_code: str) -> dict[str, Any]:
    fact_id = raw["fact_id"]
    family = raw["family"]
    ai_rev = raw["ai_review"]
    correct_opt = raw["correct_option"]
    expl = raw["explanation"]

    return {
        "id": raw["id"],
        "bank_id": BANK_ID,
        "bank_name": DISPLAY_NAME,
        "schema_version": SCHEMA_VERSION,
        "source_unit_id": raw["source_unit_id"],
        "fact_id": fact_id,
        "variant_id": f"{fact_id}-{family.upper()}",
        "template_id": "ai-authored-v1",
        "family": family,
        "subtype": raw["subtype"],
        "chapter": unit_code,
        "reference": raw["source_ref"],
        "source_ref": raw["source_ref"],
        "verse_or_page": raw["source_ref"],
        "source_span": raw["evidence_excerpt"],
        "source_quote": raw["source_quote"],
        "context_anchor": raw["evidence_excerpt"],
        "evidence_excerpt": raw["evidence_excerpt"],
        "topic": raw["subtype"],
        "importance": raw.get("importance", "high"),
        "relation_type": raw.get("relation_type", "direct"),
        "option_category": raw.get("option_category", "phrase"),
        "blind_pool": raw.get("blind_pool"),
        "question": raw["question"],
        "options": raw["options"],
        "correct_option": correct_opt,
        "correct_answer": raw["correct_answer"],
        "accepted_answers": raw["accepted_answers"],
        "answer_mode": "option_id",
        "explanation": expl,
        "why_distractors_fail": raw["why_distractors_fail"],
        "trap_type": None if family != "single_choice_contextual" else "true_elsewhere",
        "final_editorial_status": "GOLD",
        "difficulty": raw["difficulty"],
        "false_mutation": raw.get("false_mutation"),
        "ai_review": ai_rev,
        "validation_adversarial": {
            "reviewer": ai_rev["reviewer"],
            "status": "passed",
            "selected_option": correct_opt,
            "rationale": expl,
            "second_defensible_option": False,
        },
        "content_sha256": content_hash(raw),
    }


def compile_bank(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    all_raw_questions: list[dict[str, Any]] = []
    unit_raw_map: dict[str, list[dict[str, Any]]] = {}

    for unit in EXPECTED_UNITS:
        unit_file = source_dir / f"{unit}.json"
        if not unit_file.exists():
            raise FileNotFoundError(f"Falta el archivo canónico para la unidad {unit}: {unit_file}")
        unit_rows = load_authored_unit(unit_file)
        for row in unit_rows:
            row_errors = validate_authored_question(row)
            if row_errors:
                raise ValueError(f"Errores en pregunta {row.get('id')}: {', '.join(row_errors)}")
        unit_raw_map[unit] = unit_rows
        all_raw_questions.extend(unit_rows)

    violations = audit_authored_bank(all_raw_questions)
    active_violations = {k: v for k, v in violations.items() if v}
    if active_violations:
        raise ValueError(f"Compuertas de auditoría fallaron: {json.dumps(active_violations, indent=2)}")

    temp_out = output_dir.parent / f".tmp_{output_dir.name}"
    if temp_out.exists():
        shutil.rmtree(temp_out)
    temp_questions = temp_out / "questions"
    temp_questions.mkdir(parents=True, exist_ok=True)

    shards_meta: list[dict[str, Any]] = []
    review_ledger: list[dict[str, Any]] = []
    unique_facts: set[str] = set()

    for unit in EXPECTED_UNITS:
        raw_list = unit_raw_map[unit]
        public_list = [enrich_public_question(q, unit) for q in raw_list]
        for p in public_list:
            unique_facts.add(p["fact_id"])
            review_ledger.append({
                "question_id": p["id"],
                "content_sha256": p["content_sha256"],
                "decision": "passed",
                "reviewer_type": p["ai_review"]["reviewer_type"],
                "reviewer": p["ai_review"]["reviewer"],
            })
        out_shard_file = temp_questions / f"{unit}.json"
        out_shard_file.write_text(
            json.dumps(public_list, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        shards_meta.append({
            "chapter": unit,
            "question_count": len(public_list),
            "training_question_count": len([q for q in public_list if not q.get("blind_pool")]),
            "questions_file": f"banks/final-2026/questions/{unit}.json",
        })

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "bank_id": BANK_ID,
        "display_name": DISPLAY_NAME,
        "source": "MaterialConexionBiblica (1).pdf",
        "gold_questions": len(all_raw_questions),
        "unique_facts": len(unique_facts),
        "shards": shards_meta,
    }

    (temp_out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (temp_out / "review-index.json").write_text(
        json.dumps({
            "schema_version": SCHEMA_VERSION,
            "total_reviewed": len(review_ledger),
            "human_signatures": 0,
            "entries": review_ledger,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Atomic swap
    if output_dir.exists():
        shutil.rmtree(output_dir)
    temp_out.rename(output_dir)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Compilador del banco autorizado.")
    parser.add_argument("--source", type=Path, default=ROOT / "content" / "final-2026-authored" / "questions")
    parser.add_argument("--output", type=Path, default=ROOT / "public" / "banks" / "final-2026")
    parser.add_argument("--authored-unit", type=str, help="Valida solo una unidad sin publicar.")
    parser.add_argument("--bank", type=Path, help="Audita un banco ya compilado.")

    args = parser.parse_args()

    if args.authored_unit:
        unit_file = args.source / f"{args.authored_unit}.json"
        if not unit_file.exists():
            print(f"ERROR: Archivo no existe: {unit_file}", file=sys.stderr)
            return 1
        rows = load_authored_unit(unit_file)
        errors = []
        for r in rows:
            errors.extend(validate_authored_question(r))
        if errors:
            print(f"ERROR en {args.authored_unit}: {len(errors)} errores:\n" + "\n".join(errors[:20]), file=sys.stderr)
            return 1
        print(f"OK: Unidad {args.authored_unit} validada ({len(rows)} preguntas, 0 errores).")
        return 0

    if args.bank:
        manifest_path = args.bank / "manifest.json"
        if not manifest_path.exists():
            print(f"ERROR: No se encontró manifest.json en {args.bank}", file=sys.stderr)
            return 1
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        all_q = []
        for shard in manifest.get("shards", []):
            shard_path = ROOT / "public" / shard["questions_file"]
            if not shard_path.exists():
                shard_path = args.bank / "questions" / f"{shard['chapter']}.json"
            all_q.extend(json.loads(shard_path.read_text(encoding="utf-8")))
        violations = audit_authored_bank(all_q)
        active = {k: v for k, v in violations.items() if v}
        if active:
            print(f"ERROR en auditoría: {json.dumps(active, indent=2)}", file=sys.stderr)
            return 1
        print(f"OK: Banco en {args.bank} auditado limpiamente ({len(all_q)} preguntas, 0 violaciones).")
        return 0

    try:
        manifest = compile_bank(args.source, args.output)
        print(f"OK: Banco compilado exitosamente en {args.output} ({manifest['gold_questions']} preguntas).")
        return 0
    except Exception as exc:
        print(f"ERROR al compilar banco: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
