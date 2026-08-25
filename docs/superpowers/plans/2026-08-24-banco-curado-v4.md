# V4 Banco Curado Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir V4 a partir de las 3,558 preguntas del Banco Maestro, conservando V2 intacto y exponiendo únicamente preguntas aprobadas o reparadas en la práctica normal.

**Architecture:** Un pipeline Node determinista clasificará cada entrada maestra, aplicará reparaciones permitidas y generará dos bancos V4 más reportes de auditoría. La aplicación cargará esos JSON como un perfil nuevo, usará V4 por defecto en instalaciones nuevas y redefinirá Mixto para excluir el perfil técnico V2.

**Tech Stack:** Node.js ESM, TypeScript 6, React 19, Vite 8, IndexedDB, Vitest 3, Testing Library y Playwright.

**Spec:** `docs/superpowers/specs/2026-08-24-banco-curado-v4-design.md`

## Global Constraints

- `Banco_Maestro_CB2026.json` es inmutable y debe conservar su hash.
- El alcance es Daniel 1–12 y Profetas y Reyes 39–44.
- Toda entrada recibe exactamente un estado: `APPROVED`, `REPAIRED` o `REJECTED`.
- Ninguna reparación puede inventar hechos, respuestas, referencias o explicaciones.
- V4 sólo contiene preguntas `APPROVED` o `REPAIRED`.
- V2 permanece seleccionable como fuente técnica, pero Mixto curado lo excluye.
- No se añaden dependencias nuevas.
- Cada comportamiento se implementa mediante ciclo TDD rojo-verde.
- No se sobrescriben archivos V4 válidos si la nueva generación falla.

---

## File Map

**Crear**

- `scripts/lib/master-curation.mjs`: clasificación, códigos de incidencia y resolución estructural de respuestas.
- `scripts/lib/master-curation.test.mjs`: pruebas unitarias de clasificación.
- `scripts/lib/curated-question.mjs`: reparación y adaptación de una entrada aprobada.
- `scripts/lib/curated-question.test.mjs`: pruebas de redacción, tipos, respuestas y familias.
- `scripts/build-curated-v4.mjs`: generación determinista y escritura segura.
- `scripts/audit-curated-v4.mjs`: auditoría cruzada y reportes.
- `scripts/lib/curated-v4.integration.test.mjs`: prueba completa sobre las 3,558 entradas.
- `public/banks/v4_daniel.json`: salida integrada de Daniel.
- `public/banks/v4_profetas_reyes.json`: salida integrada de Profetas y Reyes.
- `reports/curated-v4-audit.json`: reporte completo para máquinas.
- `reports/curated-v4-audit.md`: resumen y rechazos para humanos.
- `src/domain/bank-profile.test.ts`: semántica de V4, V2 técnico y Mixto curado.

**Modificar**

- `scripts/lib/editorial.mjs`: reutilizar normalización editorial comprobada.
- `package.json`: scripts `build:v4` y `audit:v4`.
- `public/banks/manifest.json`: incluir ambos bancos V4.
- `src/domain/types.ts`: añadir `curated-v4`.
- `src/domain/banks.ts`: definición del perfil y semántica de selección.
- `src/storage/seed.ts`: reconocer, nombrar y reemplazar bancos V4 integrados.
- `src/storage/seed.test.ts`: perfil y reemplazo V4.
- `src/app/app-state.tsx`: conteo V4 y preferencia inicial.
- `src/domain/backup.ts`: compatibilidad de preferencias.
- `src/domain/backup.test.ts`: restauración de respaldos con y sin V4.
- `src/components/bank-selector.tsx`: tarjeta V4 y advertencia V2.
- `src/components/bank-selector.test.tsx`: accesibilidad y recomendación.
- `src/components/app-shell.tsx`: selector compacto V4/Mixto curado.
- `src/components/bank-manager-page.tsx`: resumen de curación V4.
- `src/components/dashboard-page.tsx`: copia del perfil recomendado cuando corresponda.
- `src/components/session-builder-page.tsx`: copia y selección compatibles con V4.
- `e2e/training-modes.spec.ts`: instalación nueva, V4, Mixto y recarga.
- `README.md`: explicar perfiles y comandos de regeneración.

---

### Task 1: Política de clasificación del Banco Maestro

