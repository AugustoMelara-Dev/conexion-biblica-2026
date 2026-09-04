from __future__ import annotations

import copy
import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "MaterialConexionBiblica (1).pdf"
OCR_CACHE = ROOT / "scripts" / "source-cache" / "final-v7" / "ocr-pages.json"
LEDGER_JSON = ROOT / "content" / "final-day-v18" / "source-ledger.json"
LEDGER_CSV = ROOT / "content" / "final-day-v18" / "source-ledger.csv"
LEDGER_MD = ROOT / "content" / "final-day-v18" / "source-ledger.md"

EXPECTED_SOURCE_SHA256 = (
    "0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3"
)
ALLOWED_COVERAGE = {
    "COVERED",
    "COVERED_MERGED",
    "NEEDS_QUESTION",
    "NON_ATOMIC",
    "REFERENCE_ONLY",
    "AMBIGUOUS_SOURCE",
}
REQUIRED_UNIT_FIELDS = {
    "source_unit_id",
    "work",
    "chapter",
    "verse_or_page",
    "pdf_page",
    "exact_quote",
    "nearby_context",
    "atomic_facts",
    "current_question_ids",
    "presentation_count",
    "distinct_cognitive_operations",
    "coverage_status",
    "explanation",
}


class FinalDayV18LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from scripts.build_final_day_v18_ledger import build_ledger
        except ModuleNotFoundError:
            cls.build_ledger = None
            return
        cls.build_ledger = build_ledger

    def test_real_ledger_has_canonical_source_and_atomic_units(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)

        self.assertEqual(ledger["source_sha256"], EXPECTED_SOURCE_SHA256)
        self.assertEqual(ledger["pdf_page_count"], 60)
        self.assertEqual(ledger["ocr_cache"]["source_sha256"], EXPECTED_SOURCE_SHA256)
        self.assertEqual(ledger["counts"]["source_units"], 1031)
        self.assertEqual(ledger["counts"]["daniel_verses"], 357)
        self.assertEqual(ledger["counts"]["pr_propositions"], 674)

        units = ledger["units"]
        self.assertEqual(len(units), 1031)
        self.assertEqual(
            len({unit["source_unit_id"] for unit in units}),
            len(units),
        )
        self.assertTrue(
            all(REQUIRED_UNIT_FIELDS.issubset(unit) for unit in units),
            "cada unidad debe exponer el contrato del ledger",
        )
        self.assertTrue(
            all(unit["coverage_status"] in ALLOWED_COVERAGE for unit in units)
        )
        self.assertTrue(all(unit["pdf_page"] >= 1 for unit in units))
        self.assertTrue(all(unit["exact_quote"].strip() for unit in units))

    def test_comparison_keeps_unmapped_current_questions_visible(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)
        current = ledger["comparison"]["current_bank"]

        self.assertEqual(current["question_count"], 3873)
        self.assertEqual(current["mapped_question_count"], 3633)
        self.assertEqual(current["unmapped_question_count"], 240)
        self.assertGreaterEqual(current["covered_source_units"], 1024)
        self.assertEqual(current["fact_id_count"], 2217)
        self.assertFalse(ledger["coverage_semantics"]["semantic_coverage_verified"])
        self.assertEqual(
            ledger["coverage_semantics"]["COVERED"],
            "SOURCE_UNIT_ID_LINK_ONLY",
        )
        self.assertEqual(
            ledger["comparison"]["historical_master"]["declared_fact_count"],
            2606,
        )
        self.assertEqual(
            ledger["comparison"]["historical_master"]["fact_count"],
            2606,
        )
        self.assertEqual(
            ledger["comparison"]["historical_master"]["fact_id_count"],
            2606,
        )

    def test_ocr_mismatch_is_ambiguous_and_not_silently_repaired(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)
        units = {unit["source_unit_id"]: unit for unit in ledger["units"]}

        self.assertEqual(
            units["PR39-P027-P002-S002"]["coverage_status"],
            "AMBIGUOUS_SOURCE",
        )
        self.assertIn("OCR", units["PR39-P027-P002-S002"]["explanation"])
        self.assertEqual(
            units["DAN1-V001"]["coverage_status"],
            "COVERED",
        )

    def test_multifact_unit_exposes_stable_atomic_children_and_link_only_basis(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)
        unit = next(item for item in ledger["units"] if item["source_unit_id"] == "DAN2-V002")

        self.assertEqual(unit["coverage_status"], "COVERED_MERGED")
        self.assertEqual(len(unit["atomic_facts"]), 2)
        self.assertEqual(
            [child["atomic_fact_id"] for child in unit["atomic_fact_records"]],
            ["DAN2-V002-F01", "DAN2-V002-F02"],
        )
        self.assertTrue(all(child["is_atomic"] for child in unit["atomic_fact_records"]))
        self.assertTrue(
            all(
                child["parent_source_unit_id"] == "DAN2-V002"
                and child["coverage_scope"] == "ATOMIC_FACT"
                for child in unit["atomic_fact_records"]
            )
        )
        self.assertEqual(unit["coverage_basis"], "SOURCE_UNIT_ID_LINK_ONLY")
        self.assertFalse(unit["semantic_coverage_verified"])
        self.assertEqual(unit["coverage_scope"], "SOURCE_UNIT")

    def test_references_and_anaforic_fragments_are_not_authoring_gaps(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)
        units = {unit["source_unit_id"]: unit for unit in ledger["units"]}

        self.assertEqual(units["PR39-P027-P001-S005"]["coverage_status"], "NON_ATOMIC")
        self.assertFalse(
            units["PR39-P027-P001-S005"]["atomic_fact_records"][0]["is_atomic"]
        )
        for source_unit_id in (
            "PR40-P037-P004-S002",
            "PR43-P050-P006-S004",
            "PR43-P051-P001-S004",
            "PR43-P052-P004-S005",
            "PR44-P058-P003-S006",
        ):
            self.assertEqual(units[source_unit_id]["coverage_status"], "REFERENCE_ONLY")
            self.assertFalse(units[source_unit_id]["atomic_fact_records"][0]["is_atomic"])

        needs_question = {
            unit["source_unit_id"]
            for unit in ledger["units"]
            if unit["coverage_status"] == "NEEDS_QUESTION"
        }
        self.assertEqual(needs_question, {"PR40-P036-P001-S004"})
        self.assertTrue(
            all(
                unit["coverage_status"] != "NEEDS_QUESTION"
                for unit in ledger["units"]
                if "referencia" in unit["explanation"].lower()
                or "anaf" in unit["explanation"].lower()
            )
        )

    def test_pr_units_retain_page_paragraph_and_proposition_identity(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)
        unit = next(
            item
            for item in ledger["units"]
            if item["source_unit_id"] == "PR40-P037-P004-S002"
        )

        self.assertEqual(unit["work"], "Profetas y Reyes")
        self.assertEqual(unit["chapter"], 40)
        self.assertEqual(unit["pdf_page"], 37)
        self.assertIn("p. 37", unit["verse_or_page"])
        self.assertIn("párrafo 4", unit["verse_or_page"])
        self.assertRegex(unit["source_unit_id"], r"^PR40-P037-P004-S002$")

    def test_nearby_context_does_not_cross_chapter_boundaries(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)
        units = {unit["source_unit_id"]: unit for unit in ledger["units"]}

        daniel_one_last = units["DAN1-V021"]
        daniel_two_first = units["DAN2-V001"]
        self.assertNotIn(daniel_two_first["exact_quote"], daniel_one_last["nearby_context"])
        self.assertNotIn(daniel_one_last["exact_quote"], daniel_two_first["nearby_context"])
        self.assertEqual(daniel_one_last["context_boundary"], "CHAPTER")
        self.assertEqual(daniel_two_first["context_boundary"], "CHAPTER")

        pr_first = units["PR39-P027-P001-S001"]
        self.assertEqual(pr_first["context_boundary"], "WORK")
        self.assertNotIn(daniel_two_first["exact_quote"], pr_first["nearby_context"])

    def test_heuristic_units_carry_visual_review_evidence(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        ledger = build_ledger(ROOT)
        units = {unit["source_unit_id"]: unit for unit in ledger["units"]}

        split_unit = units["DAN2-V002"]
        self.assertTrue(split_unit["requires_visual_review"])
        self.assertIn("ATOMIC_SPLIT_HEURISTIC", split_unit["review_flags"])
        self.assertEqual(split_unit["visual_review_status"], "REVIEW_REQUIRED")

        ocr_unit = units["DAN5-V018"]
        self.assertTrue(ocr_unit["requires_visual_review"])
        self.assertIn("OCR_MARKER_CONFLICT", ocr_unit["review_flags"])
        self.assertEqual(
            ledger["visual_review"]["reviewed_pdf_pages"],
            [3, 13, 27, 33, 59],
        )
        self.assertEqual(ledger["visual_review"]["total_sample_count"], 5)
        self.assertEqual(ledger["visual_review"]["reviewed_flagged_sample_count"], 3)
        self.assertEqual(ledger["visual_review"]["unreviewed_flagged_unit_count"], 305)
        self.assertEqual(
            ledger["source_inventory_evidence"]["restoration_policy"],
            "OCR_GLYPH_ONLY_UNRESOLVED_REMAINS_AMBIGUOUS",
        )
        self.assertEqual(ledger["source_inventory_evidence"]["unresolved_issue_count"], 0)

    def test_validate_rejects_duplicate_atomic_fact_id(self) -> None:
        from scripts.build_final_day_v18_ledger import validate_ledger

        ledger = copy.deepcopy(type(self).build_ledger(ROOT))
        first_id = ledger["units"][0]["atomic_fact_records"][0]["atomic_fact_id"]
        ledger["units"][1]["atomic_fact_records"][0]["atomic_fact_id"] = first_id

        with self.assertRaisesRegex(ValueError, "atomic_fact_id_duplicate"):
            validate_ledger(ledger)

    def test_validate_rejects_atomic_child_parent_mismatch(self) -> None:
        from scripts.build_final_day_v18_ledger import validate_ledger

        ledger = copy.deepcopy(type(self).build_ledger(ROOT))
        ledger["units"][0]["atomic_fact_records"][0]["parent_source_unit_id"] = "DAN99-V999"

        with self.assertRaisesRegex(ValueError, "atomic_parent"):
            validate_ledger(ledger)

    def test_validate_rejects_empty_atomic_child_text(self) -> None:
        from scripts.build_final_day_v18_ledger import validate_ledger

        ledger = copy.deepcopy(type(self).build_ledger(ROOT))
        ledger["units"][0]["atomic_fact_records"][0]["text"] = "   "

        with self.assertRaisesRegex(ValueError, "atomic_text_empty"):
            validate_ledger(ledger)

    def test_validate_rejects_atomic_text_not_in_parent_quote(self) -> None:
        from scripts.build_final_day_v18_ledger import validate_ledger

        ledger = copy.deepcopy(type(self).build_ledger(ROOT))
        ledger["units"][0]["atomic_fact_records"][0]["text"] = (
            "Texto inventado que no aparece en la cita."
        )

        with self.assertRaisesRegex(ValueError, "atomic_text_not_in_quote"):
            validate_ledger(ledger)

    def test_validate_rejects_semantic_basis_and_mixed_status_mutations(self) -> None:
        from scripts.build_final_day_v18_ledger import validate_ledger

        original = type(self).build_ledger(ROOT)
        multi_index = next(
            index
            for index, unit in enumerate(original["units"])
            if len(unit["atomic_fact_records"]) > 1
        )
        mutations = (
            ("semantic_flag", lambda ledger: ledger["units"][0].__setitem__("semantic_coverage_verified", True)),
            ("parent_coverage_basis", lambda ledger: ledger["units"][0].__setitem__("coverage_basis", "NO_CURRENT_SOURCE_UNIT_LINK")),
            ("mixed_child_status", lambda ledger: ledger["units"][multi_index]["atomic_fact_records"][0].__setitem__("coverage_status", "AMBIGUOUS_SOURCE")),
        )
        for expected_error, mutate in mutations:
            with self.subTest(expected_error=expected_error):
                ledger = copy.deepcopy(original)
                mutate(ledger)
                with self.assertRaisesRegex(ValueError, expected_error):
                    validate_ledger(ledger)

    def test_cli_writes_json_csv_and_markdown_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_final_day_v18_ledger.py",
                    "--output-dir",
                    first_dir,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            first_paths = tuple(Path(first_dir) / name for name in (
                "source-ledger.json",
                "source-ledger.csv",
                "source-ledger.md",
            ))
            for path in first_paths:
                self.assertTrue(path.exists(), f"falta salida {path.name}")

            payload = json.loads(first_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["counts"]["source_units"], 1031)
            self.assertIn("source_unit_id", first_paths[1].read_text(encoding="utf-8"))
            self.assertIn("Source ledger V18", first_paths[2].read_text(encoding="utf-8"))

    def test_cli_is_byte_deterministic_in_distinct_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            for output_dir in (first_dir, second_dir):
                result = subprocess.run(
                    [
                        sys.executable,
                        "scripts/build_final_day_v18_ledger.py",
                        "--output-dir",
                        output_dir,
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            for name in ("source-ledger.json", "source-ledger.csv", "source-ledger.md"):
                first = (Path(first_dir) / name).read_bytes()
                second = (Path(second_dir) / name).read_bytes()
                self.assertEqual(hashlib.sha256(first).digest(), hashlib.sha256(second).digest())

    def test_cache_hash_mismatch_is_rejected(self) -> None:
        build_ledger = type(self).build_ledger
        self.assertIsNotNone(build_ledger, "falta el builder del ledger V18")
        assert build_ledger is not None
        payload = json.loads(OCR_CACHE.read_text(encoding="utf-8"))
        payload["source_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_cache = Path(temp_dir) / "ocr-pages.json"
            bad_cache.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                build_ledger(ROOT, ocr_cache_path=bad_cache)


if __name__ == "__main__":
    unittest.main()
