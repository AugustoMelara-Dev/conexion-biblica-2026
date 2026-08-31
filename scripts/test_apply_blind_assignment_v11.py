from __future__ import annotations

import copy
from contextlib import contextmanager
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply_blind_assignment_v11.py"
CHECKED_MANIFEST = ROOT / "content" / "competitive-v11" / "blind-assignment-v11.json"
TEST_TEMP_PARENT = os.environ.get("CONEXION_TEST_TMPDIR")


@contextmanager
def temporary_directory():
    parent = Path(TEST_TEMP_PARENT or tempfile.gettempdir())
    path = parent / f"conexion-blind-assignment-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def compact_rows(rows: list[dict]) -> str:
    body = ",\n".join(
        "  " + json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        for row in rows
    )
    return f"[\n{body}\n]\n"


def content_hash(row: dict) -> str:
    canonical = {
        key: value
        for key, value in row.items()
        if key not in {"ai_review", "content_sha256"}
    }
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def question(question_id: str, fact_id: str, family: str, correct_option: int = 0) -> dict:
    return {
        "id": question_id,
        "source_unit_id": "DAN1-V001",
        "fact_id": fact_id,
        "role": "central",
        "family": family,
        "subtype": "factual_recall",
        "question": f"Pregunta {question_id}",
        "options": ["Verdadero", "Falso"] if family == "true_false" else ["a", "b", "c", "d"],
        "correct_option": correct_option,
        "correct_answer": ("Verdadero" if correct_option == 0 else "Falso") if family == "true_false" else "abcd"[correct_option],
        "accepted_answers": ["respuesta"],
        "explanation": "Explicación",
        "why_distractors_fail": {"distractor": "razón"},
        "source_ref": "Daniel 1:1",
        "source_quote": "Fuente",
        "evidence_excerpt": "Fuente",
        "difficulty": "hard",
        "importance": "critical",
        "relation_type": "event_action",
        "option_category": "action",
        "false_mutation": None,
        "blank_span": None,
        "significance": None,
        "variant_justification": None,
        "blind_pool": None,
        "ai_review": {"status": "passed", "reviewer_type": "ai_semantic_audit", "reviewer": "test"},
    }


class BlindAssignmentFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.content_root = root / "content" / "competitive-v11"
        self.manifest = root / "assignment.json"
        rows = [
            question("Q-A", "F-A", "single_choice_direct"),
            question("Q-B", "F-B", "fill_choice"),
            question("Q-E", "F-E", "true_false", correct_option=1),
        ]
        write_json(self.content_root / "questions" / "DAN1.json", rows)
        write_json(
            self.content_root / "reviews" / "DAN1.json",
            [
                {"question_id": row["id"], "content_sha256": content_hash(row), "decision": "passed"}
                for row in rows
            ],
        )
        authored_rows = [
            {"id": row["id"], "family": row["family"], "correct_option": row["correct_option"]}
            for row in rows
        ]
        compact_path = self.content_root / "authored-batches" / "tracked-compact.json"
        compact_path.parent.mkdir(parents=True, exist_ok=True)
        compact_path.write_text(compact_rows(authored_rows[:1]), encoding="utf-8")
        write_json(
            self.content_root / "authored-batches" / "tracked-pretty.json",
            authored_rows[1:],
        )
        write_json(
            self.content_root / "authored-batches" / "wave-blind-draft.json",
            [{"id": "Q-A", "blind_pool": "emergency"}],
        )
        write_json(
            self.manifest,
            {
                "schema_version": "1.0",
                "assignment_id": "test",
                "pools": {"A": ["Q-A"], "B": ["Q-B"], "emergency": ["Q-E"]},
                "requirements": {
                    "A": {"count": 1, "families": {"selection": 1, "fill_choice": 0, "true_false": 0}},
                    "B": {"count": 1, "families": {"selection": 0, "fill_choice": 1, "true_false": 0}},
                    "emergency": {"count": 1, "families": {"selection": 0, "fill_choice": 0, "true_false": 1}},
                },
                "excluded_authored_batch_globs": ["wave-blind-*.json"],
            },
        )

    def run(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--manifest",
                str(self.manifest),
                "--content-root",
                str(self.content_root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )


class ApplyBlindAssignmentTests(unittest.TestCase):
    def test_applies_only_blind_pool_and_review_hash_and_updates_authored_origin(self) -> None:
        with temporary_directory() as temporary:
            fixture = BlindAssignmentFixture(Path(temporary))
            before_questions = read_json(fixture.content_root / "questions" / "DAN1.json")
            before_reviews = read_json(fixture.content_root / "reviews" / "DAN1.json")
            before_draft = read_json(fixture.content_root / "authored-batches" / "wave-blind-draft.json")

            result = fixture.run()

            self.assertEqual(result.returncode, 0, result.stderr)
            after_questions = read_json(fixture.content_root / "questions" / "DAN1.json")
            after_reviews = read_json(fixture.content_root / "reviews" / "DAN1.json")
            pools = {"Q-A": "A", "Q-B": "B", "Q-E": "emergency"}
            for before, after in zip(before_questions, after_questions, strict=True):
                expected = copy.deepcopy(before)
                expected["blind_pool"] = pools[before["id"]]
                self.assertEqual(after, expected)
            for before, after, row in zip(before_reviews, after_reviews, after_questions, strict=True):
                expected = copy.deepcopy(before)
                expected["content_sha256"] = content_hash(row)
                self.assertEqual(after, expected)
            authored = [
                *read_json(fixture.content_root / "authored-batches" / "tracked-compact.json"),
                *read_json(fixture.content_root / "authored-batches" / "tracked-pretty.json"),
            ]
            self.assertEqual({row["id"]: row["blind_pool"] for row in authored}, pools)
            expected_authored = [
                {"id": row["id"], "family": row["family"], "correct_option": row["correct_option"], "blind_pool": pools[row["id"]]}
                for row in before_questions
            ]
            self.assertEqual(
                (fixture.content_root / "authored-batches" / "tracked-compact.json").read_text(encoding="utf-8"),
                compact_rows(expected_authored[:1]),
            )
            self.assertEqual(
                (fixture.content_root / "authored-batches" / "tracked-pretty.json").read_text(encoding="utf-8"),
                json.dumps(expected_authored[1:], ensure_ascii=False, indent=2) + "\n",
            )
            self.assertEqual(
                read_json(fixture.content_root / "authored-batches" / "wave-blind-draft.json"),
                before_draft,
            )

    def test_second_run_is_byte_for_byte_idempotent(self) -> None:
        with temporary_directory() as temporary:
            fixture = BlindAssignmentFixture(Path(temporary))
            first = fixture.run()
            self.assertEqual(first.returncode, 0, first.stderr)
            paths = sorted(path for path in fixture.content_root.rglob("*.json"))
            snapshot = {path: path.read_bytes() for path in paths}

            second = fixture.run()

            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual({path: path.read_bytes() for path in paths}, snapshot)

    def test_ambiguous_authored_origin_fails_closed_without_writes(self) -> None:
        with temporary_directory() as temporary:
            fixture = BlindAssignmentFixture(Path(temporary))
            write_json(
                fixture.content_root / "authored-batches" / "duplicate.json",
                [{"id": "Q-A", "family": "single_choice_direct", "correct_option": 0}],
            )
            paths = sorted(path for path in fixture.content_root.rglob("*.json"))
            snapshot = {path: path.read_bytes() for path in paths}

            result = fixture.run()

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("origen authored ambiguo", result.stderr)
            self.assertEqual({path: path.read_bytes() for path in paths}, snapshot)

    def test_checked_manifest_has_exact_disjoint_assignments_and_verified_evidence(self) -> None:
        self.assertTrue(CHECKED_MANIFEST.is_file(), "falta el manifiesto versionado")
        manifest = read_json(CHECKED_MANIFEST)
        pools = manifest["pools"]
        self.assertEqual({pool: len(ids) for pool, ids in pools.items()}, {"A": 100, "B": 100, "emergency": 50})
        all_ids = [question_id for ids in pools.values() for question_id in ids]
        self.assertEqual(len(all_ids), len(set(all_ids)))
        self.assertEqual(manifest["evidence"]["production_snapshot"], "content/competitive-v11/baseline-production.json")
        self.assertEqual(manifest["evidence"]["production_question_id_overlap"], 0)
        self.assertEqual(manifest["evidence"]["public_local_question_id_overlap"], 0)


if __name__ == "__main__":
    unittest.main()
