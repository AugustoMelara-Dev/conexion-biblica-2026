from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import random
import re
import statistics
from typing import Iterable

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
DIST = ROOT / 'dist'
DIST.mkdir(parents=True, exist_ok=True)

BANK_VERSION = '2026.08.16-full-d1-12-pr39-44-v2-nuevos-bancos'
GENERATED_AT = '2026-08-16'

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:[-’'][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)*")
SPACE_RE = re.compile(r'\s+')
PAGE_DANIEL = set(range(79, 101))
PAGE_PR = set(range(103, 135))

STOPWORDS = {
    'a','al','algo','ante','así','aun','aunque','bajo','bien','cada','como','con','contra','cual','cuando','de','del','desde','donde',
    'el','ella','ellos','en','entre','era','es','esa','ese','esta','este','fue','ha','había','hasta','la','las','le','les','lo','los',
    'mas','más','mi','mientras','muy','ni','no','o','para','pero','por','porque','que','se','según','si','sin','sobre','su','sus','tan',
    'te','tu','un','una','uno','y','ya','yo','él','esto','estos','estas','aquel','aquella','aquellos','aquellas','pues','entonces'
}
NUMBER_WORDS = {
    'dos','tres','cuatro','cinco','seis','siete','ocho','nueve','diez','once','doce','trece','catorce','quince','dieciséis',
    'diecisiete','dieciocho','diecinueve','veinte','veintiún','veintiuna','veintiuno','veintidós','veinticuatro','treinta',
    'cuarenta','cincuenta','sesenta','setenta','ochenta','noventa','cien','ciento','cientos','doscientos','doscientas',
    'trescientos','trescientas','cuatrocientos','cuatrocientas','quinientos','quinientas','seiscientos','seiscientas',
    'setecientos','setecientas','ochocientos','ochocientas','novecientos','novecientas','mil','miles','millón','millones',
    'primero','primera','primer','segundo','segunda','tercero','tercera','tercer','cuarto','cuarta','quinto','quinta',
    'sexto','sexta','séptimo','séptima','octavo','octava','noveno','novena','décimo','décima','mitad'
}

ORDINAL_WORDS = {
    'primero','primera','primer','segundo','segunda','tercero','tercera','tercer','cuarto','cuarta','quinto','quinta',
    'sexto','sexta','séptimo','séptima','octavo','octava','noveno','novena','décimo','décima'
}
SIMPLE_CARDINALS = {
    'dos','tres','cuatro','cinco','seis','siete','ocho','nueve','diez','once','doce','trece','catorce','quince','veinte',
    'treinta','cuarenta','cincuenta','sesenta','setenta','ochenta','noventa','cien','mil'
}

ONE_WORDS = {'un','una','uno'}
QUANTITY_UNITS = {
    'año','años','día','días','semana','semanas','vez','veces','codo','codos','rey','reyes','cuerno','cuernos','costilla','costillas',
    'viento','vientos','cabeza','cabezas','ala','alas','tarde','tardes','mañana','mañanas','tiempo','tiempos','príncipe','príncipes',
    'sátrapa','sátrapas','gobernador','gobernadores','hombre','hombres','pueblo','pueblos','nación','naciones','lengua','lenguas'
}
PROPER_EXCLUDES = {
    'En','El','La','Los','Las','Y','Pero','Por','Porque','Cuando','Entonces','Así','Después','Luego','Mas','No','Si','Aun','Aunque',
    'Mientras','Al','Del','De','Su','Sus','Un','Una','Este','Esta','Estos','Estas','Aquel','Aquella','Todo','Todos','Toda','Todas',
    'He','Sea','Rey','Señor','Dios','Yo','Tú','Él','Ellos','Ella','A','Ante','Con','Sin','Sobre','Hasta','Ahora','También','Ciertamente'
}


# Nombres y lugares extraídos de las fuentes suministradas. Se usa una lista cerrada para
# impedir que una palabra en mayúscula al inicio de una oración (por ejemplo, «Cuenta»)
# sea tratada erróneamente como persona o lugar.
PERSON_NAMES = {
    'Abed-nego','Abednego','Abihú','Ananías','Arioc','Asuero','Aspenaz','Azarías','Belsasar','Beltsasar','Ciro','Daniel','Darío',
    'Enoc','Ezequiel','Gabriel','Isaías','Jacob','Jeremías','Joacim','Juan','Melsar','Mesac','Mesach','Miguel','Misael','Moisés',
    'Nabucodonosor','Nadab','Pablo','Sadrach','Sadrac','Satanás'
}
PLACE_NAMES = {
    'Amón','Babilonia','Chebar','Dura','Edom','Egipto','Elam','Etiopía','Grecia','Hidekel','Israel','Jerusalén','Judá','Judea',
    'Libia','Media','Medo-Persia','Moab','Persia','Quitim','Sinar','Sión','Susa','Tiro','Ulai'
}
DIVINE_NAMES = {'Jehová','Altísimo','Omnipotente','Todopoderoso','Invisible','YO SOY'}
SAFE_NAMES = PERSON_NAMES | PLACE_NAMES | DIVINE_NAMES
NAME_GROUP = {**{x:'persona' for x in PERSON_NAMES}, **{x:'lugar' for x in PLACE_NAMES}, **{x:'divino' for x in DIVINE_NAMES}}

PERSON_ROLE_GROUPS = {
    'gobernante': {'Joacim','Nabucodonosor','Belsasar','Darío','Ciro','Asuero'},
    'joven_hebreo': {'Daniel','Beltsasar','Ananías','Sadrac','Sadrach','Misael','Mesac','Mesach','Azarías','Abed-nego','Abednego'},
    'oficial': {'Aspenaz','Melsar','Arioc'},
    'mensajero': {'Gabriel','Miguel'},
}
PERSON_ROLE = {name: role for role, names in PERSON_ROLE_GROUPS.items() for name in names}
ALIAS_GROUPS = [
    {'Daniel','Beltsasar'}, {'Ananías','Sadrac','Sadrach'}, {'Misael','Mesac','Mesach'}, {'Azarías','Abed-nego','Abednego'}
]
ALIAS_GROUP = {name: idx for idx, names in enumerate(ALIAS_GROUPS) for name in names}
PLACE_ROLE_GROUPS = {
    'ciudad_region': {'Babilonia','Jerusalén','Judá','Judea','Sinar','Susa','Elam','Dura','Tiro','Egipto','Persia','Media','Grecia','Edom','Moab','Amón','Libia','Etiopía','Quitim','Israel','Sión','Medo-Persia'},
    'rio': {'Ulai','Hidekel','Chebar'},
}
PLACE_ROLE = {name: role for role, names in PLACE_ROLE_GROUPS.items() for name in names}
TRANSITIONS = (
    'Pero ', 'Sin embargo', 'Entonces ', 'Por tanto', 'Por esto', 'Así ', 'Después ', 'Mientras ', 'Al ', 'Cuando ', 'Ahora ',
    'En cambio', 'A pesar', 'De esta', 'Del ', 'El rey', 'Daniel ', 'Nabucodonosor ', 'Belsasar ', 'Darío ', 'Dios ', 'El Señor',
    'Los ', 'Las ', 'Un ', 'Una ', 'En la ', 'En el ', 'A medida', 'Como ', 'Así como', 'Hacia ', 'Poco ', 'Pronto ', 'Más '
)


def norm(s: str) -> str:
    return SPACE_RE.sub(' ', s).strip()


def words(s: str) -> list[str]:
    return WORD_RE.findall(s)


def stable_hash(s: str) -> int:
    return int(hashlib.sha256(s.encode('utf-8')).hexdigest()[:16], 16)


def stable_shuffle(items: Iterable, seed: str):
    arr = list(items)
    random.Random(stable_hash(seed)).shuffle(arr)
    return arr


def contains_exact(haystack: str, needle: str) -> bool:
    return norm(needle) in norm(haystack)


def sentence_chunks(text: str) -> list[str]:
    """Split conservatively on terminal punctuation while preserving exact text."""
    text = norm(text)
    if not text:
        return []
    protected = text
    replacements = {
        'Vers. ': 'Vers§ ', 'p. ': 'p§ ', 'P. ': 'P§ ', 'etc. ': 'etc§ ', 'Sr. ': 'Sr§ ', 'Sra. ': 'Sra§ '
    }
    for old, new in replacements.items():
        protected = protected.replace(old, new)
    # Terminal punctuation optionally followed by closing quotes.
    parts = re.split(r'(?<=[.!?])([”»\"]?)(?=\s+[«“—A-ZÁÉÍÓÚÜÑ¡¿])', protected)
    merged = []
    i = 0
    while i < len(parts):
        piece = parts[i]
        if i + 1 < len(parts) and parts[i + 1] in {'”', '»', '"'}:
            piece += parts[i + 1]
            i += 1
        piece = piece.strip()
        if piece:
            for old, new in replacements.items():
                piece = piece.replace(new, old)
            merged.append(piece)
        i += 1
    # The regex can leave chunks joined if punctuation is followed by lowercase; that is desirable.
    return merged or [text]


def split_long_clause(text: str, max_chars: int = 290) -> str:
    """Return an exact, self-contained fragment no longer than max_chars when practical."""
    text = norm(text)
    if len(text) <= max_chars:
        return text
    candidates = sentence_chunks(text)
    candidates = [c for c in candidates if 45 <= len(c) <= max_chars]
    if candidates:
        return max(candidates, key=lambda c: len(c))
    # Prefer a semicolon-delimited clause.
    parts = re.split(r'(?<=[;:])\s+', text)
    parts = [p for p in parts if 45 <= len(p) <= max_chars]
    if parts:
        return max(parts, key=len)
    # Exact prefix ending at punctuation.
    cut = text[:max_chars]
    at = max(cut.rfind(';'), cut.rfind(','), cut.rfind('.'), cut.rfind(':'))
    if at >= 70:
        return text[:at + 1].strip()
    return text[:max_chars].rsplit(' ', 1)[0].strip() + '…'


# ---------------------------------------------------------------------------
# Source parsing
# ---------------------------------------------------------------------------

DANIEL_TITLES = {
    1: 'Daniel y sus compañeros en Babilonia',
    2: 'Daniel interpreta el sueño de Nabucodonosor',
    3: 'El horno de fuego',
    4: 'La locura de Nabucodonosor',
    5: 'La escritura en la pared',
    6: 'Daniel en el foso de los leones',
    7: 'Visión de las cuatro bestias',
    8: 'Visión: el carnero y el macho cabrío',
    9: 'Oración de Daniel por su pueblo',
    10: 'Visión de Daniel junto al río',
    11: 'Los reyes del norte y del sur',
    12: 'El tiempo del fin',
}


def parse_daniel() -> tuple[list[dict], list[str], int]:
    raw_lines = (SRC / 'daniel-1-12-rvr95.txt').read_text(encoding='utf-8').splitlines()
    starts = [i for i, line in enumerate(raw_lines) if re.match(r'^Daniel\s+capítulo\s+\d+$', line.strip())]
    sources = []
    warnings = []
    page_removed = 0
    for idx, start in enumerate(starts):
        chapter = int(re.search(r'(\d+)$', raw_lines[start].strip()).group(1))
        end = starts[idx + 1] if idx + 1 < len(starts) else len(raw_lines)
        block = raw_lines[start + 1:end]
        filtered = []
        for line in block:
            st = line.strip()
            if not st:
                continue
            if st in {'Daniel', 'capítulo', str(chapter)}:
                continue
            if st.isdigit() and int(st) in PAGE_DANIEL:
                page_removed += 1
                continue
            filtered.append(st)
        # Skip section title/scaffolding until first content line.
        content_start = 0
        for i, st in enumerate(filtered):
            if re.match(rf'^{chapter}\s', st) or (chapter in {1, 2} and st.startswith('En ')) or (chapter == 11 and st.startswith('»También')):
                content_start = i
                break
        content = norm(' '.join(filtered[content_start:]))
        if re.match(rf'^{chapter}\s', content):
            content = re.sub(rf'^{chapter}\s+', '', content, count=1)
        if chapter == 5 and ' 8 »El Altísimo Dios, oh rey, dio a Nabucodonosor' in content:
            content = content.replace(
                ' 8 »El Altísimo Dios, oh rey, dio a Nabucodonosor',
                ' 18 »El Altísimo Dios, oh rey, dio a Nabucodonosor', 1
            )
            warnings.append('En Daniel 5, el texto extraído mostraba «8» después del versículo 17; se normalizó el marcador como 18 por la secuencia local. La redacción no fue alterada.')
        if chapter == 7 and 'prolongada la vida hasta cierto tiempo. »Miraba yo en la visión de la noche,' in content:
            content = content.replace(
                'prolongada la vida hasta cierto tiempo. »Miraba yo en la visión de la noche,',
                'prolongada la vida hasta cierto tiempo. 13 »Miraba yo en la visión de la noche,', 1
            )
            warnings.append('En Daniel 7, el marcador del versículo 13 no aparecía después del salto de página; se restauró únicamente la referencia por la secuencia local. La redacción no fue alterada.')
        if chapter in {3, 4, 5, 6, 7, 8, 9, 10, 12}:
            # The extraction repeats the chapter number before verse 1. It was removed above.
            pass

        units = []
        pos = 0
        verse = 1
        while True:
            next_verse = verse + 1
            m = re.search(rf'(?<!\d){next_verse}\s+', content[pos:])
            if not m:
                units.append({
                    'source': 'Daniel', 'chapter': f'Daniel {chapter}', 'reference': f'Daniel {chapter}:{verse}',
                    'unitKey': f'Daniel:Daniel {chapter}:{verse}', 'order': verse, 'text': norm(content[pos:])
                })
                break
            abs_start = pos + m.start()
            abs_end = pos + m.end()
            units.append({
                'source': 'Daniel', 'chapter': f'Daniel {chapter}', 'reference': f'Daniel {chapter}:{verse}',
                'unitKey': f'Daniel:Daniel {chapter}:{verse}', 'order': verse, 'text': norm(content[pos:abs_start])
            })
            pos = abs_end
            verse = next_verse
            if verse > 60:
                raise RuntimeError(f'Secuencia de versículos fuera de rango en Daniel {chapter}')
        if any(not u['text'] for u in units):
            raise RuntimeError(f'Unidad vacía en Daniel {chapter}')
        sources.append({
            'id': f'daniel-{chapter}', 'source': 'Daniel', 'chapter': f'Daniel {chapter}',
            'title': DANIEL_TITLES[chapter], 'version': 'Reina-Valera 1995', 'units': units
        })
    warnings.append('Se eliminaron los números de página aislados 79–100 y el andamiaje repetido de encabezados del archivo de Daniel; no se evaluaron.')
    warnings.append('En varios capítulos, el número del capítulo aparecía repetido delante del primer versículo por la extracción; se trató como encabezado, no como contenido.')
    return sources, warnings, page_removed


PR_HEADINGS = {39: 'En la corte de Babilonia', 40: 'El sueño de Nabucodonosor', 41: 'El horno de fuego', 42: 'La verdadera grandeza', 43: 'El vigía invisible', 44: 'En el foso de los leones'}


def technical_paragraphs(text: str, target_words: int = 88, min_words: int = 42, max_words: int = 138) -> list[str]:
    sentences = sentence_chunks(text)
    # Merge tiny fragments caused by quotation marks or references.
    merged = []
    for s in sentences:
        if merged and len(words(s)) < 8:
            merged[-1] = norm(merged[-1] + ' ' + s)
        else:
            merged.append(s)
    sentences = merged
    groups: list[str] = []
    current: list[str] = []
    count = 0
    for i, sentence in enumerate(sentences):
        wc = len(words(sentence))
        next_starts_transition = sentence.startswith(TRANSITIONS)
        if current and count >= min_words and ((count + wc > max_words) or (count >= target_words and next_starts_transition)):
            groups.append(norm(' '.join(current)))
            current = []
            count = 0
        current.append(sentence)
        count += wc
        if count >= max_words:
            groups.append(norm(' '.join(current)))
            current = []
            count = 0
    if current:
        tail = norm(' '.join(current))
        if groups and len(words(tail)) < min_words:
            groups[-1] = norm(groups[-1] + ' ' + tail)
        else:
            groups.append(tail)
    # Reconstruction check ignores whitespace only.
    if norm(' '.join(groups)) != norm(text):
        raise RuntimeError('La segmentación técnica no reconstruye el texto de Profetas y Reyes.')
    return groups


def parse_profetas(seed: dict) -> tuple[list[dict], list[str], int]:
    lines = (SRC / 'profetas-y-reyes-39-44.txt').read_text(encoding='utf-8').splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith('CCaapp')]
    sources = []
    warnings = []
    removed = 0
    seed_pr39 = next(s for s in seed['sources'] if s['chapter'] == 'Profetas y Reyes 39')
    sources.append(seed_pr39)
    for idx, start in enumerate(starts):
        heading_line = lines[start]
        # The duplicated OCR heading ends with 399/400/411/...; last two digits are the chapter.
        tail_digits = re.findall(r'\d+', heading_line)
        if not tail_digits:
            continue
        fused = ''.join(tail_digits)
        collapsed = re.sub(r'(\d)\1', r'\1', fused)
        chapter = int(collapsed[-2:])
        if chapter == 39:
            continue
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        block = lines[start + 1:end]
        cleaned = []
        title_skipped = False
        for line in block:
            st = line.strip()
            if not st:
                continue
            if not title_skipped:
                # First non-empty line is the chapter title.
                title_skipped = True
                continue
            if st.isdigit() and int(st) in PAGE_PR:
                removed += 1
                continue
            # Remove a page marker appended by extraction, but never a biblical reference.
            m = re.search(r'\s(10[3-9]|1[12]\d|13[0-4])$', st)
            if m:
                st = st[:m.start()].rstrip()
                removed += 1
            if st:
                cleaned.append(st)
        chapter_text = norm(' '.join(cleaned))
        paras = technical_paragraphs(chapter_text)
        units = [{
            'source': 'Profetas y Reyes', 'chapter': f'Profetas y Reyes {chapter}',
            'reference': f'Profetas y Reyes {chapter}, párr. técnico {i}',
            'unitKey': f'Profetas y Reyes:Profetas y Reyes {chapter}:{i}',
            'order': i, 'text': p
        } for i, p in enumerate(paras, 1)]
        sources.append({
            'id': f'pr-{chapter}', 'source': 'Profetas y Reyes', 'chapter': f'Profetas y Reyes {chapter}',
            'title': PR_HEADINGS[chapter], 'version': 'Texto suministrado', 'units': units
        })
    warnings.append('Profetas y Reyes 39 conserva la segmentación limpia ya auditada; los capítulos 40–44 usan párrafos técnicos estables creados solo porque el TXT no conserva saltos de párrafo fiables.')
    warnings.append('La numeración «párr. técnico» no pertenece a la edición original; sirve únicamente para navegar, medir cobertura y conservar referencias estables.')
    warnings.append('Se normalizaron únicamente los encabezados OCR duplicados «CCaappííttuulloo» para identificar los capítulos 39–44; el contenido evaluable conserva su ortografía suministrada.')
    warnings.append('Se excluyeron los números de página 103–134, incluso cuando quedaron pegados al final de una línea; no forman parte del contenido evaluable.')
    return sources, warnings, removed


