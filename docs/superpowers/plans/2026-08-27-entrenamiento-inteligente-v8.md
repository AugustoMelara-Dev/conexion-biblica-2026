# Entrenamiento Inteligente V8 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar un banco V8 de 8,000 preguntas útiles y un entrenador que seleccione, repare y reprograme conocimiento por `fact_id` sin evaluar páginas, párrafos ni referencias.

**Architecture:** El pipeline Python extrae 2,000 hechos verificables y genera cuatro variantes por hecho; la antigua selección contextual de referencias se reemplaza por selección contextual de contenido. En el navegador, el selector agrupa primero por hecho, una cola persistida programa reparaciones y recuperaciones, y la ronda materializa una variante distinta sin perder estabilidad al recargar.

**Tech Stack:** Python 3, PyMuPDF, TypeScript, React 19, IndexedDB, Vitest, Testing Library, Playwright, Vite, service worker y Vercel.

**Spec:** `docs/superpowers/specs/2026-08-27-entrenamiento-inteligente-v8-design.md`

## Global Constraints

- Fuente única: `MaterialConexionBiblica (1).pdf`, SHA-256 `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`.
- Daniel usa exclusivamente RVR1995 contenida en el PDF; PR39–44 conserva la terminología del PDF.
- Ninguna respuesta u opción correcta puede ser una página, párrafo, referencia bíblica o ubicación física.
- La interfaz expone solo completar, Verdadero/Falso y selección única.
- Una ronda normal contiene un solo `fact_id`; solo una reparación posterior a un error puede repetirlo.
- Los cambios preservan historial, reportes, favoritos, dominio, ronda activa y uso ciego existentes.
- Cada cambio de comportamiento sigue RED → GREEN → REFACTOR y recibe un commit enfocado.

---

## File map

- `scripts/lib/final_relations.py`: detecta y modela relaciones expresas de causa, consecuencia, habla, destinatario, comparación y secuencia.
- `scripts/lib/final_editorial.py`: selecciona 2,000 hechos, genera cuatro variantes de contenido y asigna dificultad/reserva.
- `scripts/audit-final-bank-deep.py`: bloquea referencias como respuesta, ubicación editorial, duplicados semánticos y cuotas V8.
- `scripts/test_final_relations.py`, `scripts/test_final_editorial.py`: contrato editorial y de relaciones.
- `src/domain/fact-session-selection.ts`: selección por hecho, mezcla 30/25/45 y novedad entre rondas.
- `src/domain/retrieval-queue.ts`: máquina de estados de reparación y recuperación.
- `src/domain/dynamic-question.ts`: materialización estable con otra variante y combinación de distractores.
- `src/domain/types.ts`: tipos V8, ciclo por hechos y cola de recuperación.
- `src/storage/db.ts`, `src/domain/backup.ts`: IndexedDB V5, repositorio y respaldo de la cola.
- `src/App.tsx`, `src/app/app-state.tsx`: orquestación de selección y persistencia.
- `src/components/quiz-page.tsx`: inserción de reparación y explicación del motivo de aparición.
- `src/components/session-builder-page.tsx`, `src/components/massive-training-hub.tsx`, `src/components/results-page.tsx`: jerarquía de práctica y nuevas acciones.
- `src/update-manager.ts`, `src/main.tsx`, `public/sw.js`: actualización segura sin borrar datos.
- `e2e/training-v8.spec.ts`: aceptación de rondas, reparación, novedad, actualización y móvil.

---

### Task 1: Prohibir preguntas de ubicación editorial

**Files:**
- Modify: `scripts/test_final_editorial.py`
- Modify: `scripts/audit-final-bank-deep.py`
- Modify: `scripts/lib/final_editorial.py`

**Interfaces:**
- Consumes: preguntas JSON V7 con `family`, `question`, `options`, `correct_answer`, `reference`.
- Produces: `is_location_answer(question: dict) -> bool` y una familia `single_choice_contextual` cuya respuesta es contenido.

- [ ] **Step 1: Escribir pruebas que reproduzcan el defecto**

Añadir pruebas que carguen una pregunta con respuesta `Daniel 7:19` y otra con `PR43, p. 52, párrafo 3`, y exijan rechazo. Añadir una prueba de generación que exija que la selección contextual conserve `fact["answer"]` como `correct_answer`:

