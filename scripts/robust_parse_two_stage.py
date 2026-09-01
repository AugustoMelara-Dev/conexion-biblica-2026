import json, pathlib, re

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

decoder = json.JSONDecoder(strict=False)

def extract_json_objects(text):
    pos = 0
    while pos < len(text):
        match = text.find('{', pos)
        if match == -1:
            break
        try:
            obj, end_pos = decoder.raw_decode(text[match:])
            yield obj
            pos = match + end_pos
        except Exception:
            pos = match + 1

lines = main_log.read_text(encoding="utf-8").splitlines()

for line in lines:
    if not line.strip():
        continue
    row = json.loads(line)
    content = row.get("content", "")
    
    sender_match = re.search(r"sender=([0-9a-f\-]+)", content)
    if not sender_match:
        continue
    sender = sender_match.group(1)
    
    if sender not in stage_a_cids and sender not in stage_b_cids:
        continue
        
    for data in extract_json_objects(content):
        def traverse(obj):
            if isinstance(obj, dict):
                if "question_id" in obj:
                    yield obj
                for v in obj.values():
                    yield from traverse(v)
            elif isinstance(obj, list):
                for elem in obj:
                    yield from traverse(elem)
                    
        for q in traverse(data):
            qid = q.get("question_id")
            if not qid:
                continue
            if sender in stage_a_cids:
                stage_a_map[qid] = {**q, "cid": sender, "label": stage_a_cids[sender]}
            elif sender in stage_b_cids:
                stage_b_map[qid] = {**q, "cid": sender, "label": stage_b_cids[sender]}

print(f"Stage A questions parsed: {len(stage_a_map)} / 240")
print(f"Stage B questions parsed: {len(stage_b_map)} / 240")

(evidence_dir / "stage_a_compiled.json").write_text(json.dumps(stage_a_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(evidence_dir / "stage_b_compiled.json").write_text(json.dumps(stage_b_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
