#!/usr/bin/env python3
"""Apply one isolated v13 review cycle and merge it onto an immutable checkpoint."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import (  # noqa: E402
    APPLIED_SCHEMA,
    ContractError,
    apply_reviewed_release_atomic,
    blind_batch_id,
    canonical_hash,
    keyed_hash,
    normalize_authored_input,
    normalize_prompt,
)


PACKET_SET_SCHEMA = "competitive-v13-blind-packet-set/v1"


class CycleError(ContractError):
    """Raised when a reviewed cycle cannot be merged safely."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_script(filename: str, module_name: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise CycleError(f"cannot load support script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_checkpoint(checkpoint: Mapping[str, Any], label: str) -> None:
    if checkpoint.get("schema_version") != APPLIED_SCHEMA or checkpoint.get("release") != 2:
        raise CycleError(f"{label} checkpoint schema or release mismatch")
    stored_hash = checkpoint.get("release_sha256")
    payload = {
        key: value for key, value in checkpoint.items() if key != "release_sha256"
    }
    if not isinstance(stored_hash, str) or stored_hash != canonical_hash(payload):
        raise CycleError(f"{label} checkpoint release_sha256 mismatch")
    batches = checkpoint.get("batches")
    approved = checkpoint.get("approved")
    pending = checkpoint.get("pending")
    if not all(isinstance(value, list) for value in (batches, approved, pending)):
        raise CycleError(f"{label} checkpoint arrays are malformed")
    if any(not isinstance(batch, Mapping) for batch in batches):
        raise CycleError(f"{label} checkpoint batch is malformed")
    counts = [(batch.get("approved"), batch.get("pending")) for batch in batches]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for pair in counts
        for value in pair
    ):
        raise CycleError(f"{label} checkpoint batch totals mismatch")
    approved_total = sum(approved for approved, _pending in counts)
    pending_total = sum(pending for _approved, pending in counts)
    if approved_total != len(approved) or pending_total != len(pending):
        raise CycleError(f"{label} checkpoint batch totals mismatch")


def merge_checkpoints(
    prior: Mapping[str, Any],
    increment: Mapping[str, Any],
    *,
    cycle: int,
) -> dict[str, Any]:
    """Return a deterministic append-only merge without mutating either input."""

    builder = _load_script(
        "build-blind-review-cycle-v13.py", "competitive_v13_cycle_builder"
    )
    try:
        builder.validate_prior_checkpoint(prior)
    except ContractError as exc:
        raise CycleError(str(exc)) from exc
    _validate_checkpoint(increment, "increment")
    if isinstance(cycle, bool) or not isinstance(cycle, int) or cycle < 1:
        raise CycleError("cycle must be a positive integer")

    prior_batches = deepcopy(prior["batches"])
    increment_batches = deepcopy(increment["batches"])
    prior_batch_ids = {str(batch.get("batch_id") or "") for batch in prior_batches}
    increment_batch_ids: set[str] = set()
    for batch in increment_batches:
        batch_id = str(batch.get("batch_id") or "")
        if (
            not batch_id
            or not batch_id.endswith(f"-cycle{cycle}")
            or batch_id in prior_batch_ids
            or batch_id in increment_batch_ids
        ):
            raise CycleError(f"invalid or duplicate cycle batch_id: {batch_id or '<missing>'}")
        increment_batch_ids.add(batch_id)

    prior_approved = deepcopy(prior["approved"])
    increment_approved = deepcopy(increment["approved"])
    prior_ids = {str(row.get("id") or "") for row in prior_approved}
    prior_facts = {str(row.get("fact_id") or "") for row in prior_approved}
    prior_prompts = {
        normalize_prompt(str(row.get("question") or "")) for row in prior_approved
    }
    new_ids: set[str] = set()
    new_facts: set[str] = set()
    new_prompts: set[str] = set()
    for row in increment_approved:
        if not isinstance(row, Mapping):
            raise CycleError("increment approved row must be a mapping")
        if any("blind" in str(key).casefold() for key in row):
            raise CycleError("increment approved row contains blind metadata")
        question_id = str(row.get("id") or "")
        fact_id = str(row.get("fact_id") or "")
        prompt = normalize_prompt(str(row.get("question") or ""))
        if not question_id or question_id in prior_ids or question_id in new_ids:
            raise CycleError(f"question id already approved or duplicated: {question_id}")
        if not fact_id or fact_id in prior_facts or fact_id in new_facts:
            raise CycleError(f"fact_id already approved or duplicated: {fact_id}")
        if not prompt or prompt in prior_prompts or prompt in new_prompts:
            raise CycleError(f"prompt already approved or duplicated: {question_id}")
        new_ids.add(question_id)
        new_facts.add(fact_id)
        new_prompts.add(prompt)

    prior_history = prior.get("cycle_history", [])
    if not isinstance(prior_history, list) or any(
        not isinstance(entry, Mapping) for entry in prior_history
    ):
        raise CycleError("prior cycle_history is malformed")
    history_entry = {
        "cycle": cycle,
        "base_release_sha256": prior["release_sha256"],
        "increment_release_sha256": increment["release_sha256"],
        "base_approved_count": len(prior_approved),
        "new_approved_count": len(increment_approved),
        "merged_approved_count": len(prior_approved) + len(increment_approved),
    }
    merged: dict[str, Any] = {
        "schema_version": APPLIED_SCHEMA,
        "release": 2,
        "batches": [*prior_batches, *increment_batches],
        "approved": [*prior_approved, *increment_approved],
        "pending": [*deepcopy(prior["pending"]), *deepcopy(increment["pending"])],
        "cycle_history": [*deepcopy(prior_history), history_entry],
    }
    merged["release_sha256"] = canonical_hash(merged)
    return merged