```python
def test_contextual_selection_never_answers_with_a_reference(self):
    questions, _ = self.editorial.generate_gold_questions(self.facts)
    contextual = [q for q in questions if q["family"] == "single_choice_contextual"]
    self.assertTrue(contextual)
    self.assertTrue(all(q["correct_answer"] == self.fact_by_id[q["fact_id"]]["answer"] for q in contextual))
    self.assertFalse(any(re.fullmatch(r"Daniel \\d+:\\d+|PR\\d+, p\\. \\d+, párrafo \\d+", option) for q in contextual for option in q["options"]))
```

- [ ] **Step 2: Ejecutar RED**

Run: `python -m unittest scripts.test_final_editorial -v`

Expected: FAIL porque V7 usa referencias como las cuatro opciones contextuales.

- [ ] **Step 3: Implementar el contrato mínimo**

En `final_editorial.py`, reemplazar el bloque que crea `reference_rows` por distractores de contenido compatibles. El enunciado debe usar `fact["context"]` como escena y `fact["answer"]` como respuesta; `accepted_answers`, `correct_answer` y `option_category` deben conservar el contenido. En el auditor, añadir:

```python
LOCATION_ANSWER_RE = re.compile(r"^(?:Daniel \\d+:\\d+|PR\\d+, p\\. \\d+(?:, párrafo \\d+)?)$")

def is_location_answer(question: dict) -> bool:
    values = [question.get("correct_answer", ""), *question.get("options", [])]
    return any(LOCATION_ANSWER_RE.fullmatch(str(value).strip()) for value in values)
```

También rechazar enunciados que pregunten `en cuál referencia`, `en qué versículo`, `en qué página` o `en qué párrafo`.

- [ ] **Step 4: Ejecutar GREEN y auditoría focalizada**

Run: `python -m unittest scripts.test_final_editorial -v`

Expected: PASS.

Run: `python scripts/build-final-bank.py`

Expected: generación completa sin opciones de referencia.

- [ ] **Step 5: Commit**

```powershell
git add scripts/test_final_editorial.py scripts/audit-final-bank-deep.py scripts/lib/final_editorial.py public/banks/final-2026
git commit -m "fix: replace reference-location questions"
```

### Task 2: Extraer relaciones útiles y ampliar a 2,000 hechos

**Files:**
- Create: `scripts/lib/final_relations.py`
- Create: `scripts/test_final_relations.py`
- Modify: `scripts/lib/final_editorial.py`
- Modify: `scripts/build-final-bank.py`
- Modify: `scripts/audit-final-bank-deep.py`
- Regenerate: `public/banks/final-2026/**`

**Interfaces:**
- Consumes: unidades de `source_inventory.json` con texto, capítulo, referencia y listas extraídas.
- Produces: `derive_relation_candidates(unit: dict, previous_unit: dict | None, next_unit: dict | None) -> list[dict]` con `answer`, `prompt`, `semantic_skill`, `source_quote`, `relation_type`, `score`.

- [ ] **Step 1: Escribir pruebas de relaciones literales**

Crear casos tomados del PDF para:

```python
def test_extracts_explicit_cause_without_external_inference():
    unit = make_unit("Daniel 9:16", "A causa de nuestros pecados y de las maldades de nuestros padres, Jerusalén y tu pueblo son el oprobio de todos en derredor nuestro.")
    rows = derive_relation_candidates(unit, None, None)
    cause = next(row for row in rows if row["semantic_skill"] == "cause")
    assert cause["answer"] == "nuestros pecados y de las maldades de nuestros padres"
    assert cause["source_quote"] == unit["full_text"]

def test_rejects_relation_when_both_sides_are_not_explicit():
    unit = make_unit("Daniel 7:1", "Daniel tuvo un sueño y visiones de su cabeza mientras estaba en su cama.")
    assert not [row for row in derive_relation_candidates(unit, None, None) if row["semantic_skill"] in {"cause", "consequence"}]
```

Añadir casos igualmente concretos para consecuencia, hablante/destinatario y secuencia usando texto literal del inventario; cada caso debe comparar `answer`, `semantic_skill` y `source_quote`, no solo contar candidatos.

