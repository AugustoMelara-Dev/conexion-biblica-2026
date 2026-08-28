from __future__ import annotations

import re
import unicodedata
from typing import Any


GENERIC_CONTEXTUAL_FRAGMENT = "¿que opcion corresponde especificamente a esta escena:"
ALLOWED_CONTEXTUAL_ROLES = {
    "actor",
    "recipient",
    "named_entity",
    "origin",
    "destination",
    "location",
    "direction",
    "quantity",
    "duration",
    "order",
    "measure",
    "action",
    "state",
    "change",
    "subject",
    "object",
    "predicate",
    "modifier",
    "connector_object",
    "concept",
    "cause",
    "purpose",
    "consequence",
    "description",
    "formulation",
}


def _norm(value: str) -> str:
    return " ".join(
        "".join(
            char
            for char in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(char)
        ).split()
    )


def contains_normalized_phrase(text: str, phrase: str) -> bool:
    normalized_text = _norm(text)
    normalized_phrase = _norm(phrase)
    if not normalized_phrase:
        return False
    return re.search(
        rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)", normalized_text
    ) is not None


def _answer_span(fact: dict[str, Any]) -> tuple[str, str]:
    context = str(fact["context"])
    answer = str(fact["answer"])
    matches = list(
        re.finditer(
            rf"(?<!\w){re.escape(answer)}(?!\w)",
            context,
        )
    )
    if len(matches) != 1:
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:context_answer_count")
    match = matches[0]
    return context[: match.start()], context[match.end() :]


def derive_contextual_role(fact: dict[str, Any]) -> str:
    relation = str(fact.get("relation_type") or "")
    if fact.get("relation_prompt") and relation in {
        "cause",
        "purpose",
        "consequence",
        "speaker",
        "recipient",
    }:
        return "actor" if relation == "speaker" else relation

    before, after = _answer_span(fact)
    before_norm = _norm(before)
    after_norm = _norm(after)
    category = fact["category"]
    if category == "person":
        if re.search(r"\b(?:a|al)$", before_norm):
            return "recipient"
        if re.match(r"(?:dijo|respondio|vino|hizo|hablo|ordeno)\b", after_norm):
            return "actor"
        return "named_entity"
    if category == "place":
        if re.search(r"\b(?:a|hacia|hasta)$", before_norm):
            return "destination"
        if re.search(r"\b(?:de|desde)$", before_norm):
            return "origin"
        if _norm(str(fact["answer"])) in {"norte", "sur", "oriente", "poniente"}:
            return "direction"
        return "location"
    if category == "number":
        if re.match(r"(?:anos?|dias?|semanas?|tiempos?)\b", after_norm):
            return "duration"
        if re.search(r"\b(?:primer|primero|segundo|tercer|tercero)$", before_norm):
            return "order"
        return "quantity"
    if category == "action":
        return "action"
    if category == "term":
        signature = str(fact.get("_slot_signature") or "")
        if "subject" in signature:
            return "subject"
        if "predicate" in signature or "adjective" in signature:
            return "predicate"
        if "preposition" in signature:
            return "connector_object"
        if "object" in signature:
            return "object"
        return "concept"
    return relation if relation in {"cause", "purpose", "consequence"} else "formulation"


def mask_context_answer(fact: dict[str, Any], marker: str = "[…]") -> str:
    _answer_span(fact)
    answer = str(fact["answer"])
    result = re.sub(
        rf"(?<!\w){re.escape(answer)}(?!\w)",
        lambda _: marker,
        str(fact["context"]),
        flags=re.IGNORECASE,
    )
    if contains_normalized_phrase(result, str(fact["answer"])):
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:masked_answer_leak")
    return result.strip()


_QUESTION_OPENINGS = {
    "actor": "¿Quién realiza la acción descrita en",
    "recipient": "¿A quién se dirige la acción u orden expresada en",
    "named_entity": "¿Qué personaje completa la relación descrita en",
    "origin": "¿Qué lugar funciona como origen en",
    "destination": "¿Qué destino completa el movimiento descrito en",
    "location": "¿Qué lugar completa la relación espacial descrita en",
    "direction": "¿Qué dirección geográfica precisa",
    "quantity": "¿Qué dato cuantitativo precisa",
    "duration": "¿Qué duración precisa el período descrito en",
    "order": "¿Qué dato ordinal completa",
    "measure": "¿Qué medida precisa",
    "action": "¿Qué acción completa la secuencia descrita en",
    "state": "¿Qué estado completa la descripción presentada en",
    "change": "¿Qué cambio completa la secuencia presentada en",
    "subject": "¿Qué sujeto completa la relación literal expresada en",
    "object": "¿Qué objeto completa la acción expresada en",
    "predicate": "¿Qué cualidad o estado completa la predicación de",
    "modifier": "¿Qué modificador precisa la descripción de",
    "connector_object": "¿Qué concepto completa la relación introducida por la preposición en",
    "concept": "¿Qué concepto completa la relación literal de",
    "cause": "¿Qué causa declara explícitamente",
    "purpose": "¿Qué propósito declara explícitamente",
    "consequence": "¿Qué consecuencia declara explícitamente",
    "description": "¿Qué descripción completa la relación literal de",
    "formulation": "¿Qué formulación completa la relación literal de",
}

_IDENTITY_LABELS = {
    "actor": "quien realiza la acción",
    "recipient": "el destinatario",
    "named_entity": "el personaje identificado",
    "origin": "el lugar de origen",
    "destination": "el destino",
    "location": "el lugar indicado",
    "direction": "la dirección indicada",
    "quantity": "el dato cuantitativo",
    "duration": "la duración",
    "order": "el dato ordinal",
    "measure": "la medida",
    "action": "la acción indicada",
    "state": "el estado descrito",
    "change": "el cambio descrito",
    "subject": "el sujeto de la relación",
    "object": "el objeto de la acción",
    "predicate": "la cualidad o estado",
    "modifier": "el modificador",
    "connector_object": "el término regido por la preposición",
    "concept": "el concepto",
    "cause": "la causa declarada",
    "purpose": "el propósito declarado",
    "consequence": "la consecuencia declarada",
    "description": "la descripción",
    "formulation": "la formulación",
}


def render_contextual_question(fact: dict[str, Any]) -> tuple[str, str, str]:
    role = derive_contextual_role(fact)
    if role not in ALLOWED_CONTEXTUAL_ROLES:
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:invalid_contextual_role")
    evidence = mask_context_answer(fact)
    answer = str(fact["answer"])
    relation_prompt = str(fact.get("relation_prompt") or "")
    if relation_prompt and not contains_normalized_phrase(relation_prompt, answer):
        question = relation_prompt
    else:
        reference = str(fact["reference"])
        source_label = (
            "el pasaje citado"
            if contains_normalized_phrase(reference, answer)
            else reference
        )
        opening = _QUESTION_OPENINGS[role]
        if contains_normalized_phrase(opening, answer):
            opening = "¿Qué detalle completa correctamente"
        question = f"Según {source_label}, {opening} «{evidence}»?"
    if contains_normalized_phrase(question, str(fact["answer"])):
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:context_question_answer_leak")
    return question, role, evidence


def render_contextual_identity(fact: dict[str, Any]) -> tuple[str, str, str]:
    role = derive_contextual_role(fact)
    evidence = mask_context_answer(fact)
    statement = (
        f"En la escena «{evidence}», {_IDENTITY_LABELS[role]} "
        f"es «{fact['answer']}»."
    )
    if statement.count(str(fact["answer"])) != 1:
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:identity_answer_count")
    return statement, role, evidence
