import json

with open('.work/competitive-v16/piloto-r3-v2/dossiers/pilot2_batch_2.json', 'r', encoding='utf-8') as f:
    dossiers = json.load(f)['dossiers']

with open('.work/competitive-v16/dossiers_dump.txt', 'w', encoding='utf-8') as out:
    for i, d in enumerate(dossiers):
        out.write(f"=== #{i+1} idx={d['pilot_index']} id={d['id']} op={d['cognitive_operation']} diff={d['target_difficulty']} noise={d['translation_noise']} ref={d['primary_source_ref']} ===\n")
        out.write(f"QUOTE: {d['primary_source_quote']}\n")
        out.write("CONTRAST FACTS:\n")
        for cf in d['contrast_facts']:
            out.write(f"  [{cf['fact_id']} | {cf['source_ref']}] {cf['source_quote']}\n")
        out.write("\n")

print(f"Successfully dumped {len(dossiers)} dossiers to dossiers_dump.txt")
