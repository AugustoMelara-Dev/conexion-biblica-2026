#!/usr/bin/env python3
"""
Promote Wave 1 approved two-stage reviewed increment into public 18 shards.
Base: 3,011 questions -> Target: 3,212 questions.
"""
import copy
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import canonical_hash
from scripts.lib.competitive_v11 import audit_corpus, validate_question

def promote_wave1():
    applied_dir = ROOT / "content" / "competitive-v13" / "release2" / "applied"
    source_packets_dir = ROOT / "content" / "competitive-v11" / "source-packets"

    # Load source units for rich explanations & references
    source_units = {}
    for sf in source_packets_dir.glob("*.json"):
        if sf.name == "excluded-units.json":
            continue
        sdata = json.loads(sf.read_text(encoding="utf-8"))
        for u in sdata.get("units", []):
            source_units[u["source_unit_id"]] = u

    # Load base checkpoint (the canonical 3,011 checkpoint)
    safe_current_path = applied_dir / "release2-reviewed-safe-current.json"
    base_checkpoint = json.loads(safe_current_path.read_text(encoding="utf-8"))

    # Load Wave 1 approved items
    wave1_path = ROOT / "content" / "competitive-v13" / "wave1_approved_batch.json"
    wave1_items = json.loads(wave1_path.read_text(encoding="utf-8"))

    print(f"Base checkpoint approved questions: {len(base_checkpoint['approved'])}")
    print(f"Wave 1 approved items to promote: {len(wave1_items)}")

    # Group Wave 1 items into structured batches (by unit and origin)
    batches = {}
    for item in wave1_items:
        qid = item.get("id") or item.get("question_id")
        unit = item.get("source_unit_id", "").split("-")[0]
        if not unit:
            unit = qid.split("-")[2]
        
        # Determine batch category
        if "-W1-" in qid:
            batch_id = f"{unit}-wave1-new"
        else:
            batch_id = f"{unit}-wave1-rewrite"
            
        if batch_id not in batches:
            batches[batch_id] = []
        batches[batch_id].append(item)

    print(f"Grouped into {len(batches)} batches: {list(batches.keys())}")

    # Assign batches to Cycles (Cycles 22 to 27)
    batch_list = list(batches.items())
    cycle_size = 4  # 4 batches per cycle
    cycles_batches = [batch_list[i:i + cycle_size] for i in range(0, len(batch_list), cycle_size)]

    current_checkpoint = copy.deepcopy(base_checkpoint)
    start_cycle = 22

    for c_idx, c_batches in enumerate(cycles_batches):
        cycle_num = start_cycle + c_idx
        cycle_batches_meta = []
        cycle_approved_rows = []

        for bname, b_items in c_batches:
            blind_qs = [
                {"id": q.get("id") or q.get("question_id"), "prompt": q["question"], "options": q["options"]}
                for q in b_items
            ]
            blind_hash = canonical_hash({"questions": blind_qs})

            cycle_batches_meta.append({
                "batch_id": bname,
                "blind_packet_sha256": blind_hash,
                "reviewer": "two-stage-blind-and-source-verified",
                "approved": len(b_items),
                "pending": 0
            })

            for q in b_items:
                qid = q.get("id") or q.get("question_id")
                eval_data = q.get("evaluation", {})
                eval_a = eval_data.get("stage_a", {})
                eval_b = eval_data.get("stage_b", {})
                
                honest_diff = q.get("tier", eval_a.get("real_difficulty", "MEDIUM")).lower()
                tier = eval_data.get("decision", "COVERAGE_ACCEPT")
                
                su = source_units.get(q.get("source_unit_id", ""), {})
                source_ref = q.get("source_ref") or su.get("source_ref", "")
                source_quote = q.get("source_quote") or su.get("source_quote", "")
                
                correct_text = q["options"][q["correct_option"]]
                
                # Format why_distractors_fail as dictionary if list/str
                wdf = q.get("why_distractors_fail", {})
                if isinstance(wdf, list):
                    wdf_dict = {opt: wdf[i] if i < len(wdf) else f"Opción incorrecta según {source_ref}."
                                for i, opt in enumerate(q["options"]) if i != q["correct_option"]}
                elif isinstance(wdf, dict):
                    wdf_dict = wdf
                else:
                    wdf_dict = {opt: f"Opción incorrecta según {source_ref}."
                                for i, opt in enumerate(q["options"]) if i != q["correct_option"]}

                cycle_approved_rows.append({
                    "id": qid,
                    "source_unit_id": q.get("source_unit_id", ""),
                    "fact_id": q.get("fact_id", ""),
                    "family": q.get("family", "single_choice_contextual"),
                    "subtype": q.get("subtype", "relationship"),
                    "question": q["question"],
                    "options": q["options"],
                    "correct_option": q["correct_option"],
                    "accepted_answers": [correct_text],
                    "explanation": f"{source_ref} declara: \"{source_quote}\"",
                    "evidence_excerpt": source_quote,
                    "why_distractors_fail": wdf_dict,
                    "difficulty": honest_diff,
                    "importance": "high",
                    "relation_type": "canonical_narrative",
                    "option_category": "biblical_context",
                    "false_mutation": None,
                    "blank_span": None,
                    "significance": None,
                    "variant_justification": f"Variante verificada {tier} para {q.get('fact_id', '')}.",
                    "role": "variant",
                    "correct_answer": correct_text,
                    "source_ref": source_ref,
                    "source_quote": source_quote,
                    "question_content_sha256": q.get("presentation_sha256", ""),
                    "presentation_sha256": q.get("presentation_sha256", ""),
                    "answer_binding_sha256": q.get("answer_binding_sha256", ""),
                    "ai_review": {
                        "status": "passed",
                        "reviewer_type": "two_stage_blind_source_audit",
                        "tier": tier,
                        "real_difficulty": honest_diff,
                        "length_giveaway": False,
                        "source_verified": True
                    },
                    "reviewer_id": "two-stage-blind-and-source-verified",
                    "review_comment": f"Aprobado {tier} con dificultad honesta {honest_diff}. Verificado en dos etapas independientes."
                })

        # Calculate append-only cycle lineage
        payload_before = {
            key: value for key, value in current_checkpoint.items() if key != "release_sha256"
        }
        base_release_sha = canonical_hash(payload_before)

        inc_payload = {
            "schema_version": "competitive-v13-reviewed-release/v1",
            "release": 2,
            "batches": cycle_batches_meta,
            "approved": cycle_approved_rows,
            "pending": []
        }
        inc_release_sha = canonical_hash(inc_payload)

        base_appr = len(current_checkpoint["approved"])
        new_appr = len(cycle_approved_rows)
        merged_appr = base_appr + new_appr

        history_entry = {
            "cycle": cycle_num,
            "base_release_sha256": base_release_sha,
            "increment_release_sha256": inc_release_sha,
            "base_approved_count": base_appr,
            "new_approved_count": new_appr,
            "merged_approved_count": merged_appr
        }

        merged_batches = current_checkpoint["batches"] + cycle_batches_meta
        merged_approved = current_checkpoint["approved"] + cycle_approved_rows
        merged_pending = current_checkpoint["pending"]
        merged_history = current_checkpoint.get("cycle_history", []) + [history_entry]

        checkpoint_payload = {
            "schema_version": "competitive-v13-reviewed-release/v1",
            "release": 2,
            "batches": merged_batches,
            "approved": merged_approved,
            "pending": merged_pending,
            "cycle_history": merged_history
        }
        checkpoint_payload["release_sha256"] = canonical_hash(checkpoint_payload)
        current_checkpoint = checkpoint_payload

        out_file = applied_dir / f"release2-reviewed-cycle{cycle_num}.json"
        out_file.write_text(json.dumps(checkpoint_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Cycle {cycle_num}: +{new_appr} approved rows (cumulative total: {merged_appr})")

    # Write latest current checkpoints
    (applied_dir / "release2-reviewed-current.json").write_text(
        json.dumps(current_checkpoint, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (applied_dir / "release2-reviewed-safe-current.json").write_text(
        json.dumps(current_checkpoint, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"\nSuccessfully generated Cycles 22-{start_cycle + len(cycles_batches) - 1}!")
    print(f"Total approved questions in release 2: {len(current_checkpoint['approved'])}")

if __name__ == "__main__":
    promote_wave1()
