"""Quota and identity gate for the competitive v13 releases.

This module validates normalized family/material quotas and fact identifiers
only.  It deliberately neither creates nor transforms authored question text.
"""

from __future__ import annotations

import re
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "competitive-release-contract/v13"
PUBLIC_BASE_COUNT = 2468
FINAL_COUNT = 6000

RELEASE_SPECS: dict[int, dict[str, Any]] = {
    2: {
        "new_count": 2217,
        "families": {
            "selection": 998,
            "fill_choice": 665,
            "true_false": 554,
        },
    },
    3: {
        "new_count": 1315,
        "families": {
            "selection": 592,
            "fill_choice": 394,
            "true_false": 329,
        },
        "materials": {
            "DAN7-12": 592,
            "PR39-44": 395,
            "DAN1-6": 328,
        },
        "translation_noise": 198,
    },
}

_MISSING = object()
_SOURCE_UNIT_PREFIX = re.compile(
    r"^(DAN(?:1[0-2]|[1-9])|PR(?:3[9]|4[0-4]))(?:-|$)"
)


def normalize_family(family: object) -> str | None:
    """Map real question families to the three release quota buckets."""

    if not isinstance(family, str):
        return None
    if family in {"single_choice_direct", "single_choice_contextual"}:
        return "selection"
    if family in {"fill_choice", "true_false"}:
        return family
    return None


def derive_material_group(row: Mapping[str, Any] | object) -> str | None:
    """Derive an R3 material group from competitive question metadata."""

    if not isinstance(row, Mapping):
        return None

    source_unit_id = row.get("source_unit_id")
    if isinstance(source_unit_id, str):
        match = _SOURCE_UNIT_PREFIX.match(source_unit_id.upper())
        if match:
            unit = match.group(1)
            if unit.startswith("PR"):
                return "PR39-44"
            chapter = int(unit[3:])
            return "DAN7-12" if chapter >= 7 else "DAN1-6"

    chapter = row.get("chapter")
    if isinstance(chapter, str) and chapter.isdigit():
        chapter = int(chapter)
    if isinstance(chapter, int) and not isinstance(chapter, bool):
        if 1 <= chapter <= 6:
            return "DAN1-6"
        if 7 <= chapter <= 12:
            return "DAN7-12"
        if 39 <= chapter <= 44:
            return "PR39-44"
    return None


def expected_manifest() -> dict[str, Any]:
    """Return a mutable, independent copy of the canonical v13 manifest."""

    return {
        "schema_version": SCHEMA_VERSION,
        "public_base": PUBLIC_BASE_COUNT,
        "release_2": deepcopy(RELEASE_SPECS[2]),
        "release_3": deepcopy(RELEASE_SPECS[3]),
        "final_count": FINAL_COUNT,
    }


def _shown(value: object) -> str:
    return "<missing>" if value is _MISSING else repr(value) if isinstance(value, str) else str(value)


def _compare(path: str, actual: object, expected: object, errors: list[str]) -> None:
    if actual != expected:
        errors.append(f"{path}: expected {_shown(expected)}, got {_shown(actual)}")


def _child(value: object, key: str) -> object:
    if not isinstance(value, Mapping):
        return _MISSING
    return value.get(key, _MISSING)


def validate_manifest(manifest: Mapping[str, Any] | object) -> list[str]:
    """Return every quota mismatch in stable contract order."""

    if not isinstance(manifest, Mapping):
        return [f"manifest: expected mapping, got {type(manifest).__name__}"]

    errors: list[str] = []
    expected = expected_manifest()
    _compare(
        "manifest.schema_version",
        manifest.get("schema_version", _MISSING),
        expected["schema_version"],
        errors,
    )
    _compare(
        "manifest.public_base",
        manifest.get("public_base", _MISSING),
        expected["public_base"],
        errors,
    )

    for release in (2, 3):
        release_key = f"release_{release}"
        actual_release = manifest.get(release_key, _MISSING)
        spec = RELEASE_SPECS[release]
        _compare(
            f"manifest.{release_key}.new_count",
            _child(actual_release, "new_count"),
            spec["new_count"],
            errors,
        )
        actual_families = _child(actual_release, "families")
        for family, count in spec["families"].items():
            _compare(
                f"manifest.{release_key}.families.{family}",
                _child(actual_families, family),
                count,
                errors,
            )
        if release == 3:
            actual_materials = _child(actual_release, "materials")
            for material, count in spec["materials"].items():
                _compare(
                    f"manifest.{release_key}.materials.{material}",
                    _child(actual_materials, material),
                    count,
                    errors,
                )
            _compare(
                f"manifest.{release_key}.translation_noise",
                _child(actual_release, "translation_noise"),
                spec["translation_noise"],
                errors,
            )

    _compare(
        "manifest.final_count",
        manifest.get("final_count", _MISSING),
        expected["final_count"],
        errors,
    )
    return errors