**Files:**
- Create: `scripts/lib/master-curation.mjs`
- Create: `scripts/lib/master-curation.test.mjs`

**Interfaces:**
- Consumes: objetos raw con la forma de `MasterQuestionRaw` en `src/domain/master-bank.ts`.
- Produces: `classifyMasterQuestion(raw): { status, issues, answer }`.
- Produces: `resolveMasterAnswer(raw): { mode, optionId, text } | null`.
- Produces: `curationFamily(raw): { factKey, factKeys }`.

- [ ] **Step 1: Escribir pruebas fallidas para estados y respuestas**

```js
import { describe, expect, it } from "vitest"
import { classifyMasterQuestion, resolveMasterAnswer } from "./master-curation.mjs"

const base = {
  QUESTION_ID: "GEN-1", origen: "GENERATED", material: "DANIEL", capitulo: "1",
  tipo: "SELECCIÓN MÚLTIPLE", dificultad: "HARD", pregunta: "¿Quién decidió no contaminarse?",
  A: "A) Daniel", B: "B) Aspenaz", C: "C) Nabucodonosor", D: "D) Darío",
  respuesta_correcta: "A) Daniel", fuente: "Daniel 1:8, RVR95",
  FULL_FACT_IDS: ["FACT-D01-V08-001"], PARTIAL_FACT_IDS: [], INCIDENTAL_FACT_IDS: [],
  habilidad: "identificación", riesgo_objetivo: "HIGH", explicacion: "Daniel decidió no contaminarse.",
  estado_QC: "PASS_10_10", variant_of: "", generation_level: "1", duplicate_group: "DG-1",
  HIST_IDS: [], historical_status: "", fact_support: "Daniel propuso no contaminarse",
  answer_span: "Daniel", answer_category: "PERSON",
}

describe("política V4", () => {
  it("aprueba una pregunta inequívoca", () => {
    expect(classifyMasterQuestion(base)).toMatchObject({ status: "APPROVED", issues: [] })
    expect(resolveMasterAnswer(base)).toEqual({ mode: "option_id", optionId: "A", text: "Daniel" })
  })

  it("marca para reparación el lenguaje de generación", () => {
    const raw = { ...base, pregunta: "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «Daniel __________»." }
    expect(classifyMasterQuestion(raw)).toMatchObject({ status: "REPAIRED", issues: ["ARTIFICIAL_PROMPT"] })
  })

  it("rechaza una corrección todavía discutible", () => {
    const raw = { ...base, QUESTION_ID: "HIST-X", respuesta_correcta: "A) Tiro y Egipto, pero la relación requiere corrección." }
    expect(classifyMasterQuestion(raw)).toMatchObject({ status: "REJECTED" })
    expect(classifyMasterQuestion(raw).issues).toContain("UNRESOLVED_CORRECTION")
  })

  it("rechaza una opción correcta inexistente o repetida", () => {
    expect(classifyMasterQuestion({ ...base, respuesta_correcta: "E) Nadie" }).issues).toContain("UNRESOLVED_ANSWER")
    expect(classifyMasterQuestion({ ...base, B: "B) Daniel" }).issues).toContain("DUPLICATE_OPTIONS")
  })
})
```

- [ ] **Step 2: Ejecutar las pruebas y confirmar el rojo**

Run: `npm.cmd test -- scripts/lib/master-curation.test.mjs`

Expected: FAIL porque `master-curation.mjs` todavía no existe.

- [ ] **Step 3: Implementar las reglas mínimas**

