# Contextual Question Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar las 353 V/F verdaderas de presencia léxica y las 2,928 selecciones contextuales genéricas mediante papeles contextuales deterministas, sin alterar las 12,000 preguntas ni inventar relaciones.

**Architecture:** Un nuevo módulo puro clasificará el papel contextual de cada hecho y renderizará preguntas o afirmaciones desde texto literal enmascarado. `final_editorial.py` seguirá controlando selección, distractores y distribución, pero delegará el lenguaje contextual. La auditoría profunda recalculará el resultado esperado con el mismo contrato público y rechazará modos antiguos, fugas de respuesta o metadatos inconsistentes.

**Tech Stack:** Python 3.12, `unittest`, expresiones regulares estándar, generador JSON determinista, Node.js 24, Vitest, Playwright y Vercel.

**Spec:** `docs/superpowers/specs/2026-08-28-contextual-question-quality-design.md`

## Global Constraints

- Conservar exactamente 12,000 preguntas y 3,000 hechos.
- Conservar 3,000 preguntas por familia y 1,500 V/F por polaridad.
- No modificar el PDF, respuestas correctas ni referencias fuente.
- No introducir dependencias nuevas ni generación libre mediante modelos externos.
- No aumentar el banco por encima de 12,000 preguntas.
- Mantener rondas de 100 con 30 completar, 25 V/F y 45 selecciones.
- Mantener la reserva ciega fuera del entrenamiento normal.
- Toda relación debe derivarse de categoría, firma de ranura, contexto inmediato o relación explícita ya extraída.
- Una firma humana debe permanecer pendiente salvo decisión humana real.
- Preservar `.playwright-cli/`, `MaterialConexionBiblica (1).pdf` y `output/playwright/` como archivos del usuario no versionados.

---

### Task 1: Clasificador y renderizadores contextuales puros

**Files:**
- Create: `scripts/lib/contextual_roles.py`
- Create: `scripts/test_contextual_roles.py`

**Interfaces:**
- Consumes: un hecho `dict[str, Any]` con `answer`, `category`, `context`, `reference`, `relation_type`, `relation_prompt` y `_slot_signature` opcional.
- Produces: `derive_contextual_role(fact: dict[str, Any]) -> str`.
- Produces: `mask_context_answer(fact: dict[str, Any], marker: str = "[…]") -> str`.
- Produces: `render_contextual_question(fact: dict[str, Any]) -> tuple[str, str, str]`, donde la tupla es `(question, role, evidence)`.
- Produces: `render_contextual_identity(fact: dict[str, Any]) -> tuple[str, str, str]`, donde la tupla es `(statement, role, evidence)`.
- Produce constantes `ALLOWED_CONTEXTUAL_ROLES` y `GENERIC_CONTEXTUAL_FRAGMENT`.

- [ ] **Step 1: Leer las reglas de buenas pruebas**

Run: `Get-Content C:\Users\melar\.codex\plugins\cache\openai-curated-remote\superpowers\6.3.0\skills\test-driven-development\writing-good-tests.md`

Expected: el documento completo define pruebas conductuales, causa de fallo y uso de código real.

- [ ] **Step 2: Escribir las pruebas fallidas del clasificador**

Crear `scripts/test_contextual_roles.py` con casos reales y mínimos:

