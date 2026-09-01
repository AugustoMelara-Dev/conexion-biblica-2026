import json
import pathlib

path = pathlib.Path(".work/competitive-v16/waves/wave3/authors/author_2/batch_2.json")
items = json.loads(path.read_text(encoding="utf-8"))

print(f"Total items: {len(items)}")
assert len(items) == 30, f"Expected 30 items, got {len(items)}"

options_dist = [0, 0, 0, 0]
for idx, it in enumerate(items):
    opts = it["options"]
    c_idx = it["correct_option"]
    options_dist[c_idx] += 1
    lens = [len(o) for o in opts]
    ratio = max(lens) / min(lens)
    assert ratio < 1.15, f"Item {it['id']} ratio {ratio:.3f} >= 1.15 (lengths: {lens})"
    assert len(opts) == 4, f"Item {it['id']} must have 4 options"
    assert len(set(opts)) == 4, f"Item {it['id']} has duplicate options"
    assert it["correct_answer"] == opts[c_idx], f"Item {it['id']} mismatch correct_answer"
    assert it["correct_answer"] in it["accepted_answers"], f"Item {it['id']} accepted_answers error"
    for i, o in enumerate(opts):
        if i == c_idx:
            assert o not in it["why_distractors_fail"], f"Item {it['id']} correct answer in distractors"
        else:
            assert o in it["why_distractors_fail"], f"Item {it['id']} missing distractor '{o}'"
            assert len(it["why_distractors_fail"][o].strip()) > 10, f"Item {it['id']} distractor explanation too short"
    assert len(it["explanation"].strip()) > 15, f"Item {it['id']} explanation too short"
    assert len(it["question"].strip()) > 10, f"Item {it['id']} question too short"

print("All 30 items passed all strict validations!")
print("Distribution of correct_option:", options_dist)
