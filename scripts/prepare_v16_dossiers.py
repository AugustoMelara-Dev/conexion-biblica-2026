#!/usr/bin/env python3
"""
Prepares dossiers for:
1. Carril B: Piloto R3 (60 candidates):
   - 27 Dan 7-12, 18 PR 39-44, 15 Dan 1-6
   - 27 Single Choice, 18 Complete, 15 True/False
   - 9 Translation Noise
2. Carril A: Wave 3 R2 Cobertura (240 facts):
   - Stratified from the 1,247 remaining facts (Dan 7-12, PR 39-44, Dan 1-6)
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

def prepare_dossiers():
    # 1. Load canonical facts and existing R2 approved facts
    ledger = json.loads((ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "closeout" / "r2-ledger-recomputed.json").read_text(encoding="utf-8"))
    
    source_packets_dir = ROOT / "content" / "competitive-v11" / "source-packets"
    source_units = {}
    for sf in sorted(source_packets_dir.glob("*.json")):
        if "excluded-units" in sf.name:
            continue
        sdata = json.loads(sf.read_text(encoding="utf-8"))
        for u in sdata.get("units", []):
            source_units[u["source_unit_id"]] = u

    # Load all canonical questions
    canonical_questions = {}
    for sf in sorted(glob.glob("content/competitive-v11/questions/*.json")):
        qs = json.loads(pathlib.Path(sf).read_text(encoding="utf-8"))
        for q in qs:
            canonical_questions[q["fact_id"]] = q

    # Load approved facts
    approved_facts = set()
    for cycle_num in range(11, 36):
        cf = ROOT / "content" / "competitive-v13" / "release2" / "applied" / f"release2-reviewed-cycle{cycle_num}.json"
        if cf.exists():
            cdata = json.loads(cf.read_text(encoding="utf-8"))
            for it in cdata.get("approved", []):
                approved_facts.add(it["fact_id"])

    # Load wave1 and wave2 approved
    w1_app = json.loads(pathlib.Path("content/competitive-v13/wave1_approved_batch.json").read_text(encoding="utf-8"))
    for it in w1_app:
        approved_facts.add(it["fact_id"])
    w2_app = json.loads(pathlib.Path("content/competitive-v13/waves/wave2/wave2_approved_batch.json").read_text(encoding="utf-8"))
    for it in w2_app:
        approved_facts.add(it["fact_id"])

    remaining_facts = [fid for fid in canonical_questions if fid not in approved_facts]
    print(f"Total canonical facts: {len(canonical_questions)}")
    print(f"Total approved R2 facts: {len(approved_facts)}")
    print(f"Total remaining facts for R2: {len(remaining_facts)}")

    # ----------------------------------------------------
    # CARRIL B: Piloto R3 (60 Candidates)
    # ----------------------------------------------------
    # Distribution: 27 Dan 7-12, 18 PR 39-44, 15 Dan 1-6
    # Families: 27 single_choice, 18 complete_sentence, 15 true_false
    # Translation noise: 9
    r3_pilot_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3" / "dossiers"
    r3_pilot_dir.mkdir(parents=True, exist_ok=True)

    def get_section(fid: str) -> str:
        for num in range(7, 13):
            if fid.startswith(f"DAN{num}-") or fid.startswith(f"DAN{num}_"):
                return "DAN_7_12"
        for num in range(39, 45):
            if fid.startswith(f"PR{num}-") or fid.startswith(f"PR{num}_"):
                return "PR_39_44"
        for num in range(1, 7):
            if fid.startswith(f"DAN{num}-") or fid.startswith(f"DAN{num}_"):
                return "DAN_1_6"
        return "OTHER"

    dan_7_12 = [fid for fid in canonical_questions if get_section(fid) == "DAN_7_12"]
    pr_39_44 = [fid for fid in canonical_questions if get_section(fid) == "PR_39_44"]
    dan_1_6 = [fid for fid in canonical_questions if get_section(fid) == "DAN_1_6"]

    pilot_fids = dan_7_12[:27] + pr_39_44[:18] + dan_1_6[:15]
    assert len(pilot_fids) == 60, f"Pilot fids count != 60 ({len(pilot_fids)})"

    # Assign families
    # 27 single_choice, 18 complete_sentence, 15 true_false
    families_plan = ["single_choice_contextual"] * 27 + ["complete_sentence_options"] * 18 + ["true_false_reason"] * 15
    # Assign translation noise (9 items: 4 in Dan 7-12, 3 in PR, 2 in Dan 1-6)
    noise_indices = {2, 7, 14, 21, 29, 36, 42, 48, 55}

    pilot_items = []
    for idx, fid in enumerate(pilot_fids):
        cq = canonical_questions[fid]
        su_id = cq.get("source_unit_id")
        su = source_units.get(su_id, {})
        qid = f"V16-R3-PILOT-{idx+1:03d}"
        family = families_plan[idx]
        is_noise = idx in noise_indices
        unit_prefix = su_id.split("-")[0] if su_id else "DAN1"
        pilot_items.append({
            "pilot_index": idx + 1,
            "id": qid,
            "question_id": qid,
            "fact_id": fid,
            "chapter": unit_prefix,
            "source_unit_id": su_id,
            "source_ref": cq.get("source_ref"),
            "source_quote": cq.get("source_quote") or su.get("canonical_text", ""),
            "source_page": cq.get("source_page"),
            "family": family,
            "translation_noise": is_noise,
            "target_difficulty": "EXPERT" if is_noise else "HARD",
            "previous_presentation": cq.get("question")
        })

    # Save pilot dossiers in 2 batches of 30 items
    pilot_b1 = pilot_items[:30]
    pilot_b2 = pilot_items[30:]
    (r3_pilot_dir / "pilot_batch_1.json").write_text(json.dumps({"dossiers": pilot_b1}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (r3_pilot_dir / "pilot_batch_2.json").write_text(json.dumps({"dossiers": pilot_b2}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created R3 Pilot dossiers: 2 batches of 30 items in {r3_pilot_dir}")

    # ----------------------------------------------------
    # CARRIL A: Wave 3 R2 Cobertura (240 Facts)
    # ----------------------------------------------------
    # Stratified from remaining_facts: 108 Dan 7-12, 72 PR 39-44, 60 Dan 1-6
    w3_dir = ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "dossiers"
    w3_dir.mkdir(parents=True, exist_ok=True)

    rem_dan_7_12 = [fid for fid in remaining_facts if get_section(fid) == "DAN_7_12"]
    rem_pr_39_44 = [fid for fid in remaining_facts if get_section(fid) == "PR_39_44"]
    rem_dan_1_6 = [fid for fid in remaining_facts if get_section(fid) == "DAN_1_6"]

    print(f"Remaining by section: Dan 7-12 = {len(rem_dan_7_12)}, PR 39-44 = {len(rem_pr_39_44)}, Dan 1-6 = {len(rem_dan_1_6)}")

    w3_fids = rem_dan_7_12[:73] + rem_pr_39_44[:107] + rem_dan_1_6[:60]
    assert len(w3_fids) == 240, f"Wave 3 FIDs count != 240 ({len(w3_fids)})"

    w3_items = []
    for idx, fid in enumerate(w3_fids):
        cq = canonical_questions[fid]
        su_id = cq.get("source_unit_id")
        su = source_units.get(su_id, {})
        qid = f"V16-R2-W3-{idx+1:03d}"
        unit_prefix = su_id.split("-")[0] if su_id else "DAN1"
        w3_items.append({
            "wave_index": idx + 1,
            "id": qid,
            "question_id": qid,
            "fact_id": fid,
            "chapter": unit_prefix,
            "source_unit_id": su_id,
            "source_ref": cq.get("source_ref"),
            "source_quote": cq.get("source_quote") or su.get("canonical_text", ""),
            "source_page": cq.get("source_page"),
            "family": "single_choice_contextual",
            "lane": "CARRIL_R2_COBERTURA",
            "previous_presentation": cq.get("question")
        })

    # Save Wave 3 dossiers in 8 batches of 30 items
    for b_idx in range(8):
        batch_slice = w3_items[b_idx*30 : (b_idx+1)*30]
        batch_file = w3_dir / f"batch_{b_idx+1}.json"
        batch_file.write_text(json.dumps({"dossiers": batch_slice}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Created Wave 3 R2 dossiers: 8 batches of 30 items in {w3_dir}")

if __name__ == "__main__":
    prepare_dossiers()