```js
export const CurationStatus = Object.freeze({ APPROVED: "APPROVED", REPAIRED: "REPAIRED", REJECTED: "REJECTED" })

const repairRules = [
  ["ARTIFICIAL_PROMPT", (q) => /segunda formulación de alto riesgo|según el hecho/i.test(q.pregunta)],
  ["PROCESS_EXPLANATION", (q) => /pregunta histórica|fase\s*[1-4]|cobertura auditada/i.test(q.explicacion)],
  ["EDITORIAL_PREFIX", (q) => /^\[Profetas y Reyes\]/i.test(q.pregunta)],
  ["UNBALANCED_QUOTES", (q) => (q.pregunta.match(/«/g) ?? []).length !== (q.pregunta.match(/»/g) ?? []).length],
  ["SHORT_ANSWER_TYPE", (q) => /RESPUESTA CORTA/i.test(q.tipo)],
]

const rejectionRules = [
  ["OUT_OF_SCOPE", (q) => q.material === "DANIEL" ? +q.capitulo < 1 || +q.capitulo > 12 : q.material !== "PR" || +q.capitulo < 39 || +q.capitulo > 44],
  ["UNRESOLVED_CORRECTION", (q) => /requiere corrección|respuesta discutible/i.test(q.respuesta_correcta)],
]

export function classifyMasterQuestion(raw) {
  const issues = []
  for (const [code, matches] of rejectionRules) if (matches(raw)) issues.push(code)
  const answer = resolveMasterAnswer(raw)
  if (!answer) issues.push("UNRESOLVED_ANSWER")
  if (hasDuplicateOptions(raw)) issues.push("DUPLICATE_OPTIONS")
  if (issues.length) return { status: "REJECTED", issues, answer }
  for (const [code, matches] of repairRules) if (matches(raw)) issues.push(code)
  return { status: issues.length ? "REPAIRED" : "APPROVED", issues, answer }
}
```

Implementar `resolveMasterAnswer` con estas ramas exactas:

1. `VERDADERO/FALSO`: normalizar a `TRUE`/`FALSE`.
2. Respuesta con prefijo `A)`–`D)`: usar esa opción sólo si existe y es única.
3. Respuesta histórica `CORRECTED`: extraer `/forma exacta RVR95 es «([^»]+)»/` como texto canónico.
4. Respuesta corta/completar sin opciones: usar texto canónico sin prefijo.
5. Cualquier otro caso: devolver `null`.

- [ ] **Step 4: Ejecutar pruebas focalizadas**

Run: `npm.cmd test -- scripts/lib/master-curation.test.mjs`

Expected: PASS.

- [ ] **Step 5: Ampliar pruebas de alcance y familia**

Añadir casos literales para Daniel 0/13, PR 38/45, prioridad FULL → PARTIAL → INCIDENTAL → duplicate group → ID y opciones equivalentes después de quitar acentos/puntuación.

Run: `npm.cmd test -- scripts/lib/master-curation.test.mjs`

Expected: PASS.

- [ ] **Step 6: Commit del entregable**

```powershell
git add scripts/lib/master-curation.mjs scripts/lib/master-curation.test.mjs
git commit -m "feat: classify master questions for curated v4"
```

---

### Task 2: Reparación y adaptación de preguntas V4

**Files:**
- Create: `scripts/lib/curated-question.mjs`
- Create: `scripts/lib/curated-question.test.mjs`
- Modify: `scripts/lib/editorial.mjs`

**Interfaces:**
- Consumes: `classifyMasterQuestion`, `resolveMasterAnswer` y `curationFamily` de Task 1.
- Produces: `curateMasterQuestion(raw, decision): CuratedQuestion | null`.
- Produces: `repairPrompt(prompt): string` y `repairExplanation(raw): string`.

- [ ] **Step 1: Escribir pruebas fallidas de reparación**

```js
it("repara redacción y explicación sin cambiar respuesta ni fuente", () => {
  const raw = {
    ...base,
    pregunta: "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «Daniel __________».",
    explicacion: "Pregunta histórica validada en FASE 1; cobertura auditada en FASE 3.",
  }
  const decision = classifyMasterQuestion(raw)
  expect(curateMasterQuestion(raw, decision)).toMatchObject({
    id: "V4-GEN-1",
    question: "Completa la afirmación: Daniel __________.",
    correctAnswer: ["A"],
    explanation: "La respuesta se confirma en Daniel 1:8, RVR95.",
    source: { work: "Daniel", chapter: 1, reference: "Daniel 1:8, RVR95" },
    metadata: { masterQuestionId: "GEN-1", curationStatus: "REPAIRED" },
  })
})

it("convierte respuesta corta en texto canónico", () => {
  const raw = { ...base, tipo: "RESPUESTA CORTA", A: "", B: "", C: "", D: "", respuesta_correcta: "Daniel" }
  expect(curateMasterQuestion(raw, classifyMasterQuestion(raw))).toMatchObject({
    type: "reference_detail", answerMode: "canonical_text", correctAnswerText: "Daniel",
  })
})

it("no genera salida para rechazados", () => {
  const raw = { ...base, respuesta_correcta: "A) Daniel, pero requiere corrección." }
  expect(curateMasterQuestion(raw, classifyMasterQuestion(raw))).toBeNull()
})
```

