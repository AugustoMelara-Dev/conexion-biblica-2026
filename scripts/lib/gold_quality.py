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
PROPER_TERMS_RAW = (
        "Daniel Nabucodonosor Babilonia Jehová Señor Abed-nego Altísimo Belsasar Beltsasar Darío "
        "Jerusalén Persia Ananías Caldeos Israel Azarías Egipto Sadrac Miguel Grecia Anciano Príncipe "
        "Moisés Santo Salvador Aspenaz Melsar Arioc Media Gabriel Cristo Creador Todopoderoso Eufrates "
        "Medo-Persia Ezequiel Satanás Joacim Sinar Hidekel Quitim Etiopía Libia Mesac Uparsin Judea "
        "Asuero Jeremías Mesías Pentateuco Atenas Abednego Jerusalem UPHARSIN Persas Sesach Chebar Jacob"
    ).split()


def normalized_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", str(value))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", folded.encode("ascii", "ignore").decode().lower()).split())


PROPER_TERMS = {normalized_text(value) for value in PROPER_TERMS_RAW}
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
    return total >= 8 and (
        (len(before) >= 2 and len(after) >= 2)
        or max(len(before), len(after)) >= 8
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
    if kind in {"nominal", "contains_finite"}:
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


def build_consolidation_bank(root: Path) -> dict[str, Any]:
    raw_questions, facts, context = load_source(root)
    distractor_pools: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts.values():
        answer = str(fact.get("answer", ""))
        categories = _option_categories(answer, context)
        distractor_pools[grammatical_signature(answer, categories)].append(fact)
    questions = [repair_distractors(q, facts, context, distractor_pools) for q in raw_questions]
    decisions = {q["id"]: audit_question(q, context) for q in questions}
    by_fact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rejected: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    chapter_status: dict[str, Counter[str]] = defaultdict(Counter)
    for q in questions:
        decision = decisions[q["id"]]
        status_counts[decision.status.value] += 1
        chapter_status[q["chapter"]][decision.status.value] += 1
        for reason in decision.rejection_reasons:
            rejected[reason] += 1
        if decision.status is EditorialStatus.GOLD:
            by_fact[q["fact_id"]].append(q)

    # Máximo dos habilidades distintas por hecho: contextual y completar.
    selected: list[dict[str, Any]] = []
    duplicate_drops = 0
    for fact_id, candidates in sorted(by_fact.items()):
        best_by_type: dict[str, dict[str, Any]] = {}
        for q in candidates:
            if q["type"] not in best_by_type:
                best_by_type[q["type"]] = q
        chosen = [best_by_type[kind] for kind in ("multiple_choice", "fill_blank") if kind in best_by_type]
        duplicate_drops += len(candidates) - len(chosen)
        selected.extend(make_gold_question(q, facts[fact_id], decisions[q["id"]]) for q in chosen)

    # Se reaudita la reserva: solo hechos GOLD, pools disjuntos, 15% total.
    fact_ids = sorted({q["fact_id"] for q in selected})
    blind_count = min(len(fact_ids), max(250, round(len(fact_ids) * 0.15)))
    blind_candidates = sorted(fact_ids, key=lambda value: hashlib.sha256(("blind:" + value).encode()).hexdigest())[:blind_count]
    pools = partition_blind_facts(blind_candidates)
    blind_lookup = {fact_id: pool for pool, values in pools.items() for fact_id in values}
    for q in selected:
        q["blind_pool"] = blind_lookup.get(q["fact_id"])
        q["blind_final_pool"] = q["blind_pool"] is not None

    selected_ids = {q["id"] for q in selected}
    final_chapter_status: dict[str, Counter[str]] = defaultdict(Counter)
    editorial_index: list[dict[str, Any]] = []
    for q in questions:
        decision = decisions[q["id"]]
        if q["id"] in selected_ids:
            status = "gold"
            reasons: list[str] = []
        elif decision.status is EditorialStatus.GOLD:
            status = "silver"
            reasons = ["superficial_duplicate"]
        else:
            status = decision.status.value
            reasons = list(decision.rejection_reasons)
        final_chapter_status[q["chapter"]][status] += 1
        editorial_index.append({
            "id": q["id"],
            "chapter": q["chapter"],
            "template_id": q["template_id"],
            "editorial_status": status,
            "quality_score": decision.score,
            "reasons": reasons,
        })

    out = root / "public/banks/consolidation-v5"
    (out / "questions").mkdir(parents=True, exist_ok=True)
    for chapter in sorted({q["chapter"] for q in selected}):
        rows = [q for q in selected if q["chapter"] == chapter]
        (out / "questions" / f"{chapter}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    selected_chapters = Counter(q["chapter"] for q in selected)
    manifest = {
        "schema_version": "5.1",
        "profile_id": "consolidation-v5",
        "version": "V5-CONSOLIDACION-FINAL-2026-08-26",
        "source": "MaterialConexionBiblica (1).pdf",
        "original_records_preserved": len(questions),
        "gold_questions": len(selected),
        "gold_facts": len(fact_ids),
        "average_variants_per_fact": round(len(selected) / len(fact_ids), 2) if fact_ids else 0,
        "blind_pools": {key: len(value) for key, value in pools.items()},
        "disabled_templates": ["mc-sequence-v1", "tf-single-detail-v1", "tf-single-detail-v2"],
        "shards": [
            {"chapter": chapter, "question_count": selected_chapters[chapter], "questions_file": f"banks/consolidation-v5/questions/{chapter}.json"}
            for chapter in sorted(selected_chapters)
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "editorial-index.json").write_text(json.dumps(editorial_index, ensure_ascii=False), encoding="utf-8")
    raw_by_id = {q["id"]: q for q in raw_questions}
    before_after = [
        {
            "id": q["id"],
            "before": raw_by_id[q["id"]]["question"],
            "after": q["question"],
            "reference_before": raw_by_id[q["id"]]["verse_or_page"],
            "reference_after": q["verse_or_page"],
        }
        for q in selected[:20]
    ]
    tier_a = {"PR43", "PR44", "DAN7", "DAN8", "DAN9", "DAN11"}
    stratified_review: dict[str, Any] = {}
    for chapter in sorted(selected_chapters):
        requested = 100 if chapter in tier_a else 20
        sample = [q for q in selected if q["chapter"] == chapter][:requested]
        stratified_review[chapter] = {
            "requested": requested,
            "reviewed": len(sample),
            "question_ids": [q["id"] for q in sample],
            "checks": {
                "quality_score_at_least_85": all(q["quality_score"] >= 85 for q in sample),
                "source_quote_supports_answer": all(_contains(q["source_quote"], q["correct_answer"]) for q in sample),
                "unique_options": all(len({normalized_text(option) for option in q["options"]}) == len(q["options"]) for q in sample),
                "normalized_reference": all(q["verse_or_page"] == normalize_reference(q["verse_or_page"]) for q in sample),
                "sufficient_fill_anchor": all(
                    q["type"] != "fill_blank"
                    or fill_anchor_is_sufficient(q["source_span"], q["correct_answer"])
                    for q in sample
                ),
            },
        }
    report = {
        **manifest,
        "raw_status_counts": dict(status_counts),
        "final_status_counts": dict(Counter(row["editorial_status"] for row in editorial_index)),
        "final_status_by_chapter": {chapter: dict(counts) for chapter, counts in sorted(final_chapter_status.items())},
        "chapter_status_before_deduplication": {chapter: dict(counts) for chapter, counts in sorted(chapter_status.items())},
        "gold_by_chapter": dict(sorted(selected_chapters.items())),
        "rejections_by_reason": dict(rejected.most_common()),
        "duplicate_variants_removed": duplicate_drops,
        "quarantine_by_template": dict(Counter(q["template_id"] for q in questions if decisions[q["id"]].status is EditorialStatus.QUARANTINE)),
        "blind_fact_ids": pools,
        "stratified_review": stratified_review,
        "before_after_examples": before_after,
    }
    return {"manifest": manifest, "report": report, "selected": selected, "decisions": decisions}
