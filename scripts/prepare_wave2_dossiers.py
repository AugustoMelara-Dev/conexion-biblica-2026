#!/usr/bin/env python3
"""
Prepare stratified Wave 2 dossiers (240 total items):
- Carril R2 Cobertura (160 items): 72 Dan 7-12, 48 PR 39-44, 40 Dan 1-6
- Carril R3 Competitivo Temprano (80 items): 48 Dan 7-12, 24 PR 39-44, 8 Dan 1-6
"""
import glob
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def prepare_wave2():
    dossier_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "dossiers"
    authors_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "authors"
    stage_a_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "stage-a"
    stage_b_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "stage-b"

    dossier_dir.mkdir(parents=True, exist_ok=True)
    authors_dir.mkdir(parents=True, exist_ok=True)
    stage_a_dir.mkdir(parents=True, exist_ok=True)
    stage_b_dir.mkdir(parents=True, exist_ok=True)

    # Load source units
    source_units = {}
    for sf in sorted(glob.glob("content/competitive-v11/source-packets/*.json")):
        if "excluded-units" in sf:
            continue
        sdata = json.loads(pathlib.Path(sf).read_text(encoding="utf-8"))
        for u in sdata.get("units", []):
            source_units[u["source_unit_id"]] = u

    # Load base questions and map fact_id -> question / source
    base_questions = {}
    for sf in sorted(glob.glob("content/competitive-v11/questions/*.json")):
        qs = json.loads(pathlib.Path(sf).read_text(encoding="utf-8"))
        for q in qs:
            base_questions[q["fact_id"]] = q

    # Load approved R2 facts
    applied_current = json.loads(pathlib.Path("content/competitive-v13/release2/applied/release2-reviewed-current.json").read_text(encoding="utf-8"))
    approved_r2_facts = {q["fact_id"] for q in applied_current["approved"]}

    all_base_facts = set(base_questions.keys())
    remaining_r2_facts = all_base_facts - approved_r2_facts

    # Stratify remaining R2 facts
    dan_1_6 = [fid for fid in sorted(remaining_r2_facts) if fid.split("-")[0] in [f"DAN{i}" for i in range(1, 7)]]
    dan_7_12 = [fid for fid in sorted(remaining_r2_facts) if fid.split("-")[0] in [f"DAN{i}" for i in range(7, 13)]]
    pr_39_44 = [fid for fid in sorted(remaining_r2_facts) if fid.split("-")[0] in [f"PR{i}" for i in range(39, 45)]]

    # Select Carril R2 (160 facts)
    r2_dan7_12 = dan_7_12[:72]
    r2_pr = pr_39_44[:48]
    r2_dan1_6 = dan_1_6[:40]
    r2_selected_facts = r2_dan7_12 + r2_pr + r2_dan1_6

    # Select Carril R3 Competitivo (80 facts)
    # High-risk chapters in Dan 7-12: Dan 8, 9, 10, 11, 12 and sequences in Dan 7
    r3_pool_dan7_12 = [fid for fid in dan_7_12 if fid not in r2_dan7_12]
    if len(r3_pool_dan7_12) < 48:
        # If pool has fewer, take from all dan 7-12
        r3_pool_dan7_12 = [fid for fid in sorted(all_base_facts) if fid.split("-")[0] in [f"DAN{i}" for i in range(7, 13)] and fid not in r2_selected_facts]
    r3_dan7_12 = r3_pool_dan7_12[:48]

    r3_pool_pr = [fid for fid in pr_39_44 if fid not in r2_pr]
    r3_pr = r3_pool_pr[:24]

    r3_pool_dan1_6 = [fid for fid in dan_1_6 if fid not in r2_dan1_6]
    r3_dan1_6 = r3_pool_dan1_6[:8]

    r3_selected_facts = r3_dan7_12 + r3_pr + r3_dan1_6

    print(f"Carril R2 Cobertura selected: {len(r2_selected_facts)} (Dan7-12: {len(r2_dan7_12)}, PR: {len(r2_pr)}, Dan1-6: {len(r2_dan1_6)})")
    print(f"Carril R3 Competitivo selected: {len(r3_selected_facts)} (Dan7-12: {len(r3_dan7_12)}, PR: {len(r3_pr)}, Dan1-6: {len(r3_dan1_6)})")
    print(f"Total Wave 2 candidates: {len(r2_selected_facts) + len(r3_selected_facts)}")

    # Build dossiers items
    dossier_items = []
    
    # Add R2 items
    for idx, fid in enumerate(r2_selected_facts, 1):
        base_q = base_questions[fid]
        su = source_units.get(base_q["source_unit_id"], {})
        ch = fid.split("-")[0]
        qid = f"V14-R2-{ch}-W2-{idx:03d}"
        dossier_items.append({
            "id": qid,
            "lane": "CARRIL_R2_COBERTURA",
            "fact_id": fid,
            "source_unit_id": base_q["source_unit_id"],
            "chapter": ch,
            "source_ref": base_q.get("source_ref") or su.get("source_ref", ""),
            "source_quote": base_q.get("source_quote") or su.get("source_quote", ""),
            "parent_context": su.get("parent_context"),
            "previous_base_presentation": {
                "question": base_q.get("question"),
                "correct_answer": base_q.get("correct_answer"),
                "options": base_q.get("options")
            },
            "target_tier": "COVERAGE_ACCEPT"
        })

    # Add R3 items
    for idx, fid in enumerate(r3_selected_facts, 1):
        base_q = base_questions[fid]
        su = source_units.get(base_q["source_unit_id"], {})
        ch = fid.split("-")[0]
        qid = f"V14-R3-{ch}-W2-{idx:03d}"
        dossier_items.append({
            "id": qid,
            "lane": "CARRIL_R3_COMPETITIVO_TEMPRANO",
            "fact_id": fid,
            "source_unit_id": base_q["source_unit_id"],
            "chapter": ch,
            "source_ref": base_q.get("source_ref") or su.get("source_ref", ""),
            "source_quote": base_q.get("source_quote") or su.get("source_quote", ""),
            "parent_context": su.get("parent_context"),
            "previous_base_presentation": {
                "question": base_q.get("question"),
                "correct_answer": base_q.get("correct_answer"),
                "options": base_q.get("options")
            },
            "target_tier": "COMPETITIVE_ACCEPT"
        })

    # Partition into 8 author batches of 30 items
    batch_size = 30
    for b_idx in range(8):
        batch_items = dossier_items[b_idx * batch_size : (b_idx + 1) * batch_size]
        batch_file = dossier_dir / f"batch_{b_idx + 1}.json"
        batch_payload = {
            "batch_id": f"batch_{b_idx + 1}",
            "agent_id": f"author_{b_idx + 1}",
            "total_items": len(batch_items),
            "dossiers": batch_items
        }
        batch_file.write_text(json.dumps(batch_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Written dossier {batch_file.name} with {len(batch_items)} items.")

if __name__ == "__main__":
    prepare_wave2()
