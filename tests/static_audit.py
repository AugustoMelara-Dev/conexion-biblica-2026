from pathlib import Path
import collections
import hashlib
import json
import re
import sys

ROOT = Path('/mnt/data/conexion-biblica-2026')
DIST = ROOT / 'dist'
data = json.loads((DIST / 'app_data.json').read_text(encoding='utf-8'))
qs = data['questions']
audit = data['audit']

assert len(data['sources']) == 18, len(data['sources'])
expected_chapters = [*(f'Daniel {i}' for i in range(1, 13)), *(f'Profetas y Reyes {i}' for i in range(39, 45))]
assert [s['chapter'] for s in data['sources']] == expected_chapters
assert audit['valid'] == len(qs)
assert audit['created'] == audit['valid'] + audit['excluded']
assert audit['unitsWithoutQuestion'] == 0
assert all(not v['missing'] and v['covered'] == v['total'] for v in audit['coverage'].values())
assert sum(v['total'] for v in audit['coverage'].values()) == sum(len(s['units']) for s in data['sources']) == 514

allowed = {'seleccionar', 'verdadero_falso', 'completar'}
assert set(q['type'] for q in qs) == allowed
assert len({q['id'] for q in qs}) == len(qs)
normalize = lambda x: re.sub(r'\s+', ' ', str(x)).strip()
normalize_cf = lambda x: normalize(x).casefold()
assert len({normalize_cf(q['prompt']) for q in qs}) == len(qs)

units = {(s['chapter'], u['reference']): u for s in data['sources'] for u in s['units']}
unit_keys = {u['unitKey'] for s in data['sources'] for u in s['units']}
source_text = {
    source: normalize(' '.join(u['text'] for s in data['sources'] if s['source'] == source for u in s['units']))
    for source in {s['source'] for s in data['sources']}
}
required = {
    'id','source','chapter','reference','unitKey','evidence','context','type','difficulty','prompt','options',
    'correctIndex','correctAnswer','explanation','detail','family','distractorReasons','confusables','complexity','bankVersion'
}
alias_groups = [
    {'daniel','beltsasar'}, {'ananías','sadrac','sadrach'}, {'misael','mesac','mesach'},
    {'azarías','abed-nego','abednego'}
]
negative_words = re.compile(r'\b(NO|EXCEPTO|NUNCA)\b')
negative_count = 0
false_count = 0
true_count = 0

for q in qs:
    missing = required - q.keys()
    assert not missing, (q['id'], missing)
    assert q['unitKey'] in unit_keys, q['id']
    unit = units[(q['chapter'], q['reference'])]
    assert normalize_cf(q['context']) == normalize_cf(unit['text']), q['id']
    assert normalize_cf(q['evidence']) in normalize_cf(unit['text']), (q['id'], 'evidence')
    assert len(q['options']) == len(set(q['options'])), q['id']
    assert q['correctAnswer'] in q['options'] and q['options'].count(q['correctAnswer']) == 1, q['id']
    assert q['correctIndex'] == q['options'].index(q['correctAnswer']), q['id']
    assert q['type'] in allowed
    assert q['difficulty'] in {'fácil','media','difícil','trampa'}
    assert q['explanation'].strip()
    if negative_words.search(q['prompt']):
        negative_count += 1

    if q['type'] == 'verdadero_falso':
        assert q['options'] == ['Verdadero', 'Falso'], q['id']
        if q['correctAnswer'] == 'Falso':
            false_count += 1
            assert q.get('altered'), q['id']
            assert 'Se cambió' in q['explanation'], q['id']
            old, new = [x.strip() for x in q['altered'].split('→', 1)]
            assert normalize_cf(old) in normalize_cf(q['evidence']), (q['id'], old)
            # The displayed assertion must be the literal evidence with one exact alteration.
            statement = q['prompt'].split(': ', 1)[1] if q['prompt'].startswith('Según ') and ': ' in q['prompt'] else q['prompt']
            expected = q['evidence'].replace(old, new, 1)
            assert normalize_cf(statement) == normalize_cf(expected), (q['id'], statement, expected)
            for group in alias_groups:
                assert not (old.casefold() in group and new.casefold() in group), (q['id'], q['altered'])
        else:
            true_count += 1
            statement = q['prompt'].split(': ', 1)[1] if q['prompt'].startswith('Según ') and ': ' in q['prompt'] else q['prompt']
            assert normalize_cf(statement) == normalize_cf(q['evidence']), q['id']
    else:
        assert len(q['options']) == 4, q['id']
        correct = q['correctAnswer']
        for option in q['options']:
            if q.get('optionConstruction') == 'quantity-compatible':
                # The unchanged unit tail is checked by the build audit; every numeric token must occur in the source.
                tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", option)
                assert any(normalize_cf(tok) in normalize_cf(source_text[q['source']]) for tok in tokens), (q['id'], option)
            else:
                assert normalize_cf(option) in normalize_cf(source_text[q['source']]), (q['id'], option)
        for option in q['options']:
            if option != correct:
                assert normalize_cf(option) not in normalize_cf(correct)
                assert normalize_cf(correct) not in normalize_cf(option)
        if q['type'] == 'completar':
            assert '_____' in q['prompt'], q['id']
            assert normalize_cf(q['completeSentence']) in normalize_cf(q['evidence']), q['id']
            assert normalize_cf(q['blank']) in normalize_cf(q['completeSentence']), q['id']