Las pruebas deben exigir que cada candidato incluya la cita que contiene ambos lados de la relación y que la respuesta aparezca una sola vez en ella.

- [ ] **Step 2: Ejecutar RED**

Run: `python -m unittest scripts.test_final_relations -v`

Expected: ERROR por módulo inexistente.

- [ ] **Step 3: Implementar detectores conservadores**

Implementar `RelationCandidate` como `TypedDict` y patrones cerrados:

```python
CAUSE_MARKERS = ("porque", "por cuanto", "a causa de", "para que")
CONSEQUENCE_MARKERS = ("por tanto", "entonces", "de modo que", "así que")

class RelationCandidate(TypedDict):
    answer: str
    prompt: str
    semantic_skill: Literal["cause", "consequence", "speaker", "recipient", "sequence", "comparison", "scene"]
    source_quote: str
    relation_type: str
    score: float
```

Solo emitir candidato cuando pregunta y respuesta queden resueltas por la misma unidad o por dos unidades narrativas contiguas con sujetos explícitos. Registrar el motivo de rechazo para relaciones incompletas.

- [ ] **Step 4: Seleccionar exactamente 2,000 hechos**

Modificar cuotas a:

```python
FACT_QUOTAS = {
    "DAN1": 60, "DAN2": 90, "DAN3": 65, "DAN4": 75, "DAN5": 60, "DAN6": 60,
    "DAN7": 150, "DAN8": 150, "DAN9": 150, "DAN10": 90, "DAN11": 180, "DAN12": 90,
    "PR39": 120, "PR40": 130, "PR41": 120, "PR42": 120, "PR43": 160, "PR44": 130,
}
```

Intercalar hechos atómicos y relacionales; ningún capítulo podrá cubrir su cuota con más de 55 % de términos aislados. Mantener al menos un hecho por unidad salvo la exclusión editorial documentada.

- [ ] **Step 5: Generar cuatro capacidades por hecho**

Generar exactamente 8,000 preguntas: 2,000 directas, 2,000 completar, 2,000 V/F y 2,000 selecciones contextuales de contenido. `semantic_skill` debe reflejar la relación del hecho y `why_distractors_fail` explicar el contexto de cada opción.

- [ ] **Step 6: Ejecutar GREEN y auditoría completa**

Run: `python -m unittest discover -s scripts -p "test_*.py"`

Expected: PASS.

Run: `python scripts/build-final-bank.py`

Expected: `gold_questions=8000`, `unique_facts=2000`, `uncovered_source_units=0`.

Run: `python scripts/audit-final-bank-deep.py`

Expected: `errors=0`, ninguna respuesta de ubicación y cuotas exactas.

- [ ] **Step 7: Revisar visualmente OCR dudoso y muestreo adversarial**

Renderizar únicamente las páginas listadas en `source_extraction_issues.json`; comparar cada palabra dudosa con el PDF. Revisar al menos cinco preguntas de cada familia por capítulo y las diez preguntas con mayor similitud semántica de cada capítulo. Corregir la fuente de extracción solo ante error visual evidente y volver a ejecutar Step 6.

- [ ] **Step 8: Commit**

```powershell
git add scripts/lib/final_relations.py scripts/test_final_relations.py scripts/lib/final_editorial.py scripts/build-final-bank.py scripts/audit-final-bank-deep.py public/banks/final-2026
git commit -m "feat: expand verified gold bank to eight thousand"
```

### Task 3: Seleccionar por hecho y cumplir la mezcla 30/25/45

**Files:**
- Create: `src/domain/fact-session-selection.ts`
- Create: `src/domain/fact-session-selection.test.ts`
- Modify: `src/domain/adaptive-session.ts`
- Modify: `src/domain/session-selection.ts`
- Modify: `src/domain/session-selector.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Consumes: `Question[]`, `QuestionExposure[]`, `FactMastery[]`, `FactCoverageCycle | null`, configuración y semilla.
- Produces: `selectFactSession(input: FactSessionInput): FactSessionSelection` y ciclo actualizado.

- [ ] **Step 1: Escribir pruebas del selector deseado**

```typescript
it("elige 100 factId distintos con mezcla 30/25/45", () => {
  const questions = makeQuestionFamilies(120)
  const result = selectFactSession({ questions, exposures: [], mastery: [], count: 100, weakChapters: [], includeBlind: false, seed: 7, cycle: null })
  expect(new Set(result.questions.map((q) => q.factId)).size).toBe(100)
  expect(result.questions.filter((q) => q.type === "fill_blank")).toHaveLength(30)
  expect(result.questions.filter((q) => q.type === "true_false")).toHaveLength(25)
  expect(result.questions.filter((q) => q.type === "single_choice")).toHaveLength(45)
})

