import json, pathlib

ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

# Subagent 6 results
cid6 = "5e1de670-b983-461e-a7fe-8feaebc6be94"
log6 = pathlib.Path.home() / ".gemini" / "antigravity" / "brain" / cid6 / ".system_generated" / "logs" / "transcript.jsonl"

for line in log6.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    entry = json.loads(line)
    content = entry.get("content", "")
    if "```json" in content:
        import re
        blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        for block in blocks:
            try:
                data = json.loads(block)
                if "blind_batch_id" in data and "decisions" in data:
                    p_id = data["blind_batch_id"]
                    rf = reviews_dir / f"{p_id}.json"
                    rf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    print(f"Saved subagent 6 review for {p_id}")
            except Exception as e:
                print(f"Error in block: {e}")

# Check all reviews in staging-reviews
rf_files = sorted(reviews_dir.glob("blind-*.json"))
print(f"\nTotal review files in staging-reviews: {len(rf_files)}")

total_decisions = 0
all_adjudicated_options = []
all_rationales = []

for rf in rf_files:
    data = json.loads(rf.read_text(encoding="utf-8"))
    decisions = data.get("decisions", [])
    total_decisions += len(decisions)
    for d in decisions:
        all_adjudicated_options.append(d["adjudicated_option"])
        all_rationales.append(d["rationale"])

print(f"Total decisions: {total_decisions}")
from collections import Counter
c = Counter(all_adjudicated_options)
print("Adjudicated option distribution in blind packets:")
for opt, cnt in sorted(c.items()):
    pct = (cnt / total_decisions) * 100
    print(f"  Option {opt}: {cnt} ({pct:.1f}%)")

print(f"Unique rationales: {len(set(all_rationales))} / {len(all_rationales)}")