```python
from __future__ import annotations

import unittest

from scripts.lib.contextual_roles import (
    derive_contextual_role,
    mask_context_answer,
    render_contextual_identity,
    render_contextual_question,
)


def fact(**overrides):
    base = {
        "answer": "Daniel",
        "category": "person",
        "context": "Entonces el rey dijo a Daniel que respondiera.",
        "reference": "Daniel 2:16",
        "relation_type": "person",
        "relation_prompt": None,
        "_slot_signature": "person:proper",
    }
    return {**base, **overrides}


class ContextualRoleTests(unittest.TestCase):
    def test_classifies_explicit_and_syntactic_roles(self):
        self.assertEqual(derive_contextual_role(fact()), "recipient")
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="Jerusalén",
                    category="place",
                    context="vino a Jerusalén y la sitió",
                    _slot_signature="place:proper",
                )
            ),
            "destination",
        )
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="tres",
                    category="number",
                    context="durante tres años",
                    _slot_signature="number:number",
                )
            ),
            "duration",
        )
        self.assertEqual(
            derive_contextual_role(
                fact(
                    answer="la maldición",
                    category="phrase",
                    relation_type="consequence",
                    relation_prompt="¿Qué consecuencia cayó sobre Israel?",
                    context="cayó sobre nosotros la maldición",
                )
            ),
            "consequence",
        )

    def test_masks_only_the_answer_and_never_leaks_it(self):
        row = fact(answer="Daniel", context="Daniel respondió al rey.")
        self.assertEqual(mask_context_answer(row), "[…] respondió al rey.")
        self.assertNotIn("Daniel", mask_context_answer(row))

    def test_renders_role_aware_question_without_generic_copy(self):
        question, role, evidence = render_contextual_question(fact())
        self.assertEqual(role, "recipient")
        self.assertIn("¿A quién", question)
        self.assertIn("[…]", evidence)
        self.assertNotIn("corresponde específicamente a esta escena", question)
        self.assertNotIn("Daniel", question)

    def test_renders_contextual_identity_with_one_answer_occurrence(self):
        statement, role, evidence = render_contextual_identity(fact())
        self.assertEqual(role, "recipient")
        self.assertIn("Daniel", statement)
        self.assertEqual(statement.count("Daniel"), 1)
        self.assertNotIn("Daniel", evidence)
        self.assertNotIn("se menciona", statement.casefold())
        self.assertNotIn("se emplea", statement.casefold())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Ejecutar las pruebas y confirmar rojo**

Run: `python -m unittest scripts.test_contextual_roles`

Expected: ERROR por `ModuleNotFoundError: scripts.lib.contextual_roles`.

- [ ] **Step 4: Implementar el módulo mínimo**

Crear `scripts/lib/contextual_roles.py` con:

```python
from __future__ import annotations

import re
import unicodedata
from typing import Any

GENERIC_CONTEXTUAL_FRAGMENT = "¿qué opción corresponde específicamente a esta escena:"
ALLOWED_CONTEXTUAL_ROLES = {
    "actor", "recipient", "named_entity",
    "origin", "destination", "location", "direction",
    "quantity", "duration", "order", "measure",
    "action", "state", "change",
    "subject", "object", "predicate", "modifier", "connector_object", "concept",
    "cause", "purpose", "consequence", "description", "formulation",
}


def _norm(value: str) -> str:
    return " ".join(
        "".join(
            char for char in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(char)
        ).split()
    )


def contains_normalized_phrase(text: str, phrase: str) -> bool:
    return f" {_norm(phrase)} " in f" {_norm(text)} "


def _answer_span(fact: dict[str, Any]) -> tuple[str, str]:
    context = str(fact["context"])
    answer = str(fact["answer"])
    if context.count(answer) != 1:
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:context_answer_count")
    before, _, after = context.partition(answer)
    return before, after


def derive_contextual_role(fact: dict[str, Any]) -> str:
    relation = str(fact.get("relation_type") or "")
    if fact.get("relation_prompt") and relation in {
        "cause", "purpose", "consequence", "speaker", "recipient"
    }:
        return "actor" if relation == "speaker" else relation

    before, after = _answer_span(fact)
    before_norm = _norm(before)
    after_norm = _norm(after)
    category = fact["category"]
    if category == "person":
        if re.search(r"\b(?:a|al)\s*$", before_norm):
            return "recipient"
        if re.match(r"\s*(?:dijo|respondió|vino|hizo|habló|ordenó)\b", after_norm):
            return "actor"
        return "named_entity"
    if category == "place":
        if re.search(r"\b(?:a|hacia|hasta)\s*$", before_norm):
            return "destination"
        if re.search(r"\b(?:de|desde)\s*$", before_norm):
            return "origin"
        if _norm(str(fact["answer"])) in {"norte", "sur", "oriente", "poniente"}:
            return "direction"
        return "location"
    if category == "number":
        if re.match(r"\s*(?:años?|días?|semanas?|tiempos?)\b", after_norm):
            return "duration"
        if re.search(r"\b(?:primer|primero|segundo|tercer|tercero)\s*$", before_norm):
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
    before, after = _answer_span(fact)
    result = before + marker + after
    if contains_normalized_phrase(result, str(fact["answer"])):
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:masked_answer_leak")
    return result.strip()
