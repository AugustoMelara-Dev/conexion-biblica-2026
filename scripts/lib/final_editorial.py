"""Generación editorial determinista del Banco Maestro Único."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any, Iterable

from scripts.lib.final_bank import BANK_ID, DISPLAY_NAME, QUESTION_FAMILIES, SCHEMA_VERSION
from scripts.lib.contextual_roles import (
    GENERIC_CONTEXTUAL_FRAGMENT,
    contains_normalized_phrase,
    render_contextual_identity,
    render_contextual_question,
)
from scripts.lib.final_relations import extract_relation_candidates
from scripts.lib.editorial_overrides import DISTRACTOR_FACT_ID_OVERRIDES
from scripts.lib.massive_generator import NUMBER_WORDS, STOPWORDS, TOKEN_RE, _candidate_spans
from scripts.lib.source_inventory import _split_propositions


FACT_QUOTAS = {
    "DAN1": 83, "DAN2": 120, "DAN3": 90, "DAN4": 105, "DAN5": 90,
    "DAN6": 90, "DAN7": 225, "DAN8": 225, "DAN9": 225, "DAN10": 135,
    "DAN11": 306, "DAN12": 104, "PR39": 210, "PR40": 195, "PR41": 181,
    "PR42": 180, "PR43": 241, "PR44": 195,
}
DIFFICULTY_COUNTS = {"easy": 600, "medium": 2400, "hard": 5400, "expert": 3600}
SAFE_FALSE_ACTION_FORMS = {
    "future_second_singular", "future_plural", "future_singular",
    "preterite_first_singular", "preterite_plural", "preterite_second_singular", "preterite_singular",
    "conditional_plural", "conditional_singular",
    "imperfect_plural", "imperfect_singular",
    "subjunctive_past_plural", "subjunctive_past_singular",
    "future_subjunctive_plural", "future_subjunctive_singular",
    "future_second_plural", "present_first_plural", "present_second_plural",
    "gerund", "infinitive", "imperative",
    "participle_masculine_singular", "participle_feminine_singular",
    "participle_masculine_plural", "participle_feminine_plural",
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
    "PR40-P036-P001-S004": (
        "La fuente impresa contiene la errata «Babilona»; se conserva en el inventario "
        "documental, pero no se usa para evaluar al concursante."
    ),
    "PR40-P037-P004-S002": (
        "Lista aislada de referencias bíblicas sin proposición evaluable: "
        "Proverbios 14:34; 16:12; 20:28."
    ),
    "PR43-P051-P001-S004": (
        "Lista aislada de referencias bíblicas sin proposición evaluable: "
        "Isaías 13:11, 19-22; 14:23."
    ),
    "PR43-P050-P006-S004": (
        "Lista aislada de referencias bíblicas sin proposición evaluable: "
        "Jeremías 51:41; 50:23, 46; 51:8, 56, 57; 50:24, 25, 33, 34."
    ),
    "PR43-P052-P004-S005": (
        "Referencia bíblica aislada sin proposición evaluable: Ezequiel 1:4, 26; 10:8."
    ),
    "PR44-P058-P003-S006": (
        "Referencia bíblica aislada sin proposición evaluable: Daniel 12:4, 9, 13."
    ),
}
SAFE_EXACT_NEGATION_ACTION_FORMS = {
    form
    for form in SAFE_FALSE_ACTION_FORMS
    if form not in {"imperative", "infinitive", "gerund"}
    and not form.startswith("participle_")
} | {
    "present_plural",
    "present_second_singular",
}
EDITORIALLY_EXCLUDED_CANDIDATES = {
    "DAN9-V003": {"asperas"},
    "DAN2-V004": {"cuenta"},
    "DAN7-V025": {"medio"},
    # Es un componente interno de «dos mil trescientas»; aislado como término
    # crea una pregunta categorialmente incorrecta.
    "DAN8-V014": {"trescientas"},
    # La respuesta predicativa larga no tiene tres alternativas fuente de
    # extensión y sintaxis comparables; mantenerla delataría la opción.
    "DAN7-V026": {"destruido y arruinado hasta el fin"},
    # La frase predicativa es mucho más larga que todas las alternativas
    # fuente disponibles y convertiría la longitud en pista de respuesta.
    "PR41-P041-P006-S004": {"libres para elegir a quien quieren servir"},
    # «Sin embargo» es una locución fija; ocultar solo «embargo» produce
    # distractores nominales que delatan la respuesta.
    "PR39-P028-P007-S002": {"embargo"},
    # La mayúscula editorial de «Fuente» comparte sufijo con adjetivos en
    # -ente; sin un pool nominal estable la opción resulta delatora.
    "PR40-P034-P002-S003": {"fuente"},
    # Estos sustantivos comparten terminaciones productivas con verbos o
    # adjetivos y no conservan tres distractores nominales inequívocos.
    "PR42-P043-P004-S005": {"carne"},
    "PR42-P043-P002-S005": {"gobernante"},
    "PR42-P046-P001-S004": {"sentido"},
    "PR39-P030-P002-S002": {"santo"},
    "PR40-P033-P006-S002": {"sentencia"},
    # No existen tres distractores de la misma ranura y morfología para
    # «púrpura»; conservarla produciría opciones gramaticalmente delatoras.
    "PR43-P048-P004-S005": {"purpura"},
    "PR43-P052-P006-S003": {"comete"},
    # La relación Daniel–Apocalipsis permanece explícita en otras variantes
    # de esta misma unidad; «Apocalipsis» aislado no tiene tres opciones de
    # igual morfología y contexto sintáctico.
    "PR44-P059-P001-S001": {"apocalipsis"},
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
    "PR40-P036-P005-S003": "vuestra vida",
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
    "DAN2-V004": [("Cuenta", "action")],
    "DAN6-V001": [("ciento veinte", "number")],
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
    "PR44-P055-P001-S002": [("ciento veinte", "number")],
}
STOP_ANSWERS = {
    "alguno", "aquella", "aquello", "aquellos", "ellos", "estas", "estos", "mismo",
    "misma", "otros", "porque", "sobre", "todas", "todos", "cuando", "donde",
    "asi", "ahora", "luego", "despues", "tambien", "solo", "aqui", "debajo",
    "ciertamente", "dondequiera", "pues", "todavia",
    "eres", "es", "era", "eran", "estaba", "estaban", "estuve", "estuvo",
    "ser", "sido", "sea", "sean", "sera", "seran", "fue", "fueron", "habia",
    "hay", "hoy", "ayer", "manana", "cuan", "cuanto", "como", "derribad", "cortad", "trajeran",
    "levantate", "ocurrir", "sabes", "asimismo", "cualquiera", "tanto",
    "dijo", "dije", "dijeron", "decia", "dio", "habia", "habian",
    "hizo", "hicieron", "vio", "vino",
    "rey demanda es dificil", "cosa semejante a ningun",
    "tiempo algunos hombres caldeos", "dioses ni tampoco adoraremos",
    "rey confirmare pueda mudarse", "a los israelitas moises", "nadie", "quien", "quienes",
}
DIVINE_NAMES = {
    "altisimo", "anciano", "creador", "cristo", "dios", "eterno", "huesped",
    "invisible", "juez", "maestro", "jehova", "mesias", "omnipotente", "principe",
    "redentor", "revelador", "salvador", "santo", "senor",
    "todopoderoso", "vigilante",
}

EXTRA_PERSON_NAMES = {
    "abednego", "aspenaz", "belsasar", "ezequiel", "jacob", "jeremias", "moises", "pablo",
    "satanas", "samuel", "sadrach", "mesach", "israel",
}

EXTRA_PLACE_NAMES = {
    "atenas", "babilonia", "dura", "edom", "eufrates", "jerusalen", "jerusalem",
    "medo persia", "sesach", "sinar", "ufaz",
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
    "ciertamente", "dondequiera", "entonces", "pronto", "adelante", "delante", "encima", "junto",
    "hoy", "ayer", "manana", "cuan", "cuanto", "como", "ademas", "alli",
    "siquiera", "nunca", "antes", "sobremanera", "juntos", "conforme",
}
NON_VERB_IA = {
    "abundancia", "angustia", "apariencia", "bestia", "ciencia", "clemencia",
    "complacencia", "conciencia", "diligencia", "dinastia", "dia", "existencia",
    "frecuencia", "furia", "gloria", "gracia", "historia", "influencia",
    "insolencia", "inteligencia", "justicia", "limpia", "magnificencia",
    "misericordia", "obediencia", "postrimeria", "potencia", "presencia",
    "profecia", "providencia", "provincia", "sabiduria", "sentencia", "todavia",
    "victoria", "vigilancia",
    "armonia", "idolatria", "mayoria", "mia", "orgia", "osadia", "simpatia", "vigia",
}
DIRECTION_FORMS = {
    "norte", "sur", "oriente", "poniente", "este", "oeste",
    "septentrion", "mediodia",
}
NON_VERB_FORMS = NON_VERB_IA | {
    "alegria", "aparte", "carrera", "citara", "collar", "cuenta", "cuernos", "firme", "fuerte",
    "ira", "lugar", "manjar", "mar", "mujer", "altar", "poder", "primer",
    "tercer", "caracter", "bienestar", "singular", "mayordomia", "muerte",
    "parte", "suerte", "supremacia", "triste", "viviente", "concerniente", "varon", "lomos", "joven",
    "hogar", "tuya", "tuyo", "tuyos", "tuyas",
    "capacitado", "capacitada", "capacitados", "capacitadas",
    "desmoralizador", "desmoralizadora", "desmoralizadores", "desmoralizadoras",
    "nutrido", "nutrida", "nutridos", "nutridas", "pequeno", "pequena", "pequenos", "pequenas",
    "importante", "importantes", "audaz", "audaces", "controlado", "controlada", "controlados", "controladas",
    "espiritual", "espirituales", "majestuoso", "majestuosa", "majestuosos", "majestuosas",
    "enhiesto", "enhiesta", "enhiestos", "enhiestas",
    "parecer",
}
INVARIANT_ADJECTIVE_FORMS = {
    "dificil", "fragil", "fuerte", "grande", "imposible", "inferior",
    "mayor", "mejor", "menor", "notable", "principal", "semejante", "singular",
    "terrible", "valiente",
}

EXPLICIT_ADJECTIVE_FORMS = {
    "primer", "primero", "primera", "segundo", "segunda", "tercer", "tercero",
    "tercera", "ultimo", "ultima", "rapido", "rapida", "correcto", "correcta",
    "idolatra", "terrenal", "mundanal", "mental", "especial", "robusto", "ulterior",
    "bueno", "buena", "confuso", "confusa", "santo", "santa", "seguro", "segura",
    "justo", "justa", "digno", "digna", "ancho", "ancha", "limpio", "limpia",
    "alto", "alta", "halagueno", "halaguena", "seductor", "seductora", "patriota",
    "atonito", "atonita", "verdadero", "verdadera", "perpetuo", "perpetua",
    "potente", "potentes", "musical", "musicales", "muerto", "muerta",
    "tuya", "tuyo", "tuyos", "tuyas",
    "capacitado", "capacitada", "capacitados", "capacitadas",
    "desmoralizador", "desmoralizadora", "desmoralizadores", "desmoralizadoras",
    "nutrido", "nutrida", "nutridos", "nutridas", "pequeno", "pequena", "pequenos", "pequenas",
    "importante", "importantes", "audaz", "audaces", "controlado", "controlada", "controlados", "controladas",
    "espiritual", "espirituales", "majestuoso", "majestuosa", "majestuosos", "majestuosas",
    "enhiesto", "enhiesta", "enhiestos", "enhiestas",
    "profundo", "profunda", "profundos", "profundas", "flagrante", "flagrantes",
    "fiel", "fieles", "libre", "libres", "firme",
    "mundanal", "mundanales", "cansador", "cansadora", "cansadores", "cansadoras",
    "gigantesco", "gigantesca", "grandioso", "grandiosa", "anterior", "anteriores",
    "restituido", "restituida", "restituidos", "restituidas",
}
EXPLICIT_NOMINAL_FORMS = {
    "manera",
}

FUNCTION_WORDS = {
    "a", "al", "ante", "como", "con", "contra", "de", "del", "desde",
    "durante", "el", "en", "entre", "hacia", "hasta", "la", "las", "los",
    "para", "por", "segun", "sin", "sobre", "tras", "un", "una", "y",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas", "mi",
    "mis", "tu", "tus", "nuestro", "nuestra", "nuestros", "nuestras",
    "vuestro", "vuestra", "vuestros", "vuestras", "su", "sus",
    "mediante", "entonces",
    "yo", "el", "ella", "ellos", "ellas", "nosotros", "vosotros", "usted",
    "ustedes", "me", "te", "se", "nos", "os", "le", "les", "lo", "la",
    "mucho", "mucha", "muchos", "muchas", "poco", "poca", "pocos", "pocas",
    "gran", "grandes", "varios",
    "varias", "cierto", "cierta", "ciertos", "ciertas", "todo", "toda",
    "todos", "todas", "otro", "otra", "otros", "otras",
    "cuyo", "cuya", "cuyos", "cuyas", "aquel", "aquella", "aquellos",
    "aquellas", "alguno", "alguna", "algunos", "algunas", "unos", "unas",
    "ningun", "ninguno", "ninguna", "ningunos", "ningunas",
    "quien", "quienes", "cual", "cuales",
}
VERB_FORMS = {
    "dijo", "respondio", "hablo", "vino", "fue", "hizo", "vio", "miraba", "doy",
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
    "perdonar", "reemplazar", "sintiera", "puede", "pueden", "dalos", "propuso", "quiso",
    "ha", "has", "han", "he", "hemos", "habeis",
    "dicho", "hecho", "puesto", "visto",
    "esfuerzate", "haz", "hazlo", "cierra", "inclina", "presta",
    "entiende", "reprende", "lleva", "desataronse", "sirves", "mandandolo",
    "libra", "perece", "declarame", "destruidlo", "engrandezco", "dispersad",
    "tiene", "triunfe", "gobierna", "demanda", "resulta", "pudiera", "debiera",
    "encuentra", "salva", "acata", "respeta", "confirme", "revela",
    "buscandolo", "guardan", "trayendo", "entendido", "apartese", "rodean",
    "resplandezca", "huyeron", "opuso", "cobra", "tengo", "confieso", "pusolo", "alabo",
    "devora", "ensena", "guarda", "adore",
    "dispuso", "libertandolos", "aprueba", "juntaronse", "perturbose",
}


def _norm(value: str) -> str:
    # Sustituir la puntuación por espacios antes de retirar diacríticos evita
    # fusionar palabras separadas por rayas tipográficas («contemplar—un»).
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


_SEMANTIC_OPTION_ALIASES = {
    "jerusalem": "jerusalen",
    "abed nego": "abednego",
    "mesach": "mesac",
    "sadrach": "sadrac",
}


def semantic_option_key(value: str) -> str:
    """Agrupa variantes que nombran la misma entidad bíblica."""
    normalized = _norm(value)
    return _SEMANTIC_OPTION_ALIASES.get(normalized, normalized)


def semantic_option_collision_count(questions: list[dict[str, Any]]) -> int:
    return sum(
        len({semantic_option_key(str(option)) for option in question["options"]})
        != len(question["options"])
        for question in questions
    )


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _word_role(word: str) -> str:
    normalized = _norm(word)
    normalized_singular = normalized[:-1] if normalized.endswith("s") else normalized
    if normalized in ADVERB_FORMS or (
        normalized.endswith("mente") and normalized != "mente"
    ):
        return "adverb"
    if normalized in NUMBER_WORDS or normalized.isdigit():
        return "number"
    if normalized in NON_VERB_FORMS or normalized_singular in NON_VERB_FORMS:
        return "content"
    if normalized.endswith(
        ("ancia", "encia", "ismo", "miento", "sion", "cion", "tad", "dad", "ura", "eza")
    ):
        return "content"
    if re.search(r"(?:rá|rás|rán|ré|réis|remos|áis|éis|ó|é|í)(?:se)?$|(?:aremos|eremos|iremos)$", word.lower()):
        return "verb"
    if re.search(r"(?:ía|ían)$", word.lower()) and normalized not in NON_VERB_IA:
        return "verb"
    if normalized in VERB_FORMS or re.search(
        r"(?:ando|iendo|andose|iendose|aron|ieron|aste|iste|aba|aban|ara|ira|ase|iese|aran|ieran|asen|iesen|esen|eran|iran|(?:ar|er|ir)(?:me|te|se|lo|la|los|las|le|les|nos)?)$",
        normalized,
    ):
        return "verb"
    if normalized.endswith("mos") and normalized not in {"ultimos", "ramos", "blasfemos"}:
        return "verb"
    if (normalized in FUNCTION_WORDS or normalized in STOPWORDS) and word.lower() != "hacía":
        return "function"
    return "content"


def _term_word_class(word: str) -> str:
    """Distinguish high-confidence adjective forms from nominal terms."""
    normalized = _norm(word)
    singular = normalized[:-1] if normalized.endswith("s") else normalized
    if normalized in EXPLICIT_NOMINAL_FORMS:
        return "nominal"
    if normalized in INVARIANT_ADJECTIVE_FORMS or normalized in EXPLICIT_ADJECTIVE_FORMS or singular in {
        "cabrio",
        "vano",
        "vana",
        "verdadero",
        "verdadera",
        "venidero",
        "venidera",
    } or singular.endswith(
        (
            "ico",
            "ica",
            "ivo",
            "iva",
            "oso",
            "osa",
            "ano",
            "ana",
            "ero",
            "era",
            "able",
            "ible",
        )
    ):
        return "adjective"
    return "nominal"


def _contextual_word_role(text: str, start: int, end: int) -> str:
    """Refine ambiguous present-tense forms using their local syntax."""
    word = text[start:end]
    normalized_word = _norm(word)
    if word == "Cuenta" and _is_sentence_initial(text, start):
        return "verb"
    if word[:1].isupper() and not _is_sentence_initial(text, start):
        return "content"
    if (
        word[:1].isupper()
        and _is_sentence_initial(text, start)
        and re.match(r"\s*[,;]", text[end:])
        and _action_form(word) == "infinitive"
    ):
        return "content"
    if normalized_word in NON_VERB_FORMS:
        return "content"
    if normalized_word.endswith(
        ("ancia", "encia", "ismo", "miento", "sion", "cion", "tad", "dad", "ura", "eza")
    ):
        return "content"
    previous_tokens = list(TOKEN_RE.finditer(text[:start]))
    previous = previous_tokens[-1].group() if previous_tokens else ""
    previous_separator = (
        text[previous_tokens[-1].end():start] if previous_tokens else ""
    )
    following_match = TOKEN_RE.search(text, end)
    following = following_match.group() if following_match else ""
    following_separator = (
        text[end:following_match.start()] if following_match else text[end:]
    )
    previous_norm = _norm(previous)
    previous_previous_norm = (
        _norm(previous_tokens[-2].group()) if len(previous_tokens) > 1 else ""
    )
    following_norm = _norm(following)
    role = _word_role(word)
    ambiguous_determiners = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus",
        "este", "esta", "estos", "estas", "aquel", "aquella", "aquellos", "aquellas",
        "poco", "poca", "pocos", "pocas",
        "mi", "mis", "tu", "tus", "nuestro", "nuestra", "nuestros", "nuestras",
        "vuestro", "vuestra", "vuestros", "vuestras",
    }
    plural_determiners = {
        "los", "las", "unos", "unas", "sus", "estos", "estas", "aquellos", "aquellas",
        "pocos", "pocas",
    }
    noun_followers = {
        "de", "del", "en", "que", "es", "era", "eran", "sera", "seran", "fue", "fueron", "y", "o",
    }
    previous_is_determiner = (
        previous.lower() != "él" and previous_norm in ambiguous_determiners
    )
    if previous_is_determiner and role == "content":
        return "content"
    if (
        previous_norm in ambiguous_determiners
        and normalized_word in {"primera", "prueba", "vida"}
    ) or (
        previous_norm in {"buen", "mal"}
        and normalized_word == "parecer"
    ):
        return "content"
    if previous_is_determiner and role == "content" and (
        following_norm in noun_followers
        or previous_previous_norm in {
            "a", "al", "ante", "con", "contra", "de", "del", "desde", "en",
            "entre", "hacia", "hasta", "para", "por", "sin", "sobre", "tras",
        }
        or (
            previous_norm in plural_determiners
            and normalized_word.endswith("s")
            and bool(re.search(r"[,.;:!?»”\"]", following_separator))
        )
        or (
            not following_norm
            and previous_norm in plural_determiners
            and normalized_word.endswith("s")
        )
    ):
        return "content"
    if (
        previous_norm in {"ha", "has", "han", "he", "hemos", "habia", "habian"}
        and _action_form(word).startswith("participle_")
    ):
        return "verb"
    if role != "content" or not re.search(r"(?:a|e|an|en|as|es)$", word.lower()):
        return role
    subject_or_link = {
        "yo", "tu", "el", "ella", "ellos", "ellas", "nosotros", "vosotros",
        "usted", "ustedes", "que", "quien", "quienes", "se", "me", "te",
        "le", "les", "lo", "la", "los", "las", "no", "ni", "segun",
        "ha", "has", "han", "he", "hemos", "habia", "habian",
    }
    direct_object_lead = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "su", "sus",
    }
    contextual_plural_verb = (
        role == "content"
        and normalized_word.endswith(("an", "en"))
        and previous_norm
        and previous_norm not in FUNCTION_WORDS
        and previous_norm not in STOPWORDS
        and following_norm in (
            direct_object_lead
            | {"a", "al", "de", "del", "en", "con", "por", "para", "que", "y", "o"}
        )
    )
    coordinated_verb = previous_norm in {"y", "o"} and following_norm in direct_object_lead
    proper_subject = (
        bool(previous[:1].isupper())
        and previous_separator.isspace()
        and previous_norm not in FUNCTION_WORDS
        and previous_norm not in STOPWORDS
        and following_norm in (
            direct_object_lead | {"a", "al", "de", "del", "en", "con", "por", "para", "que", "y", "o"}
        )
    )
    vocative_subject = (
        bool(previous[:1].isupper())
        and bool(re.fullmatch(r"\s*,\s*", previous_separator))
        and following_norm in direct_object_lead
    )
    predicate_before_copula = (
        following_norm in {"es", "era", "sera", "seria"}
        and previous_norm not in ambiguous_determiners
        and previous_norm not in FUNCTION_WORDS
        and previous_norm not in STOPWORDS
    )
    if previous_norm in subject_or_link or coordinated_verb or proper_subject or vocative_subject or predicate_before_copula or contextual_plural_verb:
        return "verb"
    return role


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
        singular = normalized[:-1] if normalized.endswith("s") else normalized
        role = _word_role(words[0])
        if role == "verb":
            suffix = f"verb_like:{_action_form(words[0])}"
        elif role == "adverb":
            suffix = "adverb"
        elif normalized in {"primer", "tercer"}:
            suffix = "ordinal_apocopated_masculine_singular"
        elif normalized in {"primero", "tercero"}:
            suffix = "ordinal_full_apocopatable_masculine_singular"
        elif normalized in EXPLICIT_ADJECTIVE_FORMS or singular in EXPLICIT_ADJECTIVE_FORMS:
            ending = (
                "feminine_plural" if normalized.endswith("as")
                else "masculine_plural" if normalized.endswith("os")
                else "feminine_singular" if normalized.endswith("a")
                else "masculine_singular"
            )
            suffix = f"adjective_explicit:{ending}"
        elif normalized in INVARIANT_ADJECTIVE_FORMS or singular in INVARIANT_ADJECTIVE_FORMS or normalized.endswith(("ble", "il")):
            suffix = "adjective_invariant"
        elif normalized.endswith(("ivo", "iva", "ivos", "ivas")):
            suffix = f"adjective_ive:{next(ending for ending in ('ivos', 'ivas', 'ivo', 'iva') if normalized.endswith(ending))}"
        elif normalized.endswith(("oso", "osa", "osos", "osas")):
            suffix = f"adjective_ose:{next(ending for ending in ('osos', 'osas', 'oso', 'osa') if normalized.endswith(ending))}"
        elif normalized.endswith(("ante", "ente")):
            suffix = "adjective_agent"
        elif normalized.endswith(("ados", "idos")):
            suffix = "masculine_participle_plural"
        elif normalized.endswith(("adas", "idas")):
            suffix = "feminine_participle_plural"
        elif normalized.endswith(("antes", "entes")):
            suffix = "agent_plural"
        elif normalized.endswith(("amiento", "imiento")):
            suffix = "deverbal_noun_miento"
        elif normalized.endswith(("ada", "ida")):
            suffix = "feminine_participle_singular"
        elif normalized.endswith(("ado", "ido")):
            suffix = "participle_or_deverbal_noun"
        elif normalized.endswith(("anza", "encia", "ancia")):
            suffix = "abstract_noun_a"
        elif normalized.endswith(("ura", "eza")):
            suffix = "quality_noun_a"
        elif normalized.endswith("ismo"):
            suffix = "doctrine_or_system_noun"
        elif normalized.endswith("os"):
            suffix = "masculine_plural"
        elif normalized.endswith("as"):
            suffix = "feminine_plural"
        elif normalized.endswith("es"):
            suffix = "e_or_consonant_plural"
        elif normalized.endswith(("cion", "sion", "dad", "tad")):
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
        "eres": "present_second_singular", "es": "present_e", "soy": "present_other", "son": "present_plural",
        "esta": "present_a", "estan": "present_plural", "tiene": "present_e", "tienen": "present_plural",
        "sabes": "present_other", "tuvo": "preterite_singular", "dijo": "preterite_singular", "dije": "preterite_first_singular",
        "hizo": "preterite_singular", "vino": "preterite_singular", "puso": "preterite_singular",
        "dio": "preterite_singular", "bendijo": "preterite_singular",
        "trajo": "preterite_singular", "trajeron": "preterite_plural",
        "fue": "preterite_singular", "fueron": "preterite_plural",
        "ore": "preterite_first_singular", "mire": "preterite_first_singular",
        "postre": "preterite_first_singular", "recobre": "preterite_first_singular",
        "dicho": "participle_masculine_singular",
        "hecho": "participle_masculine_singular",
        "puesto": "participle_masculine_singular",
        "visto": "participle_masculine_singular",
        "decidme": "imperative", "contadme": "imperative",
        "compara": "imperative",
        "hareis": "future_second_plural",
        "podeis": "present_second_plural", "poneis": "present_second_plural",
        "propuso": "preterite_singular",
        "haz": "imperative", "hazlo": "imperative",
        "quiso": "preterite_singular",
        "hemos": "present_first_plural",
        "detenga": "subjunctive_present_singular",
        "palidezca": "subjunctive_present_singular",
        "confirme": "subjunctive_present_singular",
        "triunfe": "subjunctive_present_singular",
        "trajera": "subjunctive_past_singular",
        "resplandezca": "subjunctive_present_singular",
        "opuso": "preterite_singular", "pusolo": "preterite_singular",
        "huyeron": "preterite_plural", "tengo": "present_first_singular",
        "confieso": "present_first_singular", "alabo": "present_first_singular",
        "dalos": "imperative", "destruidlo": "imperative",
        "tuve": "preterite_first_singular",
        "dispuso": "preterite_singular", "juntaronse": "preterite_plural",
        "perturbose": "preterite_singular",
    }
    if lower in irregular:
        return irregular[lower]
    for pattern, label in (
        (r"(?:réis)$", "future_second_plural"),
        (r"(?:rás)$", "future_second_singular"),
        (r"(?:rán|remos)$", "future_plural"),
        (r"(?:rá|ré)$", "future_singular"),
        (r"(?:aron|ieron)$", "preterite_plural"),
        (r"(?:aste|iste)$", "preterite_second_singular"),
        (r"(?:ó)$", "preterite_singular"),
        (r"(?:é|í)$", "preterite_first_singular"),
        (r"(?:rían)$", "conditional_plural"),
        (r"(?:ría)$", "conditional_singular"),
        (r"(?:aban|ían)$", "imperfect_plural"),
        (r"(?:aba|ía)$", "imperfect_singular"),
        (r"(?:ieren)$", "future_subjunctive_plural"),
        (r"(?:iere)$", "future_subjunctive_singular"),
        (r"(?:aran|ieran|yeran|asen|iesen|esen)$", "subjunctive_past_plural"),
        (r"(?:ara|iera|yera|ase|iese|ese)$", "subjunctive_past_singular"),
    ):
        if re.search(pattern, raw):
            return label
    if re.search(
        r"(?:ando|iendo|yendo)(?:me|te|se|lo|la|los|las|le|les|nos)?$",
        lower,
    ):
        return "gerund"
    if re.search(r"(?:ar|er|ir)(?:me|te|se|lo|la|los|las|le|les|nos)?$", lower):
        return "infinitive"
    if re.search(r"(?:ad|ed|id|ate|ete|ite)$", lower):
        return "imperative"
    if re.search(r"(?:ados|idos)$", lower):
        return "participle_masculine_plural"
    if re.search(r"(?:adas|idas)$", lower):
        return "participle_feminine_plural"
    if re.search(r"(?:ado|ido)$", lower):
        return "participle_masculine_singular"
    if re.search(r"(?:ada|ida)$", lower):
        return "participle_feminine_singular"
    if lower.endswith(("an", "en")):
        return "present_plural"
    if lower.endswith(("ais", "eis")):
        return "present_second_plural"
    if lower.endswith("mos"):
        return "present_first_plural"
    if lower.endswith(("as", "es")):
        return "present_second_singular"
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
    prefix = text[:start].rstrip().rstrip('«»“”\"\'')
    return not prefix or prefix[-1] in ".!?¡¿"


def _broad_category(answer: str, raw_category: str, unit: dict[str, Any]) -> str:
    normalized_answer = _norm(answer)
    if (
        normalized_answer in DIVINE_NAMES and answer[:1].isupper()
    ) or normalized_answer in EXTRA_PERSON_NAMES:
        return "person"
    if normalized_answer in EXTRA_PLACE_NAMES:
        return "place"
    if normalized_answer in NON_VERB_FORMS:
        return "term"
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


def _is_compound_number_component(text: str, start: int, end: int) -> bool:
    def is_number_word(value: str) -> bool:
        normalized = _norm(value)
        return (
            normalized in NUMBER_WORDS
            or normalized.isdigit()
            or bool(
                re.fullmatch(
                    r"(?:dos|tres|cuatro|seis|sete|ocho|nove)cientos|quinientos",
                    normalized,
                )
            )
        )

    previous_tokens = list(TOKEN_RE.finditer(text[:start]))
    previous = previous_tokens[-1] if previous_tokens else None
    following_tokens = list(TOKEN_RE.finditer(text, end))
    following = following_tokens[0] if following_tokens else None
    previous_is_number = bool(
        previous
        and text[previous.end():start].isspace()
        and is_number_word(previous.group())
    )
    following_is_number = bool(
        following
        and text[end:following.start()].isspace()
        and is_number_word(following.group())
    )
    if previous and _norm(previous.group()) == "y" and len(previous_tokens) >= 2:
        before_y = previous_tokens[-2]
        previous_is_number = bool(
            text[before_y.end():previous.start()].isspace()
            and text[previous.end():start].isspace()
            and is_number_word(before_y.group())
        )
    if following and _norm(following.group()) == "y" and len(following_tokens) >= 2:
        after_y = following_tokens[1]
        following_is_number = bool(
            text[end:following.start()].isspace()
            and text[following.end():after_y.start()].isspace()
            and is_number_word(after_y.group())
        )
    return previous_is_number or following_is_number


def _number_answer_is_compound_component(fact: dict[str, Any]) -> bool:
    if fact.get("category") != "number" or len(str(fact.get("answer", "")).split()) != 1:
        return False
    context = str(fact.get("context") or "")
    answer = str(fact["answer"])
    if context.count(answer) != 1:
        return False
    start = context.index(answer)
    return _is_compound_number_component(context, start, start + len(answer))


def _is_bible_reference_number(text: str, start: int, end: int) -> bool:
    """Return whether a digit belongs to a written Bible citation."""
    if not text[start:end].isdigit():
        return False
    citation = re.compile(
        r"(?:[1-3]\s+)?[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"
        r"(?:\s+[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+){0,2}"
        r"\s+\d{1,3}:\d{1,3}"
        r"(?:(?:\s*[-,;]\s*)\d{1,3}(?::\d{1,3})?)*"
    )
    return any(
        match.start() <= start < end <= match.end()
        for match in citation.finditer(text)
    )


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
        role = _contextual_word_role(text, token.start(), token.end())
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
        roles = (
            [_contextual_word_role(text, start, end)]
            if len(words) == 1
            else [_word_role(word) for word in words]
        )
        broad_category = _broad_category(answer, raw_category, unit)
        # La sintaxis local tiene la última palabra para formas homógrafas:
        # «Cuenta el sueño» es verbo, aunque «cuenta» también sea sustantivo.
        if (
            len(words) == 1
            and roles[0] == "verb"
            and broad_category not in {"person", "place"}
        ):
            broad_category = "action"
        is_reference_number = bool(
            re.fullmatch(r"\d+(?:-\d+)+", answer)
            or (
                answer.isdigit()
                and (
                re.search(r"(?:Vers?|Caps?|Págs?|Núm)\.\s*$", text[max(0, start - 12):start], re.IGNORECASE)
                or _is_bible_reference_number(text, start, end)
                )
            )
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
            or (
                broad_category == "number"
                and len(words) == 1
                and _is_compound_number_component(text, start, end)
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
    granular = re.split(r"\s*;\s*", text)
    # Un colon puede separar dos proposiciones extensas, pero también introduce
    # una cita («Las palabras: …»). Solo se ofrece como corte cuando el ancla
    # anterior ya aporta contexto semántico suficiente por sí sola.
    for match in re.finditer(
        r":\s+(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ«“¿¡])",
        text,
    ):
        prefix = text[: match.start()].strip()
        suffix = text[match.end() :].strip()
        if len(prefix.split()) >= 4:
            granular.extend((prefix, suffix))
    containing = [
        clause.strip()
        for clause in [*clauses, *granular]
        if answer in clause and len(clause.split()) >= 7
    ]
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
    term_word_class = _term_word_class(answer)
    morphology = repr(option_signature(answer, "term"))

    def slot(label: str) -> str:
        return f"{label}:{morphology}"

    if answer_role == "adverb":
        return slot("term:adverb")
    if answer_role == "verb":
        return slot(f"term:verb_like:{_action_form(answer)}")
    copulas = {"es", "era", "eran", "sera", "seran", "fue", "fueron"}
    if term_word_class == "adjective" and (
        previous in copulas
        or (
            following in copulas
            and (not previous_raw or _word_role(previous_raw) != "content")
        )
    ):
        return slot("term:predicate_adjective")
    if (
        term_word_class == "adjective"
        and previous_raw
        and _word_role(previous_raw) == "content"
    ):
        return slot(f"term:postnominal_adjective:{following}")
    determiner_shape = {
        "el": "masculine_singular", "un": "masculine_singular",
        "este": "masculine_singular", "aquel": "masculine_singular",
        "la": "feminine_singular", "una": "feminine_singular",
        "esta": "feminine_singular", "aquella": "feminine_singular",
        "los": "masculine_plural", "unos": "masculine_plural",
        "estos": "masculine_plural", "aquellos": "masculine_plural",
        "las": "feminine_plural", "unas": "feminine_plural",
        "estas": "feminine_plural", "aquellas": "feminine_plural",
        "su": "possessive_singular", "sus": "possessive_plural",
    }.get(previous)
    if determiner_shape:
        return slot(f"term:determined_nominal:{determiner_shape}")
    if previous and _word_role(previous_raw) == "number":
        return slot("term:counted_nominal")
    if previous in {"a", "al", "ante", "con", "contra", "de", "del", "desde", "en", "entre", "hacia", "hasta", "para", "por", "sin", "sobre", "tras"}:
        return slot(f"term:prepositional:{previous}")
    if previous and _word_role(previous_raw) == "content" and (
        following in {"que", "y", "o"}
        or following in {"es", "era", "eran", "sera", "seran", "fue", "fueron"}
        or (following and _word_role(following_raw) == "verb")
        or after.lstrip().startswith((",", ";", ".", ":"))
    ):
        if term_word_class == "adjective":
            return slot(f"term:postnominal_adjective:{following}")
        return slot(f"term:postnominal_modifier:{following}")
    if following in {"de", "del"}:
        return slot("term:nominal_head")
    if before.rstrip().endswith((",", ";", ":", "—", "–")):
        return slot("term:list_or_clause_item")
    return slot(f"term:generic_{term_word_class}")


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
            normalized_answer = _norm(answer)
            if (
                normalized_answer in STOP_ANSWERS
                or normalized_answer in STOPWORDS
                or normalized_answer in excluded_candidates
            ):
                rejected += 1
                continue
            start = text.index(answer)
            relation_category = str(relation["category"])
            contextual_role = _contextual_word_role(
                text, start, start + len(answer)
            )
            if len(answer.split()) == 1:
                if contextual_role == "verb":
                    relation_category = "action"
                elif normalized_answer in EXTRA_PERSON_NAMES:
                    relation_category = "person"
                elif normalized_answer in EXTRA_PLACE_NAMES:
                    relation_category = "place"
            editorial_candidates.append(
                {
                    "answer": answer,
                    "start": start,
                    "end": start + len(answer),
                    "grammatical_category": _relation_grammatical_category(
                        answer, relation_category
                    ),
                    "category": relation_category,
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
                        else "verb" if category == "action"
                        else "phrase_plural" if override.lower().endswith("s") else "phrase_singular"
                    ),
                    "category": category,
                    "score": 10.0,
                }
            )
        if not editorial_candidates:
            raise ValueError(f"Unidad sin hecho editorial revisado: {unit['source_unit_id']}")
        source_text = _source_text(unit)
        normalized_editorial_candidates = []
        for candidate in editorial_candidates:
            if len(candidate["answer"].split()) == 1 and candidate["category"] in {"action", "term"}:
                role = _contextual_word_role(
                    source_text, int(candidate["start"]), int(candidate["end"])
                )
                if role == "function":
                    rejected += 1
                    continue
                if role == "verb":
                    candidate["category"] = "action"
                    candidate["grammatical_category"] = "verb"
                elif candidate["category"] == "action":
                    candidate["category"] = "term"
                    candidate["grammatical_category"] = (
                        "word_plural"
                        if candidate["answer"].lower().endswith("s")
                        else "word_singular"
                    )
            if candidate["category"] == "number":
                candidate["grammatical_category"] = (
                    "number_phrase"
                    if len(candidate["answer"].split()) > 1
                    else "number"
                )
            normalized_editorial_candidates.append(candidate)
        editorial_candidates = normalized_editorial_candidates
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
        for candidate in editorial_candidates:
            candidate["_slot_signature"] = _slot_syntax(
                source_text, candidate["answer"], candidate["category"]
            )
            candidate["_normalized_source"] = _norm(source_text)
        rejected += len(candidates) - len(editorial_candidates)
        by_chapter[_chapter_key(unit)].append((unit, editorial_candidates))

    def candidate_pool_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
        category = candidate["category"]
        grammar = (
            None
            if category in {"person", "place", "phrase", "term"}
            else candidate["grammatical_category"]
        )
        return (
            category,
            ("all_terms",)
            if category == "term"
            else option_signature(candidate["answer"], category),
            grammar,
            candidate.get("_slot_signature") if category == "term" else None,
        )

    # El filtrado debe converger. Una sola pasada permite que candidatos que
    # luego son eliminados sostengan artificialmente a otros candidatos.
    while True:
        pool_candidates: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for chapter_rows in by_chapter.values():
            for _, candidates in chapter_rows:
                for candidate in candidates:
                    pool_candidates[candidate_pool_key(candidate)].append(candidate)
        removed_this_pass = 0
        for chapter, chapter_rows in list(by_chapter.items()):
            filtered_rows = []
            for unit, candidates in chapter_rows:
                competitive = [
                    candidate
                    for candidate in candidates
                    if len({
                        _norm(row["answer"])
                        for row in pool_candidates[candidate_pool_key(candidate)]
                        if _norm(row["answer"]) != _norm(candidate["answer"])
                        and _norm(row["answer"]) not in candidate["_normalized_source"]
                    }) >= 3
                ]
                removed_this_pass += len(candidates) - len(competitive)
                if not competitive:
                    raise ValueError(
                        f"Unidad sin hecho con distractores competitivos: {unit['source_unit_id']}"
                    )
                filtered_rows.append((unit, competitive))
            by_chapter[chapter] = filtered_rows
        rejected += removed_this_pass
        if removed_this_pass == 0:
            break

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
            under_global_cap = [
                row
                for row in available
                if global_answer_usage[_norm(row[0]["answer"])]
                < MAX_GLOBAL_FACTS_PER_ANSWER
            ]
            if not under_global_cap:
                return None
            under_chapter_cap = [
                row
                for row in under_global_cap
                if chapter_answer_usage[_norm(row[0]["answer"])]
                < MAX_CHAPTER_FACTS_PER_ANSWER
            ]
            if not under_chapter_cap:
                return None
            available = under_chapter_cap
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
                    "_slot_signature": candidate["_slot_signature"],
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
                        "_slot_signature": candidate["_slot_signature"],
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
            (
                ("all_terms",)
                if row["category"] == "term"
                else option_signature(row["answer"], row["category"])
            ),
            grammar,
            row.get("_slot_signature") if row["category"] == "term" else None,
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
    return re.sub(
        rf"(?<!\w){re.escape(answer)}(?!\w)",
        lambda _: marker,
        text,
        flags=re.IGNORECASE,
    )


def _display_excerpt(text: str) -> str:
    """Wrap a source excerpt once, without duplicated dialogue quotation marks."""
    excerpt = text.strip().lstrip('»”\"').strip()
    for opening, closing in (("«", "»"), ("“", "”")):
        if excerpt.startswith(opening):
            if excerpt.endswith(closing) and excerpt.count(opening) == excerpt.count(closing):
                return excerpt
            excerpt = excerpt[1:].lstrip()
        if excerpt.endswith(closing) and excerpt.count(closing) > excerpt.count(opening):
            excerpt = excerpt[:-1].rstrip()
    return f"«{excerpt}»"


def _complete_statement_text(text: str) -> str:
    # Los cortes por proposición pueden comenzar con el cierre de una cita del
    # versículo anterior. Es puntuación editorial, no parte del enunciado.
    stripped = text.strip().strip('«»“”\"').strip()
    closing_match = re.search(r"([”’\"»]+)$", stripped)
    closing = closing_match.group(1) if closing_match else ""
    core = stripped[:-len(closing)] if closing else stripped
    result = core + closing if re.search(r"[.!?]$", core) else core.rstrip(" ,;:") + "." + closing
    for opening, ending in (("«", "»"), ("“", "”")):
        difference = result.count(opening) - result.count(ending)
        if difference > 0:
            result += ending * difference
        elif difference < 0:
            for _ in range(-difference):
                result = result.replace(ending, "", 1)
    return result


def _negate_exact_action_statement(statement: str, answer: str) -> str | None:
    """Negate one finite verb without breaking adjacent Spanish clitics."""
    if _action_form(answer) not in SAFE_EXACT_NEGATION_ACTION_FORMS:
        return None
    if statement.count(answer) != 1:
        return None
    answer_start = statement.index(answer)
    if (
        _action_form(answer)
        in {"present_a", "present_e", "subjunctive_past_singular"}
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
    clitic = re.search(
        r"\b(?:(?:me|te|se|lo|la|los|las|le|les|nos|os)\s+){1,3}$",
        prefix,
        re.I,
    )
    if clitic:
        insert_at = clitic.start()
    words_before = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", statement[:insert_at])
    if words_before and _norm(words_before[-1]) in {"no", "ni", "nunca", "tampoco", "sin"}:
        return None
    normalized_before = [_norm(word) for word in words_before[-3:]]
    if normalized_before and normalized_before[-1] == "todavia":
        return None
    if any(
        word in {"es", "era", "eran", "fue", "fueron", "esta", "estaba", "estaban"}
        for word in normalized_before[-2:]
    ):
        return None
    clause_start = max(
        (statement.rfind(mark, 0, insert_at) for mark in ".;:!?"),
        default=-1,
    ) + 1
    clause_ends = [
        position
        for mark in ".;:!?"
        if (position := statement.find(mark, insert_at)) >= 0
    ]
    clause_end = min(clause_ends, default=len(statement))
    complete_clause = statement[clause_start:clause_end]
    if re.search(
        r"\b(?:no|ni|ningún|ninguna|ninguno|nadie|nunca|jamás|sin|tampoco)\b",
        complete_clause,
        re.IGNORECASE,
    ):
        return None
    negation = "No " if _is_sentence_initial(statement, insert_at) else "no "
    suffix = statement[insert_at:]
    if negation == "No " and suffix:
        suffix = suffix[:1].lower() + suffix[1:]
    return statement[:insert_at] + negation + suffix


def _negated_action_detail(statement: str, answer: str) -> str:
    """Return the exact visible negated verb phrase, including a clitic."""
    match = re.search(
        rf"\bno\s+(?:(?:me|te|se|lo|la|los|las|le|les|nos|os)\s+){{0,3}}{re.escape(answer)}\b",
        statement,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"No se encontró el detalle negado visible para {answer!r}")
    return match.group(0).lower()


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
            or semantic_option_key(row["answer"]) == semantic_option_key(fact["answer"])
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
        unique.setdefault(semantic_option_key(row["answer"]), row)
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
            and semantic_option_key(row["answer"]) != semantic_option_key(original[index])
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
    def pool_signature(fact: dict[str, Any]) -> tuple[Any, ...]:
        if fact["category"] == "term":
            return ("all_terms",)
        return option_signature(fact["answer"], fact["category"])

    for fact in facts:
        distractor_pools[(fact["category"], pool_signature(fact))].append(fact)

    def compatible_rows(fact: dict[str, Any]) -> list[dict[str, Any]]:
        rows = list(
            distractor_pools[(fact["category"], pool_signature(fact))]
        ) + list(fact.get("_support_distractors", []))
        eligible = [
            row for row in rows
            if row["fact_id"] != fact["fact_id"]
            and semantic_option_key(row["answer"]) != semantic_option_key(fact["answer"])
            and row["_normalized_answer"] not in fact["_normalized_source"]
            and (
                fact["category"] != "term"
                or row.get("_slot_signature") == fact.get("_slot_signature")
            )
            and (
                fact["category"] != "term"
                or option_signature(row["answer"], "term")
                == option_signature(fact["answer"], "term")
            )
            and (
                fact["category"] in {"person", "place", "phrase", "term"}
                or row["grammatical_category"] == fact["grammatical_category"]
            )
            and (
                fact["category"] != "action"
                or _action_form(row["answer"]) == _action_form(fact["answer"])
            )
        ]
        unique: dict[str, dict[str, Any]] = {}
        for row in eligible:
            unique.setdefault(semantic_option_key(row["answer"]), row)
        return sorted(
            unique.values(),
            key=lambda row: (
                fact["category"] == "term"
                and row.get("_slot_signature") != fact.get("_slot_signature"),
                option_signature(row["answer"], row["category"])
                != option_signature(fact["answer"], fact["category"]),
                fact["category"] == "person"
                and ((_norm(row["answer"]) in DIVINE_NAMES) != (_norm(fact["answer"]) in DIVINE_NAMES)),
                fact["category"] == "action" and _action_form(row["answer"]) != _action_form(fact["answer"]),
                row["grammatical_category"] != fact["grammatical_category"],
                abs(len(row["answer"].split()) - len(fact["answer"].split())),
                abs(len(row["answer"]) - len(fact["answer"])),
                row["chapter"] != fact["chapter"],
                _hash(f"{fact['fact_id']}:{row['fact_id']}"),
            ),
        )

    distractor_map = {fact["fact_id"]: compatible_rows(fact) for fact in facts}
    facts_by_id = {fact["fact_id"]: fact for fact in facts}
    for fact_id, replacement_ids in DISTRACTOR_FACT_ID_OVERRIDES.items():
        if fact_id not in facts_by_id:
            raise ValueError(f"Override editorial sin hecho objetivo: {fact_id}")
        missing = [candidate_id for candidate_id in replacement_ids if candidate_id not in facts_by_id]
        if missing:
            raise ValueError(f"Override editorial {fact_id} apunta a hechos ausentes: {missing}")
        distractor_map[fact_id] = [facts_by_id[candidate_id] for candidate_id in replacement_ids]
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
        answer_start = fact["context"].find(fact["answer"])
        fused_article = bool(
            fact["category"] in {"person", "place"}
            and answer_start >= 0
            and re.search(r"\b(?:al|del)\s+$", fact["context"][:answer_start], re.I)
        )
        return [
            row
            for row in strict_false_distractor_map[fact["fact_id"]]
            if not _boundary_collision(fact["context"], fact["answer"], row["answer"])
            and not fused_article
            and (
                fact["category"] != "action"
                or (
                    fact["grammatical_category"] == "verb"
                    and row["grammatical_category"] == "verb"
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
        # becoming absurd. Phrase and term facts stay as exact, complete true
        # statements; closed semantic categories supply the false half.
        return (
            fact["category"] in {"person", "place", "number", "action"}
            and (
                fact["category"] != "action"
                or fact["grammatical_category"] == "verb"
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
    def true_statement_options(
        fact: dict[str, Any], *, include_contextual_identity: bool = True
    ) -> list[str]:
        rows = []
        for source_text in (fact["context"], fact["source_quote"]):
            if source_text.count(fact["answer"]) != 1:
                continue
            completed = _complete_statement_text(source_text)
            if completed.lstrip().startswith("¿") or completed.rstrip("»”\"").endswith("?"):
                continue
            if len(completed) > 500:
                continue
            if completed not in rows:
                rows.append(completed)
        if include_contextual_identity:
            identity, _, _ = render_contextual_identity(fact)
            rows.append(identity)
        return rows

    def can_use_exact_false_statement(fact: dict[str, Any]) -> bool:
        if not true_statement_options(fact, include_contextual_identity=False):
            return False
        return bool(false_replacements(fact))

    facts_by_id = {fact["fact_id"]: fact for fact in safe_false_candidates}
    statement_owner: dict[tuple[str, str], str] = {}
    statement_by_fact: dict[str, str] = {}

    def assign_unique_statement(
        fact: dict[str, Any],
        seen: set[tuple[str, str]],
        *,
        include_contextual_identity: bool,
    ) -> bool:
        for statement_text in true_statement_options(
            fact, include_contextual_identity=include_contextual_identity
        ):
            key = (fact["reference"], statement_text)
            if key in seen:
                continue
            seen.add(key)
            previous_id = statement_owner.get(key)
            if previous_id is None or assign_unique_statement(
                facts_by_id[previous_id],
                seen,
                include_contextual_identity=include_contextual_identity,
            ):
                statement_owner[key] = fact["fact_id"]
                statement_by_fact[fact["fact_id"]] = statement_text
                return True
        return False

    # Maximizar primero afirmaciones completas. La versión anterior detenía
    # el emparejamiento al llegar a 1,500 hechos y aceptaba presencia léxica
    # demasiado pronto, aunque quedaran cláusulas literales únicas disponibles.
    for fact in safe_false_candidates:
        assign_unique_statement(fact, set(), include_contextual_identity=False)

    exact_false_ready = sum(
        can_use_exact_false_statement(facts_by_id[fact_id])
        for fact_id in statement_by_fact
    )
    if exact_false_ready < 1500:
        for fact in sorted(
            safe_false_candidates,
            key=lambda row: (
                not can_use_exact_false_statement(row),
                _hash("atomic-true-fill:" + row["fact_id"]),
            ),
        ):
            if fact["fact_id"] in statement_by_fact:
                continue
            if not can_use_exact_false_statement(fact):
                continue
            statement_text, _, _ = render_contextual_identity(fact)
            key = (fact["reference"], statement_text)
            if key in statement_owner:
                continue
            statement_owner[key] = fact["fact_id"]
            statement_by_fact[fact["fact_id"]] = statement_text
            exact_false_ready += 1
            if exact_false_ready >= 1500:
                break

    if len(statement_by_fact) < 1500:
        for fact in safe_false_candidates:
            if fact["fact_id"] in statement_by_fact:
                continue
            assign_unique_statement(fact, set(), include_contextual_identity=True)
            if len(statement_by_fact) >= 1500:
                break
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
            key=lambda fact_id: (
                not can_use_exact_false_statement(facts_by_id[fact_id]),
                statement_by_fact[fact_id]
                == render_contextual_identity(facts_by_id[fact_id])[0],
                _hash("tf-true-selected:" + fact_id),
            ),
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
        audited_override_ids = DISTRACTOR_FACT_ID_OVERRIDES.get(fact["fact_id"])
        distractors = [
            row["answer"]
            if fact["category"] == "place"
            else _match_initial_case(row["answer"], fact["answer"])
            for row in distractor_facts[:3]
        ]
        distractor_slot_signatures = [
            row.get("_slot_signature") for row in distractor_facts[:3]
        ]
        why = {
            (
                row["answer"]
                if fact["category"] == "place"
                else _match_initial_case(row["answer"], fact["answer"])
            ):
                f"Es verdadero en {row['reference']}, pero no responde al contexto exacto de {fact['reference']}."
            for row in distractor_facts[:3]
        }
        for family_offset, family in enumerate(
            ("single_choice_direct", "fill_choice", "single_choice_contextual")
        ):
            base = _base_question(fact, family, index)
            position = (index + family_offset) % 4
            options = _arrange_options(fact["answer"], distractors, position)
            option_slot_signatures = [*distractor_slot_signatures]
            option_slot_signatures.insert(position, fact.get("_slot_signature"))
            masked_context = _masked(fact["context"], fact["answer"], "________")
            multiple_blanks = masked_context.count("________") > 1
            contextual_role = None
            context_evidence = None
            if family == "fill_choice":
                question_text = (
                    f"Complete todas las posiciones de {fact['reference']}: {_display_excerpt(masked_context)}"
                    if multiple_blanks
                    else f"Complete {fact['reference']}: {_display_excerpt(masked_context)}"
                )
                trap_type = None
            elif family == "single_choice_contextual":
                (
                    question_text,
                    contextual_role,
                    context_evidence,
                ) = render_contextual_question(fact)
                trap_type = "true_in_other_context"
            else:
                question_text = (
                    f"Según {fact['reference']}, ¿qué opción completa "
                    f"{'todas las posiciones marcadas de ' if multiple_blanks else 'correctamente '}"
                    f"{_display_excerpt(masked_context)}?"
                )
                trap_type = None
            base.update(
                {
                    "question": question_text,
                    "options": options,
                    "option_slot_signatures": option_slot_signatures,
                    "audited_distractor_fact_ids": list(audited_override_ids or ()),
                    "correct_option": position,
                    "correct_answer": fact["answer"],
                    "explanation": (
                        f"En el contexto exacto de {fact['reference']}, el detalle aplicable es «{fact['answer']}»: {_display_excerpt(fact['context'])}."
                        if family == "single_choice_contextual"
                        else f"{fact['reference']} declara literalmente {_display_excerpt(fact['context'])}. La respuesta pedida es «{fact['answer']}»."
                    ),
                    "why_distractors_fail": why,
                    "trap_type": trap_type,
                    "contextual_role": contextual_role,
                    "context_evidence": context_evidence,
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
            (
                replacement_row["answer"]
                if fact["category"] == "place"
                else _match_initial_case(replacement_row["answer"], fact["answer"])
            )
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
        identity_statement, identity_role, identity_evidence = render_contextual_identity(fact)
        if source_statement in exact_source_statements:
            statement_mode = "exact_source"
            contextual_role = None
            context_evidence = None
        elif not false and source_statement == identity_statement:
            statement_mode = "contextual_identity"
            contextual_role = identity_role
            context_evidence = identity_evidence
        else:
            raise ValueError(f"Modo V/F desconocido: {fact['fact_id']}")
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
                "contextual_role": contextual_role,
                "context_evidence": context_evidence,
                "replacement_source_ref": replacement_row["reference"] if replacement_row else None,
                "correct_slot_signature": fact.get("_slot_signature"),
                "replacement_slot_signature": replacement_row.get("_slot_signature") if replacement_row else None,
                "explanation": (
                    (
                        f"Es falsa por atribución contextual: el enunciado citado pertenece a "
                        f"{replacement_row['reference']}, no a {fact['reference']}. "
                        f"La fuente correcta declara: {_display_excerpt(source_statement)}."
                    )
                    if false and false_mutation_kind == "cross_reference_statement"
                    else f"Es falsa: la fuente dice «{fact['answer']}», no «{incorrect_detail}»."
                    if false
                    else (
                        f"Es verdadera: la identidad se deriva del contexto literal de {fact['reference']}."
                        if statement_mode == "contextual_identity"
                        else f"Es verdadera y reproduce literalmente {fact['reference']}."
                    )
                ),
                "why_distractors_fail": {
                    "Verdadero" if false else "Falso": (
                        (
                            f"El enunciado es verdadero en {replacement_row['reference']}, "
                            f"pero no corresponde a {fact['reference']}."
                        )
                        if false and false_mutation_kind == "cross_reference_statement"
                        else f"La única alteración es «{incorrect_detail}»; la fuente contiene «{fact['answer']}»."
                        if false
                        else (
                            "La identidad coincide con el papel que muestra el contexto fuente."
                            if statement_mode == "contextual_identity"
                            else "La afirmación coincide literalmente con la unidad fuente."
                        )
                    )
                },
                "trap_type": (
                    "true_in_other_context"
                    if false and false_mutation_kind == "cross_reference_statement"
                    else "single_plausible_detail" if false else None
                ),
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

    def cross_reference_statement_spec(
        fact: dict[str, Any],
        source_statement: str,
        replacement_rows: list[dict[str, Any]],
    ) -> tuple[str, dict[str, Any], str, str, str]:
        target_source_norm = _norm(fact["source_quote"])
        for replacement_row in replacement_rows:
            if "context" not in replacement_row or "source_quote" not in replacement_row:
                continue
            if replacement_row["reference"] == fact["reference"]:
                continue
            for visible_text in true_statement_options(
                replacement_row, include_contextual_identity=False
            ):
                if _norm(visible_text) in target_source_norm:
                    continue
                prompt = f"Verdadero o falso: Según {fact['reference']}, {visible_text}"
                if (
                    prompt not in used_true_false_prompts
                    and _norm(prompt) not in used_true_false_prompt_norms
                ):
                    replacement = (
                        replacement_row["answer"]
                        if fact["category"] == "place"
                        else _match_initial_case(
                            replacement_row["answer"], fact["answer"]
                        )
                    )
                    return (
                        source_statement,
                        replacement_row,
                        visible_text,
                        replacement,
                        "cross_reference_statement",
                    )
        raise ValueError(
            "No hay afirmación contextual ajena y única para "
            f"{fact['fact_id']}"
        )

    for fact in true_facts:
        selected: tuple[str, dict[str, Any], str, str, str] | None = None
        source_statement = statement_by_fact[fact["fact_id"]]
        exact_false_statements = true_statement_options(
            fact, include_contextual_identity=False
        )
        if exact_false_statements:
            source_statement = exact_false_statements[0]
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
                incorrect_detail = _negated_action_detail(negated, fact["answer"])
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
                source_statement = exact_false_statements[0]
                selected = cross_reference_statement_spec(
                    fact, source_statement, replacement_candidates
                )
        elif (
            fact["category"] == "person"
            and _norm(fact["answer"]) in DIVINE_NAMES
        ):
            # Sustituir «Señor» por «Santo» puede conservar el mismo referente
            # y no produce una falsedad semántica inequívoca. Además, insertar
            # un personaje humano en una acción divina crea una pista demasiado
            # obvia. Se atribuye al pasaje una afirmación completa que sí es
            # literal en otra referencia y exige distinguir el contexto.
            source_statement = exact_false_statements[0]
            selected = cross_reference_statement_spec(
                fact, source_statement, replacement_candidates
            )
        elif fact["category"] == "number" and (
            len(fact["answer"].split()) > 1
            or _number_answer_is_compound_component(fact)
        ):
            # Las expresiones numéricas compuestas pueden incluir unidades
            # distintas. Sustituirlas dentro de una cita crea frases como
            # «tiempo, tiempos... gobernadores». Se usa una proposición completa
            # tomada de otra referencia para preservar la gramática.
            source_statement = exact_false_statements[0]
            selected = cross_reference_statement_spec(
                fact, source_statement, replacement_candidates
            )
        for replacement_row in replacement_candidates:
            if selected is not None:
                break
            replacement = (
                replacement_row["answer"]
                if fact["category"] == "place"
                else _match_initial_case(replacement_row["answer"], fact["answer"])
            )
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
                    "closed_category_substitution",
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
    facts_by_id = {fact["fact_id"]: fact for fact in facts}
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
    atomic_true_false_templates = 0
    generic_contextual_prompts = 0
    contextual_role_errors = 0
    context_evidence_leaks = 0
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
                blank_count < 1
                or not question["question"].startswith("Complete ")
            )
        elif family == "single_choice_contextual":
            invalid = (
                blank_count != 0
                or question.get("trap_type") != "true_in_other_context"
                or len(question.get("why_distractors_fail", {})) != 3
            )
        else:
            invalid = blank_count < 1
        if invalid:
            family_contract_errors[family] += 1
        fact = facts_by_id[question["fact_id"]]
        if question.get("statement_mode") == "atomic_presence":
            atomic_true_false_templates += 1
        if family == "single_choice_contextual":
            expected_question, expected_role, expected_evidence = (
                render_contextual_question(fact)
            )
            if GENERIC_CONTEXTUAL_FRAGMENT in _norm(question["question"]):
                generic_contextual_prompts += 1
            if (
                question["question"] != expected_question
                or question.get("contextual_role") != expected_role
                or question.get("context_evidence") != expected_evidence
            ):
                contextual_role_errors += 1
            if contains_normalized_phrase(
                str(question.get("context_evidence") or ""),
                str(question["correct_answer"]),
            ):
                context_evidence_leaks += 1
        if question.get("statement_mode") == "contextual_identity":
            expected_statement, expected_role, expected_evidence = (
                render_contextual_identity(fact)
            )
            expected_visible_statement = (
                f"Según {question['reference']}, {expected_statement}"
            )
            if (
                question.get("statement") != expected_visible_statement
                or question.get("truth_source_statement") != expected_statement
                or question.get("contextual_role") != expected_role
                or question.get("context_evidence") != expected_evidence
            ):
                contextual_role_errors += 1
            if contains_normalized_phrase(
                str(question.get("context_evidence") or ""),
                str(question.get("asserted_detail") or ""),
            ):
                context_evidence_leaks += 1
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
        "semantic_option_collisions": semantic_option_collision_count(questions),
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
        "atomic_true_false_templates": atomic_true_false_templates,
        "generic_contextual_prompts": generic_contextual_prompts,
        "contextual_role_errors": contextual_role_errors,
        "context_evidence_leaks": context_evidence_leaks,
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
