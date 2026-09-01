import json
import pathlib

p1 = json.loads(pathlib.Path('.work/competitive-v16/piloto-r3/packets-b/packet_1.json').read_text(encoding='utf-8'))
p2 = json.loads(pathlib.Path('.work/competitive-v16/piloto-r3/packets-b/packet_2.json').read_text(encoding='utf-8'))

questions = p1['questions'] + p2['questions']
out_lines = []
out_lines.append(f"Loaded {len(questions)} questions ({len(p1['questions'])} in packet 1, {len(p2['questions'])} in packet 2)\n")

for i, q in enumerate(questions):
    out_lines.append(f"=== Q{i+1}: {q['question_id']} | Ref: {q['source_ref']} (Page: {q['source_page']}) ===")
    out_lines.append(f"SHA: {q['presentation_sha256']}")
    out_lines.append(f"Question: {q['question']}")
    out_lines.append(f"Source Quote: {q['source_quote']}")
    for idx, opt in enumerate(q['options']):
        out_lines.append(f"  [{idx}] {opt}")
    out_lines.append("")

pathlib.Path('scripts/dump_piloto_r3.txt').write_text('\n'.join(out_lines), encoding='utf-8')
print("Dumped 60 questions to scripts/dump_piloto_r3.txt")
