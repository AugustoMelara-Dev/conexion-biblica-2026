# V6 Mandatory Mix and Learning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activar al menos 5,000 preguntas GOLD fieles al PDF, imponer la mezcla competitiva 30/25/45 y medir recuperación real en lugar de exposición.

**Architecture:** La canalización Python construirá variantes editoriales desde hechos atómicos respaldados por tramos exactos del PDF, con validadores separados para completar, V/F y selección contextual. El selector TypeScript recibirá cuotas explícitas y escogerá un solo `fact_id` por ronda. El modelo de dominio conservará evidencia temporal y la interfaz mostrará las nuevas métricas sin mezclar corrección inmediata con dominio.

**Tech Stack:** Python 3 + PyMuPDF, React 19, TypeScript, IndexedDB, Vitest y Playwright.

**Spec:** `docs/superpowers/specs/2026-08-26-mezcla-obligatoria-aprendizaje-v6.md`

## Global Constraints

- Fuente única `MaterialConexionBiblica (1).pdf`; no internet ni traducciones externas.
- GOLD >= 5,000: completar >= 1,500, V/F >= 1,250, selección >= 2,250.
- Capítulos prioritarios y mezcla por sesión cumplen exactamente los mínimos de la especificación.
- No se repite `fact_id` en una ronda normal; la reserva ciega permanece aislada.
- Toda función nueva se desarrolla con prueba fallida primero.

---

### Task 1: Contrato editorial V6

**Files:**
- Modify: `scripts/lib/gold_quality.py`
- Modify: `scripts/test_gold_quality.py`
- Modify: `scripts/audit-gold-bank.py`

**Interfaces:**
- Produces: `build_consolidation_bank(root)` con manifiesto >=5,000 y `validate_mandatory_mix(selected)` sin errores.

- [ ] **Step 1: Write failing tests** for total/type/chapter quotas, single-detail V/F, sufficient fill anchors and contextual distractor provenance.
- [ ] **Step 2: Run** `python -m unittest scripts.test_gold_quality -v` and confirm quota failures.
- [ ] **Step 3: Implement** deterministic editorial variants directly from `massive-v5/facts`, using exact source spans and category-compatible nearby facts.
- [ ] **Step 4: Run** Python tests and `python scripts/audit-gold-bank.py`; require zero contract errors.
- [ ] **Step 5: Commit** generated shards, manifest and audit outputs.

### Task 2: Mezcla obligatoria de sesiones

**Files:**
- Modify: `src/domain/final-mission-selection.test.ts`
- Modify: `src/domain/final-mission-selection.ts`
- Modify: `src/app/app-state.tsx`

**Interfaces:**
- Produces: `selectMissionQuestions` with quotas `{fill_blank:30,true_false:25,single_choice:45}`, 12/13 V/F balance, >=18 contextual MC and >=10 relational MC for count 100.

- [ ] **Step 1: Write failing Vitest cases** for exact 100-question composition, trap/relational minima and unique facts.
- [ ] **Step 2: Run** the focused test and confirm the current shuffle-only selector fails.
- [ ] **Step 3: Implement** deterministic quota buckets with graceful proportional fallback only for non-100 specialized modes.
- [ ] **Step 4: Run** focused and full Vitest suites.
- [ ] **Step 5: Commit** selector and integration changes.

### Task 3: Ciclo de recuperación y dominio

**Files:**
- Modify: `src/domain/compressed-scheduler.test.ts`
- Modify: `src/domain/compressed-scheduler.ts`
- Modify: `src/domain/fact-mastery.test.ts`
- Modify: `src/domain/fact-mastery.ts`

**Interfaces:**
- Produces: repair gap 8–15; deferred windows 45–90 minutes, 6–10 hours and next-day eligibility; mastery remains gated by distinct sessions, variants, skills, hard/contextual evidence and delayed retrievals.

- [ ] **Step 1: Write failing tests** for every interval and for immediate correction not granting mastery.
- [ ] **Step 2: Run** focused tests and verify expected failures.
- [ ] **Step 3: Implement** minimal scheduling/stage fields without rewriting existing history.
- [ ] **Step 4: Run** focused and complete Vitest suites.
- [ ] **Step 5: Commit** scheduler and mastery updates.

### Task 4: Métricas y UX

**Files:**
- Modify: `src/domain/session-metrics.test.ts`
- Modify: `src/domain/session-metrics.ts`
- Modify: `src/components/statistics-page.tsx`
- Modify: `src/components/answer-learning-feedback.tsx`
- Modify: `e2e/training-modes.spec.ts`

**Interfaces:**
- Produces: accuracy slices for fill, V/F, selection, contextual, first attempt, deferred, next day, blind and recurring errors.

- [ ] **Step 1: Write failing unit/component tests** for metric separation and complete-phrase feedback.
- [ ] **Step 2: Run** focused tests and confirm missing metrics.
- [ ] **Step 3: Implement** metric aggregation and concise cards; retain immediate feedback in Aprender and deferred feedback in Simulacro.
- [ ] **Step 4: Add failing E2E assertions**, implement any missing UI wiring, then rerun focused Playwright.
- [ ] **Step 5: Commit** metrics and UI changes.

### Task 5: Verificación, documentación y producción

**Files:**
- Modify: `output/consolidacion_final/reporte_final.md`
- Modify: `output/consolidacion_final/auditoria_calidad.json`
- Modify: `output/consolidacion_final/reporte_cuarentena.md`

**Interfaces:**
- Produces: auditable counts, test evidence, commits and public deployment URL.

- [ ] **Step 1: Run** Python audit, full Vitest, ESLint, TypeScript and production build.
- [ ] **Step 2: Run** full Playwright on desktop/mobile and inspect screenshots.
- [ ] **Step 3: Review** `git diff --check`, quota report and public bank manifest.
- [ ] **Step 4: Commit, push, open PR, wait for checks and merge to `main`.
- [ ] **Step 5: Verify** production identity, manifest counts, core interaction, console health and responsive overflow; record final evidence.

