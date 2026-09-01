"""Integración real compile_bank -> HTTP -> audit-live-final-bank."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPILE_PATH = ROOT / "scripts" / "compile-competitive-v11.py"
COMPILE_SPEC = importlib.util.spec_from_file_location("compile_live_audit_fixture", COMPILE_PATH)
assert COMPILE_SPEC and COMPILE_SPEC.loader
compiler = importlib.util.module_from_spec(COMPILE_SPEC)
COMPILE_SPEC.loader.exec_module(compiler)


def question(*, suffix: str, fact_id: str, blind_pool: str | None) -> dict:
    return {
        "id": f"DAN1-V11-LIVE-{suffix}",
        "source_unit_id": "DAN1-V001",
        "fact_id": fact_id,
        "role": "central",
        "family": "single_choice_direct",
        "subtype": "factual_recall",
        "question": f"¿Quién sitió Jerusalén en el detalle competitivo {suffix}?",
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
        "difficulty": "hard" if blind_pool else "medium",
        "importance": "high",
        "relation_type": f"event_participant_{suffix.lower()}",
        "option_category": "person",
        "false_mutation": None,
        "blank_span": None,
        "significance": "Reserva compilada realmente." if blind_pool else None,
        "variant_justification": None,
        "blind_pool": blind_pool,
        "ai_review": {
            "status": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": "live-integration-reviewer",
        },
    }


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


class AuditHTTPServer(ThreadingHTTPServer):
    request_queue_size = 64


class LiveAuditCompilerIntegrationTests(unittest.TestCase):
    def test_compiled_public_and_private_artifacts_pass_the_http_gate(self) -> None:
        root = ROOT / "tmp" / "competitive-v11-tests" / "live-audit-real"
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, root, True)
        try:
            source = root / "source"
            questions = source / "questions"
            packets = source / "source-packets"
            questions.mkdir(parents=True)
            packets.mkdir(parents=True)

            rows = [
                question(suffix="TRAIN", fact_id="F-TRAIN", blind_pool=None),
                question(suffix="A", fact_id="F-BLIND-A", blind_pool="A"),
            ]
            for unit in compiler.EXPECTED_UNITS:
                payload = rows if unit == "DAN1" else []
                (questions / f"{unit}.json").write_text(
                    json.dumps(payload, ensure_ascii=False), encoding="utf-8"
                )
            source_unit = {
                "source_unit_id": "DAN1-V001",
                "source_ref": "Daniel 1:1",
                "source_quote": rows[0]["source_quote"],
            }
            (packets / "DAN1.json").write_text(
                json.dumps({"units": [source_unit]}, ensure_ascii=False), encoding="utf-8"
            )

            host_root = root / "host"
            public_output = host_root / "banks" / "final-2026"
            public_output.parent.mkdir(parents=True)
            blind_output = root / "private"
            requirements = {
                "A": {
                    "fact_count": 1,
                    "families": {"selection": 1, "fill_choice": 0, "true_false": 0},
                },
                "B": {
                    "fact_count": 0,
                    "families": {"selection": 0, "fill_choice": 0, "true_false": 0},
                },
                "emergency": {
                    "fact_count": 0,
                    "families": {"selection": 0, "fill_choice": 0, "true_false": 0},
                },
            }
            compiler.compile_bank(
                source,
                public_output,
                blind_output=blind_output,
                blind_requirements=requirements,
            )

            public_manifest = json.loads((public_output / "manifest.json").read_text(encoding="utf-8"))
            private_manifest = json.loads((blind_output / "manifest.json").read_text(encoding="utf-8"))
            public_rows = json.loads((public_output / "questions" / "DAN1.json").read_text(encoding="utf-8"))
            private_rows = json.loads((blind_output / "questions" / "A" / "DAN1.json").read_text(encoding="utf-8"))
            self.assertEqual(public_rows[0]["role"], "central")
            self.assertEqual(private_rows[0]["role"], "central")
            self.assertNotEqual(public_manifest["build_id"], public_manifest["blind_delivery"]["artifact_revision"])
            self.assertEqual(public_manifest["build_id"], private_manifest["build_id"])
            self.assertEqual(
                public_manifest["blind_delivery"]["artifact_revision"],
                private_manifest["artifact_revision"],
            )
            self.assertEqual(public_rows[0]["row_content_sha256"], compiler.emitted_row_hash(public_rows[0]))
            self.assertEqual(private_rows[0]["row_content_sha256"], compiler.emitted_row_hash(private_rows[0]))
            self.assertEqual(public_manifest["blind_pools"]["B"]["families"], requirements["B"]["families"])
            self.assertEqual(private_manifest["pools"]["emergency"]["families"], requirements["emergency"]["families"])

            server = AuditHTTPServer(
                ("127.0.0.1", 0), partial(QuietHandler, directory=str(root))
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                origin = f"http://127.0.0.1:{server.server_port}"
                audit_module = (ROOT / "scripts" / "audit-live-final-bank.mjs").as_uri()
                program = (
                    f'import {{ auditLiveFinalBank, RELEASE_BLIND_REQUIREMENTS }} from "{audit_module}";'
                    "const base={"
                    "baseUrl:process.argv[1]+'/host',publicRoot:process.argv[2],"
                    "blindBaseUrl:process.argv[1]+'/private',blindRoot:process.argv[3]};"
                    "const custom=await auditLiveFinalBank({...base,blindRequirements:JSON.parse(process.argv[4])});"
                    "const release=await auditLiveFinalBank({...base,blindRequirements:RELEASE_BLIND_REQUIREMENTS});"
                    "console.log(JSON.stringify({custom,release}));"
                    "if(custom.failures.length)process.exitCode=1;"
                )
                completed = subprocess.run(
                    [
                        "node",
                        "--input-type=module",
                        "-e",
                        program,
                        origin,
                        str(host_root),
                        str(blind_output),
                        json.dumps(requirements),
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                cli_root = root / "cli"
                shutil.copytree(host_root, cli_root / "public")
                cli_completed = subprocess.run(
                    ["node", str(ROOT / "scripts" / "audit-live-final-bank.mjs")],
                    cwd=cli_root,
                    env={**os.environ, "FINAL_BANK_BASE_URL": f"{origin}/host"},
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            reports = json.loads(completed.stdout)
            custom_report = reports["custom"]
            release_report = reports["release"]
            self.assertEqual(custom_report["failures"], [])
            self.assertEqual(custom_report["questions"], 2)
            self.assertEqual(custom_report["uniqueFacts"], 2)
            self.assertEqual(custom_report["blindQuestions"], 1)
            self.assertIn(
                "release:A:fact_count:expected_100:actual_1",
                release_report["failures"],
            )
            self.assertEqual(release_report["privateAudit"], "NOT_RUN")
            self.assertEqual(cli_completed.returncode, 0, cli_completed.stderr or cli_completed.stdout)
            cli_report = json.loads(cli_completed.stdout)
            self.assertEqual(cli_report["privateAudit"], "NOT_RUN")
            self.assertIsNone(cli_report["blindQuestions"])
            self.assertEqual(cli_report["failures"], [])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
