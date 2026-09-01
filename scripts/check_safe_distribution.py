import json, pathlib
from collections import Counter

ROOT = pathlib.Path(".")
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"

frozen_corpus = json.loads((evidence_dir / "frozen_reviewed_corpus.json").read_text(encoding="utf-8"))
classification = json.loads((evidence_dir / "honest_classification.json").read_text(encoding="utf-8"))

safe_ids = set(classification["COMPETITIVE_ACCEPT"] + classification["COVERAGE_ACCEPT"])
safe_questions = [frozen_corpus[qid] for qid in safe_ids]

chapter_counts = Counter()
for q in safe_questions:
    chapter = q["id"].split("-")[2]
    chapter_counts[chapter] += 1

print(f"Total safe approved questions to promote: {len(safe_questions)}")
print("\nDistribution by Chapter:")
for ch, cnt in sorted(chapter_counts.items()):
    print(f"  {ch}: {cnt} questions")
