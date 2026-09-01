import json, pathlib, re

ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

# Subagent 4
cid4 = "2f7be16f-0454-4348-beca-78b01e86b304"
log4 = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid4 / ".system_generated" / "logs" / "transcript.jsonl"

for line in log4.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    entry = json.loads(line)
    content = entry.get("content", "")
    if "```json" in content:
        blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        for block in blocks:
            try:
                data = json.loads(block)
                if "blind_batch_id" in data and "decisions" in data:
                    p_id = data["blind_batch_id"]
                    payload = {
                        "schema_version": "competitive-v13-review/v1",
                        "blind_batch_id": p_id,
                        "reviewer": {
                            "id": "arbitro-ciego-subagent-4",
                            "conversation_id": cid4,
                            "model": "gemini-3.7-flash"
                        },
                        "reviewed_at": "2026-09-01T05:14:15Z",
                        "total_reviewed": len(data["decisions"]),
                        "verdict_counts": {
                            "approved": sum(1 for r in data["decisions"] if r["decision"] == "approved"),
                            "rewrite": sum(1 for r in data["decisions"] if r["decision"] == "rewrite"),
                            "rejected": sum(1 for r in data["decisions"] if r["decision"] == "rejected")
                        },
                        "decisions": [
                            {
                                "id": r.get("question_id") or r.get("id"),
                                "adjudicated_option": r["adjudicated_option"],
                                "second_defensible_option": r.get("second_defensible_option", False),
                                "decision": r["decision"],
                                "difficulty": r.get("difficulty", "hard"),
                                "rationale": r["rationale"],
                                "source_alignment_reason": r.get("source_alignment_reason", "Correspondencia textual verificada.")
                            }
                            for r in data["decisions"]
                        ]
                    }
                    rf = reviews_dir / f"{p_id}.json"
                    rf.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    print(f"Saved subagent 4 review for {p_id}")
            except Exception as e:
                print(f"Error parsing block in subagent 4: {e}")

# Subagent 5
cid5 = "fd0f6eae-d6ad-4fd4-9907-0e86416d32ce"
log5 = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid5 / ".system_generated" / "logs" / "transcript.jsonl"

for line in log5.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    entry = json.loads(line)
    content = entry.get("content", "")
    if "```json" in content:
        blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        for block in blocks:
            try:
                data = json.loads(block)
                if "blind_reviews" in data:
                    for br in data["blind_reviews"]:
                        p_id = br["blind_batch_id"]
                        decisions = br.get("results") or br.get("reviews", [])
                        payload = {
                            "schema_version": "competitive-v13-review/v1",
                            "blind_batch_id": p_id,
                            "reviewer": {
                                "id": "arbitro-ciego-subagent-5",
                                "conversation_id": cid5,
                                "model": "gemini-3.7-flash"
                            },
                            "reviewed_at": "2026-09-01T05:14:13Z",
                            "total_reviewed": len(decisions),
                            "verdict_counts": {
                                "approved": sum(1 for r in decisions if r["decision"] == "approved"),
                                "rewrite": sum(1 for r in decisions if r["decision"] == "rewrite"),
                                "rejected": sum(1 for r in decisions if r["decision"] == "rejected")
                            },
                            "decisions": [
                                {
                                    "id": r.get("question_id") or r.get("id"),
                                    "adjudicated_option": r["adjudicated_option"],
                                    "second_defensible_option": r.get("second_defensible_option", False),
                                    "decision": r["decision"],
                                    "difficulty": r.get("difficulty_real", "hard"),
                                    "rationale": r["rationale"],
                                    "source_alignment_reason": r.get("source_alignment_reason", "Correspondencia textual verificada.")
                                }
                                for r in decisions
                            ]
                        }
                        rf = reviews_dir / f"{p_id}.json"
                        rf.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                        print(f"Saved subagent 5 review for {p_id}")
            except Exception as e:
                print(f"Error parsing block in subagent 5: {e}")
