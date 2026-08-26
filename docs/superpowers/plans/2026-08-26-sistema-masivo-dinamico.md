# Sistema masivo y dinámico de entrenamiento — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar 14,000+ preguntas verificadas desde el PDF local, un motor dinámico anti-memorización, 20 modos, plan de 48 horas y producción verificada.

**Architecture:** El generador produce hechos, preguntas y recursos fragmentados por capítulo. La aplicación migra IndexedDB, consulta contenido por índices y materializa variantes de sesión de forma determinista.

**Tech Stack:** Python 3.12 + PyMuPDF, React 19, TypeScript 6, Vite 8, IndexedDB, Vitest y Playwright.

**Spec:** `docs/superpowers/specs/2026-08-26-sistema-masivo-dinamico-design.md`

## Global Constraints

- Única fuente editorial: `MaterialConexionBiblica (1).pdf`.
- Conservar bancos e historial actuales y no modificar el PDF.
- Mínimo 8,000 preguntas Daniel y 6,000 PR.
- 25 % V/F, 30 % completar y 45 % selección múltiple por banco.
- 5 % fáciles, 20 % medias, 45 % difíciles y 30 % expertas por banco.
- Reserva ciega mínima de 15 %.
- TDD para comportamiento nuevo y verificación fresca antes de cada commit.

---

### Task 1: Contratos masivos y auditor de generación

**Files:**
- Create: `scripts/lib/massive_bank.py`
- Create: `scripts/test_massive_bank.py`
- Modify: `scripts/generate-pdf-competition-banks.py`

**Interfaces:**
- Produces: `MassiveQuestion`, `AtomicFact`, validadores de cuotas/unicidad/respaldo y escritor de fragmentos.

- [ ] Escribir pruebas que fallen para esquema, cuotas, blind pool y duplicados.
- [ ] Ejecutar `python -m unittest scripts.test_massive_bank -v` y confirmar fallos por API ausente.
- [ ] Implementar contratos y validadores mínimos.
- [ ] Reejecutar la prueba hasta obtener cero fallos.
- [ ] Revisar el diff y registrar el avance.

### Task 2: Extracción completa y banco 14,000+

**Files:**
- Create: `scripts/generate-massive-training-system.py`
- Modify: `scripts/lib/massive_bank.py`
- Create: `public/banks/massive-v5/manifest.json`
- Create: `output/bancos_masivos_pdf/*`

**Interfaces:**
- Consumes: `AtomicFact` y validadores de Task 1.
- Produces: fragmentos de preguntas, hechos, plantillas, distractores, estadísticas y auditoría.

- [ ] Añadir fixtures/pruebas de extracción para Daniel 1, 7, 11 y PR43–44.
- [ ] Confirmar RED con `python -m unittest scripts.test_massive_bank -v`.
- [ ] Extraer todo el PDF y construir inventario atómico ordenado.
- [ ] Generar candidatos por familias semánticas y seleccionar cuotas exactas.
- [ ] Ejecutar auditoría de fuente/calidad, eliminar duplicados y escribir fragmentos.
- [ ] Validar lectura de los archivos escritos y conteos 8,000/6,000.

### Task 3: Modelo, migración e importación paginada

**Files:**
- Modify: `src/domain/types.ts`
- Modify: `src/storage/db.ts`
- Create: `src/storage/massive-bank.ts`
- Test: `src/storage/storage.test.ts`
- Test: `src/storage/massive-bank.test.ts`

**Interfaces:**
- Produces: consultas `listForSession(filters, limit)`, exposición por variante e importación de fragmentos.

- [ ] Escribir pruebas que fallen para migración sin pérdida, índices y consultas limitadas.
- [ ] Ejecutar las pruebas enfocadas y confirmar RED.
- [ ] Subir la versión de DB, crear índices/almacén de exposición e importador idempotente.
- [ ] Implementar consultas por filtros y límite sin `getAll()` del banco masivo.
- [ ] Confirmar GREEN y ejecutar las pruebas de almacenamiento existentes.

