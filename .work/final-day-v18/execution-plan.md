# Operacion nacional ultimo dia V18 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar hoy el mayor subconjunto posible de preguntas realmente verificadas contra el PDF oficial, con paquetes utilizables y una aplicación estable.

**Architecture:** Cuatro carriles producen artefactos disjuntos: ledger canónico, auditorías textuales, autoría candidata y una integración determinista. Solo el integrador promueve preguntas y modifica el banco público; los estados de auditoría se derivan de dictámenes humanos-modelo válidos, no de heurísticas.

**Tech Stack:** React 19, TypeScript 6, Vite 8, Vitest, Playwright, Python 3, JSON/CSV/Markdown y Vercel.

**Spec:** `C:\Users\melar\.codex\attachments\db52d1cc-8a1d-4039-8cb2-9cdb17463701\pasted-text.txt`

## Global Constraints

- Fuente única: PDF SHA-256 `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`.
- Base Git exacta: `45d6e1ac6b01108080c21bed3574dc69c98e09cb`.
- Auditoría editorial final: GPT-5.6 Sol, razonamiento medium, realmente ejecutada en V18.
- Autoría y competencia ciega: GPT-5.6 Luna, razonamiento max, realmente ejecutada.
- Scripts no redactan ni resuelven contenido editorial.
- Mantener banco, progreso, IndexedDB, rotación, emergencia, simulaciones y 18 shards.
- Promover y desplegar solo evidencia verificable; nunca inflar contadores.

---

### Task 1: Preflight, fuente y baseline

**Files:**
- Create: `AGENTS.md`
- Create: `.work/final-day-v18/progress.json`
- Create: `.work/final-day-v18/progress.md`

- [x] Crear worktree y rama desde el commit canónico.
- [x] Verificar SHA, páginas y contenido visual del PDF oficial.
- [x] Localizar y clasificar el reporte AAH como fuente secundaria.
- [ ] Instalar dependencias y ejecutar baseline focal/editorial y de aplicación.
- [ ] Inventariar manifest, review-index, shards, esquemas, conteos y evidencia histórica sin promoverla a V18.

### Task 2: Ledger canónico y cobertura

**Files:**
- Create: `content/final-day-v18/source-ledger.json`
- Create: `content/final-day-v18/source-ledger.csv`
- Create: `content/final-day-v18/source-ledger.md`
- Test: `scripts/test_final_day_v18_ledger.py`

- [ ] Escribir primero pruebas de esquema, fuente, páginas, IDs y estados permitidos; comprobar RED.
- [ ] Construir ledger desde el OCR cache cuyo hash coincide, verificando visualmente muestras y ambigüedades.
- [ ] Comparar unidades contra banco actual, Banco Maestro e inventarios históricos.
- [ ] Marcar cobertura explicada sin asumir que el inventario histórico es exhaustivo.
- [ ] Ejecutar pruebas y comprobar GREEN.

### Task 3: Dosieres y auditoría V18 prioritaria

**Files:**
- Create: `.work/final-day-v18/dossiers/`
- Create: `.work/final-day-v18/audits/`
- Create: `.work/final-day-v18/blind/`
- Test: `scripts/test_final_day_v18_audit_contract.py`

- [ ] Escribir pruebas RED del contrato, ausencia de defaults, hashes y mutación posterior.
- [ ] Preparar lotes de 15-20, primero PR39-44, luego Daniel 7-12, luego Daniel 1-6.
- [ ] Ejecutar competidores Luna Max ciegos con opciones barajadas.
- [ ] Ejecutar hasta cuatro auditores Sol Medium concurrentes con fuente exacta y sin respuesta almacenada.
- [ ] Integrar determinísticamente y escalar `ANSWER_MISMATCH` o ambigüedad.
- [ ] Reprocesar reescrituras completas por ambas etapas.

### Task 4: Autoría candidata dirigida por cobertura

**Files:**
- Create: `.work/final-day-v18/authors/`
- Test: `scripts/test_final_day_v18_candidate_contract.py`

- [ ] Después del primer ledger, despachar autores Luna Max a unidades `NEEDS_QUESTION`.
- [ ] Mantener 70% PR / 30% Daniel y las cuotas internas del spec.
- [ ] Exigir presentaciones cognitivamente distintas, no paráfrasis superficiales.
- [ ] Pasar toda candidata por competidor ciego y auditor Sol antes de promoción.

### Task 5: Integración, paquetes y UI mínima

**Files:**
- Create: `scripts/compile-final-day-v18.py`
- Create: `scripts/test_final_day_v18_compile.py`
- Modify: `public/banks/final-2026/manifest.json`
- Modify: `public/banks/final-2026/review-index.json`
- Modify: `src/` únicamente donde sea necesario para filtros/paquetes/progreso.

- [ ] Escribir pruebas RED para exclusión, cuotas, audit_status, IDs, mappings y adversarial competitivo.
- [ ] Implementar compilador determinista sin decisiones editoriales.
- [ ] Formar paquetes A/B/C solo hasta los conteos realmente verificados.
- [ ] Añadir filtros/carga/progreso con el mínimo cambio de interfaz.
- [ ] Ejecutar pruebas GREEN y revisar el diff.

### Task 6: Verificación, despliegue incremental y congelamiento

**Files:**
- Update: `.work/final-day-v18/progress.json`
- Update: `.work/final-day-v18/progress.md`

- [ ] Ejecutar schemas, hashes, conteos, respuestas, referencias, mappings, shards y paquetes.
- [ ] Ejecutar Vitest, TypeScript, ESLint y build.
- [ ] Ejecutar Playwright Chromium desktop y móvil, persistencia/PWA/offline y consola.
- [ ] Revisar producción y ausencia de contenido privado.
- [ ] Commit, push y despliegue solo después de puertas verdes.
- [ ] Registrar remanente exacto y congelar la versión estable.

## Pre-flight consistency scan

| Tareas | Interfaz o archivo compartido | Resultado |
|---|---|---|
| 2 -> 3 | `source_unit_id`, cita y contexto | El dosier consume exclusivamente unidades con fuente trazable. |
| 2 -> 4 | `coverage_status` y presentaciones | Autoría comienza con el primer ledger válido, priorizando huecos. |
| 3 -> 5 | dictámenes y hashes | El compilador valida; no adjudica semántica. |
| 4 -> 3 | candidatas | Toda candidata repite las dos etapas antes de promoción. |
| 5 -> 6 | manifest, shards y paquetes | El despliegue depende de todas las puertas verdes. |
| 1 | fuente y baseline | Consistente; baseline pendiente. |
| 2 | ledger y pruebas | Consistente; las ambigüedades quedan explícitas. |
| 3 | auditoría | Consistente; auditor no recibe respuesta almacenada. |
| 4 | autoría | Consistente; producción no depende de la cuota de candidatas. |
| 5 | integración | Consistente; un solo integrador modifica artefactos públicos. |
| 6 | cierre | Consistente; publicación es un efecto externo ya autorizado en el spec. |

Ruling: La fecha del entorno es 4 de septiembre de 2026 y no se expone una hora confiable en este documento; priorizar un incremento estable verificable antes que perseguir metas numéricas completas — si el reloj real ya supera el corte, el costo de esta decisión es omitir autoría adicional para proteger producción.