def _validate_packet_set(
    packet_set: Mapping[str, Any],
    prior: Mapping[str, Any],
    binding_key: bytes,
    cycle: int,
) -> dict[str, Mapping[str, Any]]:
    payload = {
        key: value
        for key, value in packet_set.items()
        if key not in {"set_sha256", "set_hmac_sha256"}
    }
    if (
        packet_set.get("schema_version") != PACKET_SET_SCHEMA
        or packet_set.get("cycle") != cycle
        or packet_set.get("base_release_sha256") != prior.get("release_sha256")
        or packet_set.get("base_approved_count") != len(prior["approved"])
        or packet_set.get("set_sha256") != canonical_hash(payload)
        or packet_set.get("set_hmac_sha256")
        != keyed_hash(payload, binding_key=binding_key)
    ):
        raise CycleError("cycle packet-set binding mismatch")
    entries = packet_set.get("packets")
    if not isinstance(entries, list) or not entries:
        raise CycleError("cycle packet-set packets must be non-empty")
    result: dict[str, Mapping[str, Any]] = {}
    filenames: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise CycleError("cycle packet-set entry must be a mapping")
        blind_id = entry.get("blind_batch_id")
        filename = entry.get("filename")
        packet_hash = entry.get("packet_sha256")
        if (
            not isinstance(blind_id, str)
            or not blind_id
            or filename != f"{blind_id}.json"
            or not isinstance(packet_hash, str)
            or not packet_hash
            or blind_id in result
            or filename in filenames
        ):
            raise CycleError("invalid or duplicate cycle packet-set entry")
        result[blind_id] = entry
        filenames.add(filename)
    return result


