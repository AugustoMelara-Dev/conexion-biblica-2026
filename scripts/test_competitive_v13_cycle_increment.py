from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib import competitive_v13 as v13


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build-blind-review-cycle-v13.py"
APPLY_SCRIPT = ROOT / "scripts" / "apply-reviewed-cycle-v13.py"

SOURCE = {
    "source_unit_id": "DAN1-V001",
    "source_ref": "Daniel 1:1",
    "source_quote": (
        "En el tercer año del reinado de Joacim, rey de Judá, vino "
        "Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió."
    ),
    "parent_context": None,
}
SOURCE_HASH = "cycle-11-source-hash"
KEY = b"cycle-11-independent-binding-key!!"


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checkpoint_with_262() -> dict:
    approved = [
        {
            "id": f"BASE-APPROVED-{index:03d}",
            "source_unit_id": "DAN1-V001",
            "fact_id": f"DAN1-V001-OLD-F{index:03d}",
            "question": f"Presentación histórica aprobada {index}",
        }
        for index in range(262)
    ]
    value = {
        "schema_version": v13.APPLIED_SCHEMA,
        "release": 2,
        "batches": [
            {
                "batch_id": "historical",
                "blind_packet_sha256": "a" * 64,
                "reviewer": "historical-reviewer",
                "approved": 262,
                "pending": 0,
            }
        ],
        "approved": approved,
        "pending": [],
    }
    value["release_sha256"] = v13.canonical_hash(value)
    return value


