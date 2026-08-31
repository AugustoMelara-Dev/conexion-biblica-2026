# V10: privacidad de la reserva y frontera pública Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Garantizar que producción solo publique el banco entrenable y que ninguna presentación, opción, identificador ni metadato operativo de A/B/emergencia aparezca en el manifiesto, frontend, estadísticas, service worker, bundles, APIs o rutas públicas.

**Architecture:** El compilador emitirá dos contratos independientes: un artefacto público autosuficiente, sin referencias a la reserva, y un artefacto privado enlazado unilateralmente al `public_build_id`. El cliente eliminará toda capacidad de solicitar, representar o contabilizar pools privados. Un escáner de firmas de presentación inspeccionará `public/`, `dist/` y el deployment remoto; deliberadamente excluirá `fact_id`, respuesta canónica, referencia, fuente y soporte textual para no reportar como fuga el conocimiento que debe ser compartido.

**Tech Stack:** Python 3 (`unittest`, compilador V10), Node.js ESM (`node:test`, `fetch`, `crypto`), TypeScript 6, React 19, Vite 8, Vitest 3, Playwright 1.51, service worker nativo y Vercel.

**Spec:** `docs/superpowers/specs/2026-08-30-v10-cobertura-total-y-reserva-generalizacion-design.md`

## Global Constraints

- No eliminar ni reemplazar ninguna pregunta pública preexistente; las 250 preguntas anteriormente blind pasan al entrenamiento público.
- El manifiesto y los shards públicos describen exclusivamente el entrenamiento público; no contienen nombres, conteos, revisiones, rutas ni IDs de A/B/emergencia.
- Los 250 hechos privados sí comparten deliberadamente `fact_id`, respuesta canónica, fuente y soporte textual con entrenamiento público; estos campos nunca son firmas de fuga.
- Son secretos de presentación: `id`, `variant_id`, stem normalizado, estructura sintáctica, opciones, distractores, patrón de distractores y fingerprint editorial.
- La autoría privada canónica vive bajo `content/competitive-v11/private-blind/`; el artefacto efímero se compila en `output/private/competitive-v11-blind`. Ambos viven fuera de `public/` y `dist/`, no se importan desde `src/` y se excluyen del contexto enviado a Vercel.
- Vite no emite source maps de producción ni comentarios `sourceMappingURL`.
- El service worker solo precachea shell y manifiesto público, rechaza rutas reservadas y elimina cachés antiguas al activar la nueva versión.
- A/B/emergencia deben responder 404 en preview y en el deployment remoto; no se acepta un fallback SPA con HTTP 200.
- No desplegar hasta que compilación, pruebas unitarias, scanner local, build, scanner de `dist/`, E2E y auditoría remota del candidato estén en verde.
- Cualquier fallo del escáner o E2E posterior al despliegue bloquea la certificación y exige conservar o restaurar el deployment previo.

---

### Task 1: Convertir el artefacto público en un contrato autosuficiente sin metadatos blind

**Files:**
- Modify: `scripts/compile-competitive-v11.py`
- Modify: `scripts/test_competitive_v11.py`
- Modify: `scripts/test_audit_live_final_bank_integration.py`
- Regenerate: `public/banks/final-2026/manifest.json`
- Regenerate: `public/banks/final-2026/review-index.json`
- Regenerate: `public/banks/final-2026/questions/DAN1.json` through `public/banks/final-2026/questions/PR44.json`

**Interfaces:**
- Consumes: filas públicas y privadas ya clasificadas por el compilador V10 y el artefacto privado escrito mediante `--blind-output`.
- Produces: `public_build_descriptor(public_manifest: Mapping[str, Any]) -> dict[str, Any]`, `compute_public_build_id(public_manifest: Mapping[str, Any]) -> str` y filas públicas sin la clave `blind_pool`.
- Produces para el artefacto privado: `public_build_id: str`, que permite comprobar qué banco entrenable acompaña a la reserva sin publicar ningún hash o descriptor privado en sentido inverso.

- [ ] **Step 1: Escribir pruebas fallidas del nuevo manifiesto público**

Añadir a `CompetitiveV11Tests` una prueba que compile una fila pública y una privada, y que exija ausencia total de claves privadas:

```python
def test_public_artifact_contains_no_private_delivery_metadata(self) -> None:
    rows = [
        self.distinct_question(suffix="TRAIN", fact_id="F-SHARED", blind_pool=None),
        self.distinct_question(suffix="A", fact_id="F-SHARED", blind_pool="A"),
    ]
    directory = self.workspace_fixture("public-contract-v2")
    source = directory / "source"
    output = directory / "public-bank"
    blind_output = directory / "private-blind"
    self.write_compile_fixture(source, rows)
    compile_competitive_v11.compile_bank(source, output, blind_output=blind_output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    public_rows = json.loads(
        (output / "questions" / "DAN1.json").read_text(encoding="utf-8")
    )

    forbidden = {
        "blind_fact_count",
        "blind_presentation_count",
        "blind_pools",
        "blind_delivery",
        "total_fact_count",
        "total_presentation_count",
        "total_central_question_count",
        "total_presentation_variant_count",
        "total_families",
    }
    self.assertTrue(forbidden.isdisjoint(manifest))
    self.assertTrue(all("blind_pool" not in row for row in public_rows))
    self.assertEqual(manifest["unique_facts"], manifest["training_fact_count"])
    self.assertEqual(manifest["gold_questions"], manifest["training_presentation_count"])
```

En la misma prueba, verificar el enlace unilateral:

```python
private_manifest = json.loads(
    (blind_output / "manifest.json").read_text(encoding="utf-8")
)
self.assertEqual(private_manifest["public_build_id"], manifest["build_id"])
self.assertNotIn(private_manifest["artifact_revision"], json.dumps(manifest))
```

- [ ] **Step 2: Ejecutar la prueba y confirmar el rojo**

Run: `python -m unittest scripts.test_competitive_v11.CompetitiveV11Tests.test_public_artifact_contains_no_private_delivery_metadata -v`

