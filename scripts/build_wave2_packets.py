#!/usr/bin/env python3
"""
Build Wave 2 packets from direct author files:
1. Validates all author output files with fail-closed checks (AUTHOR_OUTPUT_INVALID).
2. Shuffles options deterministically.
3. Computes presentation_sha256 and answer_binding_sha256.
4. Generates Stage A packets (blind, no answers) and Stage B packets (textual, without author answer binding).
5. Packages into 8 packets of 30 questions for 4 Stage A reviewers and 4 Stage B reviewers.
"""
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

def build_wave2_packets():
    authors_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "authors"
    packets_a_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "packets-a"
    packets_b_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "packets-b"

    packets_a_dir.mkdir(parents=True, exist_ok=True)
    packets_b_dir.mkdir(parents=True, exist_ok=True)

    all_authored = []
    author_files = sorted(glob.glob(f"{authors_dir}/*/*.json"))

    print(f"Found {len(author_files)} author files.")

    for fpath in author_files:
        data = json.loads(pathlib.Path(fpath).read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("questions", data.get("dossiers", []))
        for item in items:
            # Strict schema validation (Fail-closed)
            qid = item.get("id") or item.get("question_id")
            if not qid:
                raise ValueError(f"AUTHOR_OUTPUT_INVALID: missing id in {fpath}")
            
            question_text = item.get("question")
            if not question_text or not isinstance(question_text, str) or not question_text.strip():
                raise ValueError(f"AUTHOR_OUTPUT_INVALID: missing question text for {qid}")

            options = item.get("options")
            if not options or not isinstance(options, list) or len(options) != 4:
                raise ValueError(f"AUTHOR_OUTPUT_INVALID: options must be list of 4 for {qid}")

            correct_idx = item.get("correct_option")
            if correct_idx is None or not isinstance(correct_idx, int) or not (0 <= correct_idx < 4):
                raise ValueError(f"AUTHOR_OUTPUT_INVALID: invalid correct_option for {qid}")

            correct_text = options[correct_idx]
            stated_answer = item.get("correct_answer", correct_text)
            if normalize_text(correct_text) != normalize_text(stated_answer):
                raise ValueError(f"AUTHOR_OUTPUT_INVALID: options[correct_option] != correct_answer for {qid}")

            why_dist = item.get("why_distractors_fail")
            if not why_dist or not isinstance(why_dist, dict) or len(why_dist) < 3:
                raise ValueError(f"AUTHOR_OUTPUT_INVALID: why_distractors_fail must be dict with at least 3 entries for {qid}")

            source_ref = item.get("source_ref")
            source_quote = item.get("source_quote")
            if not source_ref or not source_quote:
                raise ValueError(f"AUTHOR_OUTPUT_INVALID: missing source_ref or source_quote for {qid}")

            # Deterministic option shuffle based on question ID
            seed_val = sum(ord(c) for c in qid)
            indices = list(range(4))
            # Knuth shuffle
            for i in range(3, 0, -1):
                j = (seed_val * (i + 1) + 7) % (i + 1)
                indices[i], indices[j] = indices[j], indices[i]
                seed_val = (seed_val * 31 + 17) & 0xFFFFFFFF

            shuffled_options = [options[idx] for idx in indices]
            new_correct_idx = indices.index(correct_idx)

            # Cryptographic bindings
            pres_payload = {
                "question_id": qid,
                "question": question_text,
                "options": shuffled_options
            }
            pres_sha256 = canonical_hash(pres_payload)

            bind_payload = {
                "presentation_sha256": pres_sha256,
                "correct_answer": correct_text,
                "source_ref": source_ref,
                "source_quote": source_quote
            }
            bind_sha256 = canonical_hash(bind_payload)

            item_copy = dict(item)
            item_copy["id"] = qid
            item_copy["question_id"] = qid
            item_copy["options"] = shuffled_options
            item_copy["correct_option"] = new_correct_idx
            item_copy["correct_answer"] = correct_text
            item_copy["presentation_sha256"] = pres_sha256
            item_copy["answer_binding_sha256"] = bind_sha256

            all_authored.append(item_copy)

    print(f"Total validated authored questions: {len(all_authored)}")

    # Save compiled authored corpus
    corpus_path = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "wave2_authored_corpus.json"
    corpus_path.write_text(json.dumps(all_authored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved compiled authored corpus to {corpus_path}")

    # Partition into 8 packets of 30 questions
    batch_size = 30
    for p_idx in range(8):
        pkt_items = all_authored[p_idx * batch_size : (p_idx + 1) * batch_size]
        if not pkt_items:
            continue

        # Stage A packet (Blind: only question, options, id, presentation_sha256)
        pkt_a = {
            "packet_id": f"wave2_packet_{p_idx + 1}",
            "total_questions": len(pkt_items),
            "questions": [
                {
                    "question_id": q["id"],
                    "presentation_sha256": q["presentation_sha256"],
                    "question": q["question"],
                    "options": q["options"]
                }
                for q in pkt_items
            ]
        }
        pkt_a_path = packets_a_dir / f"packet_{p_idx + 1}.json"
        pkt_a_path.write_text(json.dumps(pkt_a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Stage B packet (Textual Source: question, options, source_ref, source_quote, WITHOUT author answer binding)
        pkt_b = {
            "packet_id": f"wave2_packet_{p_idx + 1}",
            "total_questions": len(pkt_items),
            "questions": [
                {
                    "question_id": q["id"],
                    "presentation_sha256": q["presentation_sha256"],
                    "question": q["question"],
                    "options": q["options"],
                    "fact_id": q["fact_id"],
                    "source_unit_id": q["source_unit_id"],
                    "source_ref": q["source_ref"],
                    "source_quote": q["source_quote"],
                    "parent_context": q.get("parent_context")
                }
                for q in pkt_items
            ]
        }
        pkt_b_path = packets_b_dir / f"packet_{p_idx + 1}.json"
        pkt_b_path.write_text(json.dumps(pkt_b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        print(f"Generated Packet {p_idx + 1} with {len(pkt_items)} questions (Stage A & Stage B).")

if __name__ == "__main__":
    build_wave2_packets()
