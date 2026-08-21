# Conexión Bíblica 2026 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir una aplicación web local-first completa para estudiar bancos JSON de Conexión Bíblica 2026 con modos de quiz, progreso, dominio, estadísticas, historial, reportes y respaldos.

**Architecture:** React/Vite/TypeScript con shadcn/ui. El dominio puro vive separado de React; IndexedDB persiste bancos, preguntas, progreso, sesiones y reportes; el shell de la app compone dashboard, bancos, configuración, quiz, resultados, estadísticas y auditoría. Los 10 bancos JSON existentes se incluyen en `public/banks` para el arranque offline, sin modificar los originales de la raíz.

**Tech Stack:** Vite, React, TypeScript, shadcn/ui, Tailwind CSS, lucide-react, IndexedDB nativo, Vitest, Testing Library y Playwright para smoke UI.

## Global Constraints

- Todo funciona sin internet después del build.
- No se usan APIs externas, servicios cloud, fuentes remotas, analytics ni trackers.
- Los bancos originales se conservan y el progreso se guarda separado por `bankId/questionId`.
- Se acepta `schemaVersion: "1.0"` y se rechazan preguntas inválidas sin eliminarlas silenciosamente.
- La interfaz debe ser responsive, accesible, clara y usable en escritorio y teléfono.
- El banco demo, si existe, debe decir `DEMO / NO REAL`; los bancos presentes se consideran datos iniciales reales del workspace.

---

### Task 1: Scaffold local y tokens visuales

**Files:**
- Create: `package.json`, `tsconfig.json`, `vite.config.ts`, `components.json`, `index.html`
- Create: `src/main.tsx`, `src/App.tsx`, `src/index.css`, `src/lib/utils.ts`
- Create: `src/components/ui/*` mediante shadcn CLI
- Copy: `public/banks/*.json` desde los 10 JSON de la raíz

**Interfaces:**
- Produce el alias `@/*`, el proveedor de tema y los componentes shadcn `Button`, `Card`, `Badge`, `Tabs`, `Dialog`, `AlertDialog`, `Input`, `Textarea`, `Select`, `Checkbox`, `Switch`, `Progress`, `Table`, `ScrollArea`, `Separator`, `Tooltip`, `DropdownMenu`, `Sheet`, `Toast/Sonner`, `Skeleton` y `Empty`.

- [ ] Crear el proyecto Vite React TS sin borrar los JSON existentes.
- [ ] Inicializar shadcn/ui con preset local y agregar los componentes usados.
- [ ] Definir tokens claros/oscuros en `src/index.css`, tipografía del sistema, focus visible y responsive base.
- [ ] Copiar todos los JSON detectados a `public/banks` y generar un manifest de nombres para el seed.
- [ ] Ejecutar `npm run build` para verificar que el scaffold compila.

### Task 2: Dominio y validación TDD

**Files:**
- Create: `src/domain/types.ts`, `src/domain/question-types.ts`, `src/domain/validation.ts`, `src/domain/evaluation.ts`, `src/domain/mastery.ts`, `src/domain/session-selector.ts`, `src/domain/time.ts`, `src/domain/backup.ts`
- Test: `src/domain/*.test.ts`

**Interfaces:**
- `validateBank(input: unknown, sourceName: string): ValidationResult`
- `evaluateAnswer(question: Question, answer: AnswerValue): EvaluationResult`
- `applyProgress(previous: QuestionProgress | undefined, result: EvaluationResult, now: number): QuestionProgress`
- `selectSessionQuestions(questions: Question[], progress: Map<string, QuestionProgress>, config: SessionConfig, seed: number): Question[]`
- `formatElapsedMs(ms: number): string`, `getMedian(values: number[]): number`

- [ ] Escribir tests fallando para schema, IDs duplicados, opciones, tipos soportados y bancos de 1.0.
- [ ] Ejecutar Vitest y confirmar fallos por funciones inexistentes.
- [ ] Implementar tipos y validación exacta con errores por ruta/ID sin mutar el input.
- [ ] Escribir tests fallando para los 12 tipos, incluyendo multi-select, ordering y matching.
- [ ] Implementar el evaluador, la normalización de respuestas y el manejo de no respondida.
- [ ] Escribir tests fallando para mastery, dominada, cola de repetición, temporizador y estadísticas matemáticas.
- [ ] Implementar dominio y temporizador puros.
- [ ] Escribir tests fallando para mezcla por capítulo/fuente/factKey, campeonato y deduplicación.
- [ ] Implementar selector con RNG semillado, cuotas con redistribución y penalizaciones de proximidad.
- [ ] Escribir tests de exportación/importación de respaldo y validar antes de reemplazar.
- [ ] Implementar serialización versionada de backup.
- [ ] Ejecutar toda la suite y refactorizar solo con tests verdes.

### Task 3: Persistencia IndexedDB y estado de aplicación

**Files:**
- Create: `src/storage/db.ts`, `src/storage/repositories.ts`, `src/storage/seed.ts`, `src/app/app-state.tsx`, `src/app/routes.ts`
- Test: `src/storage/*.test.ts`