```

Añadir los diccionarios y renderizadores completos:

```python
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
    if fact.get("relation_prompt"):
        question = str(fact["relation_prompt"])
    else:
        question = (
            f"Según {fact['reference']}, {_QUESTION_OPENINGS[role]} "
            f"«{evidence}»?"
        )
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
    if statement.count(str(fact["answer"])) != 1:
        raise ValueError(f"{fact.get('fact_id', '<sin-id>')}:identity_answer_count")
    return statement, role, evidence
```

- [ ] **Step 5: Ejecutar pruebas y confirmar verde**

Run: `python -m unittest scripts.test_contextual_roles`

Expected: 4 tests, OK.

- [ ] **Step 6: Añadir casos límite de fallback y errores**

Añadir pruebas que exijan:

```python
def test_uses_conservative_category_fallbacks(self):
    question, role, _ = render_contextual_question(
        fact(answer="sabiduría", category="term", context="recibió sabiduría", _slot_signature=None)
    )
    self.assertEqual(role, "concept")
    self.assertIn("concepto", question.casefold())

def test_rejects_ambiguous_or_leaking_context(self):
    with self.assertRaisesRegex(ValueError, "context_answer_count"):
        mask_context_answer(fact(context="Daniel habló con Daniel"))
```

Run: `python -m unittest scripts.test_contextual_roles`

Expected before implementation adjustment: FAIL en al menos uno de los dos nuevos contratos. Implementar solo las validaciones o etiquetas necesarias y repetir hasta OK.

- [ ] **Step 7: Commit**

```powershell
git add scripts/lib/contextual_roles.py scripts/test_contextual_roles.py
git commit -m "Add deterministic contextual role renderer"
```

---

### Task 2: Integrar preguntas de selección conscientes del papel

**Files:**
- Modify: `scripts/lib/final_editorial.py:12-15, 1930-1985`
- Modify: `scripts/test_final_editorial.py:345-395, 986-1035`
- Test: `scripts/test_contextual_roles.py`

**Interfaces:**
- Consumes de Task 1: `render_contextual_question(fact) -> tuple[str, str, str]` y `GENERIC_CONTEXTUAL_FRAGMENT`.
- Produces en cada selección contextual: `contextual_role: str`, `context_evidence: str`, pregunta sin la plantilla prohibida.
- Mantiene: `trap_type: "true_in_other_context"`, cuatro opciones, tres entradas en `why_distractors_fail`.

- [ ] **Step 1: Escribir la prueba de integración fallida**

En `test_each_family_obeys_its_visible_question_contract`, añadir:

```python
contextual_rows = [
    question for question in self.questions
    if question["family"] == "single_choice_contextual"
]
self.assertEqual(len(contextual_rows), 3000)
self.assertFalse(
    any(
        "¿qué opción corresponde específicamente a esta escena:"
        in question["question"].casefold()
        for question in contextual_rows
    )
)
self.assertTrue(
    all(question.get("contextual_role") for question in contextual_rows)
)
self.assertTrue(
    all(question.get("context_evidence") for question in contextual_rows)
)
```

Añadir una prueba separada:

```python
def test_contextual_questions_use_role_specific_language(self):
    openings = {
        question["contextual_role"]: question["question"]
        for question in self.questions
        if question["family"] == "single_choice_contextual"
    }
    for required in {"recipient", "destination", "duration", "action", "concept", "formulation"}:
        self.assertIn(required, openings)
```

- [ ] **Step 2: Ejecutar y confirmar rojo**

Run: `python -m unittest scripts.test_final_editorial.FinalEditorialTests.test_each_family_obeys_its_visible_question_contract scripts.test_final_editorial.FinalEditorialTests.test_contextual_questions_use_role_specific_language`

Expected: FAIL por 2,928 apariciones de la plantilla genérica y campos ausentes.

- [ ] **Step 3: Integrar el renderizador**

Importar:

```python
from scripts.lib.contextual_roles import render_contextual_question
```

Reemplazar la rama contextual por:

```python
elif family == "single_choice_contextual":
    question_text, contextual_role, context_evidence = render_contextual_question(fact)
    trap_type = "true_in_other_context"
