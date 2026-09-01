#!/usr/bin/env python3
"""
Evaluates both tracks:
1. Carril B: Piloto R3 (60 candidates) -> Gate check (A1, A2, B, Author)
2. Carril A: Wave 3 R2 (240 candidates) -> Gate check & Promotion
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

def evaluate():
    # ----------------------------------------------------
    # 1. EVALUATE PILOTO R3 (60 items)
    # ----------------------------------------------------
    pilot_authored = json.loads((ROOT / ".work" / "competitive-v16" / "piloto-r3" / "pilot_authored_corpus.json").read_text(encoding="utf-8"))
    pilot_a1 = {r["question_id"]: r for r in json.loads((ROOT / ".work" / "competitive-v16" / "piloto-r3" / "stage-a1" / "evaluations.json").read_text(encoding="utf-8"))}
    pilot_a2 = {r["question_id"]: r for r in json.loads((ROOT / ".work" / "competitive-v16" / "piloto-r3" / "stage-a2" / "evaluations.json").read_text(encoding="utf-8"))}
    pilot_b = {r["question_id"]: r for r in json.loads((ROOT / ".work" / "competitive-v16" / "piloto-r3" / "stage-b" / "verdicts.json").read_text(encoding="utf-8"))}

    pilot_classifications = Counter()
    pilot_records = []
    pilot_diff_a1 = Counter()
    pilot_diff_a2 = Counter()

    for q in pilot_authored:
        qid = q["id"]
        ra1 = pilot_a1[qid]
        ra2 = pilot_a2[qid]
        rb = pilot_b[qid]

        text_auth = q.get("correct_answer") or q["options"][q["correct_option"]]
        text_a1 = ra1.get("selected_option_text")
        text_a2 = ra2.get("selected_option_text")
        text_b = rb.get("selected_option_text")

        norm_auth = normalize_text(text_auth)
        norm_a1 = normalize_text(text_a1)
        norm_a2 = normalize_text(text_a2)
        norm_b = normalize_text(text_b)

        match_all = (norm_auth == norm_a1 == norm_a2 == norm_b)
        
        diff_a1 = ra1.get("real_difficulty", "MEDIUM").upper()
        diff_a2 = ra2.get("real_difficulty", "MEDIUM").upper()
        pilot_diff_a1[diff_a1] += 1
        pilot_diff_a2[diff_a2] += 1

        is_hard_or_expert = (diff_a1 in ["HARD", "EXPERT"] and diff_a2 in ["HARD", "EXPERT"])
        is_clean_b = (rb.get("decision") == "ACCEPT" and not rb.get("second_defensible_option", False))
        is_clean_a = (ra1.get("recommendation") == "ACCEPT" and ra2.get("recommendation") == "ACCEPT" and not ra1.get("length_or_precision_giveaway") and not ra2.get("length_or_precision_giveaway"))

        if match_all and is_clean_b and is_clean_a and is_hard_or_expert:
            classification = "R3_COMPETITIVE_ACCEPT"
        elif match_all and is_clean_b and is_clean_a:
            classification = "R3_DOWNGRADED_TO_COVERAGE"
        else:
            classification = "R3_REJECT"

        pilot_classifications[classification] += 1
        pilot_records.append({
            "question_id": qid,
            "fact_id": q["fact_id"],
            "classification": classification,
            "difficulty_a1": diff_a1,
            "difficulty_a2": diff_a2,
            "match_all_text": match_all,
            "decision_b": rb.get("decision")
        })

    print("\n--- PILOTO R3 EVALUATION REPORT (60 items) ---")
    for k, v in pilot_classifications.items():
        print(f"  {k}: {v}")
    print(f"A1 Difficulty Distribution: {dict(pilot_diff_a1)}")
    print(f"A2 Difficulty Distribution: {dict(pilot_diff_a2)}")

    pilot_report_path = ROOT / ".work" / "competitive-v16" / "piloto-r3" / "pilot-evaluation-report.json"
    pilot_report_path.write_text(json.dumps({
        "contract": "CB2026_PILOTO_R3_EVALUATION_REPORT_V1",
        "total_evaluated": len(pilot_authored),
        "classifications": dict(pilot_classifications),
        "difficulty_a1": dict(pilot_diff_a1),
        "difficulty_a2": dict(pilot_diff_a2),
        "records": pilot_records
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ----------------------------------------------------
    # 2. EVALUATE WAVE 3 R2 (240 items)
    # ----------------------------------------------------
    w3_authored = json.loads((ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "wave3_authored_corpus.json").read_text(encoding="utf-8"))
    
    w3_stage_a = {}
    for f in sorted(glob.glob(".work/competitive-v16/waves/wave3/stage-a/*/*.json")):
        items = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        for r in items:
            w3_stage_a[r["question_id"]] = r

    w3_stage_b = {}
    for f in sorted(glob.glob(".work/competitive-v16/waves/wave3/stage-b/*/*.json")):
        items = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        for r in items:
            w3_stage_b[r["question_id"]] = r

    w3_approved = []
    w3_evidence = []
    w3_classifications = Counter()

    for q in w3_authored:
        qid = q["id"]
        ra = w3_stage_a[qid]
        rb = w3_stage_b[qid]

        text_auth = q.get("correct_answer") or q["options"][q["correct_option"]]
        text_a = ra.get("selected_option_text")
        text_b = rb.get("selected_option_text")

        norm_auth = normalize_text(text_auth)
        norm_a = normalize_text(text_a)
        norm_b = normalize_text(text_b)

        text_match = (norm_auth == norm_a == norm_b)
        
        # Calculate Answer Binding
        binding_payload = {
            "presentation_sha256": q.get("presentation_sha256") or canonical_hash({"question_id": qid, "question": q["question"], "options": q["options"]}),
            "correct_answer": text_b,
            "source_ref": q["source_ref"],
            "source_quote": q["source_quote"]
        }
        rec_binding = canonical_hash(binding_payload)

        is_approved = (
            text_match and
            ra.get("recommendation") == "ACCEPT" and
            rb.get("decision") == "ACCEPT" and
            not rb.get("second_defensible_option", False) and
            not ra.get("length_or_precision_giveaway", False)
        )

        classification = "R2_COVERAGE_ACCEPT" if is_approved else "R2_REJECT"
        w3_classifications[classification] += 1

        if is_approved:
            # Build public question structure
            approved_q = {
                "id": qid,
                "fact_id": q["fact_id"],
                "role": "competitor_exam_bank_v13",
                "family": q.get("family", "single_choice_contextual"),
                "subtype": "contextual_meaning",
                "question": q["question"],
                "options": q["options"],
                "correct_option": q.get("correct_option", 0),
                "correct_answer": text_b,
                "accepted_answers": [text_b],
                "explanation": q.get("explanation", ""),
                "why_distractors_fail": q.get("why_distractors_fail", {}),
                "source_ref": q["source_ref"],
                "source_quote": q["source_quote"],
                "evidence_excerpt": q["source_quote"],
                "difficulty": ra.get("real_difficulty", "medium").lower(),
                "importance": "high",
                "relation_type": "temporal_sequence",
                "option_category": "historical_theological_context",
                "false_mutation": None,
                "blank_span": None,
                "significance": "essential",
                "variant_justification": f"Wave 3 R2 verified coverage for fact {q['fact_id']}",
                "blind_pool": "public_canonical_batch",
                "chapter": q.get("chapter", "DAN1"),
                "lane": "CARRIL_R2_COBERTURA",
                "tier": "COVERAGE_ACCEPT",
                "presentation_sha256": binding_payload["presentation_sha256"],
                "answer_binding_sha256": rec_binding,
                "ai_review": {
                    "reviewer": "ai-authoring-team",
                    "reviewer_type": "ai_semantic_audit",
                    "confidence_score": ra.get("confidence_0_100", 100) / 100.0,
                    "model": "gemini-2.5-pro",
                    "reviewed_at": "2026-09-01T20:00:00Z"
                }
            }
            w3_approved.append(approved_q)

        w3_evidence.append({
            "question_id": qid,
            "fact_id": q["fact_id"],
            "status": "PASS_STRICT" if is_approved else "FAIL",
            "text_match": text_match,
            "recommendation_a": ra.get("recommendation"),
            "decision_b": rb.get("decision"),
            "recalculated_binding": rec_binding
        })

    print("\n--- WAVE 3 R2 EVALUATION REPORT (240 items) ---")
    for k, v in w3_classifications.items():
        print(f"  {k}: {v}")

    w3_app_path = ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "wave3_approved_batch.json"
    w3_app_path.write_text(json.dumps(w3_approved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    w3_ev_path = ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "wave3_evaluation_evidence.json"
    w3_ev_path.write_text(json.dumps(w3_evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wave 3 approved batch written: {len(w3_approved)} items in {w3_app_path}")

if __name__ == "__main__":
    evaluate()
