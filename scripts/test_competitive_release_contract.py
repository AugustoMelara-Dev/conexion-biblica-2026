from __future__ import annotations

import unittest

from scripts.lib import competitive_release_contract as contract


def release_rows(
    release: int,
    family_counts: dict[str, int],
    *,
    material_counts: dict[str, int] | None = None,
    translation_noise: int = 0,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    families: list[str] = []
    for family, count in family_counts.items():
        if family == "selection":
            families.extend(
                "single_choice_direct" if index % 2 == 0 else "single_choice_contextual"
                for index in range(count)
            )
        else:
            families.extend(family for _ in range(count))
    source_unit_for_material = {
        "DAN7-12": "DAN10-V001",
        "PR39-44": "PR39-P027-P001-S001",
        "DAN1-6": "DAN1-V001",
    }
    source_units = [
        source_unit_for_material[material]
        for material, count in (material_counts or {}).items()
        for _ in range(count)
    ]
    for index, family in enumerate(families):
        row: dict[str, object] = {
            "fact_id": f"R{release}-F{index + 1:04d}",
            "family": family,
        }
        if source_units:
            row["source_unit_id"] = source_units[index]
            row["translation_noise"] = index < translation_noise
        rows.append(row)
    return rows


class CompetitiveReleaseManifestTests(unittest.TestCase):
    def test_canonical_manifest_satisfies_the_v13_release_arithmetic(self) -> None:
        manifest = contract.expected_manifest()

        self.assertEqual(contract.validate_manifest(manifest), [])
        self.assertEqual(manifest["public_base"], 2468)
        self.assertEqual(manifest["release_2"]["new_count"], 2217)
        self.assertEqual(manifest["release_3"]["new_count"], 1315)
        self.assertEqual(manifest["final_count"], 6000)

    def test_manifest_reports_each_wrong_quota_with_an_explicit_path(self) -> None:
        manifest = contract.expected_manifest()
        manifest["public_base"] = 2467
        manifest["release_2"]["families"]["selection"] = 997
        manifest["release_3"]["materials"]["PR39-44"] = 394
        manifest["release_3"]["translation_noise"] = 197
        manifest["final_count"] = 5999

        self.assertEqual(
            contract.validate_manifest(manifest),
            [
                "manifest.public_base: expected 2468, got 2467",
                "manifest.release_2.families.selection: expected 998, got 997",
                "manifest.release_3.materials.PR39-44: expected 395, got 394",
                "manifest.release_3.translation_noise: expected 198, got 197",
                "manifest.final_count: expected 6000, got 5999",
            ],
        )

    def test_manifest_missing_values_are_errors_instead_of_defaults(self) -> None:
        manifest = contract.expected_manifest()
        del manifest["release_2"]["new_count"]

        self.assertEqual(
            contract.validate_manifest(manifest),
            ["manifest.release_2.new_count: expected 2217, got <missing>"],
        )

    def test_expected_manifest_returns_an_independent_value(self) -> None:
        first = contract.expected_manifest()
        first["release_2"]["families"]["selection"] = 0

        self.assertEqual(
            contract.expected_manifest()["release_2"]["families"]["selection"],
            998,
        )


class CompetitiveReleaseCheckpointTests(unittest.TestCase):
    def test_family_normalization_ignores_malformed_metadata(self) -> None:
        self.assertIsNone(contract.normalize_family(["single_choice_direct"]))

    def test_real_competitive_rows_normalize_family_and_derive_material_group(self) -> None:
        # Minimal copies of the real competitive-v11 question schema.  Question
        # prose is intentionally omitted because this is a quota/identity gate.
        real_rows = [
            {
                "id": "Q-DAN10-CENTRAL-0001",
                "source_unit_id": "DAN10-V001",
                "fact_id": "DAN10-V001-F04",
                "family": "single_choice_direct",
            },
            {
                "id": "PR41-V11-BLIND-A-021",
                "source_unit_id": "PR41-P039-P002-S002",
                "fact_id": "PR41-P039-P002-S002-V11-BA-F01",
                "family": "single_choice_contextual",
            },
            {
                "id": "Q-DAN1-0001",
                "source_unit_id": "DAN1-V001",
                "fact_id": "DAN1-V001-F04",
                "family": "true_false",
            },
        ]

        self.assertEqual(
            [contract.normalize_family(row["family"]) for row in real_rows],
            ["selection", "selection", "true_false"],
        )
        self.assertEqual(
            [contract.derive_material_group(row) for row in real_rows],
            ["DAN7-12", "PR39-44", "DAN1-6"],
        )

    def test_release_2_accepts_exact_counts_and_one_fact_per_question(self) -> None:
        rows = release_rows(
            2,
            {"selection": 998, "fill_choice": 665, "true_false": 554},
        )

        self.assertEqual(
            contract.validate_checkpoint({"release": 2, "rows": rows}),
            [],
        )

    def test_release_2_reports_total_family_and_duplicate_fact_failures(self) -> None:
        rows = release_rows(
            2,
            {"selection": 998, "fill_choice": 665, "true_false": 553},
        )
        rows[1]["fact_id"] = rows[0]["fact_id"]

        self.assertEqual(
            contract.validate_checkpoint({"release": 2, "rows": rows}),
            [
                "checkpoint.release_2.rows: expected 2217, got 2216",
                "checkpoint.release_2.fact_id: duplicate R2-F0001",
                "checkpoint.release_2.families.true_false: expected 554, got 553",
            ],
        )

    def test_checkpoint_rejects_fact_ids_already_present_in_the_public_base(self) -> None:
        rows = release_rows(
            2,
            {"selection": 998, "fill_choice": 665, "true_false": 554},
        )

        self.assertEqual(
            contract.validate_checkpoint(
                {"release": 2, "rows": rows},
                base_fact_ids={"R2-F0001", "PUBLIC-EXISTING"},
            ),
            ["checkpoint.release_2.fact_id: collides with base R2-F0001"],
        )

    def test_release_3_accepts_exact_family_material_and_noise_counts(self) -> None:
        rows = release_rows(
            3,
            {"selection": 592, "fill_choice": 394, "true_false": 329},
            material_counts={"DAN7-12": 592, "PR39-44": 395, "DAN1-6": 328},
            translation_noise=198,
        )

        self.assertEqual(
            contract.validate_checkpoint({"release": 3, "rows": rows}),
            [],
        )

    def test_release_3_reports_material_noise_and_missing_fact_failures(self) -> None:
        rows = release_rows(
            3,
            {"selection": 592, "fill_choice": 394, "true_false": 329},
            material_counts={"DAN7-12": 592, "PR39-44": 394, "DAN1-6": 329},
            translation_noise=197,
        )
        del rows[0]["fact_id"]

        self.assertEqual(
            contract.validate_checkpoint({"release": 3, "rows": rows}),
            [
                "checkpoint.release_3.fact_id: missing at row 0",
                "checkpoint.release_3.materials.PR39-44: expected 395, got 394",
                "checkpoint.release_3.materials.DAN1-6: expected 328, got 329",
                "checkpoint.release_3.translation_noise: expected 198, got 197",
            ],
        )

    def test_checkpoint_rejects_unknown_release_and_malformed_rows(self) -> None:
        self.assertEqual(
            contract.validate_checkpoint({"release": 4, "rows": []}),
            ["checkpoint.release: expected 2 or 3, got 4"],
        )
        self.assertEqual(
            contract.validate_checkpoint({"release": 2, "rows": "not-a-list"}),
            ["checkpoint.release_2.rows: expected list, got str"],
        )


if __name__ == "__main__":
    unittest.main()
