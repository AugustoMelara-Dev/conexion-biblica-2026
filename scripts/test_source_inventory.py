from __future__ import annotations

import importlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "MaterialConexionBiblica (1).pdf"
OCR_CACHE = ROOT / "scripts/source-cache/final-v7/ocr-pages.json"


class SourceInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.inventory = importlib.import_module("scripts.lib.source_inventory")
        except ModuleNotFoundError:
            cls.inventory = None

    def test_repairs_only_corrupted_pdf_glyphs_from_ocr_context(self) -> None:
        self.assertIsNotNone(self.inventory, "falta scripts.lib.source_inventory")
        assert self.inventory is not None
        restored, issues = self.inventory.restore_corrupted_glyphs(
            "El Se�or entreg� a Babil�nia evidencia de su supremac�a.",
            "El Señor entregó a Babilonia evidencia de su supremacía.",
        )
        self.assertEqual(
            restored, "El Señor entregó a Babilonia evidencia de su supremacía."
        )
        self.assertEqual(issues, [])

    def test_extracts_exactly_357_daniel_verses_with_fact_placeholders(self) -> None:
        self.assertIsNotNone(self.inventory, "falta scripts.lib.source_inventory")
        self.assertTrue(OCR_CACHE.exists(), "falta caché OCR generado desde el PDF")
        assert self.inventory is not None
        pages = json.loads(OCR_CACHE.read_text(encoding="utf-8"))["pages"]
        with fitz.open(PDF) as document:
            units, issues = self.inventory.extract_daniel_inventory(document, pages)
        self.assertEqual(len(units), 357)
        self.assertEqual({unit["chapter"] for unit in units}, set(range(1, 13)))
        self.assertEqual(units[0]["source_unit_id"], "DAN1-V001")
        self.assertEqual(units[-1]["source_unit_id"], "DAN12-V013")
        self.assertTrue(all(unit["full_text"].strip() for unit in units))
        self.assertTrue(all("�" not in unit["full_text"] for unit in units))
        self.assertTrue(all(unit["meaningful_clauses"] for unit in units))
        self.assertEqual([issue for issue in issues if issue["status"] == "unresolved"], [])

    def test_extracts_pr_propositions_from_every_page_27_through_59(self) -> None:
        self.assertIsNotNone(self.inventory, "falta scripts.lib.source_inventory")
        self.assertTrue(OCR_CACHE.exists(), "falta caché OCR generado desde el PDF")
        assert self.inventory is not None
        pages = json.loads(OCR_CACHE.read_text(encoding="utf-8"))["pages"]
        with fitz.open(PDF) as document:
            units, issues = self.inventory.extract_pr_inventory(document, pages)
        self.assertEqual({unit["page"] for unit in units}, set(range(27, 60)))
        self.assertTrue(all(unit["paragraph"] >= 1 for unit in units))
        self.assertTrue(all(unit["proposition"] >= 1 for unit in units))
        self.assertTrue(all(unit["exact_text"].strip() for unit in units))
        self.assertTrue(all("�" not in unit["exact_text"] for unit in units))
        self.assertEqual([issue for issue in issues if issue["status"] == "unresolved"], [])

    def test_builds_combined_inventory_with_no_unresolved_source_units(self) -> None:
        self.assertIsNotNone(self.inventory, "falta scripts.lib.source_inventory")
        self.assertTrue(OCR_CACHE.exists(), "falta caché OCR generado desde el PDF")
        assert self.inventory is not None
        self.assertTrue(
            hasattr(self.inventory, "build_source_inventory"),
            "falta build_source_inventory",
        )
        if not hasattr(self.inventory, "build_source_inventory"):
            return
        pages = json.loads(OCR_CACHE.read_text(encoding="utf-8"))["pages"]
        inventory, issue_report = self.inventory.build_source_inventory(PDF, pages)
        self.assertEqual(inventory["schema_version"], "7.0")
        self.assertEqual(inventory["daniel_verses"], 357)
        self.assertGreater(inventory["pr_propositions"], 600)
        self.assertEqual(inventory["source_units"], len(inventory["units"]))
        self.assertEqual(issue_report["unresolved_count"], 0)

    def test_build_cli_runs_from_repository_root(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/build-final-bank.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
