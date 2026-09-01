import json, pathlib

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"

frozen_corpus = json.loads((evidence_dir / "frozen_reviewed_corpus.json").read_text(encoding="utf-8"))

for sf in staging_dir.glob("*.json"):
    data = json.loads(sf.read_text(encoding="utf-8"))
    restored = []
    for q in data:
        qid = q["id"]
        if qid in frozen_corpus:
            restored.append(frozen_corpus[qid])
        else:
            restored.append(q)
    sf.write_text(json.dumps(restored, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print("Staging files restored to EXACT reviewed corpus.")
