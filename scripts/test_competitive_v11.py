"""Pruebas del pipeline editorial competitivo V11."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts.lib.production_snapshot_v11 import import_production_snapshot
from scripts.lib.source_packets_v11 import build_source_packets


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


if __name__ == "__main__":
    unittest.main()