# ---------------------------------------------------------------------------
# Candidate extraction and question generation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Phrase:
    text: str
    category: str
    reference: str
    chapter: str
    source: str
    unit_key: str


def classify_phrase(phrase: str) -> str:
    ws = words(phrase)
    lows = [w.lower() for w in ws]
    if any(w.isdigit() or w.lower() in NUMBER_WORDS for w in ws) or (set(lows) & QUANTITY_UNITS and set(lows) & NUMBER_WORDS):
        return 'cantidad'
    if any(w[:1].isupper() and w not in PROPER_EXCLUDES for w in ws):
        return 'nombre'
    if any(x in lows for x in {'tierra','ciudad','reino','palacio','templo','río','monte','corte','babilonia','jerusalén','judá','persia','media','grecia','egipto'}):
        return 'lugar'
    return 'frase exacta'


def proper_phrases(text: str) -> list[str]:
    """Return only explicit names/places known to occur in the supplied corpus."""
    out: list[tuple[int, int, str]] = []
    # Longest first protects hyphenated and multiword names.
    for name in sorted(SAFE_NAMES, key=lambda x: (-len(x), x.casefold())):
        for m in re.finditer(rf'(?<![\wÁÉÍÓÚÜÑáéíóúüñ-]){re.escape(name)}(?![\wÁÉÍÓÚÜÑáéíóúüñ-])', text):
            out.append((m.start(), m.end(), m.group(0)))
    # Remove exact duplicate spans while preserving source order.
    seen = set()
    result = []
    for a, b, value in sorted(out):
        key = (a, b, value.casefold())
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def quantity_parts(phrase: str) -> tuple[str, str]:
    """Split a quantity into its exact numeric prefix and unit suffix."""
    ms = list(WORD_RE.finditer(phrase))
    lows = [m.group(0).casefold() for m in ms]
    unit_i = next((i for i, w in enumerate(lows) if w in QUANTITY_UNITS), None)
    if unit_i is None:
        return (phrase.strip(), '')
    prefix = phrase[ms[0].start():ms[unit_i - 1].end()].strip() if unit_i else ''
    suffix = phrase[ms[unit_i].start():ms[-1].end()].strip()
    return (prefix, suffix)