it("la segunda tanda consume hechos distintos mientras quedan pendientes", () => {
  const questions = makeQuestionFamilies(220)
  const first = selectFactSession({ questions, exposures: [], mastery: [], count: 100, weakChapters: [], includeBlind: false, seed: 7, cycle: null })
  const second = selectFactSession({ questions, exposures: [], mastery: [], count: 100, weakChapters: [], includeBlind: false, seed: 8, cycle: first.cycle })
  const firstFacts = new Set(first.questions.map((q) => q.factId))
  expect(second.questions.every((q) => !firstFacts.has(q.factId!))).toBe(true)
})

it("protege todos los hechos de blind pool", () => {
  const questions = makeQuestionFamilies(120).map((q, index) => index < 20 ? { ...q, blindFinalPool: true } : q)
  const result = selectFactSession({ questions, exposures: [], mastery: [], count: 50, weakChapters: [], includeBlind: false, seed: 9, cycle: null })
  expect(result.questions.every((q) => !q.blindFinalPool)).toBe(true)
})
```

Para la variante menos expuesta, registrar una exposición para tres de las cuatro variantes de `fact-1` y exigir que el selector devuelva la cuarta.

- [ ] **Step 2: Ejecutar RED**

Run: `npm test -- src/domain/fact-session-selection.test.ts --run`

Expected: FAIL por módulo inexistente.

- [ ] **Step 3: Añadir tipos de ciclo por hecho**

```typescript
export type FactCoverageCycle = {
  poolKey: string
  cycleId: string
  remainingFactIds: string[]
  seenFactIds: string[]
  totalFacts: number
  createdAt: number
  updatedAt: number
}

export type SelectionReason = "new" | "due" | "error" | "slow" | "weak" | "blind"
```

Mantener lectura compatible de `CoverageCycle`; migrar sus question keys a hechos al cargar, sin modificar evidencias.

- [ ] **Step 4: Implementar agrupación y asignación**

Agrupar con `Map<factId, Question[]>`; elegir hechos por cuotas de novedad 60/20/10/10; reservar los tipos 30/25/45 antes de materializar variantes. Para V/F seleccionar 12 o 13 verdaderas y completar el resto con falsas. El resultado debe incluir `reasonByFact: Map<string, SelectionReason>`.

- [ ] **Step 5: Integrar selectores existentes**

Hacer que `selectAdaptiveSession`, `selectCoverageCycle` y `selectSessionQuestions` deleguen a la selección por hechos para `final-v7`. Mantener la ruta anterior únicamente para bancos legado.

- [ ] **Step 6: Ejecutar GREEN y regresión**

Run: `npm test -- src/domain/fact-session-selection.test.ts src/domain/adaptive-session.test.ts src/domain/session-selection.test.ts --run`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/domain/fact-session-selection.ts src/domain/fact-session-selection.test.ts src/domain/adaptive-session.ts src/domain/session-selection.ts src/domain/session-selector.ts src/domain/types.ts
git commit -m "feat: select training rounds by fact"
```

### Task 4: Persistir reparaciones y recuperaciones

**Files:**
- Create: `src/domain/retrieval-queue.ts`
- Create: `src/domain/retrieval-queue.test.ts`
- Modify: `src/domain/types.ts`
- Modify: `src/storage/db.ts`
- Modify: `src/storage/storage.test.ts`
- Modify: `src/domain/backup.ts`
- Modify: `src/domain/backup.test.ts`
- Modify: `src/app/app-state.tsx`

**Interfaces:**
- Produces: `RetrievalQueueItem`, `scheduleFailure`, `scheduleRepairSuccess`, `takeDueRetrievals` y repositorio `retrievalQueue`.

- [ ] **Step 1: Escribir pruebas de estados y persistencia**