Expected: FAIL porque el manifiesto actual contiene `blind_pools`, `blind_delivery` y totales combinados, y cada fila pública contiene `blind_pool`.

- [ ] **Step 3: Separar los descriptores y sanear las filas públicas**

En `scripts/compile-competitive-v11.py`, renombrar el cuerpo actual de `public_question()` a `_emitted_question_with_private_metadata()` sin cambiar su mapeo editorial, y añadir dos wrappers para evitar que la fila pública herede `blind_pool`:

```python
def public_question(raw: dict[str, Any], unit: str) -> dict[str, Any]:
    emitted = _emitted_question_with_private_metadata(raw, unit)
    emitted.pop("blind_pool", None)
    emitted["row_content_sha256"] = emitted_row_hash(emitted)
    return emitted


def private_question(raw: dict[str, Any], unit: str) -> dict[str, Any]:
    return _emitted_question_with_private_metadata(raw, unit)
```

Reemplazar el descriptor combinado por uno exclusivamente público:

```python
def public_build_descriptor(public_manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "contract": "competitive-v11-public-descriptor-v2",
        "schema_version": public_manifest["schema_version"],
        "bank_id": public_manifest["bank_id"],
        "counts": {
            key: public_manifest[key]
            for key in (
                "unique_facts",
                "gold_questions",
                "central_question_count",
                "presentation_variant_count",
                "training_fact_count",
                "training_presentation_count",
            )
        },
        "families": public_manifest["families"],
        "review_index": public_manifest["review_index"],
        "shards": public_manifest["shards"],
    }


def compute_public_build_id(public_manifest: Mapping[str, Any]) -> str:
    payload = json.dumps(
        public_build_descriptor(public_manifest),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
```

Al construir shards, llamar `public_question()` solo para `raw["blind_pool"] is None` y `private_question()` solo para las filas de A/B/emergencia. El manifiesto público debe conservar únicamente sus conteos públicos, familias públicas, `review_index`, shards y `build_id`. El manifiesto privado mantiene pools, conteos, `artifact_revision` y añade `public_build_id`; ningún campo público apunta al artefacto privado.

- [ ] **Step 4: Actualizar la validación del par sin reintroducir enlaces públicos**

Cambiar `validate_artifact_pair()` para recibir ambos artefactos de forma explícita y validar:

```python
if private_manifest.get("public_build_id") != public_manifest.get("build_id"):
    raise ValueError("blind artifact mismatch: public_build_id")
if public_manifest.get("build_id") != compute_public_build_id(public_manifest):
    raise ValueError("public artifact mismatch: build_id")
for forbidden_key in PUBLIC_PRIVATE_FORBIDDEN_KEYS:
    if forbidden_key in public_manifest:
        raise ValueError(f"public artifact leaks private metadata: {forbidden_key}")
```

`PUBLIC_PRIVATE_FORBIDDEN_KEYS` será una tupla constante con las nueve claves comprobadas en Step 1. La validación de tamaño 100/100/50, 45/30/25 y pools disjuntos se hace exclusivamente leyendo el manifiesto privado.

- [ ] **Step 5: Actualizar la integración HTTP para auditar público y privado por canales separados**

En `scripts/test_audit_live_final_bank_integration.py`, sustituir las expectativas de `blind_delivery` y `blind_pools` públicos por:

```python
self.assertNotIn("blind_delivery", public_manifest)
self.assertNotIn("blind_pools", public_manifest)
self.assertEqual(private_manifest["public_build_id"], public_manifest["build_id"])
self.assertEqual(
    private_manifest["pools"]["emergency"]["families"],
    requirements["emergency"]["families"],
)
```

El servidor público de la prueba solo montará `host/banks/final-2026`; el auditor privado recibirá `blindRoot` local y nunca una URL pública del artefacto privado.

- [ ] **Step 6: Ejecutar pruebas del compilador e integración**

Run: `python -m unittest scripts.test_competitive_v11 scripts.test_audit_live_final_bank_integration -v`

Expected: PASS; el artefacto público no conoce pools ni revisión privada y el privado queda enlazado al `public_build_id` correcto.

- [ ] **Step 7: Commit**

```bash
git add scripts/compile-competitive-v11.py scripts/test_competitive_v11.py scripts/test_audit_live_final_bank_integration.py
git commit -m "refactor: isolate private reserve metadata"
```

---

### Task 2: Reducir el contrato TypeScript al banco entrenable

**Files:**
- Modify: `src/storage/final-bank.ts`
- Modify: `src/storage/final-bank.test.ts`
- Modify: `src/storage/final-bank-v8.real.test.ts`
- Modify: `src/app/app-state.tsx`
- Modify: `src/app/app-state.test.tsx`

**Interfaces:**
- Consumes: `FinalBankManifest` público sin metadatos privados y shards donde toda fila es entrenable.
- Produces: `loadFinalQuestionPool(input)` sin parámetro `blindPool`; carga únicamente shards declarados por el manifiesto público.
- Produce: `FinalRawQuestion` sin `blind_pool`; `adaptFinalQuestion()` no genera `blindFinalPool` ni `blindPool`.

- [ ] **Step 1: Escribir pruebas fallidas del contrato entrenable**

En `src/storage/final-bank.test.ts`, construir un manifiesto público mínimo y comprobar que ninguna opción privada forma parte de la interfaz ni del resultado:

```ts
it("loads every public row as trainable without a private-pool contract", async () => {
  const manifest: FinalBankManifest = {
    schema_version: "10.0",
    bank_id: FINAL_BANK_ID,
    display_name: FINAL_BANK_DISPLAY_NAME,
    build_id: "a".repeat(64),
    gold_questions: 1,
    unique_facts: 1,
    training_fact_count: 1,
    training_presentation_count: 1,
    shards: [{ chapter: "DAN1", question_count: 1, training_question_count: 1, questions_file: "banks/final-2026/questions/DAN1.json" }],
  }
  const [question] = await loadFinalQuestionPool({
    manifest,
    chapters: [1],
    count: 1,
    seed: 7,
    fetcher: vi.fn(async () => new Response(JSON.stringify([raw()]))) as typeof fetch,
  })
  expect(question).not.toHaveProperty("blindPool")
  expect(question).not.toHaveProperty("blindFinalPool")
})
```

