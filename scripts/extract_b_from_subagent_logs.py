import json, pathlib, re

ROOT = pathlib.Path(".")
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"
evidence_dir.mkdir(parents=True, exist_ok=True)

stage_b_cids = {
    "24820601-a075-4388-b3e5-6cf8a5c0df55": "Auditor-B1",
    "58d6d353-1453-4add-83fa-72507a4c397a": "Auditor-B2",
    "7e981d8b-1e20-4d20-83e9-bcd97eb127c8": "Auditor-B3",
    "34a20ba4-10c4-4433-b3a1-bd750e42f362": "Auditor-B4",
}

stage_b_map = json.loads((evidence_dir / "stage_b_compiled.json").read_text(encoding="utf-8"))

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

for cid, label in stage_b_cids.items():
    subagent_log = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid / ".system_generated" / "logs" / "transcript_full.jsonl"
    if not subagent_log.exists():
        print(f"Log not found for {cid}")
        continue
        
    for line in subagent_log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        content = row.get("content", "")
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
                if qid:
                    stage_b_map[qid] = {**q, "cid": cid, "label": label}

print(f"Stage B questions parsed after reading subagent logs: {len(stage_b_map)} / 240")
(evidence_dir / "stage_b_compiled.json").write_text(json.dumps(stage_b_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
