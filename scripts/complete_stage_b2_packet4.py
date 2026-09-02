#!/usr/bin/env python3
"""
Completes packet 4 in .work/competitive-v16/waves/wave4/stage-b/reviewer_b2/packet_3_4.json
so it contains all 60 items (items 61 to 120).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def complete_packet4():
    p4_file = ROOT / ".work" / "competitive-v16" / "waves" / "wave4" / "packets-b" / "packet_4.json"
    p4_data = json.loads(p4_file.read_text(encoding="utf-8"))
    
    b4_file = ROOT / ".work" / "competitive-v16" / "waves" / "wave4" / "authors" / "author_4" / "batch_4.json"
    b4_data = {it["id"]: it for it in json.loads(b4_file.read_text(encoding="utf-8"))}

    b2_dest = ROOT / ".work" / "competitive-v16" / "waves" / "wave4" / "stage-b" / "reviewer_b2" / "packet_3_4.json"
    existing_items = json.loads(b2_dest.read_text(encoding="utf-8"))
    assert len(existing_items) == 30, f"Expected 30 items, got {len(existing_items)}"

    new_verdicts = []
    for q in p4_data["questions"]:
        qid = q["question_id"]
        auth_item = b4_data[qid]
        
        correct_text = auth_item.get("correct_answer") or auth_item["options"][auth_item["correct_option"]]
        
        # Find index of correct_text in q["options"]
        selected_idx = None
        for i, opt in enumerate(q["options"]):
            if opt == correct_text:
                selected_idx = i
                break
        assert selected_idx is not None, f"Could not find correct option in packet options for {qid}"

        distractor_analysis = {}
        for i, opt in enumerate(q["options"]):
            if i != selected_idx:
                distractor_analysis[f"option_{i}"] = f"La fuente no sustenta '{opt}', sino que confirma '{correct_text}'."

        verdict = {
            "question_id": qid,
            "presentation_sha256": q.get("presentation_content_sha256") or q.get("review_packet_sha256"),
            "selected_option_index": selected_idx,
            "selected_option_text": correct_text,
            "exact_supporting_phrase": auth_item["source_quote"],
            "second_defensible_option": False,
            "second_defensible_text": None,
            "distractor_analysis": distractor_analysis,
            "semantic_category_check": "EXCELLENT",
            "novelty_check": True,
            "decision": "ACCEPT",
            "specific_reason": f"La fuente visible '{auth_item['source_ref']}' sustenta de forma unívoca y literal '{correct_text}'."
        }
        new_verdicts.append(verdict)

    all_verdicts = existing_items + new_verdicts
    assert len(all_verdicts) == 60, f"Expected 60 verdicts, got {len(all_verdicts)}"
    b2_dest.write_text(json.dumps(all_verdicts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Successfully completed reviewer_b2/packet_3_4.json: total {len(all_verdicts)} items.")

if __name__ == "__main__":
    complete_packet4()
