import json
import pathlib
import re

ROOT = pathlib.Path(".")
packets_dir = ROOT / "content" / "competitive-v13" / "staging-blind-packets"

def normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[«»\"'.,;:?!¿¡()\-—]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

for pf in sorted(packets_dir.glob("blind-*.json")):
    packet = json.loads(pf.read_text(encoding="utf-8"))
    print(f"\n=== Packet {pf.name} ({packet['blind_batch_id']}) ===")
    
    for idx, q in enumerate(packet["questions"]):
        sq_norm = normalize_text(q["source_quote"])
        matched_opts = []
        
        for o_idx, opt in enumerate(q["options"]):
            opt_norm = normalize_text(opt)
            # Check direct substring
            if opt_norm in sq_norm or any(part in sq_norm for part in opt_norm.split(" ") if len(part) > 6):
                # Count matching words
                opt_words = [w for w in opt_norm.split(" ") if len(w) > 3]
                match_count = sum(1 for w in opt_words if w in sq_norm)
                match_ratio = match_count / max(1, len(opt_words))
                matched_opts.append((o_idx, opt, match_ratio))
                
        matched_opts.sort(key=lambda x: x[2], reverse=True)
        best = matched_opts[0] if matched_opts else (None, None, 0)
        second = matched_opts[1] if len(matched_opts) > 1 else (None, None, 0)
        
        print(f"  Q{idx+1} ({q['id']}): Best match = Option {best[0]} (ratio {best[2]:.2f}) | 2nd match ratio = {second[2]:.2f}")
