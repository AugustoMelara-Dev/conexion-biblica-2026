"""Pruebas de contrato para el preparador de dosieres V18.

Estas pruebas usan un banco pequeño y fuentes sintéticas para que el contrato
sea verificable sin depender del contenido editorial del banco real.
"""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import scripts.prepare_final_day_v18_dossiers as preparer
from scripts.prepare_final_day_v18_dossiers import (
    prepare_dossiers,
    prepare_safe_first_dossiers,
    verify_artifacts,
)


# Keep the contract independent from the production constants. A change to a
# schema constant must make these tests fail until the fixture and assertions
# are deliberately reviewed together.
EXPECTED_DOSSIER_FIELDS = frozenset(
    {
        "audit_run_id",
        "question_id",
        "question",
        "options",
        "source_unit_id",
        "source_ref",
        "pdf_page",
        "exact_quote",
        "nearby_context",
        "material",
        "chapter",
    }
)
EXPECTED_BLIND_FIELDS = frozenset(
    {"audit_run_id", "question_id", "question", "options"}
)
FORBIDDEN_OUTPUT_FIELDS = frozenset(
    {
        "correct_option",
        "correct_answer",
        "accepted_answers",
        "answer",
        "difficulty",
        "tier",
        "decision",
        "results",
        "blind_results",
        "selected_option_index",
        "selected_option_text",
    }
)
CANONICAL_SOURCE_SHA256 = (
    "0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3"
)


