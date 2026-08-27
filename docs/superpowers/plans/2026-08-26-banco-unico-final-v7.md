# Banco Maestro Único Final V7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar un banco canónico único, totalmente trazable al PDF, con 6,500–8,000 preguntas GOLD en cuatro familias de selección y un plan adaptativo de 48 horas.

**Architecture:** Un pipeline Python extrae inventario, hechos, preguntas y cobertura en shards de capítulo. React adapta un único esquema canónico, migra historial conservando eventos legado y usa selectores por hechos para misiones, repaso y reservas ciegas.

**Tech Stack:** Python 3/PyMuPDF, React 19, TypeScript 6, IndexedDB, Vitest, Playwright, Vite y Vercel.

**Spec:** `docs/superpowers/specs/2026-08-26-banco-unico-final-v7-design.md`

## Global Constraints

- Única fuente: `MaterialConexionBiblica (1).pdf`; el PDF queda intacto y fuera de git.
- Único ID público: `BANCO_UNICO_CONEXION_BIBLICA_2026`; nombre `Banco Maestro Único — Final 2026`.
- Esquema técnico `7.0`; “V7” no aparece como perfil público.
- Exactamente cuatro familias y cero respuestas escritas.
- Producción requiere cobertura cero/cero/cero y mínimo 6,500 GOLD.
- No se elimina historial anterior; toda migración crea respaldo restaurable.

---

### Task 1: Contratos canónicos y pruebas de puerta