- [ ] **Step 2: Ejecutar y confirmar el rojo**

Run: `npm.cmd test -- scripts/lib/curated-question.test.mjs`

Expected: FAIL porque el adaptador no existe.

- [ ] **Step 3: Implementar el adaptador puro**

```js
export function curateMasterQuestion(raw, decision) {
  if (decision.status === "REJECTED") return null
  const { factKey, factKeys } = curationFamily(raw)
  const answer = decision.answer
  const work = raw.material === "DANIEL" ? "Daniel" : "Profetas y Reyes"
  return {
    id: `V4-${raw.QUESTION_ID}`,
    type: normalizedType(raw, answer),
    difficulty: normalizedDifficulty(raw.dificultad),
    source: { work, version: work === "Daniel" ? "RVR95" : "Material PDF", chapter: Number(raw.capitulo), reference: raw.fuente },
    tags: ["v4", raw.habilidad, raw.riesgo_objetivo].filter(Boolean),
    factKey,
    factKeys,
    question: repairPrompt(raw.pregunta),
    options: visibleOptions(raw, answer),
    correctAnswer: answer.mode === "option_id" ? [answer.optionId] : ["ANSWER"],
    ...(answer.mode === "canonical_text" ? { answerMode: "canonical_text", correctAnswerText: answer.text } : {}),
    explanation: repairExplanation(raw),
    memoryCue: `Ancla ${raw.fuente}: ${String(raw.fact_support || answer.text).replace(/[.。]+$/g, "")}.`,
    verified: true,
    metadata: {
      masterQuestionId: raw.QUESTION_ID,
      curationStatus: decision.status,
      curationIssues: decision.issues,
      originalDifficulty: raw.dificultad,
      originalType: raw.tipo,
      duplicateGroup: raw.duplicate_group,
      qc: raw.estado_QC,
      historicalStatus: raw.historical_status,
    },
  }
}
```

`repairPrompt` reutiliza `naturalizePrompt`, elimina el prefijo `[Profetas y Reyes]`, balancea únicamente comillas exteriores huérfanas y normaliza espacios. `repairExplanation` usa `fact_support` cuando existe y, para explicaciones administrativas, devuelve exactamente `La respuesta se confirma en <fuente>.`.

- [ ] **Step 4: Ejecutar pruebas del adaptador**

Run: `npm.cmd test -- scripts/lib/curated-question.test.mjs scripts/lib/editorial.test.mjs`

Expected: PASS.

- [ ] **Step 5: Añadir pruebas de no mutación**

Congelar el fixture con `structuredClone`, llamar al adaptador y comprobar `expect(raw).toEqual(before)`. Añadir un caso de corrección histórica explícita y otro de comillas internas válidas.

Run: `npm.cmd test -- scripts/lib/curated-question.test.mjs`

Expected: PASS.

- [ ] **Step 6: Commit del entregable**

```powershell
git add scripts/lib/editorial.mjs scripts/lib/curated-question.mjs scripts/lib/curated-question.test.mjs
git commit -m "feat: repair and adapt curated v4 questions"
```

---

### Task 3: Generador, auditor y reportes V4

**Files:**
- Create: `scripts/build-curated-v4.mjs`
- Create: `scripts/audit-curated-v4.mjs`
- Create: `scripts/lib/curated-v4.integration.test.mjs`
- Create: `public/banks/v4_daniel.json`
- Create: `public/banks/v4_profetas_reyes.json`
- Create: `reports/curated-v4-audit.json`
- Create: `reports/curated-v4-audit.md`
- Modify: `package.json`

**Interfaces:**
- Consumes: funciones de Tasks 1–2 y `Banco_Maestro_CB2026.json`.
- Produces: `buildCuratedV4(master): { banks, audit }` exportada desde el script o un módulo auxiliar sin efectos laterales.
- Produce bancos schema `1.0` con `bank.profileId = "curated-v4"`.

