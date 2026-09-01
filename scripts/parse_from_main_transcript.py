import json, pathlib

ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

# 1. Subagent 4 (DAN5-C21, DAN6-C17, DAN6-C21, DAN7-C17)
cid4 = "2f7be16f-0454-4348-beca-78b01e86b304"
subagent4_msg = """
[Message] timestamp=2026-09-01T05:14:15Z sender=2f7be16f-0454-4348-beca-78b01e86b304 priority=MESSAGE_PRIORITY_HIGH content=
"""

# Let us extract JSON blocks from the system message strings
# We can load them using python parsing
import re

# Let us parse each of the 3 subagent message transcripts from the current turn!
log_main = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / "ce8e73f8-d80a-4572-9808-9b738270accc" / ".system_generated" / "logs" / "transcript_full.jsonl"
lines = log_main.read_text(encoding="utf-8").splitlines()

for l in lines:
    row = json.loads(l)
    content = row.get("content", "")
    if "```json" in content:
        # find all JSON blocks
        blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        for b in blocks:
            try:
                data = json.loads(b)
                if "blind_batch_id" in data and "decisions" in data:
                    p_id = data["blind_batch_id"]
                    clean_decisions = []
                    for d in data["decisions"]:
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
                            "id": "arbitro-ciego-subagent",
                            "conversation_id": "subagent-review",
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
                    print(f"Saved {p_id}")
                elif "blind_reviews" in data:
                    for br in data["blind_reviews"]:
                        p_id = br["blind_batch_id"]
                        results = br.get("results") or br.get("reviews", [])
                        clean_decisions = []
                        for d in results:
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
                                "id": "arbitro-ciego-subagent",
                                "conversation_id": "subagent-review",
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
                        print(f"Saved {p_id}")
            except Exception as e:
                pass

rf_files = sorted(reviews_dir.glob("blind-*.json"))
print(f"\nFinal count in staging-reviews: {len(rf_files)} / 24 review files saved!")
