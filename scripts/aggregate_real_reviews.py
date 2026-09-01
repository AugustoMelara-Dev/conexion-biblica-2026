import json, pathlib, re
from collections import Counter

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
stage_a_dir = ROOT / "content" / "competitive-v13" / "stage-a-packets"
stage_b_dir = ROOT / "content" / "competitive-v13" / "stage-b-packets"
reports_dir = ROOT / "content" / "competitive-v13" / "audit-evidence"
reports_dir.mkdir(parents=True, exist_ok=True)

# Subagent conversation IDs
stage_a_cids = [
    "5a707bcc-43d7-467f-8015-cda3109cc8af",
    "1e02edbd-c8af-45a2-822b-af6678f59f62",
    "37fdafb3-6789-4b3b-bc1e-1ea26bf44035",
    "54f0f9be-8eeb-43e3-b796-b7ea95d56353",
]
stage_b_cids = [
    "24820601-a075-4388-b3e5-6cf8a5c0df55",
    "58d6d353-1453-4add-83fa-72507a4c397a",
    "7e981d8b-1e20-4d20-83e9-bcd97eb127c8",
    "34a20ba4-10c4-4433-b3a1-bd750e42f362",
]

def load_transcript_blocks(cids):
    results = {}
    for cid in cids:
        log = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid / ".system_generated" / "logs" / "transcript_full.jsonl"
        if not log.exists():
            continue
        text = log.read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            content = entry.get("content", "")
            if "```json" in content:
                blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
                for b in blocks:
                    try:
                        data = json.loads(b)
                        # could be list or dict
                        if isinstance(data, dict):
                            # format with batch_id or packets or direct questions
                            if "questions" in data:
                                for q in data["questions"]:
                                    qid = q.get("question_id") or q.get("id")
                                    if qid:
                                        results[qid] = {**q, "cid": cid}
                            if "packets" in data:
                                for p in data["packets"]:
                                    for q in p.get("questions") or p.get("reviews") or []:
                                        qid = q.get("question_id") or q.get("id")
                                        if qid:
                                            results[qid] = {**q, "cid": cid}
                            if "results" in data:
                                for q in data["results"]:
                                    qid = q.get("question_id") or q.get("id")
                                    if qid:
                                        results[qid] = {**q, "cid": cid}
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    if "questions" in item or "reviews" in item:
                                        for q in (item.get("questions") or item.get("reviews")):
                                            qid = q.get("question_id") or q.get("id")
                                            if qid:
                                                results[qid] = {**q, "cid": cid}
                                    elif "question_id" in item or "id" in item:
                                        qid = item.get("question_id") or item.get("id")
                                        results[qid] = {**item, "cid": cid}
                    except Exception:
                        pass
    return results

stage_a_results = load_transcript_blocks(stage_a_cids)
stage_b_results = load_transcript_blocks(stage_b_cids)

print(f"Loaded Stage A results: {len(stage_a_results)} / 240")
print(f"Loaded Stage B results: {len(stage_b_results)} / 240")
