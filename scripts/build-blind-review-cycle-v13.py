#!/usr/bin/env python3
"""Build one isolated v13 blind-review packet set for a numbered cycle."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import (  # noqa: E402
    APPLIED_SCHEMA,
    ContractError,
    build_blind_review_packet,
    canonical_hash,
    keyed_hash,
    normalize_authored_input,
)


PACKET_SET_SCHEMA = "competitive-v13-blind-packet-set/v1"
HISTORICAL_APPROVED_COUNT = 262


class CycleError(ContractError):
    """Raised when a review cycle cannot be isolated safely."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_existing_builder():
    path = ROOT / "scripts" / "build-blind-review-packets-v13.py"
    spec = importlib.util.spec_from_file_location("competitive_v13_packet_builder", path)
    if spec is None or spec.loader is None:
        raise CycleError(f"cannot load packet builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_prior_checkpoint(checkpoint: Mapping[str, Any]) -> list[dict[str, Any]]:
    if checkpoint.get("schema_version") != APPLIED_SCHEMA or checkpoint.get("release") != 2:
        raise CycleError("prior checkpoint schema or release mismatch")
    stored_hash = checkpoint.get("release_sha256")
    payload = {
        key: value for key, value in checkpoint.items() if key != "release_sha256"
    }
    if not isinstance(stored_hash, str) or stored_hash != canonical_hash(payload):
        raise CycleError("prior checkpoint release_sha256 mismatch")
    approved = checkpoint.get("approved")
    pending = checkpoint.get("pending")
    batches = checkpoint.get("batches")
    if not isinstance(approved, list) or len(approved) != HISTORICAL_APPROVED_COUNT:
        raise CycleError("prior checkpoint must contain exactly 262 approved rows")
    if not isinstance(pending, list) or not isinstance(batches, list):
        raise CycleError("prior checkpoint batches and pending must be lists")
    if any(not isinstance(row, dict) for row in approved):
        raise CycleError("prior approved rows must be mappings")
    counts = [
        (batch.get("approved"), batch.get("pending"))
        for batch in batches
        if isinstance(batch, Mapping)
    ]
    if len(counts) != len(batches) or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for pair in counts
        for value in pair
    ):
        raise CycleError("prior checkpoint batch totals mismatch")
    approved_total = sum(approved for approved, _pending in counts)
    pending_total = sum(pending for _approved, pending in counts)
    if approved_total != len(approved) or pending_total != len(pending):
        raise CycleError("prior checkpoint batch totals mismatch")
    return approved


def _paths_overlap(left: Path, right: Path) -> bool:
    left = left.resolve()
    right = right.resolve()
    return left == right or left in right.parents or right in left.parents


def build_cycle_packets(
    authored_dir: Path,
    source_dir: Path,
    base_questions_dir: Path,
    prior_checkpoint: Mapping[str, Any],
    output_dir: Path,
    binding_key: bytes,
    *,
    cycle: int,
) -> dict[str, Any]:
    if isinstance(cycle, bool) or not isinstance(cycle, int) or cycle < 1:
        raise CycleError("cycle must be a positive integer")
    if not isinstance(binding_key, bytes) or len(binding_key) < 32:
        raise CycleError("binding key must contain at least 32 bytes")
    authored_dir = Path(authored_dir)
    source_dir = Path(source_dir)
    base_questions_dir = Path(base_questions_dir)
    output_dir = Path(output_dir)
    for protected in (authored_dir, source_dir, base_questions_dir):
        if _paths_overlap(output_dir, protected):
            raise CycleError("cycle output must not overlap any input")
    if output_dir.exists():
        raise CycleError("cycle output directory must be new")

    existing = _load_existing_builder()
    sources, source_sha256 = existing.load_sources(source_dir)
    public_base = existing.load_questions(base_questions_dir)
    historical_approved = validate_prior_checkpoint(prior_checkpoint)
    comparison_base = [*public_base, *historical_approved]
    paths = sorted(authored_dir.glob(f"*-cycle{cycle}.json"))
    if not paths:
        raise CycleError(f"no *-cycle{cycle}.json authored batches matched")

    packets: list[dict[str, Any]] = []
    seen_batches: set[str] = set()
    seen_blind_ids: set[str] = set()
    for path in paths:
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
        if batch["batch_id"] in seen_batches:
            raise CycleError(f"duplicate cycle batch_id: {batch['batch_id']}")
        seen_batches.add(batch["batch_id"])
        packet = build_blind_review_packet(
            batch,
            sources,
            binding_key=binding_key,
            expected_source_sha256=source_sha256,
            base_questions=comparison_base,
        )
        if packet["blind_batch_id"] in seen_blind_ids:
            raise CycleError(f"duplicate blind_batch_id: {packet['blind_batch_id']}")
        seen_blind_ids.add(packet["blind_batch_id"])
        packets.append(packet)
    if not packets:
        raise CycleError(f"no non-empty *-cycle{cycle}.json authored batches matched")

    manifest_payload: dict[str, Any] = {
        "schema_version": PACKET_SET_SCHEMA,
        "cycle": cycle,
        "base_release_sha256": prior_checkpoint["release_sha256"],
        "base_approved_count": len(historical_approved),
        "packets": [
            {
                "blind_batch_id": packet["blind_batch_id"],
                "filename": f"{packet['blind_batch_id']}.json",
                "packet_sha256": packet["packet_sha256"],
            }
            for packet in packets
        ],
    }
    manifest = dict(manifest_payload)
    manifest["set_sha256"] = canonical_hash(manifest_payload)
    manifest["set_hmac_sha256"] = keyed_hash(
        manifest_payload,
        binding_key=binding_key,
    )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.", suffix=".tmp", dir=output_dir.parent)
    )
    try:
        for packet in packets:
            existing.write_json_atomic(stage / f"{packet['blind_batch_id']}.json", packet)
        existing.write_json_atomic(stage / "packet-set.json", manifest)
        os.replace(stage, output_dir)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authored-dir", type=Path, required=True)
    parser.add_argument("--prior-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
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
        existing = _load_existing_builder()
        key = existing.load_or_create_binding_key(args.binding_key_file)
        manifest = build_cycle_packets(
            args.authored_dir,
            args.source_dir,
            args.base_questions_dir,
            read_json(args.prior_checkpoint),
            args.output_dir,
            key,
            cycle=args.cycle,
        )
    except (CycleError, ContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "cycle": manifest["cycle"],
                "batches": len(manifest["packets"]),
                "base_release_sha256": manifest["base_release_sha256"],
                "output": str(args.output_dir),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