En `src/app/app-state.test.tsx`, intentar iniciar una configuración con `trainingPresetId: "blind-simulation"` y exigir que ya no exista ninguna rama/respuesta especial: el preset no está soportado y la sesión pública usa exclusivamente el pool entrenable.

- [ ] **Step 2: Ejecutar las pruebas y confirmar el rojo**

Run: `npm test -- --run src/storage/final-bank.test.ts src/app/app-state.test.tsx`

Expected: FAIL porque `FinalRawQuestion`, `loadFinalQuestionPool()` y `AppProvider` aún conocen `blind_pool`/`blindPool`.

- [ ] **Step 3: Eliminar el contrato privado del cargador público**

Modificar los tipos así:

```ts
export type FinalRawQuestion = {
  id: string
  fact_id: string
  variant_id: string
  question: string
  options: string[]
  correct_option: number
  correct_answer: string
  // conservar el resto de campos editoriales públicos existentes
}

export type FinalBankManifest = {
  schema_version: typeof FINAL_BANK_SCHEMA_VERSION | "9.0"
  bank_id: typeof FINAL_BANK_ID
  display_name: typeof FINAL_BANK_DISPLAY_NAME
  build_id: string
  gold_questions: number
  unique_facts: number
  training_fact_count: number
  training_presentation_count: number
  shards: Array<{
    chapter: string
    question_count: number
    training_question_count: number
    questions_file: string
    sha256?: string
  }>
}
```

Eliminar `blindPool` de la firma de `loadFinalQuestionPool()`, todas las ramas `row.blind_pool === ...`, y las propiedades privadas creadas en `adaptFinalQuestion()`. El cargador seguirá deduplicando por `fact_id`, filtrando familia/dificultad/tipo y adjuntando variantes públicas de reintento.

- [ ] **Step 4: Eliminar la selección privada del estado de aplicación**

En `src/app/app-state.tsx`:

- quitar `"blind-simulation"` de `FACT_MASTERY_PRESETS`;
- quitar la rama especial en `factFilterForPreset()`;
- eliminar el cálculo `blindPool` para `final-v7` y `consolidation-v5`;
- no pasar `blindPool` a `loadFinalQuestionPool()`;
- eliminar el error “La reserva ciega está protegida…” porque el cliente ya no conoce esa capacidad.

La llamada pública queda:

```ts
const gold = await loadFinalQuestionPool({
  manifest: finalManifest,
  chapters,
  count: Math.min(adaptivePoolCount, finalManifest.gold_questions),
  difficultyBands: config.difficultyBands,
  types: config.types,
  family:
    config.trainingPresetId === "27-context" ||
    config.trainingPresetId === "contextual-traps"
      ? "single_choice_contextual"
      : config.trainingPresetId === "27-fill"
        ? "fill_choice"
        : config.trainingPresetId === "27-true-false"
          ? "true_false"
          : undefined,
  seenFactIds: new Set(exposures.map((exposure) => exposure.factId)),
  exposures,
  factFilter: effectiveFactFilter,
  seed: Date.now(),
})
```

- [ ] **Step 5: Ejecutar pruebas del cargador y estado**

Run: `npm test -- --run src/storage/final-bank.test.ts src/storage/final-bank-v8.real.test.ts src/app/app-state.test.tsx`

Expected: PASS; no existe ninguna ruta de datos cliente capaz de elegir A/B/emergencia.

- [ ] **Step 6: Commit**

```bash
git add src/storage/final-bank.ts src/storage/final-bank.test.ts src/storage/final-bank-v8.real.test.ts src/app/app-state.tsx src/app/app-state.test.tsx
git commit -m "refactor: expose only trainable final bank"
```

---

### Task 3: Retirar controles, textos y estadísticas privadas del frontend público

**Files:**
- Modify: `src/domain/types.ts`
- Modify: `src/domain/training-modes.ts`
- Modify: `src/domain/training-modes.test.ts`
- Modify: `src/domain/final-48h-plan.ts`
- Modify: `src/domain/final-48h-plan.test.ts`
- Modify: `src/domain/final-mission-plan.ts`
- Modify: `src/domain/final-mission-plan.test.ts`
- Modify: `src/domain/final-mission-selection.ts`
- Modify: `src/domain/final-mission-selection.test.ts`
- Modify: `src/domain/adaptive-session.ts`
- Modify: `src/domain/adaptive-session.test.ts`
- Modify: `src/domain/fact-mastery.ts`
- Modify: `src/domain/fact-mastery.test.ts`
- Modify: `src/domain/readiness.ts`
- Modify: `src/domain/readiness.test.ts`
- Modify: `src/domain/backup.ts`
- Modify: `src/domain/backup.test.ts`
- Modify: `src/lib/learning-metrics.ts`
- Modify: `src/lib/learning-metrics.test.ts`
- Modify: `src/components/massive-training-hub.tsx`
- Modify: `src/components/massive-training-hub.test.tsx`
- Modify: `src/components/dashboard-page.tsx`
- Modify: `src/components/final-mission-dashboard.tsx`
- Modify: `src/components/final-mission-dashboard.test.tsx`
- Modify: `src/components/statistics-page.tsx`
- Modify: `src/components/insight-pages.test.tsx`
- Modify: `src/components/quiz-page.tsx`
- Modify: `src/components/quiz-page.test.tsx`
- Modify: `src/storage/db.ts`
- Modify: `src/storage/consolidation-bank.ts`
- Modify: `src/storage/consolidation-bank.test.ts`
- Modify: `src/storage/massive-bank.ts`
- Modify: `src/storage/massive-bank.test.ts`
- Modify: `src/storage/storage.test.ts`
- Modify: `src/storage/history-migration.ts`
- Modify: `src/storage/history-migration.test.ts`
- Modify: `src/app/app-state.tsx`
- Modify: `src/app/app-state.test.tsx`
- Modify: `e2e/training-modes.spec.ts`
- Modify: `e2e/production-learning-endurance.spec.ts`
- Modify: `e2e/resilience.spec.ts`

