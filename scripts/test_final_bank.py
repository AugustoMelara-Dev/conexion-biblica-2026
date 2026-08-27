from __future__ import annotations

import importlib
import unittest


class FinalBankContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.contract = importlib.import_module("scripts.lib.final_bank")
        except ModuleNotFoundError:
            cls.contract = None

    def test_exposes_one_canonical_identity_and_exactly_four_families(self) -> None:
        self.assertIsNotNone(self.contract, "falta scripts.lib.final_bank")
        assert self.contract is not None
        self.assertEqual(
            self.contract.BANK_ID, "BANCO_UNICO_CONEXION_BIBLICA_2026"
        )
        self.assertEqual(
            self.contract.DISPLAY_NAME, "Banco Maestro Único — Final 2026"
        )
        self.assertEqual(self.contract.SCHEMA_VERSION, "9.0")
        self.assertEqual(
            set(self.contract.QUESTION_FAMILIES),
            {
                "single_choice_direct",
                "fill_choice",
                "true_false",
                "single_choice_contextual",
            },
        )

    def test_gold_gate_rejects_legacy_family_and_wrong_option_count(self) -> None:
        self.assertIsNotNone(self.contract, "falta scripts.lib.final_bank")
        assert self.contract is not None
        base = {
            "id": "Q1",
            "bank_id": self.contract.BANK_ID,
            "family": "free_text",
            "options": [],
            "correct_option": 0,
            "source_unit_id": "DAN1-V001",
            "fact_id": "DAN1-V001-F01",
            "source_quote": "En el tercer año del reinado de Joacim",
            "final_editorial_status": "GOLD",
        }
        errors = self.contract.validate_gold_bank([base])
        self.assertIn("Q1:invalid_family", errors)
        self.assertIn("Q1:invalid_option_count", errors)

    def test_coverage_gate_rejects_uncovered_units_and_facts_without_gold(self) -> None:
        self.assertIsNotNone(self.contract, "falta scripts.lib.final_bank")
        assert self.contract is not None
        manifest = {
            "uncovered_source_units": 1,
            "fact_without_gold_question": 2,
            "unmapped_source_units": 1,
            "units": [
                {
                    "source_unit_id": "DAN1-V001",
                    "fact_ids": ["DAN1-V001-F01"],
                    "gold_question_ids": [],
                    "coverage_status": "uncovered",
                }
            ],
        }
        errors = self.contract.validate_coverage(manifest)
        self.assertIn("uncovered_source_units=1", errors)
        self.assertIn("fact_without_gold_question=2", errors)
        self.assertIn("unmapped_source_units=1", errors)
        self.assertIn("DAN1-V001:missing_gold_questions", errors)


if __name__ == "__main__":
    unittest.main()