**Interfaces:**
- `openAppDb(): Promise<IDBDatabase>`
- `bankRepository.upsert(bank)`, `bankRepository.list()`, `bankRepository.remove(bankId)`
- `progressRepository.get(questionKey)`, `progressRepository.put(progress)`, `progressRepository.list()`
- `sessionRepository.add(session)`, `sessionRepository.list()`, `sessionRepository.get(id)`
- `backupRepository.exportAll()`, `backupRepository.importAll(payload)`

- [ ] Escribir pruebas de repositorios con IndexedDB en memoria.
- [ ] Implementar stores `banks`, `questions`, `progress`, `sessions`, `reports`, `settings` con índices necesarios.
- [ ] Implementar seed de todos los bancos locales por fingerprint, idempotente y sin sobrescribir progreso.
- [ ] Implementar provider de estado que cargue datos una sola vez y exponga refreshes explícitos.
- [ ] Ejecutar tests de persistencia y prueba de segunda apertura.

### Task 4: Shell, dashboard y bancos

**Files:**
- Create: `src/components/AppShell.tsx`, `src/components/SidebarNav.tsx`, `src/components/DashboardPage.tsx`, `src/components/BankManagerPage.tsx`, `src/components/StatCard.tsx`, `src/components/ChapterTable.tsx`, `src/components/ImportDialog.tsx`, `src/components/BackupControls.tsx`
- Modify: `src/App.tsx`

**Interfaces:**
- Navegación interna por estado/ruta: `dashboard`, `banks`, `practice`, `stats`, `history`, `review`.
- Callbacks de importación que devuelven `ValidationResult` y solo escriben después de confirmación.

- [ ] Montar shell responsive con sidebar en escritorio y Sheet en móvil.
- [ ] Implementar dashboard con métricas generales, fuente, capítulo, dominadas, difíciles, nuevas y puntos débiles.
- [ ] Implementar dropzone multiarchivo, selector de archivos, reemplazo, eliminación, exportación de bancos y mensajes de errores detallados.
- [ ] Implementar backup/restore con diálogo de validación previa y descarga local.
- [ ] Verificar con `npm run build` y una prueba de interacción del dashboard.

### Task 5: Generador y quiz de todos los modos

**Files:**
- Create: `src/components/SessionBuilderPage.tsx`, `src/components/QuizPage.tsx`, `src/components/QuestionRenderer.tsx`, `src/components/question-types/*.tsx`, `src/components/QuizTimer.tsx`, `src/components/KeyboardShortcuts.tsx`, `src/components/ResultsPage.tsx`
- Modify: `src/app/app-state.tsx`
- Test: `src/components/quiz-flow.test.tsx`

**Interfaces:**
- `startSession(config): Promise<SessionDraft>`
- `submitAnswer(answer): void`, `advanceQuestion(): void`, `finishSession(): Promise<Session>`
- `QuestionRenderer` renderiza los 12 tipos y devuelve `AnswerValue` serializable.

- [ ] Escribir pruebas de flujo para una sesión con respuestas, timeout y persistencia de resultados.
- [ ] Implementar builder con filtros de fuente, capítulos, dificultad, tipos, estados, cantidad y timers.
- [ ] Implementar modos final, entrenamiento, errores, difíciles, velocidad, nuevas, mezcla, capítulo y campeonato como presets de configuración.
- [ ] Implementar renderer accesible para todos los tipos; ordering con drag-and-drop y botones arriba/abajo; matching con pares; multi-select con confirmación.
- [ ] Implementar reloj por pregunta/total, atajos protegidos dentro de sesión, pantalla completa y no revelar respuestas en final/velocidad/campeonato.
- [ ] Implementar favoritos, difícil, reportar, referencia y resultado final.
- [ ] Ejecutar pruebas de flujo y smoke manual en desktop/móvil.

### Task 6: Estadísticas, historial y revisión

**Files:**
- Create: `src/components/StatisticsPage.tsx`, `src/components/HistoryPage.tsx`, `src/components/SessionReviewPage.tsx`, `src/components/ReviewReportsPage.tsx`, `src/lib/statistics.ts`
- Test: `src/lib/statistics.test.ts`

- [ ] Escribir tests para agregados por fuente/capítulo/dificultad/tipo, precisión, media, mediana, peor a mejor y puntos débiles.
- [ ] Implementar tablas y tarjetas de estadísticas con ordenamiento.
- [ ] Implementar historial y revisión de una sesión con lista completa de respuestas.
- [ ] Implementar reportes sospechosos con motivo, respuesta, referencia y copia JSON.
- [ ] Verificar que los datos cambian después de una sesión y sobreviven reload.

### Task 7: QA, PWA/offline y entrega

**Files:**
- Create: `public/manifest.webmanifest`, `public/sw.js`, `tests/e2e/smoke.spec.ts`, `playwright.config.ts`
- Modify: `index.html`, `src/main.tsx`, `package.json`

- [ ] Implementar service worker de caché del app shell sin red.
- [ ] Ejecutar `npm test`, `npm run build` y `npm run lint` si están configurados.
- [ ] Iniciar preview local y ejecutar smoke: carga, banco, builder, cada tipo, timer, resultados, stats, backup/restore y reload.
- [ ] Verificar viewport desktop y móvil, focus visible, labels y ausencia de errores de consola.
- [ ] Verificar build con red desactivada después de precache.
- [ ] Revisar diff, eliminar artefactos temporales y entregar enlaces de archivos + comandos ejecutados.