**Files:**
- Create: `scripts/lib/final_bank.py`
- Create: `scripts/test_final_bank.py`
- Create: `src/domain/final-bank.ts`
- Create: `src/domain/final-bank.test.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Produces: `BANK_ID`, `QUESTION_FAMILIES`, `validate_source_inventory`, `validate_coverage`, `validate_gold_bank`, `FinalQuestionFamily`, `FINAL_BANK_ID`.
- Enforces: cuatro familias, opciones 4/4/2/4, estado GOLD y contadores de cobertura cero.

- [ ] Escribir pruebas Python y Vitest que fallen con familias antiguas, completar sin cuatro opciones, hechos sin pregunta y unidades descubiertas.
- [ ] Ejecutar `python -m unittest scripts/test_final_bank.py -v` y `npm test -- src/domain/final-bank.test.ts`; confirmar fallos por contratos ausentes.
- [ ] Implementar contratos mínimos compartidos y validadores deterministas.
- [ ] Repetir ambas pruebas y confirmar éxito.

### Task 2: Inventario independiente del PDF

**Files:**
- Create: `scripts/lib/source_inventory.py`
- Create: `scripts/test_source_inventory.py`
- Create: `scripts/build-final-bank.py`
- Generate: `public/banks/final-2026/source_inventory.json`
- Generate: `public/banks/final-2026/source_extraction_issues.json`

**Interfaces:**
- Consumes: ruta del PDF y PyMuPDF.
- Produces: `extract_daniel_inventory(pdf)`, `extract_pr_inventory(pdf)`, `SourceUnit` serializable.

- [ ] Probar que el extractor encuentra exactamente 357 versículos, capítulos 1–12 y texto no vacío.
- [ ] Probar que cada página PR27–59 aporta unidades con capítulo, párrafo, proposición y texto exacto.
- [ ] Probar correcciones OCR explícitas, incluida la numeración visible de Daniel 5:18, sin normalizar lenguaje.
- [ ] Implementar extracción, clasificación lingüística conservadora y registro de incidencias.
- [ ] Renderizar visualmente cualquier página marcada dudosa antes de aceptar una corrección.

### Task 3: Hechos, variantes y auditor adversarial

**Files:**
- Create: `scripts/lib/final_editorial.py`
- Create: `scripts/test_final_editorial.py`
- Generate: `public/banks/final-2026/fact_inventory.json`
- Generate: `public/banks/final-2026/questions/*.json`
- Generate: `public/banks/final-2026/editorial_audit.json`

**Interfaces:**
- Consumes: `SourceUnit[]`.
- Produces: `AtomicFact[]`, `GoldQuestion[]`, revisión ciega y razones de rechazo.

- [ ] Probar que toda unidad deriva al menos un hecho sustentado en su texto literal.
- [ ] Probar las cuatro familias, gramática compatible, opciones únicas y citas que contienen/sustentan la respuesta.
- [ ] Probar que el auditor sin índice esperado reconstruye una única respuesta y explica descartes.
- [ ] Implementar hechos editoriales y variantes diferenciadas por habilidad, no por posición o paráfrasis.
- [ ] Generar 6,500–8,000 GOLD balanceadas 25 % ±2 % y dificultad 5/20/45/30.
- [ ] Rechazar automáticamente duplicados semánticos, secuencias léxicas, TF rotos, referencias inválidas y fugas por longitud.

### Task 4: Manifiesto de cobertura y build gate

**Files:**
- Generate: `public/banks/final-2026/coverage_manifest.json`
- Generate: `public/banks/final-2026/manifest.json`
- Generate: `output/final-v7/reporte_final.md`
- Modify: `package.json`

**Interfaces:**
- Produces: scripts `build:final-bank`, `audit:final-bank`, `test:final-bank`.

- [ ] Probar que una unidad sin hecho, un hecho sin GOLD o una unidad no mapeada detiene la auditoría.
- [ ] Construir relaciones unidad → hechos → preguntas → familias.
- [ ] Añadir puertas específicas para Daniel 7/8/9/11 y finales de PR43/44.
- [ ] Ejecutar la auditoría completa y exigir contadores cero/cero/cero.

### Task 5: Adaptador de banco único y mezclas de ronda

**Files:**
- Create: `src/storage/final-bank.ts`
- Create: `src/storage/final-bank.test.ts`
- Modify: `src/domain/final-mission-selection.ts`
- Modify: `src/domain/final-mission-selection.test.ts`
- Modify: `src/app/app-state.tsx`

**Interfaces:**
- Produces: `readFinalManifest`, `loadFinalQuestionPool`, `selectFinalRound(count, seed)`.

- [ ] Probar adaptador con tipos 7.0 y único `bankId`.
- [ ] Probar mezclas exactas 100/50/20, hechos únicos y restricciones avanzadas de 100.
- [ ] Implementar carga paginada por shard e índices de capítulo/familia/dificultad/reserva.
- [ ] Reemplazar selección visible de perfiles por el banco canónico.

### Task 6: Respaldo, migración y exposiciones

**Files:**
- Modify: `src/storage/db.ts`
- Modify: `src/domain/backup.ts`
- Modify: `src/domain/backup.test.ts`
- Modify: `src/storage/history-migration.ts`
- Modify: `src/storage/history-migration.test.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Produces: respaldo `backupVersion: "3.0"`, `migrateToFinalBank`, exposiciones con snapshot completo y eventos legado.

- [ ] Probar respaldo previo, restauración y conservación exacta de bancos/progreso/sesiones/reportes.
- [ ] Probar consolidación segura por hecho y preservación legado en mapeos ambiguos.
- [ ] Persistir texto, opciones, posición, respuesta, intervalo, modo y pista por exposición.
- [ ] Probar recarga exacta de pregunta, opciones, orden, temporizador y misión.

### Task 7: Scheduler, dominio, reservas y Plan Final

**Files:**
- Modify: `src/domain/compressed-scheduler.ts`
- Modify: `src/domain/fact-mastery.ts`
- Modify: `src/domain/final-48h-plan.ts`
- Modify: `src/domain/adaptive-session.ts`
- Modify corresponding `*.test.ts` files.

**Interfaces:**
- Produces: estados unseen/exposed/repaired/fragile/learning/due/stable/mastered/lapsed y siguiente misión automática.

- [ ] Probar reparación separada 8–15, 45–90 min, 6–10 h y día siguiente.
- [ ] Probar que la corrección inmediata no domina y que dominio exige evidencia contextual/difícil sin pistas.
- [ ] Probar A/B disjuntos, invisibles antes de simulación y sin feedback inmediato.
- [ ] Implementar los bloques Día 1, Día 2 y competencia detrás de `CONTINUAR MI MISIÓN`.

### Task 8: Interfaz única sin escritura

**Files:**
- Modify: `src/components/question-renderer.tsx`
- Modify: `src/components/dashboard-page.tsx`
- Modify: `src/components/session-builder-page.tsx`
- Modify: `src/components/bank-manager-page.tsx`
- Modify: `src/components/statistics-page.tsx`
- Modify: `src/components/history-page.tsx`
- Modify: `src/components/review-page.tsx`
- Modify: `src/components/app-shell.tsx`
- Remove from active imports: `src/components/bank-selector.tsx`

**Interfaces:**
- Consumes: único banco y métricas por hechos.
- Produces: cuatro renderizadores de selección y páginas coherentes.

- [ ] Probar que no se renderizan versiones, perfiles, inputs de respuesta, textarea, matching, ordering ni multi-select.
- [ ] Probar botones A–D y V/F con teclado.
- [ ] Mostrar feedback con referencia, cita y descarte del distractor elegido.
- [ ] Mostrar una misión primaria y configuración manual secundaria del mismo banco.
- [ ] Verificar layout sin desbordamiento a 390 px.

### Task 9: Service worker y pruebas integrales

**Files:**
- Modify: `public/sw.js`
- Modify: `src/service-worker.test.ts`
- Create/modify: `e2e/final-bank-v7.spec.ts`
- Create: `e2e/final-bank-v7-mobile.spec.ts`

**Interfaces:**
- Produces: caché shell v9 y flujo E2E del banco único.

- [ ] Probar invalidación de caché anterior sin borrar IndexedDB.
- [ ] Ejecutar Python, Vitest, TypeScript, ESLint y build completos.
- [ ] Ejecutar Playwright escritorio y 390 px, persistencia, offline y consola limpia.
- [ ] Capturar directa, completar, V/F, contextual, feedback, resumen y recuperación.

### Task 10: Entrega y producción

**Files:**
- Modify: `README.md`
- Finalize: `output/final-v7/reporte_final.md`

**Interfaces:**
- Produces: commits, PR, merge, despliegue y evidencia pública.

- [ ] Auditar el diff y confirmar que el PDF continúa sin seguimiento.
- [ ] Commit y push de la rama `codex/banco-unico-final-v7`.
- [ ] Abrir PR, esperar checks, fusionar y verificar Vercel.
- [ ] Ejecutar las 20 comprobaciones manuales en producción y registrar capturas/resultados.
- [ ] Entregar métricas, rechazos, migración, pruebas, commits, PR y URL pública.
