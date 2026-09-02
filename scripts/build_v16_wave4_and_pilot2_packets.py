#!/usr/bin/env python3
"""
Builds review packets for:
1. Wave 4 R2: Packets A (blind resolution) and Packets B (textual auditor)
2. Piloto R3 V2: Packets A1 (Blind 1), Packets A2 (Blind 2, independent shuffle), and Packets B (Textual Auditor with contrast facts)
Pre-calculates presentation_content_sha256 and review_packet_sha256.
"""
import glob
import json
import os
import pathlib
import random
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

def compute_presentation_content_sha256(question_text: str, options: list, fact_id: str, source_unit_id: str) -> str:
    norm_q = normalize_text(question_text)
    norm_opts = sorted([normalize_text(opt) for opt in options])
    payload = {
        "contract": "CB2026_PRESENTATION_CONTENT_SHA256_V1",
        "question": norm_q,
        "options_multiset": norm_opts,
        "fact_id": fact_id,
        "source_unit_id": source_unit_id
    }
    return canonical_hash(payload)

def compute_review_packet_sha256(reviewed_original_id: str, options_received: list, pres_content_sha: str, stage: str) -> str:
    payload = {
        "contract": "CB2026_REVIEW_PACKET_SHA256_V1",
        "reviewed_original_id": reviewed_original_id,
        "options_received": options_received,
        "presentation_content_sha256": pres_content_sha,
        "stage": stage
    }
    return canonical_hash(payload)

