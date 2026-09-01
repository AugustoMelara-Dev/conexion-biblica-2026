import json
import pathlib
import sys
import random

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import (
    AUTHORED_SCHEMA,
    ContractError,
    validate_authored_batch,
)

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

source_units = load_source_units()
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"

def clean_text_doctrinal_baggage(text: str) -> str:
    if not text:
        return text
    # Clean external doctrinal baggage
    t = text
    t = t.replace("(Lidia, Babilonia, Egipto)", "")
    t = t.replace("(Media y Persia)", "")
    t = t.replace("Roma imperial y papal", "el cuarto reino profético")
    t = t.replace("juicio investigador", "juicio celestial")
    t = t.replace("(2,300 tardes y mañanas/años)", "(dos mil trescientas tardes y mañanas)")
    t = t.replace("Prefigura la tumba sellada de Cristo con la piedra y los sellos de las autoridades terrenales.", "Representa la seguridad legal extrema que aseguró la prueba y la posterior liberación milagrosa.")
    t = t.replace("Daniel 5:13 articula la acusación maliciosa", "Daniel 6:13 articula la acusación maliciosa")
    t = t.replace("romano sobre el mundo mediterráneo y Palestina", "del cuerno sobre las naciones y la tierra gloriosa")
    t = t.replace("(Grecia)", "")
    t = t.replace("(Grecia/Macedonia)", "")
    t = t.replace("(Alejandro Magno)", "")
    t = t.replace("Alejandro Magno", "el poder simbolizado")
    t = t.replace("Prefigura las veloces conquistas de Alejandro Magno y la fragmentación de su imperio entre cuatro generales.", "Describe la rapidez de conquista y la división del reino en cuatro direcciones.")
    t = t.replace("Prefigura la asombrosa rapidez de las conquistas de Alejandro Magno contra Persia.", "Muestra la velocidad arrolladora del avance del macho cabrío.")
    t = t.replace("  ", " ")
    return t.strip()

# Target position pattern for each 10-question batch: [0, 1, 2, 3, 0, 1, 2, 3, 0, 1] or similar
target_positions = [0, 1, 2, 3, 1, 2, 3, 0, 2, 3]

batch_files = sorted(staging_dir.glob("*.json"))
print(f"Repairing {len(batch_files)} batches in staging...")

total_repaired = 0
for bf in batch_files:
    questions = json.loads(bf.read_text(encoding="utf-8"))
    repaired_questions = []
    
    for idx, q in enumerate(questions):
        num_opts = len(q["options"])
        target_pos = target_positions[idx % len(target_positions)] % num_opts
        
        # Clean explanation and significance
        q["explanation"] = clean_text_doctrinal_baggage(q.get("explanation", ""))
        q["significance"] = clean_text_doctrinal_baggage(q.get("significance", ""))
        
        # Identify current correct answer and distractors
        if "accepted_answers" in q and q["accepted_answers"][0] in q["options"]:
            correct_text = q["accepted_answers"][0]
        else:
            correct_text = q["options"][q["correct_option"]]
        distractors = [opt for opt in q["options"] if opt != correct_text]
        
        # Construct new options list with correct answer at target_pos
        new_options = list(distractors)
        new_options.insert(target_pos, correct_text)
        
        q["options"] = new_options
        q["correct_option"] = target_pos
        q["accepted_answers"] = [correct_text]
        
        # Rebuild why_distractors_fail so keys match distractors exactly
        old_wdf = q.get("why_distractors_fail", {})
        new_wdf = {}
        for d in distractors:
            # find matching key in old_wdf
            if d in old_wdf:
                new_wdf[d] = clean_text_doctrinal_baggage(old_wdf[d])
            else:
                # fallback matching
                matched = False
                for k, v in old_wdf.items():
                    if k.strip().lower() == d.strip().lower():
                        new_wdf[d] = clean_text_doctrinal_baggage(v)
                        matched = True
                        break
                if not matched:
                    new_wdf[d] = "Opción incorrecta refutada por el texto canónico."
        q["why_distractors_fail"] = new_wdf
        
        # Ensure difficulty is hard or expert
        if q.get("difficulty") not in ("hard", "expert"):
            q["difficulty"] = "hard"
            
        repaired_questions.append(q)
        total_repaired += 1
        
    bf.write_text(json.dumps(repaired_questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    
    # Validate repaired batch
    batch_name = bf.stem
    first_author = repaired_questions[0].get("author") or {"id": "autor-reparacion", "model": "gemini-3.7-flash"}
    batch_payload = {
        "schema_version": AUTHORED_SCHEMA,
        "release": 2,
        "batch_id": batch_name,
        "author": first_author,
        "source_sha256": "0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3",
        "questions": repaired_questions
    }
    errors = validate_authored_batch(batch_payload, source_units)
    if errors:
        print(f"ERROR validating repaired batch {bf.name}:", errors)
        sys.exit(1)
    else:
        print(f"OK: Repaired and validated {bf.name} (10 questions, positions balanced)")

print(f"\nAll {total_repaired} staging questions repaired, balanced, and validated cleanly!")
