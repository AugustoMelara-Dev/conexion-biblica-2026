#!/usr/bin/env python3
"""Promote the independently reviewed v13 increment into the public v11 bank."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v11 import audit_corpus, validate_question  # noqa: E402
from scripts.lib.competitive_v13 import (  # noqa: E402
    APPLIED_SCHEMA,
    canonical_hash,
    normalize_prompt,
)


EXPECTED_UNITS = (
    *(f"DAN{number}" for number in range(1, 13)),
    *(f"PR{number}" for number in range(39, 45)),
)
BASE_QUESTION_COUNT = 2468
BASE_FACT_COUNT = 2217
APPROVED_INCREMENT_COUNT = 262
FINAL_QUESTION_COUNT = BASE_QUESTION_COUNT + APPROVED_INCREMENT_COUNT
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
UNIT_PREFIX_PATTERN = re.compile(r"^(DAN(?:1[0-2]|[1-9])|PR(?:3[9]|4[0-4]))(?:-|$)")


class PromotionError(ValueError):
    """Raised when a reviewed checkpoint cannot be safely promoted."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_promotion_paths(base_root: Path, output: Path) -> tuple[Path, Path]:
    base = Path(base_root).resolve()
    destination = Path(output).resolve()
    if base == destination or base in destination.parents or destination in base.parents:
        raise PromotionError("promotion output must not overlap the canonical base")
    return base, destination


