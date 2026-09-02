import glob, json, pathlib, unicodedata

def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", str(text))
    return " ".join(normalized.split()).lower()

w4_authored = json.loads(pathlib.Path(".work/competitive-v16/waves/wave4/wave4_authored_corpus.json").read_text(encoding="utf-8"))
w4_stage_a = {}
for f in sorted(glob.glob(".work/competitive-v16/waves/wave4/stage-a/*/*.json")):
    for r in json.loads(pathlib.Path(f).read_text(encoding="utf-8")):
        w4_stage_a[r["question_id"]] = r

w4_stage_b = {}
for f in sorted(glob.glob(".work/competitive-v16/waves/wave4/stage-b/*/*.json")):
    for r in json.loads(pathlib.Path(f).read_text(encoding="utf-8")):
        w4_stage_b[r["question_id"]] = r

fails = []
for q in w4_authored:
    qid = q["id"]
    ra = w4_stage_a.get(qid)
    rb = w4_stage_b.get(qid)
    if not ra or not rb:
        fails.append((qid, "missing review"))
        continue
    text_auth = q.get("correct_answer") or q["options"][q["correct_option"]]
    text_a = ra.get("selected_option_text")
    text_b = rb.get("selected_option_text")
    norm_auth = normalize_text(text_auth)
    norm_a = normalize_text(text_a)
    norm_b = normalize_text(text_b)
    if not (norm_auth == norm_a == norm_b):
        fails.append((qid, f"text mismatch: auth='{norm_auth[:25]}' a='{norm_a[:25]}' b='{norm_b[:25]}'"))
    elif ra.get("recommendation") != "ACCEPT":
        fails.append((qid, f"rec a: {ra.get('recommendation')}"))
    elif rb.get("decision") != "ACCEPT":
        fails.append((qid, f"dec b: {rb.get('decision')}"))
    elif rb.get("second_defensible_option"):
        fails.append((qid, "second defensible option"))
    elif ra.get("length_or_precision_giveaway"):
        fails.append((qid, "length giveaway"))
    elif ra.get("solved_by") not in ["KNOWLEDGE", "ELIMINATION"]:
        fails.append((qid, f"solved by: {ra.get('solved_by')}"))

print(f"Total fails: {len(fails)}")
for f in fails[:15]:
    print(" ", f)
