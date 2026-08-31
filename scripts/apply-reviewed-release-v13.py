#!/usr/bin/env python3
"""Atomically compile independently approved v13 rows; retain rejections pending."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_release_contract import validate_checkpoint  # noqa: E402
from scripts.lib.competitive_v13 import (  # noqa: E402
    ContractError,
    apply_reviewed_release_atomic,
    base_fact_sources,
    blind_batch_id,
    canonical_hash,
    keyed_hash,
    normalize_authored_input,
)

PACKET_SET_SCHEMA = "competitive-v13-blind-packet-set/v1"


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_sources(directory: Path) -> tuple[dict[str, dict[str, object]], str]:
    sources: dict[str, dict[str, object]] = {}
    hashes: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        packet = read_json(path)
        if not isinstance(packet, dict) or not isinstance(packet.get("units"), list):
            continue
        if isinstance(packet.get("source_sha256"), str):
            hashes.add(packet["source_sha256"])
        for row in packet["units"]:
            if row["source_unit_id"] in sources:
                raise ContractError(
                    f"duplicate source_unit_id: {row['source_unit_id']}"
                )
            sources[row["source_unit_id"]] = row
    if not sources or len(hashes) != 1:
        raise ContractError("source packets must contain units with one common source hash")
    return sources, next(iter(hashes))


def load_questions(directory: Path | None) -> list[dict[str, object]]:
    if directory is None:
        return []
    questions: list[dict[str, object]] = []
    for path in sorted(directory.glob("*.json")):
        value = read_json(path)
        if isinstance(value, list):
            questions.extend(value)
    return questions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authored-dir", type=Path, required=True)
    parser.add_argument("--pattern", default="*.json")
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--binding-key-file",
        type=Path,
        default=Path.home()
        / ".codex"
        / "secrets"
        / "competitive-v13-blind-binding.key",
    )
    parser.add_argument(
        "--require-complete-release",
        action="store_true",
        help="enforce all 2,217 base fact ids and exact R2 family quotas",
    )
    parser.add_argument(
        "--allow-packet-subset",
        action="store_true",
        help="diagnostic only: allow applying a strict subset of the committed packet set",
    )
    args = parser.parse_args()

    try:
        sources, source_sha256 = load_sources(args.source_dir)
        resolved_key = args.binding_key_file.resolve()
        if resolved_key == ROOT or ROOT in resolved_key.parents:
            raise ContractError("blind binding key must be stored outside the repository")
        if not args.binding_key_file.exists():
            raise ContractError("blind binding key file does not exist")
        binding_key = args.binding_key_file.read_bytes()
        if len(binding_key) < 32:
            raise ContractError("blind binding key must contain at least 32 bytes")
        packet_set = read_json(args.packet_dir / "packet-set.json")
        if not isinstance(packet_set, dict):
            raise ContractError("blind packet-set manifest is malformed")
        if packet_set.get("schema_version") != PACKET_SET_SCHEMA:
            raise ContractError("blind packet-set schema mismatch")
        packet_set_payload = {
            key: value
            for key, value in packet_set.items()
            if key not in {"set_sha256", "set_hmac_sha256"}
        }
        if packet_set.get("set_sha256") != canonical_hash(packet_set_payload):
            raise ContractError("blind packet-set hash mismatch")
        if packet_set.get("set_hmac_sha256") != keyed_hash(
            packet_set_payload, binding_key=binding_key
        ):
            raise ContractError("blind packet-set HMAC mismatch")
        entries = packet_set.get("packets")
        if not isinstance(entries, list):
            raise ContractError("blind packet-set packets must be a list")
        packet_entries: dict[str, dict[str, object]] = {}
        filenames: set[str] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ContractError(f"packet-set entry {index} must be a mapping")
            blind_id = entry.get("blind_batch_id")
            filename = entry.get("filename")
            packet_sha256 = entry.get("packet_sha256")
            if not all(isinstance(value, str) and value for value in (blind_id, filename, packet_sha256)):
                raise ContractError(f"packet-set entry {index} has invalid fields")
            if filename != f"{blind_id}.json":
                raise ContractError(f"packet-set entry {index} has noncanonical filename")
            if blind_id in packet_entries or filename in filenames:
                raise ContractError("packet-set contains duplicate id or filename")
            packet_entries[blind_id] = entry
            filenames.add(filename)
        triples = []
        active_blind_ids: set[str] = set()
        for path in sorted(args.authored_dir.glob(args.pattern)):
            if path.name.endswith(".pending.json"):
                continue
            raw = read_json(path)
            if raw == []:
                continue
            batch = normalize_authored_input(
                raw, batch_id=path.stem, source_sha256=source_sha256
            )
            batch_id = batch["batch_id"]
            blind_id = blind_batch_id(batch, binding_key=binding_key)
            active_blind_ids.add(blind_id)
            entry = packet_entries.get(blind_id)
            if not isinstance(entry, dict):
                raise ContractError(f"packet not committed in set: {blind_id}")
            packet = read_json(args.packet_dir / str(entry.get("filename") or ""))
            if packet.get("packet_sha256") != entry.get("packet_sha256"):
                raise ContractError(f"packet-set entry mismatch: {blind_id}")
            review = read_json(args.review_dir / f"{blind_id}.json")
            if not isinstance(packet, dict) or not isinstance(review, dict):
                raise ContractError(f"packet/review malformed for {batch_id}")
            triples.append((batch, packet, review))
        if not triples:
            raise ContractError("no authored batches matched")
        committed_ids = set(packet_entries)
        if args.allow_packet_subset:
            if not active_blind_ids <= committed_ids:
                raise ContractError("active batches are not a subset of packet-set")
        elif active_blind_ids != committed_ids:
            raise ContractError("active batches do not exactly match packet-set")
        base = load_questions(args.base_questions_dir)
        if args.require_complete_release:
            # Precompile to inspect the complete approved checkpoint without
            # publishing it. The atomic writer repeats all gates before replace.
            from scripts.lib.competitive_v13 import compile_reviewed_batch

            approved = []
            for batch, packet, review in triples:
                approved.extend(
                    compile_reviewed_batch(
                        batch,
                        packet,
                        review,
                        sources,
                        binding_key=binding_key,
                        expected_source_sha256=source_sha256,
                        base_questions=base,
                    )["approved"]
                )
            contract_errors = validate_checkpoint(
                {"release": 2, "rows": approved},
                base_fact_ids={row["fact_id"] for row in base},
                base_fact_sources=base_fact_sources(base),
            )
            if contract_errors:
                raise ContractError("incomplete Release 2: " + "; ".join(contract_errors))
        result = apply_reviewed_release_atomic(
            triples,
            sources,
            args.output,
            binding_key=binding_key,
            base_questions=base,
            expected_source_sha256=source_sha256,
        )
    except (ContractError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "approved": len(result["approved"]),
                "pending": len(result["pending"]),
                "release_sha256": result["release_sha256"],
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
