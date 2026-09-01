from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from scripts.lib.competitive_v13 import canonical_hash


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promote-reviewed-release-v13.py"
BASE_ROOT = ROOT / "content" / "competitive-v11"
CHECKPOINT = (
    ROOT
    / "content"
    / "competitive-v13"
    / "release2"
    / "applied"
    / "release2-reviewed-current.json"
)


def load_promoter():
    spec = importlib.util.spec_from_file_location("promote_reviewed_release_v13", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load promoter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resign(checkpoint: dict) -> dict:
    checkpoint["release_sha256"] = canonical_hash(
        {key: value for key, value in checkpoint.items() if key != "release_sha256"}
    )
    return checkpoint


class PromoteReviewedReleaseV13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.promoter = load_promoter()
        cls.checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))

    def test_promotes_real_checkpoint_without_blind_or_base_loss(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "public-bank"
            manifest = self.promoter.promote_release(
                BASE_ROOT,
                copy.deepcopy(self.checkpoint),
                output,
            )

            self.assertEqual(manifest["gold_questions"], 2730)
            self.assertEqual(manifest["unique_facts"], 2217)
            self.assertEqual(manifest["central_question_count"], 2217)
            self.assertEqual(manifest["presentation_variant_count"], 513)
            self.assertEqual(manifest["blind_fact_count"], 0)
            self.assertEqual(manifest["blind_presentation_count"], 0)
            self.assertEqual(
                manifest["families"],
                {
                    "single_choice_direct": 451,
                    "single_choice_contextual": 919,
                    "fill_choice": 747,
                    "true_false": 613,
                },
            )
            emitted = []
            for shard in manifest["shards"]:
                shard_path = output / "questions" / f"{shard['chapter']}.json"
                emitted.extend(json.loads(shard_path.read_text(encoding="utf-8")))
            self.assertEqual(len(emitted), 2730)
            self.assertEqual(sum(row["role"] == "variant" for row in emitted), 513)
            self.assertTrue(all(row["blind_pool"] is None for row in emitted))
            self.assertTrue(
                {row["id"] for row in self.checkpoint["approved"]}
                <= {row["id"] for row in emitted}
            )

    def test_rejects_tampered_release_hash(self) -> None:
        checkpoint = copy.deepcopy(self.checkpoint)
        checkpoint["approved"][0]["question"] += " alterada"

        with self.assertRaisesRegex(self.promoter.PromotionError, "release_sha256"):
            self.promoter.prepare_promotion(BASE_ROOT, checkpoint)

    def test_rejects_question_id_collision_with_base(self) -> None:
        checkpoint = copy.deepcopy(self.checkpoint)
        base = json.loads((BASE_ROOT / "questions" / "DAN1.json").read_text(encoding="utf-8"))
        checkpoint["approved"][0]["id"] = base[0]["id"]
        resign(checkpoint)

        with self.assertRaisesRegex(self.promoter.PromotionError, "question id collision"):
            self.promoter.prepare_promotion(BASE_ROOT, checkpoint)

    def test_rejects_fact_source_mismatch(self) -> None:
        checkpoint = copy.deepcopy(self.checkpoint)
        checkpoint["approved"][0]["source_unit_id"] = "DAN2-V001"
        resign(checkpoint)

        with self.assertRaisesRegex(self.promoter.PromotionError, "fact/source mismatch"):
            self.promoter.prepare_promotion(BASE_ROOT, checkpoint)

    def test_rejects_batch_totals_that_do_not_bind_checkpoint_rows(self) -> None:
        checkpoint = copy.deepcopy(self.checkpoint)
        checkpoint["batches"][0]["approved"] += 1
        resign(checkpoint)

        with self.assertRaisesRegex(self.promoter.PromotionError, "batch approved total"):
            self.promoter.prepare_promotion(BASE_ROOT, checkpoint)

    def test_rejects_output_that_overlaps_canonical_base(self) -> None:
        with self.assertRaisesRegex(self.promoter.PromotionError, "must not overlap"):
            self.promoter.validate_promotion_paths(
                BASE_ROOT,
                BASE_ROOT / "questions",
            )


if __name__ == "__main__":
    unittest.main()