def validate_checkpoint(
    checkpoint: Mapping[str, Any] | object,
    *,
    base_fact_ids: Iterable[str] | None = None,
    base_fact_sources: Mapping[str, str] | None = None,
) -> list[str]:
    """Validate one metadata checkpoint as a quota and fact-identity gate.

    ``base_fact_ids`` optionally enforces the identity relationship with the
    central public base: Release 2 must reuse it exactly once; Release 3 must
    select only a subset. Reuse is intentional and is not a collision.
    """

    if not isinstance(checkpoint, Mapping):
        return [f"checkpoint: expected mapping, got {type(checkpoint).__name__}"]

    release = checkpoint.get("release", _MISSING)
    if release not in RELEASE_SPECS:
        return [f"checkpoint.release: expected 2 or 3, got {_shown(release)}"]

    spec = RELEASE_SPECS[release]
    prefix = f"checkpoint.release_{release}"
    rows = checkpoint.get("rows", _MISSING)
    if not isinstance(rows, list):
        return [f"{prefix}.rows: expected list, got {type(rows).__name__}"]

    errors: list[str] = []
    _compare(f"{prefix}.rows", len(rows), spec["new_count"], errors)

    fact_ids: list[str] = []
    families: Counter[str] = Counter()
    materials: Counter[str] = Counter()
    translation_noise = 0
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"{prefix}.row: expected mapping at row {index}")
            continue
        fact_id = row.get("fact_id")
        if not isinstance(fact_id, str) or not fact_id:
            errors.append(f"{prefix}.fact_id: missing at row {index}")
        else:
            fact_ids.append(fact_id)
            if base_fact_sources is not None and fact_id in base_fact_sources:
                if row.get("source_unit_id") != base_fact_sources[fact_id]:
                    errors.append(
                        f"{prefix}.fact_source: mismatch {fact_id} at row {index}"
                    )
        family = normalize_family(row.get("family"))
        if family is not None:
            families[family] += 1
        if release == 3:
            material = derive_material_group(row)
            if material is not None:
                materials[material] += 1
            if row.get("translation_noise") is True:
                translation_noise += 1

    duplicates = sorted(
        fact_id for fact_id, count in Counter(fact_ids).items() if count > 1
    )
    errors.extend(f"{prefix}.fact_id: duplicate {fact_id}" for fact_id in duplicates)

    if base_fact_ids is not None or base_fact_sources is not None:
        base_ids = set(base_fact_ids or ()) | set((base_fact_sources or {}).keys())
        release_ids = set(fact_ids)
        if release == 2:
            errors.extend(
                f"{prefix}.fact_ids: missing base {fact_id}"
                for fact_id in sorted(base_ids - release_ids)
            )
        errors.extend(
            f"{prefix}.fact_ids: not in base {fact_id}"
            for fact_id in sorted(release_ids - base_ids)
        )

    for family, count in spec["families"].items():
        _compare(f"{prefix}.families.{family}", families[family], count, errors)

    if release == 3:
        for material, count in spec["materials"].items():
            _compare(f"{prefix}.materials.{material}", materials[material], count, errors)
        _compare(
            f"{prefix}.translation_noise",
            translation_noise,
            spec["translation_noise"],
            errors,
        )

    return errors
