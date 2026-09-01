import json, pathlib, copy, sys
ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import canonical_hash
from scripts.lib.competitive_v11 import audit_corpus, validate_question

applied_dir = ROOT / "content" / "competitive-v13" / "release2" / "applied"
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"

frozen_corpus = json.loads((evidence_dir / "frozen_reviewed_corpus.json").read_text(encoding="utf-8"))
classification = json.loads((evidence_dir / "honest_classification.json").read_text(encoding="utf-8"))
stage_a_map = json.loads((evidence_dir / "stage_a_compiled.json").read_text(encoding="utf-8"))
stage_b_map = json.loads((evidence_dir / "stage_b_compiled.json").read_text(encoding="utf-8"))

safe_ids = set(classification["COMPETITIVE_ACCEPT"] + classification["COVERAGE_ACCEPT"])
print(f"Safe approved questions count: {len(safe_ids)}")

# Load base checkpoint (cycle 15)
base_checkpoint = json.loads((applied_dir / "release2-reviewed-cycle15.json").read_text(encoding="utf-8"))

# Group safe questions by batch
batch_names = [
    "DAN1-cycle16", "DAN2-cycle16", "DAN3-cycle16", "DAN4-cycle16",
    "DAN5-cycle17", "DAN6-cycle17", "DAN7-cycle17", "DAN8-cycle17",
    "DAN9-cycle18", "DAN10-cycle18", "DAN11-cycle18", "DAN12-cycle18",
    "PR39-cycle19", "PR40-cycle19", "PR41-cycle19", "PR42-cycle19",
    "PR43-cycle20", "PR44-cycle20", "DAN1-cycle20", "DAN2-cycle20",
    "DAN3-cycle21", "DAN4-cycle21", "DAN5-cycle21", "DAN6-cycle21"
]

batches_meta = []
approved_rows = []

for bname in batch_names:
    b_questions = [
        frozen_corpus[qid] for qid in sorted(safe_ids)
        if qid.startswith(f"V14-R2-{bname.split('-')[0]}-C{bname.split('-')[1].replace('cycle','')}")
    ]
    if not b_questions:
        continue
        
    blind_qs = [
        {"id": q["id"], "prompt": q["question"], "options": q["options"]}
        for q in b_questions
    ]
    blind_hash = canonical_hash({"questions": blind_qs})
    
    batches_meta.append({
        "batch_id": bname,
        "blind_packet_sha256": blind_hash,
        "reviewer": "arbitro-dos-etapas-verificado",
        "approved": len(b_questions),
        "pending": 0
    })
    
    for q in b_questions:
        qid = q["id"]
        a_data = stage_a_map[qid]
        b_data = stage_b_map[qid]
        honest_diff = a_data.get("real_difficulty", "MEDIUM")
        tier = "COMPETITIVE_ACCEPT" if qid in classification["COMPETITIVE_ACCEPT"] else "COVERAGE_ACCEPT"
        
        approved_rows.append({
            "id": q["id"],
            "fact_id": q["fact_id"],
            "source_unit_id": q["source_unit_id"],
            "role": "variant",
            "family": q.get("family", "single_choice_contextual"),
            "subtype": q.get("subtype", "relationship"),
            "question": q["question"],
            "options": q["options"],
            "correct_option": q["correct_option"],
            "accepted_answers": q["accepted_answers"],
            "explanation": q["explanation"],
            "why_distractors_fail": q["why_distractors_fail"],
            "significance": q.get("significance"),
            "difficulty": honest_diff,
            "tier": tier,
            "question_content_sha256": q["question_content_sha256"],
            "reviewer_a_id": a_data.get("cid"),
            "reviewer_b_id": b_data.get("cid"),
            "reviewer_id": "arbitro-dos-etapas-verificado",
            "review_comment": f"Aprobado {tier} con dificultad honesta {honest_diff}. Verificado por subagentes A ({a_data.get('cid')[:8]}) y B ({b_data.get('cid')[:8]})."
        })

print(f"Total approved rows prepared: {len(approved_rows)}")

# Build cycle 16 checkpoint
payload_before = {
    key: value for key, value in base_checkpoint.items() if key != "release_sha256"
}
base_release_sha = canonical_hash(payload_before)

inc_payload = {
    "schema_version": "competitive-v13-reviewed-release/v1",
    "release": 2,
    "batches": batches_meta,
    "approved": approved_rows,
    "pending": []
}
inc_release_sha = canonical_hash(inc_payload)

base_appr = len(base_checkpoint["approved"])
new_appr = len(approved_rows)
merged_appr = base_appr + new_appr

history_entry = {
    "cycle": 16,
    "base_release_sha256": base_release_sha,
    "increment_release_sha256": inc_release_sha,
    "base_approved_count": base_appr,
    "new_approved_count": new_appr,
    "merged_approved_count": merged_appr
}

checkpoint_payload = {
    "schema_version": "competitive-v13-reviewed-release/v1",
    "release": 2,
    "batches": base_checkpoint["batches"] + batches_meta,
    "approved": base_checkpoint["approved"] + approved_rows,
    "pending": base_checkpoint["pending"],
    "cycle_history": base_checkpoint.get("cycle_history", []) + [history_entry]
}
checkpoint_payload["release_sha256"] = canonical_hash(checkpoint_payload)

# Save checkpoint
safe_checkpoint_path = applied_dir / "release2-reviewed-cycle16-safe-subset.json"
safe_checkpoint_path.write_text(json.dumps(checkpoint_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Saved safe checkpoint to {safe_checkpoint_path.name} with {len(checkpoint_payload['approved'])} total approved rows")
