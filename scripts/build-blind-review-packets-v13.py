#!/usr/bin/env python3
"""Build author-redacted semantic review packets for competitive v13."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import (  # noqa: E402
    ContractError,
    build_blind_review_packet,
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


def load_questions(directory: Path) -> list[dict[str, object]]:
    questions: list[dict[str, object]] = []
    for path in sorted(directory.glob("*.json")):
        value = read_json(path)
        if isinstance(value, list):
            questions.extend(row for row in value if isinstance(row, dict))
    if not questions:
        raise ContractError("public base questions are required for blind comparison")
    return questions


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def load_or_create_binding_key(path: Path) -> bytes:
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ContractError("blind binding key must be stored outside the repository")
    if path.exists():
        key = path.read_bytes()
        if len(key) < 32:
            raise ContractError("blind binding key must contain at least 32 bytes")
        return key
    path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(key)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return key


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authored-dir", type=Path, required=True)
    parser.add_argument("--pattern", default="*.json")
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
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--binding-key-file",
        type=Path,
        default=Path.home()
        / ".codex"
        / "secrets"
        / "competitive-v13-blind-binding.key",
    )
    args = parser.parse_args()

    try:
        sources, source_sha256 = load_sources(args.source_dir)
        base_questions = load_questions(args.base_questions_dir)
        binding_key = load_or_create_binding_key(args.binding_key_file)
        outputs: list[tuple[Path, dict[str, object]]] = []
        seen_batches: set[str] = set()
        seen_destinations: set[Path] = set()
        for path in sorted(args.authored_dir.glob(args.pattern)):
            if path.name.endswith(".pending.json"):
                continue
            raw = read_json(path)
            if raw == []:
                continue
            batch = normalize_authored_input(
                raw, batch_id=path.stem, source_sha256=source_sha256
            )
            if batch["batch_id"] in seen_batches:
                raise ContractError(f"duplicate batch_id: {batch['batch_id']}")
            seen_batches.add(batch["batch_id"])
            packet = build_blind_review_packet(
                batch,
                sources,
                binding_key=binding_key,
                expected_source_sha256=source_sha256,
                base_questions=base_questions,
            )
            destination = args.output_dir / f"{packet['blind_batch_id']}.json"
            if destination in seen_destinations:
                raise ContractError(
                    f"duplicate blind_batch_id: {packet['blind_batch_id']}"
                )
            seen_destinations.add(destination)
            outputs.append((destination, packet))
        if not outputs:
            raise ContractError("no authored batches matched")
        # No output is touched until every input has validated.
        for destination, packet in outputs:
            write_json_atomic(destination, packet)
        manifest: dict[str, object] = {
            "schema_version": PACKET_SET_SCHEMA,
            "packets": [
                {
                    "blind_batch_id": packet["blind_batch_id"],
                    "filename": destination.name,
                    "packet_sha256": packet["packet_sha256"],
                }
                for destination, packet in outputs
            ],
        }
        manifest["set_sha256"] = canonical_hash(manifest)
        manifest["set_hmac_sha256"] = keyed_hash(
            {
                key: value
                for key, value in manifest.items()
                if key not in {"set_sha256", "set_hmac_sha256"}
            },
            binding_key=binding_key,
        )
        # The manifest is the commit marker: consumers ignore packet files
        # until this final atomic write describes the complete validated set.
        write_json_atomic(args.output_dir / "packet-set.json", manifest)
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"batches": len(outputs), "output": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
