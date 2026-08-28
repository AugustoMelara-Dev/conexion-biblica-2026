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
    "territorial_title",
    "geographic_relation",
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
            if re.search(
                r"\b(?:vino|vinieron|llego|llegaron|entro|entraron|partio|partieron|"
                r"marcho|marcharon|regreso|regresaron|volvio|volvieron|subio|subieron|"
                r"descendio|descendieron|llevo|llevaron|llevara|llevados|llevadas|"
                r"condujo|condujeron|enviado|enviada|enviados|enviadas)\b.{0,120}"
                r"\b(?:a|hacia|hasta)$",
                before_norm,
            ):
                return "destination"
            return "geographic_relation"
        if re.search(r"\b(?:rey|reina|principe|gobernador)\s+de$", before_norm):
            return "territorial_title"
        if re.search(r"\bdesde$", before_norm) or re.search(
            r"\b(?:salio|salieron|partio|partieron|vino|vinieron|procedia|procedian)\s+de$",
            before_norm,
        ):
            return "origin"
        if re.search(r"\bde$", before_norm):
            return "geographic_relation"
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
        if _norm(str(fact["answer"])) in {
            "primer",
            "primero",
            "primera",
            "segundo",
            "segunda",
            "tercer",
            "tercero",
            "tercera",
            "cuarto",
            "cuarta",
            "quinto",
            "quinta",
            "sexto",
            "sexta",
            "septimo",
            "septima",
            "octavo",
            "octava",
            "noveno",
            "novena",
            "decimo",
            "decima",
        }:
            return "order"
        signature = str(fact.get("_slot_signature") or "")
        if "subject" in signature:
            return "subject"
        if "predicate" in signature or "adjective" in signature:
            return "predicate"
        if "preposition" in signature:
            return "connector_object"
        if "object" in signature:
            return "object"
        if _norm(str(fact["answer"])).endswith("mente"):
            return "modifier"
        if re.search(
            r"\b(?:es|son|era|eran|fue|fueron|sera|seran|sea|sean|sido|"
            r"esta|estan|estaba|estaban|quedo|quedaron)$",
            before_norm,
        ):
            return "predicate"
        if re.search(
            r"\b(?:de|del|a|al|con|sin|por|para|hasta|sobre|entre|contra|"
            r"desde|hacia)(?:\s+(?:el|la|los|las|un|una|unos|unas))?$",
            before_norm,
        ):
            return "connector_object"
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
    result = result.translate(str.maketrans("", "", '«»“”"'))
    if contains_normalized_phrase(result, str(fact["answer"])):
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:masked_answer_leak")
    return result.strip()


_QUESTION_OPENINGS = {
    "actor": "¿quién realiza la acción descrita en",
    "recipient": "¿a quién se dirige la acción u orden expresada en",
    "named_entity": "¿qué nombre o designación completa la relación descrita en",
    "origin": "¿qué lugar funciona como origen en",
    "territorial_title": "¿qué territorio completa el título territorial presente en",
    "geographic_relation": "¿qué lugar completa la relación geográfica expresada en",
    "destination": "¿qué destino completa el movimiento descrito en",
    "location": "¿qué lugar completa el detalle geográfico de",
    "direction": "¿qué dirección geográfica precisa",
    "quantity": "¿qué dato cuantitativo precisa",
    "duration": "¿qué duración precisa el período descrito en",
    "order": "¿qué dato ordinal completa",
    "measure": "¿qué medida precisa",
    "action": "¿qué forma verbal completa la secuencia descrita en",
    "state": "¿qué estado completa la descripción presentada en",
    "change": "¿qué cambio completa la secuencia presentada en",
    "subject": "¿qué sujeto completa la relación literal expresada en",
    "object": "¿qué objeto completa la acción expresada en",
    "predicate": "¿qué término completa la construcción gramatical de",
    "modifier": "¿qué modificador precisa la descripción de",
    "connector_object": "¿qué concepto completa la relación introducida por la preposición en",
    "concept": "¿qué concepto completa la relación literal de",
    "cause": "¿qué causa declara explícitamente",
    "purpose": "¿qué propósito declara explícitamente",
    "consequence": "¿qué consecuencia declara explícitamente",
    "description": "¿qué descripción completa la relación literal de",
    "formulation": "¿qué formulación completa la relación literal de",
}

_IDENTITY_LABELS = {
    "actor": "quien realiza la acción",
    "recipient": "el destinatario",
    "named_entity": "el nombre o designación indicada",
    "origin": "el lugar de origen",
    "territorial_title": "el territorio asociado al título",
    "geographic_relation": "el lugar asociado en la relación",
    "destination": "el destino",
    "location": "el lugar indicado",
    "direction": "la dirección indicada",
    "quantity": "el dato cuantitativo",
    "duration": "la duración",
    "order": "el dato ordinal",
    "measure": "la medida",
    "action": "la forma verbal indicada",
    "state": "el estado descrito",
    "change": "el cambio descrito",
    "subject": "el sujeto de la relación",
    "object": "el objeto de la acción",
    "predicate": "el término de la construcción",
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
            opening = "¿qué detalle completa correctamente"
        question = f"Según {source_label}, {opening} «{evidence}»?"
    if contains_normalized_phrase(question, str(fact["answer"])):
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:context_question_answer_leak")
    return question, role, evidence


def render_contextual_identity(fact: dict[str, Any]) -> tuple[str, str, str]:
    role = derive_contextual_role(fact)
    evidence = mask_context_answer(fact)
    statement = (
        f"en la escena «{evidence}», {_IDENTITY_LABELS[role]} "
        f"es «{fact['answer']}»."
    )
    answer_occurrences = len(
        re.findall(
            rf"(?<!\w){re.escape(str(fact['answer']))}(?!\w)",
            statement,
        )
    )
    if answer_occurrences != 1:
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:identity_answer_count")
    return statement, role, evidence
