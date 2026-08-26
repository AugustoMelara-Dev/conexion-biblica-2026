# V5 - Consolidacion Final Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar una V5 guiada que use solo preguntas GOLD, preserve el historial y mida recuperación real por hecho hasta el 29 de agosto.

**Architecture:** El banco original queda inmutable y un pipeline editorial produce shards GOLD y reportes. IndexedDB agrega dominio, migración y agenda; React consume esos servicios mediante una portada de misión única y simulaciones ciegas disjuntas.

**Tech Stack:** Python 3.12, TypeScript 6, React 19, IndexedDB, Vitest, Playwright, Vite, Vercel.

**Spec:** `docs/superpowers/specs/2026-08-26-consolidacion-final-v5-design.md`

## Global Constraints

- Fuente única: `MaterialConexionBiblica (1).pdf`; no modificarla ni usar Internet para contenido.
- Conservar `public/banks/massive-v5` y todos los datos V1-V4.
- Solo GOLD con puntuación >=85 y cero rechazo automático entra a V5.
- `mc-sequence-v1` queda deshabilitado por defecto.
- Zona horaria del plan: `America/Tegucigalpa`; competencia: 2026-08-29.
- No usar blind pool en entrenamiento ni reparación.

---

### Task 1: Pipeline editorial y banco GOLD

**Files:**
- Create: `scripts/lib/gold_quality.py`
- Create: `scripts/audit-gold-bank.py`
- Create: `scripts/test_gold_quality.py`
- Create: `public/banks/consolidation-v5/**`
- Create: `output/consolidacion_final/auditoria_calidad.json`
- Create: `output/consolidacion_final/reporte_cuarentena.md`

**Interfaces:**
- Produces: `audit_question(question, peers) -> EditorialDecision` y manifest con `editorial_status`, `quality_score`, `semantic_skill`, `blind_pool`.

- [ ] Escribir pruebas que rechacen secuencias léxicas, V/F roto, referencia artificial, distractores incompatibles, duplicados y puntuación menor de 85.
- [ ] Ejecutar `python -m unittest scripts/test_gold_quality.py` y observar fallos por módulo ausente.
- [ ] Implementar puntuación, rechazos, normalización de referencias, deduplicación y partición ciega A/B disjunta.
- [ ] Ejecutar el pipeline y verificar que los 14,000 originales no cambian.
- [ ] Ejecutar la muestra estratificada requerida y guardar conteos/rechazos/20 pares antes-después.

### Task 2: Tipos de dominio, scheduler y preparación