### Task 4: Motor dinámico y selector anti-memorización

**Files:**
- Create: `src/domain/dynamic-question.ts`
- Create: `src/domain/adaptive-session.ts`
- Test: `src/domain/dynamic-question.test.ts`
- Test: `src/domain/adaptive-session.test.ts`
- Modify: `src/domain/session-selector.ts`

**Interfaces:**
- Produces: `materializeDynamicQuestion` y `selectAdaptiveSession`.

- [ ] Escribir pruebas de barajado, distractores, identidad de variante, cuotas 60/20/10/10 y factId único.
- [ ] Ejecutar pruebas enfocadas y confirmar RED.
- [ ] Implementar materialización determinista y selección adaptativa.
- [ ] Cubrir reserva ciega y reaparición diferida en modo errores.
- [ ] Confirmar GREEN y ejecutar dominio completo.

### Task 5: Modos y PLAN FINAL — 48 HORAS

**Files:**
- Create: `src/domain/training-modes.ts`
- Create: `src/domain/final-48h-plan.ts`
- Test: `src/domain/training-modes.test.ts`
- Test: `src/domain/final-48h-plan.test.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Produces: catálogo de 20 modos, filtros y diez bloques adaptativos.

- [ ] Escribir pruebas que fallen para nombres, conteos 50/100/200 y diez bloques.
- [ ] Confirmar RED.
- [ ] Implementar catálogo y plan con adaptación por debilidad.
- [ ] Confirmar GREEN y ausencia de regresiones de configuración.

### Task 6: Integración de aplicación y estadísticas de hechos

**Files:**
- Modify: `src/app/app-state.tsx`
- Modify: `src/App.tsx`
- Modify: `src/components/session-builder-page.tsx`
- Modify: `src/components/practice/mode-picker.tsx`
- Modify: `src/components/quiz-page.tsx`
- Modify: `src/components/statistics-page.tsx`
- Test: pruebas de componentes relacionadas.

**Interfaces:**
- Consumes: repositorio paginado, selector adaptativo y catálogo de modos.
- Produces: flujos visibles, revelación post-respuesta, reportes y cobertura real.

- [ ] Escribir pruebas de interfaz para grupos de modos, plan 48h y reserva ciega.
- [ ] Confirmar RED.
- [ ] Integrar carga progresiva y sesiones sin cargar todo el banco masivo.
- [ ] Añadir exposición, referencia/explicación post-respuesta y métricas por hecho.
- [ ] Confirmar GREEN en pruebas de componentes.

### Task 7: Offline, E2E y rendimiento

**Files:**
- Modify: `public/sw.js`
- Modify: `e2e/training-modes.spec.ts`
- Modify: `e2e/responsive-experience.spec.ts`
- Modify: `vercel.json`

**Interfaces:**
- Produces: cache versionada de manifiesto/fragmentos y evidencia móvil/escritorio.

- [ ] Escribir/ajustar E2E para modos, 48h, persistencia, 50/100/200 y viewport móvil.
- [ ] Ejecutar E2E enfocado y confirmar el fallo esperado antes de la integración final.
- [ ] Versionar cache y evitar datos obsoletos.
- [ ] Ejecutar Vitest, lint, typecheck, build y Playwright completos.
- [ ] Corregir cada fallo y repetir hasta cero fallos.

### Task 8: Auditoría final, commits y Vercel

**Files:**
- Create: `output/bancos_masivos_pdf/auditoria_bancos_masivos.md`
- Create: `output/bancos_masivos_pdf/estadisticas_bancos_masivos.json`

**Interfaces:**
- Produces: evidencia final y URL pública.

- [ ] Ejecutar validación automática completa de archivos escritos.
- [ ] Revisar diff, fuente PDF intacta y ausencia de secretos/artefactos temporales.
- [ ] Ejecutar nuevamente pruebas, build y flujo Playwright principal.
- [ ] Crear commits descriptivos y desplegar producción en el proyecto Vercel ya enlazado.
- [ ] Verificar estado del despliegue y los flujos público móvil/escritorio.