**Interfaces:**
- Consumes: solo exposiciones públicas `practice | cold | deferred` y modos entrenables.
- Produces: `EvidenceKind = "practice" | "cold" | "deferred"`; `SessionConfig` sin `includeBlind`; `Question`, `QuestionSessionQuery` y `BackupPayload` sin campos de pool o uso privado.
- Produce: plan final público sin misiones `27-blind-a`, `27-blind-b` ni `d2-blind-final`.

- [ ] **Step 1: Escribir pruebas fallidas de ausencia en la UI**

En `src/components/massive-training-hub.test.tsx` sustituir el caso `blindAvailable` por:

```tsx
it("never renders reserve controls or copy in the public hub", () => {
  render(<MassiveTrainingHub onStart={vi.fn()} />)
  expect(screen.queryByText(/ciega|reserva|A\/B|emergencia/i)).not.toBeInTheDocument()
  expect(screen.queryByRole("button", { name: /simulación ciega/i })).not.toBeInTheDocument()
})
```

En `src/components/insight-pages.test.tsx`, comprobar:

```tsx
expect(screen.queryByText(/Prueba ciega|Precisión ciega|Reserva A\/B/i)).not.toBeInTheDocument()
```

En `src/domain/training-modes.test.ts` y `src/domain/final-mission-plan.test.ts`:

```ts
expect(MASSIVE_TRAINING_MODES.map((mode) => mode.id)).not.toContain("blind-simulation")
expect(buildFinalMissionPlan().some((mission) => /blind|ciega/i.test(mission.id + mission.label))).toBe(false)
```

- [ ] **Step 2: Ejecutar las pruebas y confirmar el rojo**

Run: `npm test -- --run src/components/massive-training-hub.test.tsx src/components/insight-pages.test.tsx src/domain/training-modes.test.ts src/domain/final-mission-plan.test.ts`

Expected: FAIL porque los controles, textos, planes y métricas privadas aún están en el árbol público.

- [ ] **Step 3: Eliminar tipos y persistencia privados sin romper respaldos anteriores**

En `src/domain/types.ts`, eliminar:

- `Question.blindFinalPool` y `Question.blindPool`;
- `SessionConfig.includeBlind`;
- `QuestionSessionQuery.includeBlind`;
- `BlindUsage` y `BackupPayload.blindUsage`;
- el miembro `blind` de `QuestionExposure.evidence` y `ExposureAttempt.exposureKind`.

Conservar compatibilidad de lectura en `src/domain/backup.ts` descartando datos legacy, sin volver a exponerlos en el objeto migrado:

```ts
export function migrateBackupPayload(raw: unknown): BackupPayload {
  const validation = validateBackupPayload(raw)
  if (!validation.valid)
    throw new Error(validation.errors.map((error) => `${error.path}: ${error.message}`).join("\n"))
  const legacy = structuredClone(raw) as Record<string, unknown>
  delete legacy.blindUsage
  return migrateValidatedPublicBackup(legacy)
}
```

Renombrar el cuerpo actual que sigue a la validación en `migrateBackupPayload()` a `migrateValidatedPublicBackup(payload: Record<string, unknown>): BackupPayload`; esa función conserva la migración 1.0→2.0 existente y `normalizeContexts()`, pero `normalizeContexts()` deja de añadir `blindUsage`.

En `src/storage/db.ts`, incrementar la versión de IndexedDB y eliminar el object store `blindUsage` dentro de `onupgradeneeded` si existe:

```ts
if (db.objectStoreNames.contains("blindUsage")) db.deleteObjectStore("blindUsage")
```

- [ ] **Step 4: Retirar modos, misiones y selección privadas**

Eliminar `blind-simulation` de `MassiveTrainingModeId` y `MASSIVE_TRAINING_MODES`; eliminar los bloques `27-blind-a`, `27-blind-b` y `d2-blind-final`. Simplificar `FinalMission` a:

```ts
export type FinalMission = {
  id: string
  date: string
  label: string
  description: string
  count: number
  durationMinutes: number
  chapters: number[]
  exposureKind: "practice" | "cold" | "deferred"
  mode: "smart-review" | "simulation"
}
```

En `final-mission-selection.ts` y `adaptive-session.ts`, eliminar filtros y ramas que consulten `blindPool`/`blindFinalPool`; la unicidad por hecho, GOLD, dificultad y balance público permanecen intactos.

- [ ] **Step 5: Retirar textos, controles y métricas privadas**

En `massive-training-hub.tsx`, eliminar la prop `blindAvailable`, el filtrado condicional, el badge “Reserva ciega protegida” y toda copia de cierre ciego. En `dashboard-page.tsx`, eliminar “Precisión ciega / Reserva A/B” y construir `missionConfig()` sin `includeBlind`. En `statistics-page.tsx` y `learning-metrics.ts`, eliminar `learning.blind` y `EvidenceMetric` asociado. En `readiness.ts`, renombrar `blindOrNovelAccuracy` a `novelAccuracy` conservando el peso 0.3. En `consolidation-bank.ts` y `massive-bank.ts`, eliminar parámetros y filtros `blindPool`, `blindOnly` e `includeBlind`; ambas cargas retornan solamente filas públicas. En `quiz-page.tsx`, asignar `exposureKind` únicamente desde el contexto público:

```ts
const exposureKind = config.mode === "simulation" ? "cold" : "practice"
```

- [ ] **Step 6: Ajustar pruebas de migración, dominio, componentes y E2E**

Las pruebas de respaldos legacy deben introducir un `blindUsage` de entrada y comprobar que se descarta:

```ts
const migrated = migrateBackupPayload({ ...validLegacyBackup, blindUsage: [{ pool: "A" }] })
expect(migrated).not.toHaveProperty("blindUsage")
```

`e2e/training-modes.spec.ts` debe comprobar desde la interfaz real:

```ts
await expect(page.getByText(/simulación ciega|reserva A\/B|emergencia/i)).toHaveCount(0)
```

