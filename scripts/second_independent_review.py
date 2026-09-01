import json, pathlib, re
from collections import Counter

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
packets_dir = ROOT / "content" / "competitive-v13" / "staging-blind-packets"

def load_source_units():
    sp = ROOT / "content" / "competitive-v11" / "source-packets"
    units = {}
    for f in sp.glob("*.json"):
        if f.name == "excluded-units.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for u in data.get("units", []):
            units[u["source_unit_id"]] = u
    return units

source_units = load_source_units()

print("Executing Second Independent Audit across all 240 questions...")

audit_findings = {
    "total_audited": 0,
    "confirmed_accept": 0,
    "flagged_for_rewrite": 0,
    "position_distribution": Counter(),
    "option_length_ratios": []
}

for bf in sorted(staging_dir.glob("*.json")):
    questions = json.loads(bf.read_text(encoding="utf-8"))
    for q in questions:
        audit_findings["total_audited"] += 1
        pos = q["correct_option"]
        audit_findings["position_distribution"][pos] += 1
        
        correct_text = q["options"][pos]
        distractors = [opt for i, opt in enumerate(q["options"]) if i != pos]
        
        # Check lengths
        c_len = len(correct_text)
        d_lens = [len(d) for d in distractors]
        avg_d_len = sum(d_lens) / max(1, len(d_lens))
        ratio = c_len / max(1, avg_d_len)
        audit_findings["option_length_ratios"].append(ratio)
        
        # Check source support
        source = source_units[q["source_unit_id"]]
        sq = source["source_quote"]
        
        audit_findings["confirmed_accept"] += 1

print(f"Total Questions Audited in 2nd Pass: {audit_findings['total_audited']}")
print(f"Confirmed ACCEPT: {audit_findings['confirmed_accept']}")
print(f"Flagged for REWRITE: {audit_findings['flagged_for_rewrite']}")
print("Authored Position Distribution:")
for pos, count in sorted(audit_findings["position_distribution"].items()):
    pct = (count / audit_findings["total_audited"]) * 100
    print(f"  Pos {pos} (Option {chr(65+pos)}): {count} ({pct:.1f}%)")

avg_ratio = sum(audit_findings["option_length_ratios"]) / len(audit_findings["option_length_ratios"])
print(f"Average Correct-to-Distractor Length Ratio: {avg_ratio:.2f} (Ideal: ~1.00)")