class FinalDayV18AuditContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.questions_dir = self.root / "questions"
        self.sources_dir = self.root / "sources"
        self.output_dir = self.root / "dossiers"
        self.blind_dir = self.root / "blind"
        self.questions_dir.mkdir()
        self.sources_dir.mkdir()

        for chapter_index, chapter in enumerate(("PR39", "DAN7", "DAN1")):
            units = []
            questions = []
            for index in range(10):
                unit_id = f"{chapter}-U{index + 1:03d}"
                question_id = f"Q-{chapter}-{index + 1:04d}"
                units.append(
                    {
                        "source_unit_id": unit_id,
                        "work": "Profetas y Reyes" if chapter.startswith("PR") else "Daniel",
                        "chapter": int(chapter[3:]),
                        "source_ref": f"{chapter}, p. {chapter_index + 10}, párrafo 1",
                        "source_quote": f"Cita canónica {chapter} {index + 1}.",
                        "context_before": f"Contexto anterior {chapter} {index + 1}.",
                        "context_after": f"Contexto posterior {chapter} {index + 1}.",
                        "pdf_page": chapter_index + 10,
                    }
                )
                questions.append(
                    {
                        "id": question_id,
                        "chapter": chapter,
                        "source_unit_id": unit_id,
                        "question": (
                            f"Según Profetas y Reyes, ¿qué afirma {chapter} {index + 1}?"
                            if chapter.startswith("PR")
                            else f"¿Qué afirma {chapter} {index + 1}?"
                        ),
                        "options": ["Respuesta A", "Respuesta B", "Respuesta C", "Respuesta D"],
                        # Estos campos representan el material que jamás debe
                        # cruzar la frontera hacia el dosier o el par ciego.
                        "correct_option": 0,
                        "correct_answer": "Respuesta A",
                        "difficulty": "easy",
                        "tier": "gold",
                    }
                )
            (self.questions_dir / f"{chapter}.json").write_text(
                json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (self.sources_dir / f"{chapter}.json").write_text(
                json.dumps(
                    {"source_sha256": CANONICAL_SOURCE_SHA256, "units": units},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_prepares_priority_batches_with_separate_deterministic_orders(self) -> None:
        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-test",
        )

        self.assertEqual(result["selected_count"], 30)
        self.assertEqual(result["valid_count"], 30)
        self.assertEqual(result["batch_count"], 2)
        self.assertEqual(result["batch_sizes"], [15, 15])

        first_batch = json.loads(
            (self.output_dir / "run-test" / "batch-001.json").read_text(encoding="utf-8")
        )
        items = first_batch["items"]
        self.assertEqual(items[0]["chapter"], "PR39")
        self.assertEqual(items[9]["chapter"], "PR39")
        self.assertEqual(items[10]["chapter"], "DAN7")
        self.assertEqual(set(items[0]), EXPECTED_DOSSIER_FIELDS)
        self.assertFalse(FORBIDDEN_OUTPUT_FIELDS.intersection(items[0]))

        blind_batch = json.loads(
            (self.blind_dir / "run-test" / "batch-001.json").read_text(encoding="utf-8")
        )
        blind_item = blind_batch["items"][0]
        self.assertEqual(set(blind_item), EXPECTED_BLIND_FIELDS)
        self.assertFalse(FORBIDDEN_OUTPUT_FIELDS.intersection(blind_item))
        self.assertNotEqual(items[0]["options"], blind_item["options"])

        # Re-running with the same inputs and run id must be byte-stable.
        first_bytes = (self.output_dir / "run-test" / "batch-001.json").read_bytes()
        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-test",
        )
        self.assertEqual(first_bytes, (self.output_dir / "run-test" / "batch-001.json").read_bytes())

    def test_excludes_untraceable_item_without_defaults(self) -> None:
        question_path = self.questions_dir / "PR39.json"
        questions = json.loads(question_path.read_text(encoding="utf-8"))
        questions[0]["source_unit_id"] = "PR39-MISSING"
        question_path.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")

        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-invalid",
        )

        self.assertEqual(result["invalid_count"], 1)
        invalid = json.loads(
            (self.output_dir / "run-invalid" / "invalid-items.json").read_text(encoding="utf-8")
        )
        self.assertEqual(invalid["items"][0]["question_id"], "Q-PR39-0001")
        self.assertIn("source", invalid["items"][0]["reason"])
        self.assertNotIn("pdf_page", invalid["items"][0])
        self.assertNotIn("correct_option", invalid["items"][0])

    def test_verify_artifacts_detects_post_preparation_mutation(self) -> None:
        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-hash",
        )
        run_dir = self.output_dir / "run-hash"
        self.assertTrue(verify_artifacts(run_dir))

        path = run_dir / "batch-001.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["items"][0]["question"] += " mutada"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.assertFalse(verify_artifacts(run_dir))

    def test_resolves_page_from_reproducible_ocr_prefix_without_default(self) -> None:
        source_path = self.sources_dir / "DAN7.json"
        source_payload = json.loads(source_path.read_text(encoding="utf-8"))
        source_payload["units"][0].pop("pdf_page")
        source_payload["units"][0]["source_ref"] = "Daniel 7:1"
        source_payload["units"][0]["source_quote"] += " Encabezado posterior"
        source_path.write_text(
            json.dumps(source_payload, ensure_ascii=False), encoding="utf-8"
        )
        ocr_path = self.root / "ocr.json"
        ocr_path.write_text(
            json.dumps(
                {
                    "source_sha256": CANONICAL_SOURCE_SHA256,
                    "pages": {"7": "iCita canónica DAN7 1."},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-ocr",
            ocr_path=ocr_path,
        )
        self.assertEqual(result["valid_count"], 30)
        first_batch = json.loads(
            (self.output_dir / "run-ocr" / "batch-001.json").read_text(encoding="utf-8")
        )
        dan7_item = next(item for item in first_batch["items"] if item["question_id"] == "Q-DAN7-0001")
        self.assertEqual(dan7_item["pdf_page"], 7)
        manifest = json.loads(
            (self.output_dir / "run-ocr" / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["ocr_path"], str(ocr_path.resolve()))
        self.assertEqual(manifest["ocr_status"], "VALID")
        self.assertEqual(manifest["ocr_source_sha256"], CANONICAL_SOURCE_SHA256)

    def test_rejects_ocr_page_locator_with_wrong_source_hash(self) -> None:
        source_path = self.sources_dir / "DAN7.json"
        source_payload = json.loads(source_path.read_text(encoding="utf-8"))
        source_payload["units"][0].pop("pdf_page")
        source_payload["units"][0]["source_ref"] = "Daniel 7:1"
        source_payload["units"][0]["source_quote"] += " Encabezado posterior"
        source_path.write_text(
            json.dumps(source_payload, ensure_ascii=False), encoding="utf-8"
        )
        ocr_path = self.root / "ocr-wrong-hash.json"
        ocr_path.write_text(
            json.dumps(
                {
                    "source_sha256": "sha256-no-correspondiente",
                    "pages": {"7": "Cita canónica DAN7 1."},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-ocr-wrong-hash",
            ocr_path=ocr_path,
        )
        self.assertEqual(result["valid_count"], 29)
        self.assertEqual(result["invalid_count"], 1)
        manifest = json.loads(
            (self.output_dir / "run-ocr-wrong-hash" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["ocr_status"], "INVALID_HASH")

    def test_rejects_source_packet_with_wrong_canonical_hash(self) -> None:
        source_path = self.sources_dir / "PR39.json"
        source_payload = json.loads(source_path.read_text(encoding="utf-8"))
        source_payload["source_sha256"] = "sha256-no-correspondiente"
        source_path.write_text(
            json.dumps(source_payload, ensure_ascii=False), encoding="utf-8"
        )

        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-source-wrong-hash",
        )
        self.assertEqual(result["valid_count"], 20)
        self.assertEqual(result["invalid_count"], 10)

    def test_rejects_source_packet_without_canonical_hash(self) -> None:
        source_path = self.sources_dir / "PR39.json"
        source_payload = json.loads(source_path.read_text(encoding="utf-8"))
        source_payload.pop("source_sha256")
        source_path.write_text(json.dumps(source_payload, ensure_ascii=False), encoding="utf-8")

        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-source-missing-hash",
        )

        self.assertEqual(result["valid_count"], 20)
        self.assertEqual(result["invalid_count"], 10)
        manifest = json.loads(
            (self.output_dir / "run-source-missing-hash" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(any("ausente" in error for error in manifest["source_errors"]))

    def test_rejects_ocr_without_canonical_hash(self) -> None:
        source_path = self.sources_dir / "DAN7.json"
        source_payload = json.loads(source_path.read_text(encoding="utf-8"))
        source_payload["units"][0].pop("pdf_page")
        source_payload["units"][0]["source_ref"] = "Daniel 7:1"
        source_payload["units"][0]["source_quote"] += " Encabezado posterior"
        source_path.write_text(json.dumps(source_payload, ensure_ascii=False), encoding="utf-8")
        ocr_path = self.root / "ocr-missing-hash.json"
        ocr_path.write_text(
            json.dumps({"pages": {"7": "Cita canónica DAN7 1."}}, ensure_ascii=False),
            encoding="utf-8",
        )

        result = prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-ocr-missing-hash",
            ocr_path=ocr_path,
        )

        self.assertEqual(result["valid_count"], 29)
        self.assertEqual(result["invalid_count"], 1)
        manifest = json.loads(
            (self.output_dir / "run-ocr-missing-hash" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["ocr_status"], "INVALID_HASH")

    def test_rejects_batch_bounds_outside_v18_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "entre 15 y 20"):
            prepare_dossiers(
                question_dir=self.questions_dir,
                source_dir=self.sources_dir,
                dossier_dir=self.output_dir,
                blind_dir=self.blind_dir,
                audit_run_id="run-invalid-bounds",
                min_batch_size=1,
                max_batch_size=2,
            )
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-invalid-manifest-bounds",
        )
        manifest_path = self.output_dir / "run-invalid-manifest-bounds" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["batch_min"] = 1
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(
            verify_artifacts(
                self.output_dir / "run-invalid-manifest-bounds",
                self.blind_dir / "run-invalid-manifest-bounds",
            )
        )

    def test_verify_artifacts_rejects_blind_option_multiset_mutation(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-blind-multiset",
        )
        run_dir = self.output_dir / "run-blind-multiset"
        blind_run_dir = self.blind_dir / "run-blind-multiset"
        blind_path = blind_run_dir / "batch-001.json"
        blind_payload = json.loads(blind_path.read_text(encoding="utf-8"))
        blind_payload["items"][0]["options"] = ["X", "Y", "Z", "W"]
        blind_path.write_text(
            json.dumps(blind_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(
            json.dumps(
                blind_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        manifest["blind_batches"][0]["content_sha256"] = digest
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, blind_run_dir))

    def test_verify_artifacts_rejects_batch_schema_mutation_even_with_updated_hash(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-schema-version",
        )
        run_dir = self.output_dir / "run-schema-version"
        batch_path = run_dir / "batch-002.json"
        payload = json.loads(batch_path.read_text(encoding="utf-8"))
        payload["schema_version"] = "tampered-schema"
        batch_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["batches"][1]["content_sha256"] = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, self.blind_dir / "run-schema-version"))

    def test_verify_artifacts_rejects_selected_accounting_mutation(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-accounting",
        )
        run_dir = self.output_dir / "run-accounting"
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["selected_count"] += 1
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, self.blind_dir / "run-accounting"))

    def test_verify_artifacts_rejects_intermediate_blind_batch_desynchronization(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-desync",
        )
        run_dir = self.output_dir / "run-desync"
        blind_run_dir = self.blind_dir / "run-desync"
        blind_path = blind_run_dir / "batch-002.json"
        blind_payload = json.loads(blind_path.read_text(encoding="utf-8"))
        blind_payload["items"][0]["question_id"] = "DESYNC-QUESTION"
        blind_path.write_text(
            json.dumps(blind_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["blind_batches"][1]["content_sha256"] = hashlib.sha256(
            json.dumps(
                blind_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, blind_run_dir))

    def test_verify_artifacts_rejects_non_object_payload_even_with_updated_hash(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-payload-shape",
        )
        run_dir = self.output_dir / "run-payload-shape"
        blind_run_dir = self.blind_dir / "run-payload-shape"
        blind_path = blind_run_dir / "batch-001.json"
        blind_path.write_text("[]", encoding="utf-8")
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["blind_batches"][0]["content_sha256"] = hashlib.sha256(
            b"[]"
        ).hexdigest()
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, blind_run_dir))

    def test_verify_artifacts_rejects_safe_first_exclusion_accounting_gap(self) -> None:
        question_dir, source_dir = self._write_safe_first_fixture()
        dossier_dir = self.root / "safe-first-accounting-dossiers"
        blind_dir = self.root / "safe-first-accounting-blind"
        prepare_safe_first_dossiers(
            question_dir=question_dir,
            source_dir=source_dir,
            dossier_dir=dossier_dir,
            blind_dir=blind_dir,
        )
        run_dir = dossier_dir / "v18-safe-first"
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["pr_without_delimiter_count"] += 1
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, blind_dir / "v18-safe-first"))

    def test_verify_artifacts_requires_ocr_path_when_status_is_valid(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-ocr-path",
        )
        run_dir = self.output_dir / "run-ocr-path"
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["ocr_path"] = None
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, self.blind_dir / "run-ocr-path"))

    def test_verify_artifacts_rejects_missing_trace_value_even_with_updated_hash(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-trace-value",
        )
        run_dir = self.output_dir / "run-trace-value"
        batch_path = run_dir / "batch-001.json"
        payload = json.loads(batch_path.read_text(encoding="utf-8"))
        payload["items"][0]["source_ref"] = None
        batch_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["batches"][0]["content_sha256"] = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.assertFalse(verify_artifacts(run_dir, self.blind_dir / "run-trace-value"))

    def test_verify_artifacts_rejects_unlisted_batch_file(self) -> None:
        prepare_dossiers(
            question_dir=self.questions_dir,
            source_dir=self.sources_dir,
            dossier_dir=self.output_dir,
            blind_dir=self.blind_dir,
            audit_run_id="run-extra-batch",
        )
        run_dir = self.output_dir / "run-extra-batch"
        blind_run_dir = self.blind_dir / "run-extra-batch"
        (run_dir / "batch-999.json").write_bytes((run_dir / "batch-001.json").read_bytes())
        (blind_run_dir / "batch-999.json").write_bytes(
            (blind_run_dir / "batch-001.json").read_bytes()
        )
        self.assertFalse(verify_artifacts(run_dir, blind_run_dir))

    def test_failed_write_does_not_publish_partial_run(self) -> None:
        original_write = preparer._atomic_write_json
        calls = 0

        def fail_on_second_write(path: Path, value: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("fallo de escritura simulado")
            original_write(path, value)

        with mock.patch.object(preparer, "_atomic_write_json", side_effect=fail_on_second_write):
            with self.assertRaisesRegex(RuntimeError, "fallo de escritura"):
                prepare_dossiers(
                    question_dir=self.questions_dir,
                    source_dir=self.sources_dir,
                    dossier_dir=self.output_dir,
                    blind_dir=self.blind_dir,
                    audit_run_id="run-atomic",
                )
        self.assertFalse((self.output_dir / "run-atomic").exists())
        self.assertFalse((self.blind_dir / "run-atomic").exists())

    def test_failed_second_pair_rename_does_not_publish_one_side(self) -> None:
        original_replace = preparer.os.replace
        publish_renames = 0

        def fail_on_second_publish_rename(source: str | bytes | Path, target: str | bytes | Path) -> None:
            nonlocal publish_renames
            source_name = Path(source).name
            target_name = Path(target).name
            if source_name.startswith(".run-rename.staging-") and target_name == "run-rename":
                publish_renames += 1
                if publish_renames == 2:
                    raise RuntimeError("fallo en segundo rename del par")
            original_replace(source, target)

        with mock.patch.object(preparer.os, "replace", side_effect=fail_on_second_publish_rename):
            with self.assertRaisesRegex(RuntimeError, "segundo rename"):
                prepare_dossiers(
                    question_dir=self.questions_dir,
                    source_dir=self.sources_dir,
                    dossier_dir=self.output_dir,
                    blind_dir=self.blind_dir,
                    audit_run_id="run-rename",
                )
        self.assertEqual(publish_renames, 2)
        self.assertFalse((self.output_dir / "run-rename").exists())
        self.assertFalse((self.blind_dir / "run-rename").exists())

    def _write_safe_first_fixture(
        self,
        *,
        dan9_count: int = 10,
        dan12_count: int = 10,
        dan7_count: int = 4,
    ) -> tuple[Path, Path]:
        question_dir = self.root / "safe-first-questions"
        source_dir = self.root / "safe-first-sources"
        question_dir.mkdir()
        source_dir.mkdir()

        def write_chapter(chapter: str, count: int, question_prefix: str) -> None:
            questions = []
            units = []
            for index in range(1, count + 1):
                source_unit_id = f"{chapter}-SAFE-{index:03d}"
                question_id = f"SAFE-{chapter}-{index:04d}"
                source_ref = f"{chapter}, p. {index + 100}, párrafo 1"
                quote = f"Cita trazable {chapter} {index}."
                question = f"{question_prefix} {chapter} pregunta {index}?"
                questions.append(
                    {
                        "id": question_id,
                        "chapter": chapter,
                        "source_unit_id": source_unit_id,
                        "question": question,
                        "source_quote": quote,
                        "options": [
                            f"Opción A {chapter} {index}",
                            f"Opción B {chapter} {index}",
                            f"Opción C {chapter} {index}",
                            f"Opción D {chapter} {index}",
                        ],
                        "correct_option": 0,
                        "correct_answer": f"Opción A {chapter} {index}",
                        "difficulty": "easy",
                        "tier": "gold",
                        "review": {"status": "passed"},
                    }
                )
                units.append(
                    {
                        "source_unit_id": source_unit_id,
                        "work": "Profetas y Reyes" if chapter.startswith("PR") else "Daniel",
                        "chapter": int(chapter[3:]),
                        "source_ref": source_ref,
                        "source_quote": quote,
                        "context_before": f"Antes {chapter} {index}.",
                        "context_after": f"Después {chapter} {index}.",
                        "pdf_page": index + 100,
                    }
                )
            (question_dir / f"{chapter}.json").write_text(
                json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (source_dir / f"{chapter}.json").write_text(
                json.dumps(
                    {"source_sha256": CANONICAL_SOURCE_SHA256, "units": units},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        for chapter in ("PR39", "PR40", "PR41", "PR42", "PR43", "PR44"):
            write_chapter(chapter, 10, "Según Profetas y Reyes")
        write_chapter("DAN7", dan7_count, "Según Daniel")
        write_chapter("DAN9", dan9_count, "Según Daniel: zona personal setenta semanas")
        write_chapter("DAN12", dan12_count, "Según Daniel: zona personal Miguel")
        # Distractors prove that safe-first does not widen into DAN1 or a PR
        # question lacking the exact delimiter.
        write_chapter("DAN8", 1, "Según Daniel")
        write_chapter("DAN1", 1, "Según Daniel")
        return question_dir, source_dir

    def test_safe_first_selects_exactly_60_pr_and_20_daniel_in_four_batches(self) -> None:
        question_dir, source_dir = self._write_safe_first_fixture()
        dossier_dir = self.root / "safe-first-dossiers"
        blind_dir = self.root / "safe-first-blind"

        result = prepare_safe_first_dossiers(
            question_dir=question_dir,
            source_dir=source_dir,
            dossier_dir=dossier_dir,
            blind_dir=blind_dir,
        )

        self.assertEqual(result["selected_count"], 80)
        self.assertEqual(result["valid_count"], 80)
        self.assertEqual(result["batched_count"], 80)
        self.assertEqual(result["invalid_count"], 0)
        self.assertEqual(result["batch_count"], 4)
        self.assertEqual(result["batch_sizes"], [20, 20, 20, 20])

        run_dir = dossier_dir / "v18-safe-first"
        batch_paths = sorted(run_dir.glob("batch-*.json"))
        items = [item for path in batch_paths for item in json.loads(path.read_text(encoding="utf-8"))["items"]]
        self.assertEqual(len(items), 80)
        self.assertEqual(len({item["question_id"] for item in items}), 80)
        pr_items = [item for item in items if str(item["chapter"]).startswith("PR")]
        dan_items = [item for item in items if str(item["chapter"]).startswith("DAN")]
        self.assertEqual(len(pr_items), 60)
        self.assertEqual(len(dan_items), 20)
        self.assertTrue(all("Según Profetas y Reyes" in item["question"] for item in pr_items))
        self.assertEqual(
            {item["chapter"] for item in pr_items},
            {f"PR{i}" for i in range(39, 45)},
        )
        self.assertTrue(all(item["chapter"] in {f"DAN{i}" for i in range(7, 13)} for item in dan_items))
        self.assertEqual(
            {item["chapter"] for item in dan_items[:16]},
            {"DAN9", "DAN12"},
        )
        self.assertNotIn("DAN1", {item["chapter"] for item in dan_items})

    def test_safe_first_fails_closed_when_dan9_dan12_pool_has_fewer_than_20(self) -> None:
        question_dir, source_dir = self._write_safe_first_fixture(
            dan9_count=8,
            dan12_count=8,
            dan7_count=4,
        )

        with self.assertRaisesRegex(ValueError, "DAN9/12"):
            prepare_safe_first_dossiers(
                question_dir=question_dir,
                source_dir=source_dir,
                dossier_dir=self.root / "safe-first-insufficient-dossiers",
                blind_dir=self.root / "safe-first-insufficient-blind",
            )

    def test_safe_first_manifest_counts_scope_and_pr_delimiter_exclusions(self) -> None:
        question_dir, source_dir = self._write_safe_first_fixture()
        pr_path = question_dir / "PR39.json"
        pr_rows = json.loads(pr_path.read_text(encoding="utf-8"))
        excluded_pr = dict(pr_rows[0])
        excluded_pr["id"] = "SAFE-PR39-NO-DELIMITER"
        excluded_pr["question"] = "Pregunta PR39 sin delimitación editorial"
        pr_rows.append(excluded_pr)
        pr_path.write_text(
            json.dumps(pr_rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (question_dir / "OTHER.json").write_text(
            json.dumps(
                [
                    {
                        "id": "SAFE-OTHER-0001",
                        "chapter": "OTHER",
                        "question": "Pregunta fuera de scope",
                        "options": ["A", "B"],
                    }
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        prepare_safe_first_dossiers(
            question_dir=question_dir,
            source_dir=source_dir,
            dossier_dir=self.root / "safe-first-scope-dossiers",
            blind_dir=self.root / "safe-first-scope-blind",
        )
        manifest = json.loads(
            (
                self.root
                / "safe-first-scope-dossiers"
                / "v18-safe-first"
                / "manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["pr_without_delimiter_count"], 1)
        self.assertGreaterEqual(manifest["outside_scope_count"], 1)
        self.assertEqual(manifest["outside_priority_count"], manifest["outside_scope_count"])
        self.assertEqual(manifest["unknown_priority_count"], 1)
        self.assertEqual(
            manifest["safe_first_excluded_count"],
            manifest["pr_without_delimiter_count"] + manifest["outside_scope_count"],
        )

    def test_safe_first_blind_pairs_are_private_and_orders_are_deterministic(self) -> None:
        question_dir, source_dir = self._write_safe_first_fixture()
        dossier_dir = self.root / "safe-first-dossiers"
        blind_dir = self.root / "safe-first-blind"

        prepare_safe_first_dossiers(
            question_dir=question_dir,
            source_dir=source_dir,
            dossier_dir=dossier_dir,
            blind_dir=blind_dir,
        )
        run_dir = dossier_dir / "v18-safe-first"
        blind_run_dir = blind_dir / "v18-safe-first"
        before = {
            path.relative_to(self.root): path.read_bytes()
            for path in sorted(run_dir.glob("*.json"))
        }
        before.update(
            {
                path.relative_to(self.root): path.read_bytes()
                for path in sorted(blind_run_dir.glob("*.json"))
            }
        )

        for dossier_path, blind_path in zip(
            sorted(run_dir.glob("batch-*.json")),
            sorted(blind_run_dir.glob("batch-*.json")),
        ):
            dossier_items = json.loads(dossier_path.read_text(encoding="utf-8"))["items"]
            blind_items = json.loads(blind_path.read_text(encoding="utf-8"))["items"]
            for dossier_item, blind_item in zip(dossier_items, blind_items):
                self.assertEqual(set(dossier_item), EXPECTED_DOSSIER_FIELDS)
                self.assertEqual(set(blind_item), EXPECTED_BLIND_FIELDS)
                self.assertFalse(FORBIDDEN_OUTPUT_FIELDS.intersection(dossier_item))
                self.assertFalse(FORBIDDEN_OUTPUT_FIELDS.intersection(blind_item))
                self.assertNotEqual(dossier_item["options"], blind_item["options"])
                self.assertNotIn("source_ref", blind_item)
                self.assertNotIn("exact_quote", blind_item)
                self.assertNotIn("correct_answer", blind_item)

        prepare_safe_first_dossiers(
            question_dir=question_dir,
            source_dir=source_dir,
            dossier_dir=dossier_dir,
            blind_dir=blind_dir,
        )
        after = {
            path.relative_to(self.root): path.read_bytes()
            for path in sorted(run_dir.glob("*.json"))
        }
        after.update(
            {
                path.relative_to(self.root): path.read_bytes()
                for path in sorted(blind_run_dir.glob("*.json"))
            }
        )
        self.assertEqual(before, after)
        self.assertTrue(verify_artifacts(run_dir, blind_run_dir))

    def test_safe_first_uses_only_unique_exact_quote_join_for_missing_source_id(self) -> None:
        question_dir, source_dir = self._write_safe_first_fixture()
        question_path = question_dir / "PR39.json"
        questions = json.loads(question_path.read_text(encoding="utf-8"))
        expected_source_id = questions[0]["source_unit_id"]
        questions[0]["source_unit_id"] = ""
        question_path.write_text(
            json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        result = prepare_safe_first_dossiers(
            question_dir=question_dir,
            source_dir=source_dir,
            dossier_dir=self.root / "safe-first-quote-dossiers",
            blind_dir=self.root / "safe-first-quote-blind",
        )

        self.assertEqual(result["selected_count"], 80)
        items = []
        for path in sorted((self.root / "safe-first-quote-dossiers" / "v18-safe-first").glob("batch-*.json")):
            items.extend(json.loads(path.read_text(encoding="utf-8"))["items"])
        item = next(item for item in items if item["question_id"] == "SAFE-PR39-0001")
        self.assertEqual(item["source_unit_id"], expected_source_id)


if __name__ == "__main__":
    unittest.main()
