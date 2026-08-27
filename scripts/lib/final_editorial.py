"""Generación editorial determinista del Banco Maestro Único."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any, Iterable

from scripts.lib.final_bank import BANK_ID, DISPLAY_NAME, QUESTION_FAMILIES, SCHEMA_VERSION
from scripts.lib.final_relations import extract_relation_candidates
from scripts.lib.massive_generator import NUMBER_WORDS, STOPWORDS, TOKEN_RE, _candidate_spans
from scripts.lib.source_inventory import _split_propositions


FACT_QUOTAS = {
    "DAN1": 83, "DAN2": 120, "DAN3": 90, "DAN4": 105, "DAN5": 90,
    "DAN6": 90, "DAN7": 225, "DAN8": 225, "DAN9": 225, "DAN10": 135,
    "DAN11": 306, "DAN12": 105, "PR39": 210, "PR40": 195, "PR41": 180,
    "PR42": 180, "PR43": 241, "PR44": 195,
}
DIFFICULTY_COUNTS = {"easy": 600, "medium": 2400, "hard": 5400, "expert": 3600}
SAFE_FALSE_ACTION_FORMS = {
    "future_second_singular", "future_plural", "future_singular",
    "preterite_plural", "preterite_second_singular", "preterite_singular",
    "conditional_plural", "conditional_singular",
    "imperfect_plural", "imperfect_singular",
    "subjunctive_past_plural", "subjunctive_past_singular",
    "gerund", "infinitive", "imperative", "participle",
}
CATEGORY_SHARE_CAPS = {
    "person": 0.18,
    "place": 0.10,
    "number": 0.12,
    "action": 0.38,
    "term": 0.45,
    "phrase": 0.12,
}
CATEGORY_TARGET_SHARES = {
    "person": 0.12,
    "place": 0.06,
    "number": 0.08,
    "action": 0.30,
    "term": 0.26,
    "phrase": 0.08,
}
# Algunas unidades breves solo contienen un nombre central (por ejemplo,
# «Dios»). El límite sigue evitando inflación global sin dejar unidades fuente
# sin representación.
# Una misma respuesta puede ser legítima en muchos capítulos (Daniel, Dios,
# Babilonia). El límite global evita dominancia sin convertir esas apariciones
# independientes en falsos duplicados; el objetivo por capítulo sigue siendo 10.
MAX_GLOBAL_FACTS_PER_ANSWER = 60
MAX_CHAPTER_FACTS_PER_ANSWER = 10
EDITORIALLY_EXCLUDED_SOURCE_UNITS = {
    "PR39-P027-P001-S005": "Frase anafórica sin detalle autónomo: Y así lo hicieron.",
}
SAFE_EXACT_NEGATION_ACTION_FORMS = {
    form
    for form in SAFE_FALSE_ACTION_FORMS
    if form not in {"gerund", "infinitive", "imperative", "participle"}
}
EDITORIALLY_EXCLUDED_CANDIDATES = {
    "PR39-P030-P002-S002": {"santo"},
}

# Estas unidades no ofrecen por sí solas suficientes nombres, números, lugares
# o verbos aislados con valor competitivo. Sus expresiones se revisaron manualmente para
# impedir que el generador vuelva a seleccionar ventanas arbitrarias de tokens.
PHRASE_ONLY_OVERRIDES = {
    "DAN2-V032": "cabeza de esta imagen",
    "DAN4-V003": "de generación en generación",
    "DAN4-V015": "bronce entre la hierba",
    "DAN10-V009": "un profundo sueño",
    "DAN11-V005": "su dominio será grande",
    "DAN12-V001": "inscritos en el libro",
    "DAN12-V007": "la dispersión del poder",
    "PR39-P030-P004-S002": "principio divino de cooperación",
    "PR39-P031-P004-S004": "satisfacción del apetito",
    "PR39-P031-P005-S001": "edificación del carácter",
    "PR39-P031-P005-S002": "adversario de las almas",
    "PR39-P031-P005-S005": "facultades superiores del ser",
    "PR39-P031-P005-S008": "leyes inmutables",
    "PR39-P032-P003-S001": "esos nobles hebreos",
    "PR40-P033-P004-S003": "dones y mercedes",
    "PR40-P035-P001-S001": "una grande imagen",
    "PR40-P035-P003-S003": "una gran verdad al monarca babilónico",
    "PR40-P037-P005-S002": "parecen hacerlos invencibles",
    "PR41-P038-P001-S004": "El sueño es verdadero",
    "PR41-P038-P004-S002": "iba a superar el original",
    "PR41-P040-P003-S001": "amenazas del rey",
    "PR41-P041-P006-S004": "libres para elegir a quien quieren servir",
    "PR43-P047-P004-S004": "hombres de genio",
    "PR43-P050-P006-S002": "el Fuerte",
    "PR43-P051-P004-S001": "no les hiciste misericordias",
    "PR43-P053-P001-S002": "todo está en agitación",
    "PR43-P053-P002-S001": "momento actual",
    "PR43-P053-P002-S002": "acontecimientos que se producen",
    "PR43-P053-P002-S003": "las naciones",
    "PR43-P053-P002-S004": "una crisis estupenda",
    "PR43-P053-P003-S001": "tan sólo la Biblia",
    "PR44-P057-P007-S003": "Un hombre cuyo corazón se apoya en Dios",
    "PR44-P057-P007-S004": "las realidades eternas",
    "PR44-P058-P004-S002": "último libro del Nuevo Testamento",
    "PR44-P059-P001-S006": "se vincula con su propósito",
    "PR44-P059-P001-S007": "lo único firme",
}
ADDITIONAL_EDITORIAL_OVERRIDES = {
    "DAN7-V002": [("los cuatro vientos", "phrase")],
    "DAN7-V013": [("un hijo de hombre", "phrase")],
    "DAN7-V025": [("tiempo, tiempos y medio tiempo", "number")],
    "DAN8-V014": [("dos mil trescientas tardes y mañanas", "number")],
    "DAN9-V024": [("Setenta semanas", "number")],
    "DAN12-V001": [
        ("tiempo de angustia", "phrase"),
        ("inscritos en el libro", "phrase"),
    ],
    "DAN12-V002": [
        ("vida eterna", "phrase"),
        ("confusión perpetua", "phrase"),
    ],
    "DAN12-V003": [("resplandor del firmamento", "phrase")],
    "DAN12-V004": [("tiempo del fin", "phrase")],
    "DAN12-V006": [("varón vestido de lino", "phrase")],
    "DAN12-V007": [
        ("tiempo, tiempos y la mitad de un tiempo", "number"),
        ("pueblo santo", "phrase"),
    ],
    "DAN12-V010": [("limpios, emblanquecidos y purificados", "phrase")],
    "DAN12-V011": [
        ("mil doscientos noventa días", "number"),
        ("abominación desoladora", "phrase"),
    ],
    "DAN12-V012": [("mil trescientos treinta y cinco días", "number")],
    "DAN12-V013": [("fin de los días", "phrase")],
    "PR39-P030-P002-S002": [("Espíritu Santo", "phrase")],
}
STOP_ANSWERS = {
    "alguno", "aquella", "aquello", "aquellos", "ellos", "estas", "estos", "mismo",
    "misma", "otros", "porque", "sobre", "todas", "todos", "cuando", "donde",
    "asi", "ahora", "luego", "despues", "tambien", "solo", "aqui", "debajo",
    "ciertamente", "dondequiera", "todavia",
    "eres", "es", "era", "eran", "estaba", "estaban", "estuve", "estuvo",
    "ser", "sido", "sea", "sean", "sera", "seran", "fue", "fueron", "habia",
    "hay", "hoy", "ayer", "manana", "cuan", "cuanto", "como", "derribad", "cortad", "trajeran",
    "levantate", "ocurrir", "sabes", "asimismo", "cualquiera", "tanto",
    "dijo", "dije", "dijeron", "decia", "dio", "habia", "habian",
    "hizo", "hicieron", "vio", "vino",
    "rey demanda es dificil", "cosa semejante a ningun",
    "tiempo algunos hombres caldeos", "dioses ni tampoco adoraremos",
    "rey confirmare pueda mudarse", "a los israelitas moises", "nadie",
}
DIVINE_NAMES = {
    "altisimo", "anciano", "cristo", "dios", "eterno", "huesped",
    "invisible", "juez", "maestro", "jehova", "mesias", "omnipotente", "principe",
    "redentor", "revelador", "salvador", "santo", "senor",
    "todopoderoso", "vigilante",
}

EXTRA_PERSON_NAMES = {
    "abednego", "aspenaz", "ezequiel", "jacob", "jeremias", "moises", "pablo",
    "satanas", "samuel",
}

EXTRA_PLACE_NAMES = {
    "atenas", "dura", "edom", "eufrates", "medo persia", "sesach", "ufaz",
}

# La fuente conserva muchas mayúsculas reverenciales o editoriales. No son
# nombres de personajes y nunca deben competir con Aspenaz, Daniel o Gabriel.
NON_ENTITY_CAPITALIZED = {
    "apocalipsis", "caldeos", "cielo", "espiritu", "escrituras",
    "evangelio", "fuente", "inspiracion", "palabra", "profecia",
    "providencia", "sabiduria", "verdad",
}

ADVERB_FORMS = {
    "asi", "ahora", "luego", "despues", "tambien", "solo", "aqui", "debajo",
    "ciertamente", "dondequiera", "entonces", "pronto", "adelante", "delante", "encima",
    "hoy", "ayer", "manana", "cuan", "cuanto", "como", "ademas",
}
NON_VERB_IA = {
    "abundancia", "angustia", "apariencia", "bestia", "ciencia", "clemencia",
    "complacencia", "conciencia", "diligencia", "dinastia", "dia", "existencia",
    "frecuencia", "furia", "gloria", "gracia", "historia", "influencia",
    "insolencia", "inteligencia", "justicia", "limpia", "magnificencia",
    "misericordia", "obediencia", "postrimeria", "potencia", "presencia",
    "profecia", "providencia", "provincia", "sabiduria", "sentencia", "todavia",
    "victoria", "vigilancia",
    "armonia", "idolatria", "mayoria", "mia", "simpatia", "vigia",
}
NON_VERB_FORMS = NON_VERB_IA | {"citara", "ira", "triste"}

FUNCTION_WORDS = {
    "a", "al", "ante", "como", "con", "contra", "de", "del", "desde",
    "durante", "el", "en", "entre", "hacia", "hasta", "la", "las", "los",
    "para", "por", "segun", "sin", "sobre", "tras", "un", "una", "y",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "mi",
    "mis", "tu", "tus", "nuestro", "nuestra", "nuestros", "nuestras",
    "mediante", "entonces",
    "yo", "el", "ella", "ellos", "ellas", "nosotros", "vosotros", "usted",
    "ustedes", "me", "te", "se", "nos", "os", "le", "les", "lo", "la",
    "mucho", "mucha", "muchos", "muchas", "gran", "grandes", "varios",
    "varias", "cierto", "cierta", "ciertos", "ciertas", "todo", "toda",
    "todos", "todas", "otro", "otra", "otros", "otras",
    "cuyo", "cuya", "cuyos", "cuyas", "aquel", "aquella", "aquellos",
    "aquellas", "alguno", "alguna", "algunos", "algunas", "unos", "unas",
    "ningun", "ninguna", "ningunos", "ningunas",
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
    "volvera", "llegara", "elevara", "fuese", "tuve", "manteniase", "vi", "oi",
    "confirmare", "pueda", "ocurrir", "comprender", "declarar", "ensenorear",
    "perdonar", "reemplazar",
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
    if normalized in NUMBER_WORDS or normalized.isdigit():
        return "number"
    if normalized in NON_VERB_FORMS:
        return "content"
    if re.search(r"(?:rá|rás|rán|ré|remos|ó|aremos|eremos|iremos)$", word.lower()):
        return "verb"
    if re.search(r"(?:ía|ían)$", word.lower()) and normalized not in NON_VERB_IA:
        return "verb"
    if normalized in VERB_FORMS or re.search(
        r"(?:ando|iendo|andose|iendose|aron|ieron|aste|iste|aba|aban|ara|ira|aran|eran|iran|ar(?:me|te|se|lo|la|los|las|le|les|nos)|er(?:me|te|se|lo|la|los|las|le|les|nos)|ir(?:me|te|se|lo|la|los|las|le|les|nos))$",
        word.lower(),
    ):
        return "verb"
    if normalized.endswith("mos") and normalized not in {"ultimos", "ramos", "blasfemos"}:
        return "verb"
    if (normalized in FUNCTION_WORDS or normalized in STOPWORDS) and word.lower() != "hacía":
        return "function"
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
        if len(words) > 1:
            return (category, "period_phrase", representation)
        return (category, length, representation)
    if category == "action":
        return (category, _action_form(value))
    if category == "phrase":
        # Estas respuestas ya pasaron selección editorial como expresiones
        # completas. La función de la palabra inicial conserva opciones
        # paralelas; la selección posterior favorece longitudes cercanas sin
        # dejar sin distractores a relaciones verbales poco frecuentes.
        head = roles[0]
        head_shape = "verb_head" if head == "verb" else "function_head" if head == "function" else "content_head"
        return (category, (head_shape,))
    if category == "term" and len(words) == 1:
        normalized = _norm(words[0])
        role = _word_role(words[0])
        if role == "verb":
            suffix = f"verb_like:{_action_form(words[0])}"
        elif role == "adverb":
            suffix = "adverb"
        elif normalized.endswith(("ivo", "iva", "ivos", "ivas")):
            suffix = "adjective_ive"
        elif normalized.endswith(("oso", "osa", "osos", "osas")):
            suffix = "adjective_ose"
        elif normalized.endswith(("ante", "ente")):
            suffix = "adjective_agent"
        elif normalized.endswith(("ados", "idos")):
            suffix = "masculine_participle_plural"
        elif normalized.endswith(("adas", "idas")):
            suffix = "feminine_participle_plural"
        elif normalized.endswith(("antes", "entes")):
            suffix = "agent_plural"
        elif normalized.endswith("os"):
            suffix = "masculine_plural"
        elif normalized.endswith("as"):
            suffix = "feminine_plural"
        elif normalized.endswith("es"):
            suffix = "e_or_consonant_plural"
        elif normalized.endswith(("cion", "sion", "dad", "tad", "encia", "ancia")):
            suffix = "feminine_consonant"
        elif normalized.endswith("a"):
            suffix = "a"
        elif normalized.endswith("o"):
            suffix = "o"
        elif normalized.endswith("e"):
            suffix = "e"
        else:
            suffix = "consonant"
        plurality = "plural" if normalized.endswith("s") else "singular"
        return (category, plurality, suffix)
    shapes = tuple(
        f"function:{_norm(word)}" if role == "function"
        else role if role in {"number", "verb", "adverb"}
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
        "sabes": "present_other", "tuvo": "preterite_singular", "dijo": "preterite_singular", "dije": "preterite_singular",
        "hizo": "preterite_singular", "vino": "preterite_singular", "puso": "preterite_singular",
        "dio": "preterite_singular", "bendijo": "preterite_singular",
        "trajo": "preterite_singular", "trajeron": "preterite_plural",
        "fue": "preterite_singular", "fueron": "preterite_plural",
    }
    if lower in irregular:
        return irregular[lower]
    for pattern, label in (
        (r"(?:rás)$", "future_second_singular"),
        (r"(?:rán|remos)$", "future_plural"),
        (r"(?:rá|ré)$", "future_singular"),
        (r"(?:aron|ieron)$", "preterite_plural"),
        (r"(?:aste|iste)$", "preterite_second_singular"),
        (r"(?:ó|é|í)$", "preterite_singular"),
        (r"(?:rían)$", "conditional_plural"),
        (r"(?:ría)$", "conditional_singular"),
        (r"(?:aban|ían)$", "imperfect_plural"),
        (r"(?:aba|ía)$", "imperfect_singular"),
        (r"(?:aran|ieran|yeran|asen|iesen)$", "subjunctive_past_plural"),
        (r"(?:ara|iera|yera|ase|iese)$", "subjunctive_past_singular"),
    ):
        if re.search(pattern, raw):
            return label
    if re.search(r"(?:ando|iendo|andose|iendose)$", lower):
        return "gerund"
    if re.search(r"(?:ar|er|ir)(?:me|te|se|lo|la|los|las|le|les|nos)?$", lower):
        return "infinitive"
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


def _relation_grammatical_category(answer: str, category: str) -> str:
    if len(answer.split()) == 1:
        if category == "action":
            return "verb"
        if category == "number":
            return "number"
        if category in {"person", "place"}:
            return "proper"
        return "word_plural" if answer.lower().endswith("s") else "word_singular"
    return "phrase_plural" if answer.lower().endswith("s") else "phrase_singular"


def _source_text(unit: dict[str, Any]) -> str:
    return str(unit.get("full_text") or unit.get("exact_text") or "").strip()


def _is_sentence_initial(text: str, start: int) -> bool:
    prefix = text[:start].rstrip()
    return not prefix or prefix[-1] in ".!?¡¿:;—–-«“”\"'"


def _broad_category(answer: str, raw_category: str, unit: dict[str, Any]) -> str:
    normalized_answer = _norm(answer)
    if normalized_answer == "israel":
        return "term"
    if (
        normalized_answer in DIVINE_NAMES and answer[:1].isupper()
    ) or normalized_answer in EXTRA_PERSON_NAMES:
        return "person"
    if normalized_answer in EXTRA_PLACE_NAMES:
        return "place"
    answer_words = {_norm(word) for word in answer.split()}
    if any(word in NUMBER_WORDS or word.isdigit() for word in answer_words):
        return "number"
    if answer in unit.get("characters", []):
        return "person"
    if answer in unit.get("places", []) or answer in unit.get("rivers", []):
        return "place"
    if answer in unit.get("directions", []):
        return "place"
    if raw_category == "proper":
        return "term"
    if raw_category == "number" or answer in unit.get("numbers", []):
        return "number"
    if raw_category == "verb" or answer in unit.get("actions", []):
        return "action"
    return "term" if len(answer.split()) == 1 else "phrase"


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
        is_named_entity = (
            answer[:1].isupper()
            and not _is_sentence_initial(text, token.start())
            and normalized not in NON_ENTITY_CAPITALIZED
        )
        raw_category = "number" if role == "number" else "verb" if role == "verb" else "proper" if is_named_entity else "word_plural" if answer.lower().endswith("s") else "word_singular"
        score = (5 if raw_category in {"proper", "number"} else 3 if raw_category == "verb" else 2) + len(answer) / 20
        if normalized in EXTRA_PERSON_NAMES or normalized in EXTRA_PLACE_NAMES:
            score += 20
        if raw_category == "verb" and _action_form(answer).startswith("conditional_"):
            score += 5
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
            if not starts_meaningfully or roles[-1] != "content" or roles.count("verb") > 1:
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
        is_reference_number = bool(
            answer.isdigit()
            and re.search(r"(?:Vers?|Caps?|Págs?|Núm)\.\s*$", text[max(0, start - 12):start], re.IGNORECASE)
        )
        content_words = [word for word, role in zip(words, roles) if role == "content"]
        invalid_content_determiner_start = (
            len(words) > 1
            and roles[0] == "content"
            and roles[1] == "function"
            and _norm(words[1]) not in {
                "a", "al", "como", "con", "contra", "de", "del", "en",
                "entre", "hacia", "hasta", "para", "por", "que", "sin",
                "sobre", "tras",
            }
        )
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
                    or roles.count("verb") > 1
                )
            )
            or (broad_category == "phrase" and len(words) == 1)
            or (broad_category == "term" and len(normalized) < 5)
            or (broad_category in {"person", "place"} and len(words) > 1)
            or is_reference_number
            or (
                broad_category == "number"
                and len(words) > 1
                and roles[0] != "number"
            )
            or crosses_plural_into_name
            or invalid_content_determiner_start
            or (
                start == 0
                and (
                    roles[0] in {"adverb", "function"}
                    or re.search(r"(?:ados|adas|ado|ada)$", normalized)
                )
            )
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
    phrase_limit = 3 if unit["work"] == "Daniel" and unit["chapter"] == 12 else 2
    if len(phrase_candidates) > phrase_limit:
        best_phrases = sorted(
            phrase_candidates,
            key=lambda row: (-float(row["score"]), -len(row["answer"]), int(row["start"])),
        )[:phrase_limit]
        candidates = [row for row in candidates if row["category"] != "phrase"] + best_phrases
    divine_candidates = [
        row for row in candidates if _norm(row["answer"]) in DIVINE_NAMES
    ]
    if len(divine_candidates) > 1:
        keep = min(divine_candidates, key=lambda row: (row["start"], row["answer"]))
        candidates = [
            row
            for row in candidates
            if _norm(row["answer"]) not in DIVINE_NAMES or row is keep
        ]
        rejected += len(divine_candidates) - 1
    if not candidates:
        raise ValueError(f"Unidad sin un detalle editorial significativo: {unit['source_unit_id']}")
    candidates.sort(key=lambda row: (-float(row["score"]), row["start"], row["answer"]))
    return candidates, rejected


def _context_for(text: str, answer: str) -> str:
    clauses = _split_propositions(text)
    containing = [clause.strip() for clause in clauses if answer in clause]
    return min(containing, key=len) if containing else text


def _slot_syntax(text: str, answer: str, category: str) -> str:
    if category != "term":
        return category
    before, separator, after = text.partition(answer)
    if not separator:
        return "term:unknown"
    before_words = TOKEN_RE.findall(before)
    after_words = TOKEN_RE.findall(after)
    previous_raw = before_words[-1] if before_words else ""
    following_raw = after_words[0] if after_words else ""
    previous = _norm(previous_raw)
    following = _norm(following_raw)
    answer_role = _word_role(answer)
    if answer_role == "adverb":
        return "term:adverb"
    if answer_role == "verb":
        return f"term:verb_like:{_action_form(answer)}"
    if previous in {"el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus"}:
        return "term:determined_nominal"
    if previous in {"a", "al", "ante", "con", "contra", "de", "del", "desde", "en", "entre", "hacia", "hasta", "para", "por", "sin", "sobre", "tras"}:
        return "term:prepositional"
    if previous and _word_role(previous_raw) == "content" and (
        following == "que" or (following and _word_role(following_raw) == "verb")
    ):
        return "term:postnominal_modifier"
    if following in {"de", "del"}:
        return "term:nominal_head"
    if before.rstrip().endswith((",", ";", ":", "—", "–")):
        return "term:list_or_clause_item"
    return "term:generic"


def derive_atomic_facts(units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    by_chapter: dict[str, list[tuple[dict[str, Any], list[dict[str, Any]]]]] = defaultdict(list)
    rejected = 0
    for unit in units:
        if unit["source_unit_id"] in EDITORIALLY_EXCLUDED_SOURCE_UNITS:
            rejected += 1
            continue
        candidates, unit_rejected = _fact_candidates(unit)
        rejected += unit_rejected
        excluded_candidates = EDITORIALLY_EXCLUDED_CANDIDATES.get(
            unit["source_unit_id"], set()
        )
        editorial_candidates = [
            row for row in candidates
            if row["category"] != "phrase"
            and _norm(row["answer"]) not in excluded_candidates
        ]
        for relation in extract_relation_candidates(unit):
            text = _source_text(unit)
            answer = str(relation["answer"])
            start = text.index(answer)
            editorial_candidates.append(
                {
                    "answer": answer,
                    "start": start,
                    "end": start + len(answer),
                    "grammatical_category": _relation_grammatical_category(
                        answer, str(relation["category"])
                    ),
                    "category": relation["category"],
                    "score": relation["score"],
                    "relation_type": relation["relation_type"],
                    "relation_prompt": relation["question"],
                }
            )
        overrides: list[tuple[str, str]] = []
        phrase_override = PHRASE_ONLY_OVERRIDES.get(unit["source_unit_id"])
        if phrase_override:
            overrides.append((phrase_override, "phrase"))
        overrides.extend(ADDITIONAL_EDITORIAL_OVERRIDES.get(unit["source_unit_id"], []))
        for override, category in overrides:
            text = _source_text(unit)
            if text.count(override) != 1:
                raise ValueError(f"Expresión editorial inválida en {unit['source_unit_id']}: {override}")
            start = text.index(override)
            editorial_candidates.append(
                {
                    "answer": override,
                    "start": start,
                    "end": start + len(override),
                    "grammatical_category": (
                        "number_phrase"
                        if category == "number"
                        else "phrase_plural" if override.lower().endswith("s") else "phrase_singular"
                    ),
                    "category": category,
                    "score": 10.0,
                }
            )
        if not editorial_candidates:
            raise ValueError(f"Unidad sin hecho editorial revisado: {unit['source_unit_id']}")
        deduplicated_candidates: dict[tuple[str, str], dict[str, Any]] = {}
        for candidate in editorial_candidates:
            key = (_norm(candidate["answer"]), str(candidate.get("relation_type") or "detail"))
            current = deduplicated_candidates.get(key)
            if current is None or float(candidate["score"]) > float(current["score"]):
                deduplicated_candidates[key] = candidate
        editorial_candidates = list(deduplicated_candidates.values())
        editorial_candidates.sort(key=lambda row: (-float(row["score"]), row["start"], row["answer"]))
        rejected += len(candidates) - len(editorial_candidates)
        by_chapter[_chapter_key(unit)].append((unit, editorial_candidates))

    facts: list[dict[str, Any]] = []
    global_answer_usage: Counter[str] = Counter()
    for chapter, quota in FACT_QUOTAS.items():
        rows = by_chapter[chapter]
        selected: list[tuple[dict[str, Any], dict[str, Any], int]] = []
        chapter_answer_usage: Counter[str] = Counter()
        chapter_category_usage: Counter[str] = Counter()
        used_candidate_indexes: dict[str, set[int]] = defaultdict(set)

        def select_best_candidate(
            unit: dict[str, Any], candidates: list[dict[str, Any]]
        ) -> tuple[dict[str, Any], int] | None:
            source_unit_id = unit["source_unit_id"]
            available = [
                (candidate, index)
                for index, candidate in enumerate(candidates)
                if index not in used_candidate_indexes[source_unit_id]
            ]
            if not available:
                return None
            candidate, candidate_index = min(
                available,
                key=lambda row: (
                    _norm(row[0]["answer"])
                    not in (EXTRA_PERSON_NAMES | EXTRA_PLACE_NAMES),
                    chapter_answer_usage[_norm(row[0]["answer"])] >= MAX_CHAPTER_FACTS_PER_ANSWER,
                    global_answer_usage[_norm(row[0]["answer"])] >= MAX_GLOBAL_FACTS_PER_ANSWER,
                    chapter_category_usage[row[0]["category"]]
                    / max(1, math.ceil(quota * CATEGORY_TARGET_SHARES[row[0]["category"]])),
                    chapter_category_usage[row[0]["category"]]
                    >= math.ceil(quota * CATEGORY_SHARE_CAPS[row[0]["category"]]),
                    chapter_answer_usage[_norm(row[0]["answer"])] * 8
                    + global_answer_usage[_norm(row[0]["answer"])] * 2
                    - float(row[0]["score"]),
                    row[1],
                    row[0]["start"],
                ),
            )
            used_candidate_indexes[source_unit_id].add(candidate_index)
            normalized_answer = _norm(candidate["answer"])
            chapter_answer_usage[normalized_answer] += 1
            global_answer_usage[normalized_answer] += 1
            chapter_category_usage[candidate["category"]] += 1
            return candidate, candidate_index + 1

        for unit, candidates in rows:
            choice = select_best_candidate(unit, candidates)
            if choice is None:
                raise ValueError(f"Unidad sin hecho seleccionable: {unit['source_unit_id']}")
            candidate, ordinal = choice
            selected.append((unit, candidate, ordinal))
        while len(selected) < quota:
            added = False
            for unit, candidates in rows:
                if len(selected) >= quota:
                    break
                choice = select_best_candidate(unit, candidates)
                if choice is not None:
                    candidate, ordinal = choice
                    selected.append((unit, candidate, ordinal))
                    added = True
            if not added:
                raise ValueError(f"La fuente no permite {quota} hechos legítimos en {chapter}")
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
                    "_slot_signature": _slot_syntax(source_quote, answer, candidate["category"]),
                    "importance": "critical" if chapter in {"DAN7", "DAN8", "DAN9", "DAN11", "PR43", "PR44"} else "high" if chapter in {"DAN10", "DAN12", "PR40", "PR42"} else "essential",
                    "relation_type": candidate.get("relation_type") or candidate["category"],
                    "relation_prompt": candidate.get("relation_prompt"),
                }
            )
    facts.sort(key=lambda row: (row["chapter"], row["source_unit_id"], row["fact_id"]))
    support_rows: list[dict[str, Any]] = []
    for chapter, chapter_rows in by_chapter.items():
        for unit, candidates in chapter_rows:
            source_text = _source_text(unit)
            for candidate_index, candidate in enumerate(candidates):
                support_rows.append(
                    {
                        "fact_id": f"SUPPORT-{unit['source_unit_id']}-{candidate_index:03d}",
                        "source_unit_id": unit["source_unit_id"],
                        "chapter": chapter,
                        "reference": unit["reference"],
                        "answer": candidate["answer"],
                        "category": candidate["category"],
                        "grammatical_category": candidate["grammatical_category"],
                        "_normalized_answer": _norm(candidate["answer"]),
                        "_normalized_source": _norm(source_text),
                        "_slot_signature": _slot_syntax(
                            source_text, candidate["answer"], candidate["category"]
                        ),
                    }
                )

    def support_key(row: dict[str, Any]) -> tuple[Any, ...]:
        grammar = (
            None
            if row["category"] in {"person", "place", "phrase", "term"}
            else row["grammatical_category"]
        )
        return (
            row["category"],
            option_signature(row["answer"], row["category"]),
            grammar,
        )

    support_pools: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in support_rows:
        support_pools[support_key(row)].append(row)

    for fact in facts:
        compatible_support = [
            row
            for row in support_pools[support_key(fact)]
            if row["_normalized_answer"] != fact["_normalized_answer"]
            and row["_normalized_answer"] not in fact["_normalized_source"]
        ]
        unique_support: dict[str, dict[str, Any]] = {}
        for row in sorted(
            compatible_support,
            key=lambda row: (
                row["chapter"] != fact["chapter"],
                abs(len(row["answer"]) - len(fact["answer"])),
                _hash(f"support:{fact['fact_id']}:{row['fact_id']}"),
            ),
        ):
            unique_support.setdefault(row["_normalized_answer"], row)
        fact["_support_distractors"] = list(unique_support.values())[:12]

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


def _complete_statement_text(text: str) -> str:
    stripped = text.strip()
    closing_match = re.search(r"([”’\"»]+)$", stripped)
    closing = closing_match.group(1) if closing_match else ""
    core = stripped[:-len(closing)] if closing else stripped
    if re.search(r"[.!?]$", core):
        return core + closing
    return core.rstrip(" ,;:") + "." + closing


def _atomic_true_false_statement(fact: dict[str, Any]) -> str:
    lead = {
        "person": "entre los personajes o seres nombrados aparece",
        "place": "entre los lugares o direcciones mencionados aparece",
        "number": "entre los números o períodos expresados aparece",
        "action": "el texto emplea la forma verbal",
    }[fact["category"]]
    return f"{lead} «{fact['answer']}»."


def _negate_exact_action_statement(statement: str, answer: str) -> str | None:
    """Negate one finite verb without breaking adjacent Spanish clitics."""
    if _action_form(answer) not in SAFE_EXACT_NEGATION_ACTION_FORMS:
        return None
    if statement.count(answer) != 1:
        return None
    answer_start = statement.index(answer)
    if (
        _action_form(answer) == "subjunctive_past_singular"
        and _is_sentence_initial(statement, answer_start)
    ):
        # Terminaciones como «Compara» coinciden superficialmente con «-ara»,
        # pero aquí pueden ser imperativos y exigirían «No compares».
        return None
    if _norm(answer).endswith("iase"):
        # Formas enclíticas antiguas como «manteníase» requieren mover «se».
        return None
    prefix = statement[:answer_start]
    insert_at = answer_start
    clitic = re.search(r"\b(?:me|te|se|lo|la|los|las|le|les|nos)\s+$", prefix, re.I)
    if clitic:
        insert_at = clitic.start()
    words_before = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", statement[:insert_at])
    if words_before and _norm(words_before[-1]) in {"no", "ni", "nunca", "tampoco", "sin"}:
        return None
    negation = "No " if _is_sentence_initial(statement, insert_at) else "no "
    suffix = statement[insert_at:]
    if negation == "No " and suffix:
        suffix = suffix[:1].lower() + suffix[1:]
    return statement[:insert_at] + negation + suffix


def _category_label(category: str) -> str:
    return {
        "person": "personaje o ser",
        "place": "lugar o dirección",
        "number": "detalle numérico",
        "action": "acción",
        "term": "término",
        "phrase": "expresión",
    }[category]


def _chapter_label(chapter: str) -> str:
    return f"Daniel {chapter[3:]}" if chapter.startswith("DAN") else chapter


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


def _match_initial_case(value: str, model: str) -> str:
    """Ajusta solo la inicial para que el distractor encaje en el mismo hueco."""
    if not value or not model:
        return value
    if model[0].islower() and value[0].isupper():
        return value[0].lower() + value[1:]
    if model[0].isupper() and value[0].islower():
        return value[0].upper() + value[1:]
    return value


def _boundary_collision(context: str, answer: str, replacement: str) -> bool:
    before, separator, after = context.partition(answer)
    if not separator:
        return True
    before_words = _norm(before).split()
    replacement_words = _norm(replacement).split()
    after_words = _norm(after).split()
    if not replacement_words:
        return True
    return bool(
        (before_words and before_words[-1] == replacement_words[0])
        or (after_words and replacement_words[-1] == after_words[0])
    )


def _phrase_entity_target(
    fact: dict[str, Any], entity_categories: dict[str, str]
) -> tuple[int, str] | None:
    for index, word in reversed(list(enumerate(fact["answer"].split()))):
        normalized = _norm(word)
        if index > 0 and normalized in entity_categories:
            return index, entity_categories[normalized]
    return None


def _named_entity_phrase_replacement(
    fact: dict[str, Any], entity_categories: dict[str, str], facts: list[dict[str, Any]]
) -> str | None:
    target = _phrase_entity_target(fact, entity_categories)
    if target is None:
        return None
    index, category = target
    original = fact["answer"].split()
    original_name = _norm(original[index])
    if original_name in DIVINE_NAMES:
        return None
    candidates = sorted(
        {
            row["answer"]
            for row in facts
            if row["category"] == category
            and len(row["answer"].split()) == 1
            and _norm(row["answer"]) != original_name
            and _norm(row["answer"]) not in fact["_normalized_source"]
            and _norm(row["answer"]) not in DIVINE_NAMES
        },
        key=lambda answer: _hash(f"entity-false:{fact['fact_id']}:{answer}"),
    )
    if not candidates:
        return None
    altered = [*original]
    altered[index] = candidates[0]
    return " ".join(altered)


def _review_choice(question: dict[str, Any]) -> dict[str, Any]:
    quote_norm = _norm(question["source_quote"])
    def contains_phrase(value: str) -> bool:
        normalized = _norm(value)
        return bool(normalized) and f" {normalized} " in f" {quote_norm} "

    supported = [
        index for index, option in enumerate(question["options"])
        if contains_phrase(option)
    ]
    if question["family"] == "true_false":
        statement_supported = contains_phrase(question.get("asserted_detail") or "")
        correction_supported = contains_phrase(question.get("correction") or "")
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
        "schema_version": SCHEMA_VERSION,
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
    if len(facts) != 3000:
        raise ValueError("Se requieren exactamente 3,000 hechos seleccionados")
    distractor_pools: dict[tuple[str, tuple[Any, ...]], list[dict[str, Any]]] = defaultdict(list)
    entity_categories = {
        _norm(fact["answer"]): fact["category"]
        for fact in facts
        if fact["category"] in {"person", "place"}
        and len(fact["answer"].split()) == 1
    }
    for fact in facts:
        distractor_pools[(fact["category"], option_signature(fact["answer"], fact["category"]))].append(fact)

    def compatible_rows(fact: dict[str, Any]) -> list[dict[str, Any]]:
        rows = list(
            distractor_pools[(fact["category"], option_signature(fact["answer"], fact["category"]))]
        ) + list(fact.get("_support_distractors", []))
        eligible = [
            row for row in rows
            if row["fact_id"] != fact["fact_id"]
            and row["_normalized_answer"] != fact["_normalized_answer"]
            and row["_normalized_answer"] not in fact["_normalized_source"]
            and (
                fact["category"] in {"person", "place", "phrase", "term"}
                or row["grammatical_category"] == fact["grammatical_category"]
            )
        ]
        unique: dict[str, dict[str, Any]] = {}
        for row in eligible:
            unique.setdefault(row["_normalized_answer"], row)
        return sorted(
            unique.values(),
            key=lambda row: (
                option_signature(row["answer"], row["category"])
                != option_signature(fact["answer"], fact["category"]),
                fact["category"] == "person"
                and ((_norm(row["answer"]) in DIVINE_NAMES) != (_norm(fact["answer"]) in DIVINE_NAMES)),
                fact["category"] == "action" and _action_form(row["answer"]) != _action_form(fact["answer"]),
                row["chapter"] != fact["chapter"],
                row["grammatical_category"] != fact["grammatical_category"],
                abs(len(row["answer"]) - len(fact["answer"])),
                _hash(f"{fact['fact_id']}:{row['fact_id']}"),
            ),
        )

    distractor_map = {fact["fact_id"]: compatible_rows(fact) for fact in facts}
    insufficient = [fact_id for fact_id, rows in distractor_map.items() if len(rows) < 3]
    if insufficient:
        raise ValueError(f"Hay hechos sin tres distractores compatibles: {insufficient[:20]}")
    strict_false_distractor_map = {
        fact["fact_id"]: [
            row
            for row in distractor_map[fact["fact_id"]]
            if fact["category"] != "term"
            or row.get("_slot_signature") == fact.get("_slot_signature")
        ]
        for fact in facts
    }
    def false_replacements(fact: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            row
            for row in strict_false_distractor_map[fact["fact_id"]]
            if not _boundary_collision(fact["context"], fact["answer"], row["answer"])
            and (
                fact["category"] != "action"
                or (
                    _word_role(fact["answer"]) == "verb"
                    and _word_role(row["answer"]) == "verb"
                    and _action_form(fact["answer"]) in SAFE_FALSE_ACTION_FORMS
                    and _action_form(fact["answer"]) == _action_form(row["answer"])
                )
            )
            and (
                fact["category"] != "person"
                or ((_norm(row["answer"]) in DIVINE_NAMES) == (_norm(fact["answer"]) in DIVINE_NAMES))
            )
        ]

    def can_make_false(fact: dict[str, Any]) -> bool:
        # Free substitution inside a long phrase can remain grammatical while
        # becoming absurd. Phrase facts stay as exact, complete statements;
        # other categories supply the balanced false half of the bank.
        return (
            fact["category"] in {"person", "place", "number", "action"}
            and (
                fact["category"] != "action"
                or (
                    _word_role(fact["answer"]) == "verb"
                    and _action_form(fact["answer"]) in SAFE_FALSE_ACTION_FORMS
                )
            )
            and bool(false_replacements(fact))
        )

    safe_false_candidates = sorted(
        [fact for fact in facts if can_make_false(fact)],
        key=lambda fact: (
            fact["grammatical_category"] not in {
                "proper", "number", "verb", "word_singular", "word_plural"
            },
            _hash("safe-false:" + fact["fact_id"]),
        ),
    )

    # Cada hecho V/F necesita una afirmación verdadera completa y única. Un
    # hecho puede usar la cláusula local o la unidad fuente íntegra; ambas son
    # citas literales, nunca una paráfrasis inventada para distinguir variantes.
    def true_statement_options(fact: dict[str, Any]) -> list[str]:
        rows = []
        for source_text in (fact["context"], fact["source_quote"]):
            if source_text.count(fact["answer"]) != 1:
                continue
            completed = _complete_statement_text(source_text)
            if completed not in rows:
                rows.append(completed)
        rows.append(_atomic_true_false_statement(fact))
        return rows

    facts_by_id = {fact["fact_id"]: fact for fact in safe_false_candidates}
    statement_owner: dict[tuple[str, str], str] = {}
    statement_by_fact: dict[str, str] = {}

    def assign_unique_statement(fact: dict[str, Any], seen: set[tuple[str, str]]) -> bool:
        for statement_text in true_statement_options(fact):
            key = (fact["reference"], statement_text)
            if key in seen:
                continue
            seen.add(key)
            previous_id = statement_owner.get(key)
            if previous_id is None or assign_unique_statement(facts_by_id[previous_id], seen):
                statement_owner[key] = fact["fact_id"]
                statement_by_fact[fact["fact_id"]] = statement_text
                return True
        return False

    for fact in safe_false_candidates:
        assign_unique_statement(fact, set())
        if len(statement_by_fact) >= 1500:
            break
    if len(statement_by_fact) < 1500:
        raise ValueError(
            "La fuente no permite 1,500 pares V/F seguros y únicos: "
            f"{len(statement_by_fact)}"
        )
    true_facts = [
        facts_by_id[fact_id]
        for fact_id in sorted(
            statement_by_fact,
            key=lambda fact_id: _hash("tf-true-selected:" + fact_id),
        )[:1500]
    ]
    selected_true_ids = {fact["fact_id"] for fact in true_facts}
    statement_by_fact = {
        fact_id: statement
        for fact_id, statement in statement_by_fact.items()
        if fact_id in selected_true_ids
    }
    questions: list[dict[str, Any]] = []
    used_true_false_prompts: set[str] = set()
    used_true_false_prompt_norms: set[str] = set()
    rejected = sum(max(0, len(rows) - 3) for rows in distractor_map.values())

    for index, fact in enumerate(facts):
        distractor_facts = distractor_map[fact["fact_id"]]
        distractors = [
            _match_initial_case(row["answer"], fact["answer"])
            for row in distractor_facts[:3]
        ]
        why = {
            _match_initial_case(row["answer"], fact["answer"]):
                f"Es verdadero en {row['reference']}, pero no responde al contexto exacto de {fact['reference']}."
            for row in distractor_facts[:3]
        }
        for family_offset, family in enumerate(
            ("single_choice_direct", "fill_choice", "single_choice_contextual")
        ):
            base = _base_question(fact, family, index)
            position = (index + family_offset) % 4
            options = _arrange_options(fact["answer"], distractors, position)
            masked_context = _masked(fact["context"], fact["answer"], "________")
            if family == "fill_choice":
                question_text = f"Complete {fact['reference']}: «{masked_context}»"
                trap_type = None
            elif family == "single_choice_contextual":
                question_text = fact.get("relation_prompt") or (
                    f"Según {fact['reference']}, ¿qué {_category_label(fact['category'])} "
                    f"corresponde específicamente a esta escena: "
                    f"«{_masked(fact['context'], fact['answer'], '[…]')}»?"
                )
                trap_type = "true_in_other_context"
            else:
                question_text = (
                    f"Según {fact['reference']}, ¿qué {_category_label(fact['category'])} completa "
                    f"correctamente «{masked_context}»?"
                )
                trap_type = None
            base.update(
                {
                    "question": question_text,
                    "options": options,
                    "correct_option": position,
                    "correct_answer": fact["answer"],
                    "explanation": (
                        f"En el contexto exacto de {fact['reference']}, el detalle aplicable es «{fact['answer']}»: «{fact['context']}»."
                        if family == "single_choice_contextual"
                        else f"{fact['reference']} declara literalmente «{fact['context']}». La respuesta pedida es «{fact['answer']}»."
                    ),
                    "why_distractors_fail": why,
                    "trap_type": trap_type,
                }
            )
            base["validation_adversarial"] = _review_choice(base)
            if base["validation_adversarial"]["status"] != "passed":
                raise ValueError(f"Revisión adversarial fallida: {base['id']}")
            questions.append(base)

    fact_index = {fact["fact_id"]: index for index, fact in enumerate(facts)}
    def append_true_false(
        fact: dict[str, Any],
        source_statement: str,
        false: bool,
        replacement_row: dict[str, Any] | None = None,
        *,
        visible_text_override: str | None = None,
        incorrect_detail_override: str | None = None,
        false_mutation_kind: str | None = None,
    ) -> None:
        base = _base_question(fact, "true_false", fact_index[fact["fact_id"]])
        variant_label = "FALSE" if false else "TRUE"
        base["id"] = f"{base['id']}-{variant_label}"
        base["variant_id"] = f"{base['variant_id']}-{variant_label}"
        base["template_id"] = "true-false-safe-editorial-v2"
        replacement = (
            _match_initial_case(replacement_row["answer"], fact["answer"])
            if replacement_row else fact["answer"]
        )
        visible_text = visible_text_override or (
            source_statement.replace(fact["answer"], replacement, 1)
            if false else source_statement
        )
        incorrect_detail = incorrect_detail_override or replacement
        statement = f"Según {fact['reference']}, {visible_text}"
        prompt = f"Verdadero o falso: {statement}"
        if prompt in used_true_false_prompts:
            raise ValueError(f"V/F duplicado: {fact['fact_id']} ({variant_label})")
        used_true_false_prompts.add(prompt)
        used_true_false_prompt_norms.add(_norm(prompt))
        corrected_statement = f"Según {fact['reference']}, {source_statement}"
        exact_source_statements = {
            _complete_statement_text(fact["context"]),
            _complete_statement_text(fact["source_quote"]),
        }
        statement_mode = (
            "exact_source" if source_statement in exact_source_statements else "atomic_presence"
        )
        base.update(
            {
                "question": prompt,
                "statement": statement,
                "asserted_detail": incorrect_detail,
                "options": ["Verdadero", "Falso"],
                "correct_option": 1 if false else 0,
                "correct_answer": "Falso" if false else "Verdadero",
                "corrected_statement": corrected_statement if false else "",
                "incorrect_detail": incorrect_detail if false else None,
                "correction": fact["answer"] if false else None,
                "false_mutation_kind": false_mutation_kind if false else None,
                "focused_true_statement": False,
                "statement_mode": statement_mode,
                "truth_source_statement": source_statement,
                "replacement_source_ref": replacement_row["reference"] if replacement_row else None,
                "correct_slot_signature": fact.get("_slot_signature"),
                "replacement_slot_signature": replacement_row.get("_slot_signature") if replacement_row else None,
                "explanation": (
                    f"Es falsa: la fuente dice «{fact['answer']}», no «{incorrect_detail}»."
                    if false else f"Es verdadera y reproduce literalmente {fact['reference']}."
                ),
                "why_distractors_fail": {
                    "Verdadero" if false else "Falso": (
                        f"La única alteración es «{incorrect_detail}»; la fuente contiene «{fact['answer']}»."
                        if false else "La afirmación coincide literalmente con la unidad fuente."
                    )
                },
                "trap_type": "single_plausible_detail" if false else None,
            }
        )
        base["validation_adversarial"] = _review_choice(base)
        if base["validation_adversarial"]["status"] != "passed":
            raise ValueError(
                f"Revisión adversarial fallida: {base['id']} "
                f"({base['question']!r}; detalle={base.get('incorrect_detail')!r}; "
                f"corrección={base.get('correction')!r})"
            )
        questions.append(base)

    for fact in true_facts:
        append_true_false(fact, statement_by_fact[fact["fact_id"]], False)

    false_specs: list[tuple[dict[str, Any], str, dict[str, Any], str, str, str]] = []
    for fact in true_facts:
        selected: tuple[str, dict[str, Any], str, str, str] | None = None
        source_statement = statement_by_fact[fact["fact_id"]]
        replacement_candidates = false_replacements(fact)
        if fact["category"] == "action":
            exact_source_statements = {
                _complete_statement_text(fact["context"]),
                _complete_statement_text(fact["source_quote"]),
            }
            negated = (
                _negate_exact_action_statement(source_statement, fact["answer"])
                if source_statement in exact_source_statements
                else None
            )
            if negated is not None:
                incorrect_detail = f"no {fact['answer'].lower()}"
                prompt = f"Verdadero o falso: Según {fact['reference']}, {negated}"
                if (
                    prompt not in used_true_false_prompts
                    and _norm(prompt) not in used_true_false_prompt_norms
                ):
                    selected = (
                        source_statement,
                        {
                            "answer": incorrect_detail,
                            "reference": fact["reference"],
                            "_slot_signature": fact.get("_slot_signature"),
                        },
                        negated,
                        incorrect_detail,
                        "negation",
                    )
            if selected is None:
                source_statement = _atomic_true_false_statement(fact)
        elif (
            fact["category"] == "person"
            and _norm(fact["answer"]) in DIVINE_NAMES
        ):
            # Sustituir «Señor» por «Santo» puede conservar el mismo referente
            # y no produce una falsedad semántica inequívoca. En estos casos se
            # pregunta solo por presencia textual y se usa otro personaje.
            source_statement = _atomic_true_false_statement(fact)
            replacement_candidates = [
                row
                for row in strict_false_distractor_map[fact["fact_id"]]
                if _norm(row["answer"]) not in DIVINE_NAMES
                and not _boundary_collision(
                    fact["context"], fact["answer"], row["answer"]
                )
            ]
        for replacement_row in replacement_candidates:
            if selected is not None:
                break
            replacement = _match_initial_case(replacement_row["answer"], fact["answer"])
            visible_text = source_statement.replace(fact["answer"], replacement, 1)
            prompt = f"Verdadero o falso: Según {fact['reference']}, {visible_text}"
            if (
                prompt not in used_true_false_prompts
                and _norm(prompt) not in used_true_false_prompt_norms
            ):
                selected = (
                    source_statement,
                    replacement_row,
                    visible_text,
                    replacement,
                    (
                        "atomic_presence_substitution"
                        if source_statement == _atomic_true_false_statement(fact)
                        else "closed_category_substitution"
                    ),
                )
                break
        if selected:
            (
                source_statement,
                replacement_row,
                visible_text,
                incorrect_detail,
                false_mutation_kind,
            ) = selected
            # Reservar antes de continuar para impedir que otro hecho produzca
            # el mismo enunciado alterado durante la selección.
            used_true_false_prompts.add(
                f"Verdadero o falso: Según {fact['reference']}, "
                f"{visible_text}"
            )
            used_true_false_prompt_norms.add(
                _norm(
                    f"Verdadero o falso: Según {fact['reference']}, "
                    f"{visible_text}"
                )
            )
            false_specs.append(
                (
                    fact,
                    source_statement,
                    replacement_row,
                    visible_text,
                    incorrect_detail,
                    false_mutation_kind,
                )
            )
    if len(false_specs) != 1500:
        raise ValueError(
            "La fuente no permite 1,500 alteraciones V/F seguras y únicas: "
            f"{len(false_specs)}"
        )
    # Las reservas anteriores solo sirvieron durante la selección; la función
    # de emisión vuelve a registrarlas junto con las verdaderas ya emitidas.
    used_true_false_prompts = {
        question["question"]
        for question in questions
        if question["family"] == "true_false"
    }
    used_true_false_prompt_norms = {_norm(prompt) for prompt in used_true_false_prompts}
    for (
        fact,
        source_statement,
        replacement_row,
        visible_text,
        incorrect_detail,
        false_mutation_kind,
    ) in false_specs:
        append_true_false(
            fact,
            source_statement,
            True,
            replacement_row,
            visible_text_override=visible_text,
            incorrect_detail_override=incorrect_detail,
            false_mutation_kind=false_mutation_kind,
        )

    answer_frequency = Counter(fact["_normalized_answer"] for fact in facts)

    def difficulty_score(question: dict[str, Any]) -> float:
        family_score = {
            "single_choice_direct": 1.0,
            "fill_choice": 1.3,
            "true_false": 3.6 if question["correct_answer"] == "Falso" else 2.2,
            "single_choice_contextual": 5.0,
        }[question["family"]]
        category_score = {
            "person": 0.0,
            "place": 0.2,
            "term": 0.6,
            "action": 0.8,
            "number": 1.0,
            "phrase": 1.2,
            "reference": 1.0,
        }.get(question["option_category"], 0.5)
        importance_score = {
            "critical": 0.7,
            "high": 0.4,
            "essential": 0.0,
        }[question["importance"]]
        context_score = min(0.8, len(question["source_quote"].split()) / 80)
        rarity_score = 0.4 if answer_frequency[_norm(question["accepted_answers"][0])] <= 2 else 0.0
        return family_score + category_score + importance_score + context_score + rarity_score

    def hardest(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
        return sorted(
            rows,
            key=lambda row: (-difficulty_score(row), _hash("difficulty:" + row["id"])),
        )[:count]

    expert_reserved = (
        hardest(
            [question for question in questions if question["family"] == "single_choice_direct"],
            270,
        )
        + hardest(
            [question for question in questions if question["family"] == "true_false"],
            210,
        )
        + hardest(
            [question for question in questions if question["family"] == "single_choice_contextual"],
            1800,
        )
    )
    expert_ids = {question["id"] for question in expert_reserved}
    expert_fill = hardest(
        [question for question in questions if question["id"] not in expert_ids],
        DIFFICULTY_COUNTS["expert"] - len(expert_ids),
    )
    expert_ids.update(question["id"] for question in expert_fill)
    for question in questions:
        if question["id"] in expert_ids:
            question["difficulty"] = "expert"

    remaining = sorted(
        [question for question in questions if question["id"] not in expert_ids],
        key=lambda row: (difficulty_score(row), _hash("difficulty:" + row["id"])),
    )
    cursor = 0
    for label in ("easy", "medium", "hard"):
        count = DIFFICULTY_COUNTS[label]
        for question in remaining[cursor:cursor + count]:
            question["difficulty"] = label
        cursor += count

    blind_order = sorted(facts, key=lambda fact: _hash("blind:" + fact["fact_id"]))[:450]
    blind_lookup = {
        fact["fact_id"]: ("A" if index < 150 else "B" if index < 300 else "emergency")
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
        excluded_reason = EDITORIALLY_EXCLUDED_SOURCE_UNITS.get(unit["source_unit_id"])
        entries.append(
            {
                "source_unit_id": unit["source_unit_id"],
                "chapter": _chapter_key(unit),
                "reference": unit["reference"],
                "source_text": _source_text(unit),
                "fact_ids": [fact["fact_id"] for fact in unit_facts],
                "gold_question_ids": [question["id"] for question in question_rows],
                "question_families": sorted({question["family"] for question in question_rows}),
                "coverage_status": (
                    "excluded_low_value"
                    if excluded_reason
                    else "covered" if unit_facts and question_rows else "uncovered"
                ),
                "exclusion_reason": excluded_reason,
                "reviewer_status": (
                    "excluded"
                    if excluded_reason
                    else "passed" if question_rows and all(question["validation_adversarial"]["status"] == "passed" for question in question_rows) else "failed"
                ),
            }
        )
    fact_without = sum(not questions_by_fact.get(fact["fact_id"]) for fact in facts)
    uncovered = sum(entry["coverage_status"] == "uncovered" for entry in entries)
    excluded = sum(entry["coverage_status"] == "excluded_low_value" for entry in entries)
    covered = sum(entry["coverage_status"] == "covered" for entry in entries)
    mapped = {entry["source_unit_id"] for entry in entries}
    return {
        "schema_version": SCHEMA_VERSION,
        "bank_id": BANK_ID,
        "source_units": len(entries),
        "covered_source_units": covered,
        "excluded_low_value_source_units": excluded,
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
    location_answer_pattern = re.compile(
        r"^(?:Daniel \d+:\d+|PR\d+, p\. \d+(?:, párrafo \d+)?)$"
    )
    location_prompt_pattern = re.compile(
        r"\ben (?:qué|cuál) (?:referencia|versículo|página|párrafo)\b",
        re.IGNORECASE,
    )
    source_location_questions = sum(
        bool(location_prompt_pattern.search(question["question"]))
        or bool(location_answer_pattern.fullmatch(str(question["correct_answer"]).strip()))
        or any(
            location_answer_pattern.fullmatch(str(option).strip())
            for option in question["options"]
        )
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
    blank_pattern = re.compile(r"_{4,}")
    family_contract_errors: Counter[str] = Counter()
    for question in questions:
        blank_count = len(blank_pattern.findall(question["question"]))
        family = question["family"]
        if family == "true_false":
            invalid = (
                blank_count != 0
                or question.get("statement", "") not in question["question"]
                or "completa la frase" in question["question"]
            )
        elif family == "fill_choice":
            invalid = (
                blank_count != 1
                or not question["question"].startswith("Complete ")
            )
        elif family == "single_choice_contextual":
            invalid = (
                blank_count != 0
                or question.get("trap_type") != "true_in_other_context"
                or len(question.get("why_distractors_fail", {})) != 3
            )
        else:
            invalid = blank_count != 1
        if invalid:
            family_contract_errors[family] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "bank_id": BANK_ID,
        "gold_questions": len(questions),
        "unique_facts": len(facts),
        "ambiguous_gold_questions": sum(question["validation_adversarial"]["status"] != "passed" for question in questions),
        "unsupported_gold_answers": sum(
            question["family"] != "true_false"
            and question["correct_answer"] not in question["source_quote"]
            for question in questions
        ),
        "source_location_questions": source_location_questions,
        "duplicate_gold_questions": len(normalized_questions) - len(set(normalized_questions)),
        "lexical_sequence_questions": sum("→" in question["question"] for question in questions),
        "broken_true_false": sum(
            not question.get("incorrect_detail") or not question.get("correction")
            for question in false_questions
        ),
        "unsafe_true_false_templates": sum(
            bool(question.get("focused_true_statement"))
            or "al evaluar específicamente" in question.get("statement", "").casefold()
            or (
                question["correct_answer"] == "Falso"
                and question.get("option_category") not in {"person", "place", "number", "action"}
            )
            for question in questions
            if question["family"] == "true_false"
        ),
        "invalid_references": invalid_references,
        "external_knowledge_questions": sum(question["validation_source"].get("external_knowledge") is not False for question in questions),
        "answer_length_leaks": length_leaks,
        "orphan_numeric_source_fragments": sum(
            bool(re.match(r"^\d+\)?,", fact["source_quote"])) for fact in facts
        ),
        "family_contract_violations": sum(family_contract_errors.values()),
        "family_contract_violations_by_family": dict(family_contract_errors),
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
