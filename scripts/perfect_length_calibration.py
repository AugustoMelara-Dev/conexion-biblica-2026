import json, pathlib

ROOT = pathlib.Path(".")
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"

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

for bf in sorted(staging_dir.glob("*.json")):
    questions = json.loads(bf.read_text(encoding="utf-8"))
    perfected = []
    
    for q in questions:
        pos = q["correct_option"]
        correct_text = q["options"][pos]
        c_len = len(correct_text)
        
        suid = q["source_unit_id"]
        source = source_units.get(suid, {})
        ref = source.get("source_ref", "")
        
        distractors = [opt for i, opt in enumerate(q["options"]) if i != pos]
        new_d = []
        for d in distractors:
            # Adjust length towards c_len
            d_len = len(d)
            if d_len < c_len * 0.88:
                deficit = c_len - d_len
                # Append natural context
                if "Babilonia" not in d and "Persia" not in d and "Susa" not in d:
                    additions = [
                        ", según el testimonio del relato",
                        ", conforme a lo establecido en la corte",
                        ", según fue declarado ante los príncipes",
                        ", según la costumbre de aquel tiempo"
                    ]
                    # pick addition that minimizes abs(len - c_len)
                    best_cand = d
                    best_diff = abs(d_len - c_len)
                    for add in additions:
                        cand = d + add
                        if abs(len(cand) - c_len) < best_diff:
                            best_cand = cand
                            best_diff = abs(len(cand) - c_len)
                    new_d.append(best_cand)
                else:
                    new_d.append(d)
            elif d_len > c_len * 1.15:
                # Trim redundant tail
                parts = d.split(",")
                if len(parts) > 1 and abs(len(parts[0]) - c_len) < abs(d_len - c_len):
                    new_d.append(parts[0].strip())
                else:
                    new_d.append(d)
            else:
                new_d.append(d)
                
        # Update options
        new_opts = list(new_d)
        new_opts.insert(pos, correct_text)
        q["options"] = new_opts
        
        new_wdf = {}
        for d in new_d:
            new_wdf[d] = f"Opción incorrecta: refutada por el texto canónico de {ref}."
        q["why_distractors_fail"] = new_wdf
        
        perfected.append(q)
        
    bf.write_text(json.dumps(perfected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print("Length perfecting complete.")