def _load_compiler():
    path = ROOT / "scripts" / "compile-competitive-v11.py"
    spec = importlib.util.spec_from_file_location("competitive_v11_public_compiler", path)
    if spec is None or spec.loader is None:
        raise PromotionError(f"cannot load public compiler: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_checkpoint_envelope(checkpoint: Mapping[str, Any]) -> None:
    if checkpoint.get("schema_version") != APPLIED_SCHEMA:
        raise PromotionError("checkpoint schema mismatch")
    if checkpoint.get("release") != 2:
        raise PromotionError("checkpoint release must be 2")
    stored_hash = checkpoint.get("release_sha256")
    payload = {
        key: value for key, value in checkpoint.items() if key != "release_sha256"
    }
    if not isinstance(stored_hash, str) or stored_hash != canonical_hash(payload):
        raise PromotionError("release_sha256 mismatch")

    approved = checkpoint.get("approved")
    pending = checkpoint.get("pending")
    batches = checkpoint.get("batches")
    if not isinstance(approved, list) or not isinstance(pending, list):
        raise PromotionError("checkpoint approved and pending must be lists")
    if len(approved) != APPROVED_INCREMENT_COUNT:
        raise PromotionError(
            f"approved increment count must be {APPROVED_INCREMENT_COUNT}, got {len(approved)}"
        )
    if not isinstance(batches, list) or not batches:
        raise PromotionError("checkpoint batches must be a non-empty list")

    batch_ids: set[str] = set()
    approved_total = 0
    pending_total = 0
    for index, batch in enumerate(batches):
        if not isinstance(batch, Mapping):
            raise PromotionError(f"batch {index} must be a mapping")
        batch_id = batch.get("batch_id")
        packet_hash = batch.get("blind_packet_sha256")
        reviewer = batch.get("reviewer")
        approved_count = batch.get("approved")
        pending_count = batch.get("pending")
        if not isinstance(batch_id, str) or not batch_id or batch_id in batch_ids:
            raise PromotionError(f"batch {index} has invalid or duplicate batch_id")
        batch_ids.add(batch_id)
        if not isinstance(packet_hash, str) or not SHA256_PATTERN.fullmatch(packet_hash):
            raise PromotionError(f"batch {batch_id} has invalid packet hash")
        if not isinstance(reviewer, str) or not reviewer:
            raise PromotionError(f"batch {batch_id} has invalid reviewer")
        if (
            isinstance(approved_count, bool)
            or not isinstance(approved_count, int)
            or approved_count < 0
        ):
            raise PromotionError(f"batch {batch_id} has invalid approved count")
        if (
            isinstance(pending_count, bool)
            or not isinstance(pending_count, int)
            or pending_count < 0
        ):
            raise PromotionError(f"batch {batch_id} has invalid pending count")
        approved_total += approved_count
        pending_total += pending_count
    if approved_total != len(approved):
        raise PromotionError("batch approved total does not bind checkpoint rows")
    if pending_total != len(pending):
        raise PromotionError("batch pending total does not bind checkpoint rows")


def _load_base(base_root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    questions_dir = base_root / "questions"
    source_dir = base_root / "source-packets"
    rows_by_unit: dict[str, list[dict[str, Any]]] = {}
    all_rows: list[dict[str, Any]] = []
    for unit in EXPECTED_UNITS:
        value = read_json(questions_dir / f"{unit}.json")
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            raise PromotionError(f"base questions for {unit} must be a list of mappings")
        rows_by_unit[unit] = value
        all_rows.extend(value)
    if len(all_rows) != BASE_QUESTION_COUNT:
        raise PromotionError(
            f"base question count must be {BASE_QUESTION_COUNT}, got {len(all_rows)}"
        )
    if len({str(row.get("fact_id") or "") for row in all_rows}) != BASE_FACT_COUNT:
        raise PromotionError(f"base fact count must be {BASE_FACT_COUNT}")

    source_units: dict[str, dict[str, Any]] = {}
    for path in sorted(source_dir.glob("*.json")):
        value = read_json(path)
        if not isinstance(value, Mapping):
            continue
        for row in value.get("units", []):
            if not isinstance(row, dict) or "source_quote" not in row:
                continue
            source_id = row.get("source_unit_id")
            if not isinstance(source_id, str) or not source_id:
                raise PromotionError(f"invalid source unit in {path.name}")
            if source_id in source_units:
                raise PromotionError(f"duplicate source_unit_id: {source_id}")
            source_units[source_id] = row
    if not source_units:
        raise PromotionError("base source packets contain no source units")
    return rows_by_unit, source_units


def prepare_promotion(
    base_root: Path,
    checkpoint: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Validate and return merged source rows grouped by public shard."""

    if not isinstance(checkpoint, Mapping):
        raise PromotionError("checkpoint must be a mapping")
    _validate_checkpoint_envelope(checkpoint)
    rows_by_unit, source_units = _load_base(Path(base_root))
    base_rows = [row for unit in EXPECTED_UNITS for row in rows_by_unit[unit]]

    base_ids = [str(row.get("id") or "") for row in base_rows]
    if not all(base_ids) or len(set(base_ids)) != len(base_ids):
        raise PromotionError("base question ids must be present and unique")
    base_prompts = [normalize_prompt(str(row.get("question") or "")) for row in base_rows]
    if not all(base_prompts) or len(set(base_prompts)) != len(base_prompts):
        raise PromotionError("base normalized prompts must be present and unique")

    base_fact_sources: dict[str, str] = {}
    for row in base_rows:
        fact_id = str(row.get("fact_id") or "")
        source_id = str(row.get("source_unit_id") or "")
        if not fact_id or not source_id:
            raise PromotionError("base fact_id and source_unit_id are required")
        previous = base_fact_sources.setdefault(fact_id, source_id)
        if previous != source_id:
            raise PromotionError(f"base fact/source mismatch: {fact_id}")

    approved = checkpoint["approved"]
    approved_ids: set[str] = set()
    approved_prompts: set[str] = set()
    approved_facts: set[str] = set()
    merged = {unit: [deepcopy(row) for row in rows_by_unit[unit]] for unit in EXPECTED_UNITS}
    base_id_set = set(base_ids)
    base_prompt_set = set(base_prompts)

    for index, raw in enumerate(approved):
        if not isinstance(raw, Mapping):
            raise PromotionError(f"approved row {index} must be a mapping")
        row = deepcopy(dict(raw))
        if any("blind" in str(key).casefold() for key in row):
            raise PromotionError(f"approved row {index} contains blind metadata")
        question_id = str(row.get("id") or "")
        if not question_id or question_id in base_id_set or question_id in approved_ids:
            raise PromotionError(f"question id collision: {question_id or '<missing>'}")
        approved_ids.add(question_id)

        prompt = normalize_prompt(str(row.get("question") or ""))
        if not prompt or prompt in base_prompt_set or prompt in approved_prompts:
            raise PromotionError(f"normalized prompt collision: {question_id}")
        approved_prompts.add(prompt)

        fact_id = str(row.get("fact_id") or "")
        source_id = str(row.get("source_unit_id") or "")
        if (
            not fact_id
            or fact_id in approved_facts
            or base_fact_sources.get(fact_id) != source_id
        ):
            raise PromotionError(f"fact/source mismatch or duplicate: {fact_id or '<missing>'}")
        approved_facts.add(fact_id)
        if row.get("role") != "variant":
            raise PromotionError(f"approved row must be a variant: {question_id}")

        match = UNIT_PREFIX_PATTERN.match(source_id.upper())
        if match is None:
            raise PromotionError(f"cannot derive unit from source_unit_id: {source_id}")
        unit = match.group(1)
        row["blind_pool"] = None
        errors = validate_question(row, source_units)
        if errors:
            raise PromotionError(f"approved row {question_id} invalid: {', '.join(errors)}")
        merged[unit].append(row)

    merged_rows = [row for unit in EXPECTED_UNITS for row in merged[unit]]
    if len(merged_rows) != FINAL_QUESTION_COUNT:
        raise PromotionError(f"merged question count must be {FINAL_QUESTION_COUNT}")
    if len({str(row.get("fact_id") or "") for row in merged_rows}) != BASE_FACT_COUNT:
        raise PromotionError("promotion must not add or remove base facts")
    violations = {key: value for key, value in audit_corpus(merged_rows).items() if value}
    if violations:
        raise PromotionError(f"merged corpus audit failed: {violations}")
    return merged


def promote_release(
    base_root: Path,
    checkpoint: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    """Compile a validated overlay and atomically replace the public output."""

    base_root, output = validate_promotion_paths(base_root, output)
    merged = prepare_promotion(base_root, checkpoint)
    compiler = _load_compiler()
    with tempfile.TemporaryDirectory(prefix="competitive-v13-promotion-") as directory:
        staged_source = Path(directory) / "source"
        shutil.copytree(base_root / "source-packets", staged_source / "source-packets")
        questions_dir = staged_source / "questions"
        questions_dir.mkdir(parents=True)
        for unit in EXPECTED_UNITS:
            (questions_dir / f"{unit}.json").write_text(
                json.dumps(merged[unit], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        manifest = compiler.compile_bank(staged_source, output)

    if (
        manifest.get("gold_questions") != FINAL_QUESTION_COUNT
        or manifest.get("unique_facts") != BASE_FACT_COUNT
        or manifest.get("blind_fact_count") != 0
        or manifest.get("blind_presentation_count") != 0
        or any(
            value
            for pool in manifest.get("blind_pools", {}).values()
            for value in (
                pool.get("fact_count"),
                pool.get("presentation_count"),
            )
        )
    ):
        raise PromotionError("compiled public manifest violates promotion invariants")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-root",
        type=Path,
        default=ROOT / "content" / "competitive-v11",
    )
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        checkpoint = read_json(args.release)
        manifest = promote_release(args.base_root, checkpoint, args.output)
    except (PromotionError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "output": str(args.output),
                "questions": manifest["gold_questions"],
                "facts": manifest["unique_facts"],
                "blind_questions": manifest["blind_presentation_count"],
                "build_id": manifest["build_id"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
