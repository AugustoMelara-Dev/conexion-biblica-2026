import json, pathlib, hashlib
from collections import Counter

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
stage_a_dir = ROOT / "content" / "competitive-v13" / "stage-a-packets"
stage_b_dir = ROOT / "content" / "competitive-v13" / "stage-b-packets"
evidence_dir = ROOT / "content" / "competitive-v13" / "two-stage-audit-evidence"

stage_a_map = json.loads((evidence_dir / "stage_a_compiled.json").read_text(encoding="utf-8"))
stage_b_map = json.loads((evidence_dir / "stage_b_compiled.json").read_text(encoding="utf-8"))

def compute_content_sha256(q: dict) -> str:
    payload = {
        "question": q["question"],
        "options": q["options"],
        "correct_option": q["correct_option"],
        "fact_id": q["fact_id"],
        "source_unit_id": q["source_unit_id"],
    }
    dumped = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()

stage_b_questions = {}
for pfile in sorted(stage_b_dir.glob("*.json")):
    pdata = json.loads(pfile.read_text(encoding="utf-8"))
    for q in pdata.get("questions", []):
        stage_b_questions[q["question_id"]] = q

stage_a_questions = {}
for pfile in sorted(stage_a_dir.glob("*.json")):
    pdata = json.loads(pfile.read_text(encoding="utf-8"))
    for q in pdata.get("questions", []):
        stage_a_questions[q["question_id"]] = q

staging_meta = {}
for sf in sorted(staging_dir.glob("*.json")):
    data = json.loads(sf.read_text(encoding="utf-8"))
    for q in data:
        staging_meta[q["id"]] = q

exact_reviewed_corpus = {}
for qid, q_stage_b in stage_b_questions.items():
    meta = staging_meta[qid]
    b_eval = stage_b_map[qid]
    adj_opt_idx = b_eval["adjudicated_option"]
    correct_text = q_stage_b["options"][adj_opt_idx]
    
    q_obj = {
        "id": qid,
        "fact_id": meta["fact_id"],
        "source_unit_id": q_stage_b["source_unit_id"],
        "role": meta.get("role", "variant"),
        "family": meta.get("family", "single_choice_contextual"),
        "subtype": meta.get("subtype", "relationship"),
        "question": q_stage_b["question"],
        "options": q_stage_b["options"],
        "correct_option": adj_opt_idx,
        "accepted_answers": [correct_text],
        "explanation": f"{q_stage_b.get('source_ref', '')} declara: \"{q_stage_b.get('source_quote', '')}\"",
        "why_distractors_fail": {
            opt: f"Opción incorrecta según {q_stage_b.get('source_ref', '')}."
            for i, opt in enumerate(q_stage_b["options"]) if i != adj_opt_idx
        },
        "significance": None
    }
    q_obj["question_content_sha256"] = compute_content_sha256(q_obj)
    exact_reviewed_corpus[qid] = q_obj

print(f"Total exact reviewed questions reconstructed: {len(exact_reviewed_corpus)}")

# Classify each question
classification = {
    "COMPETITIVE_ACCEPT": [],
    "COVERAGE_ACCEPT": [],
    "REWRITE": [],
    "REJECT": []
}

diff_counter = Counter()
giveaway_counter = Counter()

for qid, q in exact_reviewed_corpus.items():
    a_eval = stage_a_map[qid]
    b_eval = stage_b_map[qid]
    
    # 1. Answer alignment
    q_a = stage_a_questions[qid]
    chosen_opt_a_text = q_a["options"][a_eval["chosen_option"]]
    chosen_opt_b_text = q["options"][b_eval["adjudicated_option"]]
    
    answer_match = (chosen_opt_a_text == chosen_opt_b_text)
    second_defensible = b_eval.get("second_defensible_option", False)
    giveaway = a_eval.get("length_or_precision_giveaway", False)
    diff_a = a_eval.get("real_difficulty", "MEDIUM")
    diff_counter[diff_a] += 1
    
    if giveaway:
        giveaway_counter["giveaway_true"] += 1
    else:
        giveaway_counter["giveaway_false"] += 1
        
    # Decision logic as commanded by USER
    if not answer_match or second_defensible or b_eval.get("decision") == "REJECT":
        classification["REJECT"].append(qid)
    elif giveaway or b_eval.get("decision") == "REWRITE":
        classification["REWRITE"].append(qid)
    elif diff_a in ["HARD", "EXPERT"]:
        classification["COMPETITIVE_ACCEPT"].append(qid)
    else: # diff_a in ["EASY", "MEDIUM"]
        classification["COVERAGE_ACCEPT"].append(qid)

print("\n--- CLASIFICACIÓN HONESTA DE LAS 240 PREGUNTAS REVISADAS ---")
print(f"COMPETITIVE_ACCEPT (HARD/EXPERT real, sin giveaway, respaldo exacto): {len(classification['COMPETITIVE_ACCEPT'])}")
print(f"COVERAGE_ACCEPT (EASY/MEDIUM real por simplicidad del hecho, sin giveaway, respaldo exacto): {len(classification['COVERAGE_ACCEPT'])}")
print(f"REWRITE (Giveaway detectado por Stage A o distractores débiles para IA): {len(classification['REWRITE'])}")
print(f"REJECT (Ambigua, defecto factual o segunda opción): {len(classification['REJECT'])}")

safe_subset = classification["COMPETITIVE_ACCEPT"] + classification["COVERAGE_ACCEPT"]
print(f"\nTOTAL SUBCONJUNTO SEGURO APROBADO: {len(safe_subset)}")

print("\nDesglose de Dificultad Real de Etapa A en todo el lote:")
for d, cnt in sorted(diff_counter.items()):
    print(f"  {d}: {cnt} ({(cnt/240)*100:.1f}%)")

print("\nPistas de Longitud/Precisión detectadas por Etapa A:")
print(f"  Con Giveaway: {giveaway_counter['giveaway_true']}")
print(f"  Sin Giveaway: {giveaway_counter['giveaway_false']}")

# Save frozen evidence
(evidence_dir / "frozen_reviewed_corpus.json").write_text(
    json.dumps(exact_reviewed_corpus, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8"
)
(evidence_dir / "honest_classification.json").write_text(
    json.dumps(classification, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8"
)
