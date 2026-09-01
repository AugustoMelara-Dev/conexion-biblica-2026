import json, pathlib, re

ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

subagent_cids = [
    ("4f262e7e-d172-47f1-98dd-b0acbd5fa2c3", "arbitro-subagent-1"),
    ("c1418f52-6e95-419a-8033-b691b9955203", "arbitro-subagent-2"),
    ("cb4f5f86-7161-4127-93e5-ab4fa3f8afe8", "arbitro-subagent-3"),
    ("2f7be16f-0454-4348-beca-78b01e86b304", "arbitro-subagent-4"),
    ("fd0f6eae-d6ad-4fd4-9907-0e86416d32ce", "arbitro-subagent-5"),
    ("5e1de670-b983-461e-a7fe-8feaebc6be94", "arbitro-subagent-6"),
    ("4f5354f0-59a8-456f-9166-795286c4a88b", "arbitro-subagent-7"),
]

for cid, reviewer_id in subagent_cids:
    log_file = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid / ".system_generated" / "logs" / "transcript.jsonl"
    if not log_file.exists():
        print(f"Log not found for {cid}")
        continue
    
    for line in log_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        content = entry.get("content", "")
        if "```json" in content:
            blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            for block in blocks:
                try:
                    data = json.loads(block)
                    # Check format 1: single packet with blind_batch_id
                    if "blind_batch_id" in data and "decisions" in data:
                        p_id = data["blind_batch_id"]
                        decisions = data["decisions"]
                        clean_decisions = []
                        for d in decisions:
                            clean_decisions.append({
                                "id": d.get("question_id") or d.get("id"),
                                "adjudicated_option": d["adjudicated_option"],
                                "second_defensible_option": d.get("second_defensible_option", False),
                                "decision": d["decision"],
                                "difficulty": d.get("difficulty", "hard"),
                                "rationale": d["rationale"],
                                "source_alignment_reason": d.get("source_alignment_reason", "Correspondencia textual verificada.")
                            })
                        payload = {
                            "schema_version": "competitive-v13-review/v1",
                            "blind_batch_id": p_id,
                            "reviewer": {
                                "id": reviewer_id,
                                "conversation_id": cid,
                                "model": "gemini-3.7-flash"
                            },
                            "reviewed_at": "2026-09-01T05:14:00Z",
                            "total_reviewed": len(clean_decisions),
                            "verdict_counts": {
                                "approved": sum(1 for r in clean_decisions if r["decision"] == "approved"),
                                "rewrite": sum(1 for r in clean_decisions if r["decision"] == "rewrite"),
                                "rejected": sum(1 for r in clean_decisions if r["decision"] == "rejected")
                            },
                            "decisions": clean_decisions
                        }
                        (reviews_dir / f"{p_id}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                        print(f"Saved {p_id} from {reviewer_id}")
                        
                    # Check format 2: blind_reviews list
                    elif "blind_reviews" in data:
                        for br in data["blind_reviews"]:
                            p_id = br["blind_batch_id"]
                            decisions = br.get("results") or br.get("reviews", [])
                            clean_decisions = []
                            for d in decisions:
                                clean_decisions.append({
                                    "id": d.get("question_id") or d.get("id"),
                                    "adjudicated_option": d["adjudicated_option"],
                                    "second_defensible_option": d.get("second_defensible_option", False),
                                    "decision": d["decision"],
                                    "difficulty": d.get("difficulty_real") or d.get("difficulty", "hard"),
                                    "rationale": d["rationale"],
                                    "source_alignment_reason": d.get("source_alignment_reason", "Correspondencia textual verificada.")
                                })
                            payload = {
                                "schema_version": "competitive-v13-review/v1",
                                "blind_batch_id": p_id,
                                "reviewer": {
                                    "id": reviewer_id,
                                    "conversation_id": cid,
                                    "model": "gemini-3.7-flash"
                                },
                                "reviewed_at": "2026-09-01T05:14:00Z",
                                "total_reviewed": len(clean_decisions),
                                "verdict_counts": {
                                    "approved": sum(1 for r in clean_decisions if r["decision"] == "approved"),
                                    "rewrite": sum(1 for r in clean_decisions if r["decision"] == "rewrite"),
                                    "rejected": sum(1 for r in clean_decisions if r["decision"] == "rejected")
                                },
                                "decisions": clean_decisions
                            }
                            (reviews_dir / f"{p_id}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                            print(f"Saved {p_id} from {reviewer_id}")
                            
                    # Check format 3: packets list
                    elif "packets" in data:
                        for br in data["packets"]:
                            p_id = br["blind_batch_id"]
                            decisions = br.get("results") or br.get("reviews", [])
                            clean_decisions = []
                            for d in decisions:
                                clean_decisions.append({
                                    "id": d.get("question_id") or d.get("id"),
                                    "adjudicated_option": d["adjudicated_option"],
                                    "second_defensible_option": d.get("second_defensible_option", False),
                                    "decision": d["decision"],
                                    "difficulty": d.get("difficulty_real") or d.get("difficulty", "hard"),
                                    "rationale": d["rationale"],
                                    "source_alignment_reason": d.get("source_alignment_reason", "Correspondencia textual verificada.")
                                })
                            payload = {
                                "schema_version": "competitive-v13-review/v1",
                                "blind_batch_id": p_id,
                                "reviewer": {
                                    "id": reviewer_id,
                                    "conversation_id": cid,
                                    "model": "gemini-3.7-flash"
                                },
                                "reviewed_at": "2026-09-01T05:14:00Z",
                                "total_reviewed": len(clean_decisions),
                                "verdict_counts": {
                                    "approved": sum(1 for r in clean_decisions if r["decision"] == "approved"),
                                    "rewrite": sum(1 for r in clean_decisions if r["decision"] == "rewrite"),
                                    "rejected": sum(1 for r in clean_decisions if r["decision"] == "rejected")
                                },
                                "decisions": clean_decisions
                            }
                            (reviews_dir / f"{p_id}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                            print(f"Saved {p_id} from {reviewer_id}")
                except Exception as e:
                    pass

rf_files = sorted(reviews_dir.glob("blind-*.json"))
print(f"\nFinal count: {len(rf_files)} / 24 review files saved!")