```typescript
it("programa reparación con separación entre 8 y 15", () => {
  const item = scheduleFailure({ factId: "DAN7-V007-F01", variantId: "direct", type: "single_choice", semanticSkill: "direct", now: 1_000 })
  expect(item.stage).toBe("repair")
  expect(item.minQuestionGap).toBeGreaterThanOrEqual(8)
  expect(item.minQuestionGap).toBeLessThanOrEqual(15)
  expect(item.dueAt).toBeNull()
})

it("una reparación acertada vence entre 45 y 90 minutos", () => {
  const repaired = scheduleRepairSuccess(scheduleFailure({ factId: "DAN7-V007-F01", variantId: "direct", type: "single_choice", semanticSkill: "direct", now: 1_000 }), 10_000)
  expect(repaired.stage).toBe("hour")
  expect(repaired.dueAt!).toBeGreaterThanOrEqual(10_000 + 45 * 60_000)
  expect(repaired.dueAt!).toBeLessThanOrEqual(10_000 + 90 * 60_000)
})

it("no marca dominio por una reparación inmediata", () => {
  const mastery = applyFactEvidence(emptyFactMastery("DAN7-V007-F01"), repairEvidence)
  expect(mastery.state).not.toBe("mastered")
  expect(mastery.state).toBe("repaired")
})
```

Añadir una prueba con reloj fijo para las transiciones `hour → six_hour → next_day → contextual`; una prueba `fake-indexeddb` que abra V4 con progreso, actualice a V5 y compruebe ambos stores; y una prueba de round-trip del respaldo V3 con un elemento de cola.

- [ ] **Step 2: Ejecutar RED**

Run: `npm test -- src/domain/retrieval-queue.test.ts src/storage/storage.test.ts src/domain/backup.test.ts --run`

Expected: FAIL por tipos y store inexistentes.

- [ ] **Step 3: Implementar la máquina de estados**

```typescript
export type RetrievalStage = "repair" | "hour" | "six_hour" | "next_day" | "contextual"
export type RetrievalQueueItem = {
  factId: string
  stage: RetrievalStage
  dueAt: number | null
  minQuestionGap: number | null
  previousVariantId: string
  previousType: QuestionType
  attemptedSkills: string[]
  updatedAt: number
}
```

Usar separación determinista `8 + hash(factId) % 8`; hora `45 + hash(factId + stage) % 46` minutos; seis horas `6 + hash(factId + "six_hour") % 5` horas; día siguiente `18 + hash(factId + "next_day") % 13` horas.

- [ ] **Step 4: Añadir IndexedDB V5 y repositorio**

Crear store `retrievalQueue` con key `factId` e índices `stage` y `dueAt`; añadir `list`, `put`, `remove` y `takeDue(now)`. Incluirlo en `resetAll`, carga inicial y respaldo `backupVersion: "3.0"`; migrar V1/V2 a V3 con cola vacía.

- [ ] **Step 5: Integrar `recordAnswer`**

Al fallar, persistir `repair`; al acertar con `afterFeedback`, pasar a `hour`; al acertar una recuperación diferida, avanzar de etapa; nunca alterar dominio por una reparación inmediata.

- [ ] **Step 6: Ejecutar GREEN**

Run: `npm test -- src/domain/retrieval-queue.test.ts src/storage/storage.test.ts src/domain/backup.test.ts src/app/app-state.test.tsx --run`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/domain/retrieval-queue.ts src/domain/retrieval-queue.test.ts src/domain/types.ts src/storage/db.ts src/storage/storage.test.ts src/domain/backup.ts src/domain/backup.test.ts src/app/app-state.tsx
git commit -m "feat: persist spaced retrieval queue"
```

### Task 5: Reintentar con una variante auténtica

**Files:**
- Modify: `src/domain/dynamic-question.ts`
- Modify: `src/domain/dynamic-question.test.ts`
- Modify: `src/domain/session-selector.ts`
- Modify: `src/components/quiz-page.tsx`
- Modify: `src/components/quiz-page.test.tsx`
- Modify: `src/storage/final-bank.ts`

**Interfaces:**
- Produces: `selectRetryVariant(family, previous, exposures, attemptedSkills, seed) -> Question | undefined`.

- [ ] **Step 1: Escribir prueba de error → variante diferente**

```typescript
it("inserta otra formulación del mismo hecho después de 8 a 15 preguntas", async () => {
  renderQuizWithFourVariants()
  await answerCurrentQuestionIncorrectly()
  const persisted = await readPersistedRound()
  const first = persisted.questionSnapshots![0]
  const retryIndex = persisted.questionSnapshots!.findIndex((q, index) => index >= 9 && index <= 16 && q.factId === first.factId)
  expect(retryIndex).toBeGreaterThanOrEqual(9)
  const retry = persisted.questionSnapshots![retryIndex]
  expect(retry.variantId).not.toBe(first.variantId)
  expect(retry.question).not.toBe(first.question)
  expect(retry.type).not.toBe(first.type)
})

