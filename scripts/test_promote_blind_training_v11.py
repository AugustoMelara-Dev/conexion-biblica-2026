from __future__ import annotations

from contextlib import contextmanager
import copy
import importlib.util
from operator import itemgetter
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promote-blind-to-training-v11.py"
TEST_TEMP_PARENT = os.environ.get("CONEXION_TEST_TMPDIR")

spec = importlib.util.spec_from_file_location("scripts.promote_blind_to_training_v11", SCRIPT)
if spec is None or spec.loader is None:
    raise ImportError(f"no se pudo cargar {SCRIPT}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
promote = module.promote
assert_authored_safe = module.assert_authored_safe


@contextmanager
def temporary_directory():
    parent = Path(TEST_TEMP_PARENT or tempfile.gettempdir())
    path = parent / f"conexion-promote-blind-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def content_hash(row: dict) -> str:
    canonical = {
        key: value
        for key, value in row.items()
        if key not in {"ai_review", "content_sha256"}
    }
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def question(question_id: str, fact_id: str, pool: str, family: str) -> dict:
    return {
        "id": question_id,
        "source_unit_id": "DAN1-V001",
        "fact_id": fact_id,
        "role": "central",
        "family": family,
        "material": "Daniel",
        "chapter": 1,
        "question": f"Pregunta inmutable {question_id}",
        "options": ["a", "b", "c", "d"],
        "correct_option": 0,
        "correct_answer": "a",
        "explanation": "Prosa que no debe reescribirse.",
        "blind_pool": pool,
        "ai_review": {
            "status": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": "pre-promotion",
        },
    }


class PromotionFixture:
    def __init__(self, root: Path) -> None:
        self.content_root = root / "content" / "competitive-v11"
        self.assignment = root / "assignment.json"
        self.registry = self.content_root / "promoted.json"
        rows = [
            question("Q-A", "F-A", "A", "single_choice_direct"),
            question("Q-B", "F-B", "B", "fill_choice"),
            question("Q-E", "F-E", "emergency", "true_false"),
        ]
        write_json(self.content_root / "questions" / "DAN1.json", rows)
        write_json(
            self.content_root / "reviews" / "DAN1.json",
            [
                {"question_id": row["id"], "content_sha256": content_hash(row), "decision": "passed"}
                for row in rows
            ],
        )
        write_json(
            self.content_root / "authored-batches" / "tracked.json",
            [
                {
                    "id": row["id"],
                    "fact_id": row["fact_id"],
                    "question": row["question"],
                    "blind_pool": row["blind_pool"],
                }
                for row in rows
            ],
        )
        write_json(
            self.assignment,
            {
                "schema_version": "1.0",
                "pools": {"A": ["Q-A"], "B": ["Q-B"], "emergency": ["Q-E"]},
            },
        )

    def all_questions(self) -> list[dict]:
        return [
            row
            for path in sorted((self.content_root / "questions").glob("*.json"))
            for row in read_json(path)
        ]

    def snapshot_bytes(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.content_root).as_posix(): path.read_bytes()
            for path in sorted(self.content_root.rglob("*.json"))
        }


def load_questions(path: Path) -> list[dict]:
    return [row for file in sorted(path.glob("*.json")) for row in read_json(file)]


class PromoteBlindTrainingTests(unittest.TestCase):
    def test_authored_safety_accepts_checked_in_relative_paths(self) -> None:
        relative = Path("content/competitive-v11/authored-batches/blind-approved-a-PR41.json")
        rows = read_json(ROOT / relative)

        assert_authored_safe(relative, rows, Path("content/competitive-v11"))

    def test_promotes_exact_assignment_without_deleting_or_rewriting_prose(self) -> None:
        with temporary_directory() as temporary:
            fixture = PromotionFixture(temporary)
            before = fixture.all_questions()

            report = promote(fixture.content_root, fixture.assignment, fixture.registry)

            after = fixture.all_questions()
            self.assertEqual(set(map(itemgetter("id"), after)), set(map(itemgetter("id"), before)))
            self.assertEqual(len(after), len(before))
            self.assertEqual(report["promoted_presentations"], 3)
            self.assertTrue(all(row["blind_pool"] is None for row in after))
            self.assertEqual(
                [{k: row[k] for k in row if k not in {"blind_pool", "ai_review"}} for row in after],
                [{k: row[k] for k in row if k not in {"blind_pool", "ai_review"}} for row in before],
            )
            authored = read_json(fixture.content_root / "authored-batches" / "tracked.json")
            self.assertTrue(all("blind_pool" not in row for row in authored))

    def test_second_promotion_is_a_byte_identical_noop(self) -> None:
        with temporary_directory() as temporary:
            fixture = PromotionFixture(temporary)
            promote(fixture.content_root, fixture.assignment, fixture.registry)
            first = fixture.snapshot_bytes()

            promote(fixture.content_root, fixture.assignment, fixture.registry)

            self.assertEqual(fixture.snapshot_bytes(), first)

    def test_replace_failure_rolls_back_every_file_byte_identically(self) -> None:
        with temporary_directory() as temporary:
            fixture = PromotionFixture(temporary)
            before = fixture.snapshot_bytes()
            real_replace = os.replace
            payload_replacements = 0

            def fail_second_payload_replace(source, destination):
                nonlocal payload_replacements
                if str(source).endswith(".promotion.tmp"):
                    payload_replacements += 1
                    if payload_replacements == 2:
                        raise OSError("injected replacement failure")
                return real_replace(source, destination)

            with patch.object(module.os, "replace", side_effect=fail_second_payload_replace):
                with self.assertRaisesRegex(OSError, "injected replacement failure"):
                    promote(fixture.content_root, fixture.assignment, fixture.registry)

            self.assertEqual(fixture.snapshot_bytes(), before)
            self.assertEqual(list(fixture.content_root.rglob("*.promotion.*")), [])

    def test_checked_in_promotion_exposes_all_v10_facts(self) -> None:
        rows = load_questions(ROOT / "content" / "competitive-v11" / "questions")
        registry = read_json(ROOT / "content" / "competitive-v11" / "promoted-blind-v10.json")
        self.assertEqual(len(registry["presentations"]), 250)
        self.assertEqual(len({row["fact_id"] for row in registry["presentations"]}), 250)
        self.assertEqual(len(rows), 2468)
        self.assertEqual(len({row["fact_id"] for row in rows}), 2217)
        self.assertTrue(all(row["blind_pool"] is None for row in rows))


if __name__ == "__main__":
    unittest.main()
