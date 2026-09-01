import json
import pathlib
import sys
import hashlib
import hmac

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import (
    AUTHORED_SCHEMA,
    canonical_hash,
    authored_content_hash,
    blind_packet_hash,
)
from scripts.repair_staging_questions import load_source_units

source_units = load_source_units()
staging_dir = ROOT / "content" / "competitive-v13" / "staging-cycles16-21"
out_dir = ROOT / "content" / "competitive-v13" / "staging-blind-packets"
out_dir.mkdir(parents=True, exist_ok=True)

binding_key = (pathlib.Path.home() / ".codex" / "secrets" / "competitive-v13-blind-binding.key").read_bytes()

batch_files = sorted(staging_dir.glob("*.json"))
print(f"Building blind review packets for {len(batch_files)} batches...")

for bf in batch_files:
    batch_raw = json.loads(bf.read_text(encoding="utf-8"))
    batch_name = bf.stem
    
    blind_questions = []
    for idx, q in enumerate(batch_raw):
        source = source_units[q["source_unit_id"]]
        
        # Deterministic shuffle seed for blind packet
        shuffle_seed = int(hashlib.sha256(f"{q['id']}:{bf.name}:blind".encode("utf-8")).hexdigest()[:8], 16)
        
        # Original options
        orig_options = list(q["options"])
        # Map original indices to option text
        indexed_opts = list(enumerate(orig_options))
        # Shuffle deterministically
        import random
        r = random.Random(shuffle_seed)
        r.shuffle(indexed_opts)
        
        shuffled_options = [opt for _, opt in indexed_opts]
        
        blind_q = {
            "id": q["id"],
            "question": q["question"],
            "options": shuffled_options,
            "source_unit_id": q["source_unit_id"],
            "source_ref": source["source_ref"],
            "source_quote": source["source_quote"],
            "authored_content_sha256": authored_content_hash(q)
        }
        blind_questions.append(blind_q)
        
    blind_batch_id = hmac.new(binding_key, batch_name.encode("utf-8"), hashlib.sha256).hexdigest()[:20]
    
    packet_body = {
        "schema_version": "competitive-v13-blind-packet/v1",
        "blind_batch_id": f"blind-{blind_batch_id}",
        "questions": blind_questions
    }
    packet_body["packet_sha256"] = blind_packet_hash(packet_body)
    
    out_file = out_dir / f"blind-{blind_batch_id}.json"
    out_file.write_text(json.dumps(packet_body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated {out_file.name} for {batch_name} ({len(blind_questions)} questions)")

print(f"\nAll {len(batch_files)} blind packets generated in {out_dir}!")