it("persiste la reparación cuando no cabe al final", async () => {
  renderQuizAtLastQuestion()
  await answerCurrentQuestionIncorrectly()
  expect((await repositories.retrievalQueue.list())[0].stage).toBe("repair")
})

it("recargar conserva la materialización exacta", async () => {
  const before = await readPersistedRound()
  unmountQuiz()
  renderQuizFromRound(before)
  expect(await readVisibleQuestion()).toEqual(snapshotQuestion(before))
})
```

- [ ] **Step 2: Ejecutar RED**

Run: `npm test -- src/domain/dynamic-question.test.ts src/components/quiz-page.test.tsx --run`

Expected: FAIL porque el reintento actual puede reutilizar la misma pregunta.

- [ ] **Step 3: Implementar elección de variante**

Seleccionar dentro del grupo `factId`; excluir `previous.variantId`, excluir el mismo tipo si existe alternativa y priorizar `semanticSkill` no usado. Materializar distractores y orden con una semilla derivada de `sessionId`, `factId` y número de exposición. Guardar el snapshot materializado en la ronda activa.

- [ ] **Step 4: Integrar reparación en `QuizPage`**

Insertar la variante elegida en `currentIndex + minQuestionGap + 1`. Si excede la cola, dejar el elemento `repair` persistido. Añadir `selectionReason` a metadata y mostrar `Reparación de un error anterior` únicamente después de responder.

- [ ] **Step 5: Ejecutar GREEN**

Run: `npm test -- src/domain/dynamic-question.test.ts src/components/quiz-page.test.tsx --run`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/domain/dynamic-question.ts src/domain/dynamic-question.test.ts src/domain/session-selector.ts src/components/quiz-page.tsx src/components/quiz-page.test.tsx src/storage/final-bank.ts
git commit -m "feat: retry failed facts with new variants"
```

### Task 6: Convertir resultados en una siguiente tanda nueva

**Files:**
- Modify: `src/App.tsx`
- Modify: `src/components/results-page.tsx`
- Modify: `src/components/app-states.test.tsx`
- Modify: `src/domain/session-selection.ts`

**Interfaces:**
- Consumes: `FactCoverageCycle` actualizado.
- Produces: CTA primario `Otra tanda nueva` y acción secundaria `Repetir exactamente`.

- [ ] **Step 1: Escribir pruebas de acciones**

Exigir que `Otra tanda nueva` llame `startRound(result.config)` sin subset y consuma el ciclo por hechos; exigir que `Repetir exactamente` pase `resultQuestions` como subset.

- [ ] **Step 2: Ejecutar RED**

Run: `npm test -- src/components/app-states.test.tsx --run`

Expected: FAIL porque el CTA actual repite la tanda.

- [ ] **Step 3: Implementar acciones y textos**

Cambiar callbacks a `onNextBatch` y `onExactRepeat`, hacer primario el primero y colocar el segundo en menú/acción ghost con texto explícito. Mostrar cuántos hechos nuevos quedan en el ciclo.

- [ ] **Step 4: Ejecutar GREEN**