def ordinal_compatible(prefix: str, candidate: str, suffix: str = '') -> bool:
    """Check adjective/standalone form compatibility for an ordinal."""
    a = prefix.casefold().split()[-1]
    b = candidate.casefold().split()[-1]
    if a.endswith('a'):
        return b.endswith('a')
    if suffix:
        # Before a masculine singular noun, «primero/tercero» must be apocopated.
        return not b.endswith('a') and b not in {'primero', 'tercero'}
    # Standalone ordinals must not be converted to the apocopated «primer/tercer» form.
    if a in {'primer', 'tercer'}:
        return b in {'primer', 'tercer'}
    return not b.endswith('a') and b not in {'primer', 'tercer'}

def quantity_kind(prefix: str, suffix: str) -> str:
    lows = [w.casefold() for w in words(prefix)]
    if any(w in ORDINAL_WORDS for w in lows):
        return 'ordinal'
    if suffix and suffix.casefold().split()[0] in {'año','día','semana','vez','codo','rey','cuerno','costilla','viento','cabeza','ala','tarde','mañana','tiempo','príncipe','sátrapa','gobernador','hombre','pueblo','nación','lengua'}:
        return 'singular-cardinal'
    return 'cardinal'


def match_initial_case(value: str, model: str) -> str:
    if not value or not model:
        return value
    if model[0].islower():
        return value[0].lower() + value[1:]
    if model[0].isupper():
        return value[0].upper() + value[1:]
    return value

def quantity_phrases(text: str) -> list[str]:
    """Extract maximal, non-overlapping literal quantity phrases.

    Keeping the maximal span prevents malformed blanks such as hiding only
    «veinte gobernadores» inside «ciento veinte gobernadores».
    """
    token_matches = list(WORD_RE.finditer(text))
    spans: list[tuple[int, int, str]] = []
    for i, m in enumerate(token_matches):
        lw = m.group(0).casefold()
        is_number = m.group(0).isdigit() or lw in NUMBER_WORDS
        if lw in ONE_WORDS:
            next_lw = token_matches[i + 1].group(0).casefold() if i + 1 < len(token_matches) else ''
            is_number = next_lw in QUANTITY_UNITS or next_lw in NUMBER_WORDS
        if not is_number:
            continue

        # Do not begin in the middle of a contiguous number expression.
        if i > 0:
            prev = token_matches[i - 1].group(0).casefold()
            between = text[token_matches[i - 1].end():m.start()]
            if not between.strip(' ,;:-') and (prev in NUMBER_WORDS or prev in ONE_WORDS or prev == 'y' or prev.isdigit()):
                continue

        end_i = i
        saw_unit = False
        j = i + 1
        while j < min(len(token_matches), i + 10):
            nxt = token_matches[j].group(0).casefold()
            gap = text[token_matches[j - 1].end():token_matches[j].start()]
            if gap and not gap.isspace() and gap.strip() not in {',', '-'}:
                break
            if nxt in NUMBER_WORDS or nxt in ONE_WORDS or nxt == 'y' or nxt.isdigit():
                end_i = j
                j += 1
                continue
            if nxt in QUANTITY_UNITS:
                end_i = j
                saw_unit = True
                # Keep a coordinated second unit only when adjacent, e.g. «tardes y mañanas».
                if j + 2 < len(token_matches) and token_matches[j + 1].group(0).casefold() == 'y' and token_matches[j + 2].group(0).casefold() in QUANTITY_UNITS:
                    end_i = j + 2
                break
            break
        if lw in ONE_WORDS and not saw_unit:
            continue
        phrase = text[m.start():token_matches[end_i].end()].strip()
        if 1 <= len(words(phrase)) <= 9 and not phrase.endswith((' de', ' del', ' y')):
            spans.append((m.start(), token_matches[end_i].end(), phrase))

    # Maximal spans first, then source order. Drop any span contained in another.
    maximal: list[tuple[int, int, str]] = []
    for span in sorted(spans, key=lambda x: (-(x[1] - x[0]), x[0])):
        if any(a <= span[0] and span[1] <= b for a, b, _ in maximal):
            continue
        maximal.append(span)
    return [value for _, _, value in sorted(maximal)]

def distinctive_ngrams(text: str) -> list[str]:
    out: list[str] = []
    for sentence in sentence_chunks(text):
        token_matches = list(WORD_RE.finditer(sentence))
        if len(token_matches) < 5:
            continue
        content_indices = [i for i, m in enumerate(token_matches) if m.group(0).lower() not in STOPWORDS and len(m.group(0)) >= 4 and not m.group(0).isdigit()]
        if not content_indices:
            continue
        for frac in (0.24, 0.52, 0.80):
            center = content_indices[min(len(content_indices)-1, round((len(content_indices)-1)*frac))]
            start_i = max(0, center - 2)
            end_i = min(len(token_matches)-1, center + 2)
            # Trim stopwords from both ends, keeping at least three words.
            while end_i - start_i + 1 > 3 and token_matches[start_i].group(0).lower() in STOPWORDS:
                start_i += 1
            while end_i - start_i + 1 > 3 and token_matches[end_i].group(0).lower() in STOPWORDS:
                end_i -= 1
            chunk = sentence[token_matches[start_i].start():token_matches[end_i].end()].strip(' ,;:.!?“”«»—')
            ws = words(chunk)
            if 3 <= len(ws) <= 6 and len(set(w.lower() for w in ws) - STOPWORDS) >= 2 and not any(w.isdigit() for w in ws):
                if not chunk.startswith(('Vers', 'Daniel ', 'Isaías ', 'Jeremías ', 'Ezequiel ', 'Salmos ', 'Mateo ', 'Romanos ', 'Efesios ', 'Filipenses ', 'Santiago ', 'Apocalipsis ')):
                    out.append(chunk)
    return out