- [ ] **Step 1: Escribir la integración fallida sobre las 3,558 entradas**

```js
it("clasifica cada pregunta maestra exactamente una vez", async () => {
  const master = JSON.parse(await readFile("Banco_Maestro_CB2026.json", "utf8"))
  const result = buildCuratedV4(master)
  expect(result.audit.summary.total).toBe(3558)
  expect(result.audit.summary.approved + result.audit.summary.repaired + result.audit.summary.rejected).toBe(3558)
  expect(result.audit.summary.blockers).toBe(0)
  expect(result.banks.daniel.questions.every((q) => q.source.work === "Daniel")).toBe(true)
  expect(result.banks.prophets.questions.every((q) => q.source.work === "Profetas y Reyes")).toBe(true)
})

it("no deja lenguaje técnico ni correcciones pendientes", () => {
  const questions = [...result.banks.daniel.questions, ...result.banks.prophets.questions]
  expect(questions.some((q) => /segunda formulación|fase\s*[1-4]|cobertura auditada|requiere corrección/i.test(`${q.question} ${q.explanation} ${q.correctAnswerText ?? ""}`))).toBe(false)
})
```

- [ ] **Step 2: Ejecutar y confirmar el rojo**

Run: `npm.cmd test -- scripts/lib/curated-v4.integration.test.mjs`

Expected: FAIL porque `buildCuratedV4` no existe.

- [ ] **Step 3: Implementar construcción en memoria y validación**

El resultado tendrá esta forma exacta:

```js
{
  banks: {
    daniel: { schemaVersion: "1.0", bank: { profileId: "curated-v4", sourceWork: "Daniel", sourceVersion: "RVR95", curationSummary }, questions: [] },
    prophets: { schemaVersion: "1.0", bank: { profileId: "curated-v4", sourceWork: "Profetas y Reyes", sourceVersion: "Material PDF", curationSummary }, questions: [] },
  },
  audit: {
    generatedAt: "ISO timestamp",
    masterFingerprint: "sha256",
    summary: { total, approved, repaired, rejected, blockers },
    countsByIssue: {},
    decisions: [{ masterQuestionId, status, issues, originalQuestion, curatedQuestion }],
  },
}
```

Antes de devolver, comprobar IDs únicos, respuestas resolubles, referencias idénticas, capítulos idénticos, balance de comillas y suma de estados. Lanzar `Error` con todos los bloqueadores si falla.

- [ ] **Step 4: Ejecutar la integración y revisar cifras reales**

Run: `npm.cmd test -- scripts/lib/curated-v4.integration.test.mjs`

Expected: PASS y una cifra final de V4 menor o igual a 3,558. No fijar una cuota artificial.

- [ ] **Step 5: Implementar escritura segura y reportes**

`build-curated-v4.mjs` escribirá primero:

```js
await writeFile(`${target}.tmp`, `${JSON.stringify(value, null, 2)}\n`)
await rename(`${target}.tmp`, target)
```

Sólo ejecutar ese bloque después de validar ambos bancos y el reporte completo. En un `catch`, borrar únicamente los `.tmp` conocidos y conservar los destinos existentes.

El Markdown incluirá resumen, tabla por código, todos los rechazados y una muestra de máximo 20 reparaciones por código; el JSON conservará todas las decisiones.

- [ ] **Step 6: Añadir scripts y ejecutar generación real**

```json
"build:v4": "node scripts/build-curated-v4.mjs",
"audit:v4": "node scripts/audit-curated-v4.mjs"
```

Run: `npm.cmd run build:v4`

Run: `npm.cmd run audit:v4`

Expected: ambos terminan con código 0 y generan los seis artefactos declarados.

- [ ] **Step 7: Verificar inmutabilidad del maestro**

Calcular SHA-256 antes y después:

```powershell
Get-FileHash -Algorithm SHA256 Banco_Maestro_CB2026.json
```

Expected: el hash es idéntico.

- [ ] **Step 8: Commit del entregable**

```powershell
git add package.json scripts/build-curated-v4.mjs scripts/audit-curated-v4.mjs scripts/lib/curated-v4.integration.test.mjs public/banks/v4_daniel.json public/banks/v4_profetas_reyes.json reports/curated-v4-audit.json reports/curated-v4-audit.md
git commit -m "feat: generate and audit curated v4 banks"
```

