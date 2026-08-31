from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.lib import competitive_v13 as v13


SOURCE = {
    "source_unit_id": "DAN1-V001",
    "source_ref": "Daniel 1:1",
    "source_quote": (
        "En el tercer año del reinado de Joacim, rey de Judá, vino "
        "Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió."
    ),
    "parent_context": None,
}
BINDING_KEY = b"competitive-v13-test-binding-key!!"


def authored_question(question_id: str = "R2-DAN1-0001") -> dict[str, object]:
    return {
        "id": question_id,
        "source_unit_id": "DAN1-V001",
        "fact_id": "DAN1-V001-F04",
        "role": "variant",
        "family": "single_choice_direct",
        "subtype": "factual_recall",
        "question": "¿Qué acción militar realizó el rey al llegar a Jerusalén?",
        "options": ["La sitió", "La coronó", "La abandonó", "La reconstruyó"],
        "correct_option": 0,
        "accepted_answers": ["La sitió", "sitió"],
        "explanation": "El texto afirma que el rey sitió Jerusalén.",
        "why_distractors_fail": {
            "La coronó": "No se menciona una coronación.",
            "La abandonó": "El rey avanzó contra la ciudad.",
            "La reconstruyó": "La acción narrada es un sitio.",
        },
        "evidence_excerpt": "a Jerusalén, y la sitió",
        "difficulty": "hard",
        "importance": "high",
        "relation_type": "event_action",
        "option_category": "action",
        "false_mutation": None,
        "blank_span": None,
        "significance": None,
        "variant_justification": "Nueva formulación exigente del mismo hecho central.",
    }


def authored_batch() -> dict[str, object]:
    return {
        "schema_version": v13.AUTHORED_SCHEMA,
        "release": 2,
        "batch_id": "r2-author-agent-a-dan1",
        "author": "author-agent-a",
        "source_sha256": "0eea35",
        "questions": [authored_question()],
    }


def approved_review(batch: dict[str, object], packet: dict[str, object]) -> dict[str, object]:
    row = batch["questions"][0]
    decision = {
        "question_id": row["id"],
        "authored_content_sha256": v13.authored_content_hash(row),
        "decision": "approved",
        "adjudicated_option": row["correct_option"],
        "second_defensible_option": False,
        "rationale": "Solo la opción adjudicada coincide con el hecho preguntado.",
        "source_alignment_reason": "La evidencia contiene literalmente la acción sitió.",
    }
    decision["review_sha256"] = v13.review_decision_hash(
        decision,
        reviewer="reviewer-agent-b",
        blind_packet_sha256=packet["packet_sha256"],
    )
    return {
        "schema_version": v13.REVIEW_SCHEMA,
        "blind_batch_id": packet["blind_batch_id"],
        "reviewer": "reviewer-agent-b",
        "blind_packet_sha256": packet["packet_sha256"],
        "decisions": [decision],
    }


