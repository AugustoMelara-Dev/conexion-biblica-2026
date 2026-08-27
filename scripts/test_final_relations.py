from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "public/banks/final-2026/source_inventory.json"


class FinalRelationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        cls.units = {
            unit["source_unit_id"]: unit for unit in cls.inventory["units"]
        }
        try:
            cls.relations = importlib.import_module("scripts.lib.final_relations")
        except ModuleNotFoundError:
            cls.relations = None

    def require_relations(self):
        self.assertIsNotNone(
            self.relations, "falta scripts.lib.final_relations"
        )
        return self.relations

    def extract(self, source_unit_id: str) -> list[dict[str, object]]:
        relations = self.require_relations()
        if relations is None:
            return []
        return relations.extract_relation_candidates(self.units[source_unit_id])

    def test_extracts_explicit_consequence_without_swallowing_the_whole_verse(self) -> None:
        candidates = self.extract("DAN9-V011")
        consequence = next(
            row for row in candidates if row["relation_type"] == "consequence"
        )
        self.assertEqual(consequence["answer"], "la maldición y el juramento")
        self.assertIn("traspasó", consequence["question"].casefold())
        self.assertIn(consequence["answer"], consequence["source_quote"])
        self.assertLessEqual(len(str(consequence["answer"]).split()), 8)

    def test_extracts_explicit_declared_purpose(self) -> None:
        candidates = self.extract("DAN7-V026")
        purpose = next(row for row in candidates if row["relation_type"] == "purpose")
        self.assertEqual(purpose["answer"], "destruido y arruinado hasta el fin")
        self.assertIn("propósito", purpose["question"].casefold())
        self.assertIn(purpose["answer"], purpose["source_quote"])

    def test_extracts_explicit_speaker_and_recipient_from_dialogue(self) -> None:
        candidates = self.extract("DAN3-V026")
        by_type = {row["relation_type"]: row for row in candidates}
        self.assertEqual(by_type["speaker"]["answer"], "Nabucodonosor")
        self.assertEqual(
            by_type["recipient"]["answer"],
            "Sadrac, Mesac y Abed-nego, siervos del Dios Altísimo",
        )
        self.assertIn("salid y venid", by_type["speaker"]["question"].casefold())

    def test_does_not_invent_a_relation_from_an_unrelated_narrative_verse(self) -> None:
        candidates = self.extract("DAN7-V001")
        self.assertFalse(candidates)

    def test_sentence_initial_then_is_not_itself_a_consequence(self) -> None:
        candidates = self.extract("DAN3-V026")
        self.assertFalse(
            any(
                row["relation_type"] in {"cause", "consequence", "sequence"}
                and str(row["answer"]).casefold() == "entonces"
                for row in candidates
            )
        )

    def test_every_relation_is_explicit_unique_and_competition_worthy(self) -> None:
        relations = self.require_relations()
        if relations is None:
            return
        for unit in self.inventory["units"]:
            for candidate in relations.extract_relation_candidates(unit):
                answer = str(candidate["answer"])
                quote = str(candidate["source_quote"])
                self.assertEqual(quote.count(answer), 1, unit["source_unit_id"])
                self.assertTrue(1 <= len(answer.split()) <= 8, unit["source_unit_id"])
                self.assertNotEqual(answer.casefold(), "entonces")
                self.assertNotRegex(
                    answer,
                    r"^(?:Daniel \d+:\d+|PR\d+, p\. \d+)",
                    unit["source_unit_id"],
                )
                self.assertIn(str(unit["reference"]), str(candidate["question"]))

    def test_repeated_connectors_receive_distinct_context_anchors(self) -> None:
        candidates = self.extract("PR40-P036-P003-S002")
        purposes = [row for row in candidates if row["relation_type"] == "purpose"]
        self.assertEqual(len(purposes), 2)
        self.assertEqual(len({row["question"] for row in purposes}), 2)
        self.assertTrue(all("afirmación" in row["question"] for row in purposes))

    def test_generic_relations_never_truncate_an_answer_at_a_connector(self) -> None:
        dangling = {
            "a", "al", "con", "contra", "de", "del", "en", "entre",
            "hacia", "hasta", "para", "por", "que", "sin", "sobre", "y", "o",
        }
        for unit in self.inventory["units"]:
            for candidate in self.extract(unit["source_unit_id"]):
                last_word = str(candidate["answer"]).casefold().split()[-1]
                self.assertNotIn(last_word, dangling, candidate)
        self.assertFalse(
            any(
                row["answer"] == "al fin de ellos se presentarán delante del"
                for row in self.extract("DAN1-V005")
            )
        )


if __name__ == "__main__":
    unittest.main()