Run: `npm test -- src/components/app-states.test.tsx --run`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/App.tsx src/components/results-page.tsx src/components/app-states.test.tsx src/domain/session-selection.ts
git commit -m "fix: make next batch genuinely new"
```

### Task 7: Simplificar la práctica y el feedback

**Files:**
- Modify: `src/components/session-builder-page.tsx`
- Modify: `src/components/session-builder-page.test.tsx`
- Modify: `src/components/massive-training-hub.tsx`
- Modify: `src/components/massive-training-hub.test.tsx`
- Modify: `src/components/answer-learning-feedback.tsx`
- Modify: `src/components/answer-learning-feedback.test.tsx`
- Modify: `src/components/quiz-page.tsx`

**Interfaces:**
- Produces: orden visual CTA → resumen → modos → alcance; avanzados plegados; feedback resultado → frase → explicación → referencia.

- [ ] **Step 1: Escribir pruebas de jerarquía y copy**

Exigir `Entrenar ahora` antes de `Modos avanzados`, detalles avanzados cerrados inicialmente, métricas `Nuevas`, `Vencidas`, `Errores`, `Prioridad`, y ausencia del texto técnico `single_choice_contextual`.

- [ ] **Step 2: Ejecutar RED**

Run: `npm test -- src/components/session-builder-page.test.tsx src/components/massive-training-hub.test.tsx src/components/answer-learning-feedback.test.tsx --run`

Expected: FAIL por jerarquía actual.

- [ ] **Step 3: Implementar la jerarquía**

Mover el CTA recomendado y resumen al inicio; envolver Plan 48 horas y modos avanzados en disclosures separados; conservar los controles existentes dentro de ellos. En feedback, presentar primero `Correcta`/`Hay que repararla`, luego frase completa, explicación y botón de referencia.

- [ ] **Step 4: Validar 390 px y escritorio localmente**

Run: `npm test -- src/components/session-builder-page.test.tsx src/components/massive-training-hub.test.tsx src/components/answer-learning-feedback.test.tsx --run`

Expected: PASS.

Run: `npm run test:e2e -- --grep "jerarquía|móvil"`

Expected: PASS sin solapamiento ni footer sobre contenido.

- [ ] **Step 5: Commit**

```powershell
git add src/components/session-builder-page.tsx src/components/session-builder-page.test.tsx src/components/massive-training-hub.tsx src/components/massive-training-hub.test.tsx src/components/answer-learning-feedback.tsx src/components/answer-learning-feedback.test.tsx src/components/quiz-page.tsx
git commit -m "feat: focus practice on the next learning action"
```

### Task 8: Actualizar sin borrar datos

**Files:**
- Create: `src/update-manager.ts`
- Create: `src/update-manager.test.ts`
- Modify: `src/main.tsx`
- Modify: `public/sw.js`
- Modify: `src/service-worker.test.ts`
- Modify: `src/App.tsx`

**Interfaces:**
- Produces: `registerUpdateManager({ hasActiveRound, onUpdateReady })` y evento de UI `UpdateReady`.

- [ ] **Step 1: Escribir pruebas de actualización**

```typescript
it("comprueba actualizaciones al recuperar foco", async () => {
  const registration = makeRegistration()
  registerUpdateManager({ registration, hasActiveRound: () => false, onUpdateReady: vi.fn() })
  setDocumentVisibility("visible")
  document.dispatchEvent(new Event("visibilitychange"))
  expect(registration.update).toHaveBeenCalledOnce()
})

it("no recarga durante una ronda activa", async () => {
  const registration = makeRegistration({ waiting: makeWaitingWorker() })
  const onUpdateReady = vi.fn()
  registerUpdateManager({ registration, hasActiveRound: () => true, onUpdateReady })
  await notifyWaitingWorker(registration)
  expect(registration.waiting!.postMessage).not.toHaveBeenCalled()
  expect(onUpdateReady).toHaveBeenCalledWith("deferred")
})

