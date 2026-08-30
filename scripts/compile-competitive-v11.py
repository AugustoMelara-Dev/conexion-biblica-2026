#!/usr/bin/env python3
"""Compila el corpus V11 a un banco público de ensayo sin generar prosa."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from pathlib import PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v11 import (
    RELEASE_BLIND_REQUIREMENTS,
    audit_corpus,
    blind_family,
    content_hash,
    validate_question,
)
from scripts.lib.final_bank import BANK_ID, DISPLAY_NAME, SCHEMA_VERSION

EXPECTED_UNITS = [
    *(f"DAN{number}" for number in range(1, 13)),
    *(f"PR{number}" for number in range(39, 45)),
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


BLIND_POOLS = ("A", "B", "emergency")
BLIND_FAMILIES = ("selection", "fill_choice", "true_false")
BLIND_DELIVERY_CONTRACT = "private-blind-artifact-v1"
BLIND_ARTIFACT_ID = "competitive-v11-blind"
BUILD_DESCRIPTOR_CONTRACT = "competitive-v11-emitted-descriptors-v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def validate_blind_requirements(requirements: object) -> dict:
    if not isinstance(requirements, dict) or set(requirements) != set(BLIND_POOLS):
        raise ValueError("blind requirements must define exactly A, B and emergency")
    for pool in BLIND_POOLS:
        requirement = requirements[pool]
        if not isinstance(requirement, dict) or set(requirement) != {
            "fact_count",
            "families",
        }:
            raise ValueError(f"invalid blind requirement schema for {pool}")
        fact_count = requirement["fact_count"]
        if isinstance(fact_count, bool) or not isinstance(fact_count, int) or fact_count < 0:
            raise ValueError(f"invalid fact_count for {pool}")
        families = requirement["families"]
        if not isinstance(families, dict) or set(families) != set(BLIND_FAMILIES):
            raise ValueError(f"invalid family schema for {pool}")
        for family in BLIND_FAMILIES:
            count = families[family]
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError(f"invalid {family} count for {pool}")
        if sum(families.values()) != fact_count:
            raise ValueError(f"family counts do not add up to fact_count for {pool}")
    return requirements


def _validate_windows_components(path: Path) -> None:
    anchor = path.anchor.casefold()
    for raw_part in path.parts:
        part = str(raw_part)
        if part.casefold() == anchor or part in {"/", "\\"}:
            continue
        if part.endswith((".", " ")):
            raise ValueError(f"unsafe Win32 trailing character in path component: {part!r}")
        if ":" in part:
            raise ValueError(f"unsafe Win32 ADS path component: {part!r}")
        base_name = part.split(".", 1)[0].upper()
        if base_name in WINDOWS_RESERVED_NAMES:
            raise ValueError(f"reserved Win32 path component: {part!r}")


def _win32_identity(path: Path) -> tuple[str, ...]:
    return tuple(part.casefold() for part in PureWindowsPath(str(path)).parts)


def _paths_overlap(left: Path, right: Path) -> bool:
    left_parts = _win32_identity(left)
    right_parts = _win32_identity(right)
    shortest = min(len(left_parts), len(right_parts))
    return left_parts[:shortest] == right_parts[:shortest]


def _stage_path(target: Path) -> Path:
    return target.parent / f".{target.name}.tmp"


def _backup_path(target: Path) -> Path:
    return target.parent / f".{target.name}.backup"


def validate_output_paths(
    source_root: Path,
    output: Path,
    blind_output: Path | None = None,
) -> tuple[Path, Path, Path | None]:
    for raw_path in (source_root, output, blind_output):
        if raw_path is not None:
            _validate_windows_components(raw_path)
    source = source_root.resolve()
    public = output.resolve()
    private = blind_output.resolve() if blind_output is not None else None
    artifact_paths = [public, _stage_path(public), _backup_path(public)]
    if private is not None:
        artifact_paths.extend([private, _stage_path(private), _backup_path(private)])
    for path in artifact_paths:
        _validate_windows_components(path)
    if any(_paths_overlap(source, path) for path in artifact_paths):
        raise ValueError("source_root must not overlap outputs, staging or backups")
    for index, left in enumerate(artifact_paths):
        for right in artifact_paths[index + 1 :]:
            if _paths_overlap(left, right):
                raise ValueError("output, blind_output, staging and backups must not overlap")
    if private is not None:
        web_root = (ROOT / "public").resolve()
        for path in (private, _stage_path(private), _backup_path(private)):
            if _paths_overlap(path, web_root):
                raise ValueError("blind_output must remain outside the public web root")
    return source, public, private


def write_json(path: Path, value: Any) -> dict[str, Any]:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def emitted_row_hash(row: Mapping[str, Any]) -> str:
    canonical = {
        key: value for key, value in row.items() if key != "row_content_sha256"
    }
    payload = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def artifact_build_descriptor(
    public_manifest: Mapping[str, Any],
    private_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    public_count_keys = (
        "unique_facts",
        "gold_questions",
        "central_question_count",
        "presentation_variant_count",
        "training_fact_count",
        "training_presentation_count",
        "total_fact_count",
        "total_presentation_count",
        "total_central_question_count",
        "total_presentation_variant_count",
        "blind_fact_count",
        "blind_presentation_count",
    )
    descriptor: dict[str, Any] = {
        "contract": BUILD_DESCRIPTOR_CONTRACT,
        "schema_version": public_manifest.get("schema_version"),
        "bank_id": public_manifest.get("bank_id"),
        "artifact_revision": (
            public_manifest.get("blind_delivery") or {}
        ).get("artifact_revision"),
        "public": {
            "counts": {key: public_manifest.get(key) for key in public_count_keys},
            "families": public_manifest.get("families"),
            "total_families": public_manifest.get("total_families"),
            "blind_pools": public_manifest.get("blind_pools"),
            "review_index": public_manifest.get("review_index"),
            "shards": public_manifest.get("shards"),
        },
        "private": None,
    }
    if private_manifest is not None:
        descriptor["private"] = {
            "contract": private_manifest.get("contract"),
            "artifact_id": private_manifest.get("artifact_id"),
            "artifact_revision": private_manifest.get("artifact_revision"),
            "schema_version": private_manifest.get("schema_version"),
            "bank_id": private_manifest.get("bank_id"),
            "counts": {
                key: private_manifest.get(key)
                for key in (
                    "total_fact_count",
                    "total_presentation_count",
                    "central_question_count",
                    "presentation_variant_count",
                )
            },
            "families": private_manifest.get("families"),
            "review_index": private_manifest.get("review_index"),
            "pools": private_manifest.get("pools"),
        }
    return descriptor


def compute_artifact_build_id(
    public_manifest: Mapping[str, Any],
    private_manifest: Mapping[str, Any] | None,
) -> str:
    payload = json.dumps(
        artifact_build_descriptor(public_manifest, private_manifest),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _rename_with_retry(source: Path, target: Path, attempts: int = 4) -> None:
    for attempt in range(attempts):
        try:
            source.rename(target)
            return
        except PermissionError:
            if attempt + 1 == attempts:
                raise
            time.sleep(0.05 * (2**attempt))


def _recover_backup(target: Path) -> None:
    backup = _backup_path(target)
    if not backup.exists():
        return
    if target.exists():
        raise ValueError(f"ambiguous artifact recovery for {target}")
    _rename_with_retry(backup, target)


def replace_artifact_pair(
    public_stage: Path,
    public: Path,
    private_stage: Path,
    private: Path,
) -> None:
    public_backup = _backup_path(public)
    private_backup = _backup_path(private)
    _recover_backup(public)
    _recover_backup(private)
    public_backed_up = False
    private_backed_up = False
    public_installed = False
    private_installed = False
    try:
        if public.exists():
            _rename_with_retry(public, public_backup)
            public_backed_up = True
        if private.exists():
            _rename_with_retry(private, private_backup)
            private_backed_up = True
        _rename_with_retry(public_stage, public)
        public_installed = True
        _rename_with_retry(private_stage, private)
        private_installed = True
    except Exception:
        if public_installed:
            _remove_tree(public)
        if private_installed:
            _remove_tree(private)
        if public_backed_up:
            _rename_with_retry(public_backup, public)
        if private_backed_up:
            _rename_with_retry(private_backup, private)
        raise
    _remove_tree(public_backup)
    _remove_tree(private_backup)


def replace_artifact(stage: Path, target: Path) -> None:
    backup = _backup_path(target)
    _recover_backup(target)
    backed_up = False
    installed = False
    try:
        if target.exists():
            _rename_with_retry(target, backup)
            backed_up = True
        _rename_with_retry(stage, target)
        installed = True
    except Exception:
        if installed:
            _remove_tree(target)
        if backed_up:
            _rename_with_retry(backup, target)
        raise
    _remove_tree(backup)


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"blind artifact mismatch: invalid {label}")
    return value


def _descriptor_payload(
    descriptor: object,
    *,
    label: str,
    path_key: str,
    root: Path | None,
    public_prefix: str = "",
) -> bytes | None:
    if not isinstance(descriptor, Mapping):
        raise ValueError(f"blind artifact mismatch: invalid {label} descriptor")
    file_name = descriptor.get(path_key)
    digest = descriptor.get("sha256")
    byte_count = descriptor.get("bytes")
    if not isinstance(file_name, str) or not file_name:
        raise ValueError(f"blind artifact mismatch: invalid {label} path")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise ValueError(f"blind artifact mismatch: invalid {label} sha256")
    _nonnegative_int(byte_count, f"{label} bytes")
    if root is None:
        return None
    if public_prefix:
        if not file_name.startswith(public_prefix):
            raise ValueError(f"blind artifact mismatch: invalid {label} public path")
        file_name = file_name.removeprefix(public_prefix)
    relative = PureWindowsPath(file_name.replace("/", "\\"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"blind artifact mismatch: unsafe {label} path")
    candidate = (root / Path(*relative.parts)).resolve()
    resolved_root = root.resolve()
    if candidate == resolved_root or not _paths_overlap(candidate, resolved_root):
        raise ValueError(f"blind artifact mismatch: escaped {label} path")
    try:
        payload = candidate.read_bytes()
    except OSError as exc:
        raise ValueError(f"blind artifact integrity mismatch: missing {label}") from exc
    if len(payload) != byte_count or hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError(f"blind artifact integrity mismatch: {label}")
    return payload


def _validate_pool_metadata(pool: str, metadata: object) -> tuple[int, int]:
    if not isinstance(metadata, Mapping):
        raise ValueError(f"blind artifact mismatch: invalid pool {pool}")
    fact_count = _nonnegative_int(metadata.get("fact_count"), f"{pool} fact_count")
    presentation_count = _nonnegative_int(
        metadata.get("presentation_count"), f"{pool} presentation_count"
    )
    families = metadata.get("families")
    if not isinstance(families, Mapping) or set(families) != set(BLIND_FAMILIES):
        raise ValueError(f"blind artifact mismatch: invalid {pool} families")
    family_total = sum(
        _nonnegative_int(families[family], f"{pool} {family}")
        for family in BLIND_FAMILIES
    )
    if fact_count != presentation_count or family_total != presentation_count:
        raise ValueError(f"blind artifact mismatch: inconsistent pool {pool}")
    return fact_count, presentation_count


def validate_artifact_pair(
    public_manifest: Mapping[str, Any],
    private_manifest: Mapping[str, Any],
    public_root: Path | None = None,
    private_root: Path | None = None,
) -> str:
    if (public_root is None) != (private_root is None):
        raise ValueError("blind artifact mismatch: both roots are required for integrity")
    delivery = public_manifest.get("blind_delivery")
    if not isinstance(delivery, Mapping):
        raise ValueError("blind artifact mismatch: missing public delivery contract")
    build_id = public_manifest.get("build_id")
    if (
        delivery.get("contract") != BLIND_DELIVERY_CONTRACT
        or private_manifest.get("contract") != BLIND_DELIVERY_CONTRACT
        or delivery.get("artifact_id") != BLIND_ARTIFACT_ID
        or private_manifest.get("artifact_id") != BLIND_ARTIFACT_ID
    ):
        raise ValueError("blind artifact mismatch: contract or identity")
    artifact_revision = delivery.get("artifact_revision")
    private_build_id = private_manifest.get("build_id")
    if (
        not isinstance(build_id, str)
        or not SHA256_PATTERN.fullmatch(build_id)
        or not isinstance(private_build_id, str)
        or not SHA256_PATTERN.fullmatch(private_build_id)
        or private_build_id != build_id
        or not isinstance(artifact_revision, str)
        or not SHA256_PATTERN.fullmatch(artifact_revision)
        or private_manifest.get("artifact_revision") != artifact_revision
    ):
        raise ValueError("blind artifact mismatch: build_id")
    if (
        public_manifest.get("schema_version") != SCHEMA_VERSION
        or private_manifest.get("schema_version") != SCHEMA_VERSION
        or public_manifest.get("bank_id") != BANK_ID
        or private_manifest.get("bank_id") != BANK_ID
    ):
        raise ValueError("blind artifact mismatch: schema or bank")

    public_pools = public_manifest.get("blind_pools")
    private_pools = private_manifest.get("pools")
    if (
        not isinstance(public_pools, Mapping)
        or not isinstance(private_pools, Mapping)
        or set(public_pools) != set(BLIND_POOLS)
        or set(private_pools) != set(BLIND_POOLS)
    ):
        raise ValueError("blind artifact mismatch: pools A/B/emergency required")
    blind_facts = 0
    blind_presentations = 0
    private_shard_presentations = 0
    private_rows_by_pool: dict[str, list[Mapping[str, Any]]] = {
        pool: [] for pool in BLIND_POOLS
    }
    for pool in BLIND_POOLS:
        facts, presentations = _validate_pool_metadata(pool, public_pools[pool])
        private_facts, private_presentations = _validate_pool_metadata(
            pool, private_pools[pool]
        )
        if (
            facts != private_facts
            or presentations != private_presentations
            or public_pools[pool].get("families")
            != private_pools[pool].get("families")
        ):
            raise ValueError(f"blind artifact mismatch: public/private pool {pool}")
        blind_facts += facts
        blind_presentations += presentations
        shards = private_pools[pool].get("shards")
        if not isinstance(shards, list):
            raise ValueError(f"blind artifact mismatch: invalid {pool} shards")
        pool_shard_count = 0
        for index, shard in enumerate(shards):
            if not isinstance(shard, Mapping):
                raise ValueError(f"blind artifact mismatch: invalid {pool} shard")
            count = _nonnegative_int(
                shard.get("question_count"), f"{pool} shard question_count"
            )
            payload = _descriptor_payload(
                shard,
                label=f"private {pool} shard {index}",
                path_key="questions_file",
                root=private_root,
            )
            if payload is not None:
                try:
                    rows = json.loads(payload)
                except json.JSONDecodeError as exc:
                    raise ValueError("blind artifact integrity mismatch: invalid shard JSON") from exc
                if not isinstance(rows, list) or len(rows) != count:
                    raise ValueError("blind artifact mismatch: private shard question_count")
                for row in rows:
                    if not isinstance(row, Mapping):
                        raise ValueError("blind artifact mismatch: invalid private shard row")
                    if row.get("role") != "central":
                        raise ValueError("blind artifact mismatch: private shard role")
                    if row.get("blind_pool") != pool:
                        raise ValueError("blind artifact mismatch: private shard pool")
                    if (
                        not isinstance(row.get("row_content_sha256"), str)
                        or row["row_content_sha256"] != emitted_row_hash(row)
                    ):
                        raise ValueError(
                            "blind artifact mismatch: private review ledger row hash"
                        )
                    private_rows_by_pool[pool].append(row)
            pool_shard_count += count
        if pool_shard_count != presentations:
            raise ValueError(f"blind artifact mismatch: {pool} shard totals")
        private_shard_presentations += pool_shard_count

    public_blind_facts = _nonnegative_int(
        public_manifest.get("blind_fact_count"), "public blind_fact_count"
    )
    public_blind_presentations = _nonnegative_int(
        public_manifest.get("blind_presentation_count"),
        "public blind_presentation_count",
    )
    private_fact_total = _nonnegative_int(
        private_manifest.get("total_fact_count"), "private total_fact_count"
    )
    private_presentation_total = _nonnegative_int(
        private_manifest.get("total_presentation_count"),
        "private total_presentation_count",
    )
    if (
        not (blind_facts == public_blind_facts == private_fact_total)
        or blind_presentations != public_blind_presentations
        or blind_presentations != private_presentation_total
        or blind_presentations != private_shard_presentations
    ):
        raise ValueError("blind artifact mismatch: blind totals")

    private_families = private_manifest.get("families")
    if (
        private_manifest.get("central_question_count") != blind_presentations
        or private_manifest.get("presentation_variant_count") != 0
        or not isinstance(private_families, Mapping)
        or set(private_families) != set(BLIND_FAMILIES)
        or any(
            isinstance(private_families[family], bool)
            or not isinstance(private_families[family], int)
            or private_families[family] < 0
            for family in BLIND_FAMILIES
        )
        or sum(private_families.values()) != blind_presentations
        or any(
            private_families[family]
            != sum(private_pools[pool]["families"][family] for pool in BLIND_POOLS)
            for family in BLIND_FAMILIES
        )
    ):
        raise ValueError("blind artifact mismatch: private totals")

    actual_blind_fact_ids: set[str] = set()
    if private_root is not None:
        for pool in BLIND_POOLS:
            pool_rows = private_rows_by_pool[pool]
            pool_fact_ids = [str(row.get("fact_id") or "") for row in pool_rows]
            if (
                not all(pool_fact_ids)
                or len(set(pool_fact_ids)) != len(pool_fact_ids)
                or Counter(blind_family(row.get("family")) for row in pool_rows)
                != Counter(private_pools[pool]["families"])
                or actual_blind_fact_ids.intersection(pool_fact_ids)
            ):
                raise ValueError("blind artifact mismatch: private blind facts")
            actual_blind_fact_ids.update(pool_fact_ids)
        if len(actual_blind_fact_ids) != blind_facts:
            raise ValueError("blind artifact mismatch: private blind facts")

    training_facts = _nonnegative_int(
        public_manifest.get("training_fact_count"), "training_fact_count"
    )
    training_presentations = _nonnegative_int(
        public_manifest.get("training_presentation_count"),
        "training_presentation_count",
    )
    if (
        public_manifest.get("unique_facts") != training_facts
        or public_manifest.get("gold_questions") != training_presentations
        or public_manifest.get("total_fact_count") != training_facts + blind_facts
        or public_manifest.get("total_presentation_count")
        != training_presentations + blind_presentations
    ):
        raise ValueError("blind artifact mismatch: public totals")
    training_central = _nonnegative_int(
        public_manifest.get("central_question_count"), "central_question_count"
    )
    training_variants = _nonnegative_int(
        public_manifest.get("presentation_variant_count"),
        "presentation_variant_count",
    )
    total_central = _nonnegative_int(
        public_manifest.get("total_central_question_count"),
        "total_central_question_count",
    )
    total_variants = _nonnegative_int(
        public_manifest.get("total_presentation_variant_count"),
        "total_presentation_variant_count",
    )
    if (
        training_central + training_variants != training_presentations
        or total_central + total_variants
        != training_presentations + blind_presentations
        or total_central != training_central + blind_presentations
        or total_variants != training_variants
    ):
        raise ValueError("blind artifact mismatch: role totals")
    public_families = public_manifest.get("families")
    if not isinstance(public_families, Mapping) or any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in public_families.values()
    ) or sum(public_families.values()) != training_presentations:
        raise ValueError("blind artifact mismatch: public families")

    public_shards = public_manifest.get("shards")
    if not isinstance(public_shards, list):
        raise ValueError("blind artifact mismatch: public shards")
    public_shard_total = 0
    public_rows: list[Mapping[str, Any]] = []
    for index, shard in enumerate(public_shards):
        if not isinstance(shard, Mapping):
            raise ValueError("blind artifact mismatch: invalid public shard")
        count = _nonnegative_int(
            shard.get("question_count"), "public shard question_count"
        )
        if shard.get("training_question_count") != count:
            raise ValueError("blind artifact mismatch: training shard count")
        payload = _descriptor_payload(
            shard,
            label=f"public shard {index}",
            path_key="questions_file",
            root=public_root,
            public_prefix="banks/final-2026/",
        )
        if payload is not None:
            try:
                rows = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError("blind artifact integrity mismatch: invalid public JSON") from exc
            if not isinstance(rows, list) or len(rows) != count:
                raise ValueError("blind artifact mismatch: public shard question_count")
            for row in rows:
                if not isinstance(row, Mapping):
                    raise ValueError("blind artifact mismatch: invalid public shard row")
                if row.get("role") not in {"central", "variant"}:
                    raise ValueError("blind artifact mismatch: public shard role")
                if row.get("blind_pool") is not None:
                    raise ValueError("blind artifact mismatch: public shard blind leak")
                if (
                    not isinstance(row.get("row_content_sha256"), str)
                    or row["row_content_sha256"] != emitted_row_hash(row)
                ):
                    raise ValueError(
                        "blind artifact mismatch: public review ledger row hash"
                    )
                public_rows.append(row)
        public_shard_total += count
    if public_shard_total != training_presentations:
        raise ValueError("blind artifact mismatch: public shard totals")
    if public_root is not None:
        actual_training_facts = {str(row.get("fact_id") or "") for row in public_rows}
        actual_roles = Counter(row.get("role") for row in public_rows)
        actual_families = Counter(row.get("family") for row in public_rows)
        if (
            "" in actual_training_facts
            or len(actual_training_facts) != training_facts
            or actual_roles["central"] != training_central
            or actual_roles["variant"] != training_variants
            or actual_families != Counter(public_families)
        ):
            raise ValueError("blind artifact mismatch: public shard totals")
        if actual_training_facts.intersection(actual_blind_fact_ids):
            raise ValueError("blind artifact mismatch: fact ownership")
        actual_blind_families = Counter(
            row.get("family")
            for pool in BLIND_POOLS
            for row in private_rows_by_pool[pool]
        )
        total_families = public_manifest.get("total_families")
        if (
            not isinstance(total_families, Mapping)
            or Counter(total_families) != actual_families + actual_blind_families
        ):
            raise ValueError("blind artifact mismatch: total families")

    domain_rows = {
        "public": public_rows,
        "private": [
            row
            for pool in BLIND_POOLS
            for row in private_rows_by_pool[pool]
        ],
    }
    if public_root is not None:
        public_ids = {str(row.get("id") or "") for row in domain_rows["public"]}
        private_ids = {str(row.get("id") or "") for row in domain_rows["private"]}
        if (
            "" in public_ids
            or "" in private_ids
            or len(public_ids) != len(domain_rows["public"])
            or len(private_ids) != len(domain_rows["private"])
            or public_ids.intersection(private_ids)
        ):
            raise ValueError("blind artifact mismatch: review ledger domain IDs")

    for domain, label, manifest, root, expected in (
        (
            "public",
            "public review-index",
            public_manifest,
            public_root,
            training_presentations,
        ),
        (
            "private",
            "private review-index",
            private_manifest,
            private_root,
            blind_presentations,
        ),
    ):
        payload = _descriptor_payload(
            manifest.get("review_index"),
            label=label,
            path_key="file",
            root=root,
            public_prefix="banks/final-2026/" if label.startswith("public") else "",
        )
        if payload is not None:
            try:
                review = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError("blind artifact integrity mismatch: review JSON") from exc
            if (
                not isinstance(review, Mapping)
                or review.get("total_reviewed") != expected
                or not isinstance(review.get("entries"), list)
                or len(review["entries"]) != expected
            ):
                raise ValueError("blind artifact mismatch: review ledger totals")
            expected_rows = domain_rows[domain]
            expected_ledger = {
                str(row["id"]): (
                    row["row_content_sha256"],
                    row.get("content_sha256"),
                )
                for row in expected_rows
            }
            entries = review["entries"]
            ledger_ids = [
                str(entry.get("question_id") or "")
                if isinstance(entry, Mapping)
                else ""
                for entry in entries
            ]
            if len(set(ledger_ids)) != len(ledger_ids) or set(ledger_ids) != set(
                expected_ledger
            ):
                raise ValueError(
                    f"blind artifact mismatch: {domain} review ledger IDs"
                )
            for entry in entries:
                question_id = str(entry["question_id"])
                row_digest, source_digest = expected_ledger[question_id]
                if (
                    entry.get("content_sha256") != row_digest
                    or entry.get("source_content_sha256") != source_digest
                ):
                    raise ValueError(
                        f"blind artifact mismatch: {domain} review ledger hash"
                    )
    expected_build_id = compute_artifact_build_id(public_manifest, private_manifest)
    if build_id != expected_build_id:
        raise ValueError("blind artifact mismatch: build_id descriptor digest")
    return build_id


def validate_emitted_pair(public_root: Path, private_root: Path) -> str:
    public_manifest = read_json(public_root / "manifest.json")
    private_manifest = read_json(private_root / "manifest.json")
    return validate_artifact_pair(
        public_manifest, private_manifest, public_root, private_root
    )


def public_question(raw: dict, unit: str) -> dict:
    row = {
        "id": raw["id"], "bank_id": BANK_ID, "bank_name": DISPLAY_NAME,
        "schema_version": SCHEMA_VERSION, "source_unit_id": raw["source_unit_id"],
        "fact_id": raw["fact_id"], "variant_id": raw["id"],
        "role": raw["role"],
        "template_id": "ai-authored-v11", "family": raw["family"],
        "subtype": raw["subtype"], "chapter": unit, "reference": raw["source_ref"],
        "source_ref": raw["source_ref"], "verse_or_page": raw["source_ref"],
        "source_span": raw["evidence_excerpt"], "source_quote": raw["source_quote"],
        "context_anchor": raw["evidence_excerpt"], "evidence_excerpt": raw["evidence_excerpt"],
        "topic": raw["subtype"], "importance": raw["importance"],
        "relation_type": raw["relation_type"], "option_category": raw["option_category"],
        "blind_pool": raw["blind_pool"], "question": raw["question"],
        "options": raw["options"], "correct_option": raw["correct_option"],
        "correct_answer": raw["correct_answer"], "accepted_answers": raw["accepted_answers"],
        "answer_mode": "option_id", "explanation": raw["explanation"],
        "why_distractors_fail": raw["why_distractors_fail"], "trap_type": None,
        "final_editorial_status": "GOLD", "difficulty": raw["difficulty"],
        "false_mutation": raw.get("false_mutation"), "ai_review": raw["ai_review"],
        "validation_adversarial": {
            "reviewer": raw["ai_review"]["reviewer"], "status": "passed",
            "selected_option": raw["correct_option"], "rationale": raw["explanation"],
            "second_defensible_option": False,
        },
        "content_sha256": content_hash(raw),
    }
    row["row_content_sha256"] = emitted_row_hash(row)
    return row


def compile_bank(
    source_root: Path,
    output: Path,
    *,
    blind_output: Path | None = None,
    blind_requirements: dict | None = None,
) -> dict:
    source_root, output, blind_output = validate_output_paths(
        source_root, output, blind_output
    )
    if blind_requirements is not None:
        blind_requirements = validate_blind_requirements(blind_requirements)
        if blind_output is None:
            raise ValueError("blind_output is required by the blind release gate")
    source_units = {}
    for path in sorted((source_root / "source-packets").glob("*.json")):
        for row in read_json(path).get("units", []):
            if "source_quote" in row:
                source_units[row["source_unit_id"]] = row

    rows_by_unit = {}
    all_rows = []
    for unit in EXPECTED_UNITS:
        rows = read_json(source_root / "questions" / f"{unit}.json")
        for row in rows:
            errors = validate_question(row, source_units)
            if errors:
                raise ValueError(f"{row['id']}: {', '.join(errors)}")
        rows_by_unit[unit] = rows
        all_rows.extend(rows)
    violations = {
        key: value
        for key, value in audit_corpus(
            all_rows, blind_requirements=blind_requirements
        ).items()
        if value
    }
    if violations:
        raise ValueError(f"Auditoría global falló: {violations}")
    blind_source_rows = [row for row in all_rows if row["blind_pool"] is not None]
    if blind_source_rows and blind_output is None:
        raise ValueError("blind_output is required when the corpus contains blind facts")

    temp = _stage_path(output)
    if temp.exists():
        shutil.rmtree(temp)
    (temp / "questions").mkdir(parents=True)
    blind_temp = None
    if blind_output is not None:
        blind_temp = _stage_path(blind_output)
        if blind_temp.exists():
            shutil.rmtree(blind_temp)
        blind_temp.mkdir(parents=True)
    shards = []
    blind_shards = {pool: [] for pool in BLIND_POOLS}
    training_review_entries = []
    blind_review_entries = []
    for unit, rows in rows_by_unit.items():
        public_rows = [public_question(row, unit) for row in rows]
        training_rows = [row for row in public_rows if row["blind_pool"] is None]
        integrity = write_json(temp / "questions" / f"{unit}.json", training_rows)
        shards.append({
            "chapter": unit, "question_count": len(training_rows),
            "training_question_count": len(training_rows),
            "questions_file": f"banks/final-2026/questions/{unit}.json",
            **integrity,
        })
        for pool in blind_shards:
            pool_rows = [row for row in public_rows if row["blind_pool"] == pool]
            if not pool_rows:
                continue
            assert blind_temp is not None
            integrity = write_json(
                blind_temp / "questions" / pool / f"{unit}.json", pool_rows
            )
            blind_shards[pool].append({
                "chapter": unit,
                "question_count": len(pool_rows),
                "questions_file": f"questions/{pool}/{unit}.json",
                **integrity,
            })
        training_review_entries.extend({
            "question_id": row["id"],
            "content_sha256": row["row_content_sha256"],
            "source_content_sha256": row["content_sha256"],
            "decision": "passed", "reviewer_type": row["ai_review"]["reviewer_type"],
            "reviewer": row["ai_review"]["reviewer"],
        } for row in training_rows)
        blind_review_entries.extend({
            "question_id": row["id"],
            "content_sha256": row["row_content_sha256"],
            "source_content_sha256": row["content_sha256"],
            "decision": "passed", "reviewer_type": row["ai_review"]["reviewer_type"],
            "reviewer": row["ai_review"]["reviewer"],
        } for row in public_rows if row["blind_pool"] is not None)
    training_source_rows = [row for row in all_rows if row["blind_pool"] is None]
    blind_rows = blind_source_rows
    artifact_revision = hashlib.sha256(
        "\n".join(sorted(content_hash(row) for row in all_rows)).encode("utf-8")
    ).hexdigest()
    training_roles = Counter(row["role"] for row in training_source_rows)
    total_roles = Counter(row["role"] for row in all_rows)
    blind_pools = {}
    private_pools = {}
    for pool, pool_shard_rows in blind_shards.items():
        pool_rows = [row for row in all_rows if row["blind_pool"] == pool]
        family_counts = Counter(blind_family(row["family"]) for row in pool_rows)
        metadata = {
            "fact_count": len({row["fact_id"] for row in pool_rows}),
            "presentation_count": len(pool_rows),
            "families": {
                family: family_counts[family] for family in BLIND_FAMILIES
            },
        }
        blind_pools[pool] = metadata
        private_pools[pool] = {**metadata, "shards": pool_shard_rows}
    public_review_integrity = write_json(temp / "review-index.json", {
        "schema_version": SCHEMA_VERSION,
        "total_reviewed": len(training_review_entries),
        "human_signatures": 0,
        "entries": training_review_entries,
    })
    manifest = {
        "schema_version": SCHEMA_VERSION, "bank_id": BANK_ID, "display_name": DISPLAY_NAME,
        "source": "MaterialConexionBiblica (1).pdf",
        "unique_facts": len({row["fact_id"] for row in training_source_rows}),
        "gold_questions": len(training_source_rows),
        "central_question_count": training_roles["central"],
        "presentation_variant_count": training_roles["variant"],
        "training_fact_count": len({row["fact_id"] for row in training_source_rows}),
        "training_presentation_count": len(training_source_rows),
        "total_fact_count": len({row["fact_id"] for row in all_rows}),
        "total_presentation_count": len(all_rows),
        "total_central_question_count": total_roles["central"],
        "total_presentation_variant_count": total_roles["variant"],
        "blind_fact_count": len({row["fact_id"] for row in blind_rows}),
        "blind_presentation_count": len(blind_rows),
        "blind_pools": blind_pools,
        "blind_delivery": {
            "contract": BLIND_DELIVERY_CONTRACT,
            "artifact_id": BLIND_ARTIFACT_ID,
            "artifact_revision": artifact_revision,
        },
        "families": Counter(row["family"] for row in training_source_rows),
        "total_families": Counter(row["family"] for row in all_rows),
        "review_index": {
            "file": "banks/final-2026/review-index.json",
            **public_review_integrity,
        },
        "shards": shards,
    }
    if blind_temp is not None:
        private_review_integrity = write_json(blind_temp / "review-index.json", {
            "schema_version": SCHEMA_VERSION,
            "total_reviewed": len(blind_review_entries),
            "human_signatures": 0,
            "entries": blind_review_entries,
        })
        private_manifest = {
            "contract": BLIND_DELIVERY_CONTRACT,
            "artifact_id": BLIND_ARTIFACT_ID,
            "artifact_revision": artifact_revision,
            "schema_version": SCHEMA_VERSION,
            "bank_id": BANK_ID,
            "total_fact_count": len({row["fact_id"] for row in blind_rows}),
            "total_presentation_count": len(blind_rows),
            "central_question_count": len(blind_rows),
            "presentation_variant_count": 0,
            "families": {
                family: sum(
                    private_pools[pool]["families"][family]
                    for pool in BLIND_POOLS
                )
                for family in BLIND_FAMILIES
            },
            "review_index": {
                "file": "review-index.json",
                **private_review_integrity,
            },
            "pools": private_pools,
        }
        build_id = compute_artifact_build_id(manifest, private_manifest)
        manifest["build_id"] = build_id
        private_manifest["build_id"] = build_id
        write_json(temp / "manifest.json", manifest)
        write_json(blind_temp / "manifest.json", private_manifest)
        validate_artifact_pair(manifest, private_manifest, temp, blind_temp)
        replace_artifact_pair(temp, output, blind_temp, blind_output)
    else:
        manifest["build_id"] = compute_artifact_build_id(manifest, None)
        write_json(temp / "manifest.json", manifest)
        replace_artifact(temp, output)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "content" / "competitive-v11")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--validate-pair",
        nargs=2,
        type=Path,
        metavar=("PUBLIC_ROOT", "PRIVATE_ROOT"),
        help="Valida un par ya emitido sin modificarlo.",
    )
    parser.add_argument(
        "--blind-output",
        type=Path,
        help="Directorio separado y privado para la reserva ciega.",
    )
    gate = parser.add_mutually_exclusive_group()
    gate.add_argument(
        "--require-blind-release",
        action="store_true",
        help="Exige la reserva oficial A/B/emergency antes de publicar.",
    )
    gate.add_argument(
        "--blind-requirements",
        type=Path,
        help="JSON con conteos y mezcla por pool para un gate personalizado.",
    )
    args = parser.parse_args()
    if args.validate_pair:
        try:
            build_id = validate_emitted_pair(*args.validate_pair)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"valid": True, "build_id": build_id}))
        return 0
    if args.output is None:
        parser.error("--output is required unless --validate-pair is used")
    blind_requirements = None
    if args.require_blind_release:
        blind_requirements = RELEASE_BLIND_REQUIREMENTS
    elif args.blind_requirements:
        blind_requirements = read_json(args.blind_requirements)
    try:
        manifest = compile_bank(
            args.source_root,
            args.output,
            blind_output=args.blind_output,
            blind_requirements=blind_requirements,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"output": str(args.output), "questions": manifest["gold_questions"], "facts": manifest["unique_facts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
