#!/usr/bin/env python3
"""
Promote Wave 2 approved items into sequential append-only cycles (Cycles 28 to 35).
Chains lineage hashes from Cycle 27 to maintain strict historical lineage integrity.
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import canonical_hash

APPLIED_DIR = ROOT / "content" / "competitive-v13" / "release2" / "applied"
WAVE2_APPROVED_PATH = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "wave2_approved_batch.json"

def promote_wave2():
    wave2_items = json.loads(WAVE2_APPROVED_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(wave2_items)} Wave 2 approved items.")

    current_manifest_path = APPLIED_DIR / "release2-reviewed-current.json"
    current_manifest = json.loads(current_manifest_path.read_text(encoding="utf-8"))
    
    cumulative_approved = list(current_manifest["approved"])
    last_cycle_num = current_manifest.get("cycle_number", 27)
    last_cycle_hash = current_manifest.get("current_cycle_hash", "")
    print(f"Current lineage: Cycle {last_cycle_num}, cumulative approved: {len(cumulative_approved)}")

    # Chunk into 8 cycles of 30 items
    chunk_size = 30
    chunks = [wave2_items[i:i + chunk_size] for i in range(0, len(wave2_items), chunk_size)]
    print(f"Partitioned into {len(chunks)} new cycles.")

    for idx, chunk in enumerate(chunks, 1):
        cycle_num = last_cycle_num + idx
        cycle_file = APPLIED_DIR / f"release2-reviewed-cycle{cycle_num}.json"

        # Transform chunk into canonical approved rows
        cycle_approved_rows = []
        for q in chunk:
            row = {
                "id": q["id"],
                "lane": q.get("lane", "CARRIL_R2_COBERTURA"),
                "fact_id": q["fact_id"],
                "source_unit_id": q["source_unit_id"],
                "question": q["question"],
                "options": q["options"],
                "correct_option": q["correct_option"],
                "correct_answer": q["correct_answer"],
                "accepted_answers": q.get("accepted_answers", [q["correct_answer"]]),
                "why_distractors_fail": q["why_distractors_fail"],
                "explanation": q["explanation"],
                "source_ref": q["source_ref"],
                "source_quote": q["source_quote"],
                "parent_context": q.get("parent_context"),
                "family": q.get("family", "single_choice_contextual"),
                "subtype": q.get("subtype", "relationship"),
                "difficulty": q.get("difficulty", "medium"),
                "tier": q.get("tier", "COVERAGE_ACCEPT"),
                "presentation_sha256": q["presentation_sha256"],
                "answer_binding_sha256": q["answer_binding_sha256"],
                "evaluation": q.get("evaluation", {})
            }
            cycle_approved_rows.append(row)

        cumulative_approved.extend(cycle_approved_rows)

        cycle_payload = {
            "cycle_number": cycle_num,
            "previous_cycle_hash": last_cycle_hash,
            "approved_in_this_cycle": len(cycle_approved_rows),
            "total_approved_cumulative": len(cumulative_approved),
            "approved": cycle_approved_rows
        }
        cycle_hash = canonical_hash(cycle_payload)
        cycle_payload["cycle_hash"] = cycle_hash

        cycle_file.write_text(json.dumps(cycle_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Written Cycle {cycle_num}: {len(cycle_approved_rows)} items (cumulative {len(cumulative_approved)}), hash={cycle_hash[:12]}...")

        last_cycle_hash = cycle_hash

    # Update current manifests
    current_manifest["cycle_number"] = last_cycle_num + len(chunks)
    current_manifest["total_approved_cumulative"] = len(cumulative_approved)
    current_manifest["approved_count"] = len(cumulative_approved)
    current_manifest["current_cycle_hash"] = last_cycle_hash
    current_manifest["approved"] = cumulative_approved

    current_manifest_path.write_text(json.dumps(current_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    
    safe_manifest_path = APPLIED_DIR / "release2-reviewed-safe-current.json"
    safe_manifest_path.write_text(json.dumps(current_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {current_manifest_path} and safe manifest to Cycle {current_manifest['cycle_number']} ({len(cumulative_approved)} total approved).")

if __name__ == "__main__":
    promote_wave2()