def apply_cycle_reviews(
    authored_dir: Path,
    packet_dir: Path,
    review_dir: Path,
    source_dir: Path,
    base_questions_dir: Path,
    prior: Mapping[str, Any],
    output: Path,
    binding_key: bytes,
    *,
    cycle: int,
) -> dict[str, Any]:
    builder = _load_script(
        "build-blind-review-cycle-v13.py", "competitive_v13_cycle_builder_apply"
    )
    try:
        builder.validate_prior_checkpoint(prior)
    except ContractError as exc:
        raise CycleError(str(exc)) from exc
    if not isinstance(binding_key, bytes) or len(binding_key) < 32:
        raise CycleError("binding key must contain at least 32 bytes")
    output = Path(output)
    if output.exists():
        raise CycleError("merged checkpoint output must be new")

    existing = _load_script(
        "apply-reviewed-release-v13.py", "competitive_v13_existing_applier"
    )
    sources, source_sha256 = existing.load_sources(Path(source_dir))
    public_base = existing.load_questions(Path(base_questions_dir))
    comparison_base = [*public_base, *prior["approved"]]
    packet_set = read_json(Path(packet_dir) / "packet-set.json")
    if not isinstance(packet_set, Mapping):
        raise CycleError("cycle packet-set is malformed")
    entries = _validate_packet_set(packet_set, prior, binding_key, cycle)

    triples = []
    active_blind_ids: set[str] = set()
    for path in sorted(Path(authored_dir).glob(f"*-cycle{cycle}.json")):
        raw = read_json(path)
        if raw == []:
            continue
        batch = normalize_authored_input(
            raw,
            batch_id=path.stem,
            source_sha256=source_sha256,
        )
        if not str(batch["batch_id"]).endswith(f"-cycle{cycle}"):
            raise CycleError(f"batch_id is not bound to cycle {cycle}: {batch['batch_id']}")
        blind_id = blind_batch_id(batch, binding_key=binding_key)
        entry = entries.get(blind_id)
        if entry is None:
            raise CycleError(f"cycle packet not committed: {blind_id}")
        packet = read_json(Path(packet_dir) / str(entry["filename"]))
        review = read_json(Path(review_dir) / f"{blind_id}.json")
        if not isinstance(packet, Mapping) or not isinstance(review, Mapping):
            raise CycleError(f"cycle packet/review malformed: {blind_id}")
        if packet.get("packet_sha256") != entry.get("packet_sha256"):
            raise CycleError(f"cycle packet-set entry mismatch: {blind_id}")
        active_blind_ids.add(blind_id)
        triples.append((batch, packet, review))
    if not triples or active_blind_ids != set(entries):
        raise CycleError("cycle authored batches do not exactly match packet-set")

    with tempfile.TemporaryDirectory(prefix=f"competitive-v13-cycle{cycle}-") as directory:
        increment_path = Path(directory) / "increment.json"
        increment = apply_reviewed_release_atomic(
            triples,
            sources,
            increment_path,
            binding_key=binding_key,
            base_questions=comparison_base,
            expected_source_sha256=source_sha256,
        )
        merged = merge_checkpoints(prior, increment, cycle=cycle)
    builder_existing = builder._load_existing_builder()
    builder_existing.write_json_atomic(output, merged)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authored-dir", type=Path, required=True)
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--prior-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycle", type=int, default=11)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "source-packets",
    )
    parser.add_argument(
        "--base-questions-dir",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "questions",
    )
    parser.add_argument(
        "--binding-key-file",
        type=Path,
        default=Path.home() / ".codex" / "secrets" / "competitive-v13-blind-binding.key",
    )
    args = parser.parse_args()
    try:
        prior_path = args.prior_checkpoint.resolve()
        if args.output.resolve() == prior_path:
            raise CycleError("merged output must not overwrite prior checkpoint")
        key_path = args.binding_key_file.resolve()
        if key_path == ROOT or ROOT in key_path.parents:
            raise CycleError("blind binding key must be stored outside the repository")
        key = args.binding_key_file.read_bytes()
        merged = apply_cycle_reviews(
            args.authored_dir,
            args.packet_dir,
            args.review_dir,
            args.source_dir,
            args.base_questions_dir,
            read_json(args.prior_checkpoint),
            args.output,
            key,
            cycle=args.cycle,
        )
    except (CycleError, ContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "cycle": args.cycle,
                "approved_total": len(merged["approved"]),
                "pending_total": len(merged["pending"]),
                "release_sha256": merged["release_sha256"],
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