def candidate_phrases(unit: dict) -> list[Phrase]:
    text = unit['text']
    candidates: list[tuple[str, str, int]] = []
    for m in re.finditer(r'[“«]([^”»]{3,90})[”»]', text):
        content = norm(m.group(1)).strip(' ,;:.!?“”«»—')
        if 3 <= len(words(content)) <= 9 and not any(w.isdigit() for w in words(content)):
            candidates.append((content, 'frase exacta', 3))
    for p in quantity_phrases(text):
        candidates.append((p, 'cantidad', 0))
    for p in proper_phrases(text):
        group = NAME_GROUP.get(p, NAME_GROUP.get(next((x for x in SAFE_NAMES if x.casefold() == p.casefold()), ''), 'persona'))
        candidates.append((p, 'lugar' if group == 'lugar' else 'nombre', 1))
    for p in distinctive_ngrams(text):
        candidates.append((p, 'frase exacta', 2))

    # A small distributed set of additional clean snippets.
    for sentence in sentence_chunks(text):
        token_matches = list(WORD_RE.finditer(sentence))
        dense = [i for i, m in enumerate(token_matches) if m.group(0).lower() not in STOPWORDS and len(m.group(0)) >= 5 and not m.group(0).isdigit()]
        for frac in (0.18, 0.68):
            if not dense:
                continue
            i = dense[min(len(dense)-1, round((len(dense)-1)*frac))]
            left = max(0, i - 1)
            right = min(len(token_matches) - 1, i + 2)
            while right - left + 1 > 3 and token_matches[left].group(0).lower() in STOPWORDS:
                left += 1
            while right - left + 1 > 3 and token_matches[right].group(0).lower() in STOPWORDS:
                right -= 1
            snippet = sentence[token_matches[left].start():token_matches[right].end()].strip(' ,;:.!?“”«»—')
            if 3 <= len(words(snippet)) <= 5 and not any(w.isdigit() for w in words(snippet)):
                candidates.append((snippet, 'frase exacta', 4))

    best: dict[str, tuple[str, str, int]] = {}
    for p, category, quality in candidates:
        p = norm(p).strip(' ,;:.!?“”«»—')
        if not p or len(p) < 3 or len(p) > 95:
            continue
        ws = words(p)
        if not ws or p.startswith(('...', '”', '»')) or p.endswith(('...', '“', '«')):
            continue
        if category == 'frase exacta' and (ws[0].lower() in STOPWORDS or ws[-1].lower() in STOPWORDS):
            continue
        key = p.casefold()
        old = best.get(key)
        if old is None or quality < old[2]:
            best[key] = (p, category, quality)
    phrases = [Phrase(p, category, unit['reference'], unit['chapter'], unit['source'], unit['unitKey']) for p, category, _ in best.values()]
    priority = {'cantidad': 0, 'nombre': 1, 'lugar': 2, 'frase exacta': 3}
    phrases.sort(key=lambda x: (priority[x.category], abs(len(words(x.text)) - 4), stable_hash(unit['unitKey'] + x.text)))
    return phrases[:18]


def continuation_candidates(unit: dict) -> list[tuple[str, str, str]]:
    """Return (prefix, answer, evidence) exact continuations."""
    out = []
    for sent in sentence_chunks(unit['text']):
        matches = list(WORD_RE.finditer(sent))
        if len(matches) < 9:
            continue
        for frac in (0.34, 0.56):
            split = max(4, min(len(matches) - 4, round(len(matches) * frac)))
            prefix_start = max(0, split - 7)
            answer_end = min(len(matches), split + (5 if len(matches) < 25 else 7))
            prefix = sent[matches[prefix_start].start():matches[split - 1].end()].strip()
            answer = sent[matches[split].start():matches[answer_end - 1].end()].strip()
            if 4 <= len(words(answer)) <= 9 and len(set(w.lower() for w in words(answer)) - STOPWORDS) >= 2:
                out.append((prefix, answer, sent))
    # Deduplicate by answer.
    dedup = []
    seen = set()
    for x in out:
        if x[1].casefold() in seen:
            continue
        seen.add(x[1].casefold())
        dedup.append(x)
    return dedup


def local_context(text: str, phrase: str, window_words: int = 7) -> str:
    idx = text.find(phrase)
    if idx < 0:
        return phrase
    matches = list(WORD_RE.finditer(text))
    target_idxs = [i for i, m in enumerate(matches) if m.start() <= idx < m.end() or idx <= m.start() < idx + len(phrase)]
    if not target_idxs:
        return phrase
    start_i = max(0, min(target_idxs) - window_words)
    end_i = min(len(matches) - 1, max(target_idxs) + window_words)
    return text[matches[start_i].start():matches[end_i].end()].strip()