def authored_cycle11() -> dict:
    return {
        "schema_version": v13.AUTHORED_SCHEMA,
        "release": 2,
        "batch_id": "DAN1-cycle11",
        "author": "cycle11-author",
        "source_sha256": SOURCE_HASH,
        "questions": [
            {
                "id": "R2-C11-DAN1-001",
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
        ],
    }


def incremental_checkpoint() -> dict:
    value = {
        "schema_version": v13.APPLIED_SCHEMA,
        "release": 2,
        "batches": [
            {
                "batch_id": "DAN1-cycle11",
                "blind_packet_sha256": "b" * 64,
                "reviewer": "cycle11-reviewer",
                "approved": 1,
                "pending": 0,
            }
        ],
        "approved": [
            {
                "id": "R2-C11-DAN1-001",
                "source_unit_id": "DAN1-V001",
                "fact_id": "DAN1-V001-F04",
                "question": "¿Qué acción militar realizó el rey al llegar a Jerusalén?",
            }
        ],
        "pending": [],
    }
    value["release_sha256"] = v13.canonical_hash(value)
    return value


class CompetitiveV13CycleIncrementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_script(BUILD_SCRIPT, "build_blind_review_cycle_v13")
        cls.applier = load_script(APPLY_SCRIPT, "apply_reviewed_cycle_v13")

    def test_builder_packages_only_cycle11_against_immutable_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authored = root / "authored"
            sources = root / "sources"
            base = root / "base"
            output = root / "blind-cycle11"
            authored.mkdir()
            sources.mkdir()
            base.mkdir()
            (authored / "DAN1-cycle11.json").write_text(
                json.dumps(authored_cycle11(), ensure_ascii=False), encoding="utf-8"
            )
            (authored / "DAN2-cycle10.json").write_text("{", encoding="utf-8")
            (sources / "DAN1.json").write_text(
                json.dumps({"source_sha256": SOURCE_HASH, "units": [SOURCE]}),
                encoding="utf-8",
            )
            (base / "DAN1.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "CENTRAL",
                            "source_unit_id": "DAN1-V001",
                            "fact_id": "DAN1-V001-F04",
                            "question": "¿Quién puso sitio a Jerusalén?",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manifest = self.builder.build_cycle_packets(
                authored,
                sources,
                base,
                checkpoint_with_262(),
                output,
                KEY,
                cycle=11,
            )

            self.assertEqual(manifest["cycle"], 11)
            self.assertEqual(manifest["base_approved_count"], 262)
            self.assertEqual(len(manifest["packets"]), 1)
            packet = json.loads(
                (output / manifest["packets"][0]["filename"]).read_text(encoding="utf-8")
            )
            self.assertEqual(packet["questions"][0]["id"], "R2-C11-DAN1-001")
            self.assertNotIn("cycle11-author", json.dumps(packet, ensure_ascii=False))

    def test_merge_preserves_prior_checkpoint_and_is_deterministic(self) -> None:
        prior = checkpoint_with_262()
        frozen = copy.deepcopy(prior)
        increment = incremental_checkpoint()

        first = self.applier.merge_checkpoints(prior, increment, cycle=11)
        second = self.applier.merge_checkpoints(prior, increment, cycle=11)

        self.assertEqual(prior, frozen)
        self.assertEqual(first, second)
        self.assertEqual(first["approved"][:262], frozen["approved"])
        self.assertEqual(len(first["approved"]), 263)
        self.assertEqual(first["batches"][:1], frozen["batches"])
        self.assertEqual(
            first["cycle_history"],
            [
                {
                    "cycle": 11,
                    "base_release_sha256": frozen["release_sha256"],
                    "increment_release_sha256": increment["release_sha256"],
                    "base_approved_count": 262,
                    "new_approved_count": 1,
                    "merged_approved_count": 263,
                }
            ],
        )
        self.assertEqual(
            first["release_sha256"],
            v13.canonical_hash(
                {key: value for key, value in first.items() if key != "release_sha256"}
            ),
        )

    def test_apply_cycle_compiles_increment_before_append_only_merge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authored = root / "authored"
            sources = root / "sources"
            base = root / "base"
            packets = root / "packets"
            reviews = root / "reviews"
            output = root / "merged.json"
            for path in (authored, sources, base, reviews):
                path.mkdir()
            batch = authored_cycle11()
            (authored / "DAN1-cycle11.json").write_text(
                json.dumps(batch, ensure_ascii=False), encoding="utf-8"
            )
            (sources / "DAN1.json").write_text(
                json.dumps({"source_sha256": SOURCE_HASH, "units": [SOURCE]}),
                encoding="utf-8",
            )
            (base / "DAN1.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "CENTRAL",
                            "source_unit_id": "DAN1-V001",
                            "fact_id": "DAN1-V001-F04",
                            "question": "¿Quién puso sitio a Jerusalén?",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            prior = checkpoint_with_262()
            manifest = self.builder.build_cycle_packets(
                authored, sources, base, prior, packets, KEY, cycle=11
            )
            packet = json.loads(
                (packets / manifest["packets"][0]["filename"]).read_text(encoding="utf-8")
            )
            authored_row = batch["questions"][0]
            decision = {
                "question_id": authored_row["id"],
                "authored_content_sha256": v13.authored_content_hash(authored_row),
                "decision": "approved",
                "adjudicated_option": 0,
                "second_defensible_option": False,
                "rationale": "La pregunta conserva una sola respuesta defendible.",
                "source_alignment_reason": "La acción está explícita en la cita.",
            }
            decision["review_sha256"] = v13.review_decision_hash(
                decision,
                reviewer="cycle11-reviewer",
                blind_packet_sha256=packet["packet_sha256"],
            )
            review = {
                "schema_version": v13.REVIEW_SCHEMA,
                "blind_batch_id": packet["blind_batch_id"],
                "reviewer": "cycle11-reviewer",
                "blind_packet_sha256": packet["packet_sha256"],
                "decisions": [decision],
            }
            (reviews / f"{packet['blind_batch_id']}.json").write_text(
                json.dumps(review, ensure_ascii=False), encoding="utf-8"
            )

            merged = self.applier.apply_cycle_reviews(
                authored,
                packets,
                reviews,
                sources,
                base,
                prior,
                output,
                KEY,
                cycle=11,
            )

            self.assertEqual(len(merged["approved"]), 263)
            self.assertEqual(merged["approved"][:262], prior["approved"])
            self.assertEqual(merged["approved"][-1]["id"], "R2-C11-DAN1-001")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), merged)

    def test_merge_rejects_duplicate_fact_already_approved(self) -> None:
        prior = checkpoint_with_262()
        increment = incremental_checkpoint()
        increment["approved"][0]["fact_id"] = prior["approved"][0]["fact_id"]
        increment["release_sha256"] = v13.canonical_hash(
            {key: value for key, value in increment.items() if key != "release_sha256"}
        )

        with self.assertRaisesRegex(self.applier.CycleError, "fact_id already approved"):
            self.applier.merge_checkpoints(prior, increment, cycle=11)

    def test_merge_rejects_tampered_prior_checkpoint(self) -> None:
        prior = checkpoint_with_262()
        prior["approved"][0]["question"] = "alterada"

        with self.assertRaisesRegex(self.applier.CycleError, "release_sha256"):
            self.applier.merge_checkpoints(prior, incremental_checkpoint(), cycle=11)

    def test_builder_rejects_non_integer_checkpoint_batch_totals(self) -> None:
        prior = checkpoint_with_262()
        prior["batches"][0]["approved"] = "262"
        prior["release_sha256"] = v13.canonical_hash(
            {key: value for key, value in prior.items() if key != "release_sha256"}
        )

        with self.assertRaisesRegex(self.builder.CycleError, "batch totals"):
            self.builder.validate_prior_checkpoint(prior)


if __name__ == "__main__":
    unittest.main()