- [ ] **Step 7: Ejecutar el lote completo del frontend público**

Run: `npm test -- --run src/domain/types.ts src/domain/training-modes.test.ts src/domain/final-48h-plan.test.ts src/domain/final-mission-plan.test.ts src/domain/final-mission-selection.test.ts src/domain/adaptive-session.test.ts src/domain/fact-mastery.test.ts src/domain/readiness.test.ts src/domain/backup.test.ts src/lib/learning-metrics.test.ts src/components/massive-training-hub.test.tsx src/components/final-mission-dashboard.test.tsx src/components/insight-pages.test.tsx src/components/quiz-page.test.tsx src/storage/consolidation-bank.test.ts src/storage/massive-bank.test.ts src/storage/storage.test.ts src/storage/history-migration.test.ts src/app/app-state.test.tsx`

Run: `npm run typecheck`

Expected: PASS; no interfaz, configuración, estadística ni respaldo público conoce A/B/emergencia.

- [ ] **Step 8: Commit**

```bash
git add src e2e/training-modes.spec.ts
git commit -m "refactor: remove reserve controls from public client"
```

---

### Task 4: Blindar la frontera de build, Vercel, source maps y service worker

**Files:**
- Create: `.vercelignore`
- Modify: `vite.config.ts`
- Modify: `vercel.json`
- Modify: `public/sw.js`
- Modify: `src/deployment-cache.test.ts`
- Modify: `src/service-worker.test.ts`

**Interfaces:**
- Consumes: repositorio con contenido privado bajo `content/competitive-v11/` y artefactos privados bajo `output/`.
- Produces: upload de Vercel sin `content/`, `output/`, `scripts/`, documentos, pruebas ni PDF fuente; build Vite sin mapas; service worker `conexion-biblica-shell-v12` que devuelve 404 local para rutas reservadas.

- [ ] **Step 1: Escribir pruebas fallidas de configuración**

En `src/deployment-cache.test.ts` añadir:

```ts
it("excludes source and private artifacts from Vercel and disables source maps", () => {
  const ignored = readFileSync(join(process.cwd(), ".vercelignore"), "utf8")
  for (const path of ["content/", "output/", "reports/", "scripts/", "docs/", "e2e/", "*.pdf"])
    expect(ignored.split(/\r?\n/)).toContain(path)

  const vite = readFileSync(join(process.cwd(), "vite.config.ts"), "utf8")
  expect(vite).toContain("sourcemap: false")
})
```

En `src/service-worker.test.ts` añadir una solicitud a `/banks/final-2026/blind/A.json` y exigir 404, cero fetch y cero escritura en caché.

- [ ] **Step 2: Ejecutar las pruebas y confirmar el rojo**

Run: `npm test -- --run src/deployment-cache.test.ts src/service-worker.test.ts`

Expected: FAIL porque `.vercelignore` no existe, Vite no declara `sourcemap: false` y el worker actual intenta resolver cualquier `/banks/`.

- [ ] **Step 3: Crear la allowlist negativa del upload de Vercel**

Crear `.vercelignore` exactamente con:

```text
content/
output/
reports/
docs/
scripts/
e2e/
playwright-report/
test-results/
tmp/
*.pdf
```

Estas rutas no son necesarias para `tsc -b && vite build`; `public/` y `src/` permanecen disponibles.

- [ ] **Step 4: Desactivar mapas y endurecer cabeceras públicas**

En `vite.config.ts`:

```ts
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: { sourcemap: false },
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "./src") } },
})
```

En `vercel.json`, añadir `X-Content-Type-Options: nosniff` a `/banks/(.*)`. No añadir `rewrites` que conviertan rutas inexistentes en `index.html`; la ausencia física de archivos privados debe producir el 404 nativo de Vercel, comprobado en Tasks 6 y 7.

- [ ] **Step 5: Rechazar rutas reservadas antes de consultar red o caché**

En `public/sw.js`:

```js
const CACHE_NAME = "conexion-biblica-shell-v12"
const RESERVED_PATH = /(?:^|\/)(?:blind|private|emergency|competitive-v11-blind)(?:\/|$)/i

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return
  const requestUrl = new URL(event.request.url)
  if (RESERVED_PATH.test(requestUrl.pathname)) {
    event.respondWith(Promise.resolve(new Response("Not Found", { status: 404 })))
    return
  }
  // conservar después las estrategias actuales de navegación y /banks/ públicas
})
```

La activación de v12 borra todos los cachés `conexion-biblica-shell-*` distintos de v12, evitando que una versión anterior conserve datos obsoletos.

- [ ] **Step 6: Construir y comprobar la salida física**

Run: `npm test -- --run src/deployment-cache.test.ts src/service-worker.test.ts`

Run: `npm run build`

Run: `Get-ChildItem dist -Recurse -File | Where-Object { $_.Extension -eq '.map' -or (Select-String -LiteralPath $_.FullName -SimpleMatch 'sourceMappingURL' -Quiet) }`

Expected: las pruebas pasan y el último comando no produce salida.

- [ ] **Step 7: Commit**

```bash
git add .vercelignore vite.config.ts vercel.json public/sw.js src/deployment-cache.test.ts src/service-worker.test.ts
git commit -m "build: harden public deployment boundary"
```

---

### Task 5: Crear el escáner Python de firmas privadas sin falsos positivos factuales

**Files:**
- Create: `scripts/audit-blind-privacy-v11.py`
- Create: `scripts/test_audit_blind_privacy_v11.py`
- Modify: `package.json`

**Interfaces:**
- Produces: `load_private_signature_index(private_root: Path) -> LeakSignatureIndex`.
- Produce: `scan_directory(root: Path, index: LeakSignatureIndex, label: Literal["public", "dist"]) -> list[LeakFinding]`.
- Produce: `scan_artifact(path: str, payload: bytes, index: LeakSignatureIndex) -> list[LeakFinding]`.
- `LeakSignatureIndex` contiene `presentation_ids`, `variant_ids`, `normalized_stems`, `normalized_option_sets`, `normalized_distractor_sets`, `editorial_fingerprints`; no contiene `fact_id`, `correct_answer`, `reference`, `source_ref`, `source_span`, `source_quote` ni `evidence_excerpt`. El scanner también rechaza rutas bajo `public/` o `dist/` cuyo nombre contenga `private-blind`/`competitive-v11-blind`, y las claves estructurales públicas `blind_pool`, `blind_pools` o `blind_delivery`.
- CLI: `python scripts/audit-blind-privacy-v11.py --private-root <dir> --public-root public --dist-root dist [--base-url <url>]` y salida JSON `{ "ok": bool, "scanned": int, "findings": list }`.

