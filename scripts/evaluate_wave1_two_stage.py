#!/usr/bin/env python3
"""
Wave 1 Two-Stage Review Reconciler & Cryptographic Verification Script
"""
import json
import os
import sys

def run_evaluation():
    authored_path = "content/competitive-v13/wave1_authored_corpus.json"
    stage_a_path = "content/competitive-v13/wave1_stage_a_all.json"
    stage_b_path = "content/competitive-v13/wave1_stage_b_all.json"

    # Extract reviews from subagent transcripts if not present
    if not os.path.exists(stage_a_path) or not os.path.exists(stage_b_path):
        import re
        subagent_logs = {
            "A1": r"C:\Users\melar\.gemini\antigravity\brain\7d664a6b-6cf7-4604-be44-77ec9443e21e\.system_generated\logs\transcript_full.jsonl",
            "A2": r"C:\Users\melar\.gemini\antigravity\brain\6a95b081-aa67-4a27-ad86-962e543c7bf5\.system_generated\logs\transcript_full.jsonl",
            "A3": r"C:\Users\melar\.gemini\antigravity\brain\e8a35fc6-beb2-4eaf-b93e-b377165b3ed6\.system_generated\logs\transcript_full.jsonl",
            "A4": r"C:\Users\melar\.gemini\antigravity\brain\33d39bd4-738d-443b-be1c-39a6dfbbb398\.system_generated\logs\transcript_full.jsonl",
            "B1": r"C:\Users\melar\.gemini\antigravity\brain\97be8c93-ee28-43b3-b2c5-75ab69450cea\.system_generated\logs\transcript_full.jsonl",
            "B2": r"C:\Users\melar\.gemini\antigravity\brain\82e797d5-75f4-49ca-8215-06ad0bdca966\.system_generated\logs\transcript_full.jsonl",
            "B3": r"C:\Users\melar\.gemini\antigravity\brain\7ee6e265-4551-46ba-82d8-a3f641be3064\.system_generated\logs\transcript_full.jsonl",
            "B4": r"C:\Users\melar\.gemini\antigravity\brain\c2a70a56-0dd9-4562-a65f-93d2cdfdc0df\.system_generated\logs\transcript_full.jsonl",
        }
        
        def extract_json(log_path):
            if not os.path.exists(log_path):
                return None
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                    for tc in data.get("tool_calls", []):
                        if tc.get("name") == "send_message":
                            msg = tc.get("args", {}).get("Message", "")
                            match = re.search(r"\[\s*\{.*\}\s*\]", msg, re.DOTALL)
                            if match:
                                try:
                                    return json.loads(match.group(0))
                                except:
                                    pass
                    content = data.get("content", "")
                    match = re.search(r"\[\s*\{.*\}\s*\]", content, re.DOTALL)
                    if match:
                        try:
                            return json.loads(match.group(0))
                        except:
                            pass
                except:
                    pass
            return None

        stage_a = []
        for k in ["A1", "A2", "A3", "A4"]:
            res = extract_json(subagent_logs[k])
            if res:
                stage_a.extend(res)
        with open(stage_a_path, "w", encoding="utf-8") as f:
            json.dump(stage_a, f, ensure_ascii=False, indent=2)

        stage_b = []
        for k in ["B1", "B2", "B3", "B4"]:
            res = extract_json(subagent_logs[k])
            if res:
                stage_b.extend(res)
        with open(stage_b_path, "w", encoding="utf-8") as f:
            json.dump(stage_b, f, ensure_ascii=False, indent=2)

    with open(authored_path, "r", encoding="utf-8") as f:
        raw_authored = json.load(f)
    with open(stage_a_path, "r", encoding="utf-8") as f:
        stage_a_reviews = json.load(f)
    with open(stage_b_path, "r", encoding="utf-8") as f:
        stage_b_reviews = json.load(f)

    if isinstance(raw_authored, dict):
        authored_map = raw_authored
    else:
        authored_map = {q["question_id"]: q for q in raw_authored}

    stage_a_map = {r["question_id"]: r for r in stage_a_reviews}
    stage_b_map = {r["question_id"]: r for r in stage_b_reviews}

    print(f"Authored corpus items: {len(authored_map)}")
    print(f"Stage A review items: {len(stage_a_map)}")
    print(f"Stage B review items: {len(stage_b_map)}")

    reconciled_items = []
    stats = {
        "COMPETITIVE_ACCEPT": 0,
        "COVERAGE_ACCEPT": 0,
        "REWRITE": 0,
        "REJECT": 0,
        "hash_verification_passed": 0,
        "hash_verification_failed": 0,
        "giveaways_detected": 0
    }

    for qid, q in authored_map.items():
        eval_a = stage_a_map.get(qid)
        eval_b = stage_b_map.get(qid)

        if not eval_a or not eval_b:
            print(f"Missing review for {qid}: A={bool(eval_a)}, B={bool(eval_b)}")
            continue

        pres_a_match = eval_a.get("presentation_sha256") == q["presentation_sha256"]
        pres_b_match = eval_b.get("presentation_sha256") == q["presentation_sha256"]
        bind_b_match = eval_b.get("answer_binding_sha256") == q["answer_binding_sha256"]

        if pres_a_match and pres_b_match and bind_b_match:
            stats["hash_verification_passed"] += 1
        else:
            stats["hash_verification_failed"] += 1
            print(f"Hash mismatch for {qid}: PresA={pres_a_match}, PresB={pres_b_match}, BindB={bind_b_match}")

        has_giveaway = eval_a.get("length_or_precision_giveaway", False)
        if has_giveaway:
            stats["giveaways_detected"] += 1

        b_decision = eval_b.get("decision", "").upper()
        second_def = eval_b.get("second_defensible_option", False)
        a_diff = eval_a.get("real_difficulty", "MEDIUM").upper()

        if b_decision == "ACCEPT" and not second_def and not has_giveaway:
            if a_diff in ["HARD", "EXPERT"]:
                final_decision = "COMPETITIVE_ACCEPT"
                final_tier = "HARD" if a_diff == "HARD" else "EXPERT"
            else:
                final_decision = "COVERAGE_ACCEPT"
                final_tier = a_diff if a_diff in ["EASY", "MEDIUM"] else "MEDIUM"
        elif b_decision == "REWRITE" or has_giveaway:
            final_decision = "REWRITE"
            final_tier = a_diff
        else:
            final_decision = "REJECT"
            final_tier = a_diff

        stats[final_decision] += 1

        reconciled_q = dict(q)
        reconciled_q["tier"] = final_tier
        reconciled_q["difficulty"] = final_tier
        reconciled_q["evaluation"] = {
            "decision": final_decision,
            "stage_a": eval_a,
            "stage_b": eval_b,
            "hash_verified": pres_a_match and pres_b_match and bind_b_match
        }
        reconciled_items.append(reconciled_q)

    print("\n--- RECONCILIATION AND AUDIT SUMMARY ---")
    print(f"Total processed: {len(reconciled_items)}")
    print(f"Hash verifications passed: {stats['hash_verification_passed']}/{len(reconciled_items)}")
    print(f"COMPETITIVE_ACCEPT: {stats['COMPETITIVE_ACCEPT']}")
    print(f"COVERAGE_ACCEPT: {stats['COVERAGE_ACCEPT']}")
    print(f"REWRITE: {stats['REWRITE']}")
    print(f"REJECT: {stats['REJECT']}")
    print(f"Giveaways detected: {stats['giveaways_detected']}")

    evidence_path = "content/competitive-v13/wave1_evaluation_evidence.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": stats,
            "items": reconciled_items
        }, f, ensure_ascii=False, indent=2)
    print(f"\nSaved evaluation evidence to {evidence_path}")

    approved_items = [
        item for item in reconciled_items
        if item["evaluation"]["decision"] in ["COMPETITIVE_ACCEPT", "COVERAGE_ACCEPT"]
    ]
    approved_path = "content/competitive-v13/wave1_approved_batch.json"
    with open(approved_path, "w", encoding="utf-8") as f:
        json.dump(approved_items, f, ensure_ascii=False, indent=2)
    print(f"Saved approved batch ({len(approved_items)} items) to {approved_path}")

if __name__ == "__main__":
    run_evaluation()