**Files:**
- Create: `src/domain/fact-mastery.ts`
- Create: `src/domain/fact-mastery.test.ts`
- Create: `src/domain/compressed-scheduler.ts`
- Create: `src/domain/compressed-scheduler.test.ts`
- Create: `src/domain/readiness.ts`
- Create: `src/domain/readiness.test.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Produces: `applyFactEvidence(previous, event)`, `scheduleNextRetrieval(evidence)`, `calculateChapterReadiness(metrics)`.

- [ ] Escribir pruebas para repaired +0, pista +0, lenta fragile, sesiones/variantes separadas, mastered y lapsed.
- [ ] Ejecutar las pruebas y confirmar fallos por exports inexistentes.
- [ ] Implementar estados, evidencia y los intervalos 8-15 preguntas, 45-90 minutos, 6-12 horas y día siguiente.
- [ ] Implementar preparación 40/30/20/10 sin permitir 100% por exposición.
- [ ] Ejecutar pruebas focalizadas hasta quedar verdes.

### Task 3: Persistencia y migración V1-V4

**Files:**
- Create: `src/storage/history-migration.ts`
- Create: `src/storage/history-migration.test.ts`
- Modify: `src/storage/db.ts`
- Modify: `src/domain/backup.ts`
- Modify: `src/domain/backup.test.ts`
- Modify: `src/app/app-state.tsx`

**Interfaces:**
- Produces stores `factMastery`, `legacyEvents`, `migrationBackups`, `missionPlan`, `blindUsage`; `migrateLegacyHistory()` retorna conteos seguros/inseguros.

- [ ] Escribir pruebas de upgrade no destructivo, respaldo previo, match inequívoco y evento legado inseguro.
- [ ] Ejecutar y observar fallos con DB v3/stores ausentes.
- [ ] Subir la versión, crear índices por capítulo/estado/vencimiento y migrar una sola vez.
- [ ] Ampliar exportación/restauración manteniendo respaldos 2.0 válidos.
- [ ] Ejecutar pruebas de almacenamiento y respaldo.

### Task 4: Carga GOLD, selección y blind pools

**Files:**
- Create: `src/storage/consolidation-bank.ts`
- Create: `src/storage/consolidation-bank.test.ts`
- Create: `src/domain/final-mission-selection.ts`
- Create: `src/domain/final-mission-selection.test.ts`
- Modify: `src/domain/adaptive-session.ts`
- Modify: `src/domain/banks.ts`
- Modify: `src/storage/seed.ts`

**Interfaces:**
- Produces: loader paginado GOLD; `selectMissionQuestions` sin factos duplicados; `selectBlindSimulation('A'|'B')` disjunto.

- [ ] Escribir pruebas de exclusión SILVER/QUARANTINE/blind y ausencia de `fact_id` repetido.
- [ ] Ejecutar y confirmar fallos por loader inexistente.
- [ ] Implementar carga por shards e índices, pesos Tier A/B/C y mezcla 40/25/15/10/10.
- [ ] Implementar consumo independiente de A/B y reserva de emergencia.
- [ ] Ejecutar pruebas focalizadas.

### Task 5: Plan final y CTA único

**Files:**
- Create: `src/domain/final-mission-plan.ts`
- Create: `src/domain/final-mission-plan.test.ts`
- Create: `src/components/final-mission-dashboard.tsx`
- Create: `src/components/final-mission-dashboard.test.tsx`
- Modify: `src/components/dashboard-page.tsx`
- Modify: `src/components/massive-training-hub.tsx`
- Modify: `src/app/app-state.tsx`
- Modify: `src/index.css`

**Interfaces:**
- Produces: `buildFinalMissionPlan(now, availability, evidence)` y CTA `Continuar mi misión` que inicia/reanuda el bloque exacto.

- [ ] Escribir pruebas para días 26-29, defaults, reanudación y prioridad de capítulos débiles.
- [ ] Ejecutar y confirmar fallos por plan/componente ausentes.
- [ ] Implementar configuración breve, cuenta regresiva, próxima misión y modos avanzados secundarios.
- [ ] Establecer `consolidation-v5` como selección inicial sin ocultar V1-V4.
- [ ] Ejecutar pruebas de componentes y app state.

### Task 6: Feedback, cuaderno y métricas separadas

**Files:**
- Create: `src/components/answer-learning-feedback.tsx`
- Create: `src/components/answer-learning-feedback.test.tsx`
- Create: `src/components/error-notebook.tsx`
- Modify: `src/components/quiz-page.tsx`
- Modify: `src/components/statistics-page.tsx`
- Modify: `src/components/fact-coverage-panel.tsx`

**Interfaces:**
- Produces feedback contrastivo de 2-4 líneas, botones `Entendido`/`Todavía lo confundo`, próxima recuperación y métricas practice/cold/deferred/blind.

- [ ] Escribir pruebas de explicación específica, error recurrente y separación de métricas.
- [ ] Ejecutar y confirmar fallos de UI esperados.
- [ ] Implementar feedback, cuaderno, fatiga no bloqueante y panel de preparación por capítulo.
- [ ] Ejecutar pruebas focalizadas y accesibilidad básica.

### Task 7: Regresión, build y UI real

**Files:**
- Modify: `e2e/*.spec.ts`
- Modify: `public/sw.js`
- Create: `output/consolidacion_final/screenshots/*.png`

**Interfaces:**
- Verifica móvil 390 px, escritorio, misión, acierto/error, feedback, pausa/recarga, blind, historial, estadísticas y exportación.

- [ ] Ejecutar pruebas editoriales y unitarias completas.
- [ ] Ejecutar typecheck, lint y build; corregir cada fallo con prueba de regresión.
- [ ] Ejecutar Playwright y verificar consola, desbordamiento y service worker.
- [ ] Capturar portada, misión, feedback, progreso y simulación ciega.

### Task 8: Revisión, commits y producción

**Files:**
- Create: `output/consolidacion_final/reporte_final.md`

**Interfaces:**
- Produce commit(s), despliegue Vercel y URL comprobada.

- [ ] Revisar diff y confirmar que el PDF y massive-v5 originales están sin cambios.
- [ ] Ejecutar nuevamente las puertas de verificación desde un árbol limpio salvo el PDF local.
- [ ] Crear commits descriptivos, integrar a `main` y desplegar mediante la integración existente.
- [ ] Verificar producción en móvil/escritorio, consola, versión visible y CTA.
- [ ] Registrar conteos, migración, intervalos, pools, pruebas, commits, URL y diez pares antes/después.
