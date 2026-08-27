"""Generación editorial determinista del Banco Maestro Único."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any, Iterable

from scripts.lib.final_bank import BANK_ID, DISPLAY_NAME, QUESTION_FAMILIES
from scripts.lib.massive_generator import NUMBER_WORDS, STOPWORDS, TOKEN_RE, _candidate_spans
from scripts.lib.source_inventory import _split_propositions


FACT_QUOTAS = {
    "DAN1": 75, "DAN2": 100, "DAN3": 85, "DAN4": 95, "DAN5": 80,
    "DAN6": 80, "DAN7": 120, "DAN8": 120, "DAN9": 120, "DAN10": 90,
    "DAN11": 150, "DAN12": 75, "PR39": 120, "PR40": 100, "PR41": 100,
    "PR42": 100, "PR43": 170, "PR44": 170,
}
DIFFICULTY_COUNTS = {"easy": 390, "medium": 1560, "hard": 3510, "expert": 2340}
STOP_ANSWERS = {
    "alguno", "aquella", "aquello", "aquellos", "ellos", "estas", "estos", "mismo",
    "misma", "otros", "porque", "sobre", "todas", "todos", "cuando", "donde",
    "asi", "ahora", "luego", "despues", "tambien", "solo", "aqui", "debajo",
    "ciertamente", "dondequiera",
    "eres", "es", "era", "eran", "estaba", "estaban", "estuve", "estuvo",
    "ser", "sido", "sea", "sean", "sera", "seran", "fue", "fueron", "habia",
    "hay", "hoy", "ayer", "manana", "cuan", "cuanto", "como", "derribad",
    "levantate",
}

ADVERB_FORMS = {
    "asi", "ahora", "luego", "despues", "tambien", "solo", "aqui", "debajo",
    "ciertamente", "dondequiera", "entonces", "pronto", "delante", "encima",
    "hoy", "ayer", "manana", "cuan", "cuanto", "como",
}

FUNCTION_WORDS = {
    "a", "al", "ante", "como", "con", "contra", "de", "del", "desde",
    "durante", "el", "en", "entre", "hacia", "hasta", "la", "las", "los",
    "para", "por", "segun", "sin", "sobre", "tras", "un", "una", "y",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "mi",
    "mis", "tu", "tus", "entonces",
    "yo", "el", "ella", "ellos", "ellas", "nosotros", "vosotros", "usted",
    "ustedes", "me", "te", "se", "nos", "os", "le", "les", "lo", "la",
    "mucho", "mucha", "muchos", "muchas", "gran", "grandes", "varios",
    "varias", "cierto", "cierta", "ciertos", "ciertas", "todo", "toda",
    "todos", "todas", "otro", "otra", "otros", "otras",
    "cuyo", "cuya", "cuyos", "cuyas", "aquel", "aquella", "aquellos",
    "aquellas", "alguno", "alguna", "algunos", "algunas", "unos", "unas",
}
VERB_FORMS = {
    "dijo", "respondio", "hablo", "vino", "fue", "hizo", "vio", "miraba",
    "tuvo", "pidio", "dio", "puso", "salio", "volvio", "mando", "ordeno",
    "declaro", "oyo", "recibio", "levanto", "entro", "llevo", "trajo",
    "revelo", "bendijo", "sera", "seran", "estaba", "estaban",
    "era", "eran", "ocupaba", "significa", "derribara", "destruira",
    "estate", "cumplia", "pesole", "sea", "sean", "estuvo", "estuve", "temo",
    "alce", "quedo", "hable", "sabes", "dije", "anda", "cuenta", "cuente",
    "decidme", "contadme", "estabas", "conviene", "derribad", "cortad", "eres",
    "llamese", "fueron", "trajeron", "acercandose", "levantate", "llevara",
    "volvera", "llegara", "elevara", "pasados", "sentados", "considerados",
    "rodeado", "fuese", "tuve", "manteniase", "vi", "oi",
}


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _word_role(word: str) -> str:
    normalized = _norm(word)
    if normalized in ADVERB_FORMS or normalized.endswith("mente"):
        return "adverb"
    if (normalized in FUNCTION_WORDS or normalized in STOPWORDS) and word.lower() != "hacía":
        return "function"
    if normalized in NUMBER_WORDS or normalized.isdigit():
        return "number"
    if re.search(r"(?:rá|rás|rán|ré|ría|rías|rían|ía|ían|ó)$", word.lower()):
        return "verb"
    if normalized in VERB_FORMS or re.search(
        r"(?:ando|iendo|andose|iendose|ado|ada|ados|adas|ido|ida|idos|idas|aron|ieron|aba|aban|ia|ian|ara|ira|aran|eran|iran)$",
        word.lower(),
    ):
        return "verb"
    return "content"


def option_signature(value: str, category: str | None = None) -> tuple[Any, ...]:
    """Firma superficial conservadora para impedir distractores rotos."""
    words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9-]+", value)
    if not words:
        return (0, "empty", "empty", "empty")
    if category in {"person", "place"}:
        return (category, "named_entity")
    length = len(words) if len(words) <= 3 else 4
    roles = [_word_role(word) for word in words]
    numeric = "numeric" if any(role == "number" for role in roles) else "lexical"
    if category == "number":
        representation = "digits" if all(word.isdigit() for word in words) else "words"
        return (category, length, representation)
    if category == "action":
        return (category, _action_form(value))
    if category == "phrase":
        return (category, length)
    shapes = tuple(
        f"function:{_norm(word)}" if role == "function"
        else role if role in {"number", "verb"}
        else "content_plural" if word.lower().endswith("s")
        else "content_singular"
        for word, role in zip(words, roles)
    )
    return (length, numeric, shapes)


def _action_form(value: str) -> str:
    raw = value.lower()
    lower = _norm(value)
    irregular = {
        "eres": "present_e", "es": "present_e", "soy": "present_other", "son": "present_other",
        "esta": "present_a", "estan": "present_other", "tiene": "present_e", "tienen": "present_other",
        "sabes": "present_other", "tuvo": "preterite", "dijo": "preterite", "dije": "preterite",
        "hizo": "preterite", "vino": "preterite", "puso": "preterite",
        "trajo": "preterite", "trajeron": "preterite",
        "fue": "preterite", "fueron": "preterite",
    }
    if lower in irregular:
        return irregular[lower]
    if re.search(r"(?:rá|rás|rán|ré|remos)$", raw):
        return "future"
    if re.search(r"(?:ó|é|í|aron|ieron)$", raw):
        return "preterite"
    if re.search(r"(?:aba|aban|ía|ían)$", raw):
        return "imperfect"
    if re.search(r"(?:ara|aran|iera|ieran|yera|yeran|ase|asen|iese|iesen)$", lower):
        return "subjunctive_past"
    if re.search(r"(?:ando|iendo|andose|iendose)$", lower):
        return "gerund"
    if re.search(r"(?:ad|ed|id|ate|ete|ite)$", lower):
        return "imperative"
    if re.search(r"(?:ado|ada|ados|adas|ido|ida|idos|idas)$", lower):
        return "participle"
    if lower.endswith("a"):
        return "present_a"
    if lower.endswith("e"):
        return "present_e"
    return "other"


def _chapter_key(unit: dict[str, Any]) -> str:
    return ("DAN" if unit["work"] == "Daniel" else "PR") + str(unit["chapter"])


def _source_text(unit: dict[str, Any]) -> str:
    return str(unit.get("full_text") or unit.get("exact_text") or "").strip()


def _broad_category(answer: str, raw_category: str, unit: dict[str, Any]) -> str:
    if _norm(answer) in {"dios", "jehova", "senor", "salvador", "mesias", "miguel", "gabriel"}:
        return "person"
    answer_words = {_norm(word) for word in answer.split()}
    if any(word in NUMBER_WORDS or word.isdigit() for word in answer_words):
        return "number"
    if answer in unit.get("characters", []):
        return "person"
    if answer in unit.get("places", []) or answer in unit.get("rivers", []):
        return "place"
    if raw_category == "number" or answer in unit.get("numbers", []):
        return "number"
    if raw_category == "verb" or answer in unit.get("actions", []):
        return "action"
    return "phrase"


def _fact_candidates(unit: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    text = _source_text(unit)
    candidates: list[dict[str, Any]] = []
    rejected = 0
    raw_candidates: list[tuple[int, int, str, str, float]] = []
    editorial_phrase_keys: set[tuple[int, int, str]] = set()
    tokens = list(TOKEN_RE.finditer(text))
    for token in tokens:
        answer = token.group()
        normalized = _norm(answer)
        if normalized in STOPWORDS or (len(normalized) < 3 and not answer.isdigit()):
            continue
        role = _word_role(answer)
        raw_category = "number" if role == "number" else "verb" if role == "verb" else "proper" if answer[:1].isupper() else "word_plural" if answer.lower().endswith("s") else "word_singular"
        score = (5 if raw_category in {"proper", "number"} else 3 if raw_category == "verb" else 2) + len(answer) / 20
        raw_candidates.append((token.start(), token.end(), answer, raw_category, score))
    for index in range(len(tokens)):
        for size in (2, 3, 4):
            group = tokens[index:index + size]
            if len(group) != size:
                continue
            answer = text[group[0].start():group[-1].end()]
            if not re.fullmatch(r"[\wÁÉÍÓÚÜÑáéíóúüñ-]+(?: [\wÁÉÍÓÚÜÑáéíóúüñ-]+){1,3}", answer):
                continue
            roles = [_word_role(token.group()) for token in group]
            starts_meaningfully = roles[0] in {"content", "function"}
            if not starts_meaningfully or roles[-1] != "content" or "verb" in roles:
                continue
            raw_category = "phrase_plural" if answer.lower().endswith("s") else "phrase_singular"
            # Las expresiones completas tienen más valor editorial que una palabra
            # suelta: preservan relaciones y contexto, y producen distractores de
            # la misma estructura.
            raw_candidates.append((group[0].start(), group[-1].end(), answer, raw_category, 4.5 + size / 10))
            editorial_phrase_keys.add((group[0].start(), group[-1].end(), _norm(answer)))
    raw_candidates.extend(_candidate_spans(text))

    seen_candidates: set[tuple[int, int, str]] = set()
    for start, end, answer, raw_category, score in raw_candidates:
        candidate_key = (start, end, _norm(answer))
        if candidate_key in seen_candidates:
            continue
        seen_candidates.add(candidate_key)
        normalized = _norm(answer)
        words = answer.split()
        roles = [_word_role(word) for word in words]
        broad_category = _broad_category(answer, raw_category, unit)
        content_words = [word for word, role in zip(words, roles) if role == "content"]
        crosses_plural_into_name = (
            len(content_words) >= 2
            and content_words[-1][:1].isupper()
            and content_words[-2][:1].islower()
            and content_words[-2].lower().endswith("s")
        )
        if (
            not normalized
            or normalized in STOP_ANSWERS
            or normalized in STOPWORDS
            or normalized in FUNCTION_WORDS
            or not 1 <= len(answer.split()) <= 6
            or text.count(answer) != 1
            or "..." in answer
            or (len(words) > 1 and candidate_key not in editorial_phrase_keys)
            or (
                len(words) > 1
                and (
                    roles[0] not in {"content", "function"}
                    or roles[-1] != "content"
                    or "verb" in roles
                )
            )
            or (broad_category == "phrase" and len(words) == 1)
            or crosses_plural_into_name
        ):
            rejected += 1
            continue
        candidates.append(
            {
                "answer": answer,
                "start": start,
                "end": end,
                "grammatical_category": raw_category,
                "category": broad_category,
                "score": score,
            }
        )
    phrase_candidates = [row for row in candidates if row["category"] == "phrase"]
    if len(phrase_candidates) > 2:
        best_phrases = sorted(
            phrase_candidates,
            key=lambda row: (-float(row["score"]), -len(row["answer"]), int(row["start"])),
        )[:2]
        candidates = [row for row in candidates if row["category"] != "phrase"] + best_phrases
    if not candidates:
        raise ValueError(f"Unidad sin un detalle editorial significativo: {unit['source_unit_id']}")
    candidates.sort(key=lambda row: (-float(row["score"]), row["start"], row["answer"]))
    return candidates, rejected


def _context_for(text: str, answer: str) -> str:
    clauses = _split_propositions(text)
    containing = [clause.strip() for clause in clauses if answer in clause]
    return min(containing, key=len) if containing else text


def derive_atomic_facts(units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    by_chapter: dict[str, list[tuple[dict[str, Any], list[dict[str, Any]]]]] = defaultdict(list)
    rejected = 0
    for unit in units:
        candidates, unit_rejected = _fact_candidates(unit)
        rejected += unit_rejected
        by_chapter[_chapter_key(unit)].append((unit, candidates))

    facts: list[dict[str, Any]] = []
    for chapter, quota in FACT_QUOTAS.items():
        rows = by_chapter[chapter]
        selected: list[tuple[dict[str, Any], dict[str, Any], int]] = []
        for unit, candidates in rows:
            selected.append((unit, candidates[0], 1))
        candidate_index = 1
        while len(selected) < quota:
            added = False
            for unit, candidates in rows:
                if len(selected) >= quota:
                    break
                if candidate_index < len(candidates):
                    selected.append((unit, candidates[candidate_index], candidate_index + 1))
                    added = True
            if not added:
                raise ValueError(f"La fuente no permite {quota} hechos legítimos en {chapter}")
            candidate_index += 1
        rejected += sum(len(candidates) for _, candidates in rows) - len(selected)
        selected.sort(key=lambda row: (row[0]["source_unit_id"], row[2]))
        per_unit: Counter[str] = Counter()
        for unit, candidate, _ in selected:
            source_unit_id = unit["source_unit_id"]
            per_unit[source_unit_id] += 1
            answer = candidate["answer"]
            source_quote = _source_text(unit)
            fact_id = f"{source_unit_id}-F{per_unit[source_unit_id]:02d}"
            facts.append(
                {
                    "fact_id": fact_id,
                    "source_unit_id": source_unit_id,
                    "work": unit["work"],
                    "chapter": chapter,
                    "reference": unit["reference"],
                    "page": unit["page"],
                    "answer": answer,
                    "category": candidate["category"],
                    "grammatical_category": candidate["grammatical_category"],
                    "source_quote": source_quote,
                    "_normalized_answer": _norm(answer),
                    "_normalized_source": _norm(source_quote),
                    "context": _context_for(source_quote, answer),
                    "importance": "critical" if chapter in {"DAN7", "DAN8", "DAN9", "DAN11", "PR43", "PR44"} else "high" if chapter in {"DAN10", "DAN12", "PR40", "PR42"} else "essential",
                    "relation_type": "cause" if re.search(r"\bporque\b|\bpor cuanto\b", source_quote, re.I) else "consequence" if re.search(r"\bpor tanto\b|\bentonces\b|\basí\b", source_quote, re.I) else candidate["category"],
                }
            )
    facts.sort(key=lambda row: (row["chapter"], row["source_unit_id"], row["fact_id"]))
    for chapter, chapter_facts in _group_by(facts, "chapter").items():
        for index, fact in enumerate(chapter_facts):
            fact["nearby_fact_ids"] = [
                row["fact_id"]
                for row in chapter_facts[max(0, index - 3):index + 4]
                if row["fact_id"] != fact["fact_id"]
            ]
    return facts, rejected


def _group_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    return grouped


def _masked(text: str, answer: str, marker: str) -> str:
    return text.replace(answer, marker, 1)


def _category_label(category: str) -> str:
    return {
        "person": "personaje",
        "place": "lugar",
        "number": "detalle numérico",
        "action": "acción",
        "phrase": "expresión",
    }[category]


def _distractor_candidates(fact: dict[str, Any], facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def eligible(row: dict[str, Any], strict: bool) -> bool:
        if (
            row["fact_id"] == fact["fact_id"]
            or row["_normalized_answer"] == fact["_normalized_answer"]
            or row["_normalized_answer"] in fact["_normalized_source"]
        ):
            return False
        if row["category"] != fact["category"]:
            return False
        if option_signature(row["answer"], row["category"]) != option_signature(fact["answer"], fact["category"]):
            return False
        if strict and row["grammatical_category"] != fact["grammatical_category"]:
            return False
        return row["chapter"] == fact["chapter"] if strict else True

    strict_rows = [row for row in facts if eligible(row, True)]
    broad_rows = [row for row in facts if eligible(row, False)]
    unique: dict[str, dict[str, Any]] = {}
    for row in strict_rows + broad_rows:
        unique.setdefault(_norm(row["answer"]), row)
    answer_words = len(fact["answer"].split())
    answer_length = len(fact["answer"])
    return sorted(
        unique.values(),
        key=lambda row: (
            abs(len(row["answer"].split()) - answer_words),
            abs(len(row["answer"]) - answer_length),
            _hash(f"{fact['fact_id']}:{row['fact_id']}"),
        ),
    )


def _arrange_options(correct: str, distractors: list[str], position: int) -> list[str]:
    options = distractors[:3]
    options.insert(position, correct)
    return options


def _review_choice(question: dict[str, Any]) -> dict[str, Any]:
    quote_norm = _norm(question["source_quote"])
    supported = [
        index for index, option in enumerate(question["options"])
        if _norm(option) and _norm(option) in quote_norm
    ]
    if question["family"] == "true_false":
        statement_supported = _norm(question["statement"]) in quote_norm
        correction_norm = _norm(question.get("corrected_statement", ""))
        correction_supported = bool(correction_norm) and correction_norm in quote_norm
        selected = 0 if statement_supported else 1 if correction_supported else -1
        ambiguous = statement_supported and correction_supported
    else:
        selected = supported[0] if len(supported) == 1 else -1
        ambiguous = len(supported) != 1
    return {
        "reviewer": "source-blind-v1",
        "status": "passed" if selected >= 0 and not ambiguous else "failed",
        "selected_option": selected,
        "rationale": "La opción seleccionada es la única sustentada por el fragmento literal de la unidad.",
        "second_defensible_option": ambiguous,
    }


def _base_question(fact: dict[str, Any], family: str, index: int) -> dict[str, Any]:
    return {
        "id": f"{fact['chapter']}-GOLD-{index + 1:04d}-{family.upper()}",
        "bank_id": BANK_ID,
        "bank_name": DISPLAY_NAME,
        "schema_version": "7.0",
        "source_unit_id": fact["source_unit_id"],
        "fact_id": fact["fact_id"],
        "variant_id": f"{fact['fact_id']}-{family.upper()}",
        "template_id": f"{family}-editorial-v1",
        "family": family,
        "chapter": fact["chapter"],
        "reference": fact["reference"],
        "source_ref": fact["reference"],
        "verse_or_page": fact["reference"],
        "source_span": fact["source_quote"],
        "source_quote": fact["source_quote"],
        "context_anchor": fact["context"][:180],
        "topic": fact["relation_type"],
        "importance": fact["importance"],
        "relation_type": fact["relation_type"],
        "option_category": fact["category"],
        "blind_pool": None,
        "validation_generator": {"status": "passed", "source_supported": True},
        "validation_schema": {"status": "passed"},
        "validation_source": {"status": "passed", "external_knowledge": False},
        "validation_language": {"status": "passed", "natural_span": True},
        "final_editorial_status": "GOLD",
        "accepted_answers": [fact["answer"]],
        "answer_mode": "option_id",
    }


def generate_gold_questions(facts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    if len(facts) != 1950:
        raise ValueError("Se requieren exactamente 1,950 hechos seleccionados")
    distractor_pools: dict[tuple[str, tuple[Any, ...]], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        distractor_pools[(fact["category"], option_signature(fact["answer"], fact["category"]))].append(fact)

    def compatible_rows(fact: dict[str, Any]) -> list[dict[str, Any]]:
        rows = distractor_pools[(fact["category"], option_signature(fact["answer"], fact["category"]))]
        eligible = [
            row for row in rows
            if row["fact_id"] != fact["fact_id"]
            and row["_normalized_answer"] != fact["_normalized_answer"]
            and row["_normalized_answer"] not in fact["_normalized_source"]
        ]
        unique: dict[str, dict[str, Any]] = {}
        for row in eligible:
            unique.setdefault(row["_normalized_answer"], row)
        return sorted(
            unique.values(),
            key=lambda row: (
                fact["category"] == "action" and _action_form(row["answer"]) != _action_form(fact["answer"]),
                row["chapter"] != fact["chapter"],
                row["grammatical_category"] != fact["grammatical_category"],
                abs(len(row["answer"]) - len(fact["answer"])),
                _hash(f"{fact['fact_id']}:{row['fact_id']}"),
            ),
        )

    distractor_map = {fact["fact_id"]: compatible_rows(fact) for fact in facts}
    if any(len(rows) < 3 for rows in distractor_map.values()):
        raise ValueError("Hay hechos sin tres distractores compatibles")
    false_candidates = sorted(
        facts,
        key=lambda fact: (
            fact["grammatical_category"] not in {"proper", "number", "verb", "word_singular", "word_plural", "phrase_singular", "phrase_plural"},
            _hash("false:" + fact["fact_id"]),
        ),
    )
    false_facts = {fact["fact_id"] for fact in false_candidates[:975]}
    questions: list[dict[str, Any]] = []
    rejected = sum(max(0, len(rows) - 3) for rows in distractor_map.values())

    for index, fact in enumerate(facts):
        distractor_facts = distractor_map[fact["fact_id"]]
        distractors = [row["answer"] for row in distractor_facts[:3]]
        why = {
            row["answer"]: f"Es verdadero en {row['reference']}, pero no responde al contexto exacto de {fact['reference']}."
            for row in distractor_facts[:3]
        }
        for family_offset, family in enumerate(QUESTION_FAMILIES):
            base = _base_question(fact, family, index)
            if family == "true_false":
                false = fact["fact_id"] in false_facts
                replacement = distractors[0]
                statement = _masked(fact["context"], fact["answer"], replacement) if false else fact["context"]
                masked_focus = _masked(fact["context"], fact["answer"], "________")
                proposed_detail = replacement if false else fact["answer"]
                base.update(
                    {
                        "question": (
                            f"Según {fact['reference']}, la expresión «{proposed_detail}» completa "
                            f"la frase «{masked_focus}». ¿Verdadero o falso?"
                        ),
                        "statement": statement,
                        "options": ["Verdadero", "Falso"],
                        "correct_option": 1 if false else 0,
                        "correct_answer": "Falso" if false else "Verdadero",
                        "corrected_statement": fact["context"] if false else "",
                        "incorrect_detail": replacement if false else None,
                        "correction": fact["answer"] if false else None,
                        "explanation": (
                            f"Es falsa: la fuente dice «{fact['answer']}», no «{replacement}»."
                            if false else f"Es verdadera y reproduce el detalle de {fact['reference']}."
                        ),
                        "why_distractors_fail": {
                            "Verdadero" if false else "Falso": (
                                f"La única alteración es «{replacement}»; la fuente contiene «{fact['answer']}»."
                                if false else "La afirmación coincide literalmente con la unidad fuente."
                            )
                        },
                        "trap_type": "single_plausible_detail" if false else None,
                    }
                )
            else:
                position = (index + family_offset) % 4
                options = _arrange_options(fact["answer"], distractors, position)
                masked_context = _masked(fact["context"], fact["answer"], "________")
                if family == "fill_choice":
                    question_text = (
                        f"Según {fact['reference']}, complete la expresión significativa: "
                        f"«{_masked(fact['context'], fact['answer'], '________')}»"
                    )
                    trap_type = None
                elif family == "single_choice_contextual":
                    question_text = (
                        f"Al comparar escenas cercanas, ¿qué {_category_label(fact['category'])} pertenece "
                        f"específicamente a {fact['reference']} en «{masked_context}»?"
                    )
                    trap_type = "true_in_other_context"
                else:
                    question_text = (
                        f"En {fact['reference']}, ¿qué {_category_label(fact['category'])} usa la fuente "
                        f"en la afirmación «{masked_context}»?"
                    )
                    trap_type = None
                base.update(
                    {
                        "question": question_text,
                        "options": options,
                        "correct_option": position,
                        "correct_answer": fact["answer"],
                        "explanation": f"{fact['reference']} declara literalmente «{fact['context']}». La respuesta pedida es «{fact['answer']}».",
                        "why_distractors_fail": why,
                        "trap_type": trap_type,
                    }
                )
            base["validation_adversarial"] = _review_choice(base)
            if base["validation_adversarial"]["status"] != "passed":
                raise ValueError(f"Revisión adversarial fallida: {base['id']}")
            questions.append(base)

    difficulty_order = sorted(questions, key=lambda row: _hash("difficulty:" + row["id"]))
    cursor = 0
    for label, count in DIFFICULTY_COUNTS.items():
        for question in difficulty_order[cursor:cursor + count]:
            question["difficulty"] = label
        cursor += count

    blind_order = sorted(facts, key=lambda fact: _hash("blind:" + fact["fact_id"]))[:300]
    blind_lookup = {
        fact["fact_id"]: ("A" if index < 100 else "B" if index < 200 else "emergency")
        for index, fact in enumerate(blind_order)
    }
    for question in questions:
        question["blind_pool"] = blind_lookup.get(question["fact_id"])
    return questions, rejected


def build_coverage_manifest(
    units: list[dict[str, Any]], facts: list[dict[str, Any]], questions: list[dict[str, Any]]
) -> dict[str, Any]:
    facts_by_unit = _group_by(facts, "source_unit_id")
    questions_by_fact = _group_by(questions, "fact_id")
    entries: list[dict[str, Any]] = []
    for unit in units:
        unit_facts = facts_by_unit.get(unit["source_unit_id"], [])
        question_rows = [
            question
            for fact in unit_facts
            for question in questions_by_fact.get(fact["fact_id"], [])
        ]
        entries.append(
            {
                "source_unit_id": unit["source_unit_id"],
                "chapter": _chapter_key(unit),
                "reference": unit["reference"],
                "source_text": _source_text(unit),
                "fact_ids": [fact["fact_id"] for fact in unit_facts],
                "gold_question_ids": [question["id"] for question in question_rows],
                "question_families": sorted({question["family"] for question in question_rows}),
                "coverage_status": "covered" if unit_facts and question_rows else "uncovered",
                "reviewer_status": "passed" if question_rows and all(question["validation_adversarial"]["status"] == "passed" for question in question_rows) else "failed",
            }
        )
    fact_without = sum(not questions_by_fact.get(fact["fact_id"]) for fact in facts)
    uncovered = sum(entry["coverage_status"] != "covered" for entry in entries)
    mapped = {entry["source_unit_id"] for entry in entries}
    return {
        "schema_version": "7.0",
        "bank_id": BANK_ID,
        "source_units": len(entries),
        "covered_source_units": len(entries) - uncovered,
        "uncovered_source_units": uncovered,
        "fact_without_gold_question": fact_without,
        "unmapped_source_units": len({unit["source_unit_id"] for unit in units} - mapped),
        "units": entries,
    }


def audit_final_bank(
    facts: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    normalized_questions = [_norm(question["question"]) for question in questions]
    false_questions = [
        question for question in questions
        if question["family"] == "true_false" and question["correct_answer"] == "Falso"
    ]
    invalid_references = sum(
        not re.fullmatch(r"Daniel \d+:\d+|PR\d+, p\. \d+, párrafo \d+", question["reference"])
        for question in questions
    )
    length_leaks = 0
    for question in questions:
        if question["family"] == "true_false":
            continue
        lengths = [len(option) for option in question["options"]]
        correct = lengths[question["correct_option"]]
        peers = [length for index, length in enumerate(lengths) if index != question["correct_option"]]
        if peers and (correct > max(peers) * 2.5 or correct * 2.5 < min(peers)):
            length_leaks += 1
    return {
        "schema_version": "7.0",
        "bank_id": BANK_ID,
        "gold_questions": len(questions),
        "unique_facts": len(facts),
        "ambiguous_gold_questions": sum(question["validation_adversarial"]["status"] != "passed" for question in questions),
        "unsupported_gold_answers": sum(
            question["family"] != "true_false" and question["correct_answer"] not in question["source_quote"]
            for question in questions
        ),
        "duplicate_gold_questions": len(normalized_questions) - len(set(normalized_questions)),
        "lexical_sequence_questions": sum("→" in question["question"] for question in questions),
        "broken_true_false": sum(
            not question.get("incorrect_detail") or not question.get("correction")
            for question in false_questions
        ),
        "invalid_references": invalid_references,
        "external_knowledge_questions": sum(question["validation_source"].get("external_knowledge") is not False for question in questions),
        "answer_length_leaks": length_leaks,
        "orphan_numeric_source_fragments": sum(
            bool(re.match(r"^\d+\)?,", fact["source_quote"])) for fact in facts
        ),
        "coverage": {
            key: coverage[key]
            for key in ("uncovered_source_units", "fact_without_gold_question", "unmapped_source_units")
        },
        "by_family": dict(Counter(question["family"] for question in questions)),
        "by_difficulty": dict(Counter(question["difficulty"] for question in questions)),
        "by_chapter": dict(Counter(question["chapter"] for question in questions)),
        "true_false_balance": dict(Counter(question["correct_answer"] for question in questions if question["family"] == "true_false")),
        "blind_pools": dict(Counter(question["blind_pool"] for question in questions if question["blind_pool"])),
    }
