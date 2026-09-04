"""Compila evidencia editorial V18 sin tomar decisiones semánticas.

El compilador solo promueve una pregunta cuando el dictamen Sol, el intento
ciego y la respuesta almacenada convergen.  Nunca infiere ni rellena una
respuesta ausente.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".work" / "final-day-v18"
SOL_ITEM_FIELDS = {
    "audit_run_id", "question_id", "selected_option_index", "selected_option_text",
    "exact_supporting_phrase", "stem_fully_supported", "one_unambiguous_answer",
    "second_defensible_option", "second_defensible_text", "source_boundary",
    "option_analysis", "answer_length_giveaway", "grammar_giveaway",
    "precision_giveaway", "duplicate_or_superficial_variant", "real_difficulty",
    "decision", "specific_reason", "model", "reasoning_effort", "agent_id",
    "conversation_id", "conversation_id_kind", "reviewed_at",
    "input_content_sha256", "output_sha256",
}
BLIND_ITEM_FIELDS = {
    "audit_run_id", "question_id", "selected_option_index", "selected_option_text",
    "confidence_0_100", "second_option_index", "second_option_text",
    "initially_plausible_options_count", "solved_by", "clues_detected",
    "apparent_difficulty", "recommendation", "specific_reason", "model",
    "reasoning_effort", "agent_id", "conversation_id", "conversation_id_kind",
    "reviewed_at", "input_content_sha256", "output_sha256",
}


def _json_bytes(value: Any, *, sorted_keys: bool = False) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=sorted_keys,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha(value: Any, *, sorted_keys: bool = False) -> str:
    return hashlib.sha256(_json_bytes(value, sorted_keys=sorted_keys)).hexdigest()


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _same_multiset(left: list[str], right: list[str]) -> bool:
    return Counter(left) == Counter(right) and len(left) == len(right)


def adjudicate_item(stored: dict, dossier: dict, sol: dict, blind: dict) -> dict:
    """Apply mechanical gates; ``sol`` remains the sole semantic authority."""

    question_id = stored.get("id")
    blocking: list[str] = []
    status = "INVALID_OUTPUT"

    if not question_id or any(x.get("question_id") != question_id for x in (dossier, sol, blind)):
        blocking.append("question_id")
    stored_options = stored.get("options")
    correct_index = stored.get("correct_option")
    if (
        not isinstance(stored_options, list)
        or not isinstance(correct_index, int)
        or not (0 <= correct_index < len(stored_options))
        or "correct_answer" not in stored
    ):
        blocking.append("stored_answer_contract")
        stored_answer = None
    else:
        stored_answer = stored_options[correct_index]
        if stored.get("correct_answer") != stored_answer:
            blocking.append("stored")

    if (
        dossier.get("question") != stored.get("question")
        or not _same_multiset(dossier.get("options", []), stored_options or [])
        or dossier.get("source_unit_id") != stored.get("source_unit_id")
        or dossier.get("source_ref") != stored.get("source_ref")
        or dossier.get("exact_quote") != stored.get("source_quote")
    ):
        blocking.append("content_mutation")

    dossier_options = dossier.get("options", [])
    sol_index = sol.get("selected_option_index")
    blind_text = blind.get("selected_option_text")
    if (
        not isinstance(sol_index, int)
        or not (0 <= sol_index < len(dossier_options))
        or dossier_options[sol_index] != sol.get("selected_option_text")
    ):
        blocking.append("sol_selection_contract")
    sol_text = sol.get("selected_option_text")
    if sol_text != stored_answer:
        blocking.append("stored")
    if blind_text != sol_text:
        blocking.append("blind")
    blind_authority_ok = (
        blind.get("model") == "GPT-5.6 Luna"
        and str(blind.get("reasoning_effort", "")).lower() == "max"
        and bool(blind.get("agent_id"))
        and bool(blind.get("conversation_id"))
        and blind.get("agent_id") != sol.get("agent_id")
        and blind.get("conversation_id") != sol.get("conversation_id")
    )
    if not blind_authority_ok:
        blocking.append("blind_authority")
    if blind.get("recommendation") != "ACCEPT":
        blocking.append("blind_quality")

    analyses = sol.get("option_analysis")
    if not isinstance(analyses, list) or len(analyses) != len(dossier_options):
        blocking.append("option_analysis")
    elif any(not x.get("exact_reason") or x.get("text") != dossier_options[i] for i, x in enumerate(analyses)):
        blocking.append("option_analysis")

    material = dossier.get("material")
    if material == "Profetas y Reyes" and not str(dossier.get("question", "")).startswith(
        "Según Profetas y Reyes"
    ):
        blocking.append("pr_source_delimiter")

    decision = sol.get("decision")
    semantic_ok = (
        sol.get("model") == "GPT-5.6 Sol"
        and sol.get("reasoning_effort") == "medium"
        and bool(sol.get("agent_id"))
        and bool(sol.get("conversation_id"))
        and sol.get("stem_fully_supported") is True
        and sol.get("one_unambiguous_answer") is True
        and sol.get("second_defensible_option") is False
        and not sol.get("second_defensible_text")
    )
    if decision == "REJECT":
        status = "REJECTED"
    elif decision == "REWRITE":
        status = "REWRITE_REQUIRED"
    elif decision not in {"ACCEPT_COVERAGE", "ACCEPT_COMPETITIVE"}:
        blocking.append("sol_decision")
    elif not semantic_ok:
        blocking.append("sol_semantic_gate")
    elif blocking:
        status = "ANSWER_MISMATCH" if "stored" in blocking else (
            "INVALID_OUTPUT" if any(x in blocking for x in ("question_id", "stored_answer_contract", "content_mutation", "sol_selection_contract", "option_analysis", "blind_authority"))
            else "REWRITE_REQUIRED"
        )
    elif decision == "ACCEPT_COMPETITIVE":
        competitive_ok = (
            sol.get("real_difficulty") in {"HARD", "EXPERT"}
            and not sol.get("answer_length_giveaway")
            and not sol.get("grammar_giveaway")
            and not sol.get("precision_giveaway")
            and blind.get("initially_plausible_options_count", 0) >= 2
            and blind.get("solved_by") not in {"WORDING_CLUE", "GUESS"}
            and not blind.get("clues_detected")
            and blind.get("recommendation") == "ACCEPT"
        )
        if competitive_ok:
            status = "VERIFIED_COMPETITIVE_SOL"
        else:
            blocking.append("competitive_blind_quality")
            status = "REWRITE_REQUIRED"
    else:
        status = "VERIFIED_COVERAGE_SOL"

    return {
        "question_id": question_id,
        "fact_id": stored.get("fact_id"),
        "source_unit_id": stored.get("source_unit_id"),
        "chapter": stored.get("chapter"),
        "audit_status": status,
        "selected_answer": sol_text,
        "blocking_reasons": sorted(set(blocking)),
        "sol_conversation_id": sol.get("conversation_id"),
        "sol_model": sol.get("model"),
        "sol_reasoning_effort": sol.get("reasoning_effort"),
        "blind_conversation_id": blind.get("conversation_id"),
        "blind_model": blind.get("model"),
        "blind_reasoning_effort": str(blind.get("reasoning_effort", "")).lower(),
    }


def _load_questions(root: Path) -> dict[str, dict]:
    manifest = json.loads((root / "public/banks/final-2026/manifest.json").read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for shard in manifest["shards"]:
        rows = json.loads((root / "public" / shard["questions_file"]).read_text(encoding="utf-8"))
        for row in rows:
            if row["id"] in result:
                raise ValueError(f"ID duplicado: {row['id']}")
            result[row["id"]] = row
    return result


def _validate_agent_output(payload: dict, input_path: Path, expected_schema: str | set[str]) -> None:
    allowed_schemas = {expected_schema} if isinstance(expected_schema, str) else expected_schema
    if payload.get("schema_version") not in allowed_schemas:
        raise ValueError(f"schema inesperado en {input_path.name}")
    if payload.get("input_sha256") != _file_sha(input_path):
        raise ValueError(f"input_sha256 inválido en {input_path.name}")
    input_payload = json.loads(input_path.read_text(encoding="utf-8"))
    input_items = {item["question_id"]: item for item in input_payload.get("items", [])}
    required = SOL_ITEM_FIELDS if payload.get("schema_version") == "final-day-v18-sol-audit-1.0" else BLIND_ITEM_FIELDS
    if not isinstance(payload.get("items"), list) or len(payload["items"]) != len(input_items):
        raise ValueError(f"conteo de items inválido en {input_path.name}")
    for item in payload.get("items", []):
        item_fields = set(item)
        optional_fields = {"suggested_rewrite"} if required is SOL_ITEM_FIELDS else set()
        if not required.issubset(item_fields) or not item_fields.issubset(required | optional_fields):
            raise ValueError(f"contrato de campos inválido: {item.get('question_id')}")
        source = input_items.get(item.get("question_id"))
        index = item.get("selected_option_index")
        if source is None or not isinstance(index, int) or not (0 <= index < len(source["options"])):
            raise ValueError(f"selección inválida: {item.get('question_id')}")
        if item.get("selected_option_text") != source["options"][index]:
            raise ValueError(f"índice/texto desalineado: {item.get('question_id')}")
        candidate = dict(item)
        supplied = candidate.pop("output_sha256", None)
        # Early agents used sorted canonical keys; later agents preserved the
        # declared schema order.  Both are deterministic, explicit encodings.
        if not supplied or supplied not in {
            _sha(candidate),
            _sha(candidate, sorted_keys=True),
        }:
            raise ValueError(f"output_sha256 inválido: {item.get('question_id')}")


def compile_run(root: Path = ROOT, run_id: str = "v18-priority-audit") -> dict:
    dossier_dir = root / ".work/final-day-v18/dossiers" / run_id
    blind_dir = root / ".work/final-day-v18/blind" / run_id
    sol_dir = root / ".work/final-day-v18/audits" / run_id / "sol-medium"
    blind_result_dir = root / ".work/final-day-v18/blind-results" / run_id
    try:
        from scripts.prepare_final_day_v18_dossiers import verify_artifacts
    except ModuleNotFoundError:
        from prepare_final_day_v18_dossiers import verify_artifacts
    if not verify_artifacts(dossier_dir, blind_dir):
        raise ValueError(f"expedientes no publicables o transacción activa: {run_id}")
    questions = _load_questions(root)
    records: list[dict] = []
    incomplete_batches: list[str] = []
    invalid_batches: list[dict[str, str]] = []
    for dossier_path in sorted(dossier_dir.glob("batch-*.json")):
        batch_id = dossier_path.stem
        sol_path = sol_dir / dossier_path.name
        blind_input_path = blind_dir / dossier_path.name
        blind_result_path = blind_result_dir / dossier_path.name
        if not (sol_path.exists() and blind_input_path.exists() and blind_result_path.exists()):
            incomplete_batches.append(batch_id)
            continue
        dossier_payload = json.loads(dossier_path.read_text(encoding="utf-8"))
        blind_input = json.loads(blind_input_path.read_text(encoding="utf-8"))
        sol_payload = json.loads(sol_path.read_text(encoding="utf-8"))
        blind_payload = json.loads(blind_result_path.read_text(encoding="utf-8"))
        dossier_items = {x["question_id"]: x for x in dossier_payload["items"]}
        try:
            _validate_agent_output(sol_payload, dossier_path, "final-day-v18-sol-audit-1.0")
            _validate_agent_output(
                blind_payload,
                blind_input_path,
                {"final-day-v18-blind-1.0", "final-day-v18-blind-result-1.0"},
            )
        except ValueError as error:
            invalid_batches.append({"batch_id": batch_id, "reason": str(error)})
            records.extend(
                {
                    "question_id": question_id,
                    "fact_id": questions.get(question_id, {}).get("fact_id"),
                    "source_unit_id": item.get("source_unit_id"),
                    "chapter": item.get("chapter"),
                    "audit_status": "INVALID_OUTPUT",
                    "selected_answer": None,
                    "blocking_reasons": ["batch_integrity"],
                    "sol_conversation_id": None,
                    "blind_conversation_id": None,
                }
                for question_id, item in dossier_items.items()
            )
            continue
        sol_items = {x["question_id"]: x for x in sol_payload["items"]}
        blind_items = {x["question_id"]: x for x in blind_payload["items"]}
        blind_input_items = {x["question_id"]: x for x in blind_input["items"]}
        if not (dossier_items.keys() == sol_items.keys() == blind_items.keys() == blind_input_items.keys()):
            raise ValueError(f"desalineación de IDs en {batch_id}")
        for question_id, item in dossier_items.items():
            if not _same_multiset(item["options"], blind_input_items[question_id]["options"]):
                raise ValueError(f"opciones ciegas mutadas: {question_id}")
            records.append(
                adjudicate_item(
                    questions[question_id], item, sol_items[question_id], blind_items[question_id]
                )
            )
    if incomplete_batches:
        raise ValueError(
            f"auditoría incompleta para {run_id}: faltan {len(incomplete_batches)} lotes"
        )
    counts = Counter(record["audit_status"] for record in records)
    result = {
        "schema_version": "final-day-v18-integration-1.0",
        "audit_run_id": run_id,
        "records": records,
        "summary": {
            "integrated": len(records),
            "status_counts": dict(sorted(counts.items())),
            "incomplete_batches": incomplete_batches,
            "invalid_batches": invalid_batches,
        },
    }
    result["content_sha256"] = _sha(result, sorted_keys=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="v18-priority-audit")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = compile_run(ROOT, args.run_id)
    if args.write:
        _atomic_json(WORK / "integration" / f"{args.run_id}.json", result)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
