import json
import pathlib

p3 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_3.json').read_text(encoding='utf-8'))
p4 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_4.json').read_text(encoding='utf-8'))
all_packets_q = {q['question_id']: q for q in (p3['questions'] + p4['questions'])}

res = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/stage-b/reviewer_b2/packet_3_4.json').read_text(encoding='utf-8'))

print(f"Total reviews in output: {len(res)}")
assert len(res) == 60, f"Expected 60 reviews, got {len(res)}"

required_fields = [
    'question_id', 'presentation_sha256', 'selected_option_index',
    'selected_option_text', 'exact_supporting_phrase',
    'second_defensible_option', 'second_defensible_text',
    'distractor_analysis', 'semantic_category_check',
    'novelty_check', 'decision', 'specific_reason'
]

for idx, r in enumerate(res):
    qid = r['question_id']
    assert qid in all_packets_q, f"Unknown question_id {qid}"
    src_q = all_packets_q[qid]
    
    # Check required fields
    for f in required_fields:
        assert f in r, f"{qid}: missing field {f}"
        
    # Check SHA
    assert r['presentation_sha256'] == src_q['presentation_sha256'], f"{qid}: SHA mismatch"
    
    # Check index and text
    sel_idx = r['selected_option_index']
    assert 0 <= sel_idx < 4, f"{qid}: invalid index {sel_idx}"
    assert r['selected_option_text'] == src_q['options'][sel_idx], f"{qid}: option text mismatch"
    
    # Check phrase
    phrase = r['exact_supporting_phrase']
    assert phrase in src_q['source_quote'], f"{qid}: phrase '{phrase}' not in quote '{src_q['source_quote']}'"
    
    # Check distractors
    dist = r['distractor_analysis']
    expected_keys = {f'option_{i}' for i in range(4) if i != sel_idx}
    assert set(dist.keys()) == expected_keys, f"{qid}: distractor keys mismatch"
    
    # Check decision
    assert r['decision'] in ['ACCEPT', 'REWRITE', 'REJECT'], f"{qid}: invalid decision"
    assert r['semantic_category_check'] in ['EXCELLENT', 'GOOD', 'POOR']
    assert isinstance(r['novelty_check'], bool)
    assert isinstance(r['second_defensible_option'], bool)

print("ALL 60 VERDICTS FULLY AUDITED AND VERIFIED WITH 100% SUCCESS!")
