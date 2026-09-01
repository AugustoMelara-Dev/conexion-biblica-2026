import json, pathlib
ROOT = pathlib.Path(".")
reviews_dir = ROOT / "content" / "competitive-v13" / "staging-reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

# Subagent 5 results
subagent5_batches = [
  ("blind-b6a2dc273eed1f1a21d2", "DAN8-C17"),
  ("blind-d6ac0ebf533ec662836c", "DAN9-C18"),
  ("blind-4b8536108a56ed58d743", "DAN10-C18"),
  ("blind-28b79792a82536652033", "DAN11-C18")
]

# Let us load decisions from the subagent transcripts or structured text
# We can parse subagent 5 and 4 decisions
from scripts.verify_blind_options import normalize_text

# Write helper to save reviews
