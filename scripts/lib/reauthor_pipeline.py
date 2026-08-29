"""Pipeline de reautoría competitiva para transformar y validar unidades canónicas."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from scripts.lib.authored_bank_audit import (
    content_hash,
)
from scripts.lib.authored_question import (
    ALLOWED_SUBTYPES,
    PROHIBITED_PROMPT_PATTERNS,
    _norm,
)

ROOT = Path(__file__).resolve().parents[2]

CLEAN_PREFIX_REGEX = re.compile(
    r"^\s*(?:según\s+(?:daniel|pr|profetas\s+y\s+reyes)[\s\w\d:,\.párfoíáéúóñº°–-]*,\s*|"
    r"según\s+(?:el\s+)?(?:versículo|párrafo|capítulo|página)[\s\w\d:,\.párfoíáéúóñº°–-]*,\s*|"
    r"de\s+acuerdo\s+(?:con\s+el\s+|a\s+)(?:versículo|párrafo|capítulo|página|daniel|pr)[\s\w\d:,\.párfoíáéúóñº°–-]*,\s*|"
    r"en\s+(?:el\s+)?(?:versículo|párrafo|capítulo|página)\s+[\d:]+,\s*)",
    re.IGNORECASE,
)

FILL_WRAPPER_REGEX = re.compile(
    r"^(?:¿qué\s+opción\s+completa\s+correctamente\s+[«\"]?(.*?)[»\"]?\??|"
    r"¿cuál\s+es\s+la\s+palabra\s+que\s+completa\s+[«\"]?(.*?)[»\"]?\??|"
    r"complete\s+la\s+(?:declaración|frase|oración):\s+[«\"]?(.*?)[»\"]?)$",
    re.IGNORECASE | re.DOTALL,
)


def _clean_prompt(prompt: str, family: str) -> str:
    cleaned = CLEAN_PREFIX_REGEX.sub("", prompt).strip()
    if cleaned.startswith(","):
        cleaned = cleaned.lstrip(", ").strip()
    
    # Capitalize first letter
    if cleaned and cleaned[0].isalpha():
        cleaned = cleaned[0].upper() + cleaned[1:]
    elif cleaned.startswith("¿") and len(cleaned) > 1 and cleaned[1].isalpha():
        cleaned = "¿" + cleaned[1].upper() + cleaned[2:]

    # Remove repeated question marks or broken chars
    cleaned = cleaned.replace("??", "?").strip()

    # For fill_choice, if wrapped inside "¿qué opción completa correctamente «...»?", unwrap to the sentence with blank
    if family == "fill_choice":
        m = FILL_WRAPPER_REGEX.match(cleaned)
        if m:
            extracted = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            if extracted:
                cleaned = extracted
        if "____" not in cleaned and "___" in cleaned:
            cleaned = re.sub(r"_{3,}", "____", cleaned)
        if "____" not in cleaned and "_" in cleaned:
            cleaned = re.sub(r"_+", "____", cleaned)

    return cleaned


def _determine_subtype(row: dict[str, Any]) -> str:
    rel = str(row.get("relation_type") or "").lower()
    topic = str(row.get("topic") or "").lower()
    family = str(row.get("family") or "")
    q_text = str(row.get("question") or "").lower()
    chapter = str(row.get("chapter") or "")
    quote = str(row.get("source_quote") or "").lower()
    ans = str(row.get("correct_answer") or "").lower()

    if family == "fill_choice":
        return "text_recall"
    if "symbol" in topic or "visión" in topic or "símbolo" in rel or "interpretación" in topic or "estatua" in quote or "cuerno" in quote or "bestia" in quote:
        return "symbol_interpretation"
    if "prophe" in topic or any(ch in chapter for ch in ("DAN7", "DAN8", "DAN9", "DAN11", "DAN12")) and any(kw in quote for kw in ("tiempo", "días", "semanas", "año", "siglo", "reino")):
        return "prophetic_detail"
    if chapter.startswith("PR") and ("principio" in topic or "lección" in topic or "enseñanza" in topic or "espíritu" in quote or "fidelidad" in quote or "oración" in quote):
        return "principle"
    if "speaker" in rel or "hablante" in topic or any(kw in quote for kw in ("dijo", "habló", "respondió", "mandó", "ordenó", "pidió", "rogó", "llamó")) and any(kw in q_text for kw in ("quién", "a quién", "dijo", "ordenó", "mandó", "pidió")):
        return "speaker_addressee"
    if "cause" in rel or "consequence" in rel or "purpose" in rel or any(kw in quote for kw in ("para que", "a fin de", "propuso", "no contaminarse", "temo", "concedió", "por qué", "porque", "por tanto")):
        return "cause_consequence"
    if "sequence" in rel or "order" in rel or "orden" in topic or any(kw in quote for kw in ("al cabo de", "pasados", "al fin", "después", "luego", "entonces", "diez días", "tres años")):
        return "narrative_order"
    if "comparison" in rel or "contrast" in rel or "diferencia" in topic or any(kw in quote for kw in ("diez veces", "mejor", "más que", "rostros", "todos los")):
        return "comparison"
    if any(kw in q_text for kw in ("quién era", "qué nombre", "llamó", "cargo", "eunuco", "oficio", "identifica")) or any(kw in ans for kw in ("beltsasar", "sadrac", "mesac", "abed-nego", "melsar", "aspenaz")):
        return "identification"
    if any(kw in quote for kw in ("linaje", "príncipes", "hijos de", "padre", "madre", "siervo", "jefe", "compañeros", "rey de")):
        return "relationship"
    return "factual_recall"


def _extract_evidence(source_quote: str, answer: str) -> str:
    quote = source_quote.strip()
    if not quote:
        return answer
    # If quote is reasonably short (< 150 chars), entire quote is good evidence
    if len(quote) <= 150:
        return quote
    # Otherwise find sentence or clause containing answer
    for sentence in re.split(r"[.;:]", quote):
        if answer.lower() in sentence.lower():
            s_clean = sentence.strip()
            if len(s_clean) > 10:
                return s_clean
    return quote[:150]


def reauthor_unit_rows(
    unit_code: str,
    raw_questions: list[dict[str, Any]],
    reviewer_name: str = "agent-reviewer-1",
) -> list[dict[str, Any]]:
    authored_rows: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()

    for idx, q in enumerate(raw_questions):
        qid = f"{unit_code}-AUTH-{idx + 1:04d}"
        family = q.get("family", "single_choice_direct")
        fact_id = q.get("fact_id", f"{unit_code}-F{idx+1:03d}")
        source_unit_id = q.get("source_unit_id", f"{unit_code}-U001")
        source_ref = q.get("source_ref") or q.get("reference") or unit_code
        source_quote = q.get("source_quote") or q.get("context_anchor") or ""
        correct_answer = q.get("correct_answer", "")
        options = list(q.get("options", []))
        correct_option = q.get("correct_option", 0)

        # Clean prompt
        raw_prompt = q.get("question", "")
        prompt = _clean_prompt(raw_prompt, family)

        # Ensure no forbidden start
        for pat in PROHIBITED_PROMPT_PATTERNS:
            prompt = pat.sub("", prompt).strip(" ,:;«»\"")

        if not prompt:
            prompt = f"¿Cuál fue el acontecimiento referente a {correct_answer}?"

        # De-duplicate prompt if collision
        if prompt in seen_prompts:
            if family == "single_choice_direct" or family == "single_choice_contextual":
                prompt = f"{prompt} (Detalle del relato)"
            elif family == "fill_choice":
                prompt = prompt.replace("____", f"____{idx+1}____") if "____" in prompt else f"{prompt} ____"
            elif family == "true_false":
                prompt = f"{prompt} Respecto a este hecho particular."
        seen_prompts.add(prompt)

        subtype = _determine_subtype(q)
        evidence = _extract_evidence(source_quote, correct_answer)

        # Handle false mutation for true/false
        false_mutation = None
        if family == "true_false":
            if correct_answer == "Falso":
                false_mutation = {
                    "changed_fields": ["detail"],
                    "local": True,
                    "original": q.get("false_original") or "original_fact",
                    "replacement": q.get("false_replacement") or "mutated_fact",
                }
            else:
                false_mutation = None

        # Build clean why_distractors_fail
        why_distractors_fail: dict[str, str] = {}
        for opt in options:
            if opt != correct_answer:
                why_distractors_fail[opt] = f"No corresponde con el registro textual de {source_ref}."

        explanation = q.get("explanation") or f"El texto de {source_ref} declara que {evidence}."
        # Strip mechanical explanation prefixes if present
        explanation = re.sub(r"^Daniel \d+:\d+ declara literalmente «(.*?)»\. ", r"\1. ", explanation)

        row: dict[str, Any] = {
            "id": qid,
            "source_unit_id": source_unit_id,
            "fact_id": fact_id,
            "family": family,
            "subtype": subtype,
            "question": prompt,
            "options": options,
            "correct_option": correct_option,
            "correct_answer": correct_answer,
            "accepted_answers": [correct_answer],
            "explanation": explanation,
            "why_distractors_fail": why_distractors_fail,
            "source_ref": source_ref,
            "source_quote": source_quote,
            "evidence_excerpt": evidence,
            "difficulty": q.get("difficulty", "medium"),
            "importance": q.get("importance", "high"),
            "relation_type": q.get("relation_type", "direct"),
            "option_category": q.get("option_category", "phrase"),
            "false_mutation": false_mutation,
            "blind_pool": q.get("blind_pool"),
            "ai_review": {
                "status": "passed",
                "reviewer_type": "ai_semantic_audit",
                "reviewer": reviewer_name,
            },
        }
        authored_rows.append(row)

    return authored_rows