assert false_count + true_count == sum(q['type'] == 'verdadero_falso' for q in qs)
assert false_count >= 150 and true_count >= 150, (false_count, true_count)
assert negative_count / len(qs) <= 0.15, negative_count

# Correct option positions must not form a predictable pattern.
positions = collections.Counter(q['correctIndex'] for q in qs if q['type'] != 'verdadero_falso')
assert set(positions) == {0,1,2,3}
assert max(positions.values()) - min(positions.values()) <= 5, positions

# All chapters have transparent goals and the perfect score always means 100%.
profiles = data['profiles']
assert len(profiles) == 19 and profiles[-1]['chapter'] == 'Banco combinado'
for p in profiles:
    assert p['perfectGoal'] == 100
    expected_goal = 100 if p['questions'] <= 60 else 99 if p['questions'] <= 150 else 98
    assert p['competitiveGoal'] == expected_goal, p
    assert 0 <= p['complexity'] <= 100

# Offline/single-file constraints.
html = (DIST / 'index.html').read_text(encoding='utf-8')
for pattern in [
    r'<script[^>]+src=', r'<link[^>]+href=', r'<img[^>]+src=', r'\bfetch\s*\(',
    r'XMLHttpRequest', r'new\s+WebSocket', r'EventSource\s*\(', r'https?://'
]:
    assert not re.search(pattern, html, re.I), pattern
for required_text in [
    'localStorage','Piensa primero','Modo Final','exportProgress','exportBank','importFile',
    'visibilitychange','orientationchange','SCHEMA_VERSION=4','function iconSvg','lucide-icon',
    'Clasifiqué a distrito','Clasifiqué a asociación'
]:
    assert required_text in html, required_text
assert '__APP_DATA__' not in html
assert len(html.encode('utf-8')) == (DIST / 'index.html').stat().st_size

# No page marker became its own unit.
assert all(not u['text'].strip().isdigit() for s in data['sources'] for u in s['units'])

result = {
    'questions': len(qs),
    'types': dict(collections.Counter(q['type'] for q in qs)),
    'difficulty': dict(collections.Counter(q['difficulty'] for q in qs)),
    'trueFalse': {'false': false_count, 'true': true_count},
    'positions': dict(positions),
    'chapters': len(data['sources']),
    'units': 514,
    'created': audit['created'],
    'valid': audit['valid'],
    'corrected': audit['corrected'],
    'excluded': audit['excluded'],
    'htmlBytes': (DIST / 'index.html').stat().st_size,
    'htmlSha256': hashlib.sha256((DIST / 'index.html').read_bytes()).hexdigest(),
}
(DIST / 'static_audit_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('STATIC_AUDIT_OK')
print(json.dumps(result, ensure_ascii=False, indent=2))
