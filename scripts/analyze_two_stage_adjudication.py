import json, pathlib
from collections import Counter

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
stage_a_dir = ROOT / "content" / "competitive-v13" / "stage-a-packets"
stage_b_dir = ROOT / "content" / "competitive-v13" / "stage-b-packets"
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"

stage_a_map = json.loads((evidence_dir / "stage_a_compiled.json").read_text(encoding="utf-8"))
stage_b_map = json.loads((evidence_dir / "stage_b_compiled.json").read_text(encoding="utf-8"))

# Load packets to know shuffled option texts
def load_packet_questions(p_dir):
    p_map = {}
    for pf in p_dir.glob("*.json"):
        data = json.loads(pf.read_text(encoding="utf-8"))
        for q in data.get("questions", []):
            p_map[q["question_id"]] = q
    return p_map

pack_a = load_packet_questions(stage_a_dir)
pack_b = load_packet_questions(stage_b_dir)

# Load authored questions
authored_map = {}
for bf in staging_dir.glob("*.json"):
    data = json.loads(bf.read_text(encoding="utf-8"))
    for q in data:
        authored_map[q["id"]] = q

print("Cross-referencing 240 questions between Stage A, Stage B, and Authored corpus...")

analysis_results = {
    "total": 0,
    "unanimous_answer_match": 0,
    "answer_mismatch": 0,
    "pure_accept_hard_expert": 0,
    "easy_medium_needs_recalibration": 0,
    "length_giveaway_needs_recalibration": 0,
    "difficulty_distribution_a": Counter(),
    "ratios": [],
    "items_to_recalibrate": [],
    "items_pure_accept": []
}

for qid in sorted(authored_map.keys()):
    analysis_results["total"] += 1
    auth = authored_map[qid]
    a_eval = stage_a_map[qid]
    b_eval = stage_b_map[qid]
    
    # 1. Option text chosen in Stage A
    opts_a = pack_a[qid]["options"]
    chosen_idx_a = a_eval.get("chosen_option")
    chosen_text_a = opts_a[chosen_idx_a]
    
    # 2. Option text adjudicated in Stage B
    opts_b = pack_b[qid]["options"]
    adj_idx_b = b_eval.get("adjudicated_option")
    adj_text_b = opts_b[adj_idx_b]
    
    # 3. Authored correct text
    auth_correct = auth["options"][auth["correct_option"]]
    
    if chosen_text_a == auth_correct and adj_text_b == auth_correct:
        analysis_results["unanimous_answer_match"] += 1
    else:
        analysis_results["answer_mismatch"] += 1
        
    diff_a = a_eval.get("real_difficulty", "MEDIUM")
    analysis_results["difficulty_distribution_a"][diff_a] += 1
    
    giveaway = a_eval.get("length_or_precision_giveaway", False)
    
    # Length ratio
    correct_len = len(auth_correct)
    distractor_lens = [len(opt) for i, opt in enumerate(auth["options"]) if i != auth["correct_option"]]
    avg_d_len = sum(distractor_lens) / max(1, len(distractor_lens))
    ratio = correct_len / max(1, avg_d_len)
    analysis_results["ratios"].append(ratio)
    
    # Check if pure accept HARD/EXPERT without giveaway and ratio <= 1.20
    if diff_a in ["HARD", "EXPERT"] and not giveaway and ratio <= 1.20:
        analysis_results["pure_accept_hard_expert"] += 1
        analysis_results["items_pure_accept"].append(qid)
    else:
        if diff_a in ["EASY", "MEDIUM"]:
            analysis_results["easy_medium_needs_recalibration"] += 1
        if giveaway or ratio > 1.20:
            analysis_results["length_giveaway_needs_recalibration"] += 1
        analysis_results["items_to_recalibrate"].append({
            "question_id": qid,
            "difficulty_a": diff_a,
            "giveaway": giveaway,
            "ratio": ratio,
            "wording_notes": a_eval.get("wording_notes", "")
        })

print(f"\nTotal Evaluated in Two Stages: {analysis_results['total']}")
print(f"Unanimous Answer Agreement (Author == Competitor A == Auditor B): {analysis_results['unanimous_answer_match']} / {analysis_results['total']}")
print(f"Answer Mismatches: {analysis_results['answer_mismatch']}")

print("\nCompetitor (Stage A) Real Difficulty Breakdown:")
for d, c in sorted(analysis_results["difficulty_distribution_a"].items()):
    pct = (c / analysis_results['total']) * 100
    print(f"  {d}: {c} ({pct:.1f}%)")

avg_ratio = sum(analysis_results["ratios"]) / len(analysis_results["ratios"])
print(f"\nAverage Correct-to-Distractor Length Ratio: {avg_ratio:.2f}")
print(f"Questions meeting PURE ACCEPT (HARD/EXPERT, no giveaway, ratio <= 1.20): {analysis_results['pure_accept_hard_expert']}")
print(f"Questions flagged for Distractor Recalibration/Lengthening: {len(analysis_results['items_to_recalibrate'])}")

(evidence_dir / "adjudication_summary.json").write_text(json.dumps({
    "total": analysis_results["total"],
    "unanimous_answer_match": analysis_results["unanimous_answer_match"],
    "pure_accept_count": analysis_results["pure_accept_hard_expert"],
    "recalibrate_count": len(analysis_results["items_to_recalibrate"]),
    "difficulty_distribution": dict(analysis_results["difficulty_distribution_a"]),
    "pure_accept_ids": analysis_results["items_pure_accept"],
    "recalibrate_items": analysis_results["items_to_recalibrate"]
}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