- [ ] **Step 1: Escribir pruebas fallidas de construcción de firmas**

En `scripts/test_audit_blind_privacy_v11.py`, crear un fixture privado temporal con una pregunta y comprobar inclusiones/exclusiones:

```python
def test_indexes_presentation_secrets_but_excludes_shared_factual_fields(self) -> None:
    index = privacy.load_private_signature_index(self.private_root)
    self.assertIn("BLIND-A-001", index.presentation_ids)
    self.assertIn("BLIND-VAR-001", index.variant_ids)
    self.assertIn(
        privacy.normalize_text("¿Qué detalle distinguió la escena?"),
        index.normalized_stems,
    )
    serialized = json.dumps(dataclasses.asdict(index), ensure_ascii=False)
    self.assertNotIn("FACT-DAN10-001", serialized)
    self.assertNotIn("Miguel", serialized)
    self.assertNotIn("Daniel 10:13", serialized)
```
```

- [ ] **Step 2: Escribir pruebas fallidas de detección y falsos positivos**

Añadir casos que exijan:

```python
def test_does_not_flag_legitimate_shared_fact_answer_or_source(self) -> None:
    payload = json.dumps({
        "fact_id": "FACT-DAN10-001",
        "correct_answer": "Miguel",
        "reference": "Daniel 10:13",
        "source_quote": "Miguel, uno de los principales príncipes",
    }, ensure_ascii=False).encode("utf-8")
    self.assertEqual(privacy.scan_artifact("public.json", payload, self.index), [])

def test_flags_ids_stems_option_sets_distractors_and_fingerprints(self) -> None:
    for leaked in self.private_documents:
        self.assertTrue(
            privacy.scan_artifact("asset.js", leaked.encode("utf-8"), self.index)
        )
```
```

La prueba de opciones usará el conjunto completo normalizado; una opción aislada como “Miguel” no dispara el scanner.

- [ ] **Step 3: Ejecutar las pruebas y confirmar el rojo**

Run: `python -m unittest scripts.test_audit_blind_privacy_v11 -v`

Expected: FAIL con `ModuleNotFoundError` porque el scanner aún no existe.

- [ ] **Step 4: Implementar normalización e índice privado**

Implementar:

```python
def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[¿?¡!.,;:()\"“”'‘’]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def presentation_fingerprint(row: Mapping[str, Any]) -> str:
    descriptor = {
        "stem": normalize_text(row["question"]),
        "syntax": row.get("presentation_syntax", row.get("syntax_signature", "")),
        "options": [normalize_text(option) for option in row["options"]],
        "distractors": sorted(
            normalize_text(option)
            for index, option in enumerate(row["options"])
            if index != row["correct_option"]
        ),
        "pattern": row.get("distractor_pattern", ""),
    }
    payload = json.dumps(descriptor, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
```
```

`loadPrivateSignatureIndex()` recorre exclusivamente los shards declarados por el manifiesto privado. Rechaza una fila sin `id`, `variant_id`, stem, opciones o fingerprint. Nunca serializa ni indexa campos factuales compartidos.

- [ ] **Step 5: Implementar inspección estructural y textual**

Para JSON, parsear recursivamente objetos y arrays: comparar `id`, `variant_id`, stem normalizado, conjunto completo normalizado de opciones, conjunto completo de distractores y fingerprint; reportar además cualquier clave `blind_pool`, `blind_pools` o `blind_delivery`. Para JS/HTML/CSS/service worker, buscar IDs y fingerprints exactos, stems normalizados de al menos 24 caracteres y arrays de strings decodificables; no buscar respuestas u opciones individuales. `scan_directory()` falla antes de leer el contenido si una ruta pública contiene `private-blind` o `competitive-v11-blind`, cubriendo reportes y artefactos QC privados copiados por error.

Cada hallazgo tendrá:

```python
LeakFinding(
    artifact="dist/assets/index-AbCd.js",
    kind="presentation_id",
    signature="sha256:redacted-for-report",
    offset=1042,
)
```

El reporte nunca imprime el texto privado, solo el hash de la firma y la ubicación.

- [ ] **Step 6: Implementar CLI y scripts de paquete**

Agregar a `package.json`:

```json
{
  "scripts": {
    "audit:privacy:local": "python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --public-root public",
    "audit:privacy:dist": "python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --dist-root dist",
    "audit:privacy:remote": "python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --base-url https://conexion-biblica-2026.vercel.app"
  }
}
```

El CLI termina con código 1 ante cualquier hallazgo o artefacto privado inválido, y con código 0 únicamente cuando `findings` es `[]`.

- [ ] **Step 7: Ejecutar pruebas y escaneos locales**

Run: `python -m unittest scripts.test_audit_blind_privacy_v11 -v`

Run: `npm run audit:privacy:local`

Run: `npm run build && npm run audit:privacy:dist`

Expected: PASS y `{ "ok": true, "findings": [] }` tanto para `public/` como para `dist/`.

- [ ] **Step 8: Commit**

```bash
git add scripts/audit-blind-privacy-v11.py scripts/test_audit_blind_privacy_v11.py package.json
git commit -m "test: add private presentation leak scanner"
```

---

### Task 6: Auditar rutas, red del navegador y contenido remoto

**Files:**
- Modify: `scripts/audit-blind-privacy-v11.py`
- Modify: `scripts/test_audit_blind_privacy_v11.py`
- Create: `e2e/private-reserve-boundary.spec.ts`
- Modify: `playwright.config.ts`

**Interfaces:**
- Produces: `discover_remote_resources(base_url: str) -> list[str]`, limitado al mismo origen y alimentado por HTML, `manifest.webmanifest`, `sw.js`, manifiesto del banco y sus shards.
- Produce: `scan_remote(base_url: str, index: LeakSignatureIndex) -> RemoteScanResult` con `findings`, `resources` y `probes`.
- Produce: `reserved_route_candidates(private_manifest: Mapping[str, Any]) -> list[str]`; cada candidato debe devolver 404 y `Content-Type` no ejecutable.

- [ ] **Step 1: Escribir pruebas fallidas del crawler y las rutas 404**

En el unittest Python, levantar un `ThreadingHTTPServer` temporal que sirva `/`, un bundle y manifiesto públicos, y que accidentalmente responda 200 a `/api/blind/A`. Exigir:

```python
result = privacy.scan_remote(self.origin, self.index)
self.assertIn(f"{self.origin}/assets/index.js", result.resources)
self.assertTrue(
    any(item.kind == "reserved_route_exposed" for item in result.findings)
)
```

Después configurar el fixture para devolver 404 y comprobar `findings: []`.

- [ ] **Step 2: Ejecutar el test y confirmar el rojo**

Run: `python -m unittest scripts.test_audit_blind_privacy_v11 -v`

Expected: FAIL porque aún no existen `discover_remote_resources()`, `scan_remote()` ni `reserved_route_candidates()`.

- [ ] **Step 3: Implementar descubrimiento remoto cerrado**

El crawler seguirá solo:

- `/`, `/index.html`, `/manifest.webmanifest`, `/sw.js`;
- scripts, styles, modulepreload e iconos del HTML;
- `public/banks/final-2026/manifest.json`;
- `review_index.file` y cada `shards[].questions_file` del manifiesto público.

Rechazará redirects fuera del origen y limitará cada respuesta a 20 MiB. Escaneará bytes antes de interpretar JSON. No enumerará directorios ni seguirá URLs introducidas por contenido no canónico.

- [ ] **Step 4: Implementar probes negativos de rutas**

`reserved_route_candidates()` devolverá al menos:

```python
[
  "/blind/manifest.json",
  "/private/manifest.json",
  "/banks/final-2026/blind/manifest.json",
  "/banks/final-2026/questions/A/DAN1.json",
  "/banks/final-2026/questions/B/DAN1.json",
  "/banks/final-2026/questions/emergency/DAN1.json",
  "/api/blind",
  "/api/blind/A",
  "/api/blind/B",
  "/api/blind/emergency",
]
```

Una respuesta 200, redirect, fallback HTML o cuerpo con firma privada genera `reserved_route_exposed`. Solo 404 es aprobado.

- [ ] **Step 5: Crear E2E de red y service worker**

En `e2e/private-reserve-boundary.spec.ts`:

```ts
test("the public client never requests reserve resources", async ({ page }) => {
  const requested: string[] = []
  page.on("request", (request) => requested.push(new URL(request.url()).pathname))
  await page.goto("/")
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
  await page.getByRole("button", { name: "Practicar" }).click()
  expect(requested.filter((path) => /blind|private|emergency|\/questions\/(?:A|B)\//i.test(path))).toEqual([])
})

test("reserve routes are genuine 404 responses", async ({ request }) => {
  for (const path of RESERVED_ROUTE_PROBES) {
    const response = await request.get(path, { maxRedirects: 0 })
    expect(response.status(), path).toBe(404)
  }
})

test("service-worker caches contain public resources only", async ({ page }) => {
  await page.goto("/")
  await page.evaluate(async () => navigator.serviceWorker.ready)
  const cached = await page.evaluate(async () =>
    (await Promise.all((await caches.keys()).map(async (name) =>
      (await caches.open(name).then((cache) => cache.keys())).map((request) => new URL(request.url).pathname)
    ))).flat()
  )
  expect(cached.filter((path) => /blind|private|emergency|\/questions\/(?:A|B)\//i.test(path))).toEqual([])
})
```

Exportar `RESERVED_ROUTE_PROBES` desde un archivo compartido E2E o repetir exactamente la lista del scanner; no usar comodines que puedan aceptar un 200 accidental.

- [ ] **Step 6: Ejecutar preview, E2E y scanner remoto local**

Run: `npm run build`

Run: `npx playwright test e2e/private-reserve-boundary.spec.ts --project=desktop-chromium`

Run: `python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --base-url http://127.0.0.1:4173`

Expected: PASS; cero solicitudes privadas, cachés limpias, diez rutas 404 y cero firmas encontradas en todos los recursos descubiertos.

- [ ] **Step 7: Ejecutar la matriz E2E de frontera**

Run: `npx playwright test e2e/private-reserve-boundary.spec.ts`

Expected: PASS en Chromium, Firefox y WebKit, desktop y móvil.

- [ ] **Step 8: Commit**

```bash
git add scripts/audit-blind-privacy-v11.py scripts/test_audit_blind_privacy_v11.py e2e/private-reserve-boundary.spec.ts playwright.config.ts
git commit -m "test: verify reserve boundary over browser and HTTP"
```

---

### Task 7: Integrar la puerta de privacidad a la certificación y verificar el deployment

**Files:**
- Modify: `scripts/audit-live-final-bank.mjs`
- Modify: `scripts/audit-live-final-bank.check.mjs`
- Modify: `package.json`
- Create: `docs/runbooks/v10-private-reserve-release.md`

**Interfaces:**
- Consumes: manifiesto público autosuficiente, artefacto privado local, scanner de privacidad y URL candidata.
- Produce: `auditLiveFinalBank({ baseUrl, publicRoot })` que solo valida el banco público; la validación privada se ejecuta localmente mediante el compilador y el scanner.
- Produce: `npm run verify:privacy-release`, puerta local determinista previa al despliegue.

- [ ] **Step 1: Escribir pruebas fallidas del auditor público independiente**

En `scripts/audit-live-final-bank.check.mjs`, crear un fixture de manifiesto público sin `blind_delivery` y exigir que pase sin `blindBaseUrl`/`blindRoot`:

```js
test("public production audit needs no private manifest or route", async () => {
  const result = await auditLiveFinalBank({
    baseUrl: fixture.origin,
    publicRoot: fixture.publicRoot,
  })
  assert.deepEqual(result.failures, [])
  assert.equal(result.questions, fixture.publicQuestions.length)
  assert.equal(result.blindQuestions, undefined)
})
```

Añadir otro fixture que inserte `blind_pools` en el manifiesto público y exigir `manifest:private_metadata_leak`.

- [ ] **Step 2: Ejecutar el auditor y confirmar el rojo**

Run: `node --test scripts/audit-live-final-bank.check.mjs`

Expected: FAIL porque el auditor actual exige `blind_delivery`, descarga el artefacto privado y calcula totales combinados.

- [ ] **Step 3: Convertir el auditor live en auditor estrictamente público**

Eliminar `BLIND_CONTRACT`, `BLIND_ARTIFACT_ID`, `auditPrivateArtifact()` y todas las lecturas remotas privadas. Añadir:

```js
const FORBIDDEN_PUBLIC_MANIFEST_KEYS = new Set([
  "blind_fact_count", "blind_presentation_count", "blind_pools", "blind_delivery",
  "total_fact_count", "total_presentation_count", "total_central_question_count",
  "total_presentation_variant_count", "total_families",
])

for (const key of FORBIDDEN_PUBLIC_MANIFEST_KEYS) {
  if (key in manifest) fail(context, `manifest:private_metadata_leak:${key}`)
}
```

En cada shard público, fallar si existe `blind_pool`, incluso con valor `null`.

- [ ] **Step 4: Crear la puerta agregada previa al despliegue**

Añadir a `package.json`:

```json
{
  "scripts": {
    "verify:privacy-release": "python -m unittest scripts.test_competitive_v11 scripts.test_audit_live_final_bank_integration scripts.test_audit_blind_privacy_v11 && node --test scripts/audit-live-final-bank.check.mjs && npm run typecheck && npm test -- --run && npm run build && npm run audit:privacy:local && npm run audit:privacy:dist && npx playwright test e2e/private-reserve-boundary.spec.ts --project=desktop-chromium"
  }
}
```

- [ ] **Step 5: Documentar el runbook reversible**

`docs/runbooks/v10-private-reserve-release.md` debe contener estos comandos exactos y criterios:

```powershell
git rev-parse HEAD
npm run verify:privacy-release
vercel deploy --yes
$env:PLAYWRIGHT_BASE_URL='<candidate-url>'
npx playwright test e2e/private-reserve-boundary.spec.ts --project=desktop-chromium
python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --base-url '<candidate-url>'
vercel promote '<candidate-url>' --yes
python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --base-url 'https://conexion-biblica-2026.vercel.app'
```

Registrar antes del promote la URL y Git SHA del deployment vigente. Si la verificación posterior falla, no certificar el release y promover nuevamente la URL previa mediante `vercel promote '<previous-production-url>' --yes`.

- [ ] **Step 6: Ejecutar todas las puertas locales**

Run: `node --test scripts/audit-live-final-bank.check.mjs`

Run: `npm run verify:privacy-release`

Expected: PASS; scanner local y `dist/` sin hallazgos, E2E Chromium en verde.

- [ ] **Step 7: Revisar el diff de frontera antes de cualquier deployment**

Run: `git diff --check`

Run: `git diff --stat HEAD~6..HEAD`

Run: `git grep -n -E 'blind_delivery|blind_pools|blind_pool|Simulación ciega|Reserva A/B|27-blind|d2-blind' -- public src`

Expected: `git diff --check` sin salida; el grep sin coincidencias en `public/` y sin cadenas alcanzables desde el frontend público.

- [ ] **Step 8: Commit de la puerta de release**

```bash
git add scripts/audit-live-final-bank.mjs scripts/audit-live-final-bank.check.mjs package.json docs/runbooks/v10-private-reserve-release.md
git commit -m "ci: gate releases on private reserve isolation"
```

- [ ] **Step 9: Verificar candidato y producción sin promover a ciegas**

Run: `vercel deploy --yes`

Run: `$env:PLAYWRIGHT_BASE_URL='<candidate-url>'; npx playwright test e2e/private-reserve-boundary.spec.ts --project=desktop-chromium`

Run: `python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --base-url '<candidate-url>'`

Expected: ambos PASS. Solo entonces ejecutar `vercel promote '<candidate-url>' --yes` y repetir el E2E y scanner contra `https://conexion-biblica-2026.vercel.app`.

- [ ] **Step 10: Registrar evidencia de certificación**

Anotar en el reporte final: Git SHA, deployment anterior, candidate URL, production URL, salida de `verify:privacy-release`, cantidad de recursos remotos inspeccionados, diez probes 404, seis proyectos E2E y `findings: []`. Clasificar privacidad como `STAGING_VERIFIED` antes del promote y `STAGING_VERIFIED` o `LOCALLY_VERIFIED` —nunca “producción verificada”— si la comprobación contra el dominio público no se ejecutó realmente.

---

## Self-Review

- Cobertura de especificación: Tasks 1–3 eliminan metadatos, controles, estadísticas y rutas cliente; Task 4 blinda upload, source maps y service worker; Tasks 5–6 inspeccionan IDs, variantes, stems, opciones, distractores y fingerprints sin usar campos factuales compartidos; Task 7 integra las puertas, reversibilidad y verificación remota.
- Falsos positivos: el índice excluye expresamente `fact_id`, respuesta canónica, referencia, fuente y soporte; opciones/distractores solo se denuncian como conjuntos completos, nunca como palabras aisladas.
- Frontera pública/privada: el enlace solo fluye de privado a `public_build_id`; el manifiesto público no declara la existencia, tamaño, revisión ni rutas de la reserva.
- Rutas: preview, candidate y producción deben devolver 404 real para cada probe; service worker no consulta red ni caché para rutas reservadas.
- Build: `public/`, `dist/`, source maps y recursos remotos son puertas independientes; pasar una no sustituye las demás.