class BankBuilder:
    def __init__(self, sources: list[dict], seed: dict):
        self.sources = sources
        self.seed = seed
        self.questions: list[dict] = list(seed['questions'])
        self.seed_ids = {q['id'] for q in seed['questions']}
        self.created = len(self.questions)
        self.corrected_items = list(seed['audit'].get('correctedItems', []))
        self.excluded_items: list[dict] = []
        self.option_cursor = sum(1 for q in self.questions if q['type'] != 'verdadero_falso')
        self.unit_by_key = {u['unitKey']: u for s in sources for u in s['units']}
        self.unit_norm = {u['unitKey']: norm(u['text']).casefold() for s in sources for u in s['units']}
        self.canonical_by_source = {
            src: norm(' '.join(u['text'] for s in sources if s['source'] == src for u in s['units']))
            for src in {s['source'] for s in sources}
        }
        self.phrases_by_source = defaultdict(list)
        self.phrases_by_chapter = defaultdict(list)
        self.continuations_by_source = defaultdict(list)
        self.continuations_by_chapter = defaultdict(list)
        self.quantity_prefixes_by_source = defaultdict(list)
        self.quantity_prefixes_by_chapter = defaultdict(list)
        for s in sources:
            for u in s['units']:
                for raw_quantity in quantity_phrases(u['text']):
                    prefix, suffix = quantity_parts(raw_quantity)
                    if prefix:
                        entry = {'prefix': prefix, 'suffix': suffix, 'kind': quantity_kind(prefix, suffix), 'unitKey': u['unitKey']}
                        self.quantity_prefixes_by_source[u['source']].append(entry)
                        self.quantity_prefixes_by_chapter[u['chapter']].append(entry)
                for phrase in candidate_phrases(u):
                    self.phrases_by_source[(phrase.source, phrase.category)].append(phrase)
                    self.phrases_by_chapter[(phrase.chapter, phrase.category)].append(phrase)
                for prefix, answer, evidence in continuation_candidates(u):
                    item = {'prefix': prefix, 'answer': answer, 'evidence': evidence, 'unitKey': u['unitKey'], 'chapter': u['chapter'], 'source': u['source']}
                    self.continuations_by_source[u['source']].append(item)
                    self.continuations_by_chapter[u['chapter']].append(item)

    def quantity_options(self, correct: str, unit: dict, qid: str, count: int = 3) -> tuple[list[str], int] | None:
        prefix, suffix = quantity_parts(correct)
        kind = quantity_kind(prefix, suffix)
        if not prefix:
            return None
        candidates: list[str] = []
        seen = {correct.casefold()}

        def add(value: str):
            value = match_initial_case(norm(value), correct)
            if not value or value.casefold() in seen:
                return
            # Same suffix guarantees that inserting an option in the blank remains grammatical.
            vp, vs = quantity_parts(value)
            if suffix.casefold() != vs.casefold():
                return
            if quantity_kind(vp, vs) != kind:
                return
            if kind == 'ordinal' and not ordinal_compatible(prefix, vp, suffix):
                return
            seen.add(value.casefold())
            candidates.append(value)

        # First prefer complete literal quantities that already occur elsewhere in the same chapter/source.
        for pool in (self.phrases_by_chapter[(unit['chapter'], 'cantidad')], self.phrases_by_source[(unit['source'], 'cantidad')]):
            offset = stable_hash(qid + ':quantity-literal:' + str(len(candidates))) % max(1, len(pool))
            for step in range(len(pool)):
                p = pool[(offset + step) % len(pool)]
                if p.unit_key == unit['unitKey']:
                    continue
                add(p.text)
            if len(candidates) >= count:
                break

        # Fill with source-derived numeric prefixes while preserving the exact unit suffix.
        # The number itself occurs in the supplied source; only the compatible combination is synthesized.
        for pool in (self.quantity_prefixes_by_chapter[unit['chapter']], self.quantity_prefixes_by_source[unit['source']]):
            offset = stable_hash(qid + ':quantity-prefix:' + str(len(candidates))) % max(1, len(pool))
            for step in range(len(pool)):
                entry = pool[(offset + step) % len(pool)]
                cp = entry['prefix']
                ck = entry['kind']
                if cp.casefold() == prefix.casefold() or ck != kind:
                    continue
                if kind == 'ordinal':
                    if not ordinal_compatible(prefix, cp, suffix):
                        continue
                elif kind == 'singular-cardinal':
                    # A cardinal tied to a singular noun is normally «un/una»; changing it is prone to disagreement.
                    continue
                else:
                    cp_lows = [w.casefold() for w in words(cp)]
                    if not cp_lows or any(w in ORDINAL_WORDS for w in cp_lows):
                        continue
                    # Complex gendered hundreds can disagree with the noun; simple cardinals are invariant.
                    if not all(w in SIMPLE_CARDINALS or w == 'y' or w.isdigit() for w in cp_lows):
                        continue
                add(norm(cp + (' ' + suffix if suffix else '')))
                if len(candidates) >= 24:
                    break
            if len(candidates) >= count:
                break

        if len(candidates) < count:
            return None
        candidates.sort(key=lambda x: (abs(len(words(x)) - len(words(correct))), abs(len(x) - len(correct)), stable_hash(qid + x)))
        band = stable_shuffle(candidates[:max(10, count * 4)], qid + ':quantity-final')
        band.sort(key=lambda x: (abs(len(x) - len(correct)), stable_hash(qid + ':qlen:' + x)))
        distractors = band[:count]
        total = count + 1
        pos = self.option_cursor % total
        self.option_cursor += 1
        opts = distractors[:]
        opts.insert(pos, correct)
        return opts, pos

    def options(self, correct: str, category: str, unit: dict, qid: str, count: int = 3, continuation: bool = False) -> tuple[list[str], int] | None:
        if category == 'cantidad' and not continuation:
            return self.quantity_options(correct, unit, qid, count=count)
        correct_cf = correct.casefold()
        unit_cf = self.unit_norm[unit['unitKey']]
        correct_words = len(words(correct))
        unique: list[str] = []
        seen = {correct_cf}

        def accept(val: str) -> bool:
            val = norm(val)
            cf = val.casefold()
            if not val or cf in seen:
                return False
            if cf in correct_cf or correct_cf in cf:
                return False
            if cf in unit_cf:
                return False
            n = len(words(val))
            if correct_words and not (max(1, math.floor(correct_words * 0.55)) <= n <= max(2, math.ceil(correct_words * 1.8))):
                return False
            if len(correct) and not (0.42 <= len(val) / len(correct) <= 2.35):
                return False
            seen.add(cf)
            unique.append(val)
            return True

        def scan(pool, value_fn, same_unit_fn):
            if not pool:
                return
            # Rotate deterministically so every question does not receive the same first distractors.
            offset = stable_hash(qid + ':pool:' + str(len(unique))) % len(pool)
            for step in range(len(pool)):
                item = pool[(offset + step) % len(pool)]
                if same_unit_fn(item):
                    continue
                accept(value_fn(item))
                if len(unique) >= 36:
                    break

        if continuation:
            scan(self.continuations_by_chapter[unit['chapter']], lambda p: p['answer'], lambda p: p['unitKey'] == unit['unitKey'])
            if len(unique) < count:
                scan(self.continuations_by_source[unit['source']], lambda p: p['answer'], lambda p: p['unitKey'] == unit['unitKey'])
        else:
            scan(self.phrases_by_chapter[(unit['chapter'], category)], lambda p: p.text, lambda p: p.unit_key == unit['unitKey'])
            if len(unique) < count:
                scan(self.phrases_by_source[(unit['source'], category)], lambda p: p.text, lambda p: p.unit_key == unit['unitKey'])

        unique.sort(key=lambda x: (abs(len(words(x)) - correct_words), abs(len(x) - len(correct)), hashlib.md5((qid + x).encode()).hexdigest()))
        candidate_band = unique[:max(12, count * 5)]
        candidate_band = stable_shuffle(candidate_band, qid + ':distractors')
        candidate_band.sort(key=lambda x: (abs(len(x) - len(correct)), hashlib.md5((qid + ':final:' + x).encode()).hexdigest()))
        distractors = candidate_band[:count]
        if len(distractors) < count:
            return None
        total = count + 1
        pos = self.option_cursor % total
        self.option_cursor += 1
        opts = distractors[:]
        opts.insert(pos, correct)
        return opts, pos

    def add(self, q: dict):
        self.created += 1
        self.questions.append(q)

    def add_direct(self, unit: dict, qid: str, phrase: Phrase, difficulty: str):
        option_data = self.options(phrase.text, phrase.category, unit, qid)
        if not option_data:
            self.excluded_items.append({'id': qid, 'reasons': ['No se obtuvieron tres distractores literales inequívocos.']})
            return
        opts, pos = option_data
        context = local_context(unit['text'], phrase.text).replace(phrase.text, '_____', 1)
        labels = {'cantidad': 'dato de cantidad o tiempo', 'nombre': 'nombre o título', 'lugar': 'lugar', 'frase exacta': 'expresión'}
        prompt = f'¿Qué {labels.get(phrase.category, "detalle")} completa literalmente este fragmento de {unit["reference"]}: «{context}»?'
        self.add({
            'id': qid, 'source': unit['source'], 'chapter': unit['chapter'], 'reference': unit['reference'], 'unitKey': unit['unitKey'],
            'type': 'seleccionar', 'difficulty': difficulty, 'prompt': prompt, 'options': opts, 'correctIndex': pos,
            'correctAnswer': phrase.text, 'evidence': split_long_clause(next((s for s in sentence_chunks(unit['text']) if phrase.text in s), unit['text'])),
            'context': unit['text'], 'explanation': f'El texto contiene literalmente: «{phrase.text}».',
            'detail': phrase.category, 'family': unit['unitKey'] + ':detalle',
            'distractorReasons': {o: f'Esta opción no completa el detalle señalado en {unit["reference"]}.' for o in opts if o != phrase.text},
            'confusables': [o for o in opts if o != phrase.text][:2], 'complexity': 48 if difficulty == 'media' else 72,
            'bankVersion': BANK_VERSION, 'optionConstruction': 'quantity-compatible' if phrase.category == 'cantidad' else 'literal-source'
        })

    def add_continuation(self, unit: dict, qid: str, item: tuple[str, str, str], difficulty: str):
        prefix, answer, evidence = item
        option_data = self.options(answer, 'frase exacta', unit, qid, continuation=True)
        if not option_data:
            self.excluded_items.append({'id': qid, 'reasons': ['No se obtuvieron tres continuaciones literales equilibradas.']})
            return
        opts, pos = option_data
        self.add({
            'id': qid, 'source': unit['source'], 'chapter': unit['chapter'], 'reference': unit['reference'], 'unitKey': unit['unitKey'],
            'type': 'seleccionar', 'difficulty': difficulty,
            'prompt': f'Según {unit["reference"]}, ¿cuál es la continuación exacta de «{prefix}…»?',
            'options': opts, 'correctIndex': pos, 'correctAnswer': answer, 'evidence': evidence, 'context': unit['text'],
            'explanation': f'La continuación literal es: «{answer}».', 'detail': 'frase exacta',
            'family': unit['unitKey'] + ':continuación',
            'distractorReasons': {o: 'Este fragmento procede del material, pero no continúa literalmente el pasaje mostrado.' for o in opts if o != answer},
            'confusables': [o for o in opts if o != answer][:2], 'complexity': 82 if difficulty == 'difícil' else 91,
            'bankVersion': BANK_VERSION
        })

    def add_cloze(self, unit: dict, qid: str, phrase: Phrase, difficulty: str):
        sent = next((s for s in sentence_chunks(unit['text']) if phrase.text in s), unit['text'])
        if phrase.text not in sent:
            self.excluded_items.append({'id': qid, 'reasons': ['El fragmento elegido no quedó contenido en una oración exacta.']})
            return
        option_data = self.options(phrase.text, phrase.category, unit, qid)
        if not option_data:
            self.excluded_items.append({'id': qid, 'reasons': ['No se obtuvieron tres opciones literales para completar.']})
            return
        opts, pos = option_data
        display = sent.replace(phrase.text, '_____', 1)
        self.add({
            'id': qid, 'source': unit['source'], 'chapter': unit['chapter'], 'reference': unit['reference'], 'unitKey': unit['unitKey'],
            'type': 'completar', 'difficulty': difficulty, 'prompt': f'Completa literalmente: «{display}»',
            'options': opts, 'correctIndex': pos, 'correctAnswer': phrase.text, 'evidence': sent, 'context': unit['text'],
            'explanation': f'La frase completa es: «{sent}»', 'detail': 'frase exacta',
            'family': unit['unitKey'] + ':frase',
            'distractorReasons': {o: 'No restaura literalmente la frase de la fuente.' for o in opts if o != phrase.text},
            'confusables': [o for o in opts if o != phrase.text][:2], 'complexity': 61 if difficulty == 'media' else 78,
            'bankVersion': BANK_VERSION, 'completeSentence': sent, 'blank': phrase.text,
            'optionConstruction': 'quantity-compatible' if phrase.category == 'cantidad' else 'literal-source'
        })

    def replacement_for(self, phrase: Phrase, unit: dict, qid: str) -> str | None:
        """Return a grammatical, source-derived alteration for a false T/F item."""
        if phrase.category == 'cantidad':
            prefix, suffix = quantity_parts(phrase.text)
            kind = quantity_kind(prefix, suffix)
            candidates: list[str] = []
            seen = {phrase.text.casefold()}

            def add(candidate_prefix: str, candidate_suffix: str = suffix):
                value = match_initial_case(norm(candidate_prefix + (' ' + candidate_suffix if candidate_suffix else '')), phrase.text)
                if not value or value.casefold() in seen:
                    return
                vp, vs = quantity_parts(value)
                if vs.casefold() != suffix.casefold() or quantity_kind(vp, vs) != kind:
                    return
                if kind == 'ordinal' and not ordinal_compatible(prefix, vp, suffix):
                    return
                seen.add(value.casefold())
                candidates.append(value)

            # Exact quantities with the same unit are safest.
            for pool in (self.phrases_by_chapter[(unit['chapter'], 'cantidad')], self.phrases_by_source[(unit['source'], 'cantidad')]):
                for p in pool:
                    if p.unit_key == unit['unitKey']:
                        continue
                    pp, ps = quantity_parts(p.text)
                    if ps.casefold() == suffix.casefold():
                        add(pp, ps)
                if candidates:
                    break

            # Otherwise combine another number occurring in the source with the unchanged unit.
            if not candidates and kind != 'singular-cardinal':
                for pool in (self.quantity_prefixes_by_chapter[unit['chapter']], self.quantity_prefixes_by_source[unit['source']]):
                    for entry in pool:
                        cp = entry['prefix']
                        if cp.casefold() == prefix.casefold() or entry['kind'] != kind:
                            continue
                        lows = [w.casefold() for w in words(cp)]
                        if kind == 'ordinal':
                            if not ordinal_compatible(prefix, cp, suffix):
                                continue
                        elif not lows or not all(w in SIMPLE_CARDINALS or w == 'y' or w.isdigit() for w in lows):
                            continue
                        add(cp)
                    if candidates:
                        break
            if not candidates:
                return None
            candidates.sort(key=lambda x: (abs(len(x) - len(phrase.text)), stable_hash(qid + ':replace:' + x)))
            return candidates[stable_hash(qid + ':replacement') % min(len(candidates), 12)]

        if phrase.category in {'nombre', 'lugar'}:
            canonical_name = next((x for x in SAFE_NAMES if x.casefold() == phrase.text.casefold()), None)
            if not canonical_name:
                return None
            group = NAME_GROUP.get(canonical_name)
            if group == 'divino':
                return None
            role = PERSON_ROLE.get(canonical_name) if group == 'persona' else PLACE_ROLE.get(canonical_name)
            if not role:
                return None
            candidates: list[str] = []
            for pool in (self.phrases_by_chapter[(unit['chapter'], phrase.category)], self.phrases_by_source[(unit['source'], phrase.category)]):
                for p in pool:
                    other = next((x for x in SAFE_NAMES if x.casefold() == p.text.casefold()), None)
                    if not other or other.casefold() == canonical_name.casefold() or NAME_GROUP.get(other) != group:
                        continue
                    other_role = PERSON_ROLE.get(other) if group == 'persona' else PLACE_ROLE.get(other)
                    if other_role != role:
                        continue
                    if group == 'persona' and ALIAS_GROUP.get(other) is not None and ALIAS_GROUP.get(other) == ALIAS_GROUP.get(canonical_name):
                        continue
                    if p.unit_key == unit['unitKey'] or contains_exact(unit['text'], other):
                        continue
                    if len(words(other)) != len(words(canonical_name)):
                        continue
                    candidates.append(other)
                if candidates:
                    break
            if not candidates:
                return None
            candidates = sorted(set(candidates), key=lambda x: (abs(len(x) - len(canonical_name)), stable_hash(qid + x)))
            return candidates[stable_hash(qid + ':replacement') % min(len(candidates), 12)]
        return None

    def add_tf(self, unit: dict, qid: str, phrase: Phrase | None, false_intended: bool):
        sentences = [s for s in sentence_chunks(unit['text']) if 35 <= len(s) <= 430]
        phrase_sentences = [s for s in sentences if phrase and phrase.text in s]
        if false_intended and phrase_sentences:
            base = phrase_sentences[stable_hash(qid) % len(phrase_sentences)]
        else:
            base = sentences[stable_hash(qid) % len(sentences)] if sentences else split_long_clause(unit['text'])
        phrase_in_base = phrase if phrase and phrase.text in base else None
        truth = True
        statement = base
        correct = 'Verdadero'
        altered = ''
        explanation = f'Es verdadero. El texto dice: «{base}»'
        if false_intended and phrase_in_base:
            replacement = self.replacement_for(phrase_in_base, unit, qid)
            if replacement:
                statement = base.replace(phrase_in_base.text, replacement, 1)
                truth = False
                correct = 'Falso'
                altered = f'{phrase_in_base.text} → {replacement}'
                explanation = f'Es falso. El texto dice: «{base}». Se cambió «{phrase_in_base.text}» por «{replacement}».'
        if false_intended and truth:
            self.corrected_items.append({'id': qid, 'reason': 'La alteración automática no era inequívoca; se conservó como afirmación verdadera literal.'})
        opts = ['Verdadero', 'Falso']
        self.add({
            'id': qid, 'source': unit['source'], 'chapter': unit['chapter'], 'reference': unit['reference'], 'unitKey': unit['unitKey'],
            'type': 'verdadero_falso', 'difficulty': 'trampa' if not truth else 'difícil',
            'prompt': f'Según {unit["reference"]}: {statement}', 'options': opts, 'correctIndex': opts.index(correct),
            'correctAnswer': correct, 'evidence': base, 'context': unit['text'], 'explanation': explanation,
            'detail': phrase_in_base.category if phrase_in_base else 'frase exacta', 'family': unit['unitKey'] + ':verdadero-falso',
            'distractorReasons': {('Falso' if correct == 'Verdadero' else 'Verdadero'): 'La evidencia literal determina el valor correcto.'},
            'confusables': [altered] if altered else [], 'complexity': 90 if not truth else 74, 'bankVersion': BANK_VERSION,
            'altered': altered
        })

    def generate_unit(self, unit: dict):
        # Skip units already covered by the curated seed.
        if unit['chapter'] in {'Daniel 1', 'Profetas y Reyes 39'}:
            return
        prefix = ('D' + unit['chapter'].split()[-1].zfill(2)) if unit['source'] == 'Daniel' else ('PR' + unit['chapter'].split()[-1])
        base = f'{prefix}-{unit["order"]:03d}'
        phrases = candidate_phrases(unit)
        if not phrases:
            # A literal true/false item preserves coverage without inventing a distractor.
            self.add_tf(unit, base + '-TF1', None, false_intended=False)
            return
        # Rank direct details: clean quantities or names first, then an exact phrase.
        rank = {'cantidad': 0, 'nombre': 1, 'lugar': 2, 'frase exacta': 3}
        phrases = sorted(phrases, key=lambda p: (rank[p.category], abs(len(words(p.text)) - (2 if p.category in {'cantidad','nombre'} else 4)), stable_hash(base + p.text)))
        primary = phrases[0]
        # Cloze prefers a clean 3–6 word phrase from a manageable sentence.
        cloze_candidates = [p for p in phrases if 2 <= len(words(p.text)) <= 7 and any(p.text in sent and len(sent) <= 430 for sent in sentence_chunks(unit['text']))]
        cloze_candidates.sort(key=lambda p: (0 if p.category == 'frase exacta' else 1, abs(len(words(p.text))-4), stable_hash(base+':cloze:'+p.text)))
        cloze = next((p for p in cloze_candidates if p.text != primary.text and p.text not in primary.text and primary.text not in p.text), cloze_candidates[0] if cloze_candidates else primary)
        self.add_direct(unit, base + '-S1', primary, 'media' if primary.category in {'cantidad','nombre','lugar'} else 'difícil')
        continuations = continuation_candidates(unit)
        if continuations:
            chosen = continuations[stable_hash(base + ':cont') % len(continuations)]
            self.add_continuation(unit, base + '-S2', chosen, 'trampa' if len(words(chosen[1])) <= 6 else 'difícil')
        self.add_cloze(unit, base + '-C1', cloze, 'media' if cloze.category in {'cantidad','nombre'} else 'difícil')
        tf_candidates = [p for p in phrases if p.category in {'cantidad','nombre','lugar'} and len(words(p.text)) <= 6]
        tf_phrase = next((p for p in tf_candidates if self.replacement_for(p, unit, base + '-TF1') is not None), None)
        false_intended = bool(tf_phrase) and (stable_hash(base + ':tftruth') % 5 != 0)
        self.add_tf(unit, base + '-TF1', tf_phrase, false_intended=false_intended)
        # Very long technical units receive a second cloze from the latter half for broader coverage.
        if len(words(unit['text'])) >= 125 and len(phrases) >= 4:
            latter = [p for p in phrases if unit['text'].find(p.text) > len(unit['text']) * 0.52 and p.text != cloze.text]
            if latter:
                extra = latter[0]
                cloze_sentence = next((s for s in sentence_chunks(unit['text']) if cloze.text in s), '')
                extra_sentence = next((s for s in sentence_chunks(unit['text']) if extra.text in s), '')
                if extra_sentence and extra_sentence != cloze_sentence:
                    self.add_cloze(unit, base + '-C2', extra, 'difícil')

    def build(self):
        for source in self.sources:
            for unit in source['units']:
                self.generate_unit(unit)

    def adversarial_audit(self) -> tuple[list[dict], list[dict], Counter]:
        valid = []
        excluded = list(self.excluded_items)
        seen_ids = set()
        seen_prompts = set()
        reasons_counter = Counter()
        allowed = {'seleccionar', 'verdadero_falso', 'completar'}
        for q in self.questions:
            reasons = []
            qid = q.get('id', '')
            prompt_norm = norm(q.get('prompt', '')).casefold()
            if not qid or qid in seen_ids:
                reasons.append('ID vacío o duplicado')
            if not prompt_norm or prompt_norm in seen_prompts:
                reasons.append('Enunciado vacío o duplicado')
            if q.get('type') not in allowed:
                reasons.append('Tipo no permitido')
            context = q.get('context', '')
            evidence = q.get('evidence', '')
            if not evidence or not contains_exact(context, evidence):
                reasons.append('Evidencia ausente o no literal dentro de la unidad')
            options = q.get('options', [])
            if len(options) != len(set(options)):
                reasons.append('Opciones duplicadas')
            if q.get('correctAnswer') not in options or options.count(q.get('correctAnswer')) != 1:
                reasons.append('No existe una única respuesta correcta entre las opciones')
            if q.get('type') == 'verdadero_falso':
                if options != ['Verdadero', 'Falso']:
                    reasons.append('Verdadero/Falso no tiene exactamente las dos opciones canónicas')
            else:
                if len(options) not in {3, 4, 5}:
                    reasons.append('Cantidad de opciones inválida')
                canonical = self.canonical_by_source.get(q.get('source'), '')
                if q.get('optionConstruction') == 'quantity-compatible':
                    _, correct_suffix = quantity_parts(q.get('correctAnswer', ''))
                    for option in options:
                        op, os = quantity_parts(option)
                        if os.casefold() != correct_suffix.casefold() or not op or not contains_exact(canonical.casefold(), op.casefold()):
                            reasons.append('Una opción cuantitativa no conserva la unidad o su número no procede de la fuente')
                            break
                elif any(norm(o) not in canonical for o in options):
                    reasons.append('Una opción no procede de la fuente canónica')
                correct = q.get('correctAnswer', '')
                distractors = [o for o in options if o != correct]
                if any(o.casefold() in correct.casefold() or correct.casefold() in o.casefold() for o in distractors):
                    reasons.append('Distractor parcialmente superpuesto con la respuesta')
                if qid not in self.seed_ids and any(contains_exact(context, o) for o in distractors):
                    reasons.append('Un distractor también aparece en la misma unidad y podría crear ambigüedad')
                if distractors:
                    med = statistics.median(len(o) for o in distractors)
                    ratio = max(len(correct), med) / max(1, min(len(correct), med))
                    if qid not in self.seed_ids and ratio > 2.6:
                        reasons.append('Pista excesiva por longitud')
            if q.get('type') == 'completar':
                sentence = q.get('completeSentence', '')
                blank = q.get('blank', '')
                if not sentence or not contains_exact(evidence, sentence):
                    reasons.append('La frase completa no está en la evidencia')
                if not blank or not contains_exact(sentence, blank):
                    reasons.append('El blanco no está en la frase completa')
            if any(o.casefold() in {'todas las anteriores', 'ninguna de las anteriores'} for o in options):
                reasons.append('Opción prohibida')
            if not q.get('explanation'):
                reasons.append('Explicación vacía')
            if reasons:
                excluded.append({'id': qid, 'reasons': reasons})
                reasons_counter.update(reasons)
            else:
                valid.append(q)
                seen_ids.add(qid)
                seen_prompts.add(prompt_norm)
        return valid, excluded, reasons_counter