class CompetitiveV13Tests(unittest.TestCase):
    def test_blind_cli_refuses_a_binding_key_inside_the_repository(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        forbidden_key = repository / ".work" / "competitive-v13-test.key"
        self.assertFalse(forbidden_key.exists())
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("build-blind-review-packets-v13.py")),
                    "--authored-dir",
                    directory,
                    "--output-dir",
                    str(Path(directory) / "blind"),
                    "--binding-key-file",
                    str(forbidden_key),
                ],
                capture_output=True,
                check=False,
                text=True,
            )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("outside the repository", completed.stderr)
        self.assertFalse(forbidden_key.exists())

    def test_blind_cli_ignores_empty_and_pending_author_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authored = root / "authored"
            sources = root / "sources"
            base = root / "base"
            output = root / "blind"
            reviews = root / "reviews"
            release = root / "release.json"
            binding_key_file = root / "blind-binding.key"
            authored.mkdir()
            sources.mkdir()
            base.mkdir()
            (authored / "empty.json").write_text("[]\n", encoding="utf-8")
            (authored / "rejected.pending.json").write_text(
                json.dumps(authored_batch(), ensure_ascii=False), encoding="utf-8"
            )
            (authored / "ready.json").write_text(
                json.dumps(authored_batch(), ensure_ascii=False), encoding="utf-8"
            )
            (sources / "DAN1.json").write_text(
                json.dumps(
                    {"source_sha256": "0eea35", "units": [SOURCE]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (base / "DAN1.json").write_text(
                json.dumps(
                    [
                        {
                            "fact_id": "DAN1-V001-F04",
                            "source_unit_id": "DAN1-V001",
                            "question": "¿Quién sitió la ciudad de Jerusalén?",
                            "family": "single_choice_direct",
                            "subtype": "factual_recall",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("build-blind-review-packets-v13.py")),
                    "--authored-dir",
                    str(authored),
                    "--source-dir",
                    str(sources),
                    "--base-questions-dir",
                    str(base),
                    "--output-dir",
                    str(output),
                    "--binding-key-file",
                    str(binding_key_file),
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["batches"], 1)
            packet_paths = list(output.glob("blind-*.json"))
            self.assertEqual(len(packet_paths), 1)
            self.assertTrue((output / "packet-set.json").exists())
            packet = json.loads(packet_paths[0].read_text(encoding="utf-8"))
            reviews.mkdir()
            (reviews / packet_paths[0].name).write_text(
                json.dumps(approved_review(authored_batch(), packet), ensure_ascii=False),
                encoding="utf-8",
            )

            apply_command = [
                sys.executable,
                str(Path(__file__).with_name("apply-reviewed-release-v13.py")),
                "--authored-dir",
                str(authored),
                "--source-dir",
                str(sources),
                "--base-questions-dir",
                str(base),
                "--packet-dir",
                str(output),
                "--review-dir",
                str(reviews),
                "--binding-key-file",
                str(binding_key_file),
                "--output",
                str(release),
            ]
            applied = subprocess.run(
                apply_command,
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(json.loads(applied.stdout)["approved"], 1)
            self.assertEqual(len(json.loads(release.read_text(encoding="utf-8"))["approved"]), 1)

            previous_release = release.read_bytes()
            manifest_path = output / "packet-set.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["packets"].append(
                {
                    "blind_batch_id": "blind-extra",
                    "filename": "blind-extra.json",
                    "packet_sha256": "0" * 64,
                }
            )
            payload = {
                key: value
                for key, value in manifest.items()
                if key not in {"set_sha256", "set_hmac_sha256"}
            }
            manifest["set_sha256"] = v13.canonical_hash(payload)
            manifest["set_hmac_sha256"] = v13.keyed_hash(
                payload, binding_key=binding_key_file.read_bytes()
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            rejected_manifest = subprocess.run(
                apply_command,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(rejected_manifest.returncode, 1)
            self.assertIn("exactly match", rejected_manifest.stderr)
            self.assertEqual(release.read_bytes(), previous_release)

    def test_array_input_with_per_row_author_normalizes_to_canonical_envelope(self) -> None:
        row = authored_question()
        row.pop("role")
        row["difficulty"] = "EXPERT"
        row["importance"] = "CRITICAL"
        row["author"] = {"id": "author-agent-a", "model": "gpt-5.6"}

        batch = v13.normalize_authored_input(
            [row], batch_id="raw-dan1", source_sha256="source-hash"
        )

        self.assertEqual(batch["schema_version"], v13.AUTHORED_SCHEMA)
        self.assertEqual(
            batch["author"], {"id": "author-agent-a", "model": "gpt-5.6"}
        )
        self.assertEqual(batch["questions"][0]["role"], "variant")
        self.assertEqual(batch["questions"][0]["difficulty"], "expert")
        self.assertEqual(batch["questions"][0]["importance"], "critical")
        self.assertNotIn("author", batch["questions"][0])
        self.assertEqual(v13.validate_authored_batch(batch, {"DAN1-V001": SOURCE}), [])

    def test_selection_family_normalizes_deterministically_and_bad_text_is_rejected(self) -> None:
        direct = authored_question()
        direct["family"] = "selection"
        direct["subtype"] = "direct"
        direct["author"] = {"id": "a", "model": "m"}
        contextual = authored_question("R2-DAN1-0002")
        contextual["fact_id"] = "DAN1-V001-F05"
        contextual["question"] = "¿Qué relación explica el sitio de Jerusalén?"
        contextual["family"] = "selection"
        contextual["subtype"] = "contextual"
        contextual["author"] = {"id": "a", "model": "m"}

        batch = v13.normalize_authored_input([direct, contextual])

        self.assertEqual(batch["questions"][0]["family"], "single_choice_direct")
        self.assertEqual(batch["questions"][0]["subtype"], "factual_recall")
        self.assertEqual(batch["questions"][1]["family"], "single_choice_contextual")
        self.assertEqual(batch["questions"][1]["subtype"], "relationship")
        batch["questions"][0]["question"] = "Pregunta 12: Elige la correcta �"
        errors = v13.validate_authored_batch(batch, {"DAN1-V001": SOURCE})
        self.assertIn("questions[0].replacement_character", errors)
        self.assertIn("questions[0].generic_prompt_preamble", errors)

    def test_repetitive_editorial_preambles_are_a_batch_gate(self) -> None:
        prompts = [
            f"Examina los detalles y selecciona la respuesta exacta: caso {index}"
            for index in range(4)
        ]
        self.assertEqual(
            v13.repetitive_prompt_preambles(prompts),
            ["examina los detalles y selecciona la respuesta exacta"],
        )

    def test_envelope_upgrades_matching_per_row_author_without_leaking_it_into_rows(self) -> None:
        value = authored_batch()
        value["questions"][0]["author"] = {
            "id": "author-agent-a",
            "model": "gpt-5.6-sol",
        }
        normalized = v13.normalize_authored_input(value)
        self.assertEqual(
            normalized["author"],
            {"id": "author-agent-a", "model": "gpt-5.6-sol"},
        )
        self.assertNotIn("author", normalized["questions"][0])

    def test_missing_evidence_excerpt_is_reported_explicitly(self) -> None:
        batch = authored_batch()
        del batch["questions"][0]["evidence_excerpt"]
        self.assertIn(
            "questions[0].evidence_excerpt: missing",
            v13.validate_authored_batch(batch, {"DAN1-V001": SOURCE}),
        )

    def test_authorship_has_no_embedded_review_and_requires_variant_hard_or_expert(self) -> None:
        batch = authored_batch()
        self.assertEqual(v13.validate_authored_batch(batch, {"DAN1-V001": SOURCE}), [])

        invalid = copy.deepcopy(batch)
        invalid["questions"][0]["review"] = {"reviewer": "same-agent"}
        invalid["questions"][0]["role"] = "central"
        invalid["questions"][0]["difficulty"] = "medium"
        errors = v13.validate_authored_batch(invalid, {"DAN1-V001": SOURCE})
        self.assertIn("questions[0].embedded_review_forbidden", errors)
        self.assertIn("questions[0].role: expected 'variant'", errors)
        self.assertIn("questions[0].difficulty: expected hard or expert", errors)

        mojibake = copy.deepcopy(batch)
        mojibake["questions"][0]["question"] = "RevisiÃ³n del dato bíblico"
        self.assertIn(
            "questions[0].replacement_character",
            v13.validate_authored_batch(mojibake, {"DAN1-V001": SOURCE}),
        )

    def test_source_provenance_must_match_the_loaded_source_hash(self) -> None:
        batch = authored_batch()
        self.assertIn(
            "source_sha256_mismatch",
            v13.validate_authored_batch(
                batch, {"DAN1-V001": SOURCE}, expected_source_sha256="different"
            ),
        )
        self.assertIn(
            "questions[0].fact_source_mismatch",
            v13.validate_authored_batch(
                batch,
                {"DAN1-V001": SOURCE},
                expected_fact_sources={"DAN1-V001-F04": "OTHER-SOURCE"},
            ),
        )

    def test_blind_packet_hides_author_answer_and_explanations_but_keeps_evidence(self) -> None:
        base = [
            {
                "fact_id": "DAN1-V001-F04",
                "source_unit_id": "DAN1-V001",
                "question": "¿Quién sitió Jerusalén?",
                "family": "single_choice_direct",
                "subtype": "factual_recall",
            }
        ]
        packet = v13.build_blind_review_packet(
            authored_batch(),
            {"DAN1-V001": SOURCE},
            binding_key=BINDING_KEY,
            base_questions=base,
        )
        serialized = json.dumps(packet, ensure_ascii=False)

        for secret in (
            "author-agent-a",
            "r2-author-agent-a-dan1",
            "correct_option",
            "accepted_answers",
            "explanation",
            "why_distractors_fail",
        ):
            self.assertNotIn(secret, serialized)
        row = packet["questions"][0]
        self.assertEqual(row["source_quote"], SOURCE["source_quote"])
        self.assertEqual(row["evidence_excerpt"], "a Jerusalén, y la sitió")
        self.assertEqual(row["existing_presentations"][0]["question"], "¿Quién sitió Jerusalén?")
        self.assertEqual(packet["packet_sha256"], v13.blind_packet_hash(packet))

    def test_review_must_be_independent_hashed_unambiguous_and_match_authored_answer(self) -> None:
        batch = authored_batch()
        packet = v13.build_blind_review_packet(
            batch, {"DAN1-V001": SOURCE}, binding_key=BINDING_KEY
        )
        review = approved_review(batch, packet)
        self.assertEqual(
            v13.validate_review(batch, packet, review, binding_key=BINDING_KEY), []
        )

        invalid = copy.deepcopy(review)
        invalid["reviewer"] = batch["author"]
        invalid["decisions"][0]["adjudicated_option"] = 1
        invalid["decisions"][0]["second_defensible_option"] = True
        errors = v13.validate_review(
            batch, packet, invalid, binding_key=BINDING_KEY
        )
        self.assertIn("reviewer_must_differ_from_author", errors)
        self.assertIn("decisions[0].adjudicated_option_mismatch", errors)
        self.assertIn("decisions[0].second_defensible_option: expected false", errors)
        self.assertIn("decisions[0].review_sha256_mismatch", errors)

        swapped_reviewer = copy.deepcopy(review)
        swapped_reviewer["reviewer"] = "reviewer-agent-c"
        self.assertIn(
            "decisions[0].review_sha256_mismatch",
            v13.validate_review(
                batch, packet, swapped_reviewer, binding_key=BINDING_KEY
            ),
        )

        swapped_author = copy.deepcopy(batch)
        swapped_author["author"] = "reviewer-agent-b"
        self.assertIn(
            "blind_batch_authorship_binding_mismatch",
            v13.validate_review(
                swapped_author, packet, review, binding_key=BINDING_KEY
            ),
        )

    def test_only_approved_rows_compile_and_rejections_remain_pending_without_blind_data(self) -> None:
        batch = authored_batch()
        batch["questions"].append(authored_question("R2-DAN1-0002"))
        batch["questions"][1]["fact_id"] = "DAN1-V001-F05"
        batch["questions"][1]["question"] = "¿Qué hizo el monarca frente a la ciudad de Jerusalén?"
        packet = v13.build_blind_review_packet(
            batch, {"DAN1-V001": SOURCE}, binding_key=BINDING_KEY
        )
        review = approved_review(batch, packet)
        rejected = {
            "question_id": "R2-DAN1-0002",
            "authored_content_sha256": v13.authored_content_hash(batch["questions"][1]),
            "decision": "rejected",
            "adjudicated_option": 0,
            "second_defensible_option": False,
            "rationale": "La formulación no alcanza el estándar competitivo.",
            "source_alignment_reason": "La respuesta sí tiene apoyo, pero el ítem es débil.",
        }
        rejected["review_sha256"] = v13.review_decision_hash(
            rejected,
            reviewer=review["reviewer"],
            blind_packet_sha256=packet["packet_sha256"],
        )
        review["decisions"].append(rejected)

        result = v13.compile_reviewed_batch(
            batch,
            packet,
            review,
            {"DAN1-V001": SOURCE},
            binding_key=BINDING_KEY,
        )
        self.assertEqual([row["id"] for row in result["approved"]], ["R2-DAN1-0001"])
        self.assertEqual(result["pending"][0]["question_id"], "R2-DAN1-0002")
        public = json.dumps(result["approved"], ensure_ascii=False)
        self.assertNotIn("blind_packet", public)
        self.assertNotIn("blind_pool", public)
        self.assertEqual(result["approved"][0]["ai_review"]["reviewer"], "reviewer-agent-b")

    def test_atomic_writer_preserves_previous_output_on_validation_failure(self) -> None:
        batch = authored_batch()
        packet = v13.build_blind_review_packet(
            batch, {"DAN1-V001": SOURCE}, binding_key=BINDING_KEY
        )
        review = approved_review(batch, packet)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release.json"
            output.write_text('{"previous": true}\n', encoding="utf-8")
            bad_review = copy.deepcopy(review)
            bad_review["decisions"][0]["review_sha256"] = "tampered"
            with self.assertRaises(v13.ContractError):
                v13.apply_reviewed_release_atomic(
                    [(batch, packet, bad_review)],
                    {"DAN1-V001": SOURCE},
                    output,
                    binding_key=BINDING_KEY,
                )
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"previous": True})

    def test_increment_rejects_duplicate_fact_ids_across_batches(self) -> None:
        first = authored_batch()
        second = copy.deepcopy(first)
        second["batch_id"] = "r2-dan1-c"
        second["author"] = "author-agent-c"
        second["questions"][0]["id"] = "R2-DAN1-0002"
        second["questions"][0]["question"] = "¿Cuál fue la acción bélica contra Jerusalén?"
        base = [
            {
                "id": "CENTRAL",
                "fact_id": "DAN1-V001-F04",
                "source_unit_id": "DAN1-V001",
                "question": "¿Quién puso sitio a Jerusalén?",
                "family": "single_choice_direct",
                "subtype": "factual_recall",
            }
        ]
        first_packet = v13.build_blind_review_packet(
            first,
            {"DAN1-V001": SOURCE},
            binding_key=BINDING_KEY,
            base_questions=base,
        )
        second_packet = v13.build_blind_review_packet(
            second,
            {"DAN1-V001": SOURCE},
            binding_key=BINDING_KEY,
            base_questions=base,
        )
        first_review = approved_review(first, first_packet)
        second_review = approved_review(second, second_packet)

        with self.assertRaisesRegex(v13.ContractError, "duplicate Release 2 fact_ids"):
            v13.apply_reviewed_release_atomic(
                [
                    (first, first_packet, first_review),
                    (second, second_packet, second_review),
                ],
                {"DAN1-V001": SOURCE},
                Path("unused.json"),
                binding_key=BINDING_KEY,
                base_questions=base,
            )

    def test_existing_prompt_reuse_is_rejected_before_blind_review(self) -> None:
        batch = authored_batch()
        existing = {
            "id": "EXISTING",
            "fact_id": "DAN1-V001-F04",
            "source_unit_id": "DAN1-V001",
            "question": batch["questions"][0]["question"],
        }
        with self.assertRaisesRegex(v13.ContractError, "existing_prompt_reused"):
            v13.build_blind_review_packet(
                batch,
                {"DAN1-V001": SOURCE},
                binding_key=BINDING_KEY,
                base_questions=[existing],
            )


if __name__ == "__main__":
    unittest.main()