def build_packets():
    # ----------------------------------------------------
    # 1. WAVE 4 R2 PACKETS (240 questions)
    # ----------------------------------------------------
    w4_author_files = sorted(glob.glob(".work/competitive-v16/waves/wave4/authors/author_*/batch_*.json"))
    if len(w4_author_files) == 8:
        w4_items = []
        for af in w4_author_files:
            items = json.loads(pathlib.Path(af).read_text(encoding="utf-8"))
            w4_items.extend(items)

        if len(w4_items) == 240:
            (ROOT / ".work" / "competitive-v16" / "waves" / "wave4" / "wave4_authored_corpus.json").write_text(
                json.dumps(w4_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            pkt_a_dir = ROOT / ".work" / "competitive-v16" / "waves" / "wave4" / "packets-a"
            pkt_b_dir = ROOT / ".work" / "competitive-v16" / "waves" / "wave4" / "packets-b"
            pkt_a_dir.mkdir(parents=True, exist_ok=True)
            pkt_b_dir.mkdir(parents=True, exist_ok=True)

            for b_idx in range(8):
                batch_slice = w4_items[b_idx*30 : (b_idx+1)*30]
                batch_a = []
                batch_b = []

                for item in batch_slice:
                    qid = item["id"]
                    fid = item["fact_id"]
                    suid = item["source_unit_id"]
                    q_text = item["question"]
                    orig_opts = list(item["options"])

                    pres_sha = compute_presentation_content_sha256(q_text, orig_opts, fid, suid)

                    # Shuffle for Stage A
                    rng_a = random.Random(f"w4_a_{qid}")
                    opts_a = list(orig_opts)
                    rng_a.shuffle(opts_a)
                    pkt_sha_a = compute_review_packet_sha256(qid, opts_a, pres_sha, "A")

                    # Shuffle for Stage B
                    rng_b = random.Random(f"w4_b_{qid}")
                    opts_b = list(orig_opts)
                    rng_b.shuffle(opts_b)
                    pkt_sha_b = compute_review_packet_sha256(qid, opts_b, pres_sha, "B")

                    batch_a.append({
                        "question_id": qid,
                        "question": q_text,
                        "options": opts_a,
                        "presentation_content_sha256": pres_sha,
                        "review_packet_sha256": pkt_sha_a
                    })

                    batch_b.append({
                        "question_id": qid,
                        "fact_id": fid,
                        "source_ref": item["source_ref"],
                        "source_quote": item["source_quote"],
                        "question": q_text,
                        "options": opts_b,
                        "presentation_content_sha256": pres_sha,
                        "review_packet_sha256": pkt_sha_b
                    })

                (pkt_a_dir / f"packet_{b_idx+1}.json").write_text(
                    json.dumps({"contract": "CB2026_STAGE_A_REVIEW_PACKET_V1", "batch_index": b_idx+1, "questions": batch_a}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8"
                )
                (pkt_b_dir / f"packet_{b_idx+1}.json").write_text(
                    json.dumps({"contract": "CB2026_STAGE_B_REVIEW_PACKET_V1", "batch_index": b_idx+1, "questions": batch_b}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8"
                )
            print(f"Wave 4 review packets created: 8 in packets-a, 8 in packets-b")

    # ----------------------------------------------------
    # 2. PILOTO R3 V2 PACKETS (60 questions)
    # ----------------------------------------------------
    p2_author_files = sorted(glob.glob(".work/competitive-v16/piloto-r3-v2/authors/author_*/batch_*.json"))
    if len(p2_author_files) == 2:
        p2_items = []
        for af in p2_author_files:
            items = json.loads(pathlib.Path(af).read_text(encoding="utf-8"))
            p2_items.extend(items)

        if len(p2_items) == 60:
            (ROOT / ".work" / "competitive-v16" / "piloto-r3-v2" / "pilot2_authored_corpus.json").write_text(
                json.dumps(p2_items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            pkt_a1_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3-v2" / "packets-a1"
            pkt_a2_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3-v2" / "packets-a2"
            pkt_b_dir = ROOT / ".work" / "competitive-v16" / "piloto-r3-v2" / "packets-b"
            pkt_a1_dir.mkdir(parents=True, exist_ok=True)
            pkt_a2_dir.mkdir(parents=True, exist_ok=True)
            pkt_b_dir.mkdir(parents=True, exist_ok=True)

            for b_idx in range(2):
                batch_slice = p2_items[b_idx*30 : (b_idx+1)*30]
                batch_a1 = []
                batch_a2 = []
                batch_b = []

                for item in batch_slice:
                    qid = item["id"]
                    fid = item.get("primary_fact_id") or item["fact_id"]
                    suid = item.get("source_unit_id", "")
                    q_text = item["question"]
                    orig_opts = list(item["options"])

                    pres_sha = compute_presentation_content_sha256(q_text, orig_opts, fid, suid)

                    # Shuffle A1
                    rng_a1 = random.Random(f"p2_a1_{qid}")
                    opts_a1 = list(orig_opts)
                    rng_a1.shuffle(opts_a1)
                    pkt_sha_a1 = compute_review_packet_sha256(qid, opts_a1, pres_sha, "A1")

                    # Shuffle A2 (different seed)
                    rng_a2 = random.Random(f"p2_a2_{qid}_alt")
                    opts_a2 = list(orig_opts)
                    rng_a2.shuffle(opts_a2)
                    pkt_sha_a2 = compute_review_packet_sha256(qid, opts_a2, pres_sha, "A2")

                    # Shuffle B
                    rng_b = random.Random(f"p2_b_{qid}")
                    opts_b = list(orig_opts)
                    rng_b.shuffle(opts_b)
                    pkt_sha_b = compute_review_packet_sha256(qid, opts_b, pres_sha, "B")

                    batch_a1.append({
                        "question_id": qid,
                        "question": q_text,
                        "options": opts_a1,
                        "presentation_content_sha256": pres_sha,
                        "review_packet_sha256": pkt_sha_a1
                    })

                    batch_a2.append({
                        "question_id": qid,
                        "question": q_text,
                        "options": opts_a2,
                        "presentation_content_sha256": pres_sha,
                        "review_packet_sha256": pkt_sha_a2
                    })

                    batch_b.append({
                        "question_id": qid,
                        "primary_fact_id": fid,
                        "primary_source_ref": item.get("primary_source_ref") or item.get("source_ref"),
                        "primary_source_quote": item.get("primary_source_quote") or item.get("source_quote"),
                        "cognitive_operation": item.get("cognitive_operation", "contrast"),
                        "contrast_facts": item.get("contrast_facts", []),
                        "question": q_text,
                        "options": opts_b,
                        "presentation_content_sha256": pres_sha,
                        "review_packet_sha256": pkt_sha_b
                    })

                (pkt_a1_dir / f"packet_{b_idx+1}.json").write_text(
                    json.dumps({"contract": "CB2026_PILOT_R3_STAGE_A1_PACKET_V1", "batch_index": b_idx+1, "questions": batch_a1}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8"
                )
                (pkt_a2_dir / f"packet_{b_idx+1}.json").write_text(
                    json.dumps({"contract": "CB2026_PILOT_R3_STAGE_A2_PACKET_V1", "batch_index": b_idx+1, "questions": batch_a2}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8"
                )
                (pkt_b_dir / f"packet_{b_idx+1}.json").write_text(
                    json.dumps({"contract": "CB2026_PILOT_R3_STAGE_B_PACKET_V1", "batch_index": b_idx+1, "questions": batch_b}, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8"
                )
            print(f"Piloto R3 V2 review packets created: 2 in packets-a1, 2 in packets-a2, 2 in packets-b")

if __name__ == "__main__":
    build_packets()