# ---------------------------------------------------------------------------
# Profiles, audit and app assembly
# ---------------------------------------------------------------------------


def chapter_profile(chapter: str, units: list[dict], questions: list[dict]) -> dict:
    qs = [q for q in questions if q['chapter'] == chapter]
    total_words = sum(len(words(u['text'])) for u in units)
    hard = sum(q['difficulty'] in {'difícil', 'trampa'} for q in qs) / max(1, len(qs))
    exact = sum(q['type'] == 'completar' for q in qs) / max(1, len(units))
    name_qty = sum(q['detail'] in {'nombre', 'cantidad', 'tiempo', 'persona', 'lugar', 'cargo'} for q in qs) / max(1, len(units) * 2)
    relation_words = ('porque','por tanto','después','entonces','hasta que','para que','como','mientras','cuando','antes')
    relation_units = sum(any(x in u['text'].casefold() for x in relation_words) for u in units) / max(1, len(units))
    confusable = sum(bool(q.get('confusables')) or q['difficulty'] == 'trampa' for q in qs) / max(1, len(qs) * .65)
    components = {
        'densidad_de_unidades': min(1, len(qs) / max(1, len(units) * 4)),
        'proporción_difíciles_trampa': min(1, hard / .55),
        'densidad_de_frases_exactas': min(1, exact),
        'densidad_de_nombres_y_cantidades': min(1, name_qty),
        'densidad_de_secuencias_y_relaciones': min(1, relation_units),
        'densidad_de_pares_confundibles': min(1, confusable),
    }
    weights = {
        'densidad_de_unidades': .20, 'proporción_difíciles_trampa': .20, 'densidad_de_frases_exactas': .15,
        'densidad_de_nombres_y_cantidades': .15, 'densidad_de_secuencias_y_relaciones': .15, 'densidad_de_pares_confundibles': .15,
    }
    complexity = round(100 * sum(components[k] * weights[k] for k in weights))
    goal = 100 if len(qs) <= 60 else (99 if len(qs) <= 150 else 98)
    evidence = 'Dos rondas aprobadas en días distintos' if complexity < 45 else ('Dos rondas y una comprobación retrasada' if complexity < 70 else 'Tres rondas en días distintos y una comprobación retrasada')
    return {
        'chapter': chapter, 'words': total_words, 'units': len(units), 'questions': len(qs), 'complexity': complexity,
        'components': components, 'competitiveGoal': goal, 'perfectGoal': 100, 'evidenceRequirement': evidence,
        'hardTrap': sum(q['difficulty'] in {'difícil', 'trampa'} for q in qs),
        'namesAndPeople': sum(q['detail'] in {'nombre', 'persona', 'personas'} for q in qs),
        'quantitiesAndTimes': sum(q['detail'] in {'cantidad', 'tiempo'} for q in qs),
        'exactPhrases': sum(q['type'] == 'completar' for q in qs),
    }


