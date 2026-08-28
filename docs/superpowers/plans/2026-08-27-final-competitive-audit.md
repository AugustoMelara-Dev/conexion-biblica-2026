# Auditoría competitiva final — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auditar la semántica de alto riesgo y hacer que las rondas competitivas conserven su mezcla exacta mientras priorizan errores y respuestas lentas.

**Architecture:** La selección obligatoria seguirá resolviendo cuotas por familia y unicidad de `fact_id`, pero aceptará prioridad por hecho y variante. El cargador V9 calculará esas prioridades a partir de exposiciones persistidas antes de elegir las 100 preguntas. Un auditor reproducible generará la muestra estratificada y las métricas multirronda.

**Tech Stack:** React 19, TypeScript 6, Vitest, Playwright, Node.js, IndexedDB, banco JSON V9.

**Spec:** `docs/superpowers/specs/2026-08-27-final-competitive-audit.md`

## Global Constraints

- Mantener exactamente 12,000 preguntas GOLD y 3,000 hechos.
- Mantener 30 completar, 25 verdadero/falso y 45 selecciones en rondas de 100.
- No repetir `fact_id` ni exponer reservas ciegas en entrenamiento normal.
- No modificar el PDF fuente ni desplegar a producción.

---

### Task 1: Prioridad adaptativa dentro de cuotas obligatorias

**Files:**

- Modify: `src/domain/final-mission-selection.ts`
- Modify: `src/storage/final-bank.ts`
- Modify: `src/app/app-state.tsx`
- Test: `src/storage/final-bank.test.ts`
- Test: `src/storage/final-bank-v8.real.test.ts`

**Interfaces:**

- Consumes: `QuestionExposure[]` persistidas por `AppProvider`.
- Produces: `loadFinalQuestionPool({ ..., exposures })` y selección obligatoria ordenada por riesgo sin romper cuotas.

- [ ] **Step 1: Escribir la prueba roja** que construye suficientes preguntas nuevas y un hecho fallado/lento visto, solicita 100 y exige que el hecho de riesgo entre conservando la mezcla literal 30/25/45.
- [ ] **Step 2: Ejecutar `npm test -- src/storage/final-bank.test.ts`** y confirmar que falla porque el cargador actual llena la ronda solo con hechos nuevos.
- [ ] **Step 3: Implementar la prioridad mínima** agregando un mapa de riesgo por hecho/variante y usándolo como orden estable dentro del emparejamiento de cuotas.
- [ ] **Step 4: Ejecutar las pruebas focales** y confirmar que pasan la prioridad, las cuotas, la unicidad y la exclusión ciega.

### Task 2: Validación multirronda de aprendizaje

**Files:**

- Modify: `src/domain/dynamic-question.test.ts`
- Modify: `src/domain/fact-mastery.test.ts`
- Modify: `src/components/quiz-page.test.tsx`
- Test: `src/storage/final-bank-v8.real.test.ts`

**Interfaces:**

- Consumes: variantes de reintento, barajado por exposición y evidencia de dominio.
- Produces: pruebas observables de cambio de posición/variante, separación de errores y corrección sin dominio.

- [ ] **Step 1: Añadir pruebas rojas** para reaparición prioritaria con otra variante y distribución de posiciones entre exposiciones.
- [ ] **Step 2: Ejecutar las pruebas focales** y confirmar que cualquier garantía ausente falla por el comportamiento correcto.
- [ ] **Step 3: Implementar solo las garantías ausentes** sin cambiar el contrato visible de las preguntas.
- [ ] **Step 4: Ejecutar `npm test`** y comprobar cero regresiones.

### Task 3: Auditoría semántica estratificada e informe

**Files:**

- Create: `scripts/audit-competitive-readiness.mjs`
- Create: `reports/final-competitive-audit.md`
- Create: `reports/final-competitive-audit.json`

**Interfaces:**

- Consumes: manifiesto V9, fragmentos de preguntas y PDF validado por SHA-256.
- Produces: muestra determinista por capítulo/familia, métricas de rondas y lista explícita de hallazgos.

- [ ] **Step 1: Implementar el auditor** con muestra mínima de 108 preguntas: tres por cada combinación de 12 capítulos y tres familias de alto riesgo.
- [ ] **Step 2: Revisar manualmente cada fila** comparando enunciado, respuesta, cita, corrección falsa y distractores.
- [ ] **Step 3: Ejecutar `npm run audit:final:deep`, el auditor nuevo y `npm run audit:production`**.
- [ ] **Step 4: Ejecutar `npm run lint`, `npm run typecheck`, `npm run build` y la validación de navegador**; documentar resultados y riesgos residuales.
