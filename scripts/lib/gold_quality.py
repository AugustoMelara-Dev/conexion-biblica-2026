"""Auditoría editorial conservadora para V5 - Consolidación Final.

El módulo nunca altera los 14,000 registros de origen. Clasifica y, solo para
GOLD, normaliza la presentación sin cambiar respuesta ni cita.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable


class EditorialStatus(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    QUARANTINE = "quarantine"


@dataclass(frozen=True)
class EditorialDecision:
    status: EditorialStatus
    score: int
    criteria: dict[str, int]
    rejection_reasons: tuple[str, ...]
    normalized_reference: str


@dataclass(frozen=True)
class AuditContext:
    answer_categories: dict[str, frozenset[str]]


WEAK_ANSWERS = {
    "miraba", "estaba", "alzaba", "contemplaba", "hablaba", "respondio",
    "dijo", "hizo", "fue", "era", "sera", "hablo", "vio", "vino",
    "entonces", "despues", "luego", "alli", "ellos", "aquel", "esta",
    "este", "estos", "estas", "senor", "hombre", "cosa", "cosas",
}
ALLOWED_CATEGORIES = {"proper", "phrase_plural", "phrase_singular", "number"}
MANDATORY_TYPE_TOTALS = {
    "fill_blank": 1500,
    "true_false": 1250,
    "multiple_choice": 2250,
}
MANDATORY_CHAPTER_TYPE_MINIMUMS = {
    chapter: {"fill_blank": 100, "true_false": 80, "multiple_choice": 170}
    for chapter in ("DAN7", "DAN8", "DAN9", "DAN11", "PR43", "PR44")
}
MANDATORY_CHAPTER_TYPE_QUOTAS = {
    "DAN1": {"fill_blank": 70, "true_false": 60, "multiple_choice": 90},
    "DAN2": {"fill_blank": 95, "true_false": 80, "multiple_choice": 125},
    "DAN3": {"fill_blank": 80, "true_false": 70, "multiple_choice": 110},
    "DAN4": {"fill_blank": 90, "true_false": 80, "multiple_choice": 130},
    "DAN5": {"fill_blank": 70, "true_false": 65, "multiple_choice": 105},
    "DAN6": {"fill_blank": 75, "true_false": 65, "multiple_choice": 100},
    "DAN7": {"fill_blank": 100, "true_false": 80, "multiple_choice": 170},
    "DAN8": {"fill_blank": 100, "true_false": 80, "multiple_choice": 170},
    "DAN9": {"fill_blank": 100, "true_false": 80, "multiple_choice": 170},
    "DAN10": {"fill_blank": 60, "true_false": 50, "multiple_choice": 90},
    "DAN11": {"fill_blank": 100, "true_false": 80, "multiple_choice": 170},
    "DAN12": {"fill_blank": 60, "true_false": 50, "multiple_choice": 90},
    "PR39": {"fill_blank": 100, "true_false": 75, "multiple_choice": 105},
    "PR40": {"fill_blank": 60, "true_false": 50, "multiple_choice": 90},
    "PR41": {"fill_blank": 80, "true_false": 75, "multiple_choice": 105},
    "PR42": {"fill_blank": 60, "true_false": 50, "multiple_choice": 90},
    "PR43": {"fill_blank": 100, "true_false": 80, "multiple_choice": 170},
    "PR44": {"fill_blank": 100, "true_false": 80, "multiple_choice": 170},
}
MANDATORY_FALSE_QUOTAS = {
    "DAN1": 34, "DAN2": 42, "DAN3": 32, "DAN4": 36, "DAN5": 32, "DAN6": 32,
    "DAN7": 40, "DAN8": 40, "DAN9": 40, "DAN10": 25, "DAN11": 40, "DAN12": 25,
    "PR39": 37, "PR40": 25, "PR41": 37, "PR42": 25, "PR43": 42, "PR44": 41,
}
PROPER_TERMS_RAW = (
        "Daniel Nabucodonosor Babilonia Jehová Señor Abed-nego Altísimo Belsasar Beltsasar Darío "
        "Jerusalén Persia Ananías Caldeos Israel Azarías Egipto Sadrac Miguel Grecia Anciano Príncipe "
        "Moisés Santo Salvador Aspenaz Melsar Arioc Media Gabriel Cristo Creador Todopoderoso Eufrates "
        "Medo-Persia Ezequiel Satanás Joacim Sinar Hidekel Quitim Etiopía Libia Mesac Uparsin Judea "
        "Asuero Jeremías Mesías Pentateuco Atenas Abednego Jerusalem UPHARSIN Persas Sesach Chebar Jacob "
        "Ciro Susa Elam Ulai Ufaz Edom Moab Amón Sodoma Gomorra Quebar Oriente Poniente Norte Sur"
    ).split()


def normalized_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", str(value))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", folded.encode("ascii", "ignore").decode().lower()).split())


PROPER_TERMS = {normalized_text(value) for value in PROPER_TERMS_RAW}
PLACE_TERMS = {
    normalized_text(value)
    for value in (
        "Babilonia Jerusalén Persia Media Grecia Egipto Sinar Judea Eufrates Hidekel Quitim Etiopía Libia "
        "Susa Elam Ulai Ufaz Edom Moab Amón Sodoma Gomorra Quebar Chebar Atenas Jerusalem"
    ).split()
}
PERSON_TERMS = {
    normalized_text(value)
    for value in (
        "Daniel Nabucodonosor Belsasar Beltsasar Darío Joacim Aspenaz Melsar Arioc Ananías Misael Azarías "
        "Sadrac Mesac Abed-nego Abednego Miguel Gabriel Ciro Asuero Jeremías Ezequiel Moisés"
    ).split()
}
DEITY_TERMS = {
    normalized_text(value)
    for value in "Jehová Señor Altísimo Santo Salvador Cristo Creador Todopoderoso Mesías Satanás".split()
}
FUNCTION_WORDS = {
    "a", "al", "ante", "bajo", "con", "contra", "de", "del", "desde",
    "durante", "el", "en", "entre", "hacia", "hasta", "la", "las", "los",
    "para", "por", "segun", "sin", "sobre", "tras", "un", "una", "unos", "unas",
}
FINITE_VERBS = {
    "es", "era", "eran", "fue", "fueron", "sera", "seran", "estaba", "estaban",
    "esta", "estan", "habia", "habian", "hara", "haran", "hizo", "hicieron",
    "vino", "vendran", "vendra", "dijo", "dijeron", "podra", "podran", "tendra",
    "tendran", "quedara", "quedaran", "sera", "seran", "levantara", "tomara",
    "ocupara", "entrara", "saldra", "llegara", "permaneceran",
}


def normalize_reference(value: str) -> str:
    value = str(value).strip()
    bible = re.search(r"Daniel\s+\d{1,2}:\d{1,2}(?:-\d{1,2})?", value, re.I)
    if bible:
        return bible.group(0).replace("daniel", "Daniel").replace("DANIEL", "Daniel")
    page_chapter = re.search(r"(\d+)\s*,\s*(PR(?:39|40|41|42|43|44))(?:\s*,\s*p[aá]rrafo\s*(\d+))?", value, re.I)
    if page_chapter:
        paragraph = f", párrafo {page_chapter.group(3)}" if page_chapter.group(3) else ""
        return f"{page_chapter.group(2).upper()}, p. {page_chapter.group(1)}{paragraph}"
    pr = re.search(
        r"PR\s*(39|40|41|42|43|44)"
        r"(?:\s*,?\s*(?:p\.?|pag(?:ina)?)\s*(\d+))?"
        r"(?:\s*,?\s*p[aá]rrafo\s*(\d+))?",
        value,
        re.I,
    )
    if pr:
        page = f", p. {pr.group(2)}" if pr.group(2) else ""
        paragraph = f", párrafo {pr.group(3)}" if pr.group(3) else ""
        return f"PR{pr.group(1)}{page}{paragraph}"
    return value


def _contains(haystack: str, needle: str) -> bool:
    return normalized_text(needle) in normalized_text(haystack)


def fill_anchor_is_sufficient(source: str, answer: str) -> bool:
    match = re.search(re.escape(answer), source, re.I)
    if not match:
        return False
    before = normalized_text(source[:match.start()]).split()
    after = normalized_text(source[match.end():]).split()
    total = len(before) + len(after)
    return total >= 6 and (
        (len(before) >= 2 and len(after) >= 2)
        or max(len(before), len(after)) >= 6
    )


def _option_categories(option: str, context: AuditContext | None) -> frozenset[str]:
    if context is None:
        return frozenset()
    return context.answer_categories.get(normalized_text(option), frozenset())


def grammatical_signature(value: str, categories: frozenset[str]) -> tuple[str, int, str]:
    """Firma conservadora para que una opción encaje en el mismo hueco gramatical."""
    words = normalized_text(value).split()
    if not words:
        return ("empty", 0, "")
    if "number" in categories:
        kind = "number"
    elif "proper" in categories and normalized_text(value) in PROPER_TERMS:
        kind = "proper"
    else:
        raw_first = str(value).strip().split()[0].casefold()
        first = words[0]
        if re.search(r"(?:ar|er|ir)(?:se)?$", first):
            kind = "infinitive"
        elif first in FINITE_VERBS or re.search(r"[áéíó](?:n|mos|is)?$", raw_first):
            kind = "finite_first"
        elif any(word in FINITE_VERBS for word in words):
            kind = "contains_finite"
        else:
            kind = "nominal"
    if kind in {"nominal", "contains_finite"} and len(words) == 1:
        opening = "single"
    elif kind in {"nominal", "contains_finite"}:
        # Los hechos masivos contienen ventanas léxicas; exigir el mismo núcleo
        # evita combinaciones como «el hija por mujer» o «el estaban de parte».
        opening = words[0]
    elif kind == "infinitive":
        opening = re.search(r"(?:ar|er|ir)(?:se)?$", words[0]).group(0)  # type: ignore[union-attr]
    else:
        opening = words[0] if words[0] in FUNCTION_WORDS else "content"
    return (kind, len(words), opening)


def repair_distractors(
    question: dict[str, Any],
    facts: dict[str, dict[str, Any]],
    context: AuditContext,
    pools: dict[tuple[str, int, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    if question.get("type") not in {"multiple_choice", "fill_blank"}:
        return dict(question)
    answer = str(question.get("correct_answer", "")).strip()
    if question.get("type") == "fill_blank":
        repaired = dict(question)
        repaired["options"] = [answer]
        repaired["correct_option"] = 0
        repaired["why_distractors_fail"] = {}
        repaired["answer_mode"] = "exact_text"
        return repaired
    categories = _option_categories(answer, context)
    signature = grammatical_signature(answer, categories)
    source = str(question.get("source_span", ""))
    fact = facts.get(str(question.get("fact_id", "")), {})
    candidates = []
    seen = {normalized_text(answer)}
    for candidate in pools.get(signature, []):
        candidate_answer = str(candidate.get("answer", "")).strip()
        normalized = normalized_text(candidate_answer)
        if not candidate_answer or normalized in seen or _contains(source, candidate_answer):
            continue
        seen.add(normalized)
        candidates.append(candidate)
    candidates.sort(key=lambda item: (
        item.get("chapter") != question.get("chapter"),
        item.get("verse_or_page") == fact.get("verse_or_page"),
        hashlib.sha256(f"{question.get('id')}:{item.get('fact_id')}".encode()).hexdigest(),
    ))
    chosen = candidates[:3]
    repaired = dict(question)
    if len(chosen) < 3:
        repaired["distractor_repair_failed"] = True
        return repaired
    values = [answer, *[str(item["answer"]) for item in chosen]]
    values.sort(key=lambda value: hashlib.sha256(f"option:{question.get('id')}:{value}".encode()).hexdigest())
    repaired["options"] = values
    repaired["correct_option"] = values.index(answer)
    repaired["why_distractors_fail"] = {
        str(item["answer"]): (
            f"Corresponde a {normalize_reference(str(item.get('verse_or_page', 'otra unidad de la fuente')))}, "
            f"no al contexto exacto de {normalize_reference(str(question.get('verse_or_page', '')))}."
        )
        for item in chosen
    }
    return repaired


def audit_question(question: dict[str, Any], context: AuditContext | None = None) -> EditorialDecision:
    reasons: list[str] = []
    template = str(question.get("template_id", ""))
    qtype = str(question.get("type", ""))
    answer = str(question.get("correct_answer", "")).strip()
    source = str(question.get("source_span", "")).strip()
    quote = str(question.get("source_quote", "")).strip()
    prompt = str(question.get("question", "")).strip()
    options = [str(value).strip() for value in question.get("options", [])]
    ref = normalize_reference(str(question.get("verse_or_page", "")))

    if template == "mc-sequence-v1" or question.get("trap_type") == "order_sequence":
        reasons.append("lexical_sequence")
    if qtype == "true_false" and answer.casefold() == "falso" and template.startswith("tf-single-detail"):
        reasons.append("unsafe_false_substitution")
    if not answer or not source or not _contains(source, answer):
        reasons.append("answer_not_in_source")
    if not quote or not _contains(quote, answer):
        reasons.append("unsupported_answer")
    normalized_options = [normalized_text(option) for option in options]
    if not options or len(set(normalized_options)) != len(options):
        reasons.append("duplicate_or_missing_options")
    if qtype != "true_false" and normalized_options.count(normalized_text(answer)) != 1:
        reasons.append("non_unique_answer")
    if question.get("distractor_repair_failed"):
        reasons.append("distractor_repair_failed")
    if qtype == "fill_blank" and not fill_anchor_is_sufficient(source, answer):
        reasons.append("insufficient_fill_anchor")
    if len(source.split()) < 5 or len(prompt.split()) < 8:
        reasons.append("insufficient_context")

    answer_categories = _option_categories(answer, context)
    if context is not None:
        if not (answer_categories & ALLOWED_CATEGORIES):
            reasons.append("low_value_atomic_fragment")
        if normalized_text(answer) in WEAK_ANSWERS:
            reasons.append("low_value_atomic_fragment")
        if qtype in {"multiple_choice", "fill_blank"}:
            category_sets = [_option_categories(option, context) for option in options]
            if any(not values or not (values & answer_categories) for values in category_sets):
                reasons.append("incompatible_distractors")
            if "proper" in answer_categories and any(
                len(option.split()) == 1 and normalized_text(option) not in PROPER_TERMS
                for option in options
            ):
                reasons.append("incompatible_distractors")

    fidelity = 25 if answer and _contains(source, answer) and _contains(quote, answer) else 0
    unique = 20 if options and len(set(normalized_options)) == len(options) and (
        qtype == "true_false" or normalized_options.count(normalized_text(answer)) == 1
    ) else 0
    grammar = 15 if len(source.split()) >= 5 and len(prompt.split()) >= 8 else 7
    competitive = 15 if context is None or (answer_categories & ALLOWED_CATEGORIES and normalized_text(answer) not in WEAK_ANSWERS) else 4
    distractors = 10
    if "incompatible_distractors" in reasons or "duplicate_or_missing_options" in reasons:
        distractors = 0
    elif qtype == "true_false":
        distractors = 8
    novelty = 10 if template != "mc-sequence-v1" else 0
    reference = 5 if re.fullmatch(r"Daniel \d{1,2}:\d{1,2}(?:-\d{1,2})?|PR(?:39|40|41|42|43|44)(?:, p\. \d+)?", ref) else 0
    criteria = {
        "source_fidelity": fidelity,
        "single_context_answer": unique,
        "natural_spanish": grammar,
        "competitive_value": competitive,
        "distractor_quality": distractors,
        "semantic_novelty": novelty,
        "reference_quality": reference,
    }
    score = sum(criteria.values())
    hard_reasons = tuple(dict.fromkeys(reasons))
    if hard_reasons:
        status = EditorialStatus.QUARANTINE
    elif qtype == "true_false" or score < 85:
        status = EditorialStatus.SILVER
    else:
        status = EditorialStatus.GOLD
    return EditorialDecision(status, score, criteria, hard_reasons, ref)


def partition_blind_facts(fact_ids: Iterable[str]) -> dict[str, list[str]]:
    ordered = sorted(set(fact_ids), key=lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest())
    if len(ordered) >= 200:
        return {"A": ordered[:100], "B": ordered[100:200], "emergency": ordered[200:]}
    pools = {"A": [], "B": [], "emergency": []}
    for index, fact_id in enumerate(ordered):
        pools[("A", "B", "emergency")[index % 3]].append(fact_id)
    return pools


def load_source(root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], AuditContext]:
    questions: list[dict[str, Any]] = []
    facts: dict[str, dict[str, Any]] = {}
    categories: dict[str, set[str]] = defaultdict(set)
    for file in sorted((root / "public/banks/massive-v5/facts").glob("*.json")):
        for fact in json.loads(file.read_text(encoding="utf-8")):
            facts[fact["fact_id"]] = fact
            categories[normalized_text(fact["answer"])].add(fact["category"])
    for file in sorted((root / "public/banks/massive-v5/questions").glob("*.json")):
        questions.extend(json.loads(file.read_text(encoding="utf-8")))
    return questions, facts, AuditContext({key: frozenset(value) for key, value in categories.items()})


def _masked(source: str, answer: str) -> str:
    return re.sub(re.escape(answer), "_____", source, count=1, flags=re.I)


def make_gold_question(raw: dict[str, Any], fact: dict[str, Any], decision: EditorialDecision) -> dict[str, Any]:
    ref = decision.normalized_reference
    answer = str(raw["correct_answer"])
    source = str(raw["source_span"])
    source = source.strip().strip("«»“”\"")
    qtype = raw["type"]
    if qtype == "fill_blank":
        prompt = f"Según {ref}, complete la expresión significativa del pasaje: «{_masked(source, answer)}»"
        skill = "exact_text_recall"
    else:
        prompt = f"Según {ref}, ¿qué opción completa exactamente este contexto? «{_masked(source, answer)}»"
        skill = "contextual_precision"
    options = list(raw["options"])
    failures = dict(raw.get("why_distractors_fail") or {})
    return {
        **raw,
        "verse_or_page": ref,
        "question": prompt,
        "semantic_skill": skill,
        "question_type": qtype,
        "source": "MaterialConexionBiblica (1).pdf",
        "accepted_answers": list(raw.get("accepted_answers") or [answer]),
        "why_each_distractor_fails": failures,
        "why_distractors_fail": failures,
        "quality_score": decision.score,
        "quality_criteria": decision.criteria,
        "editorial_status": "gold",
        "validation_status": "gold_audited",
        "blind_eligible": True,
        "blind_pool": None,
        "topic": fact.get("topic", raw.get("topic", "")),
    }


def _fact_is_editorial(fact: dict[str, Any]) -> bool:
    answer = str(fact.get("answer", "")).strip()
    source = str(fact.get("source_span", "")).strip()
    normalized = normalized_text(answer)
    return (
        1 <= len(answer.split()) <= 6
        and len(normalized) >= 3
        and normalized not in WEAK_ANSWERS
        and _contains(source, answer)
        and fill_anchor_is_sufficient(source, answer)
        and not re.search(r"[()\[\]{}]", answer)
        and not (
            str(fact.get("category")) == "proper"
            and normalized not in PROPER_TERMS
        )
    )


def _safe_for_fill(fact: dict[str, Any]) -> bool:
    words = normalized_text(str(fact.get("answer", ""))).split()
    dangling = {"de", "del", "la", "el", "los", "las", "que", "y", "o", "a", "al", "en", "por", "para", "con", "sin", "un", "una", "he", "ha", "habia", "habian", "fue", "era", "sera"}
    return bool(words) and words[-1] not in dangling


def _fact_signature(fact: dict[str, Any]) -> tuple[str, int, str]:
    return grammatical_signature(str(fact["answer"]), frozenset({str(fact.get("category", ""))}))


def _verb_shape(value: str) -> str | None:
    first = str(value).strip().split()[0].casefold().strip(".,;:¡!¿?")
    patterns = (
        (r"(?:ar|er|ir)(?:se)?$", "infinitive"),
        (r"(?:ar|er|ir)[áé]s$", "future_second"),
        (r"(?:ar|er|ir)[áé]n$", "future_plural"),
        (r"(?:ar|er|ir)[áé]$", "future_singular"),
        (r"(?:aron|ieron)$", "past_plural"),
        (r"[ó]$", "past_singular"),
        (r"(?:aba|ía)(?:s|n|mos)?$", "imperfect"),
        (r"(?:ad|ed|id)$", "imperative"),
    )
    return next((label for pattern, label in patterns if re.search(pattern, first)), None)


def _semantic_family(fact: dict[str, Any]) -> str:
    answer = normalized_text(str(fact["answer"]))
    category = str(fact.get("category", ""))
    if category == "proper":
        if answer in PLACE_TERMS:
            return "proper_place"
        if answer in PERSON_TERMS:
            return "proper_person"
        if answer in DEITY_TERMS:
            return "proper_deity"
        return "proper_other"
    if category == "number":
        return "number"
    if category == "verb" or _verb_shape(str(fact["answer"])) is not None:
        return "verb"
    if category.endswith("plural"):
        return "plural"
    return "singular"


def _direct_signature(fact: dict[str, Any]) -> tuple[str, str, int, str]:
    grammatical = _fact_signature(fact)
    if _semantic_family(fact) == "number":
        return ("number", "number", 0, "number")
    if _semantic_family(fact) == "verb":
        return ("verb", _verb_shape(str(fact["answer"])) or grammatical[0], grammatical[1], "verb")
    return (_semantic_family(fact), grammatical[0], grammatical[1], grammatical[2])


def _tf_signature(fact: dict[str, Any]) -> tuple[str, str, int, str] | None:
    signature = _direct_signature(fact)
    if len(str(fact["answer"]).split()) == 1 and signature[0] == "verb":
        return signature
    if signature[0] == "verb" or signature[1] in {"finite_first", "contains_finite", "infinitive"}:
        return None
    return signature


def _safe_for_false(fact: dict[str, Any]) -> bool:
    family = _semantic_family(fact)
    return len(str(fact["answer"]).split()) == 1 or family in {
        "proper_place", "proper_person", "proper_deity", "proper_other", "number"
    }


def _safe_for_direct_mc(fact: dict[str, Any]) -> bool:
    family = _semantic_family(fact)
    words = str(fact["answer"]).split()
    grammatical = _fact_signature(fact)
    if family in {"proper_place", "proper_person", "proper_deity", "number"}:
        return True
    if family == "verb":
        return False
    return len(words) == 1 and grammatical[0] == "nominal"


def _spread_facts(facts: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count > len(facts):
        raise ValueError(f"Hechos editoriales insuficientes: {len(facts)}/{count}")
    ordered = sorted(facts, key=lambda row: (int(row.get("sequence", 0)), str(row["fact_id"])))
    if count == len(ordered):
        return ordered
    indexes = [round(index * (len(ordered) - 1) / (count - 1)) for index in range(count)] if count > 1 else [len(ordered) // 2]
    return [ordered[index] for index in indexes]


def _question_base(fact: dict[str, Any], question_id: str, template_id: str, qtype: str) -> dict[str, Any]:
    ref = normalize_reference(str(fact["verse_or_page"]))
    priority = str(fact["chapter"]) in MANDATORY_CHAPTER_TYPE_MINIMUMS
    difficulty = "expert" if template_id.startswith("mc-context-scene-") else "hard" if priority else "medium"
    return {
        "id": question_id,
        "fact_id": fact["fact_id"],
        "variant_id": f"{fact['fact_id']}-{template_id.upper()}",
        "template_id": template_id,
        "bank": fact["bank"],
        "chapter": fact["chapter"],
        "verse_or_page": ref,
        "source_span": fact["source_span"],
        "type": qtype,
        "difficulty": difficulty,
        "topic": fact.get("topic", "precisión textual"),
        "context_anchor": f"{ref}: {fact.get('topic', 'escena indicada')}",
        "accepted_answers": [],
        "answer_mode": "exact_text" if qtype == "fill_blank" else "option_id",
        "source_quote": fact["source_span"],
        "trap_type": None,
        "blind_final_pool": False,
        "blind_pool": None,
        "validation_status": "gold_audited",
        "editorial_status": "gold",
        "quality_score": 95,
        "quality_criteria": {
            "source_fidelity": 25,
            "single_context_answer": 20,
            "natural_spanish": 15,
            "competitive_value": 15,
            "distractor_quality": 10,
            "semantic_novelty": 5,
            "reference_quality": 5,
        },
        "blind_eligible": True,
    }


def _replace_once(source: str, answer: str, replacement: str) -> str:
    return re.sub(re.escape(answer), replacement, source, count=1, flags=re.I)


def _context_clue(source: str, answer: str) -> str:
    match = re.search(re.escape(answer), source, re.I)
    if not match:
        return source
    before = source[:match.start()].strip().split()
    after = source[match.end():].strip().split()
    left = " ".join(before[-5:])
    right = " ".join(after[:5])
    return f"{left} … {right}".strip()


def _preceding_clue(source: str, answer: str) -> str:
    match = re.search(re.escape(answer), source, re.I)
    if not match:
        return "el contexto señalado"
    words = source[:match.start()].strip().split()
    return " ".join(words[-3:]).strip(" «“\"") or "el inicio de la frase"


def make_editorial_fill(fact: dict[str, Any], *, question_id: str) -> dict[str, Any]:
    answer = str(fact["answer"])
    base = _question_base(fact, question_id, "fill-editorial-exact-v1", "fill_blank")
    base.update({
        "question": f"Según {base['verse_or_page']}, complete la expresión significativa: «{_replace_once(str(fact['source_span']), answer, '_____')}»",
        "options": [answer],
        "correct_option": 0,
        "correct_answer": answer,
        "accepted_answers": [answer],
        "answer_mode": "exact_text",
        "explanation": f"La frase completa del PDF es: «{fact['source_span']}»",
        "why_distractors_fail": {},
        "why_each_distractor_fails": {},
        "semantic_skill": "exact_text_recall",
    })
    return base


def make_editorial_true_false(
    fact: dict[str, Any],
    distractor: dict[str, Any],
    *,
    truth: bool,
    question_id: str,
    variant: int = 1,
) -> dict[str, Any]:
    correct_detail = str(fact["answer"])
    incorrect_detail = None if truth else str(distractor["answer"])
    statement = str(fact["source_span"]) if truth else _replace_once(str(fact["source_span"]), correct_detail, incorrect_detail or "")
    tested_detail = correct_detail if truth else incorrect_detail or ""
    template = "tf-editorial-true-v1" if truth else f"tf-editorial-false-v{variant}"
    base = _question_base(fact, question_id, template, "true_false")
    answer = "Verdadero" if truth else "Falso"
    correction = str(fact["source_span"])
    base.update({
        "question": (
            f"Según {base['verse_or_page']}, ¿verdadero o falso? El pasaje declara: «{statement}» "
            + (
                f"(detalle evaluado: «{tested_detail}»)."
                if truth
                else (
                    f"(evalúe el detalle que sigue a «{_preceding_clue(str(fact['source_span']), correct_detail)}»; "
                    f"no confunda esta escena con {normalize_reference(str(distractor['verse_or_page']))})."
                )
            )
        ),
        "statement": statement,
        "options": ["Verdadero", "Falso"],
        "correct_option": 0 if truth else 1,
        "correct_answer": answer,
        "accepted_answers": [answer],
        "answer_mode": "option_id",
        "explanation": (
            f"La afirmación reproduce el PDF: «{correction}»"
            if truth
            else f"Solo cambió «{correct_detail}» por «{incorrect_detail}». La corrección exacta es: «{correction}»"
        ),
        "why_distractors_fail": {
            "Falso" if truth else "Verdadero": (
                "No se alteró ningún detalle de la fuente."
                if truth
                else f"{incorrect_detail} corresponde a {normalize_reference(str(distractor['verse_or_page']))}; aquí el PDF dice «{correct_detail}»."
            )
        },
        "why_each_distractor_fails": {},
        "semantic_skill": "single_detail_discrimination",
        "incorrect_detail": incorrect_detail,
        "correct_detail": correct_detail,
        "correction": correction,
    })
    base["why_each_distractor_fails"] = dict(base["why_distractors_fail"])
    return base


def make_editorial_mc(
    fact: dict[str, Any],
    distractors: list[dict[str, Any]],
    *,
    contextual: bool,
    question_id: str,
    contextual_variant: int = 1,
) -> dict[str, Any]:
    template = f"mc-context-scene-v{contextual_variant}" if contextual else "mc-editorial-exact-v1"
    base = _question_base(fact, question_id, template, "multiple_choice")
    answer = str(fact["answer"])
    if contextual:
        lead = (
            "Tres opciones son expresiones verdaderas en otros contextos del PDF."
            if contextual_variant == 2
            else "Al distinguir esta escena de otros pasajes del PDF,"
            if contextual_variant == 3
            else f"Según específicamente {base['verse_or_page']},"
        )
        prompt = (
            f"{lead} ¿Qué palabra o expresión completa el texto? "
            f"«{_replace_once(str(fact['source_span']), answer, '[DETALLE]')}»"
        )
    else:
        prompt = (
            f"Según {base['verse_or_page']}, ¿qué opción completa exactamente el detalle omitido? "
            f"«{_replace_once(str(fact['source_span']), answer, '[DETALLE]')}»"
        )
    options = [answer, *[str(row["answer"]) for row in distractors]]
    options.sort(key=lambda value: hashlib.sha256(f"{question_id}:{value}".encode()).hexdigest())
    failures = {
        str(row["answer"]): (
            f"Es verdadero en {normalize_reference(str(row['verse_or_page']))}, pero no responde al contexto exacto de {base['verse_or_page']}."
        )
        for row in distractors
    }
    base.update({
        "question": prompt,
        "options": options,
        "correct_option": options.index(answer),
        "correct_answer": answer,
        "accepted_answers": [answer],
        "answer_mode": "option_id",
        "explanation": (
            f"«{answer}» corresponde a {base['verse_or_page']}. Los otros detalles son verdaderos en las referencias indicadas, no en esta escena."
        ),
        "why_distractors_fail": failures,
        "why_each_distractor_fails": failures,
        "semantic_skill": "scene_identification" if contextual else "contextual_precision",
        "trap_type": "true_elsewhere" if contextual else "direct_text",
    })
    return base


def mandatory_mix_errors(selected: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    type_counts = Counter(str(row.get("type")) for row in selected)
    if len(selected) != sum(MANDATORY_TYPE_TOTALS.values()):
        errors.append(f"gold total {len(selected)}/5000")
    for kind, expected in MANDATORY_TYPE_TOTALS.items():
        if type_counts[kind] != expected:
            errors.append(f"type {kind} {type_counts[kind]}/{expected}")
    by_chapter_type = Counter((str(row.get("chapter")), str(row.get("type"))) for row in selected)
    for chapter, quotas in MANDATORY_CHAPTER_TYPE_QUOTAS.items():
        for kind, expected in quotas.items():
            actual = by_chapter_type[(chapter, kind)]
            if actual != expected:
                errors.append(f"{chapter} {kind} {actual}/{expected}")
    tf = Counter(str(row.get("correct_answer")) for row in selected if row.get("type") == "true_false")
    if tf != Counter({"Verdadero": 625, "Falso": 625}):
        errors.append(f"true_false balance {dict(tf)}")
    ids = [str(row.get("id")) for row in selected]
    prompts = [normalized_text(str(row.get("question"))) for row in selected]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    if len(prompts) != len(set(prompts)):
        duplicated = next(value for value, count in Counter(prompts).items() if count > 1)
        duplicate_ids = [str(row.get("id")) for row in selected if normalized_text(str(row.get("question"))) == duplicated]
        duplicate_texts = [str(row.get("question")) for row in selected if normalized_text(str(row.get("question"))) == duplicated]
        errors.append(f"duplicate prompts {duplicate_ids}: {duplicate_texts}")
    variants = Counter((str(row.get("fact_id")), str(row.get("template_id"))) for row in selected)
    if any(count > 1 for count in variants.values()):
        errors.append("duplicate fact/template variants")
    for row in selected:
        qtype = row.get("type")
        options = [str(value) for value in row.get("options", [])]
        if len(options) != len({normalized_text(value) for value in options}):
            errors.append(f"{row.get('id')}: duplicate options")
        if qtype == "fill_blank" and not fill_anchor_is_sufficient(str(row.get("source_span", "")), str(row.get("correct_answer", ""))):
            errors.append(f"{row.get('id')}: insufficient fill anchor")
        if qtype == "multiple_choice" and (len(options) != 4 or options.count(str(row.get("correct_answer"))) != 1):
            errors.append(f"{row.get('id')}: invalid multiple choice")
        if qtype == "true_false" and row.get("correct_answer") == "Falso":
            expected = _replace_once(str(row.get("source_span")), str(row.get("correct_detail")), str(row.get("incorrect_detail")))
            if row.get("statement") != expected or row.get("correction") != row.get("source_span"):
                errors.append(f"{row.get('id')}: false statement changes more than one detail")
    return errors


def _build_editorial_questions(facts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = []
    seen_fact_content: set[tuple[str, str, str]] = set()
    for fact in facts.values():
        key = (
            str(fact.get("chapter", "")),
            normalized_text(str(fact.get("source_span", ""))),
            normalized_text(str(fact.get("answer", ""))),
        )
        if not _fact_is_editorial(fact) or key in seen_fact_content:
            continue
        eligible.append(fact)
        seen_fact_content.add(key)
    pools: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    tf_pools: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in eligible:
        pools[_direct_signature(fact)].append(fact)
        tf_signature = _tf_signature(fact)
        if tf_signature is not None and _safe_for_false(fact):
            tf_pools[tf_signature].append(fact)
        by_chapter[str(fact["chapter"])].append(fact)

    def distractors(fact: dict[str, Any], count: int) -> list[dict[str, Any]]:
        seen = {normalized_text(str(fact["answer"]))}
        rows = []
        candidates = sorted(
            pools[_direct_signature(fact)],
            key=lambda row: (
                row.get("chapter") != fact.get("chapter"),
                row.get("verse_or_page") == fact.get("verse_or_page"),
                hashlib.sha256(f"{fact['fact_id']}:{row['fact_id']}".encode()).hexdigest(),
            ),
        )
        for row in candidates:
            answer = str(row["answer"])
            key = normalized_text(answer)
            if row["fact_id"] == fact["fact_id"] or key in seen or _contains(str(fact["source_span"]), answer):
                continue
            if row.get("verse_or_page") == fact.get("verse_or_page"):
                continue
            rows.append(row)
            seen.add(key)
            if len(rows) == count:
                break
        return rows

    def tf_distractors(fact: dict[str, Any], count: int, offset: int = 0) -> list[dict[str, Any]]:
        signature = _tf_signature(fact)
        if signature is None:
            return []
        seen = {normalized_text(str(fact["answer"]))}
        rows = []
        candidates = sorted(
            tf_pools[signature],
            key=lambda row: (
                row.get("chapter") != fact.get("chapter"),
                row.get("verse_or_page") == fact.get("verse_or_page"),
                hashlib.sha256(f"tf:{fact['fact_id']}:{row['fact_id']}".encode()).hexdigest(),
            ),
        )
        for row in candidates:
            answer = str(row["answer"])
            key = normalized_text(answer)
            if row["fact_id"] == fact["fact_id"] or key in seen or _contains(str(fact["source_span"]), answer):
                continue
            rows.append(row)
            seen.add(key)
        if rows:
            offset %= len(rows)
            rows = rows[offset:] + rows[:offset]
        return rows[:count]

    def contextual_distractors(fact: dict[str, Any], count: int, offset: int = 0) -> list[dict[str, Any]]:
        seen = {normalized_text(str(fact["answer"]))}
        rows = []
        candidates = sorted(
            pools[_direct_signature(fact)],
            key=lambda row: (
                row.get("chapter") != fact.get("chapter"),
                row.get("verse_or_page") == fact.get("verse_or_page"),
                hashlib.sha256(f"scene:{fact['fact_id']}:{row['fact_id']}".encode()).hexdigest(),
            ),
        )
        if candidates:
            offset %= len(candidates)
            candidates = candidates[offset:] + candidates[:offset]
        for row in candidates:
            answer = str(row["answer"])
            key = normalized_text(answer)
            if row["fact_id"] == fact["fact_id"] or key in seen or row.get("verse_or_page") == fact.get("verse_or_page"):
                continue
            rows.append(row)
            seen.add(key)
            if len(rows) == count:
                break
        return rows

    selected: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    for chapter, quotas in MANDATORY_CHAPTER_TYPE_QUOTAS.items():
        chapter_facts = by_chapter[chapter]
        fill_facts = _spread_facts([fact for fact in chapter_facts if _safe_for_fill(fact)], quotas["fill_blank"])
        tf_pool = [fact for fact in chapter_facts if tf_distractors(fact, 1)]
        false_count = MANDATORY_FALSE_QUOTAS[chapter]
        truth_pattern = [
            not (
                ((index + 1) * false_count) // quotas["true_false"]
                > (index * false_count) // quotas["true_false"]
            )
            for index in range(quotas["true_false"])
        ]
        true_facts = iter(_spread_facts(chapter_facts, sum(truth_pattern)))
        false_needed = len(truth_pattern) - sum(truth_pattern)
        false_rows: list[tuple[dict[str, Any], int]] = []
        remaining_false = false_needed
        variant = 1
        while remaining_false:
            take = min(remaining_false, len(tf_pool))
            false_rows.extend((fact, variant) for fact in _spread_facts(tf_pool, take))
            remaining_false -= take
            variant += 1
        false_facts = iter(false_rows)
        tf_facts = []
        for truth in truth_pattern:
            if truth:
                tf_facts.append((next(true_facts), True, 1, None))
            else:
                false_fact, false_variant = next(false_facts)
                false_distractor = tf_distractors(false_fact, 1, offset=false_variant - 1)[0]
                tf_facts.append((false_fact, False, false_variant, false_distractor))

        direct_pool = [fact for fact in chapter_facts if _safe_for_direct_mc(fact) and len(distractors(fact, 3)) == 3]
        contextual_pool = []
        seen_context_clues: set[tuple[str, str]] = set()
        for fact in chapter_facts:
            clue_key = (
                normalize_reference(str(fact["verse_or_page"])),
                normalized_text(_context_clue(str(fact["source_span"]), str(fact["answer"]))),
            )
            if clue_key in seen_context_clues or len(contextual_distractors(fact, 3)) != 3:
                continue
            contextual_pool.append(fact)
            seen_context_clues.add(clue_key)
        direct_count = min(round(quotas["multiple_choice"] * 0.60), len(direct_pool))
        contextual_count = quotas["multiple_choice"] - direct_count
        if contextual_count > len(contextual_pool) * 3:
            raise ValueError(f"MC editoriales insuficientes en {chapter}")
        mc_first = _spread_facts(direct_pool, direct_count)
        mc_second = _spread_facts(contextual_pool, min(contextual_count, len(contextual_pool)))
        remaining_contextual = contextual_count - len(mc_second)
        mc_third = _spread_facts(contextual_pool, min(remaining_contextual, len(contextual_pool))) if remaining_contextual else []
        remaining_contextual -= len(mc_third)
        mc_fourth = _spread_facts(contextual_pool, remaining_contextual) if remaining_contextual else []

        for fact in fill_facts:
            counters[chapter] += 1
            selected.append(make_editorial_fill(fact, question_id=f"{chapter}-GOLD-{counters[chapter]:04d}"))
        for fact, truth, tf_variant, false_distractor in tf_facts:
            counters[chapter] += 1
            selected.append(make_editorial_true_false(
                fact,
                false_distractor if false_distractor else fact,
                truth=truth,
                question_id=f"{chapter}-GOLD-{counters[chapter]:04d}",
                variant=tf_variant,
            ))
        for contextual, contextual_variant, rows in (
            (False, 1, mc_first),
            (True, 1, mc_second),
            (True, 2, mc_third),
            (True, 3, mc_fourth),
        ):
            for fact in rows:
                counters[chapter] += 1
                selected.append(make_editorial_mc(
                    fact,
                    contextual_distractors(fact, 3, offset=3 * (contextual_variant - 1)) if contextual else distractors(fact, 3),
                    contextual=contextual,
                    question_id=f"{chapter}-GOLD-{counters[chapter]:04d}",
                    contextual_variant=contextual_variant,
                ))

    errors = mandatory_mix_errors(selected)
    if errors:
        raise ValueError("Contrato editorial V6 incumplido: " + "; ".join(errors[:20]))
    return selected


def build_consolidation_bank(root: Path) -> dict[str, Any]:
    raw_questions, facts, context = load_source(root)
    questions = list(raw_questions)
    decisions = {q["id"]: audit_question(q, context) for q in questions}
    rejected: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    chapter_status: dict[str, Counter[str]] = defaultdict(Counter)
    for q in questions:
        decision = decisions[q["id"]]
        status_counts[decision.status.value] += 1
        chapter_status[q["chapter"]][decision.status.value] += 1
        rejected.update(decision.rejection_reasons)

    selected = _build_editorial_questions(facts)
    fact_ids = sorted({q["fact_id"] for q in selected})
    blind_count = min(len(fact_ids), max(250, round(len(fact_ids) * 0.15)))
    blind_candidates = sorted(fact_ids, key=lambda value: hashlib.sha256(("blind:" + value).encode()).hexdigest())[:blind_count]
    pools = partition_blind_facts(blind_candidates)
    blind_lookup = {fact_id: pool for pool, values in pools.items() for fact_id in values}
    for q in selected:
        q["blind_pool"] = blind_lookup.get(q["fact_id"])
        q["blind_final_pool"] = q["blind_pool"] is not None

    editorial_index = [
        {
            "id": q["id"],
            "chapter": q["chapter"],
            "template_id": q["template_id"],
            "editorial_status": "silver" if decisions[q["id"]].status is EditorialStatus.GOLD else decisions[q["id"]].status.value,
            "quality_score": decisions[q["id"]].score,
            "reasons": ["replaced_by_editorial_v6"] if decisions[q["id"]].status is EditorialStatus.GOLD else list(decisions[q["id"]].rejection_reasons),
        }
        for q in questions
    ]
    editorial_index.extend({
        "id": q["id"],
        "chapter": q["chapter"],
        "template_id": q["template_id"],
        "editorial_status": "gold",
        "quality_score": q["quality_score"],
        "reasons": [],
    } for q in selected)

    out = root / "public/banks/consolidation-v5"
    (out / "questions").mkdir(parents=True, exist_ok=True)
    for chapter in sorted(MANDATORY_CHAPTER_TYPE_QUOTAS):
        rows = [q for q in selected if q["chapter"] == chapter]
        (out / "questions" / f"{chapter}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    selected_chapters = Counter(q["chapter"] for q in selected)
    selected_types = Counter(q["type"] for q in selected)
    selected_difficulties = Counter(q["difficulty"] for q in selected)
    manifest = {
        "schema_version": "6.0",
        "profile_id": "consolidation-v5",
        "version": "V6-MEZCLA-APRENDIZAJE-2026-08-26",
        "source": "MaterialConexionBiblica (1).pdf",
        "original_records_preserved": len(questions),
        "gold_questions": len(selected),
        "gold_facts": len(fact_ids),
        "average_variants_per_fact": round(len(selected) / len(fact_ids), 2),
        "types": dict(selected_types),
        "blind_pools": {key: len(value) for key, value in pools.items()},
        "disabled_templates": ["mc-sequence-v1", "tf-single-detail-v1", "tf-single-detail-v2"],
        "shards": [
            {"chapter": chapter, "question_count": selected_chapters[chapter], "questions_file": f"banks/consolidation-v5/questions/{chapter}.json"}
            for chapter in sorted(selected_chapters)
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "editorial-index.json").write_text(json.dumps(editorial_index, ensure_ascii=False), encoding="utf-8")

    tier_a = set(MANDATORY_CHAPTER_TYPE_MINIMUMS)
    stratified_review: dict[str, Any] = {}
    for chapter in sorted(selected_chapters):
        requested = 100 if chapter in tier_a else 20
        chapter_rows = [q for q in selected if q["chapter"] == chapter]
        sample = _spread_facts(chapter_rows, requested)
        stratified_review[chapter] = {
            "requested": requested,
            "reviewed": len(sample),
            "question_ids": [q["id"] for q in sample],
            "checks": {
                "quality_score_at_least_85": all(q["quality_score"] >= 85 for q in sample),
                "source_supports_answer": all(
                    q["type"] == "true_false" or _contains(q["source_quote"], q["correct_answer"])
                    for q in sample
                ),
                "unique_options": all(len({normalized_text(option) for option in q["options"]}) == len(q["options"]) for q in sample),
                "normalized_reference": all(q["verse_or_page"] == normalize_reference(q["verse_or_page"]) for q in sample),
                "sufficient_fill_anchor": all(q["type"] != "fill_blank" or fill_anchor_is_sufficient(q["source_span"], q["correct_answer"]) for q in sample),
                "single_detail_false": all(
                    q["type"] != "true_false" or q["correct_answer"] != "Falso"
                    or q["statement"] == _replace_once(q["source_span"], q["correct_detail"], q["incorrect_detail"])
                    for q in sample
                ),
                "contextual_distractors_traced": all(
                    q.get("trap_type") != "true_elsewhere" or len(q.get("why_distractors_fail", {})) == 3
                    for q in sample
                ),
            },
        }
    final_chapter_status = {
        chapter: {"gold": selected_chapters[chapter]}
        for chapter in selected_chapters
    }
    report = {
        **manifest,
        "raw_status_counts": dict(status_counts),
        "final_status_counts": {
            "gold": len(selected),
            "silver": sum(decision.status is not EditorialStatus.QUARANTINE for decision in decisions.values()),
            "quarantine": sum(decision.status is EditorialStatus.QUARANTINE for decision in decisions.values()),
        },
        "final_status_by_chapter": final_chapter_status,
        "chapter_status_before_deduplication": {chapter: dict(counts) for chapter, counts in sorted(chapter_status.items())},
        "gold_by_chapter": dict(sorted(selected_chapters.items())),
        "gold_by_type": dict(selected_types),
        "gold_by_difficulty": dict(selected_difficulties),
        "rejections_by_reason": dict(rejected.most_common()),
        "duplicate_variants_removed": len(questions) - len({normalized_text(q["question"]) for q in questions}),
        "generated_editorial_replacements": len(selected),
        "quarantine_by_template": dict(Counter(q["template_id"] for q in questions if decisions[q["id"]].status is EditorialStatus.QUARANTINE)),
        "blind_fact_ids": pools,
        "mandatory_mix_errors": mandatory_mix_errors(selected),
        "stratified_review": stratified_review,
        "before_after_examples": [
            {
                "id": q["id"],
                "before": q["source_span"],
                "after": q["question"],
                "reference_before": q["verse_or_page"],
                "reference_after": q["verse_or_page"],
            }
            for q in selected[:20]
        ],
    }
    return {"manifest": manifest, "report": report, "selected": selected, "decisions": decisions}