it("activa y recarga una sola vez fuera de ronda", async () => {
  const registration = makeRegistration({ waiting: makeWaitingWorker() })
  registerUpdateManager({ registration, hasActiveRound: () => false, onUpdateReady: vi.fn() })
  await notifyWaitingWorker(registration)
  expect(registration.waiting!.postMessage).toHaveBeenCalledWith({ type: "SKIP_WAITING" })
})
```

Conservar las pruebas existentes que ejercitan network-first para navegación y `/banks/`; ampliarlas para comprobar que un fallo de red devuelve el cache sin convertir una respuesta HTTP fallida en contenido nuevo.

- [ ] **Step 2: Ejecutar RED**

Run: `npm test -- src/update-manager.test.ts src/service-worker.test.ts --run`

Expected: FAIL por módulo inexistente y falta de comprobación al recuperar foco.

- [ ] **Step 3: Implementar gestor y caché V10**

Registrar una vez, llamar `registration.update()` en `visibilitychange` cuando el documento vuelva a visible, detectar `waiting`, y posponer `postMessage({ type: "SKIP_WAITING" })` mientras exista ronda activa. Añadir listener de mensaje al worker y cambiar `CACHE_NAME` a `conexion-biblica-shell-v10`.

- [ ] **Step 4: Ejecutar GREEN**

Run: `npm test -- src/update-manager.test.ts src/service-worker.test.ts --run`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/update-manager.ts src/update-manager.test.ts src/main.tsx public/sw.js src/service-worker.test.ts src/App.tsx
git commit -m "fix: apply updates without clearing study data"
```

### Task 9: Aceptación integral y despliegue

**Files:**
- Create: `e2e/training-v8.spec.ts`
- Modify: `scripts/audit-live-final-bank.mjs`
- Modify: `package.json` only if a new audit script is required.

**Interfaces:**
- Consumes: banco V8, aplicación local y URL pública.
- Produces: evidencia reproducible de calidad, aprendizaje, responsive y sincronización de producción.

- [ ] **Step 1: Escribir E2E antes de cerrar implementación**

Cubrir:

```typescript
test("100 preguntas iniciales no repiten hechos", async ({ page }) => {
  await startSeededRound(page, 100)
  const factIds = await collectRoundFactIds(page)
  expect(factIds).toHaveLength(100)
  expect(new Set(factIds).size).toBe(100)
})

test("ninguna pregunta pide páginas párrafos o referencias", async ({ page }) => {
  await startSeededRound(page, 100)
  const prompts = await collectRoundPrompts(page)
  expect(prompts.some((prompt) => /en (?:qué|cuál) (?:página|párrafo|versículo|referencia)/i.test(prompt))).toBe(false)
})

test("práctica funciona a 390 px sin contenido tapado", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await startSeededRound(page, 10)
  const overlap = await page.evaluate(() => {
    const question = document.querySelector("#question-title")!.getBoundingClientRect()
    const footer = document.querySelector("footer")!.getBoundingClientRect()
    return question.bottom > footer.top
  })
  expect(overlap).toBe(false)
})
```

Añadir dos escenarios completos usando los mismos helpers: el primero falla la pregunta inicial y comprueba otra formulación entre las posiciones 9–16; el segundo completa una tanda, inicia `Otra tanda nueva` y exige que la intersección de sus 100 `fact_id` sea vacía mientras el ciclo tenga al menos 200 hechos.

- [ ] **Step 2: Ejecutar todos los controles locales**

Run: `python -m unittest discover -s scripts -p "test_*.py"`

Run: `python scripts/audit-final-bank-deep.py`

Run: `npm run lint`

Run: `npm run typecheck`

Run: `npm test -- --run`

Run: `npm run build`

Run: `npm run test:e2e`

Expected: todos con exit code 0; las únicas omisiones E2E serán las condicionadas al viewport contrario.

- [ ] **Step 3: Revisar diff y commit de aceptación**

Run: `git diff --check`

Confirmar que el PDF y `output/playwright/` siguen sin añadirse. Commit:

```powershell
git add e2e/training-v8.spec.ts scripts/audit-live-final-bank.mjs package.json
git commit -m "test: verify intelligent training v8"
```

- [ ] **Step 4: Publicar**

Run: `git push origin main`

Esperar a que todos los estados Vercel del commit sean `success`.

- [ ] **Step 5: Auditar producción**

Run: `npm run audit:production`

Expected: `failures: []`, 18 shards V8 y checksums idénticos.

Run: `$env:PLAYWRIGHT_BASE_URL='https://conexion-biblica-2026.vercel.app'; npm run test:e2e`

Expected: suite aprobada en escritorio y móvil, sin errores de consola.

- [ ] **Step 6: Entregar métricas finales**

Reportar URL, commits, preguntas, hechos, variantes, distribución por capítulo/tipo/dificultad, candidatos rechazados, tamaño ciego, pruebas y cualquier limitación editorial que aún exista. No declarar finalización si producción no coincide con el commit auditado.
