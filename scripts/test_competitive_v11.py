"""Pruebas del pipeline editorial competitivo V11."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts.lib.production_snapshot_v11 import import_production_snapshot
from scripts.lib.source_packets_v11 import build_source_packets
from scripts.lib.competitive_v11 import audit_corpus, content_hash, validate_question


def valid_v11_question(**overrides):
    row = {
        "id": "DAN1-V11-0001",
        "source_unit_id": "DAN1-V001",
        "fact_id": "DAN1-V001-F01",
        "role": "central",
        "family": "single_choice_direct",
        "subtype": "factual_recall",
        "question": "¿Quién sitió Jerusalén durante el tercer año del reinado de Joacim?",
        "options": ["Nabucodonosor", "Ciro", "Darío", "Belsasar"],
        "correct_option": 0,
        "correct_answer": "Nabucodonosor",
        "accepted_answers": ["Nabucodonosor"],
        "explanation": "Nabucodonosor llegó a Jerusalén y la sitió.",
        "why_distractors_fail": {
            "Ciro": "Gobernó en una etapa posterior.",
            "Darío": "Gobernó después de la caída de Babilonia.",
            "Belsasar": "Reinó hacia el final del dominio babilónico.",
        },
        "source_ref": "Daniel 1:1",
        "source_quote": "En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió.",
        "evidence_excerpt": "vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió",
        "difficulty": "medium",
        "importance": "high",
        "relation_type": "event_participant",
        "option_category": "person",
        "false_mutation": None,
        "blank_span": None,
        "significance": None,
        "variant_justification": None,
        "blind_pool": None,
        "ai_review": {
            "status": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": "v11-test-reviewer",
        },
    }
    row.update(overrides)
    return row


def v11_sources():
    return {
        "DAN1-V001": {
            "source_ref": "Daniel 1:1",
            "source_quote": "En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió.",
        }
    }


class ProductionSnapshotTests(unittest.TestCase):
    """Protege contra snapshots parciales o imposibles de auditar."""

    def test_import_rejects_a_missing_manifest_shard_without_writing_destination(self) -> None:
        base_url = "https://training.example"
        manifest = {
            "schema_version": "10.0",
            "bank_id": "BANCO_UNICO_CONEXION_BIBLICA_2026",
            "gold_questions": 2,
            "central_question_count": 2,
            "presentation_variant_count": 0,
            "training_presentation_count": 2,
            "shards": [
                {
                    "chapter": "DAN1",
                    "question_count": 1,
                    "questions_file": "banks/final-2026/questions/DAN1.json",
                },
                {
                    "chapter": "DAN12",
                    "question_count": 1,
                    "questions_file": "banks/final-2026/questions/DAN12.json",
                },
            ],
        }
        resources = {
            f"{base_url}/banks/final-2026/manifest.json": json.dumps(manifest).encode(),
            f"{base_url}/banks/final-2026/questions/DAN1.json": b"[]",
        }

        def fetch_bytes(url: str) -> bytes:
            try:
                return resources[url]
            except KeyError as exc:
                raise FileNotFoundError(url) from exc

        test_temp_root = Path("tmp/competitive-v11-tests")
        test_temp_root.mkdir(parents=True, exist_ok=True)
        destination = test_temp_root / "missing-shard-baseline.json"
        destination.unlink(missing_ok=True)
        self.addCleanup(destination.unlink, missing_ok=True)

        with self.assertRaisesRegex(ValueError, "DAN12"):
            import_production_snapshot(
                base_url,
                destination,
                fetch_bytes=fetch_bytes,
                fetched_at="2026-08-30T00:00:00Z",
            )

        self.assertFalse(destination.exists())

    def test_import_writes_auditable_counts_and_hashes_after_all_shards_arrive(self) -> None:
        base_url = "https://training.example"
        manifest = {
            "schema_version": "10.0",
            "bank_id": "BANCO_UNICO_CONEXION_BIBLICA_2026",
            "gold_questions": 2,
            "central_question_count": 2,
            "presentation_variant_count": 1,
            "training_presentation_count": 3,
            "shards": [
                {
                    "chapter": "DAN1",
                    "question_count": 1,
                    "questions_file": "banks/final-2026/questions/DAN1.json",
                },
                {
                    "chapter": "DAN12",
                    "question_count": 1,
                    "questions_file": "banks/final-2026/questions/DAN12.json",
                },
            ],
        }
        manifest_bytes = json.dumps(manifest).encode()
        resources = {
            f"{base_url}/banks/final-2026/manifest.json": manifest_bytes,
            f"{base_url}/banks/final-2026/questions/DAN1.json": b"[]",
            f"{base_url}/banks/final-2026/questions/DAN12.json": b"[]",
        }

        destination_root = Path("tmp/competitive-v11-tests")
        destination_root.mkdir(parents=True, exist_ok=True)
        destination = destination_root / "complete-baseline.json"
        destination.unlink(missing_ok=True)
        self.addCleanup(destination.unlink, missing_ok=True)

        snapshot = import_production_snapshot(
            base_url,
            destination,
            fetch_bytes=lambda url: resources[url],
            fetched_at="2026-08-30T00:00:00Z",
        )

        self.assertTrue(destination.exists(), "el snapshot completo debe escribirse")
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), snapshot)
        self.assertEqual(
            snapshot["counts"],
            {
                "central_question_count": 2,
                "presentation_variant_count": 1,
                "training_presentation_count": 3,
                "shards": 2,
            },
        )
        shard_resources = [
            row for row in snapshot["resources"] if row["kind"] == "question_shard"
        ]
        self.assertEqual(len(shard_resources), 2)
        self.assertEqual(
            {row["sha256"] for row in shard_resources},
            {"4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"},
        )

    def test_import_assigns_an_utc_timestamp_when_caller_omits_it(self) -> None:
        base_url = "https://training.example"
        manifest = {
            "central_question_count": 0,
            "presentation_variant_count": 0,
            "training_presentation_count": 0,
            "shards": [],
        }
        resources = {
            f"{base_url}/banks/final-2026/manifest.json": json.dumps(manifest).encode()
        }
        destination_root = Path("tmp/competitive-v11-tests")
        destination_root.mkdir(parents=True, exist_ok=True)
        destination = destination_root / "timestamp-baseline.json"
        destination.unlink(missing_ok=True)
        self.addCleanup(destination.unlink, missing_ok=True)

        try:
            snapshot = import_production_snapshot(
                base_url,
                destination,
                fetch_bytes=lambda url: resources[url],
            )
        except TypeError as exc:
            self.fail(f"la API pública debe asignar fetched_at: {exc}")

        self.assertIsNotNone(
            re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", snapshot["fetched_at"])
        )


class SourcePacketTests(unittest.TestCase):
    """Mantiene completa y contextual la fuente que leerá el autor."""

    def test_builds_packets_for_useful_units_and_keeps_exclusions_separate(self) -> None:
        inventory = {
            "source_units": 3,
            "units": [
                {
                    "source_unit_id": "DAN1-V001",
                    "work": "Daniel",
                    "chapter": 1,
                    "reference": "Daniel 1:1",
                    "full_text": "Primera unidad.",
                    "characters": ["Daniel"],
                    "actions": ["propuso"],
                },
                {
                    "source_unit_id": "DAN1-V002",
                    "work": "Daniel",
                    "chapter": 1,
                    "reference": "Daniel 1:2",
                    "full_text": "Unidad sin valor autónomo.",
                },
                {
                    "source_unit_id": "DAN1-V003",
                    "work": "Daniel",
                    "chapter": 1,
                    "reference": "Daniel 1:3",
                    "full_text": "Tercera unidad.",
                },
            ],
        }
        exclusions = {"DAN1-V002": "No contiene conocimiento evaluable."}

        packets, excluded = build_source_packets(inventory, exclusions)

        self.assertEqual(list(packets), ["DAN1"])
        self.assertEqual(
            [row["source_unit_id"] for row in packets["DAN1"]],
            ["DAN1-V001", "DAN1-V003"],
        )
        self.assertEqual(packets["DAN1"][0]["context_after"], "Unidad sin valor autónomo.")
        self.assertEqual(packets["DAN1"][1]["context_before"], "Unidad sin valor autónomo.")
        self.assertIn("semantic_hints", packets["DAN1"][0])
        self.assertEqual(
            packets["DAN1"][0].get("semantic_hints"),
            {"characters": ["Daniel"], "actions": ["propuso"]},
        )
        self.assertEqual(
            excluded,
            [
                {
                    "source_unit_id": "DAN1-V002",
                    "source_ref": "Daniel 1:2",
                    "reason": "No contiene conocimiento evaluable.",
                }
            ],
        )

    def test_checked_in_packets_cover_all_1024_useful_source_units(self) -> None:
        packet_root = Path("content/competitive-v11/source-packets")
        self.assertTrue(packet_root.exists(), "deben generarse los paquetes V11")
        packet_files = sorted(packet_root.glob("*.json"))
        unit_files = [path for path in packet_files if path.name != "excluded-units.json"]
        self.assertEqual(len(unit_files), 18)

        rows = [
            row
            for path in unit_files
            for row in json.loads(path.read_text(encoding="utf-8"))["units"]
        ]
        self.assertEqual(len(rows), 1024)
        self.assertEqual(len({row["source_unit_id"] for row in rows}), 1024)
        self.assertTrue(all(row["source_quote"].strip() for row in rows))

        excluded = json.loads(
            (packet_root / "excluded-units.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(excluded["units"]), 7)

    def test_preserves_the_parent_paragraph_for_a_pr_proposition(self) -> None:
        inventory = {
            "source_units": 1,
            "units": [
                {
                    "source_unit_id": "PR39-P001-P001-S001",
                    "work": "Profetas y Reyes",
                    "chapter": 39,
                    "reference": "PR39, p. 1, párrafo 1",
                    "parent_text": "Párrafo completo con el sujeto y su explicación.",
                    "exact_text": "Su explicación.",
                }
            ],
        }

        packets, _ = build_source_packets(inventory, {})

        self.assertIn("parent_context", packets["PR39"][0])
        self.assertEqual(
            packets["PR39"][0].get("parent_context"),
            "Párrafo completo con el sujeto y su explicación.",
        )


class CompetitiveV11ContractTests(unittest.TestCase):
    """Bloquea los defectos editoriales que inflaron bancos anteriores."""

    def test_rejects_location_crutches_and_cross_passage_falsehoods(self) -> None:
        located = valid_v11_question(
            question="Según el párrafo 4, ¿quién sitió Jerusalén?"
        )
        transplanted = valid_v11_question(
            id="DAN1-V11-0002",
            family="true_false",
            question="Ciro sitió Jerusalén durante el tercer año de Joacim.",
            options=["Verdadero", "Falso"],
            correct_option=1,
            correct_answer="Falso",
            accepted_answers=["Falso"],
            why_distractors_fail={},
            option_category="truth_value",
            false_mutation={
                "changed_fields": ["source_ref"],
                "local": False,
                "original": "Daniel 1:1",
                "replacement": "Daniel 2:1",
            },
        )

        self.assertIn("source_location_prompt", validate_question(located, v11_sources()))
        self.assertIn(
            "cross_passage_falsehood",
            validate_question(transplanted, v11_sources()),
        )

    def test_rejects_a_third_variant_without_an_editorial_justification(self) -> None:
        rows = [
            valid_v11_question(
                id=f"DAN1-V11-000{index}",
                question=f"Pregunta competitiva única número {index}.",
            )
            for index in range(1, 4)
        ]

        self.assertEqual(
            audit_corpus(rows)["unjustified_third_variants"],
            ["DAN1-V11-0003"],
        )

    def test_accepts_a_complete_source_grounded_question(self) -> None:
        self.assertEqual(validate_question(valid_v11_question(), v11_sources()), [])

    def test_rejects_source_and_evidence_that_do_not_match_the_packet(self) -> None:
        unknown = valid_v11_question(source_unit_id="DAN1-V999")
        wrong_reference = valid_v11_question(source_ref="Daniel 1:2")
        wrong_quote = valid_v11_question(source_quote="Texto ajeno a la unidad.")
        unsupported_evidence = valid_v11_question(evidence_excerpt="Ciro emitió un decreto")

        self.assertIn("unknown_source_unit", validate_question(unknown, v11_sources()))
        self.assertIn(
            "source_reference_mismatch",
            validate_question(wrong_reference, v11_sources()),
        )
        self.assertIn("source_quote_mismatch", validate_question(wrong_quote, v11_sources()))
        self.assertIn(
            "evidence_not_in_source",
            validate_question(unsupported_evidence, v11_sources()),
        )

    def test_rejects_broken_options_answers_and_distractor_ledgers(self) -> None:
        duplicate_options = valid_v11_question(
            options=["Nabucodonosor", "Nabucodonosor", "Darío", "Belsasar"]
        )
        wrong_index = valid_v11_question(correct_option=1)
        incomplete_ledger = valid_v11_question(
            why_distractors_fail={"Ciro": "Gobernó después."}
        )

        self.assertIn(
            "duplicate_options",
            validate_question(duplicate_options, v11_sources()),
        )
        self.assertIn("answer_index_mismatch", validate_question(wrong_index, v11_sources()))
        self.assertIn(
            "incomplete_distractor_ledger",
            validate_question(incomplete_ledger, v11_sources()),
        )

    def test_false_statement_must_change_exactly_one_local_supported_value(self) -> None:
        false_row = valid_v11_question(
            family="true_false",
            question="Ciro sitió Jerusalén durante el tercer año de Joacim.",
            options=["Verdadero", "Falso"],
            correct_option=1,
            correct_answer="Falso",
            accepted_answers=["Falso"],
            why_distractors_fail={},
            option_category="truth_value",
            false_mutation={
                "changed_fields": ["person", "place"],
                "local": True,
                "original": "Alejandro",
                "replacement": "Ciro",
            },
        )

        errors = validate_question(false_row, v11_sources())

        self.assertIn("false_mutation_must_change_one_field", errors)
        self.assertIn("false_mutation_original_not_in_source", errors)

    def test_completion_requires_a_significant_supported_blank(self) -> None:
        completion = valid_v11_question(
            family="fill_choice",
            question="____ sitió Jerusalén durante el tercer año de Joacim.",
            blank_span="el",
            significance="",
        )

        errors = validate_question(completion, v11_sources())

        self.assertIn("blank_span_answer_mismatch", errors)
        self.assertIn("trivial_completion_blank", errors)

    def test_corpus_audit_detects_duplicate_ids_and_normalized_prompts(self) -> None:
        first = valid_v11_question()
        duplicate = valid_v11_question(question="¿Quién sitió Jerusalén durante el tercer año del reinado de Joacim?!")

        audit = audit_corpus([first, duplicate])

        self.assertEqual(audit["duplicate_ids"], [duplicate["id"]])
        self.assertEqual(audit["normalized_duplicate_prompts"], [duplicate["id"]])
        original_hash = content_hash(first)
        first["explanation"] = "Explicación editorial modificada."
        self.assertNotEqual(content_hash(first), original_hash)

    def test_rejects_missing_contract_fields_and_a_leaked_choice_answer(self) -> None:
        missing = valid_v11_question()
        del missing["option_category"]
        leaked = valid_v11_question(
            question="Nabucodonosor sitió Jerusalén; ¿quién fue el responsable?"
        )

        self.assertIn("missing_key_option_category", validate_question(missing, v11_sources()))
        self.assertIn("answer_leaked_in_prompt", validate_question(leaked, v11_sources()))


if __name__ == "__main__":
    unittest.main()
