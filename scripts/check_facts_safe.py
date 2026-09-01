import json, pathlib
from collections import Counter

ROOT = pathlib.Path(".")
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"

frozen_corpus = json.loads((evidence_dir / "frozen_reviewed_corpus.json").read_text(encoding="utf-8"))
classification = json.loads((evidence_dir / "honest_classification.json").read_text(encoding="utf-8"))

safe_ids = classification["COMPETITIVE_ACCEPT"] + classification["COVERAGE_ACCEPT"]
safe_questions = [frozen_corpus[qid] for qid in safe_ids]

fact_counts = Counter(q["fact_id"] for q in safe_questions)
dup_facts = {f: c for f, c in fact_counts.items() if c > 1}
print(f"Total safe questions: {len(safe_questions)}")
print(f"Unique facts covered: {len(fact_counts)}")
print(f"Duplicate facts among safe questions: {len(dup_facts)}")
if dup_facts:
    print("Examples of duplicate facts:", list(dup_facts.items())[:5])
