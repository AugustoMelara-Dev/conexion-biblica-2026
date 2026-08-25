# Preparación Conexión Bíblica V3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar un banco curado de 500 preguntas por familias y tres modos de práctica con estadísticas competitivas separadas.

**Architecture:** `prep-v3` será un banco local autónomo; los selectores puros decidirán elegibilidad, diversidad por `factKey` y prioridad adaptativa. Cada intento llevará contexto de práctica o simulacro, y las estadísticas competitivas se derivarán sólo de sesiones de simulacro.

**Tech Stack:** React 19, TypeScript 6, Vite 8, IndexedDB, Vitest, Testing Library y JSON local.

**Spec:** `docs/superpowers/specs/2026-08-24-preparacion-v3-design.md`

## Global Constraints

- Mantener la aplicación offline, sin login ni APIs externas.
- No modificar `MaterialConexionBiblica (1).pdf` ni `Banco_Maestro_CB2026.json`.
- Conservar IDs, progreso y respaldos de V1/V2.
- Generar exactamente 500 preguntas: 28 por Daniel 1-12, 27 por Profetas y Reyes 39-44 y 2 integradoras.
- Toda pregunta debe tener `factKey`, referencia, explicación, `trapReason`, `memoryCue` y trazabilidad local.
- Escribir y ejecutar primero una prueba que falle para cada comportamiento nuevo.

---

### Task 1: Fijar el contrato del banco de 500 preguntas

**Files:** `src/domain/types.ts`, `src/domain/prep-bank.test.ts`, `scripts/validate-prep-bank.mjs`, `public/banks/v3_daniel.json`, `public/banks/v3_profetas_reyes.json`.

**Interfaces:** `Question.integrative?: boolean` distingue las dos preguntas transversales. El validador sale con código 0 sólo con 500 preguntas, cuotas exactas, campos pedagógicos completos, IDs/preguntas únicos y opciones válidas.

- [ ] Escribir pruebas que exijan 500 registros, cuotas 28/27/2 y campos completos; ejecutarlas y confirmar que fallan con el suplemento actual de 72.
- [ ] Implementar el validador con diagnósticos por archivo, capítulo, ID y `factKey`.
- [ ] Construir las 500 preguntas desde las fuentes locales y conservar referencia/familia en cada registro.
- [ ] Ejecutar la prueba enfocada y el validador hasta obtener cero errores.

### Task 2: Selección por familia sin repetición literal

**Files:** `src/domain/session-selector.ts`, `src/domain/session-selection.test.ts`, `src/domain/family-selection.test.ts`.

**Interfaces:** `selectDiverseQuestions` evita `factKey` consecutivo cuando existe alternativa; `selectNextFamilyVariant` agota variantes no vistas antes de reciclar.

- [ ] Escribir pruebas de agotamiento, cambio de redacción, determinismo y fallback; confirmar fallos.
- [ ] Implementar la selección mínima y conectarla a Aprender y Repaso inteligente.
- [ ] Ejecutar las pruebas de selector y dominio.

### Task 3: Modelar contextos y tres modos

**Files:** `src/domain/types.ts`, `src/app/app-state.tsx`, `src/components/session-builder-page.tsx`, `src/components/quiz-page.tsx` y sus pruebas.

**Interfaces:** `SessionMode` añade `learn`, `smart-review` y `simulation`; `AttemptRecord.context` y `Session.context` usan `practice | simulation`; `sessionContextForMode` clasifica de forma pura y compatible.

- [ ] Escribir pruebas del contrato de modos, feedback inmediato/diferido y clasificación; confirmar fallos.
- [ ] Añadir tipos y migración por defecto a práctica.
- [ ] Añadir los tres accesos principales y sus configuraciones seguras.
- [ ] Mostrar pista inmediata sólo en práctica y después del cierre en simulacro.
- [ ] Ejecutar pruebas de componentes, tipos y persistencia.

### Task 4: Prioridad adaptativa por familia

**Files:** `src/domain/family-mastery.ts`, `src/domain/family-mastery.test.ts`, `src/domain/session-selector.ts`.

**Interfaces:** `buildFamilyMastery` agrega dominio, errores, latencia y última exposición por `factKey`; Repaso inteligente ordena familias débiles antes que dominadas sin excluir contenido nuevo.

- [ ] Escribir pruebas para error, lentitud, antigüedad y familias nuevas; confirmar fallos.
- [ ] Implementar agregación y puntuación mínima.
- [ ] Integrarla en el selector determinista y ejecutar pruebas.

### Task 5: Separar estadísticas competitivas

**Files:** `src/lib/statistics.ts`, `src/lib/statistics.test.ts`, `src/components/statistics-page.tsx`, `src/components/results-page.tsx`.

**Interfaces:** `buildSimulationStatistics(sessions)` ignora toda sesión de práctica; la interfaz etiqueta claramente dominio de práctica y resultados de simulacro.

- [ ] Escribir una prueba donde varios errores de práctica no cambien el 100% del simulacro; confirmar fallo.
- [ ] Implementar el agregado competitivo y renderizarlo separado.
- [ ] Ejecutar pruebas de estadísticas y resultados.

### Task 6: Compatibilidad, validación y recorrido real

**Files:** `src/domain/backup.ts`, `src/domain/backup.test.ts`, `README.md`.

**Interfaces:** Respaldos 1.0/2.0 sin `context` migran a práctica sin perder datos.

- [ ] Escribir y ejecutar la prueba de migración antes del cambio.
- [ ] Implementar la normalización compatible y documentar los tres modos.
- [ ] Ejecutar pruebas completas, lint, typecheck, build y el validador.
- [ ] Recorrer los tres modos en la interfaz; revisar feedback, tiempo, resultados, recarga y responsive.
- [ ] Revisar el diff y confirmar que las dos fuentes locales permanecen intactas.
