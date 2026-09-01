import json, pathlib, sys
ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.lib.competitive_v13 import normalize_prompt
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"

frozen_corpus = json.loads((evidence_dir / "frozen_reviewed_corpus.json").read_text(encoding="utf-8"))
classification = json.loads((evidence_dir / "honest_classification.json").read_text(encoding="utf-8"))

safe_ids = classification["COMPETITIVE_ACCEPT"] + classification["COVERAGE_ACCEPT"]
safe_questions = [frozen_corpus[qid] for qid in safe_ids]

# Base prompts
base_prompts = set()
for f in (ROOT / "content" / "competitive-v11" / "questions").glob("*.json"):
    for q in json.loads(f.read_text(encoding="utf-8")):
        base_prompts.add(normalize_prompt(q.get("question", "")))

# Already approved in cycles 11-15
applied_current = json.loads((ROOT / "content" / "competitive-v13" / "release2" / "applied" / "release2-reviewed-cycle15.json").read_text(encoding="utf-8"))
for q in applied_current.get("approved", []):
    base_prompts.add(normalize_prompt(q.get("question", "")))

collisions = []
for q in safe_questions:
    p = normalize_prompt(q.get("question", ""))
    if p in base_prompts:
        collisions.append((q["id"], q["question"]))

print(f"Total safe questions: {len(safe_questions)}")
print(f"Prompt collisions with base/prior approved: {len(collisions)}")
for cid, prompt in collisions[:10]:
    print(f"  {cid}: {prompt}")
