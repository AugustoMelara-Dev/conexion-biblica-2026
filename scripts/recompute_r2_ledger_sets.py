#!/usr/bin/env python3
"""
Section 4: Mathematical Recomputation of the R2 Ledger Using Real Sets
Reconstructs sets from actual checkpoints and questions:
- ALL_2217_CANONICAL_FACTS
- PRE_W1_R2_FACTS (Cycles 11-21)
- W1_CARRIL_A_FACTS (81 rewrite items)
- W1_CARRIL_B_FACTS (120 new items)
- W2_R2_LANE_FACTS (160 R2 items)
- W2_R3_LANE_FACTS (80 R3 items)
Outputs content/competitive-v13/waves/wave2/closeout/r2-ledger-recomputed.json.
"""
from collections import Counter
import glob
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def recompute_ledger():
    out_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "closeout"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. ALL_2217_CANONICAL_FACTS
    canonical_facts = set()
    for sf in sorted(glob.glob("content/competitive-v11/questions/*.json")):
        qs = json.loads(pathlib.Path(sf).read_text(encoding="utf-8"))
        for q in qs:
            canonical_facts.add(q["fact_id"])

    # 2. PRE_W1_R2_FACTS (Approved in Cycles 11 to 21)
    pre_w1_facts = set()
    for cycle_num in range(11, 22):
        cf = ROOT / "content" / "competitive-v13" / "release2" / "applied" / f"release2-reviewed-cycle{cycle_num}.json"
        if cf.exists():
            cdata = json.loads(cf.read_text(encoding="utf-8"))
            for item in cdata.get("approved", []):
                pre_w1_facts.add(item["fact_id"])

    # 3. Wave 1 Carril A and Carril B Facts
    w1_approved = json.loads(pathlib.Path("content/competitive-v13/wave1_approved_batch.json").read_text(encoding="utf-8"))
    w1_carril_a_facts = set()
    w1_carril_b_facts = set()
    w1_all_facts = set()

    for item in w1_approved:
        fid = item["fact_id"]
        w1_all_facts.add(fid)
        lane = item.get("lane", "")
        if "CARRIL_A" in lane or "REWRITE" in lane:
            w1_carril_a_facts.add(fid)
        else:
            w1_carril_b_facts.add(fid)

    # 4. Wave 2 R2 and R3 Facts
    w2_approved = json.loads(pathlib.Path("content/competitive-v13/waves/wave2/wave2_approved_batch.json").read_text(encoding="utf-8"))
    w2_r2_lane_facts = set()
    w2_r3_lane_facts = set()
    w2_all_facts = set()

    for item in w2_approved:
        fid = item["fact_id"]
        w2_all_facts.add(fid)
        lane = item.get("lane", "")
        if "CARRIL_R3" in lane:
            w2_r3_lane_facts.add(fid)
        else:
            w2_r2_lane_facts.add(fid)

    # Mathematical Set Computations
    w1_intersection_a_b = w1_carril_a_facts & w1_carril_b_facts
    w2_intersection_r2_r3 = w2_r2_lane_facts & w2_r3_lane_facts

    w1_new_unique_r2 = (w1_carril_a_facts | w1_carril_b_facts) - pre_w1_facts
    post_w1_r2_facts = pre_w1_facts | w1_new_unique_r2

    # R3 facts in Wave 2 eligible as R2 coverage (pending and valid)
    w2_eligible_facts = w2_r2_lane_facts | w2_r3_lane_facts
    w2_new_unique_r2 = w2_eligible_facts - post_w1_r2_facts

    post_w2_r2_facts = pre_w1_facts | w1_new_unique_r2 | w2_new_unique_r2
    r2_remaining = canonical_facts - post_w2_r2_facts

    # Duplicate and missing checks
    w1_missing_from_ledger = set()
    w2_missing_from_ledger = set()

    print("\n--- R2 LEDGER MATHEMATICAL RECOMPUTATION ---")
    print(f"ALL_2217_CANONICAL_FACTS: {len(canonical_facts)}")
    print(f"PRE_W1_R2_FACTS (Cycles 11-21): {len(pre_w1_facts)}")
    print(f"W1_CARRIL_A_FACTS: {len(w1_carril_a_facts)}")
    print(f"W1_CARRIL_B_FACTS: {len(w1_carril_b_facts)}")
    print(f"Intersection W1 Carril A AND Carril B: {len(w1_intersection_a_b)}")
    print(f"W1_NEW_UNIQUE_R2: {len(w1_new_unique_r2)}")
    print(f"POST_W1_R2_FACTS: {len(post_w1_r2_facts)}")
    print(f"W2_R2_LANE_FACTS: {len(w2_r2_lane_facts)}")
    print(f"W2_R3_LANE_FACTS: {len(w2_r3_lane_facts)}")
    print(f"Intersection W2 R2 AND R3: {len(w2_intersection_r2_r3)}")
    print(f"W2_NEW_UNIQUE_R2: {len(w2_new_unique_r2)}")
    print(f"POST_W2_R2_FACTS: {len(post_w2_r2_facts)}")
    print(f"R2_REMAINING: {len(r2_remaining)}")

    ledger_payload = {
        "contract": "CB2026_R2_LEDGER_RECOMPUTED_V1",
        "set_sizes": {
            "ALL_2217_CANONICAL_FACTS": len(canonical_facts),
            "PRE_W1_R2_FACTS": len(pre_w1_facts),
            "W1_CARRIL_A_FACTS": len(w1_carril_a_facts),
            "W1_CARRIL_B_FACTS": len(w1_carril_b_facts),
            "W1_INTERSECTION_A_B": len(w1_intersection_a_b),
            "W1_NEW_UNIQUE_R2": len(w1_new_unique_r2),
            "POST_W1_R2_FACTS": len(post_w1_r2_facts),
            "W2_R2_LANE_FACTS": len(w2_r2_lane_facts),
            "W2_R3_LANE_FACTS": len(w2_r3_lane_facts),
            "W2_INTERSECTION_R2_R3": len(w2_intersection_r2_r3),
            "W2_NEW_UNIQUE_R2": len(w2_new_unique_r2),
            "POST_W2_R2_FACTS": len(post_w2_r2_facts),
            "R2_REMAINING": len(r2_remaining)
        },
        "intersections": {
            "w1_carril_a_and_b": sorted(list(w1_intersection_a_b)),
            "w2_r2_and_r3": sorted(list(w2_intersection_r2_r3))
        },
        "double_eligibility_registered": {
            "w2_r3_facts_credited_to_r2_coverage": len(w2_r3_lane_facts),
            "fact_ids": sorted(list(w2_r3_lane_facts))
        }
    }

    out_file = out_dir / "r2-ledger-recomputed.json"
    out_file.write_text(json.dumps(ledger_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved recomputed ledger to {out_file}")

if __name__ == "__main__":
    recompute_ledger()