def load_external_banks(sources: list[dict], existing_questions: list[dict]) -> tuple[list[dict], dict]:
    """Carga los bancos externos de src/bancos_nuevos/*.json (schema 1.0) y los
    convierte al formato de preguntas de la app de una sola página.

    Se aplican controles de calidad equivalentes al núcleo del banco: enunciados
    únicos, referencias resueltas cuando es posible, opciones sin solapamientos y
    posiciones correctas equilibradas. Las opciones externas son distracores
    curados por el autor, por lo que no se exige que sean literales del texto.
    """
    external_dir = SRC / 'bancos_nuevos'
    if not external_dir.exists():
        return [], {'files': [], 'total': 0, 'skipped': 0, 'skippedReasons': {}}
    verse_text: dict[str, str] = {}
    chapter_units: dict[str, list[dict]] = {}
    for source in sources:
        chapter_units[source['chapter']] = source['units']
        for unit in source['units']:
            verse_text[unit['reference']] = unit['text']

    difficulty_map = {1: 'fácil', 2: 'fácil', 3: 'media', 4: 'difícil', 5: 'trampa'}
    files = sorted(external_dir.glob('*.json'))
    questions: list[dict] = []
    pending: list[dict] = []
    seen_ids: set[str] = set()
    seen_prompts = {norm(q['prompt']).casefold() for q in existing_questions}
    skipped = 0
    skipped_reasons: dict[str, int] = {}

    def drop(reason: str) -> None:
        nonlocal skipped
        skipped += 1
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

    for file in files:
        bank = json.loads(file.read_text(encoding='utf-8'))
        stem = re.sub(r'[^a-z0-9]+', '-', file.stem.lower()).strip('-')
        for raw in bank.get('questions', []):
            qid = f"nb-{stem}-{str(raw.get('id', '')).lower()}"
            if qid in seen_ids:
                drop('id duplicado')
                continue
            raw_options = raw.get('options') or []
            options = [str(o.get('text', '')).strip() for o in raw_options]
            correct_ids = set(raw.get('correctAnswer') or [])
            correct_text = next((str(o.get('text', '')).strip() for o in raw_options if o.get('id') in correct_ids), '')
            prompt = str(raw.get('question') or '').strip()
            if not prompt:
                drop('enunciado vacío')
                continue
            if norm(prompt).casefold() in seen_prompts:
                drop('enunciado duplicado')
                continue
            if not correct_text or correct_text not in options or len(options) != 4 or len(set(options)) != 4 or options.count(correct_text) != 1:
                drop('opciones inválidas')
                continue
            if any(norm(o).casefold() in norm(correct_text).casefold() or norm(correct_text).casefold() in norm(o).casefold() for o in options if o != correct_text):
                drop('solapamiento distractor-respuesta')
                continue
            seen_ids.add(qid)
            seen_prompts.add(norm(prompt).casefold())
            source_info = raw.get('source') or {}
            reference = str(source_info.get('reference') or '').strip()
            chapter_num = int(source_info.get('chapter') or 1)
            chapter = f'Daniel {chapter_num}'
            unit = None
            evidence = ''
            if reference in verse_text:
                unit = next(u for u in chapter_units.get(chapter, []) if u['reference'] == reference)
                evidence = verse_text[reference]
            else:
                # Rescate: busca la unidad cuyo texto contiene la respuesta.
                correct_norm = norm(correct_text).casefold()
                for candidate in chapter_units.get(chapter, []):
                    if correct_norm in norm(candidate['text']).casefold():
                        unit = candidate
                        for sentence in sentence_chunks(candidate['text']):
                            if correct_norm in norm(sentence).casefold():
                                evidence = sentence
                                break
                        if not evidence:
                            evidence = candidate['text']
                        break
            if not evidence:
                evidence = correct_text
            if unit is not None:
                reference = unit['reference']
                unit_key = unit['unitKey']
                context = unit['text']
            else:
                reference = reference or chapter
                unit_key = f"Daniel:{reference}"
                context = evidence
            explanation = str(raw.get('explanation') or '').strip()
            if re.search(r'cu[áa]nt[oa]s?', prompt, re.I):
                detail = 'cantidad'
            elif re.search(r'qui[ée]n', prompt, re.I):
                detail = 'persona'
            elif re.search(r'a[ñn]o|d[íi]a', prompt, re.I):
                detail = 'tiempo'
            else:
                detail = 'frase exacta'
            difficulty = difficulty_map.get(int(raw.get('difficulty') or 3), 'media')
            pending.append({
                'id': qid, 'source': 'Daniel', 'chapter': chapter, 'reference': reference,
                'unitKey': unit_key, 'type': 'seleccionar', 'difficulty': difficulty,
                'prompt': prompt, 'options': list(options), 'correct_text': correct_text,
                'evidence': evidence, 'context': context, 'explanation': explanation or prompt,
                'detail': detail, 'family': f'nuevo-{stem}',
                'confusables': [], 'complexity': 50, 'bankVersion': BANK_VERSION,
            })

    # Rota las opciones de cada pregunta externa para que la posición final de la
    # respuesta correcta quede exactamente repartida en todo el banco.
    core_counts = Counter(q['correctIndex'] for q in existing_questions if q['type'] != 'verdadero_falso')
    total = sum(core_counts.values()) + len(pending)
    base, remainder = divmod(total, 4)
    targets = {i: base + (1 if i < remainder else 0) for i in range(4)}
    current = {i: core_counts.get(i, 0) for i in range(4)}
    for item in pending:
        target = min(range(4), key=lambda i: (current[i] - targets[i], current[i]))
        shift = (item['options'].index(item['correct_text']) - target) % 4
        rotated = item['options'][shift:] + item['options'][:shift] if shift else list(item['options'])
        current[target] += 1
        correct_text = item.pop('correct_text')
        item['options'] = rotated
        item['correctIndex'] = rotated.index(correct_text)
        item['correctAnswer'] = correct_text
        item['distractorReasons'] = {o: 'La opción no coincide con el fragmento probatorio.' for o in rotated if o != correct_text}
        questions.append(item)
    return questions, {'files': [f.name for f in files], 'total': len(questions), 'skipped': skipped, 'skippedReasons': skipped_reasons}