```

Antes de `base.update`, inicializar `contextual_role = None` y `context_evidence = None`; incluir ambos campos en el diccionario para todas las familias. Para contextuales, conservar una explicación literal sin mostrar al usuario el identificador interno del papel:

```python
f"En el contexto exacto de {fact['reference']}, el detalle aplicable es "
f"«{fact['answer']}»: {_display_excerpt(fact['context'])}."
```

- [ ] **Step 4: Ejecutar pruebas y confirmar verde**

Run: `python -m unittest scripts.test_contextual_roles scripts.test_final_editorial.FinalEditorialTests.test_each_family_obeys_its_visible_question_contract scripts.test_final_editorial.FinalEditorialTests.test_contextual_questions_use_role_specific_language`

Expected: OK; 3,000 contextuales sin plantilla genérica.

- [ ] **Step 5: Ejecutar contratos de ocultamiento y distractores**

Run: `python -m unittest scripts.test_final_editorial.FinalEditorialTests.test_formulations_do_not_repeat_or_add_the_answer_inside_one_prompt scripts.test_final_editorial.FinalEditorialTests.test_distractor_signatures_do_not_mix_verbs_names_and_connectors`

Expected: OK.

- [ ] **Step 6: Commit**

```powershell
git add scripts/lib/final_editorial.py scripts/test_final_editorial.py
git commit -m "Render role-aware contextual questions"
```

---

### Task 3: Eliminar `atomic_presence` de V/F verdaderas

**Files:**
- Modify: `scripts/lib/final_editorial.py:1427-1440, 1790-1910, 1990-2045`
- Modify: `scripts/test_final_editorial.py:345-370, 570-710`
- Test: `scripts/test_contextual_roles.py`

**Interfaces:**
- Consumes de Task 1: `render_contextual_identity(fact) -> tuple[str, str, str]`.
- Produce: `statement_mode: "exact_source" | "contextual_identity"`; nunca `atomic_presence`.
- Produce para identidad: `contextual_role`, `context_evidence` y `truth_source_statement` iguales al resultado determinista del renderizador.
- Mantiene las V/F falsas en `exact_source` con los tres tipos seguros existentes.

- [ ] **Step 1: Escribir la prueba fallida de cero presencia**

En `test_true_false_is_balanced_unique_and_uses_only_safe_false_details`, añadir antes de validar las falsas:

```python
self.assertEqual(
    sum(row.get("statement_mode") == "atomic_presence" for row in rows),
    0,
)
self.assertEqual(
    sum(
        row.get("statement_mode") == "contextual_identity"
        for row in rows
        if row["correct_answer"] == "Verdadero"
    ),
    353,
)
```

En el contrato visible, cambiar la regla de V/F de términos y frases para permitir verdaderas contextuales, y exigir:

```python
if question.get("statement_mode") == "contextual_identity":
    self.assertEqual(question["correct_answer"], "Verdadero")
    self.assertIn("[…]", question["context_evidence"])
    self.assertNotIn(question["asserted_detail"], question["context_evidence"])
    self.assertEqual(question["statement"].count(f"«{question['asserted_detail']}»"), 1)
```

- [ ] **Step 2: Ejecutar y confirmar rojo**

Run: `python -m unittest scripts.test_final_editorial.FinalEditorialTests.test_true_false_is_balanced_unique_and_uses_only_safe_false_details`

Expected: FAIL, `atomic_presence` actual 353 en vez de 0.

- [ ] **Step 3: Sustituir el fallback del emparejamiento**

Cambiar `true_statement_options` a:

```python
def true_statement_options(
    fact: dict[str, Any], *, include_contextual_identity: bool = True
) -> list[str]:
    rows = []
    # conservar las dos opciones exactas actuales
    if include_contextual_identity:
        identity, _, _ = render_contextual_identity(fact)
        rows.append(identity)
    return rows
