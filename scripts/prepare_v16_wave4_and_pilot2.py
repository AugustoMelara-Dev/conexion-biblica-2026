#!/usr/bin/env python3
"""
Prepares dossiers for:
1. Carril A: Wave 4 R2 Cobertura (240 facts out of 1,007 remaining)
   - Stratified across all 18 chapters
   - Final IDs pre-assigned: V16-R2-{chapter}-W4-{idx:03d}
2. Carril B: Piloto R3 V2 (60 contrast items)
   - Rich contrast dossiers with 6-10 contrast facts strictly from Daniel 1-12 and PR 39-44
   - Complex cognitive operations
"""
from collections import Counter, defaultdict
import glob
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def prepare():
    # 1. Load canonical questions and units
    canonical_questions = {}
    for sf in sorted(glob.glob("content/competitive-v11/questions/*.json")):
        qs = json.loads(pathlib.Path(sf).read_text(encoding="utf-8"))
        for q in qs:
            canonical_questions[q["fact_id"]] = q

    source_packets_dir = ROOT / "content" / "competitive-v11" / "source-packets"
    source_units = {}
    for sf in sorted(source_packets_dir.glob("*.json")):
        if "excluded-units" in sf.name:
            continue
        sdata = json.loads(sf.read_text(encoding="utf-8"))
        for u in sdata.get("units", []):
            source_units[u["source_unit_id"]] = u

    # 2. Identify all approved R2 facts (Cycles 11 to 43 + Wave 1 + Wave 2 + Wave 3)
    approved_facts = set()
    for cycle_num in range(11, 44):
        cf = ROOT / "content" / "competitive-v13" / "release2" / "applied" / f"release2-reviewed-cycle{cycle_num}.json"
        if cf.exists():
            cdata = json.loads(cf.read_text(encoding="utf-8"))
            for it in cdata.get("approved", []):
                approved_facts.add(it["fact_id"])

    w1_app = json.loads(pathlib.Path("content/competitive-v13/wave1_approved_batch.json").read_text(encoding="utf-8"))
    for it in w1_app:
        approved_facts.add(it["fact_id"])
    w2_app = json.loads(pathlib.Path("content/competitive-v13/waves/wave2/wave2_approved_batch.json").read_text(encoding="utf-8"))
    for it in w2_app:
        approved_facts.add(it["fact_id"])
    w3_app = json.loads(pathlib.Path(".work/competitive-v16/waves/wave3/wave3_approved_batch.json").read_text(encoding="utf-8"))
    for it in w3_app:
        approved_facts.add(it["fact_id"])

    remaining_facts = [fid for fid in canonical_questions if fid not in approved_facts]
    print(f"Total canonical facts: {len(canonical_questions)}")
    print(f"Total approved R2 facts: {len(approved_facts)}")
    print(f"Remaining R2 facts: {len(remaining_facts)}")

    # Group remaining facts by chapter (18 chapters)
    def get_chapter(fid: str) -> str:
        parts = fid.split("-")
        return parts[0]

    remaining_by_chapter = defaultdict(list)
    for fid in remaining_facts:
        ch = get_chapter(fid)
        remaining_by_chapter[ch].append(fid)

    print("\nRemaining facts per chapter:")
    for ch in sorted(remaining_by_chapter.keys()):
        print(f"  {ch}: {len(remaining_by_chapter[ch])}")

    # ----------------------------------------------------
    # CARRIL A: Wave 4 R2 Selection (240 facts)
    # ----------------------------------------------------
    # Stratified selection allocating proportionally:
    # 1. Take all remaining Dan 7-12 facts
    # 2. Proportional allocation from PR 39-44 and Dan 1-6
    w4_selected_facts = []

    # Priority 1: Dan 7-12
    for num in range(7, 13):
        ch = f"DAN{num}"
        w4_selected_facts.extend(remaining_by_chapter[ch])

    dan_7_12_count = len(w4_selected_facts)
    print(f"\nWave 4 Dan 7-12 allocated: {dan_7_12_count}")

    # Priority 2: PR 39-44
    needed = 240 - dan_7_12_count
    pr_target = min(180, needed - 30) # leave at least 30 for Dan 1-6
    pr_selected = []
    for num in range(39, 45):
        ch = f"PR{num}"
        avail = remaining_by_chapter[ch]
        take = min(len(avail), pr_target // 6 + 5)
        pr_selected.extend(avail[:take])

    pr_selected = pr_selected[:pr_target]
    w4_selected_facts.extend(pr_selected)
    print(f"Wave 4 PR 39-44 allocated: {len(pr_selected)}")

    # Priority 3: Dan 1-6
    dan_1_6_needed = 240 - len(w4_selected_facts)
    dan_1_6_selected = []
    for num in range(1, 7):
        ch = f"DAN{num}"
        avail = remaining_by_chapter[ch]
        take = min(len(avail), dan_1_6_needed // 6 + 3)
        dan_1_6_selected.extend(avail[:take])

    # Fill up to exactly 240 if needed
    for num in range(1, 7):
        ch = f"DAN{num}"
        for fid in remaining_by_chapter[ch]:
            if fid not in w4_selected_facts and len(w4_selected_facts) < 240:
                w4_selected_facts.append(fid)

    for num in range(39, 45):
        ch = f"PR{num}"
        for fid in remaining_by_chapter[ch]:
            if fid not in w4_selected_facts and len(w4_selected_facts) < 240:
                w4_selected_facts.append(fid)

    assert len(w4_selected_facts) == 240, f"Expected 240 facts for Wave 4, got {len(w4_selected_facts)}"
    assert len(set(w4_selected_facts)) == 240, "Duplicate fact selected in Wave 4"

    # Save Wave 4 dossiers (8 batches of 30 items) with pre-assigned final IDs
    w4_dir = ROOT / ".work" / "competitive-v16" / "waves" / "wave4" / "dossiers"
    w4_dir.mkdir(parents=True, exist_ok=True)

    w4_items = []
    for idx, fid in enumerate(w4_selected_facts):
        cq = canonical_questions[fid]
        su_id = cq.get("source_unit_id")
        su = source_units.get(su_id, {})
        ch = get_chapter(fid)
        qid = f"V16-R2-{ch}-W4-{idx+1:03d}"
        w4_items.append({
            "wave_index": idx + 1,
            "id": qid,
            "question_id": qid,
            "fact_id": fid,
            "chapter": ch,
            "source_unit_id": su_id,
            "source_ref": cq.get("source_ref"),
            "source_quote": cq.get("source_quote") or su.get("canonical_text", ""),
            "source_page": cq.get("source_page"),
            "family": "single_choice_contextual",
            "lane": "CARRIL_R2_COBERTURA",
            "previous_presentation": cq.get("question")
        })

    for b_idx in range(8):
        batch_slice = w4_items[b_idx*30 : (b_idx+1)*30]
        batch_file = w4_dir / f"batch_{b_idx+1}.json"
        batch_file.write_text(json.dumps({"dossiers": batch_slice}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Created Wave 4 R2 dossiers: 8 batches of 30 items in {w4_dir}")

    # ----------------------------------------------------
    # CARRIL B: Piloto R3 V2 Contrast Dossiers (60 items)
    # ----------------------------------------------------
    # 27 Dan 7-12, 18 PR 39-44, 15 Dan 1-6, 9 Translation Noise
    r3_v2_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3-v2" / "dossiers"
    r3_v2_dir.mkdir(parents=True, exist_ok=True)

    dan_7_12_all = [fid for fid in canonical_questions if any(fid.startswith(f"DAN{num}-") for num in range(7, 13))]
    pr_39_44_all = [fid for fid in canonical_questions if any(fid.startswith(f"PR{num}-") for num in range(39, 45))]
    dan_1_6_all = [fid for fid in canonical_questions if any(fid.startswith(f"DAN{num}-") for num in range(1, 7))]

    # Select 60 primary facts (different from Pilot 1)
    p2_fids = dan_7_12_all[30:57] + pr_39_44_all[30:48] + dan_1_6_all[30:45]
    assert len(p2_fids) == 60, f"Expected 60 primary facts for Pilot 2, got {len(p2_fids)}"

    # Operations: pairing, sequence, attribution, chapter/year/river, PR vs Bible
    operations = [
        "cross_passage_fact_pairing",
        "chronological_event_sequence",
        "speaker_recipient_intermediary_attribution",
        "vision_year_monarch_river_correlation",
        "biblical_text_vs_prophets_and_kings_contrast",
        "cause_condition_consequence_chain"
    ]

    p2_items = []
    noise_indices = {3, 9, 16, 23, 31, 38, 44, 51, 58}

    for idx, fid in enumerate(p2_fids):
        cq = canonical_questions[fid]
        su_id = cq.get("source_unit_id")
        su = source_units.get(su_id, {})
        ch = get_chapter(fid)
        qid = f"V16-R3-PILOT2-{ch}-{idx+1:03d}"
        op = operations[idx % len(operations)]
        is_noise = idx in noise_indices

        # Find 6-10 contrast facts from the same book/material
        pool = dan_7_12_all if ch.startswith("DAN") and int(ch.replace("DAN","")) >= 7 else (
            pr_39_44_all if ch.startswith("PR") else dan_1_6_all
        )
        contrast_fids = [c_fid for c_fid in pool if c_fid != fid][:8]
        contrast_facts = []
        for c_fid in contrast_fids:
            ccq = canonical_questions[c_fid]
            contrast_facts.append({
                "fact_id": c_fid,
                "chapter": get_chapter(c_fid),
                "source_ref": ccq.get("source_ref"),
                "source_quote": ccq.get("source_quote") or ccq.get("evidence_excerpt", ""),
                "brief_description": ccq.get("question")
            })

        p2_items.append({
            "pilot_index": idx + 1,
            "id": qid,
            "question_id": qid,
            "primary_fact_id": fid,
            "chapter": ch,
            "source_unit_id": su_id,
            "primary_source_ref": cq.get("source_ref"),
            "primary_source_quote": cq.get("source_quote") or su.get("canonical_text", ""),
            "cognitive_operation": op,
            "translation_noise": is_noise,
            "target_difficulty": "EXPERT" if is_noise or "contrast" in op else "HARD",
            "contrast_facts": contrast_facts
        })

    # Save Pilot 2 dossiers (2 batches of 30 items)
    (r3_v2_dir / "pilot2_batch_1.json").write_text(json.dumps({"dossiers": p2_items[:30]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (r3_v2_dir / "pilot2_batch_2.json").write_text(json.dumps({"dossiers": p2_items[30:]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created Piloto R3 V2 Contrast Dossiers: 2 batches of 30 items in {r3_v2_dir}")

if __name__ == "__main__":
    prepare()
