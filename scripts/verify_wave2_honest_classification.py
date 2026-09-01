#!/usr/bin/env python3
"""
Section 3: Honest Competitive Classification for Wave 2 (240 items)
Evaluates each question based on empirical blind and source findings:
- R2_COVERAGE_ACCEPT
- R2_COMPETITIVE_ACCEPT
- R2_REWRITE / R2_REJECT
- R3_COMPETITIVE_ACCEPT
- R3_DOWNGRADED_TO_COVERAGE
- R3_REWRITE / R3_REJECT
Outputs content/competitive-v13/waves/wave2/closeout/wave2-honest-classification.json.
"""
from collections import Counter
import glob
import json
import os
import pathlib
import sys
import unicodedata

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import canonical_hash

def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", str(text))
    return " ".join(normalized.split()).lower()

def run_honest_classification():
    out_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "closeout"
    out_dir.mkdir(parents=True, exist_ok=True)

    corpus_path = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "wave2_authored_corpus.json"
    authored_corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    authored_map = {q["id"]: q for q in authored_corpus}

    # Load Stage A reviews
    stage_a_reviews = {}
    for f in sorted(glob.glob("content/competitive-v13/waves/wave2/stage-a/*/*.json")):
        data = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("evaluations", data.get("reviews", data.get("questions", [])))
        for r in items:
            stage_a_reviews[r["question_id"]] = r

    # Load Stage B reviews
    stage_b_reviews = {}
    for f in sorted(glob.glob("content/competitive-v13/waves/wave2/stage-b/*/*.json")):
        data = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("verdicts", data.get("evaluations", data.get("reviews", data.get("questions", []))))
        for r in items:
            stage_b_reviews[r["question_id"]] = r

    # Metrics counters
    difficulty_dist = Counter()
    solved_by_dist = Counter()
    plausible_options_dist = Counter()
    recommendations_a_dist = Counter()
    decisions_b_dist = Counter()
    giveaways_dist = Counter()
    disagreements_count = 0

    classification_counts = Counter()
    detailed_records = []

    for qid, auth_q in sorted(authored_map.items()):
        rev_a = stage_a_reviews[qid]
        rev_b = stage_b_reviews[qid]

        lane = auth_q.get("lane", "CARRIL_R2_COBERTURA")
        is_r3_candidate = (lane == "CARRIL_R3_COMPETITIVO_TEMPRANO")

        # Stage A fields
        diff_a = rev_a.get("real_difficulty", "MEDIUM").upper()
        solved_by_a = rev_a.get("solved_by", "KNOWLEDGE").upper()
        plausible_cnt_a = rev_a.get("initially_plausible_options_count", 1)
        rec_a = rev_a.get("recommendation", "ACCEPT").upper()
        giveaway_a = rev_a.get("length_or_precision_giveaway", False)
        text_a = rev_a.get("selected_option_text")

        difficulty_dist[diff_a] += 1
        solved_by_dist[solved_by_a] += 1
        plausible_options_dist[plausible_cnt_a] += 1
        recommendations_a_dist[rec_a] += 1
        if giveaway_a:
            giveaways_dist["length_or_precision"] += 1

        # Stage B fields
        dec_b = rev_b.get("decision", "ACCEPT").upper()
        sec_def_b = rev_b.get("second_defensible_option", False)
        text_b = rev_b.get("selected_option_text")
        sem_cat_b = rev_b.get("semantic_category_check", "EXCELLENT").upper()
        decisions_b_dist[dec_b] += 1

        # Triple text match
        norm_a = normalize_text(text_a)
        norm_b = normalize_text(text_b)
        norm_auth = normalize_text(auth_q["correct_answer"])
        text_match = (norm_a == norm_b == norm_auth)
        if not text_match:
            disagreements_count += 1

        # Recalculated Answer Binding
        binding_payload = {
            "presentation_sha256": auth_q["presentation_sha256"],
            "correct_answer": text_b,
            "source_ref": auth_q["source_ref"],
            "source_quote": auth_q["source_quote"]
        }
        recalc_binding = canonical_hash(binding_payload)
        binding_match = (recalc_binding == auth_q["answer_binding_sha256"])

        # Rigorous Competitive Acceptance Criteria
        is_competitive_qualified = (
            text_match and
            binding_match and
            dec_b == "ACCEPT" and
            not sec_def_b and
            rec_a == "ACCEPT" and
            diff_a in ["HARD", "EXPERT"] and
            plausible_cnt_a >= 2 and
            solved_by_a in ["KNOWLEDGE", "ELIMINATION"] and
            solved_by_a not in ["WORDING_CLUE", "GUESS"] and
            not giveaway_a and
            sem_cat_b in ["EXCELLENT", "GOOD"]
        )

        # Base Coverage Acceptance Criteria
        is_coverage_qualified = (
            text_match and
            binding_match and
            dec_b == "ACCEPT" and
            not sec_def_b and
            rec_a == "ACCEPT" and
            not giveaway_a
        )

        # Classify
        if is_r3_candidate:
            if is_competitive_qualified:
                classification = "R3_COMPETITIVE_ACCEPT"
            elif is_coverage_qualified:
                classification = "R3_DOWNGRADED_TO_COVERAGE"
            elif sec_def_b or dec_b == "REJECT" or not text_match:
                classification = "R3_REJECT"
            else:
                classification = "R3_REWRITE"
        else: # R2 candidate
            if is_competitive_qualified:
                classification = "R2_COMPETITIVE_ACCEPT"
            elif is_coverage_qualified:
                classification = "R2_COVERAGE_ACCEPT"
            elif sec_def_b or dec_b == "REJECT" or not text_match:
                classification = "R2_REJECT"
            else:
                classification = "R2_REWRITE"

        classification_counts[classification] += 1

        detailed_records.append({
            "question_id": qid,
            "fact_id": auth_q["fact_id"],
            "lane": lane,
            "classification": classification,
            "real_difficulty": diff_a,
            "solved_by": solved_by_a,
            "initially_plausible_options_count": plausible_cnt_a,
            "recommendation_a": rec_a,
            "decision_b": dec_b,
            "second_defensible_option": sec_def_b,
            "length_or_precision_giveaway": giveaway_a,
            "triple_text_match": text_match,
            "recalculated_binding_match": binding_match
        })

    print("\n--- HONEST CLASSIFICATION REPORT (WAVE 2) ---")
    print(f"Total evaluated: {len(authored_map)}")
    print("Classifications:")
    for k, v in sorted(classification_counts.items()):
        print(f"  {k}: {v}")
    print("\nDistributions:")
    print(f"  Difficulty: {dict(difficulty_dist)}")
    print(f"  Solved By: {dict(solved_by_dist)}")
    print(f"  Plausible Options: {dict(plausible_options_dist)}")
    print(f"  Stage A Recommendations: {dict(recommendations_a_dist)}")
    print(f"  Stage B Decisions: {dict(decisions_b_dist)}")
    print(f"  Giveaways: {dict(giveaways_dist)}")
    print(f"  Triple Disagreements: {disagreements_count}")

    r3_competitive_count = classification_counts["R3_COMPETITIVE_ACCEPT"]
    print(f"\nReal Cumulative R3 Count from Wave 2: {r3_competitive_count}")

    out_file = out_dir / "wave2-honest-classification.json"
    out_payload = {
        "contract": "CB2026_WAVE2_HONEST_CLASSIFICATION_V1",
        "total_evaluated": len(authored_map),
        "classifications": dict(classification_counts),
        "r3_competitive_accumulated": r3_competitive_count,
        "distributions": {
            "difficulty": dict(difficulty_dist),
            "solved_by": dict(solved_by_dist),
            "plausible_options_count": dict(plausible_options_dist),
            "recommendations_a": dict(recommendations_a_dist),
            "decisions_b": dict(decisions_b_dist),
            "giveaways": dict(giveaways_dist),
            "disagreements": disagreements_count
        },
        "records": detailed_records
    }
    out_file.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved honest classification report to {out_file}")

if __name__ == "__main__":
    run_honest_classification()