```

Actualizar las llamadas `include_atomic=False` a `include_contextual_identity=False`. Sustituir comparaciones con `_atomic_true_false_statement(fact)` por el primer elemento de `render_contextual_identity(fact)`. Conservar el algoritmo de emparejamiento: primero maximiza citas completas y después completa hasta 1,500 con identidades contextuales únicas.

- [ ] **Step 4: Emitir metadatos del nuevo modo**

En `append_true_false`, calcular:

```python
identity_statement, identity_role, identity_evidence = render_contextual_identity(fact)
if source_statement in exact_source_statements:
    statement_mode = "exact_source"
elif source_statement == identity_statement:
    statement_mode = "contextual_identity"
else:
    raise ValueError(f"Modo V/F desconocido: {fact['fact_id']}")
```

Guardar `contextual_role` y `context_evidence` solo para `contextual_identity`. Eliminar la posibilidad de producir `atomic_presence_substitution`; las falsas nunca reciben una identidad contextual.

- [ ] **Step 5: Ejecutar pruebas y confirmar verde**

Run: `python -m unittest scripts.test_contextual_roles scripts.test_final_editorial.FinalEditorialTests.test_true_false_is_balanced_unique_and_uses_only_safe_false_details scripts.test_final_editorial.FinalEditorialTests.test_each_family_obeys_its_visible_question_contract`

Expected: OK; 1,500 verdaderas únicas, 353 identidades y cero presencia.

- [ ] **Step 6: Ejecutar regresiones de V/F falsas**

Run: `python -m unittest scripts.test_final_editorial.FinalEditorialTests.test_known_broken_formulations_can_never_reenter_gold scripts.test_final_editorial.FinalEditorialTests.test_distractor_signatures_do_not_mix_verbs_names_and_connectors scripts.test_final_editorial.FinalEditorialTests.test_audit_and_coverage_gates_finish_at_zero`

Expected: OK; 1,500 falsas completas y cero plantillas inseguras.

- [ ] **Step 7: Commit**

```powershell
git add scripts/lib/final_editorial.py scripts/test_final_editorial.py
git commit -m "Replace lexical true-false checks with contextual identity"
```

---

### Task 4: Endurecer la auditoría profunda y competitiva

**Files:**
- Modify: `scripts/audit-final-bank-deep.py:10-30, 190-285`
- Modify: `scripts/lib/final_editorial.py:2380-2490`
- Modify: `scripts/lib/competitive-audit.mjs:140-210`
- Modify: `scripts/lib/competitive-audit.test.mjs`
- Modify: `scripts/test_final_editorial.py:1190-1235`

**Interfaces:**
- Consumes: `derive_contextual_role`, `render_contextual_identity`, `render_contextual_question`, `ALLOWED_CONTEXTUAL_ROLES`, `GENERIC_CONTEXTUAL_FRAGMENT`.
- Produce: auditoría profunda que recalcula texto y metadatos esperados.
- Produce: banderas competitivas `generic_contextual_prompt`, `atomic_true_false`, `contextual_role_mismatch`, `context_evidence_leak`.

- [ ] **Step 1: Escribir pruebas fallidas del auditor competitivo**

En `competitive-audit.test.mjs`, añadir una fila base y cuatro pruebas:

```javascript
const contextualBase = {
  id: "CTX",
  family: "single_choice_contextual",
  question: "Según Daniel 7:1, ¿quién realiza la acción descrita en «[…] respondió»?",
  options: ["Daniel", "Gabriel", "Miguel", "Darío"],
  correct_option: 0,
  correct_answer: "Daniel",
  source_quote: "Daniel respondió",
  trap_type: "true_in_other_context",
  contextual_role: "actor",
  context_evidence: "[…] respondió",
  why_distractors_fail: {
    Gabriel: "Es verdadero en Daniel 8:16, pero no aquí.",
    Miguel: "Es verdadero en Daniel 10:13, pero no aquí.",
    Darío: "Es verdadero en Daniel 6:1, pero no aquí.",
  },
}

it("flags generic contextual prompts", () => {
  const findings = exhaustiveRiskFlags({
    ...contextualBase,
    family: "single_choice_contextual",
    question: "Según Daniel 7:1, ¿qué opción corresponde específicamente a esta escena: «[…]»?",
  })
  expect(findings).toContain("generic_contextual_prompt")
})

