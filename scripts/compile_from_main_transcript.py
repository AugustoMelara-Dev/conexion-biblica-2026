import json, pathlib, re
from collections import Counter

ROOT = pathlib.Path(".")
main_log = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / "ce8e73f8-d80a-4572-9808-9b738270accc" / ".system_generated" / "logs" / "transcript_full.jsonl"
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"
evidence_dir.mkdir(parents=True, exist_ok=True)

stage_a_cids = {
    "5a707bcc-43d7-467f-8015-cda3109cc8af": "Competidor-A1",
    "1e02edbd-c8af-45a2-822b-af6678f59f62": "Competidor-A2",
    "37fdafb3-6789-4b3b-bc1e-1ea26bf44035": "Competidor-A3",
    "54f0f9be-8eeb-43e3-b796-b7ea95d56353": "Competidor-A4",
}

stage_b_cids = {
    "24820601-a075-4388-b3e5-6cf8a5c0df55": "Auditor-B1",
    "58d6d353-1453-4add-83fa-72507a4c397a": "Auditor-B2",
    "7e981d8b-1e20-4d20-83e9-bcd97eb127c8": "Auditor-B3",
    "34a20ba4-10c4-4433-b3a1-bd750e42f362": "Auditor-B4",
}

stage_a_map = {}
stage_b_map = {}

lines = main_log.read_text(encoding="utf-8").splitlines()

for line in lines:
    if not line.strip():
        continue
    row = json.loads(line)
    content = row.get("content", "")
    
    # Check if content has sender
    sender = None
    for cid in list(stage_a_cids.keys()) + list(stage_b_cids.keys()):
        if cid in content:
            sender = cid
            break
            
    if not sender:
        continue
        
    blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if not blocks:
        # Check raw JSON
        match = re.search(r"(\{\s*\"(?:stage|audit_version|audit_type|stage_a_resolutions|batches)[\s\S]*\})", content)
        if match:
            blocks = [match.group(1)]
            
    for b in blocks:
        try:
            data = json.loads(b)
            # Traverse
            def find_questions(obj):
                if isinstance(obj, dict):
                    if "question_id" in obj:
                        yield obj
                    for k, v in obj.items():
                        yield from find_questions(v)
                elif isinstance(obj, list):
                    for elem in obj:
                        yield from find_questions(elem)
                        
            for q in find_questions(data):
                qid = q.get("question_id")
                if not qid:
                    continue
                if sender in stage_a_cids:
                    stage_a_map[qid] = {**q, "cid": sender, "label": stage_a_cids[sender]}
                elif sender in stage_b_cids:
                    stage_b_map[qid] = {**q, "cid": sender, "label": stage_b_cids[sender]}
        except Exception as e:
            pass

print(f"Total Stage A evaluations compiled from main transcript: {len(stage_a_map)} / 240")
print(f"Total Stage B evaluations compiled from main transcript: {len(stage_b_map)} / 240")

# Save compiled evidence files
(evidence_dir / "stage_a_compiled.json").write_text(json.dumps(stage_a_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(evidence_dir / "stage_b_compiled.json").write_text(json.dumps(stage_b_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
