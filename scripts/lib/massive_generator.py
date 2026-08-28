"""Extracción y generación masiva determinista desde el PDF de competencia."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from dataclasses import replace
from typing import Any

import fitz

from scripts.lib.massive_bank import (
    AtomicFact,
    DIFFICULTY_RATIOS,
    MassiveQuestion,
    TYPE_RATIOS,
)


DANIEL_PAGE_MAP = {
    1: (3,),
    2: (4, 5, 6),
    3: (7, 8),
    4: (9, 10, 11),
    5: (12, 13),
    6: (14, 15),
    7: (16, 17),
    8: (18, 19),
    9: (20, 21),
    10: (22,),
    11: (23, 24),
    12: (25,),
}

DANIEL_LAST_VERSE = {
    1: 21,
    2: 49,
    3: 30,
    4: 37,
    5: 31,
    6: 28,
    7: 28,
    8: 27,
    9: 27,
    10: 21,
    11: 45,
    12: 13,
}

PR_PAGE_TOPICS = {
    27: "cautiverio, misión y cambio de nombres",
    28: "alimento real, vino e idolatría",
    29: "Melsar, prueba de diez días y templanza",
    30: "educación, salud y verdadero éxito",
    31: "cooperación divina, deberes pequeños y carácter",
    32: "aplicación a los jóvenes actuales",
    33: "sueño olvidado, sabios, amenaza y recompensa",
    34: "Daniel, Arioc, oración y visión nocturna",
    35: "imagen, metales, piedra y reinos",
    36: "honores, naciones y agentes divinos",
    37: "filosofía de la historia y propósito de Dios",
    38: "propósito del sueño y orgullo del rey",
    39: "estatua de oro, símbolo falseado y dedicación",
    40: "acusación y fidelidad de los tres hebreos",
    41: "cuarta persona, liberación y proclamación",
    42: "poder civil, sábado y fidelidad final",
    43: "prosperidad, Babilonia y segundo sueño",
    44: "árbol, vigilante, cepa y siete tiempos",
    45: "interpretación, arrepentimiento y demora del juicio",
    46: "humillación, restauración y grandeza",
    47: "Belsasar, Babilonia sitiada y banquete",
    48: "Vigía invisible, escritura y reina madre",
    49: "Daniel, reprensión y sentencia",
    50: "caída de Babilonia, Ciro y Eufrates",
    51: "destrucción y profecías sobre Babilonia",
    52: "imperios y visión de Ezequiel",
    53: "tiempo final y señales de los tiempos",
    54: "promesa de liberación para la iglesia",
    55: "reorganización, celos y decreto",
    56: "oración, acusación, foso, piedra y sellos",
    57: "liberación, acusadores y proclamación de Darío",
    58: "Daniel como estadista, profeta y embajador",
    59: "Daniel 7–12, Apocalipsis y verdadero objeto de la vida",
}


@dataclass(frozen=True)
class SourceUnit:
    bank: str
    chapter: str
    page: int
    locator: str
    source_ref: str
    topic: str
    sequence: int
    text: str


def normalize_space(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\s*\n\s*(?=\w)", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def split_segments(text: str) -> list[str]:
    text = normalize_space(text)
    raw = re.split(r"(?<=[.!?])(?:[”’\"»])?\s+|\s*;\s+", text)
    segments: list[str] = []
    for item in raw:
        item = item.strip()
        if len(item.split()) < 5:
            continue
        if len(item.split()) <= 72:
            segments.append(item)
            continue
        chunks = re.split(r"\s*,\s+(?=(?:y |pero |porque |para |cuando |mientras |que ))", item)
        segments.extend(chunk.strip() for chunk in chunks if len(chunk.split()) >= 7)
    return segments


def _clean_page_lines(text: str) -> list[str]:
    return [
        line.rstrip()
        for line in text.splitlines()
        if not re.fullmatch(r"\s*\d{2,3}\s*", line)
    ]


def extract_all_daniel_verses(
    document: fitz.Document,
) -> dict[int, dict[int, tuple[int, str]]]:
    result: dict[int, dict[int, tuple[int, str]]] = {}
    for chapter, pages in DANIEL_PAGE_MAP.items():
        chunks: list[tuple[int, str]] = []
        for page_index, page in enumerate(pages):
            lines = _clean_page_lines(document[page - 1].get_text())
            if page_index == 0:
                lines = [
                    line
                    for line in lines
                    if not re.fullmatch(
                        rf"Daniel\s+capítulo\s+{chapter}",
                        normalize_space(line),
                        re.IGNORECASE,
                    )
                ]
                if chapter == 11:
                    lines = [
                        line
                        for line in lines
                        if normalize_space(line) != "Los reyes del norte y del sur"
                    ]
                while lines and not re.match(
                    rf"^\s*{chapter}\s+", lines[0]
                ) and not (chapter in (1, 2, 11) and page_index == 0):
                    lines.pop(0)
                if chapter in (1, 2):
                    while lines and len(normalize_space(lines[0]).split()) < 7:
                        lines.pop(0)
            text = normalize_space("\n".join(lines))
            # La página PDF 13 muestra "8" entre 5:17 y 5:19. La continuidad
            # visible de la numeración confirma que se perdió el dígito 1.
            if chapter == 5 and page == 13:
                text = re.sub(r"(?<=\.)\s+8\s+(?=[«»]El Altísimo)", " 18 ", text, count=1)
            if page_index == 0:
                if re.match(rf"^{chapter}\s+", text):
                    text = re.sub(rf"^{chapter}\s+", "1 ", text, count=1)
                elif not re.match(r"^1\s+", text):
                    text = f"1 {text}"
            if chapter == 7 and page == 17 and not re.match(r"^13\s", text):
                text = f"13 {text}"
            chunks.append((page, text))

        combined = " ".join(text for _, text in chunks)
        positions: list[tuple[int, int]] = []
        cursor = 0
        for verse in range(1, DANIEL_LAST_VERSE[chapter] + 1):
            match = re.search(rf"(?<!\d){verse}\s+", combined[cursor:])
            if not match:
                raise ValueError(f"No se localizó Daniel {chapter}:{verse}")
            absolute = cursor + match.start()
            positions.append((verse, absolute))
            cursor += match.end()

        boundaries: list[tuple[int, int]] = []
        running = 0
        for page, text in chunks:
            boundaries.append((running, page))
            running += len(text) + 1
        chapter_verses: dict[int, tuple[int, str]] = {}
        for index, (verse, start) in enumerate(positions):
            content_start = start + len(str(verse)) + 1
            end = positions[index + 1][1] if index + 1 < len(positions) else len(combined)
            value = normalize_space(combined[content_start:end]).strip(" »")
            page = max(
                (page for boundary, page in boundaries if boundary <= start),
                default=pages[0],
            )
            if not value:
                raise ValueError(f"Daniel {chapter}:{verse} quedó vacío")
            chapter_verses[verse] = (page, value)
        result[chapter] = chapter_verses
    return result


def _pr_chapter_for_page(page: int) -> int:
    if page <= 32:
        return 39
    if page <= 37:
        return 40
    if page <= 42:
        return 41
    if page <= 46:
        return 42
    if page <= 54:
        return 43
    return 44


def extract_pr_units(document: fitz.Document) -> list[SourceUnit]:
    units: list[SourceUnit] = []
    sequence = 0
    for page in range(27, 60):
        chapter = _pr_chapter_for_page(page)
        paragraphs: list[str] = []
        for block in document[page - 1].get_text("blocks"):
            text = block[4]
            if block[1] < 85 or re.fullmatch(r"\s*\d{2,3}\s*", text):
                continue
            text = re.sub(r"\n\s*\d{2,3}\s*$", "", text)
            for part in re.split(r"\n\s*\n", text):
                clean = normalize_space(part)
                if len(clean.split()) >= 7:
                    paragraphs.append(clean)
        for paragraph_index, paragraph in enumerate(paragraphs, 1):
            for segment_index, segment in enumerate(split_segments(paragraph) or [paragraph], 1):
                sequence += 1
                units.append(
                    SourceUnit(
                        bank="PR39-44",
                        chapter=f"PR{chapter}",
                        page=page,
                        locator=f"P{page:03d}-S{paragraph_index:02d}-{segment_index:02d}",
                        source_ref=f"PDF p.{page}, PR{chapter}, párrafo {paragraph_index}",
                        topic=PR_PAGE_TOPICS[page],
                        sequence=sequence,
                        text=segment,
                    )
                )
    return units


TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:-[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)?")

STOPWORDS = {
    "a", "al", "algo", "ante", "así", "aun", "aunque", "bajo", "cada", "como",
    "con", "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante",
    "e", "el", "ella", "ellos", "en", "entre", "era", "eran", "es", "esa", "ese",
    "esto", "fue", "ha", "había", "hasta", "la", "las", "le", "les", "lo", "los",
    "más", "mas", "mi", "mientras", "muy", "ni", "no", "o", "para", "pero", "por",
    "porque", "que", "se", "ser", "si", "sin", "sobre", "su", "sus", "también",
    "tan", "todo", "todos", "tras", "un", "una", "uno", "y", "ya",
}

NUMBER_WORDS = {
    "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
    "diez", "once", "doce", "trece", "catorce", "quince", "veinte", "treinta",
    "dieciseis", "diecisiete", "dieciocho", "diecinueve",
    "veintiuno", "veintiun", "veintidos", "veintitres", "veinticuatro",
    "veinticinco", "veintiseis", "veintisiete", "veintiocho", "veintinueve",
    "cuarenta", "cincuenta", "sesenta", "setenta", "ciento", "mil", "millones",
}

VERB_WORDS = {
    "dijo", "respondió", "habló", "vino", "fue", "hizo", "vio", "miraba", "tuvo",
    "pidió", "dio", "puso", "salió", "volvió", "mandó", "ordenó", "declaró", "oyó",
    "recibió", "levantó", "entró", "llevó", "trajo", "reveló", "bendijo", "oró",
}


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def daniel_topic(chapter: int, verse: int) -> str:
    emphasis = {
        1: "cautiverio, formación, fidelidad y sabiduría",
        2: "sueño, oración, imagen e interpretación",
        3: "estatua, decreto, horno y liberación",
        4: "árbol, advertencia, humillación y restauración",
        5: "banquete, escritura, reprensión y caída",
        6: "administración, decreto, oración y foso",
        7: "bestias, juicio, Hijo del Hombre y santos",
        8: "carnero, macho cabrío, santuario e interpretación",
        9: "confesión, misericordia, Gabriel y setenta semanas",
        10: "visión, conflicto, fortalecimiento y libro de la verdad",
        11: "reyes del norte y sur, pacto, sabios y tiempo del fin",
        12: "Miguel, resurrección, sellamiento, tiempos y heredad",
    }
    return f"{emphasis[chapter]} (Daniel {chapter}:{verse})"


def extract_daniel_units(document: fitz.Document) -> list[SourceUnit]:
    verses = extract_all_daniel_verses(document)
    units: list[SourceUnit] = []
    sequence = 0
    for chapter, chapter_verses in verses.items():
        for verse, (page, text) in chapter_verses.items():
            for segment_index, segment in enumerate(split_segments(text) or [text], 1):
                sequence += 1
                units.append(
                    SourceUnit(
                        bank="DANIEL1-12",
                        chapter=f"DAN{chapter}",
                        page=page,
                        locator=f"V{verse:02d}-S{segment_index:02d}",
                        source_ref=f"PDF p.{page}, Daniel {chapter}:{verse}",
                        topic=daniel_topic(chapter, verse),
                        sequence=sequence,
                        text=segment,
                    )
                )
    return units


def _category(value: str, token_index: int) -> str:
    normalized = normalized_text(value)
    if value.isdigit() or normalized in NUMBER_WORDS:
        return "number"
    if value[:1].isupper() and token_index > 0:
        return "proper"
    if normalized in {normalized_text(word) for word in VERB_WORDS}:
        return "verb"
    if normalized.endswith(("ó", "aron", "ieron", "aba", "ían", "ará", "erá", "irá")):
        return "verb"
    if value.lower().endswith("s"):
        return "word_plural"
    return "word_singular"


def _candidate_spans(text: str) -> list[tuple[int, int, str, str, float]]:
    tokens = list(TOKEN_RE.finditer(text))
    candidates: list[tuple[int, int, str, str, float]] = []

    def inside_parenthetical(position: int) -> bool:
        return text.rfind("(", 0, position) > text.rfind(")", 0, position)

    for index, token in enumerate(tokens):
        value = token.group()
        normalized = normalized_text(value)
        if (
            inside_parenthetical(token.start())
            or normalized in STOPWORDS
            or (len(normalized) < 5 and not value.isdigit())
        ):
            continue
        category = _category(value, index)
        score = len(normalized) / 10
        if category in {"proper", "number"}:
            score += 4
        if category == "verb":
            score += 2
        candidates.append((token.start(), token.end(), value, category, score))

    # Las frases breves conservan listas, periodos y expresiones de alto riesgo.
    for index in range(max(0, len(tokens) - 1)):
        for size in (2, 3):
            if index + size > len(tokens):
                continue
            group = tokens[index:index + size]
            words = [normalized_text(token.group()) for token in group]
            if words[0] in STOPWORDS or words[-1] in STOPWORDS:
                continue
            if not any(word not in STOPWORDS and len(word) >= 5 for word in words):
                continue
            value = text[group[0].start():group[-1].end()]
            if (
                inside_parenthetical(group[0].start())
                or not re.fullmatch(
                    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9-]+(?: [A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9-]+){1,2}",
                    value,
                )
            ):
                continue
            category = "phrase_plural" if value.lower().endswith("s") else "phrase_singular"
            score = 1.2 + size * 0.4
            if all(word in NUMBER_WORDS or word.isdigit() or word == "y" for word in words):
                category = "number"
                score += 3
            candidates.append((group[0].start(), group[-1].end(), value, category, score))

    candidates.sort(key=lambda item: (-item[4], item[0], item[1] - item[0]))
    selected: list[tuple[int, int, str, str, float]] = []
    seen: set[str] = set()
    for candidate in candidates:
        start, end, value = candidate[:3]
        key = normalized_text(value)
        if key in seen:
            continue
        if any(max(0, min(end, prior[1]) - max(start, prior[0])) > 0 for prior in selected):
            continue
        selected.append(candidate)
        seen.add(key)
        if len(selected) == 8:
            break
    return selected


def _sentence_roles(text: str, answer: str) -> tuple[str, str, str, str]:
    words = [match.group() for match in TOKEN_RE.finditer(text)]
    action_index = next(
        (index for index, word in enumerate(words) if normalized_text(word) in {normalized_text(v) for v in VERB_WORDS}),
        None,
    )
    action = words[action_index] if action_index is not None else "expresa"
    subject_words = words[:action_index] if action_index is not None else words[:4]
    subject = " ".join(subject_words[-4:]) or words[0]
    context = " ".join(words[:14])
    return subject, action, answer, context


def build_atomic_facts(units: list[SourceUnit]) -> tuple[list[AtomicFact], int]:
    facts: list[AtomicFact] = []
    rejected = 0
    for unit in units:
        candidates = _candidate_spans(unit.text)
        rejected += max(0, len(TOKEN_RE.findall(unit.text)) - len(candidates))
        for fact_index, (_, _, answer, category, score) in enumerate(candidates, 1):
            subject, action, object_value, context = _sentence_roles(unit.text, answer)
            facts.append(
                AtomicFact(
                    fact_id=f"{unit.chapter}-{unit.locator}-F{fact_index:02d}",
                    bank=unit.bank,
                    chapter=unit.chapter,
                    verse_or_page=unit.source_ref.removeprefix("PDF p."),
                    source_span=unit.text,
                    subject=subject,
                    action=action,
                    object=object_value,
                    context=context,
                    relation_type=("number" if category == "number" else "action" if category == "verb" else "detail"),
                    importance="high" if score >= 4 else "medium",
                    topic=unit.topic,
                    sequence=unit.sequence,
                    answer=answer,
                    category=category,
                )
            )
    ordered = sorted(facts, key=lambda fact: (fact.chapter, fact.sequence, fact.fact_id))
    updated: list[AtomicFact] = []
    for index, fact in enumerate(ordered):
        neighbors = tuple(
            neighbor.fact_id
            for neighbor in ordered[max(0, index - 2):index + 3]
            if neighbor.fact_id != fact.fact_id and neighbor.chapter == fact.chapter
        )
        updated.append(replace(fact, nearby_fact_ids=neighbors))
    return updated, rejected


def _quota_totals(total: int, ratios: dict[str, float]) -> dict[str, int]:
    raw = {label: total * ratio for label, ratio in ratios.items()}
    result = {label: math.floor(value) for label, value in raw.items()}
    remaining = total - sum(result.values())
    for label in sorted(ratios, key=lambda item: (-(raw[item] - result[item]), item))[:remaining]:
        result[label] += 1
    return result


def _quota_matrix(chapter_targets: dict[str, int], totals: dict[str, int]) -> dict[str, dict[str, int]]:
    full_total = sum(chapter_targets.values())
    raw = {
        chapter: {
            label: chapter_total * label_total / full_total
            for label, label_total in totals.items()
        }
        for chapter, chapter_total in chapter_targets.items()
    }
    result = {
        chapter: {label: math.floor(value) for label, value in values.items()}
        for chapter, values in raw.items()
    }
    rows = {
        chapter: chapter_targets[chapter] - sum(result[chapter].values())
        for chapter in chapter_targets
    }
    columns = {
        label: totals[label] - sum(result[chapter][label] for chapter in chapter_targets)
        for label in totals
    }
    while any(value for value in rows.values()):
        choices = [
            (-(raw[chapter][label] - result[chapter][label]), chapter, label)
            for chapter in chapter_targets
            for label in totals
            if rows[chapter] > 0 and columns[label] > 0
        ]
        if not choices:
            raise ValueError("No se pudo cerrar la matriz de cuotas")
        _, chapter, label = min(choices)
        result[chapter][label] += 1
        rows[chapter] -= 1
        columns[label] -= 1
    return result


def _select_facts_for_chapter(facts: list[AtomicFact], target: int) -> list[AtomicFact]:
    required = math.ceil(target / 6)

    def spread(pool: list[AtomicFact], count: int) -> list[AtomicFact]:
        if count <= 0:
            return []
        by_locator: dict[str, list[AtomicFact]] = defaultdict(list)
        for fact in pool:
            locator = fact.fact_id.rsplit("-F", 1)[0]
            by_locator[locator].append(fact)
        locators = sorted(
            by_locator,
            key=lambda locator: min(f.sequence for f in by_locator[locator]),
        )
        if count <= len(locators):
            if count == 1:
                chosen_locators = [locators[len(locators) // 2]]
            else:
                chosen_indexes = [
                    round(index * (len(locators) - 1) / (count - 1))
                    for index in range(count)
                ]
                chosen_locators = [locators[index] for index in chosen_indexes]
            return [by_locator[locator][0] for locator in chosen_locators]

        chosen: list[AtomicFact] = []
        depth = 0
        while len(chosen) < count:
            progressed = False
            for locator in locators:
                values = by_locator[locator]
                if depth < len(values):
                    chosen.append(values[depth])
                    progressed = True
                    if len(chosen) == count:
                        break
            if not progressed:
                break
            depth += 1
        return chosen

    def pdf_page(fact: AtomicFact) -> int:
        return int(fact.verse_or_page.split(",", 1)[0])

    # Las dos secciones con límites editoriales reciben cuotas explícitas.
    # Los márgenes se calculan sobre hechos (no frases) y dejan espacio para
    # que cada hecho produzca hasta seis variantes sin rebasar el porcentaje.
    if facts and facts[0].chapter == "PR43":
        groups = (
            ([fact for fact in facts if 47 <= pdf_page(fact) <= 49], min(83, required)),
            ([fact for fact in facts if 50 <= pdf_page(fact) <= 51], round(required * 0.33)),
        )
        selected = [fact for pool, count in groups for fact in spread(pool, count)]
        remaining = required - len(selected)
        selected.extend(spread([fact for fact in facts if pdf_page(fact) >= 52], remaining))
        if len(selected) == required:
            return sorted(selected, key=lambda fact: (fact.sequence, fact.fact_id))

    if facts and facts[0].chapter == "PR44":
        early_count = min(101, required)
        selected = spread([fact for fact in facts if 55 <= pdf_page(fact) <= 57], early_count)
        selected.extend(spread([fact for fact in facts if pdf_page(fact) >= 58], required - len(selected)))
        if len(selected) == required:
            return sorted(selected, key=lambda fact: (fact.sequence, fact.fact_id))

    selected = spread(facts, required)
    if len(selected) != required:
        raise ValueError(f"Hechos insuficientes: {len(selected)}/{required}")
    return selected


def _interleaved_labels(quotas: dict[str, int]) -> list[str]:
    remaining = dict(quotas)
    result: list[str] = []
    previous = None
    while sum(remaining.values()):
        choices = [label for label, count in remaining.items() if count > 0]
        alternatives = [label for label in choices if label != previous]
        if alternatives:
            choices = alternatives
        label = max(choices, key=lambda item: (remaining[item], item))
        result.append(label)
        remaining[label] -= 1
        previous = label
    return result


def _short_quote(fact: AtomicFact) -> str:
    tokens = list(TOKEN_RE.finditer(fact.source_span))
    answer_start = fact.source_span.find(fact.answer)
    index = next((i for i, token in enumerate(tokens) if token.start() <= answer_start < token.end()), 0)
    start = max(0, index - 5)
    end = min(len(tokens), index + len(fact.answer.split()) + 7)
    return fact.source_span[tokens[start].start():tokens[end - 1].end()] if tokens else fact.answer


def _masked_source(fact: AtomicFact, replacement: str) -> str:
    start = fact.source_span.find(fact.answer)
    if start < 0:
        raise ValueError(f"La fuente no contiene la respuesta: {fact.fact_id}")
    return f"{fact.source_span[:start]}{replacement}{fact.source_span[start + len(fact.answer):]}"


def _distractors(
    fact: AtomicFact,
    pools: dict[str, list[AtomicFact]],
    chapter_pools: dict[tuple[str, str], list[AtomicFact]],
    offset: int,
) -> list[AtomicFact]:
    candidates = chapter_pools.get((fact.chapter, fact.category), []) + pools.get(fact.category, [])
    unique: list[AtomicFact] = []
    seen = {normalized_text(fact.answer)}
    for candidate in candidates[offset:] + candidates[:offset]:
        key = normalized_text(candidate.answer)
        if candidate.fact_id == fact.fact_id or key in seen or not 1 <= len(candidate.answer.split()) <= 8:
            continue
        unique.append(candidate)
        seen.add(key)
        if len(unique) == 3:
            return unique
    # La reserva general solo se usa cuando una categoría estrecha tiene menos de tres vecinos.
    fallback = sorted(
        (candidate for values in pools.values() for candidate in values),
        key=lambda candidate: (abs(len(candidate.answer) - len(fact.answer)), candidate.fact_id),
    )
    for candidate in fallback:
        key = normalized_text(candidate.answer)
        if candidate.fact_id == fact.fact_id or key in seen or not 1 <= len(candidate.answer.split()) <= 8:
            continue
        unique.append(candidate)
        seen.add(key)
        if len(unique) == 3:
            return unique
    raise ValueError(f"Distractores insuficientes para {fact.fact_id}")


FILL_STEMS = (
    "complete con la expresión exacta del PDF",
    "seleccione las palabras que restituyen el detalle omitido",
    "identifique la formulación que completa fielmente el pasaje",
)
MC_STEMS = (
    "¿qué opción completa correctamente el detalle señalado?",
    "¿qué formulación corresponde específicamente a este contexto?",
    "¿qué dato conserva la relación exacta descrita en el versículo o párrafo?",
    "¿qué opción distingue correctamente esta escena de los pasajes cercanos?",
)
TF_STEMS = (
    "determine si el detalle marcado conserva el texto de la fuente",
    "juzgue la afirmación atendiendo únicamente al contexto citado",
    "indique si sujeto, acción y detalle coinciden con el pasaje",
    "evalúe si la formulación mantiene sin cambios el dato señalado",
)


def _make_question(
    fact: AtomicFact,
    *,
    question_id: str,
    kind: str,
    difficulty: str,
    variant_number: int,
    correct_option: int,
    truth_value: bool,
    distractor_facts: list[AtomicFact],
    blind: bool,
) -> MassiveQuestion:
    source_label = fact.verse_or_page
    context_anchor = fact.context
    source_quote = _short_quote(fact)
    distractor_answers = [candidate.answer for candidate in distractor_facts]
    template_index = variant_number
    incorrect_detail = None
    correction = None
    if kind == "fill_blank":
        template_id = f"fill-context-v{template_index % len(FILL_STEMS) + 1}"
        masked = _masked_source(fact, "_____")
        question = (
            f"Según {source_label}, en la escena sobre {fact.topic}, {FILL_STEMS[template_index % len(FILL_STEMS)]}: "
            f"«{masked}»"
        )
        options = distractor_answers[:]
        options.insert(correct_option, fact.answer)
        answer = fact.answer
        explanation = f"La expresión omitida es «{fact.answer}»; el respaldo breve dice: «{source_quote}»."
        failures = {
            candidate.answer: f"«{candidate.answer}» procede de {candidate.verse_or_page}, no del espacio exacto solicitado."
            for candidate in distractor_facts
        }
        accepted = [fact.answer]
        answer_mode = "exact_text"
    elif kind == "true_false":
        template_id = f"tf-single-detail-v{template_index % len(TF_STEMS) + 1}"
        if truth_value:
            statement = _masked_source(fact, f"⟦{fact.answer}⟧")
            answer = "Verdadero"
            explanation = f"El detalle marcado coincide con el PDF: «{source_quote}»."
            failures = {"Falso": "El detalle marcado reproduce la fuente sin alteración."}
        else:
            incorrect_detail = distractor_facts[0].answer
            statement = _masked_source(fact, f"⟦{incorrect_detail}⟧")
            answer = "Falso"
            correction = fact.source_span
            explanation = (
                f"Solo se alteró «{fact.answer}» por «{incorrect_detail}». "
                f"La corrección exacta es: «{fact.source_span}»"
            )
            failures = {"Verdadero": f"El pasaje dice «{fact.answer}», no «{incorrect_detail}»."}
        question = (
            f"Según {source_label}, en la escena sobre {fact.topic}, {TF_STEMS[template_index % len(TF_STEMS)]}: "
            f"Elemento bajo prueba: «{fact.answer if truth_value else incorrect_detail}». Afirmación: «{statement}»"
        )
        options = ["Verdadero", "Falso"]
        correct_option = 0 if answer == "Verdadero" else 1
        accepted = [answer]
        answer_mode = "exact_text"
    else:
        template_id = f"mc-contextual-v{template_index % len(MC_STEMS) + 1}"
        masked = _masked_source(fact, "[DETALLE]")
        question = (
            f"Según {source_label}, en la escena sobre {fact.topic}, {MC_STEMS[template_index % len(MC_STEMS)]} "
            f"Marco: «{masked}»"
        )
        options = distractor_answers[:]
        options.insert(correct_option, fact.answer)
        answer = fact.answer
        explanation = (
            f"«{fact.answer}» completa el dato de {source_label}. Los demás elementos aparecen en otras "
            "unidades de la fuente, pero no responden a este anclaje exacto."
        )
        failures = {
            candidate.answer: f"Es un dato de {candidate.verse_or_page}; no completa el marco de {source_label}."
            for candidate in distractor_facts
        }
        accepted = [fact.answer]
        answer_mode = "exact_text"

    variant_id = f"{fact.fact_id}-{template_id.upper()}-{variant_number + 1:02d}"
    return MassiveQuestion(
        id=question_id,
        fact_id=fact.fact_id,
        variant_id=variant_id,
        template_id=template_id,
        bank=fact.bank,
        chapter=fact.chapter,
        verse_or_page=source_label,
        source_span=fact.source_span,
        type=kind,
        difficulty=difficulty,
        topic=fact.topic,
        context_anchor=context_anchor,
        question=question,
        options=options,
        correct_answer=answer,
        accepted_answers=accepted,
        answer_mode=answer_mode,
        explanation=explanation,
        why_distractors_fail=failures,
        source_quote=source_quote,
        trap_type=None,
        blind_final_pool=blind,
        validation_status="verified",
        correct_option=correct_option,
        incorrect_detail=incorrect_detail,
        correction=correction,
    )


def generate_questions_for_specs(
    units: list[SourceUnit],
    *,
    bank: str,
    chapter_targets: dict[str, int],
) -> tuple[list[MassiveQuestion], list[AtomicFact], dict[str, Any]]:
    all_facts, raw_rejected = build_atomic_facts(units)
    facts_by_chapter: dict[str, list[AtomicFact]] = defaultdict(list)
    for fact in all_facts:
        facts_by_chapter[fact.chapter].append(fact)

    selected_by_chapter = {
        chapter: _select_facts_for_chapter(facts_by_chapter[chapter], target)
        for chapter, target in chapter_targets.items()
    }
    selected_facts = [fact for chapter in chapter_targets for fact in selected_by_chapter[chapter]]
    pools: dict[str, list[AtomicFact]] = defaultdict(list)
    chapter_pools: dict[tuple[str, str], list[AtomicFact]] = defaultdict(list)
    for fact in all_facts:
        pools[fact.category].append(fact)
        chapter_pools[(fact.chapter, fact.category)].append(fact)

    total = sum(chapter_targets.values())
    type_totals = _quota_totals(total, TYPE_RATIOS)
    difficulty_totals = _quota_totals(total, DIFFICULTY_RATIOS)
    type_matrix = _quota_matrix(chapter_targets, type_totals)
    difficulty_matrix = _quota_matrix(chapter_targets, difficulty_totals)

    questions: list[MassiveQuestion] = []
    option_cursor = 0
    tf_cursor = 0
    question_counters: Counter[str] = Counter()
    fact_occurrences: Counter[str] = Counter()
    generation_rows: list[tuple[AtomicFact, str, str, int]] = []
    assigned_fact_type: Counter[tuple[str, str]] = Counter()

    for chapter, target in chapter_targets.items():
        selected = selected_by_chapter[chapter]
        difficulty_labels = _interleaved_labels(difficulty_matrix[chapter])
        remaining_types = dict(type_matrix[chapter])
        for index in range(target):
            fact = selected[index % len(selected)]
            choices = [
                label
                for label, remaining in remaining_types.items()
                if remaining > 0
                and assigned_fact_type[(fact.fact_id, label)]
                < {"true_false": 2, "fill_blank": 3, "multiple_choice": 4}[label]
            ]
            if not choices:
                raise ValueError(f"No se pudo diferenciar tipos para {fact.fact_id}")
            kind = min(
                choices,
                key=lambda label: (
                    assigned_fact_type[(fact.fact_id, label)] / TYPE_RATIOS[label],
                    -remaining_types[label],
                    label,
                ),
            )
            assigned_fact_type[(fact.fact_id, kind)] += 1
            remaining_types[kind] -= 1
            generation_rows.append((fact, kind, difficulty_labels[index], index))
            fact_occurrences[fact.fact_id] += 1

    blind_minimum = math.ceil(total * 0.15)
    blind_facts: set[str] = set()
    blind_questions = 0
    for fact in sorted(selected_facts, key=lambda value: hashlib.sha256(value.fact_id.encode()).hexdigest()):
        if blind_questions >= blind_minimum:
            break
        blind_facts.add(fact.fact_id)
        blind_questions += fact_occurrences[fact.fact_id]

    per_fact_type: Counter[tuple[str, str]] = Counter()
    per_fact_variant: Counter[str] = Counter()
    for fact, kind, difficulty, row_index in generation_rows:
        question_counters[fact.chapter] += 1
        variant_number = per_fact_variant[fact.fact_id]
        per_fact_variant[fact.fact_id] += 1
        type_variant = per_fact_type[(fact.fact_id, kind)]
        per_fact_type[(fact.fact_id, kind)] += 1
        distractor_facts = _distractors(
            fact,
            pools,
            chapter_pools,
            offset=(variant_number * 3 + row_index) % max(1, len(pools[fact.category])),
        )
        correct_option = option_cursor % 4
        if kind != "true_false":
            option_cursor += 1
        truth_value = tf_cursor % 2 == 0
        if kind == "true_false":
            tf_cursor += 1
        question_id = f"{fact.chapter}-{question_counters[fact.chapter]:04d}"
        questions.append(
            _make_question(
                fact,
                question_id=question_id,
                kind=kind,
                difficulty=difficulty,
                variant_number=type_variant,
                correct_option=correct_option,
                truth_value=truth_value,
                distractor_facts=distractor_facts,
                blind=fact.fact_id in blind_facts,
            )
        )

    mc_indexes = [index for index, question in enumerate(questions) if question.type == "multiple_choice"]
    trap_count = round(len(mc_indexes) * 0.40)
    trap_positions = {
        mc_indexes[index]
        for index in range(len(mc_indexes))
        if math.floor((index + 1) * trap_count / len(mc_indexes)) > math.floor(index * trap_count / len(mc_indexes))
    }
    questions = [
        replace(question, trap_type="true_elsewhere" if index in trap_positions else "close_detail")
        for index, question in enumerate(questions)
    ]

    # Una fracción de las selecciones múltiples prueba orden real de unidades
    # consecutivas, no una paráfrasis adicional del mismo espacio.
    fact_by_id = {fact.fact_id: fact for fact in selected_facts}
    ordered_by_chapter: dict[str, list[AtomicFact]] = defaultdict(list)
    for fact in selected_facts:
        ordered_by_chapter[fact.chapter].append(fact)
    for values in ordered_by_chapter.values():
        values.sort(key=lambda fact: (fact.sequence, fact.fact_id))
    sequence_target = max(1, round(len(mc_indexes) * 0.10))
    sequence_done = 0
    sequence_facts: set[str] = set()
    sequence_prompts: set[str] = set()
    transformed: list[MassiveQuestion] = []
    for question in questions:
        if (
            sequence_done >= sequence_target
            or question.type != "multiple_choice"
            or question.trap_type != "close_detail"
            or question.fact_id in sequence_facts
        ):
            transformed.append(question)
            continue
        fact = fact_by_id[question.fact_id]
        later: list[AtomicFact] = []
        seen_answers = {normalized_text(fact.answer)}
        for candidate in ordered_by_chapter[fact.chapter]:
            if candidate.sequence <= fact.sequence:
                continue
            key = normalized_text(candidate.answer)
            if key in seen_answers or len(candidate.answer.split()) > 4:
                continue
            later.append(candidate)
            seen_answers.add(key)
            if len(later) == 2:
                break
        if len(later) != 2:
            transformed.append(question)
            continue
        first, second, third = fact.answer, later[0].answer, later[1].answer
        correct = f"{first} → {second} → {third}"
        alternatives = [
            f"{first} → {third} → {second}",
            f"{second} → {first} → {third}",
            f"{third} → {second} → {first}",
        ]
        options = alternatives[:]
        options.insert(question.correct_option or 0, correct)
        failures = {
            option: "Altera el orden de aparición de las tres unidades citadas."
            for option in alternatives
        }
        sequence_prompt = (
            f"Entre {fact.verse_or_page} y {later[1].verse_or_page}, ¿qué secuencia respeta el orden "
            f"en que aparecen estos tres detalles en el PDF? Conjunto a ordenar: "
            f"{', '.join(sorted((first, second, third), key=normalized_text))}."
        )
        prompt_key = normalized_text(sequence_prompt)
        if prompt_key in sequence_prompts:
            transformed.append(question)
            continue
        transformed.append(
            replace(
                question,
                variant_id=f"{question.fact_id}-MC-SEQUENCE-{sequence_done + 1:02d}",
                template_id="mc-sequence-v1",
                question=sequence_prompt,
                options=options,
                correct_answer=correct,
                accepted_answers=[correct],
                explanation=(
                    f"La fuente presenta primero «{first}», después «{second}» y finalmente «{third}»."
                ),
                why_distractors_fail=failures,
                source_quote=f"{_short_quote(fact)} | {_short_quote(later[0])} | {_short_quote(later[1])}",
                source_span=f"{fact.source_span} | {later[0].source_span} | {later[1].source_span}",
                context_anchor=f"{fact.verse_or_page} → {later[0].verse_or_page} → {later[1].verse_or_page}",
                trap_type="order_sequence",
            )
        )
        sequence_done += 1
        sequence_facts.add(question.fact_id)
        sequence_prompts.add(prompt_key)
    questions = transformed

    meta = {
        "source_facts": len(all_facts),
        "selected_facts": len(selected_facts),
        "candidates": len(selected_facts) * 8,
        "selected": len(questions),
        "rejected": raw_rejected + max(0, len(selected_facts) * 8 - len(questions)),
        "blind_questions": sum(question.blind_final_pool for question in questions),
        "blind_facts": len(blind_facts),
        "templates": len({question.template_id for question in questions}),
        "dynamic_distractors": len({normalized_text(fact.answer) for fact in selected_facts}),
    }
    return questions, selected_facts, meta