---

### Task 4: Perfil V4 y carga integrada

**Files:**
- Modify: `src/domain/types.ts`
- Modify: `src/domain/banks.ts`
- Modify: `src/storage/seed.ts`
- Modify: `src/storage/seed.test.ts`
- Modify: `public/banks/manifest.json`
- Create: `src/domain/bank-profile.test.ts`

**Interfaces:**
- Extiende `BankProfileId` con `"curated-v4"`.
- `BankSelection` continúa siendo `BankProfileId | "mixed"`.
- `questionBelongsToSelection(question, "mixed")` excluye `master-v2`.

- [ ] **Step 1: Escribir pruebas fallidas de perfil y selección**

```ts
it("Mixto curado incluye V1, V3 y V4 pero excluye V2", () => {
  expect(questionBelongsToSelection(question("legacy-v1"), "mixed")).toBe(true)
  expect(questionBelongsToSelection(question("prep-v3"), "mixed")).toBe(true)
  expect(questionBelongsToSelection(question("curated-v4"), "mixed")).toBe(true)
  expect(questionBelongsToSelection(question("master-v2"), "mixed")).toBe(false)
})

it("reconoce un banco V4 integrado", () => {
  const bank = createBankFromRaw(v4Fixture, "v4_daniel.json", 1)
  expect(bank).toMatchObject({ bankProfileId: "curated-v4", name: "V4 — Banco Curado Daniel" })
})
```

- [ ] **Step 2: Ejecutar y confirmar errores de tipos/comportamiento**

Run: `npm.cmd test -- src/domain/bank-profile.test.ts src/storage/seed.test.ts`

Expected: FAIL porque `curated-v4` no pertenece a la unión y el seed lo trata como V1.

- [ ] **Step 3: Extender tipos, definiciones y seed**

```ts
export type BankProfileId = "legacy-v1" | "master-v2" | "prep-v3" | "curated-v4"

"curated-v4": {
  id: "curated-v4",
  label: "V4 — Banco Curado",
  description: "Cobertura amplia revisada",
  readOnly: true,
  version: "CB2026-CURATED-V4",
},
```

En `createBankFromRaw`, resolver `metadata.profileId` con una función exhaustiva y nombrar V4 según `sourceWork`. En `shouldReplaceBundledBank`, reutilizar huella; V4 será integrado y de sólo lectura igual que V3.

- [ ] **Step 4: Añadir V4 al manifest**

```json
{
  "files": [
    "v3_daniel.json",
    "v3_profetas_reyes.json",
    "v4_daniel.json",
    "v4_profetas_reyes.json"
  ]
}
```

- [ ] **Step 5: Ejecutar pruebas focalizadas y tipos**

Run: `npm.cmd test -- src/domain/bank-profile.test.ts src/storage/seed.test.ts src/domain/prep-bank.test.ts`

Run: `npm.cmd run typecheck`

Expected: PASS.

- [ ] **Step 6: Commit del entregable**

```powershell
git add src/domain/types.ts src/domain/banks.ts src/domain/bank-profile.test.ts src/storage/seed.ts src/storage/seed.test.ts public/banks/manifest.json
git commit -m "feat: load curated v4 as a bank profile"
```

---

### Task 5: Preferencias, respaldos y conteos compatibles

**Files:**
- Modify: `src/app/app-state.tsx`
- Modify: `src/domain/backup.ts`
- Modify: `src/domain/backup.test.ts`
- Modify: `src/lib/statistics.test.ts`

**Interfaces:**
- `bankCounts` añade `curated: number`.
- Instalaciones sin preferencia usan `lastBankSelection: "curated-v4"`.
- Preferencias existentes válidas conservan su valor.

- [ ] **Step 1: Escribir pruebas fallidas de respaldo**

```ts
it("acepta y conserva curated-v4", () => {
  const payload = createBackupPayload({ ...state, preferences: { ...preferences, lastBankSelection: "curated-v4" } })
  expect(validateBackupPayload(payload).valid).toBe(true)
  expect(migrateBackupPayload(payload).preferences.lastBankSelection).toBe("curated-v4")
})

it("mantiene una selección antigua válida", () => {
  const payload = oldBackup({ lastBankSelection: "prep-v3" })
  expect(migrateBackupPayload(payload).preferences.lastBankSelection).toBe("prep-v3")
})
```

