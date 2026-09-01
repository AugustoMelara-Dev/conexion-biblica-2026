import json
import pathlib
import unittest
from collections import Counter
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

class AntiSimulationInvariantsTest(unittest.TestCase):
    """Rigorous gate preventing simulated reviews and editorial contract violations."""

    def test_no_constant_adjudication_in_reviews(self):
        """Review packets must not have constant adjudicated_option across all questions."""
        reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
        if not reviews_dir.exists() or not list(reviews_dir.glob("blind-*.json")):
            self.skipTest("No staging reviews to check yet.")
        for rf in reviews_dir.glob("blind-*.json"):
            data = json.loads(rf.read_text(encoding="utf-8"))
            decisions = data.get("decisions", [])
            options = [d["adjudicated_option"] for d in decisions if "adjudicated_option" in d]
            if len(options) >= 5:
                # Check that not all options are the same index
                self.assertGreater(
                    len(set(options)), 1,
                    f"Violation: {rf.name} has constant adjudicated_option across all questions: {set(options)}"
                )

    def test_no_identical_rationales_in_reviews(self):
        """Rationales must be unique and specific to each question."""
        reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
        if not reviews_dir.exists() or not list(reviews_dir.glob("blind-*.json")):
            self.skipTest("No staging reviews to check yet.")
        for rf in reviews_dir.glob("blind-*.json"):
            data = json.loads(rf.read_text(encoding="utf-8"))
            decisions = data.get("decisions", [])
            rationales = [d["rationale"].strip() for d in decisions if "rationale" in d]
            self.assertEqual(
                len(rationales), len(set(rationales)),
                f"Violation: {rf.name} has duplicate/identical review rationales."
            )

    def test_blind_packets_omit_forbidden_author_fields(self):
        """Blind review packets must never contain correct_option, accepted_answers, etc."""
        packets_dir = ROOT / "content" / "competitive-v13" / "staging-blind-packets"
        forbidden = {
            "correct_option", "accepted_answers", "explanation", "why_distractors_fail",
            "variant_justification", "significance", "author"
        }
        for pf in packets_dir.glob("blind-*.json"):
            data = json.loads(pf.read_text(encoding="utf-8"))
            for q in data.get("questions", []):
                for f in forbidden:
                    self.assertNotIn(
                        f, q,
                        f"Leak violation: Blind packet {pf.name} question {q.get('id')} contains forbidden field {f}."
                    )

    def test_authored_position_balance(self):
        """Authored batches must not place all correct options in position 0."""
        staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
        for bf in staging_dir.glob("*.json"):
            data = json.loads(bf.read_text(encoding="utf-8"))
            positions = [q["correct_option"] for q in data]
            self.assertGreater(
                len(set(positions)), 1,
                f"Position imbalance violation: {bf.name} has all correct options at index {positions[0]}."
            )

    def test_no_unsupported_external_theology_in_staging(self):
        """Explanations must not introduce external doctrinal claims outside PDF."""
        staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
        banned_phrases = [
            "roma imperial y papal",
            "juicio investigador",
            "lidia, babilonia, egipto",
            "tumba sellada de cristo",
            "2,300 tardes y mañanas/años"
        ]
        for bf in staging_dir.glob("*.json"):
            data = json.loads(bf.read_text(encoding="utf-8"))
            for q in data:
                sig = q.get("significance") or ""
                exp = q.get("explanation") or ""
                text = (exp + " " + sig).lower()
                for phrase in banned_phrases:
                    self.assertNotIn(
                        phrase, text,
                        f"External theology violation in {bf.name} {q.get('id')}: found '{phrase}'"
                    )

    def test_provenance_requires_real_model_conversation_id(self):
        """Reviews must preserve genuine conversation IDs and model provenance."""
        reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
        if not reviews_dir.exists() or not list(reviews_dir.glob("blind-*.json")):
            self.skipTest("No staging reviews to check yet.")
        for rf in reviews_dir.glob("blind-*.json"):
            data = json.loads(rf.read_text(encoding="utf-8"))
            reviewer = data.get("reviewer", {})
            self.assertIn("conversation_id", reviewer, f"Missing conversation_id in {rf.name}")
            cid = reviewer["conversation_id"]
            self.assertTrue(
                len(cid) >= 10,
                f"Invalid conversation_id in {rf.name}: '{cid}'"
            )

if __name__ == "__main__":
    unittest.main()
