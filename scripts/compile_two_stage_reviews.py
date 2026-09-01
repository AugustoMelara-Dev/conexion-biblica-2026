import json, pathlib, re
from collections import Counter

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
stage_a_dir = ROOT / "content" / "competitive-v13" / "stage-a-packets"
stage_b_dir = ROOT / "content" / "competitive-v13" / "stage-b-packets"
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"
evidence_dir.mkdir(parents=True, exist_ok=True)

# 1. Parse Stage A from transcripts
stage_a_cids = {
    "5a707bcc-43d7-467f-8015-cda3109cc8af": "Competidor-A1",
    "1e02edbd-c8af-45a2-822b-af6678f59f62": "Competidor-A2",
    "37fdafb3-6789-4b3b-bc1e-1ea26bf44035": "Competidor-A3",
    "54f0f9be-8eeb-43e3-b796-b7ea95d56353": "Competidor-A4",
}

stage_a_map = {}
for cid, label in stage_a_cids.items():
    log = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid / ".system_generated" / "logs" / "transcript_full.jsonl"
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        content = row.get("content", "")
        if "```json" in content or "{" in content:
            blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if not blocks and content.strip().startswith("{") and content.strip().endswith("}"):
                blocks = [content.strip()]
            for b in blocks:
                try:
                    data = json.loads(b)
                    # Traverse all lists/dicts
                    items = []
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list):
                                items.extend(v)
                    elif isinstance(data, list):
                        items = data
                    for item in items:
                        if isinstance(item, dict):
                            # Batch container?
                            if "evaluations" in item or "results" in item or "reviews" in item or "verdicts" in item:
                                sub = item.get("evaluations") or item.get("results") or item.get("reviews") or item.get("verdicts") or []
                                for q in sub:
                                    if isinstance(q, dict) and "question_id" in q:
                                        stage_a_map[q["question_id"]] = {**q, "cid": cid, "label": label}
                            elif "question_id" in item:
                                stage_a_map[item["question_id"]] = {**item, "cid": cid, "label": label}
                except Exception:
                    pass

# 2. Parse Stage B from transcripts
stage_b_cids = {
    "24820601-a075-4388-b3e5-6cf8a5c0df55": "Auditor-B1",
    "58d6d353-1453-4add-83fa-72507a4c397a": "Auditor-B2",
    "7e981d8b-1e20-4d20-83e9-bcd97eb127c8": "Auditor-B3",
    "34a20ba4-10c4-4433-b3a1-bd750e42f362": "Auditor-B4",
}

stage_b_map = {}
for cid, label in stage_b_cids.items():
    log = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid / ".system_generated" / "logs" / "transcript_full.jsonl"
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        content = row.get("content", "")
        if "```json" in content or "{" in content:
            blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if not blocks and content.strip().startswith("{") and content.strip().endswith("}"):
                blocks = [content.strip()]
            for b in blocks:
                try:
                    data = json.loads(b)
                    items = []
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list):
                                items.extend(v)
                    elif isinstance(data, list):
                        items = data
                    for item in items:
                        if isinstance(item, dict):
                            if "questions" in item or "evaluations" in item or "verdicts" in item:
                                sub = item.get("questions") or item.get("evaluations") or item.get("verdicts") or []
                                for q in sub:
                                    if isinstance(q, dict) and "question_id" in q:
                                        stage_b_map[q["question_id"]] = {**q, "cid": cid, "label": label}
                            elif "question_id" in item:
                                stage_b_map[item["question_id"]] = {**item, "cid": cid, "label": label}
                except Exception:
                    pass

print(f"Total Stage A evaluations compiled: {len(stage_a_map)} / 240")
print(f"Total Stage B evaluations compiled: {len(stage_b_map)} / 240")

# Save evidence files
(evidence_dir / "stage_a_compiled.json").write_text(json.dumps(stage_a_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(evidence_dir / "stage_b_compiled.json").write_text(json.dumps(stage_b_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Analyze Stage A Difficulty & Format Signals
diff_counts = Counter()
giveaway_count = 0
for qid, a_data in stage_a_map.items():
    diff_counts[a_data.get("real_difficulty", "UNKNOWN")] += 1
    if a_data.get("length_or_precision_giveaway"):
        giveaway_count += 1

print("\n--- STAGE A (COMPETITOR) METRICS ---")
print("Real Difficulty Distribution as experienced by contestant:")
for diff, cnt in sorted(diff_counts.items()):
    pct = (cnt / len(stage_a_map)) * 100
    print(f"  {diff}: {cnt} ({pct:.1f}%)")
print(f"Questions with length/precision giveaway detected: {giveaway_count} / {len(stage_a_map)} ({(giveaway_count/len(stage_a_map))*100:.1f}%)")