- [ ] **Step 2: Ejecutar y confirmar el rojo**

Run: `npm.cmd test -- src/domain/backup.test.ts`

Expected: FAIL en validación de `curated-v4`.

- [ ] **Step 3: Implementar preferencia y conteo**

```ts
const defaultPreferences: Preferences = {
  theme: "system",
  lastMode: "training",
  reducedMotion: false,
  lastBankSelection: "curated-v4",
}

const bankCounts = {
  legacy: count("legacy-v1"),
  master: count("master-v2"),
  prep: count("prep-v3"),
  curated: count("curated-v4"),
}
```

La migración sólo reemplaza selecciones desconocidas; no cambia V1, V2, V3 o `mixed` existentes.

- [ ] **Step 4: Ejecutar pruebas y tipos**

Run: `npm.cmd test -- src/domain/backup.test.ts src/lib/statistics.test.ts`

Run: `npm.cmd run typecheck`

Expected: PASS.

- [ ] **Step 5: Commit del entregable**

```powershell
git add src/app/app-state.tsx src/domain/backup.ts src/domain/backup.test.ts src/lib/statistics.test.ts
git commit -m "feat: persist curated v4 preferences and counts"
```

---

### Task 6: Selector, etiquetas y resumen de curación

**Files:**
- Modify: `src/components/bank-selector.tsx`
- Modify: `src/components/bank-selector.test.tsx`
- Modify: `src/components/app-shell.tsx`
- Modify: `src/components/bank-manager-page.tsx`
- Modify: `src/components/dashboard-page.tsx`
- Modify: `src/components/session-builder-page.tsx`

**Interfaces:**
- `BankSelector` recibe `curatedCount`.
- La tarjeta V4 lleva `recommended`.
- La tarjeta V2 lleva `technical` y una advertencia visible.

- [ ] **Step 1: Escribir pruebas fallidas del selector**

```tsx
render(<BankSelector value="curated-v4" onChange={onChange} legacyCount={10} masterCount={3558} prepCount={500} curatedCount={3200} />)
expect(screen.getByRole("radio", { name: /V4 — Banco Curado/ })).toBeChecked()
expect(screen.getByText("Recomendado")).toBeInTheDocument()
expect(screen.getByText(/Fuente técnica/)).toBeInTheDocument()
await user.click(screen.getByRole("radio", { name: /Mixto curado/ }))
expect(onChange).toHaveBeenCalledWith("mixed")
```

- [ ] **Step 2: Ejecutar y confirmar el rojo**

Run: `npm.cmd test -- src/components/bank-selector.test.tsx`

Expected: FAIL porque falta `curatedCount` y la opción V4.

- [ ] **Step 3: Implementar las cinco opciones visibles**

Orden exacto:

1. V4 — Banco Curado · recomendado para cobertura amplia.
2. V3 — Preparación intensiva de 4 días.
3. V1 — Clásica.
4. Mixto curado — V1 + V3 + V4.
5. V2 — Fuente técnica · puede contener redacción de auditoría.

Usar una cuadrícula responsiva `sm:grid-cols-2 xl:grid-cols-5`; V2 no lleva recomendación.

- [ ] **Step 4: Mostrar resumen V4 en Banco de preguntas**

Leer `bank.raw?.bank?.curationSummary` y mostrar:

```tsx
<div aria-label="Resumen de curación V4">
  <span>{summary.approved} aprobadas</span>
  <span>{summary.repaired} reparadas</span>
  <span>{summary.rejected} rechazadas</span>
</div>
```

Para V2 mostrar `Fuente técnica conservada sin modificaciones`. Mantener ambos bancos como sólo lectura.

- [ ] **Step 5: Actualizar copias compactas**

En `app-shell.tsx`, añadir V4 y renombrar `mixed` a “Mixto curado”. En Dashboard y Session Builder, usar “V4 — cobertura amplia” cuando sea el perfil activo; no condicionar lógica por textos visibles.

- [ ] **Step 6: Ejecutar pruebas y accesibilidad básica**

Run: `npm.cmd test -- src/components/bank-selector.test.tsx src/components/session-builder-page.test.tsx`