it("flags atomic true-false templates", () => {
  const findings = exhaustiveRiskFlags({
    ...contextualBase,
    family: "true_false",
    statement_mode: "atomic_presence",
  })
  expect(findings).toContain("atomic_true_false")
})

it("flags a contextual row without a role", () => {
  const findings = exhaustiveRiskFlags({
    ...contextualBase,
    family: "single_choice_contextual",
    contextual_role: null,
    context_evidence: "Daniel respondió al rey",
  })
  expect(findings).toContain("contextual_role_mismatch")
})

it("flags contextual evidence that reveals the answer", () => {
  const findings = exhaustiveRiskFlags({
    ...contextualBase,
    family: "single_choice_contextual",
    contextual_role: "actor",
    context_evidence: "Daniel respondió al rey",
    correct_answer: "Daniel",
  })
  expect(findings).toContain("context_evidence_leak")
})
```

- [ ] **Step 2: Ejecutar y confirmar rojo**

Run: `npx vitest run scripts/lib/competitive-audit.test.mjs`

Expected: FAIL porque las cuatro banderas no existen.

- [ ] **Step 3: Implementar las banderas mínimas**

Ampliar `exhaustiveRiskFlags(row)` para añadir exactamente las cuatro condiciones. La evidencia se compara con `normalizeText` y límites de frase, y solo en familias contextuales o modo `contextual_identity`. Añadir las cuatro claves a `RISK_WEIGHT` con peso 100 para que cualquier regresión quede priorizada como bloqueador editorial.

- [ ] **Step 4: Ejecutar pruebas y confirmar verde**

Run: `npx vitest run scripts/lib/competitive-audit.test.mjs`

Expected: todos los tests del archivo pasan.

- [ ] **Step 5: Escribir la prueba fallida de auditoría profunda**

En `test_audit_and_coverage_gates_finish_at_zero`, añadir a las claves exigidas en cero:

```python
"atomic_true_false_templates",
"generic_contextual_prompts",
"contextual_role_errors",
"context_evidence_leaks",
```

Expected al ejecutar la prueba: FAIL por claves ausentes o conteos anteriores.

- [ ] **Step 6: Implementar validación profunda**

Importar en `final_editorial.py` y `audit-final-bank-deep.py`:

```python
from scripts.lib.contextual_roles import (
    GENERIC_CONTEXTUAL_FRAGMENT,
    contains_normalized_phrase,
    render_contextual_identity,
    render_contextual_question,
)
```

En la iteración de `audit_final_bank`, recalcular el contrato en vez de confiar en los metadatos almacenados:

```python
atomic_true_false_templates = 0
generic_contextual_prompts = 0
contextual_role_errors = 0
context_evidence_leaks = 0

for row in questions:
    fact = facts_by_id[row["fact_id"]]
    if row.get("statement_mode") == "atomic_presence":
        atomic_true_false_templates += 1

    if row["family"] == "single_choice_contextual":
        expected_question, expected_role, expected_evidence = render_contextual_question(fact)
        if GENERIC_CONTEXTUAL_FRAGMENT in _norm(row["question"]):
            generic_contextual_prompts += 1
        if (
            row["question"] != expected_question
            or row.get("contextual_role") != expected_role
            or row.get("context_evidence") != expected_evidence
        ):
            contextual_role_errors += 1
        if contains_normalized_phrase(
            str(row.get("context_evidence") or ""), str(row["correct_answer"])
        ):
            context_evidence_leaks += 1

    if row.get("statement_mode") == "contextual_identity":
        expected_statement, expected_role, expected_evidence = render_contextual_identity(fact)
        if (
            row["statement"] != expected_statement
            or row.get("truth_source_statement") != expected_statement
            or row.get("contextual_role") != expected_role
            or row.get("context_evidence") != expected_evidence
        ):
            contextual_role_errors += 1
        if contains_normalized_phrase(
            str(row.get("context_evidence") or ""), str(row["asserted_detail"])
        ):
            context_evidence_leaks += 1
