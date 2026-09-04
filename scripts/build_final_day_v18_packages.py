"""Construye paquetes V18 exclusivamente desde resultados integrados."""

from __future__ import annotations

import json
import os
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
VERIFIED = {"VERIFIED_COVERAGE_SOL", "VERIFIED_COMPETITIVE_SOL"}
EVIDENCE_FIELDS = {
    "question_id", "chapter", "fact_id", "source_unit_id", "selected_answer",
    "audit_status", "blocking_reasons",
    "sol_model", "sol_reasoning_effort", "sol_conversation_id",
    "blind_model", "blind_reasoning_effort", "blind_conversation_id",
}


def _chapter_key(value: str) -> tuple[int, int]:
    return (0 if value.startswith("PR") else 1, int("".join(filter(str.isdigit, value)) or 0))


def _distinct_facts_first(rows: list[dict]) -> list[dict]:
    ordered = sorted(rows, key=lambda row: (_chapter_key(row["chapter"]), row["question_id"]))
    seen: set[str] = set()
    first: list[dict] = []
    repeats: list[dict] = []
    for row in ordered:
        fact = row.get("fact_id") or row["question_id"]
        (repeats if fact in seen else first).append(row)
        seen.add(fact)
    return first + repeats


def build_packages(records: Iterable[dict]) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    invalid_records: list[str] = []
    for row in records:
        question_id = str(row.get("question_id") or "<missing>")
        if (
            not EVIDENCE_FIELDS.issubset(row)
            or row.get("sol_model") != "GPT-5.6 Sol"
            or row.get("sol_reasoning_effort") != "medium"
            or row.get("blind_model") != "GPT-5.6 Luna"
            or row.get("blind_reasoning_effort") != "max"
            or not row.get("sol_conversation_id")
            or not row.get("blind_conversation_id")
            or row.get("sol_conversation_id") == row.get("blind_conversation_id")
            or not row.get("source_unit_id")
            or not row.get("selected_answer")
        ):
            invalid_records.append(question_id)
            continue
        grouped[row["question_id"]].append(row)

    conflicts: list[str] = []
    accepted: list[dict] = []
    for question_id, rows in grouped.items():
        statuses = {row["audit_status"] for row in rows}
        verified_statuses = statuses & VERIFIED
        identities = {
            (
                row.get("chapter"),
                row.get("fact_id"),
                row.get("source_unit_id"),
                row.get("selected_answer"),
            )
            for row in rows
        }
        if len(statuses) != 1 or len(verified_statuses) != 1 or len(identities) != 1:
            if verified_statuses:
                conflicts.append(question_id)
            continue
        if any(row.get("blocking_reasons") != [] for row in rows):
            invalid_records.append(question_id)
            continue
        accepted.append(rows[0])

    coverage = _distinct_facts_first(accepted)[:1000]
    competitive = _distinct_facts_first(
        [row for row in accepted if row["audit_status"] == "VERIFIED_COMPETITIVE_SOL"]
    )[:300]
    repair = _distinct_facts_first(
        [row for row in accepted if row["chapter"] in {"DAN9", "DAN12"}]
    )

    def package(target: int | None, rows: list[dict]) -> dict:
        chapters = Counter(row["chapter"] for row in rows)
        return {
            "target_count": target,
            "actual_count": len(rows),
            "complete": target is not None and len(rows) == target,
            "question_ids": [row["question_id"] for row in rows],
            "distinct_facts": len({row.get("fact_id") or row["question_id"] for row in rows}),
            "by_chapter": dict(sorted(chapters.items(), key=lambda item: _chapter_key(item[0]))),
        }

    return {
        "schema_version": "final-day-v18-packages-1.0",
        "authority": "Sol Medium textual audit + blind competitor + deterministic integration",
        "conflicts": sorted(conflicts),
        "invalid_records": sorted(invalid_records),
        "verified_question_count": len(accepted),
        "audit_status_by_question_id": {
            row["question_id"]: row["audit_status"]
            for row in sorted(accepted, key=lambda item: item["question_id"])
        },
        "packages": {
            "ULTIMO_DIA_COBERTURA_1000": package(1000, coverage),
            "ULTIMO_DIA_ADVERSARIAL_300": package(300, competitive),
            "REPARACION_PERSONAL": package(None, repair),
        },
    }


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def main() -> int:
    try:
        from scripts.compile_final_day_v18 import compile_run
    except ModuleNotFoundError:  # ejecución directa: sys.path apunta a scripts/
        from compile_final_day_v18 import compile_run

    records: list[dict] = []
    # Priority was regenerated under a stricter delimiter contract and is not
    # publishable until every new batch is re-audited.  Never consume a partial
    # run; the safe-first run is complete and independently verifiable.
    for run_id in ("v18-safe-first",):
        payload = compile_run(ROOT, run_id)
        supplied_hash = payload.pop("content_sha256", None)
        computed_hash = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if (
            payload.get("schema_version") != "final-day-v18-integration-1.0"
            or not payload.get("audit_run_id")
            or supplied_hash != computed_hash
        ):
            raise ValueError(f"integración no confiable: {run_id}")
        records.extend(payload["records"])
    result = build_packages(records)
    public_path = ROOT / "public/banks/final-2026/packages-v18.json"
    _atomic_write(public_path, json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    coverage = result["packages"]["ULTIMO_DIA_COBERTURA_1000"]["question_ids"]
    competitive = result["packages"]["ULTIMO_DIA_ADVERSARIAL_300"]["question_ids"]
    repair = result["packages"]["REPARACION_PERSONAL"]["question_ids"]
    statuses = result["audit_status_by_question_id"]
    ts = (
        "// Auto-generated by scripts/build_final_day_v18_packages.py - DO NOT EDIT\n"
        f"export const V18_VERIFIED_COVERAGE_IDS = new Set<string>({json.dumps(coverage, ensure_ascii=False)})\n"
        f"export const V18_VERIFIED_COMPETITIVE_IDS = new Set<string>({json.dumps(competitive, ensure_ascii=False)})\n"
        f"export const V18_PERSONAL_REPAIR_IDS = new Set<string>({json.dumps(repair, ensure_ascii=False)})\n"
        "export type V18AuditStatus = 'VERIFIED_COVERAGE_SOL' | 'VERIFIED_COMPETITIVE_SOL'\n"
        f"export const V18_AUDIT_STATUS_BY_ID: Readonly<Record<string, V18AuditStatus>> = {json.dumps(statuses, ensure_ascii=False)}\n"
        "export const V18_PACKAGE_COUNTS: Readonly<Record<'coverage' | 'competitive' | 'repair', number>> = {\n"
        f"  coverage: {len(coverage)},\n  competitive: {len(competitive)},\n  repair: {len(repair)},\n"
        "}\n"
    )
    _atomic_write(ROOT / "src/data/final-day-v18.ts", ts)
    print(json.dumps({name: value["actual_count"] for name, value in result["packages"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
