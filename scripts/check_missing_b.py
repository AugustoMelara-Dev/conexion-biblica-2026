import json, pathlib

ROOT = pathlib.Path(".")
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"
stage_a = json.loads((evidence_dir / "stage_a_compiled.json").read_text(encoding="utf-8"))
stage_b = json.loads((evidence_dir / "stage_b_compiled.json").read_text(encoding="utf-8"))

missing_in_b = [qid for qid in stage_a if qid not in stage_b]
print(f"Missing in Stage B ({len(missing_in_b)}): {missing_in_b}")
