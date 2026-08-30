"""Pruebas del pipeline editorial competitivo V11."""

from __future__ import annotations

import json
import importlib.util
import hashlib
import io
import os
import re
import shutil
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from scripts.lib.production_snapshot_v11 import import_production_snapshot
from scripts.lib.source_packets_v11 import build_source_packets
from scripts.lib.competitive_v11 import audit_corpus, content_hash, validate_question
from scripts.lib.import_seed_v11 import import_seed
from scripts.lib.author_batch_v11 import compile_authored_batch


COMPILE_SCRIPT = Path(__file__).resolve().with_name("compile-competitive-v11.py")
COMPILE_SPEC = importlib.util.spec_from_file_location(
    "compile_competitive_v11", COMPILE_SCRIPT
)
assert COMPILE_SPEC and COMPILE_SPEC.loader
compile_competitive_v11 = importlib.util.module_from_spec(COMPILE_SPEC)
COMPILE_SPEC.loader.exec_module(compile_competitive_v11)


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

    def test_allows_natural_attribution_to_a_speakers_conclusion(self) -> None:
        attributed = valid_v11_question(
            question=(
                "Según la conclusión de Nabucodonosor, ¿qué hizo el rey de Babilonia "
                "al llegar a Jerusalén?"
            )
        )

        self.assertNotIn(
            "source_location_prompt",
            validate_question(attributed, v11_sources()),
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

    def test_choice_accepts_inflection_when_an_accepted_answer_matches_source(self) -> None:
        source_quote = "Aquel que tenía semejanza de hombre me fortaleció."
        sources = {
            "DAN1-V001": {
                "source_ref": "Daniel 1:1",
                "source_quote": source_quote,
            }
        }
        choice = valid_v11_question(
            question="¿Cómo terminó Daniel después del nuevo toque?",
            options=["fortalecido", "paralizado", "escondido", "desorientado"],
            correct_answer="fortalecido",
            accepted_answers=["fortalecido", "me fortaleció"],
            why_distractors_fail={
                "paralizado": "Recuperó fuerza.",
                "escondido": "No se ocultó.",
                "desorientado": "La consecuencia fue fortalecimiento.",
            },
            source_quote=source_quote,
            evidence_excerpt=source_quote,
            option_category="effect",
        )

        self.assertNotIn("answer_not_supported", validate_question(choice, sources))

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

    def test_false_mutation_allows_a_pronominal_shift_when_content_word_is_local(self) -> None:
        source_quote = "Las visiones de mi cabeza me asombraron."
        sources = {
            "DAN1-V001": {
                "source_ref": "Daniel 1:1",
                "source_quote": source_quote,
            }
        }
        false_row = valid_v11_question(
            family="true_false",
            question="Las visiones dejaron indiferente a Daniel.",
            options=["Verdadero", "Falso"],
            correct_option=1,
            correct_answer="Falso",
            accepted_answers=["Falso"],
            why_distractors_fail={},
            source_quote=source_quote,
            evidence_excerpt=source_quote,
            option_category="truth_value",
            false_mutation={
                "changed_fields": ["response"],
                "local": True,
                "original": "lo asombraron",
                "replacement": "lo dejaron indiferente",
            },
        )

        self.assertNotIn(
            "false_mutation_original_not_in_source",
            validate_question(false_row, sources),
        )

    def test_false_mutation_matches_an_enclitic_pronoun_to_its_local_verb(self) -> None:
        source_quote = "Ninguna bestia podía parar delante de él."
        sources = {
            "DAN1-V001": {
                "source_ref": "Daniel 1:1",
                "source_quote": source_quote,
            }
        }
        false_row = valid_v11_question(
            family="true_false",
            question="Una bestia podía detener al carnero.",
            options=["Verdadero", "Falso"],
            correct_option=1,
            correct_answer="Falso",
            accepted_answers=["Falso"],
            why_distractors_fail={},
            source_quote=source_quote,
            evidence_excerpt=source_quote,
            option_category="truth_value",
            false_mutation={
                "changed_fields": ["ability"],
                "local": True,
                "original": "ninguna bestia podía pararlo",
                "replacement": "una bestia podía detenerlo",
            },
        )

        self.assertNotIn(
            "false_mutation_original_not_in_source",
            validate_question(false_row, sources),
        )

    def test_false_mutation_accepts_a_high_overlap_conceptual_restatement(self) -> None:
        source_quote = "Tuya es, Señor, la justicia, y nuestra la confusión de rostro."
        sources = {
            "DAN1-V001": {
                "source_ref": "Daniel 1:1",
                "source_quote": source_quote,
            }
        }
        false_row = valid_v11_question(
            family="true_false",
            question="La confusión pertenece al Señor y la justicia al pueblo.",
            options=["Verdadero", "Falso"],
            correct_option=1,
            correct_answer="Falso",
            accepted_answers=["Falso"],
            why_distractors_fail={},
            source_quote=source_quote,
            evidence_excerpt=source_quote,
            option_category="truth_value",
            false_mutation={
                "changed_fields": ["attribution"],
                "local": True,
                "original": "La justicia pertenece al Señor y la confusión de rostro al pueblo",
                "replacement": "La confusión pertenece al Señor y la justicia al pueblo",
            },
        )

        self.assertNotIn(
            "false_mutation_original_not_in_source",
            validate_question(false_row, sources),
        )

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

    def test_completion_accepts_one_blank_run_longer_than_four_underscores(self) -> None:
        completion = valid_v11_question(
            family="fill_choice",
            question="________ llegó a Jerusalén y la sitió.",
            blank_span="Nabucodonosor",
            significance="Identifica al responsable directo del sitio.",
        )

        self.assertNotIn(
            "invalid_completion_blank",
            validate_question(completion, v11_sources()),
        )

    def test_completion_accepts_adapted_grammar_when_an_accepted_answer_is_literal(self) -> None:
        source_quote = "Guardé el asunto en mi corazón."
        sources = {
            "DAN1-V001": {
                "source_ref": "Daniel 1:1",
                "source_quote": source_quote,
            }
        }
        completion = valid_v11_question(
            family="fill_choice",
            question="Al cerrar el relato, Daniel ____.",
            options=[
                "guardó el asunto en su corazón",
                "rechazó lo que había visto",
                "entregó el asunto a otros",
                "proclamó la visión en público",
            ],
            correct_answer="guardó el asunto en su corazón",
            accepted_answers=[
                "guardó el asunto en su corazón",
                "Guardé el asunto en mi corazón",
            ],
            why_distractors_fail={
                "rechazó lo que había visto": "No rechazó la visión.",
                "entregó el asunto a otros": "La guardó consigo.",
                "proclamó la visión en público": "El cierre describe reserva interior.",
            },
            source_quote=source_quote,
            evidence_excerpt=source_quote,
            blank_span="guardó el asunto en su corazón",
            significance="Evalúa la acción final de Daniel.",
            option_category="action",
        )

        self.assertNotIn("blank_not_in_source", validate_question(completion, sources))

    def test_completion_accepts_a_supported_derivational_form(self) -> None:
        source_quote = "El rey se contristará y retrocederá."
        sources = {
            "DAN1-V001": {
                "source_ref": "Daniel 1:1",
                "source_quote": source_quote,
            }
        }
        completion = valid_v11_question(
            family="fill_choice",
            question="El encuentro provocará en el rey ____ antes del retroceso.",
            options=["euforia", "aflicción", "indiferencia", "audacia"],
            correct_option=1,
            correct_answer="aflicción",
            accepted_answers=["aflicción", "contristación", "tristeza"],
            why_distractors_fail={
                "euforia": "Invierte la reacción.",
                "indiferencia": "El encuentro sí lo afecta.",
                "audacia": "El texto describe abatimiento.",
            },
            source_quote=source_quote,
            evidence_excerpt=source_quote,
            blank_span="aflicción",
            significance="Evalúa la reacción emocional del rey.",
            option_category="emotion",
        )

        errors = validate_question(completion, sources)

        self.assertNotIn("answer_not_supported", errors)
        self.assertNotIn("blank_not_in_source", errors)

    def test_completion_accepts_an_explicit_literal_support_term(self) -> None:
        source_quote = "Nunca compele Dios a los hombres a obedecer."
        sources = {
            "DAN1-V001": {
                "source_ref": "Daniel 1:1",
                "source_quote": source_quote,
            }
        }
        completion = valid_v11_question(
            family="fill_choice",
            question="Dios deja la obediencia libre de ____.",
            options=["instrucción", "convicción", "responsabilidad", "compulsión"],
            correct_option=3,
            correct_answer="compulsión",
            accepted_answers=["compulsión", "coacción"],
            why_distractors_fail={
                "instrucción": "No equivale a compeler.",
                "convicción": "No equivale a compeler.",
                "responsabilidad": "No equivale a compeler.",
            },
            source_quote=source_quote,
            evidence_excerpt=source_quote,
            blank_span="compulsión",
            significance="Evalúa la libertad de la obediencia.",
            option_category="principle",
            answer_support_term="compele",
        )

        errors = validate_question(completion, sources)

        self.assertNotIn("answer_not_supported", errors)
        self.assertNotIn("blank_not_in_source", errors)

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


class BlindPoolContractTests(unittest.TestCase):
    """Impide que una reserva ciega se filtre o reutilice hechos de práctica."""

    def distinct_question(self, *, suffix: str, fact_id: str, blind_pool):
        return valid_v11_question(
            id=f"DAN1-V11-BLIND-{suffix}",
            fact_id=fact_id,
            question=f"¿Qué participante corresponde al detalle competitivo {suffix}?",
            blind_pool=blind_pool,
        )

    def write_compile_fixture(self, root: Path, rows: list[dict]) -> None:
        questions = root / "questions"
        packets = root / "source-packets"
        questions.mkdir(parents=True, exist_ok=True)
        packets.mkdir(parents=True, exist_ok=True)
        for unit in compile_competitive_v11.EXPECTED_UNITS:
            payload = rows if unit == "DAN1" else []
            (questions / f"{unit}.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
        source = {
            "source_unit_id": "DAN1-V001",
            **v11_sources()["DAN1-V001"],
        }
        (packets / "DAN1.json").write_text(
            json.dumps({"units": [source]}, ensure_ascii=False), encoding="utf-8"
        )

    def workspace_fixture(self, name: str) -> Path:
        root = Path("tmp/competitive-v11-tests") / f"{name}-{os.getpid()}"
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, root, True)
        return root

    def test_rejects_a_fact_shared_between_training_and_blind_domains(self) -> None:
        rows = [
            self.distinct_question(suffix="TRAIN", fact_id="F-SHARED", blind_pool=None),
            self.distinct_question(suffix="A", fact_id="F-SHARED", blind_pool="A"),
        ]

        audit = audit_corpus(rows)

        self.assertEqual(audit["mixed_fact_ownership"], ["F-SHARED"])

    def test_rejects_a_fact_shared_by_two_blind_pools(self) -> None:
        rows = [
            self.distinct_question(suffix="A", fact_id="F-SHARED", blind_pool="A"),
            self.distinct_question(suffix="B", fact_id="F-SHARED", blind_pool="B"),
        ]

        audit = audit_corpus(rows)

        self.assertEqual(audit["blind_pool_fact_collisions"], ["F-SHARED"])

    def test_blind_facts_have_exactly_one_presentation(self) -> None:
        rows = [
            self.distinct_question(suffix="A1", fact_id="F-A", blind_pool="A"),
            self.distinct_question(suffix="A2", fact_id="F-A", blind_pool="A"),
        ]

        audit = audit_corpus(rows)

        self.assertEqual(audit["blind_facts_with_multiple_presentations"], ["F-A"])

    def test_rejects_every_blind_variant_even_when_it_is_orphaned(self) -> None:
        blind_variant = self.distinct_question(
            suffix="VARIANT", fact_id="F-VARIANT", blind_pool="A"
        )
        blind_variant["role"] = "variant"
        blind_variant["variant_justification"] = "Presentación alternativa."

        self.assertIn(
            "blind_variant_not_allowed",
            validate_question(blind_variant, v11_sources()),
        )

    def test_release_requirements_validate_parametric_fact_and_family_counts(self) -> None:
        rows = [
            self.distinct_question(suffix="A", fact_id="F-A", blind_pool="A"),
        ]
        requirements = {
            "A": {"fact_count": 2, "families": {"selection": 2}},
            "B": {"fact_count": 1, "families": {"selection": 1}},
        }

        audit = audit_corpus(rows, blind_requirements=requirements)

        self.assertEqual(
            audit["blind_pool_requirement_violations"],
            [
                "A:fact_count:expected=2:actual=1",
                "A:family:selection:expected=2:actual=1",
                "B:fact_count:expected=1:actual=0",
                "B:family:selection:expected=1:actual=0",
            ],
        )

    def test_rejects_invalid_custom_requirement_schemas(self) -> None:
        valid = {
            "A": {"fact_count": 1, "families": {"selection": 1, "fill_choice": 0, "true_false": 0}},
            "B": {"fact_count": 0, "families": {"selection": 0, "fill_choice": 0, "true_false": 0}},
            "emergency": {"fact_count": 0, "families": {"selection": 0, "fill_choice": 0, "true_false": 0}},
        }
        invalid = [
            {key: value for key, value in valid.items() if key != "emergency"},
            {**valid, "C": valid["B"]},
            {**valid, "A": {**valid["A"], "fact_count": -1}},
            {**valid, "A": {**valid["A"], "fact_count": True}},
            {**valid, "A": {**valid["A"], "families": {"selection": 1}}},
            {**valid, "A": {**valid["A"], "families": {**valid["A"]["families"], "other": 0}}},
            {**valid, "A": {**valid["A"], "families": {**valid["A"]["families"], "selection": "1"}}},
            {**valid, "A": {**valid["A"], "fact_count": 2}},
        ]

        self.assertEqual(compile_competitive_v11.validate_blind_requirements(valid), valid)
        for requirements in invalid:
            with self.subTest(requirements=requirements):
                with self.assertRaises(ValueError):
                    compile_competitive_v11.validate_blind_requirements(requirements)

    def test_compiler_separates_public_training_from_private_blind_artifact(self) -> None:
        rows = [
            self.distinct_question(suffix="TRAIN", fact_id="F-TRAIN", blind_pool=None),
            self.distinct_question(suffix="A", fact_id="F-A", blind_pool="A"),
            self.distinct_question(suffix="B", fact_id="F-B", blind_pool="B"),
        ]
        directory = self.workspace_fixture("blind-compiler-partition")
        root = directory / "source"
        output = directory / "public-bank"
        blind_output = directory / "private-blind"
        self.write_compile_fixture(root, rows)

        manifest = compile_competitive_v11.compile_bank(
            root, output, blind_output=blind_output
        )

        training = json.loads(
            (output / "questions" / "DAN1.json").read_text(encoding="utf-8")
        )
        blind_a = json.loads(
            (blind_output / "questions" / "A" / "DAN1.json").read_text(
                encoding="utf-8"
            )
        )
        blind_b = json.loads(
            (blind_output / "questions" / "B" / "DAN1.json").read_text(
                encoding="utf-8"
            )
        )
        private_manifest = json.loads(
            (blind_output / "manifest.json").read_text(encoding="utf-8")
        )
        public_reviews = json.loads(
            (output / "review-index.json").read_text(encoding="utf-8")
        )
        private_reviews = json.loads(
            (blind_output / "review-index.json").read_text(encoding="utf-8")
        )

        self.assertFalse((output / "blind").exists())
        self.assertEqual([row["fact_id"] for row in training], ["F-TRAIN"])
        self.assertEqual([row["fact_id"] for row in blind_a], ["F-A"])
        self.assertEqual([row["fact_id"] for row in blind_b], ["F-B"])
        self.assertEqual(training[0]["role"], "central")
        self.assertEqual(blind_a[0]["role"], "central")
        self.assertEqual(manifest["gold_questions"], 1)
        self.assertEqual(manifest["unique_facts"], 1)
        self.assertEqual(manifest["training_presentation_count"], 1)
        self.assertEqual(manifest["total_presentation_count"], 3)
        self.assertEqual(manifest["total_fact_count"], 3)
        self.assertEqual(manifest["blind_presentation_count"], 2)
        self.assertEqual(
            manifest["blind_pools"]["A"],
            {
                "fact_count": 1,
                "presentation_count": 1,
                "families": {"selection": 1, "fill_choice": 0, "true_false": 0},
            },
        )
        self.assertEqual(manifest["blind_delivery"]["contract"], "private-blind-artifact-v1")
        self.assertEqual(manifest["blind_delivery"]["artifact_id"], "competitive-v11-blind")
        self.assertRegex(manifest["blind_delivery"]["artifact_revision"], r"^[0-9a-f]{64}$")
        self.assertNotIn("questions_file", json.dumps(manifest["blind_pools"]))
        self.assertNotIn("F-A", json.dumps(manifest))
        self.assertEqual(
            [entry["question_id"] for entry in public_reviews["entries"]],
            ["DAN1-V11-BLIND-TRAIN"],
        )
        self.assertEqual(
            {entry["question_id"] for entry in private_reviews["entries"]},
            {"DAN1-V11-BLIND-A", "DAN1-V11-BLIND-B"},
        )
        self.assertEqual(private_manifest["contract"], "private-blind-artifact-v1")
        self.assertEqual(
            private_manifest["artifact_revision"],
            manifest["blind_delivery"]["artifact_revision"],
        )
        self.assertEqual(private_manifest["build_id"], manifest["build_id"])
        self.assertEqual(
            compile_competitive_v11.validate_artifact_pair(manifest, private_manifest),
            manifest["build_id"],
        )
        self.assertEqual(
            compile_competitive_v11.validate_artifact_pair(
                manifest, private_manifest, output, blind_output
            ),
            manifest["build_id"],
        )
        self.assertEqual(
            compile_competitive_v11.validate_emitted_pair(output, blind_output),
            manifest["build_id"],
        )
        with patch(
            "sys.argv",
            ["compile-competitive-v11.py", "--validate-pair", str(output), str(blind_output)],
        ), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(compile_competitive_v11.main(), 0)
            self.assertIn(manifest["build_id"], stdout.getvalue())
        self.assertEqual(
            private_manifest["pools"]["A"]["shards"][0]["questions_file"],
            "questions/A/DAN1.json",
        )

        for artifact_root, shard in [
            (output, manifest["shards"][0]),
            (blind_output, private_manifest["pools"]["A"]["shards"][0]),
        ]:
            relative = (
                shard["questions_file"].removeprefix("banks/final-2026/")
                if artifact_root == output
                else shard["questions_file"]
            )
            payload = (artifact_root / relative).read_bytes()
            self.assertEqual(shard["bytes"], len(payload))
            self.assertEqual(shard["sha256"], hashlib.sha256(payload).hexdigest())

        tampered_manifest = json.loads(json.dumps(manifest))
        tampered_manifest["blind_pools"]["A"]["fact_count"] = 9
        with self.assertRaisesRegex(ValueError, "mismatch"):
            compile_competitive_v11.validate_artifact_pair(
                tampered_manifest, private_manifest
            )

        tampered_totals_public = json.loads(json.dumps(manifest))
        tampered_totals_private = json.loads(json.dumps(private_manifest))
        tampered_totals_public["blind_fact_count"] = 9
        tampered_totals_private["total_fact_count"] = 9
        with self.assertRaisesRegex(ValueError, "blind totals"):
            compile_competitive_v11.validate_artifact_pair(
                tampered_totals_public, tampered_totals_private
            )

        invalid_build_public = json.loads(json.dumps(manifest))
        invalid_build_private = json.loads(json.dumps(private_manifest))
        for target in (
            invalid_build_public,
            invalid_build_public["blind_delivery"],
            invalid_build_private,
        ):
            if "build_id" in target:
                target["build_id"] = "A" * 64
            if "artifact_revision" in target:
                target["artifact_revision"] = "A" * 64
        with self.assertRaisesRegex(ValueError, "build_id"):
            compile_competitive_v11.validate_artifact_pair(
                invalid_build_public, invalid_build_private
            )

        invalid_roles = json.loads(json.dumps(manifest))
        invalid_roles["central_question_count"] = 0
        invalid_roles["presentation_variant_count"] = 1
        with self.assertRaisesRegex(ValueError, "role totals"):
            compile_competitive_v11.validate_artifact_pair(
                invalid_roles, private_manifest
            )

        original_blind_a = blind_output / "questions" / "A" / "DAN1.json"
        original_blind_a_payload = original_blind_a.read_bytes()
        tampered_private = json.loads(json.dumps(private_manifest))
        tampered_rows = json.loads(original_blind_a_payload)
        tampered_rows[0]["role"] = "variant"
        integrity = compile_competitive_v11.write_json(original_blind_a, tampered_rows)
        tampered_private["pools"]["A"]["shards"][0].update(integrity)
        with self.assertRaisesRegex(ValueError, "private shard role"):
            compile_competitive_v11.validate_artifact_pair(
                manifest, tampered_private, output, blind_output
            )
        original_blind_a.write_bytes(original_blind_a_payload)

        original_blind_b = blind_output / "questions" / "B" / "DAN1.json"
        original_blind_b_payload = original_blind_b.read_bytes()
        duplicate_fact_private = json.loads(json.dumps(private_manifest))
        duplicate_fact_rows = json.loads(original_blind_b_payload)
        duplicate_fact_rows[0]["fact_id"] = "F-A"
        duplicate_fact_rows[0]["row_content_sha256"] = (
            compile_competitive_v11.emitted_row_hash(duplicate_fact_rows[0])
        )
        integrity = compile_competitive_v11.write_json(
            original_blind_b, duplicate_fact_rows
        )
        duplicate_fact_private["pools"]["B"]["shards"][0].update(integrity)
        with self.assertRaisesRegex(ValueError, "blind facts"):
            compile_competitive_v11.validate_artifact_pair(
                manifest, duplicate_fact_private, output, blind_output
            )
        original_blind_b.write_bytes(original_blind_b_payload)

        cross_domain_private = json.loads(json.dumps(private_manifest))
        cross_domain_rows = json.loads(original_blind_b_payload)
        cross_domain_rows[0]["fact_id"] = "F-TRAIN"
        cross_domain_rows[0]["row_content_sha256"] = (
            compile_competitive_v11.emitted_row_hash(cross_domain_rows[0])
        )
        integrity = compile_competitive_v11.write_json(
            original_blind_b, cross_domain_rows
        )
        cross_domain_private["pools"]["B"]["shards"][0].update(integrity)
        with self.assertRaisesRegex(ValueError, "fact ownership"):
            compile_competitive_v11.validate_artifact_pair(
                manifest, cross_domain_private, output, blind_output
            )
        original_blind_b.write_bytes(original_blind_b_payload)

        blind_path = blind_output / "questions" / "A" / "DAN1.json"
        blind_path.write_bytes(blind_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            compile_competitive_v11.validate_artifact_pair(
                manifest, private_manifest, output, blind_output
            )

    def test_output_path_guards_reject_source_and_artifact_overlap(self) -> None:
        directory = self.workspace_fixture("blind-output-guards").resolve()
        source = directory / "source"
        public = directory / "public"
        private = directory / "private"
        source.mkdir()
        invalid = [
            (source, private),
            (source / "generated", private),
            (source.parent, private),
            (public, public),
            (public, public / "blind"),
            (public / "nested", public),
            (public, public.parent / f".{public.name}.tmp"),
        ]

        for output, blind_output in invalid:
            with self.subTest(output=output, blind_output=blind_output):
                with self.assertRaises(ValueError):
                    compile_competitive_v11.validate_output_paths(
                        source, output, blind_output
                    )

        self.assertEqual(
            compile_competitive_v11.validate_output_paths(source, public, private),
            (source, public, private),
        )
        with self.assertRaisesRegex(ValueError, "web root"):
            compile_competitive_v11.validate_output_paths(
                source,
                public,
                compile_competitive_v11.ROOT / "public" / "private-blind",
            )
        with self.assertRaisesRegex(ValueError, "web root"):
            compile_competitive_v11.validate_output_paths(
                Path("C:/external-source"),
                Path("C:/external-public"),
                compile_competitive_v11.ROOT,
            )

    def test_emitted_build_id_detects_shard_and_descriptor_tampering(self) -> None:
        directory = self.workspace_fixture("blind-build-descriptor-tamper")
        root = directory / "source"
        output = directory / "public-bank"
        blind_output = directory / "private-blind"
        self.write_compile_fixture(
            root,
            [
                self.distinct_question(
                    suffix="TRAIN", fact_id="F-TRAIN", blind_pool=None
                ),
                self.distinct_question(suffix="A", fact_id="F-A", blind_pool="A"),
            ],
        )
        compile_competitive_v11.compile_bank(root, output, blind_output=blind_output)
        public_manifest = json.loads(
            (output / "manifest.json").read_text(encoding="utf-8")
        )
        private_manifest = json.loads(
            (blind_output / "manifest.json").read_text(encoding="utf-8")
        )
        shard_path = blind_output / "questions" / "A" / "DAN1.json"
        rows = json.loads(shard_path.read_text(encoding="utf-8"))
        payload = json.dumps(
            rows, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        shard_path.write_bytes(payload)
        integrity = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
        private_manifest["pools"]["A"]["shards"][0].update(integrity)

        with self.assertRaisesRegex(ValueError, "build_id"):
            compile_competitive_v11.validate_artifact_pair(
                public_manifest, private_manifest, output, blind_output
            )

    def test_review_ledgers_are_exact_and_cannot_cross_domains(self) -> None:
        directory = self.workspace_fixture("blind-review-ledger-attacks")
        root = directory / "source"
        output = directory / "public-bank"
        blind_output = directory / "private-blind"
        self.write_compile_fixture(
            root,
            [
                self.distinct_question(
                    suffix="TRAIN-1", fact_id="F-TRAIN-1", blind_pool=None
                ),
                self.distinct_question(
                    suffix="TRAIN-2", fact_id="F-TRAIN-2", blind_pool=None
                ),
                self.distinct_question(suffix="A", fact_id="F-A", blind_pool="A"),
            ],
        )
        compile_competitive_v11.compile_bank(root, output, blind_output=blind_output)
        public_manifest = json.loads(
            (output / "manifest.json").read_text(encoding="utf-8")
        )
        private_manifest = json.loads(
            (blind_output / "manifest.json").read_text(encoding="utf-8")
        )
        review_path = output / "review-index.json"
        original_review = json.loads(review_path.read_text(encoding="utf-8"))

        attacks = []
        crossed = json.loads(json.dumps(original_review))
        crossed["entries"][0]["question_id"] = "DAN1-V11-BLIND-A"
        attacks.append(crossed)
        duplicated = json.loads(json.dumps(original_review))
        duplicated["entries"][1]["question_id"] = duplicated["entries"][0][
            "question_id"
        ]
        attacks.append(duplicated)
        missing = json.loads(json.dumps(original_review))
        missing["entries"].pop()
        missing["total_reviewed"] = 1
        attacks.append(missing)
        wrong_hash = json.loads(json.dumps(original_review))
        wrong_hash["entries"][0]["content_sha256"] = "0" * 64
        attacks.append(wrong_hash)

        for review in attacks:
            tampered_manifest = json.loads(json.dumps(public_manifest))
            integrity = compile_competitive_v11.write_json(review_path, review)
            tampered_manifest["review_index"].update(integrity)
            with self.subTest(review=review["entries"]):
                with self.assertRaisesRegex(ValueError, "review ledger"):
                    compile_competitive_v11.validate_artifact_pair(
                        tampered_manifest,
                        private_manifest,
                        output,
                        blind_output,
                    )

    def test_windows_path_guards_reject_aliases_and_reserved_components(self) -> None:
        base = Path("C:/safe-contract-root")
        source = base / "source"
        public = base / "public-artifact"
        invalid_private = [
            base / "private.",
            base / "private ",
            base / "private:stream",
            base / "CON",
            base / "prn.json",
            base / "AuX",
            base / "NUL.txt",
            base / "COM1",
            base / "lpt9.data",
        ]
        for private in invalid_private:
            with self.subTest(private=private):
                with self.assertRaises(ValueError):
                    compile_competitive_v11.validate_output_paths(
                        source, public, private
                    )

        with self.assertRaises(ValueError):
            compile_competitive_v11.validate_output_paths(
                source, base / "CaseAlias", base / "casealias"
            )

    def test_pair_swap_rolls_back_when_private_replacement_fails(self) -> None:
        directory = self.workspace_fixture("blind-pair-rollback")
        public = directory / "public"
        private = directory / "private"
        public_stage = directory / ".public.tmp"
        private_stage = directory / ".private.tmp"
        for path, marker in [
            (public, "old-public"),
            (private, "old-private"),
            (public_stage, "new-public"),
            (private_stage, "new-private"),
        ]:
            path.mkdir()
            (path / "marker.txt").write_text(marker, encoding="utf-8")
        original_rename = Path.rename

        def fail_private_stage(path: Path, target: Path):
            if path == private_stage:
                raise PermissionError("simulated private swap failure")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_private_stage), patch(
            "time.sleep", return_value=None
        ):
            with self.assertRaises(PermissionError):
                compile_competitive_v11.replace_artifact_pair(
                    public_stage, public, private_stage, private
                )

        self.assertEqual((public / "marker.txt").read_text(), "old-public")
        self.assertEqual((private / "marker.txt").read_text(), "old-private")

    def test_pair_swap_failure_without_previous_pair_leaves_both_absent(self) -> None:
        directory = self.workspace_fixture("blind-pair-first-failure")
        public = directory / "public"
        private = directory / "private"
        public_stage = directory / ".public.tmp"
        private_stage = directory / ".private.tmp"
        public_stage.mkdir()
        private_stage.mkdir()
        original_rename = Path.rename

        def fail_private_stage(path: Path, target: Path):
            if path == private_stage:
                raise PermissionError("simulated private swap failure")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_private_stage), patch(
            "time.sleep", return_value=None
        ):
            with self.assertRaises(PermissionError):
                compile_competitive_v11.replace_artifact_pair(
                    public_stage, public, private_stage, private
                )

        self.assertFalse(public.exists())
        self.assertFalse(private.exists())

    def test_pair_swap_keeps_old_pair_when_first_backup_move_fails(self) -> None:
        directory = self.workspace_fixture("blind-pair-backup-failure")
        public = directory / "public"
        private = directory / "private"
        public_stage = directory / ".public.tmp"
        private_stage = directory / ".private.tmp"
        for path, marker in [
            (public, "old-public"),
            (private, "old-private"),
            (public_stage, "new-public"),
            (private_stage, "new-private"),
        ]:
            path.mkdir()
            (path / "marker.txt").write_text(marker, encoding="utf-8")
        original_rename = Path.rename

        def fail_public_backup(path: Path, target: Path):
            if path == public:
                raise PermissionError("simulated backup failure")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_public_backup), patch(
            "time.sleep", return_value=None
        ):
            with self.assertRaises(PermissionError):
                compile_competitive_v11.replace_artifact_pair(
                    public_stage, public, private_stage, private
                )

        self.assertEqual((public / "marker.txt").read_text(), "old-public")
        self.assertEqual((private / "marker.txt").read_text(), "old-private")

    def test_pair_swap_recovers_stale_backup_before_attempting_new_pair(self) -> None:
        directory = self.workspace_fixture("blind-pair-stale-backup")
        public = directory / "public"
        private = directory / "private"
        public_backup = directory / ".public.backup"
        public_stage = directory / ".public.tmp"
        private_stage = directory / ".private.tmp"
        for path, marker in [
            (public_backup, "old-public"),
            (private, "old-private"),
            (public_stage, "new-public"),
            (private_stage, "new-private"),
        ]:
            path.mkdir()
            (path / "marker.txt").write_text(marker, encoding="utf-8")
        original_rename = Path.rename

        def fail_private_stage(path: Path, target: Path):
            if path == private_stage:
                raise PermissionError("simulated private swap failure")
            return original_rename(path, target)

        with patch.object(Path, "rename", fail_private_stage), patch(
            "time.sleep", return_value=None
        ):
            with self.assertRaises(PermissionError):
                compile_competitive_v11.replace_artifact_pair(
                    public_stage, public, private_stage, private
                )

        self.assertEqual((public / "marker.txt").read_text(), "old-public")
        self.assertEqual((private / "marker.txt").read_text(), "old-private")

    def test_public_and_private_manifests_expose_detectable_build_mismatch(self) -> None:
        public = {
            "blind_delivery": {
                "contract": "private-blind-artifact-v1",
                "artifact_id": "competitive-v11-blind",
                "artifact_revision": "a" * 64,
            },
            "build_id": "a" * 64,
        }
        private = {
            "contract": "private-blind-artifact-v1",
            "artifact_id": "competitive-v11-blind",
            "artifact_revision": "b" * 64,
            "build_id": "b" * 64,
        }

        with self.assertRaisesRegex(ValueError, "mismatch"):
            compile_competitive_v11.validate_artifact_pair(public, private)

    def test_recompile_removes_stale_public_and_private_shards(self) -> None:
        directory = self.workspace_fixture("blind-stale-cleanup")
        root = directory / "source"
        output = directory / "public-bank"
        blind_output = directory / "private-blind"
        self.write_compile_fixture(
            root,
            [
                self.distinct_question(suffix="TRAIN", fact_id="F-TRAIN", blind_pool=None),
                self.distinct_question(suffix="A", fact_id="F-A", blind_pool="A"),
            ],
        )
        compile_competitive_v11.compile_bank(root, output, blind_output=blind_output)
        (output / "blind" / "stale").mkdir(parents=True)
        (output / "blind" / "stale" / "leak.json").write_text("secret", encoding="utf-8")
        self.assertTrue((blind_output / "questions" / "A" / "DAN1.json").exists())

        self.write_compile_fixture(
            root,
            [self.distinct_question(suffix="TRAIN", fact_id="F-TRAIN", blind_pool=None)],
        )
        compile_competitive_v11.compile_bank(root, output, blind_output=blind_output)

        self.assertFalse((output / "blind").exists())
        self.assertFalse((blind_output / "questions" / "A" / "DAN1.json").exists())
        private_manifest = json.loads(
            (blind_output / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            private_manifest["pools"],
            {
                pool: {
                    "fact_count": 0,
                    "presentation_count": 0,
                    "families": {"selection": 0, "fill_choice": 0, "true_false": 0},
                    "shards": [],
                }
                for pool in ("A", "B", "emergency")
            },
        )

    def test_release_gate_is_optional_but_fails_closed_when_requested(self) -> None:
        rows = [
            self.distinct_question(suffix="TRAIN", fact_id="F-TRAIN", blind_pool=None),
        ]
        requirements = {
            "A": {"fact_count": 1, "families": {"selection": 1, "fill_choice": 0, "true_false": 0}},
            "B": {"fact_count": 0, "families": {"selection": 0, "fill_choice": 0, "true_false": 0}},
            "emergency": {"fact_count": 0, "families": {"selection": 0, "fill_choice": 0, "true_false": 0}},
        }
        directory = self.workspace_fixture("blind-compiler-gate")
        root = directory / "source"
        output = directory / "public-bank"
        self.write_compile_fixture(root, rows)

        manifest = compile_competitive_v11.compile_bank(root, output)
        self.assertEqual(manifest["blind_presentation_count"], 0)

        with self.assertRaisesRegex(ValueError, "blind_output"):
            compile_competitive_v11.compile_bank(
                root,
                output,
                blind_requirements=requirements,
            )

        with self.assertRaisesRegex(ValueError, "blind_pool_requirement_violations"):
            compile_competitive_v11.compile_bank(
                root,
                output,
                blind_output=directory / "private-blind",
                blind_requirements=requirements,
            )


class SeedImportTests(unittest.TestCase):
    """Preserva el banco bueno y declara honestamente su revisión heredada."""

    def test_flattens_a_verified_presentation_variant_without_rewriting_prose(self) -> None:
        central = valid_v11_question()
        for key in ("role", "blank_span", "significance", "variant_justification"):
            central.pop(key)
        central["content_sha256"] = "production-central-hash"
        central["validation_adversarial"] = {
            "reviewer": "production-cross-reviewer",
            "status": "passed",
            "selected_option": 0,
            "second_defensible_option": False,
            "content_sha256": "production-central-hash",
        }
        central["presentation_variants"] = [
            {
                "id": "PV-DAN1-0001",
                "question": "____ llegó a Jerusalén y la sitió.",
                "options": ["Nabucodonosor", "Ciro", "Darío", "Belsasar"],
                "correct_option": 0,
                "correct_answer": "Nabucodonosor",
                "accepted_answers": ["Nabucodonosor"],
                "explanation": "Nabucodonosor llegó a Jerusalén y la sitió.",
                "why_distractors_fail": central["why_distractors_fail"],
                "content_sha256": "production-variant-hash",
                "review": {
                    "status": "passed",
                    "reviewer_type": "ai_semantic_audit",
                    "reviewer": "production-variant-reviewer",
                    "content_sha256": "production-variant-hash",
                    "selected_option": 0,
                    "second_defensible_option": False,
                },
            }
        ]

        authored, reviews = import_seed("DAN1", [central], v11_sources())

        self.assertEqual(len(authored), 2)
        self.assertEqual(authored[0]["role"], "central")
        self.assertEqual(authored[0]["question"], central["question"])
        self.assertEqual(authored[1]["role"], "variant")
        self.assertEqual(authored[1]["family"], "fill_choice")
        self.assertEqual(authored[1]["question"], "____ llegó a Jerusalén y la sitió.")
        self.assertTrue(
            all("human" not in row["ai_review"]["reviewer_type"] for row in authored)
        )
        self.assertEqual(
            [review["source_content_sha256"] for review in reviews],
            ["production-central-hash", "production-variant-hash"],
        )
        self.assertEqual(
            [review["content_sha256"] for review in reviews],
            [content_hash(row) for row in authored],
        )

    def test_checked_in_seed_contains_the_verified_production_baseline(self) -> None:
        question_root = Path("content/competitive-v11/questions")
        review_root = Path("content/competitive-v11/reviews")
        self.assertTrue(question_root.exists(), "debe importarse el corpus inicial V11")
        question_files = sorted(question_root.glob("*.json"))
        review_files = sorted(review_root.glob("*.json"))
        self.assertEqual(len(question_files), 18)
        self.assertEqual(len(review_files), 18)

        questions = [
            row
            for path in question_files
            for row in json.loads(path.read_text(encoding="utf-8"))
        ]
        reviews = [
            row
            for path in review_files
            for row in json.loads(path.read_text(encoding="utf-8"))
        ]
        baseline_questions = [row for row in questions if "-V11-" not in row["id"]]
        baseline_reviews = [
            row for row in reviews if "-V11-" not in row["question_id"]
        ]
        self.assertEqual(
            len([row for row in baseline_questions if row["role"] == "central"]),
            1024,
        )
        self.assertEqual(
            len([row for row in baseline_questions if row["role"] == "variant"]),
            251,
        )
        self.assertEqual(len(baseline_questions), 1275)
        self.assertEqual(len(baseline_reviews), 1275)
        self.assertEqual(
            {row["question_id"]: row["content_sha256"] for row in baseline_reviews},
            {row["id"]: content_hash(row) for row in baseline_questions},
        )

    def test_recognizes_true_false_variant_when_option_order_is_reversed(self) -> None:
        central = valid_v11_question()
        central["false_mutation"] = {
            "changed_fields": ["person"],
            "local": True,
            "original": "Nabucodonosor",
            "replacement": "Ciro",
        }
        for key in ("role", "blank_span", "significance", "variant_justification"):
            central.pop(key)
        central["content_sha256"] = "production-central-hash"
        central["validation_adversarial"] = {
            "reviewer": "production-cross-reviewer",
            "status": "passed",
            "selected_option": 0,
            "second_defensible_option": False,
        }
        central["presentation_variants"] = [
            {
                "id": "PV-DAN1-TF-0001",
                "question": "Nabucodonosor llegó a Jerusalén y la sitió.",
                "options": ["Falso", "Verdadero"],
                "correct_option": 1,
                "correct_answer": "Verdadero",
                "accepted_answers": ["Verdadero"],
                "explanation": "La afirmación reproduce la acción narrada.",
                "why_distractors_fail": {
                    "Falso": "El sitio de Jerusalén sí aparece en la fuente."
                },
                "content_sha256": "production-tf-variant-hash",
                "review": {
                    "status": "passed",
                    "reviewer_type": "ai_semantic_audit",
                    "reviewer": "production-variant-reviewer",
                    "content_sha256": "production-tf-variant-hash",
                    "selected_option": 1,
                    "second_defensible_option": False,
                },
            }
        ]

        try:
            authored, _ = import_seed("DAN1", [central], v11_sources())
        except ValueError as exc:
            self.fail(f"la variante V/F invertida debe importarse: {exc}")

        self.assertEqual(authored[1]["family"], "true_false")
        self.assertIsNone(authored[1]["false_mutation"])

    def test_applies_an_explicit_editorial_mutation_to_a_false_variant(self) -> None:
        central = valid_v11_question()
        for key in ("role", "blank_span", "significance", "variant_justification"):
            central.pop(key)
        central["content_sha256"] = "production-central-hash"
        central["validation_adversarial"] = {
            "reviewer": "production-cross-reviewer",
            "status": "passed",
            "selected_option": 0,
            "second_defensible_option": False,
        }
        central["presentation_variants"] = [
            {
                "id": "PV-DAN1-FALSE-0001",
                "question": "Ciro llegó a Jerusalén y la sitió.",
                "options": ["Verdadero", "Falso"],
                "correct_option": 1,
                "correct_answer": "Falso",
                "accepted_answers": ["Falso"],
                "explanation": "La fuente identifica a Nabucodonosor, no a Ciro.",
                "why_distractors_fail": {
                    "Verdadero": "La identidad del sitiador fue alterada."
                },
                "content_sha256": "production-false-variant-hash",
                "review": {
                    "status": "passed",
                    "reviewer_type": "ai_semantic_audit",
                    "reviewer": "production-variant-reviewer",
                    "content_sha256": "production-false-variant-hash",
                    "selected_option": 1,
                    "second_defensible_option": False,
                },
            }
        ]
        override = {
            "PV-DAN1-FALSE-0001": {
                "changed_fields": ["person"],
                "local": True,
                "original": "Nabucodonosor",
                "replacement": "Ciro",
            }
        }

        try:
            authored, _ = import_seed(
                "DAN1",
                [central],
                v11_sources(),
                false_mutation_overrides=override,
            )
        except (TypeError, ValueError) as exc:
            self.fail(f"la mutación editorial explícita debe aplicarse: {exc}")

        self.assertEqual(authored[1]["false_mutation"], override["PV-DAN1-FALSE-0001"])

    def test_explicit_editorial_mutation_can_correct_existing_central_metadata(self) -> None:
        central = valid_v11_question(
            family="true_false",
            question="Ciro llegó a Jerusalén y la sitió.",
            options=["Verdadero", "Falso"],
            correct_option=1,
            correct_answer="Falso",
            accepted_answers=["Falso"],
            false_mutation={
                "changed_fields": ["person"],
                "local": True,
                "original": "el monarca babilónico",
                "replacement": "Ciro",
            },
        )
        for key in ("role", "blank_span", "significance", "variant_justification"):
            central.pop(key)
        central["content_sha256"] = "production-central-hash"
        central["validation_adversarial"] = {
            "reviewer": "production-cross-reviewer",
            "status": "passed",
            "selected_option": 1,
            "second_defensible_option": False,
        }
        override = {
            central["id"]: {
                "changed_fields": ["person"],
                "local": True,
                "original": "Nabucodonosor",
                "replacement": "Ciro",
            }
        }

        authored, _ = import_seed(
            "DAN1",
            [central],
            v11_sources(),
            false_mutation_overrides=override,
        )

        self.assertEqual(authored[0]["false_mutation"], override[central["id"]])

    def test_explicit_question_correction_removes_a_seed_answer_leak(self) -> None:
        central = valid_v11_question()
        for key in ("role", "blank_span", "significance", "variant_justification"):
            central.pop(key)
        central["content_sha256"] = "production-central-hash"
        central["validation_adversarial"] = {
            "reviewer": "production-cross-reviewer",
            "status": "passed",
            "selected_option": 0,
            "second_defensible_option": False,
        }
        central["presentation_variants"] = [
            {
                "id": "PV-DAN1-LEAK-0001",
                "question": "Además de Nabucodonosor, ¿quién sitió Jerusalén?",
                "options": ["Ciro", "Darío", "Belsasar", "Nabucodonosor"],
                "correct_option": 3,
                "correct_answer": "Nabucodonosor",
                "accepted_answers": ["Nabucodonosor"],
                "explanation": "La fuente identifica a Nabucodonosor.",
                "why_distractors_fail": {
                    "Ciro": "No aparece en el episodio.",
                    "Darío": "No aparece en el episodio.",
                    "Belsasar": "No aparece en el episodio.",
                },
                "content_sha256": "production-variant-hash",
                "review": {
                    "status": "passed",
                    "reviewer_type": "ai_semantic_audit",
                    "reviewer": "production-variant-reviewer",
                    "content_sha256": "production-variant-hash",
                    "selected_option": 3,
                    "second_defensible_option": False,
                },
            }
        ]
        correction = {
            "PV-DAN1-LEAK-0001": {
                "question": "¿Quién llegó a Jerusalén y la sitió?",
                "reviewer": "gpt-5.6-sol-v11-import-review",
                "reason": "Elimina la respuesta incluida en el enunciado.",
            }
        }

        authored, reviews = import_seed(
            "DAN1",
            [central],
            v11_sources(),
            editorial_overrides=correction,
        )

        self.assertEqual(authored[1]["question"], correction[authored[1]["id"]]["question"])
        self.assertEqual(reviews[1]["decision"], "corrected_during_v11_import")


class AuthoredBatchTests(unittest.TestCase):
    def test_compiles_authored_prose_without_generating_it(self) -> None:
        authored_input = {
            "id": "DAN1-V11-PILOT-001",
            "source_unit_id": "DAN1-V001",
            "fact_id": "DAN1-V001-V11-F02",
            "family": "single_choice_direct",
            "subtype": "factual_recall",
            "question": "¿Durante qué reinado llegó Nabucodonosor a Jerusalén?",
            "options": ["Joacim", "Ciro", "Darío", "Belsasar"],
            "correct_option": 0,
            "accepted_answers": ["Joacim"],
            "explanation": "El episodio se ubica en el reinado de Joacim.",
            "why_distractors_fail": {
                "Ciro": "Pertenece a otro período.",
                "Darío": "Pertenece a otro período.",
                "Belsasar": "Pertenece a otro período.",
            },
            "difficulty": "medium",
            "importance": "high",
            "relation_type": "time",
            "option_category": "person",
            "review": {
                "reviewer": "gpt-5.6-sol-v11-pilot-review",
                "rationale": "Joacim es la única respuesta respaldada.",
            },
        }

        questions, reviews = compile_authored_batch([authored_input], v11_sources())

        self.assertEqual(questions[0]["question"], authored_input["question"])
        self.assertEqual(questions[0]["source_quote"], v11_sources()["DAN1-V001"]["source_quote"])
        self.assertEqual(questions[0]["correct_answer"], "Joacim")
        self.assertEqual(reviews[0]["content_sha256"], content_hash(questions[0]))
        self.assertEqual(validate_question(questions[0], v11_sources()), [])

    def test_checked_in_pilot_has_exactly_100_reviewed_questions(self) -> None:
        question_paths = [
            Path("content/competitive-v11/questions/DAN7.json"),
            Path("content/competitive-v11/questions/PR43.json"),
        ]
        review_paths = [
            Path("content/competitive-v11/reviews/DAN7.json"),
            Path("content/competitive-v11/reviews/PR43.json"),
        ]
        questions = [
            row
            for path in question_paths
            for row in json.loads(path.read_text(encoding="utf-8"))
            if "-V11-PILOT-" in row["id"]
        ]
        reviews = [
            row
            for path in review_paths
            for row in json.loads(path.read_text(encoding="utf-8"))
            if "-V11-PILOT-" in row["question_id"]
        ]

        families = Counter(
            "selection" if row["family"].startswith("single_choice") else row["family"]
            for row in questions
        )
        units = Counter(row["id"].split("-V11-PILOT-")[0] for row in questions)

        self.assertEqual(len(questions), 100)
        self.assertEqual(families, {"selection": 45, "fill_choice": 30, "true_false": 25})
        self.assertEqual(units, {"DAN7": 40, "PR43": 60})
        selection_positions = Counter(
            row["correct_option"]
            for row in questions
            if row["family"].startswith("single_choice")
        )
        fill_positions = Counter(
            row["correct_option"] for row in questions if row["family"] == "fill_choice"
        )
        truth_balance = Counter(
            row["correct_answer"] for row in questions if row["family"] == "true_false"
        )
        self.assertLessEqual(max(selection_positions.values()) - min(selection_positions.values()), 1)
        self.assertLessEqual(max(fill_positions.values()) - min(fill_positions.values()), 1)
        self.assertEqual(truth_balance, {"Verdadero": 12, "Falso": 13})
        self.assertEqual(len(reviews), 100)
        self.assertEqual(
            {row["question_id"]: row["content_sha256"] for row in reviews},
            {row["id"]: content_hash(row) for row in questions},
        )
        self.assertFalse(any(audit_corpus(questions).values()))


if __name__ == "__main__":
    unittest.main()