Run: `npm.cmd run typecheck`

Expected: PASS.

- [ ] **Step 7: Commit del entregable**

```powershell
git add src/components/bank-selector.tsx src/components/bank-selector.test.tsx src/components/app-shell.tsx src/components/bank-manager-page.tsx src/components/dashboard-page.tsx src/components/session-builder-page.tsx
git commit -m "feat: present curated v4 across the interface"
```

---

### Task 7: E2E, documentación y verificación final

**Files:**
- Modify: `e2e/training-modes.spec.ts`
- Modify: `README.md`

**Interfaces:**
- Verifica el sistema completo construido en Tasks 1–6.

- [ ] **Step 1: Añadir E2E de instalación nueva y Mixto curado**

```ts
test("V4 es recomendado en una instalación nueva", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByText("Preparando tus bancos")).toBeHidden({ timeout: 30_000 })
  await page.getByRole("button", { name: "Banco de preguntas" }).click()
  await expect(page.getByRole("radio", { name: /V4 — Banco Curado/ })).toBeChecked()
  await expect(page.getByText(/aprobadas/)).toBeVisible()
  await expect(page.getByText(/reparadas/)).toBeVisible()
  await expect(page.getByText(/rechazadas/)).toBeVisible()
})

test("Mixto curado nunca inicia una pregunta V2", async ({ page }) => {
  await selectBank(page, "Mixto curado")
  await startLearnRound(page, 25)
  for (let index = 0; index < 25; index += 1) {
    await expect(page.getByText("V2", { exact: true })).toBeHidden()
    await answerAndAdvance(page, index === 24)
  }
})
```

- [ ] **Step 2: Añadir E2E de los cuatro flujos V4**

Parametrizar Aprender, Repaso inteligente y Simulacro para seleccionar explícitamente V4. Mantener la prueba de recarga y afirmar que el badge activo dice `V4` antes y después de recargar.

- [ ] **Step 3: Ejecutar E2E focalizado y corregir sólo fallos V4**

Run: `npx.cmd playwright test -g "V4|Mixto curado"`

Expected: PASS.

- [ ] **Step 4: Documentar perfiles y regeneración**

Añadir a README:

```md
### Perfiles de banco

- V4 — Banco Curado: cobertura amplia recomendada.
- V3 — Preparación intensiva de cuatro días.
- V2 — fuente técnica auditable; no participa en Mixto curado.

Regenerar y auditar V4:

    npm run build:v4
    npm run audit:v4
```

- [ ] **Step 5: Ejecutar la matriz final completa**

Run, en este orden:

```powershell
npm.cmd run build:v4
npm.cmd run audit:v4
node scripts/validate-prep-bank.mjs
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
npx.cmd playwright test
git diff --check
```

Expected:

- V4: cero bloqueadores.
- V3: 500 preguntas, 252 familias y cero hallazgos.
- Vitest: cero fallos.
- ESLint: cero errores.
- TypeScript: código 0.
- Vite build: código 0.
- Playwright: todos los flujos aprobados.
- `git diff --check`: sin errores de espacios.

- [ ] **Step 6: Revisar el diff y el reporte**

Confirmar manualmente:

- `Banco_Maestro_CB2026.json` conserva su SHA-256 inicial.
- Los dos bancos V4 sólo contienen estados `APPROVED`/`REPAIRED`.
- El número de decisiones es 3,558.
- Cada rechazo aparece en JSON y Markdown.
- No hay archivos `.tmp` ni artefactos de renderizado.
- No se incluyeron cambios ajenos a V4.

- [ ] **Step 7: Commit final**

```powershell
git add README.md e2e/training-modes.spec.ts
git commit -m "test: verify curated v4 workflows"
```

---

## Execution Notes

- El repositorio actualmente contiene cambios locales previos. Antes de cada commit, usar `git status --short` y añadir únicamente los archivos de la tarea.
- No usar `git reset --hard`, `git checkout --` ni restaurar archivos que pertenezcan al usuario.
- Si una regla nueva aumenta rechazos, informar la cifra y el código; no reducir la política para alcanzar una cuota.
- Si la auditoría completa descubre una contradicción semántica no resoluble automáticamente, clasificarla `REJECTED` y conservarla en el reporte.