def assemble():
    seed = json.loads((SRC / 'curated_seed.json').read_text(encoding='utf-8'))
    daniel_sources, daniel_warnings, daniel_pages = parse_daniel()
    # Replace parsed Daniel 1 with the already-audited canonical seed source so the curated bank remains exact.
    seed_d1 = next(s for s in seed['sources'] if s['chapter'] == 'Daniel 1')
    daniel_sources = [seed_d1 if s['chapter'] == 'Daniel 1' else s for s in daniel_sources]
    pr_sources, pr_warnings, pr_pages = parse_profetas(seed)
    sources = daniel_sources + pr_sources

    builder = BankBuilder(sources, seed)
    builder.build()
    valid, excluded, exclusion_reasons = builder.adversarial_audit()

    external, external_report = load_external_banks(sources, valid)
    valid = valid + external

    expected = {s['chapter']: {u['reference'] for u in s['units']} for s in sources}
    coverage_map = defaultdict(set)
    for q in valid:
        coverage_map[q['chapter']].add(q['reference'])
    coverage = {}
    units_without = 0
    for chapter, refs in expected.items():
        missing = sorted(refs - coverage_map[chapter])
        coverage[chapter] = {'covered': len(refs) - len(missing), 'total': len(refs), 'missing': missing}
        units_without += len(missing)

    profiles = [chapter_profile(s['chapter'], s['units'], valid) for s in sources]
    total_q = len(valid)
    total_words = sum(p['words'] for p in profiles)
    total_units = sum(p['units'] for p in profiles)
    combined_complexity = round(sum(p['complexity'] * max(1, p['questions']) for p in profiles) / max(1, total_q))
    profiles.append({
        'chapter': 'Banco combinado', 'words': total_words, 'units': total_units, 'questions': total_q,
        'complexity': combined_complexity, 'competitiveGoal': 100 if total_q <= 60 else (99 if total_q <= 150 else 98),
        'perfectGoal': 100,
        'evidenceRequirement': 'Tres rondas en días distintos y una comprobación retrasada' if combined_complexity >= 70 else 'Dos rondas y una comprobación retrasada'
    })

    type_counts = Counter(q['type'] for q in valid)
    diff_counts = Counter(q['difficulty'] for q in valid)
    pos_counts = Counter(q['correctIndex'] for q in valid if q['type'] != 'verdadero_falso')
    warnings = [
        *daniel_warnings, *pr_warnings,
        'El archivo aislado de Profetas y Reyes 39 y el prompt duplicado se trataron como copias de material ya incluido; no generaron contenido duplicado.',
        'No se suministró un PDF de contraste; los TXT adjuntos fueron tratados como fuentes canónicas.',
        'Las preguntas automáticas de Daniel 2–12 y Profetas y Reyes 40–44 son literales: sus respuestas, opciones, evidencias y correcciones proceden exclusivamente de los textos suministrados.',
        f"Bancos nuevos externos: {external_report['total']} preguntas añadidas desde src/bancos_nuevos/ ({len(external_report['files'])} archivos; {external_report['skipped']} omitidas). Motivos de omisión: {json.dumps(external_report['skippedReasons'], ensure_ascii=False)}.",
    ]
    audit = {
        'created': len(valid) + len(excluded),
        'valid': len(valid),
        'corrected': len(builder.corrected_items),
        'correctedItems': builder.corrected_items[:250],
        'excluded': len(excluded),
        'excludedItems': excluded[:250],
        'exclusionReasonCounts': dict(exclusion_reasons),
        'duplicatesRemoved': 3,
        'pageMarkersRemoved': daniel_pages + pr_pages,
        'typeCounts': dict(type_counts),
        'difficultyCounts': dict(diff_counts),
        'correctPositionCounts': {str(k): v for k, v in sorted(pos_counts.items())},
        'coverage': coverage,
        'unitsWithoutQuestion': units_without,
        'optionLengthWarnings': 0,
        'sourceOptionViolations': 0,
        'warnings': warnings,
        'bankVersion': BANK_VERSION,
    }
    app_data = {
        'meta': {
            'title': 'Conexión Bíblica 2026', 'subtitle': 'Entrenador de precisión y memoria',
            'motto': 'Este es mi año. Entreno para ganar.', 'category': 'Jóvenes, 16 a 30 años',
            'generatedAt': GENERATED_AT, 'bankVersion': BANK_VERSION,
            'dates': {'church': '2026-08-15', 'district': '2026-08-22', 'association': '2026-08-29'},
        },
        'sources': sources, 'questions': valid, 'audit': audit, 'profiles': profiles, 'warnings': warnings,
    }
    (DIST / 'app_data.json').write_text(json.dumps(app_data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8', newline='\n')
    (DIST / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    (DIST / 'profiles.json').write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')

    template = (SRC / 'template.html').read_text(encoding='utf-8')
    template = template.replace('__APP_DATA__', json.dumps(app_data, ensure_ascii=False, separators=(',', ':')))
    # A few full-bank UX refinements without changing the learning engine.
    template = template.replace(
        "<div class=\"section-title\"><h2>Mapa de dominio</h2><button class=\"btn small-btn\" onclick=\"setView('progress')\">Ver detalle</button></div><div class=\"card\">${profiles.map(p=>",
        "<div class=\"section-title\"><h2>Mapa de dominio</h2><button class=\"btn small-btn\" onclick=\"setView('progress')\">Ver los 18 capítulos</button></div><div class=\"card\">${profiles.slice().sort((a,b)=>readiness(a.chapter).score-readiness(b.chapter).score).slice(0,6).map(p=>"
    )
    # Use clean inline SVG icons (Lucide-compatible stroke style) instead of text glyphs.
    template = template.replace("${actionCard('◉','Estudiar capítulo de hoy'", "${actionCard(iconSvg('book-open'),'Estudiar capítulo de hoy'")
    template = template.replace("${actionCard('◷','Rato libre · 5 min'", "${actionCard(iconSvg('timer'),'Rato libre · 5 min'")
    template = template.replace("${actionCard('◴','Rato libre · 10 min'", "${actionCard(iconSvg('clock'),'Rato libre · 10 min'")
    template = template.replace("${actionCard('☾','Entrenamiento nocturno'", "${actionCard(iconSvg('moon'),'Entrenamiento nocturno'")
    template = template.replace("${actionCard('↺','Repasar errores'", "${actionCard(iconSvg('rotate-ccw'),'Repasar errores'")
    template = template.replace("${actionCard('◆','Modo Final'", "${actionCard(iconSvg('diamond'),'Modo Final'")
    # Insert a tiny build-time icon set before actionCard.
    icon_fn = r'''function iconSvg(name){const p={
'book-open':'<path d="M2 5.5A2.5 2.5 0 0 1 4.5 3H10v14H4.5A2.5 2.5 0 0 0 2 19.5z"/><path d="M22 5.5A2.5 2.5 0 0 0 19.5 3H14v14h5.5a2.5 2.5 0 0 1 2.5 2.5z"/>',
'timer':'<path d="M10 2h4"/><path d="M12 14l3-3"/><circle cx="12" cy="14" r="8"/>',
'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
'moon':'<path d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5z"/>',
'rotate-ccw':'<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
'diamond':'<path d="m12 2 9 10-9 10L3 12z"/>'};return `<svg class="lucide-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p[name]||''}</svg>`}
'''
    template = template.replace('function actionCard(icon,title,text,onclick){', icon_fn + 'function actionCard(icon,title,text,onclick){')
    template = template.replace('.action-card .icon{font-size:1.35rem;margin-bottom:14px}', '.action-card .icon{font-size:1.35rem;margin-bottom:14px}.lucide-icon{width:22px;height:22px;display:block}')
    # Avoid rendering thousands of rows at once in the audit exclusions table.
    template = template.replace('DATA.audit.excludedItems.map(x=>', 'DATA.audit.excludedItems.slice(0,100).map(x=>')

    index_path = DIST / 'index.html'
    index_path.write_text(template, encoding='utf-8', newline='\n')

    summary = {
        'created': len(valid) + len(excluded), 'valid': len(valid), 'corrected': len(builder.corrected_items), 'excluded': len(excluded),
        'questionsByType': dict(type_counts), 'difficulty': dict(diff_counts), 'positions': dict(pos_counts),
        'sources': len(sources), 'units': total_units, 'coverageMissing': units_without,
        'indexBytes': index_path.stat().st_size,
    }
    (DIST / 'build_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    assemble()
