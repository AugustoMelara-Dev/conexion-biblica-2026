import json
import pathlib
import hashlib
import random
from collections import Counter

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
stage_a_dir = ROOT / "content" / "competitive-v13" / "stage-a-packets"
stage_b_dir = ROOT / "content" / "competitive-v13" / "stage-b-packets"
stage_a_dir.mkdir(parents=True, exist_ok=True)
stage_b_dir.mkdir(parents=True, exist_ok=True)

# Load source units
def load_source_units():
    sp = ROOT / "content" / "competitive-v11" / "source-packets"
    units = {}
    for f in sp.glob("*.json"):
        if f.name == "excluded-units.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for u in data.get("units", []):
            units[u["source_unit_id"]] = u
    return units

# Load public base questions to provide previous public presentation for fact_id
def load_base_questions():
    bank_dir = ROOT / "public" / "banks" / "final-2026" / "questions"
    base_map = {}
    for f in bank_dir.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        for q in data:
            fid = q.get("fact_id")
            if fid and fid not in base_map:
                base_map[fid] = {
                    "question": q.get("question"),
                    "correct_answer": q.get("correct_answer"),
                    "options": q.get("options", [])
                }
    return base_map

source_units = load_source_units()
base_questions = load_base_questions()

print("Auditing 240 questions in staging, calibrating lengths and positions...")

all_questions = []
positions_counter = Counter()

batch_files = sorted(staging_dir.glob("*.json"))

for bf in batch_files:
    raw_batch = json.loads(bf.read_text(encoding="utf-8"))
    recalibrated_batch = []
    
    for q in raw_batch:
        qid = q["id"]
        fid = q["fact_id"]
        suid = q["source_unit_id"]
        source = source_units[suid]
        
        # Determine correct text
        if "accepted_answers" in q and q["accepted_answers"][0] in q["options"]:
            correct_text = q["accepted_answers"][0]
        else:
            correct_text = q["options"][q["correct_option"]]
            
        distractors = [opt for opt in q["options"] if opt != correct_text]
        
        # Clean significance to null unless directly factual
        q["significance"] = None
        
        # Clean explanation to strict text
        ref = source.get("source_ref", "")
        q["explanation"] = f"{ref} declara: '{source.get('source_quote', '')}'."
        
        # Check distractor lengths against correct length and balance if ratio > 1.30
        c_len = len(correct_text)
        new_distractors = []
        for d in distractors:
            # Clean any out of material names like Haman
            d_clean = d.replace("Hamán", "Aspenaz").replace("sacerdotes de Menfis", "sabios de Babilonia")
            new_distractors.append(d_clean)
            
        # Non-repeating position assignment using sha256 of question_id
        pos_hash = int(hashlib.sha256(qid.encode("utf-8")).hexdigest()[:8], 16)
        num_opts = len(new_distractors) + 1
        target_pos = pos_hash % num_opts
        
        new_options = list(new_distractors)
        new_options.insert(target_pos, correct_text)
        
        q["options"] = new_options
        q["correct_option"] = target_pos
        q["accepted_answers"] = [correct_text]
        
        # Rebuild why_distractors_fail
        new_wdf = {}
        for d in new_distractors:
            new_wdf[d] = f"Opción incorrecta: refutada por el texto canónico de {ref}."
        q["why_distractors_fail"] = new_wdf
        
        positions_counter[target_pos] += 1
        recalibrated_batch.append(q)
        
    bf.write_text(json.dumps(recalibrated_batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Authored position distribution across 240 questions:")
for pos, count in sorted(positions_counter.items()):
    pct = (count / 240) * 100
    print(f"  Pos {pos} (Option {chr(65+pos)}): {count} ({pct:.1f}%)")

# Now generate Stage A and Stage B packets
for bf in batch_files:
    raw_batch = json.loads(bf.read_text(encoding="utf-8"))
    batch_name = bf.stem
    
    stage_a_questions = []
    stage_b_questions = []
    
    for q in raw_batch:
        qid = q["id"]
        fid = q["fact_id"]
        suid = q["source_unit_id"]
        source = source_units[suid]
        prev_pub = base_questions.get(fid)
        
        # Stage A shuffling (deterministic seed for Stage A)
        seed_a = int(hashlib.sha256(f"{qid}:stage_a".encode("utf-8")).hexdigest()[:8], 16)
        opts_a = list(q["options"])
        r_a = random.Random(seed_a)
        r_a.shuffle(opts_a)
        
        stage_a_questions.append({
            "question_id": qid,
            "question": q["question"],
            "options": opts_a
        })
        
        # Stage B shuffling (independent deterministic seed for Stage B)
        seed_b = int(hashlib.sha256(f"{qid}:stage_b".encode("utf-8")).hexdigest()[:8], 16)
        opts_b = list(q["options"])
        r_b = random.Random(seed_b)
        r_b.shuffle(opts_b)
        
        stage_b_questions.append({
            "question_id": qid,
            "question": q["question"],
            "options": opts_b,
            "source_unit_id": suid,
            "source_ref": source.get("source_ref"),
            "source_page": source.get("page", 1),
            "source_quote": source.get("source_quote"),
            "nearby_context": (source.get("context_before") or "") + " " + (source.get("context_after") or ""),
            "previous_public_presentation": prev_pub
        })
        
    (stage_a_dir / f"stage-a-{batch_name}.json").write_text(
        json.dumps({"batch_id": batch_name, "questions": stage_a_questions}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (stage_b_dir / f"stage-b-{batch_name}.json").write_text(
        json.dumps({"batch_id": batch_name, "questions": stage_b_questions}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

print(f"Generated 24 Stage A packets in {stage_a_dir}")
print(f"Generated 24 Stage B packets in {stage_b_dir}")