```

Incorporar los cuatro valores al objeto de auditoría devuelto. En `audit-final-bank-deep.py`, repetir la recomputación por ID y llamar a `fail(question_id, code, details)` ante cualquier diferencia, para que un JSON editado manualmente no pueda aprobar solo por declarar metadatos plausibles.

- [ ] **Step 7: Ejecutar auditorías unitarias**

Run: `python -m unittest scripts.test_final_editorial.FinalEditorialTests.test_audit_and_coverage_gates_finish_at_zero`

Expected: OK y las cuatro claves en cero.

Run: `python scripts/audit-final-bank-deep.py`

Expected antes de regenerar: FAIL sobre el banco público antiguo, demostrando que la puerta detecta contenido obsoleto.

- [ ] **Step 8: Commit**

```powershell
git add scripts/audit-final-bank-deep.py scripts/lib/final_editorial.py scripts/lib/competitive-audit.mjs scripts/lib/competitive-audit.test.mjs scripts/test_final_editorial.py
git commit -m "Audit contextual roles and identity statements"
```

---

### Task 5: Regenerar el banco y revisar la muestra de alto riesgo

**Files:**
- Modify generated: `public/banks/final-2026/**`
- Modify generated: `reports/final-competitive-audit.json`
- Modify generated: `reports/final-competitive-audit-sample.md`
- Modify generated: `reports/final-exhaustive-audit-ledger.json`
- Modify generated: `reports/final-exhaustive-review-packet.json`
- Modify: `reports/final-ai-editorial-review.md`

**Interfaces:**
- Consumes: generador y auditores de Tasks 1-4.
- Produce: banco público determinista y reportes con huellas actualizadas.

- [ ] **Step 1: Regenerar el banco**

Run: `npm run build:final-bank`

Expected: JSON con `facts: 3000`, `gold_questions: 12000`, `unresolved: 0`.

- [ ] **Step 2: Ejecutar auditoría profunda**

Run: `npm run audit:final:deep`

Expected: `questions: 12000`, `errors: 0`.

- [ ] **Step 3: Medir los contratos editoriales nuevos**

Run:

```powershell
node --input-type=module -e "import fs from 'node:fs';import path from 'node:path';const d='public/banks/final-2026/questions';const q=fs.readdirSync(d).flatMap(f=>JSON.parse(fs.readFileSync(path.join(d,f),'utf8')));const tf=q.filter(x=>x.family==='true_false');const c=q.filter(x=>x.family==='single_choice_contextual');console.log(JSON.stringify({total:q.length,atomic:tf.filter(x=>x.statement_mode==='atomic_presence').length,identities:tf.filter(x=>x.statement_mode==='contextual_identity').length,generic:c.filter(x=>x.question.includes('¿qué opción corresponde específicamente a esta escena:')).length,roles:c.filter(x=>x.contextual_role).length},null,2));"
```

Expected:

```json
{
  "total": 12000,
  "atomic": 0,
  "identities": 353,
  "generic": 0,
  "roles": 3000
}
```

- [ ] **Step 4: Regenerar auditorías competitiva y exhaustiva**

Run: `npm run audit:competitive`

Expected: `sample_size: 108`, `strata: 36`, `automatic_flags: []`.

Run: `npm run audit:exhaustive`

Expected: `bank_questions: 12000`, `automatic_attention: 0`, `review_packet: 600`, `pending_human: 12000`.

- [ ] **Step 5: Revisar muestras legibles por estrato**

Abrir `reports/final-competitive-audit-sample.md` y comprobar las 36 V/F falsas, 36 completar y 36 contextuales. Registrar cualquier frase antinatural como prueba de regresión antes de corregirla. La revisión debe comprobar pregunta, cuatro opciones, respuesta, fuente y explicación de cada distractor.

- [ ] **Step 6: Actualizar el informe IA**

En `reports/final-ai-editorial-review.md`, reemplazar el límite anterior por evidencia nueva:

```markdown
- V/F verdaderas de presencia léxica: 0.
- Contextuales con plantilla universal: 0.
- Identidades contextuales trazables: 353.
- Preguntas contextuales con papel explícito: 3,000.
```

Conservar la declaración de que la revisión IA no sustituye firma humana.

- [ ] **Step 7: Commit**

```powershell
git add public/banks/final-2026 reports/final-competitive-audit.json reports/final-competitive-audit-sample.md reports/final-exhaustive-audit-ledger.json reports/final-exhaustive-review-packet.json reports/final-ai-editorial-review.md
git commit -m "Regenerate role-aware final question bank"
```

---

### Task 6: Verificación integral, despliegue y producción

**Files:**
- Verify only: repository and production resources.
- Do not add: `.playwright-cli/`, `MaterialConexionBiblica (1).pdf`, `output/playwright/`.

**Interfaces:**
- Consumes: banco y código de Tasks 1-5.
- Produces: commits en `main`, dos despliegues Vercel exitosos y producción byte-equivalente.

- [ ] **Step 1: Ejecutar suite Python completa**

Run: `python -m unittest scripts.test_contextual_roles scripts.test_final_editorial`

Expected: todos los tests pasan en una sola ejecución, sin fallos ni errores.

- [ ] **Step 2: Ejecutar suite web completa**

Run: `npm test`

Expected: al menos 62 archivos y 339 pruebas aprobadas; cero fallos.

- [ ] **Step 3: Compilar y revisar lint**

Run: `npm run build`

Expected: `built` y código de salida 0; solo se admite la advertencia existente de chunk mayor de 500 kB.

Run: `npm run lint`

Expected: salida 0 sin errores.

- [ ] **Step 4: Repetir auditorías finales**

Run: `npm run audit:final:deep`

Expected: `errors: 0`.

Run: `npm run audit:competitive`

Expected: `automatic_flags: []`.

- [ ] **Step 5: Revisar diff y estado**

Run: `git diff --check`

Expected: sin salida.

Run: `git status --short`

Expected: solo archivos intencionados o los tres artefactos del usuario no versionados.

- [ ] **Step 6: Commit de cualquier ajuste final de verificación**

Si la verificación exigió una corrección, esa corrección debe haber seguido un nuevo ciclo rojo-verde. Después:

```powershell
git add scripts/lib/contextual_roles.py scripts/test_contextual_roles.py scripts/lib/final_editorial.py scripts/test_final_editorial.py scripts/audit-final-bank-deep.py scripts/lib/competitive-audit.mjs scripts/lib/competitive-audit.test.mjs public/banks/final-2026 reports/final-ai-editorial-review.md reports/final-competitive-audit.json reports/final-competitive-audit-sample.md reports/final-exhaustive-audit-ledger.json reports/final-exhaustive-review-packet.json
git commit -m "Finalize contextual quality verification"
```

Si no hubo cambios, omitir este commit.

- [ ] **Step 7: Push y despliegue**

Run: `git push origin main`

Expected: `main -> main` con el commit final.

Consultar el estado conectado:

```powershell
gh api repos/AugustoMelara-Dev/conexion-biblica-2026/commits/HEAD/status --jq '{state: .state, statuses: [.statuses[] | {context, state, description}]}'
```

Expected: ambos contextos Vercel en `success`. Si el token CLI está vencido, no intentar falsificar éxito: esperar la integración GitHub conectada.

- [ ] **Step 8: Auditar contenido público**

Run: `npm run audit:production`

Expected: `resources: 24`, `failures: []` para `https://conexion-biblica-2026.vercel.app`.

- [ ] **Step 9: Ejecutar matriz multinavegador en producción**

Run:

```powershell
$env:PLAYWRIGHT_BASE_URL='https://conexion-biblica-2026.vercel.app'; npx playwright test
```

Expected: todos los casos activos pasan en Chromium, Firefox y WebKit, escritorio y móvil; las omisiones corresponden únicamente a condiciones explícitas de proyecto o viewport.

- [ ] **Step 10: Handoff final**

Informar:

- commit final y URL pública;
- conteos `atomic = 0`, `generic = 0`, `identities = 353`, `roles = 3000`;
- pruebas Python, Vitest, build, lint, auditorías y Playwright;
- permanencia de 12,000 firmas humanas pendientes;
- cualquier limitación real restante, sin utilizar “perfección absoluta”.
