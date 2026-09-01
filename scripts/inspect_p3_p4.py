import json
import pathlib
import sys

def print_range(start, end):
    p3 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_3.json').read_text(encoding='utf-8'))
    p4 = json.loads(pathlib.Path('content/competitive-v13/waves/wave2/packets-b/packet_4.json').read_text(encoding='utf-8'))
    qs = p3['questions'] + p4['questions']
    for idx in range(start, min(end, len(qs))):
        q = qs[idx]
        print(f"*** [{idx+1}/60] ID: {q['question_id']} | Ref: {q['source_ref']}")
        print(f"Q: {q['question']}")
        print(f"Quote: {q['source_quote']}")
        for opt_i, opt in enumerate(q['options']):
            print(f"  ({opt_i}) {opt}")
        print()

if __name__ == '__main__':
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    e = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    print_range(s, e)
