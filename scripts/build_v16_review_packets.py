#!/usr/bin/env python3
"""
Builds review packets for:
1. Carril B: Piloto R3 (60 items) -> Packets A1, Packets A2, Packets B
2. Carril A: Wave 3 R2 (240 items) -> Packets A, Packets B
Computes presentation_sha256 and answer_binding_sha256.
Ensures Stage B packets do NOT contain author answer binding.
"""
import glob
import json
import os
import pathlib
import random
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import canonical_hash

def build_packets():
    # ----------------------------------------------------
    # 1. Carril B: Piloto R3 (60 items)
    # ----------------------------------------------------
    pilot_author_files = [
        ROOT / ".work" / "competitive-v16" / "piloto-r3" / "authors" / "author_1" / "batch_1.json",
        ROOT / ".work" / "competitive-v16" / "piloto-r3" / "authors" / "author_2" / "batch_2.json",
    ]
    pilot_corpus = []
    for f in pilot_author_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("questions", data.get("dossiers", []))
        pilot_corpus.extend(items)

    assert len(pilot_corpus) == 60, f"Pilot corpus count != 60 ({len(pilot_corpus)})"
    (ROOT / ".work" / "competitive-v16" / "piloto-r3" / "pilot_authored_corpus.json").write_text(
        json.dumps(pilot_corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Directories for Piloto packets
    a1_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3" / "packets-a1"
    a2_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3" / "packets-a2"
    b_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3" / "packets-b"
    a1_dir.mkdir(parents=True, exist_ok=True)
    a2_dir.mkdir(parents=True, exist_ok=True)
    b_dir.mkdir(parents=True, exist_ok=True)

    # Generate Piloto A1, A2, B packets (2 batches of 30 items)
    for b_idx in range(2):
        batch_slice = pilot_corpus[b_idx*30 : (b_idx+1)*30]
        
        # A1 Packet (Permutation 1)
        a1_qs = []
        for q in batch_slice:
            opts = list(q["options"])
            rng = random.Random(f"pilot_a1_{q['id']}_seed")
            rng.shuffle(opts)
            pres_sha = canonical_hash({"question_id": q["id"], "question": q["question"], "options": opts})
            a1_qs.append({
                "question_id": q["id"],
                "presentation_sha256": pres_sha,
                "question": q["question"],
                "options": opts,
                "family": q.get("family"),
                "translation_noise": q.get("translation_noise", False)
            })
        (a1_dir / f"packet_{b_idx+1}.json").write_text(
            json.dumps({"questions": a1_qs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        # A2 Packet (Permutation 2)
        a2_qs = []
        for q in batch_slice:
            opts = list(q["options"])
            rng = random.Random(f"pilot_a2_{q['id']}_seed")
            rng.shuffle(opts)
            pres_sha = canonical_hash({"question_id": q["id"], "question": q["question"], "options": opts})
            a2_qs.append({
                "question_id": q["id"],
                "presentation_sha256": pres_sha,
                "question": q["question"],
                "options": opts,
                "family": q.get("family"),
                "translation_noise": q.get("translation_noise", False)
            })
        (a2_dir / f"packet_{b_idx+1}.json").write_text(
            json.dumps({"questions": a2_qs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        # B Packet (Permutation 3, Source, No Answer Binding)
        b_qs = []
        for q in batch_slice:
            opts = list(q["options"])
            rng = random.Random(f"pilot_b_{q['id']}_seed")
            rng.shuffle(opts)
            pres_sha = canonical_hash({"question_id": q["id"], "question": q["question"], "options": opts})
            b_qs.append({
                "question_id": q["id"],
                "presentation_sha256": pres_sha,
                "question": q["question"],
                "options": opts,
                "source_ref": q["source_ref"],
                "source_quote": q["source_quote"],
                "source_page": q.get("source_page"),
                "previous_public_presentation": q.get("previous_presentation")
            })
        (b_dir / f"packet_{b_idx+1}.json").write_text(
            json.dumps({"questions": b_qs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Created Piloto R3 Packets: A1, A2, B (60 items) in {ROOT / '.work' / 'competitive-v16' / 'piloto-r3'}")

    # ----------------------------------------------------
    # 2. Carril A: Wave 3 R2 Cobertura (240 items)
    # ----------------------------------------------------
    w3_corpus = []
    for i in range(1, 9):
        f = ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "authors" / f"author_{i}" / f"batch_{i}.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("questions", data.get("dossiers", []))
        w3_corpus.extend(items)

    assert len(w3_corpus) == 240, f"Wave 3 corpus count != 240 ({len(w3_corpus)})"
    (ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "wave3_authored_corpus.json").write_text(
        json.dumps(w3_corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    w3_a_dir = ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "packets-a"
    w3_b_dir = ROOT / ".work" / "competitive-v16" / "waves" / "wave3" / "packets-b"
    w3_a_dir.mkdir(parents=True, exist_ok=True)
    w3_b_dir.mkdir(parents=True, exist_ok=True)

    for b_idx in range(8):
        batch_slice = w3_corpus[b_idx*30 : (b_idx+1)*30]
        
        # Stage A Packet
        a_qs = []
        for q in batch_slice:
            opts = list(q["options"])
            rng = random.Random(f"w3_a_{q['id']}_seed")
            rng.shuffle(opts)
            pres_sha = canonical_hash({"question_id": q["id"], "question": q["question"], "options": opts})
            a_qs.append({
                "question_id": q["id"],
                "presentation_sha256": pres_sha,
                "question": q["question"],
                "options": opts
            })
        (w3_a_dir / f"packet_{b_idx+1}.json").write_text(
            json.dumps({"questions": a_qs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        # Stage B Packet
        b_qs = []
        for q in batch_slice:
            opts = list(q["options"])
            rng = random.Random(f"w3_b_{q['id']}_seed")
            rng.shuffle(opts)
            pres_sha = canonical_hash({"question_id": q["id"], "question": q["question"], "options": opts})
            b_qs.append({
                "question_id": q["id"],
                "presentation_sha256": pres_sha,
                "question": q["question"],
                "options": opts,
                "source_ref": q["source_ref"],
                "source_quote": q["source_quote"],
                "source_page": q.get("source_page"),
                "previous_public_presentation": q.get("previous_presentation")
            })
        (w3_b_dir / f"packet_{b_idx+1}.json").write_text(
            json.dumps({"questions": b_qs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Created Wave 3 R2 Packets: A and B (240 items) in {ROOT / '.work' / 'competitive-v16' / 'waves' / 'wave3'}")

if __name__ == "__main__":
    build_packets()
