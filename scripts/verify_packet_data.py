import json
import pathlib
import sys

p3 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_3.json').read_text(encoding='utf-8'))
p4 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_4.json').read_text(encoding='utf-8'))
all_questions = p3['questions'] + p4['questions']

print(f"Total questions to audit: {len(all_questions)}")
