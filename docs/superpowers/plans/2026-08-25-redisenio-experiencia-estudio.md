# Rediseño integral de la experiencia de estudio — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar todas las pantallas de Conexión Bíblica 2026 como un espacio de estudio enfocado, espacioso, responsive y accesible sin modificar datos ni lógica de entrenamiento.

**Architecture:** Se conservarán React, Tailwind CSS v4, Radix UI, IndexedDB y el estado actual. El cambio se apoyará en primitivas visuales compartidas, un shell adaptable y componentes de página más pequeños; la lógica de dominio seguirá en sus módulos existentes. Cada pantalla migrará de tarjetas repetitivas a una jerarquía de cabecera, secciones, listas y divulgación progresiva.

**Tech Stack:** React 19, TypeScript 6, Vite 8, Tailwind CSS v4, Radix UI, Vitest, Testing Library y Playwright.

**Spec:** `docs/superpowers/specs/2026-08-25-redisenio-experiencia-estudio.md`

## Global Constraints

- No modificar el modelo de dominio, el formato de bancos ni las claves de IndexedDB.
- No borrar ni migrar progreso, sesiones, reportes o preferencias.
- No añadir dependencias visuales nuevas sin una carencia demostrable.
- Mantener los modos claro y oscuro.
- Mantener el funcionamiento offline y la política del service worker.
- Máximo tres columnas; contenido textual extenso en un máximo de dos.
- Mantener contraste WCAG AA, foco visible y objetivos táctiles primarios de al menos 44 px.
- Respetar `prefers-reduced-motion`.
- Ejecutar pruebas con `--exclude ".worktrees/**"` para evitar descubrir copias anidadas.

---

## File Structure

### Nuevos archivos

- `src/components/layout/page-header.tsx`: cabecera coherente para páginas.
- `src/components/layout/section-header.tsx`: título y acción de secciones.
- `src/components/layout/metric-strip.tsx`: métricas compactas y responsivas.
- `src/components/layout/empty-state.tsx`: estados vacíos accionables.
- `src/components/layout/focus-shell.tsx`: experiencia sin navegación durante una ronda.
- `src/components/layout/layout-primitives.test.tsx`: contrato accesible de las primitivas.
- `src/components/practice/mode-picker.tsx`: elección de modo de entrenamiento.
- `src/components/practice/essential-settings.tsx`: banco, cantidad y alcance principal.
- `src/components/practice/advanced-settings.tsx`: filtros secundarios plegables.
- `src/components/practice/round-summary.tsx`: resumen del conjunto elegible y acción de inicio.
- `src/components/app-shell.test.tsx`: navegación de escritorio y móvil.
- `e2e/responsive-experience.spec.ts`: flujos de escritorio y móvil.

### Archivos modificados

- `src/index.css`: tokens, tipografía, ritmo, transiciones y utilidades globales.
- `src/components/ui/button.tsx`: alturas, radios y estados interactivos.
- `src/components/ui/card.tsx`: superficies más silenciosas.
- `src/components/app-shell.tsx`: riel colapsable, navegación móvil y enlace de salto.
- `src/components/dashboard-page.tsx`: jerarquía de Inicio.
- `src/components/bank-selector.tsx`: selector maestro–detalle.
- `src/components/bank-selector.test.tsx`: comportamiento responsive y accesible.
- `src/components/session-builder-page.tsx`: composición de práctica y divulgación progresiva.
- `src/components/session-builder-page.test.tsx`: controles esenciales y avanzados.
- `src/components/quiz-page.tsx`: modo concentración.
- `src/components/quiz-page.test.tsx`: navegación oculta y acciones del quiz.
- `src/components/results-page.tsx`: conclusión, recomendación y lista filtrable.
- `src/components/bank-manager-page.tsx`: lista escaneable de bancos.
- `src/components/statistics-page.tsx`: análisis por pestañas.
- `src/components/history-page.tsx`: filas de sesiones.
- `src/components/review-page.tsx`: cola priorizada de revisión.
- `src/App.tsx`: elección entre shell global y `FocusShell`; esqueletos de carga.
- `e2e/training-modes.spec.ts`: selectores estables después del rediseño.
- `playwright.config.ts`: proyecto móvil adicional.

---

### Task 1: Fundamentos visuales y primitivas de layout

**Files:**
- Create: `src/components/layout/page-header.tsx`
- Create: `src/components/layout/section-header.tsx`
- Create: `src/components/layout/metric-strip.tsx`
- Create: `src/components/layout/empty-state.tsx`
- Create: `src/components/layout/layout-primitives.test.tsx`
- Modify: `src/index.css`
- Modify: `src/components/ui/button.tsx`
- Modify: `src/components/ui/card.tsx`

**Interfaces:**
- Produces: `PageHeader({ eyebrow?, title, description?, action? })`.
- Produces: `SectionHeader({ title, description?, action? })`.
- Produces: `MetricStrip({ items })`, donde `items` es `Array<{ label: string; value: ReactNode; detail?: string; icon?: LucideIcon }>`.
- Produces: `EmptyState({ title, description, action?, icon? })`.

- [ ] **Step 1: Write the failing primitive contract tests**

```tsx
it("presenta una sola cabecera principal y conserva la acción", () => {
  render(<PageHeader eyebrow="Preparación" title="Practicar" description="Configura una ronda" action={<button>Comenzar</button>} />)
  expect(screen.getByRole("heading", { level: 1, name: "Practicar" })).toBeVisible()
  expect(screen.getByRole("button", { name: "Comenzar" })).toBeVisible()
})

it("expone las métricas como una lista accesible", () => {
  render(<MetricStrip items={[{ label: "Precisión", value: "82%" }, { label: "Tiempo", value: "8.4 s" }]} />)
  expect(screen.getByRole("list")).toBeVisible()
  expect(screen.getAllByRole("listitem")).toHaveLength(2)
})
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `npm.cmd test -- src/components/layout/layout-primitives.test.tsx --reporter=dot`

Expected: FAIL because the four layout modules do not exist.

- [ ] **Step 3: Implement the shared primitives**

```tsx
export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <header className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
      <div className="max-w-2xl">
        {eyebrow ? <p className="text-sm font-medium text-primary">{eyebrow}</p> : null}
        <h1 className="mt-2 text-balance text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">{title}</h1>
        {description ? <p className="mt-3 max-w-[65ch] text-pretty leading-7 text-muted-foreground">{description}</p> : null}
      </div>
      {action ? <div className="flex sm:justify-start lg:justify-end">{action}</div> : null}
    </header>
  )
}
```

Implement `SectionHeader`, `MetricStrip` and `EmptyState` with semantic `header`, `ul`/`li` and `section` elements. Update button default height to `h-11`, pressed feedback to `active:translate-y-px`, and cards to use `border-border/70 shadow-none`. Add `font-variant-numeric: tabular-nums` to metric values and `text-wrap: balance/pretty` rules in `src/index.css`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `npm.cmd test -- src/components/layout/layout-primitives.test.tsx --reporter=dot`

Expected: PASS with 2 tests.

- [ ] **Step 5: Run existing component tests**

Run: `npm.cmd test -- src/components --exclude ".worktrees/**" --reporter=dot`

Expected: PASS; fix only class-sensitive assertions affected by the new shared primitives.

- [ ] **Step 6: Commit**

```powershell
git add src/index.css src/components/ui/button.tsx src/components/ui/card.tsx src/components/layout
git commit -m "feat: establece sistema visual de estudio"
```

---

### Task 2: Shell adaptable y navegación de baja distracción

**Files:**
- Create: `src/components/app-shell.test.tsx`
- Create: `src/components/layout/focus-shell.tsx`
- Modify: `src/components/app-shell.tsx`
- Modify: `src/App.tsx`

**Interfaces:**
- Consumes: `PageHeader` from Task 1.
- Produces: `AppShell({ children })` with a compact/expanded rail persisted under `conexion-biblica-navigation-collapsed`.
- Produces: `FocusShell({ children, onExit? })` without global navigation.
- Preserves: `QuickStartButton` and `ImportShortcut` exports.

- [ ] **Step 1: Write failing shell tests**

```tsx
it("ofrece un enlace para saltar al contenido", () => {
  renderWithApp(<AppShell><p>Contenido</p></AppShell>)
  expect(screen.getByRole("link", { name: "Saltar al contenido" })).toHaveAttribute("href", "#main-content")
  expect(document.querySelector("#main-content")).not.toBeNull()
})

it("colapsa el riel sin perder nombres accesibles", async () => {
  renderWithApp(<AppShell><p>Contenido</p></AppShell>)
  await userEvent.click(screen.getByRole("button", { name: "Contraer navegación" }))
  expect(screen.getByRole("button", { name: "Practicar" })).toBeVisible()
  expect(localStorage.getItem("conexion-biblica-navigation-collapsed")).toBe("true")
})
```

- [ ] **Step 2: Run the shell tests and verify RED**

Run: `npm.cmd test -- src/components/app-shell.test.tsx --reporter=dot`

Expected: FAIL because the skip link and collapse control are absent.

- [ ] **Step 3: Implement desktop rail, mobile navigation and focus shell**

```tsx
const primaryMobileItems = navItems.filter(({ key }) => ["dashboard", "practice", "stats"].includes(key))

return (
  <>
    <a href="#main-content" className="skip-link">Saltar al contenido</a>
    <aside data-collapsed={collapsed} className={cn("fixed inset-y-0 hidden border-r lg:block", collapsed ? "w-20" : "w-56")}>
      <SidebarContent collapsed={collapsed} />
    </aside>
    <main id="main-content" className={cn("min-h-screen pb-24 lg:pb-0", collapsed ? "lg:pl-20" : "lg:pl-56")}>
      {children}
    </main>
    <nav aria-label="Navegación móvil" className="fixed inset-x-0 bottom-0 lg:hidden">...</nav>
  </>
)
```

In `App.tsx`, render `FocusShell` whenever `activeRound` is truthy; keep the existing round persistence and `onExit` behavior unchanged. Ensure desktop nav buttons retain `aria-current="page"` and mobile «Más» exposes Bancos, Historial and Revisión.

- [ ] **Step 4: Run shell and app-state tests**

Run: `npm.cmd test -- src/components/app-shell.test.tsx src/app/app-state.test.tsx --reporter=dot`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/components/app-shell.tsx src/components/app-shell.test.tsx src/components/layout/focus-shell.tsx src/App.tsx
git commit -m "feat: simplifica navegación y modo concentración"
```

---

### Task 3: Inicio y selector maestro–detalle

**Files:**
- Modify: `src/components/dashboard-page.tsx`
- Modify: `src/components/bank-selector.tsx`
- Modify: `src/components/bank-selector.test.tsx`
- Modify: `src/components/stat-card.tsx`

**Interfaces:**
- Consumes: `PageHeader`, `SectionHeader`, `MetricStrip`.
- Preserves: `BankSelectorProps` fields `value`, `onChange`, `legacyCount`, `masterCount`, `prepCount`, `curatedCount`.
- Produces: one selected profile detail panel and a compact selectable list.

- [ ] **Step 1: Replace the old selector test with failing master–detail expectations**

```tsx
it("muestra detalle solo para el perfil seleccionado", async () => {
  render(<BankSelector value="curated-v4" onChange={onChange} legacyCount={2360} masterCount={3558} prepCount={500} curatedCount={3220} />)
  expect(screen.getByRole("region", { name: "Detalle del banco seleccionado" })).toHaveTextContent("3,220 preguntas")
  expect(screen.getAllByRole("radio")).toHaveLength(5)
  await userEvent.click(screen.getByRole("radio", { name: /V3 — Preparación/ }))
  expect(onChange).toHaveBeenCalledWith("prep-v3")
})

it("no repite advertencias técnicas en opciones no seleccionadas", () => {
  const counts = { legacyCount: 2360, masterCount: 3558, prepCount: 500, curatedCount: 3220 }
  render(<BankSelector value="curated-v4" {...counts} onChange={vi.fn()} />)
  expect(screen.queryByText("Advertencia técnica: conserva el texto original.")).not.toBeInTheDocument()
})
```

- [ ] **Step 2: Run selector tests and verify RED**

Run: `npm.cmd test -- src/components/bank-selector.test.tsx --reporter=dot`

Expected: FAIL because all descriptions and warnings are rendered inside five equal cards.

- [ ] **Step 3: Implement the two-column selector and simplified dashboard**

```tsx
const selected = options.find((option) => option.id === value) ?? options[0]

return (
  <div className="grid gap-4 lg:grid-cols-[minmax(15rem,0.75fr)_minmax(0,1.25fr)]">
    <div role="radiogroup" aria-label="Versión del banco" className="grid gap-2">
      {options.map((option) => (
        <label key={option.id} className="flex min-h-14 items-center gap-3 rounded-xl px-4 py-3 hover:bg-muted/60">
          <input type="radio" name="bank-selection" value={option.id} checked={value === option.id} onChange={() => onChange(option.id)} />
          <span className="font-medium">{option.label}</span>
        </label>
      ))}
    </div>
    <section aria-label="Detalle del banco seleccionado" className="rounded-2xl bg-secondary/55 p-6 sm:p-8">
      <p className="text-sm font-medium text-primary">{selected.recommended ? "Recomendado" : "Perfil disponible"}</p>
      <h3 className="mt-2 text-2xl font-semibold tracking-tight">{selected.label}</h3>
      <p className="mt-3 max-w-[52ch] text-muted-foreground">{selected.description}</p>
      <p className="mt-8 text-3xl font-semibold tabular-nums">{selected.count.toLocaleString("es-HN")}</p>
      <p className="text-sm text-muted-foreground">preguntas</p>
    </section>
  </div>
)
```

Replace the four independent stat cards with `MetricStrip`. Keep only two primary dashboard blocks above the fold: source progress and recommendation. Move the chapter table below a `SectionHeader` and replace the bottom storage card with a compact status line.

- [ ] **Step 4: Run dashboard-related tests**

Run: `npm.cmd test -- src/components/bank-selector.test.tsx src/app/app-state.test.tsx --reporter=dot`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/components/dashboard-page.tsx src/components/bank-selector.tsx src/components/bank-selector.test.tsx src/components/stat-card.tsx
git commit -m "feat: convierte inicio en espacio de estudio"
```

---

### Task 4: Práctica con divulgación progresiva

**Files:**
- Create: `src/components/practice/mode-picker.tsx`
- Create: `src/components/practice/essential-settings.tsx`
- Create: `src/components/practice/advanced-settings.tsx`
- Create: `src/components/practice/round-summary.tsx`
- Modify: `src/components/session-builder-page.tsx`
- Modify: `src/components/session-builder-page.test.tsx`

**Interfaces:**
- Produces: `ModePicker({ value, onChange })` using `SessionMode`.
- Produces: `EssentialSettings({ bankSelection, count, sourceWorks, onBankChange, onCountChange, onSourceWorksChange })` using `BankSelection`, `SessionConfig["count"]` and `SourceWork[]`.
- Produces: `AdvancedSettings({ open, onOpenChange, children })`.
- Produces: `RoundSummary({ eligibleCount, count, mode, onStart, disabled })`.
- Preserves: `SessionBuilderPage({ onStart })` and all `SessionConfig` fields.

- [ ] **Step 1: Write failing progressive-disclosure tests**

```tsx
it("oculta filtros secundarios hasta abrir configuración avanzada", async () => {
  renderSessionBuilder()
  expect(screen.queryByText("Dificultad")).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole("button", { name: "Configuración avanzada" }))
  expect(screen.getByText("Dificultad")).toBeVisible()
  expect(screen.getByText("Tipos de pregunta")).toBeVisible()
})

it("mantiene visibles banco, cantidad y resumen", () => {
  renderSessionBuilder()
  expect(screen.getByRole("combobox", { name: "Cantidad" })).toBeVisible()
  expect(screen.getByText(/preguntas disponibles/)).toBeVisible()
  expect(screen.getByRole("button", { name: "Comenzar ronda" })).toBeEnabled()
})
```

- [ ] **Step 2: Run practice tests and verify RED**

Run: `npm.cmd test -- src/components/session-builder-page.test.tsx --reporter=dot`

Expected: FAIL because advanced filters are visible in the initial layout.

- [ ] **Step 3: Extract focused components and recompose the builder**

```tsx
const advancedSettingsContent = (
  <div className="space-y-6">
    {difficultyControls}
    {questionTypeControls}
    {statusControls}
    {orderingAndTimingControls}
  </div>
)

<PageHeader eyebrow="Entrenamiento" title="Configura tu próxima ronda" description="Elige cómo quieres estudiar; ajusta los detalles solo si los necesitas." />
<ModePicker value={config.mode} onChange={setMode} />
<section className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem]">
  <div className="space-y-6">
    <EssentialSettings
      bankSelection={config.bankSelection ?? bankSelection}
      count={config.count}
      sourceWorks={config.sourceWorks}
      onBankChange={(value) => setConfig((current) => ({ ...current, bankSelection: value }))}
      onCountChange={(value) => setConfig((current) => ({ ...current, count: value }))}
      onSourceWorksChange={(value) => setConfig((current) => ({ ...current, sourceWorks: value }))}
    />
    <AdvancedSettings open={advancedOpen} onOpenChange={setAdvancedOpen}>
      <div data-testid="advanced-round-settings">{advancedSettingsContent}</div>
    </AdvancedSettings>
  </div>
  <RoundSummary eligibleCount={eligible.length} count={config.count} mode={config.mode} disabled={!eligible.length} onStart={() => onStart(config, resetCycle)} />
</section>
```

Move only presentation into the new files. Keep eligibility calculations, simulation preset application, study-day selection and `onStart` semantics in `session-builder-page.tsx`.

- [ ] **Step 4: Run unit and domain tests**

Run: `npm.cmd test -- src/components/session-builder-page.test.tsx src/domain/session-selection.test.ts src/domain/session-selector.test.ts --reporter=dot`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/components/session-builder-page.tsx src/components/session-builder-page.test.tsx src/components/practice
git commit -m "feat: enfoca configuración de práctica"
```

---

### Task 5: Quiz enfocado y resultados accionables

**Files:**
- Modify: `src/components/quiz-page.tsx`
- Modify: `src/components/quiz-page.test.tsx`
- Modify: `src/components/question-renderer.tsx`
- Modify: `src/components/results-page.tsx`

**Interfaces:**
- Consumes: `FocusShell` selected by `App.tsx` in Task 2.
- Preserves: all `QuizPage` props and callbacks.
- Preserves: all `ResultsPage` props and callbacks.

- [ ] **Step 1: Write failing focus and result-priority tests**

```tsx
it("presenta metadatos, pregunta y acción en una región de estudio", () => {
  renderQuiz()
  expect(screen.getByRole("main", { name: "Ronda de estudio" })).toBeVisible()
  expect(screen.getByText("Pregunta 1 de 1")).toBeVisible()
  expect(screen.getByRole("button", { name: "Confirmar respuesta" })).toBeVisible()
})

it("prioriza repasar errores cuando existen respuestas incorrectas", () => {
  render(<ResultsPage session={sessionWithErrors} {...callbacks} />)
  expect(screen.getByRole("button", { name: "Repasar errores" })).toHaveAttribute("data-variant", "default")
  expect(screen.getByRole("button", { name: "Repetir esta tanda" })).toHaveAttribute("data-variant", "outline")
})
```

- [ ] **Step 2: Run quiz tests and verify RED**

Run: `npm.cmd test -- src/components/quiz-page.test.tsx --reporter=dot`

Expected: FAIL because the quiz lacks the named study region and result action priority.

- [ ] **Step 3: Implement the focused hierarchy**

```tsx
<main aria-label="Ronda de estudio" className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-3xl flex-col px-4 py-6 sm:px-6">
  <header className="grid grid-cols-[auto_1fr_auto] items-center gap-4">
    <Button variant="ghost" onClick={onExit}>Salir</Button>
    <Progress aria-label="Progreso de la ronda" value={((index + 1) / questions.length) * 100} />
    <span className="tabular-nums">{remaining !== null ? `${remaining}s` : "Sin límite"}</span>
  </header>
  <article className="my-auto py-10">
    <p className="text-sm text-muted-foreground">{question.source.reference} · {typeLabel(question.type)}</p>
    <h1 className="mt-4 text-pretty text-2xl font-semibold leading-tight sm:text-3xl">{question.question}</h1>
    <QuestionRenderer question={displayedQuestion} value={value} disabled={submitted} onChange={setValue} />
    {showFeedback ? (
      <Alert variant={feedback.isCorrect ? "default" : "destructive"}>
        <AlertTitle>{feedback.isCorrect ? "Respuesta correcta" : "Respuesta incorrecta"}</AlertTitle>
        <AlertDescription>{question.explanation}</AlertDescription>
      </Alert>
    ) : null}
  </article>
  <footer className="sticky bottom-0 bg-background/95 py-4 backdrop-blur">
    <Button className="min-h-11 w-full sm:ml-auto sm:w-auto" onClick={() => { if (submitted) advance(); else void submit() }}>
      {submitted ? index === queue.length - 1 ? "Ver resultados" : "Siguiente" : "Confirmar respuesta"}
    </Button>
  </footer>
</main>
```

In Results, use `MetricStrip` for secondary values, render one recommendation block, make «Repasar errores» primary only when errors exist, and add a toggle «Solo incorrectas» before the answer list.

- [ ] **Step 4: Run quiz, resume and evaluation tests**

Run: `npm.cmd test -- src/components/quiz-page.test.tsx src/domain/session-resume.test.ts src/domain/evaluation.test.ts --reporter=dot`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/components/quiz-page.tsx src/components/quiz-page.test.tsx src/components/question-renderer.tsx src/components/results-page.tsx
git commit -m "feat: crea experiencia de ronda enfocada"
```

---

### Task 6: Bancos como lista escaneable

**Files:**
- Modify: `src/components/bank-manager-page.tsx`
- Create: `src/components/bank-manager-page.test.tsx`

**Interfaces:**
- Consumes: `PageHeader`, `SectionHeader`, `EmptyState`.
- Preserves: import, replace, remove, export and backup callbacks from `useApp`.
- Produces: search input labelled `Buscar bancos` and filter labelled `Fuente`.

- [ ] **Step 1: Write failing list and search tests**

```tsx
it("filtra bancos por nombre sin ocultar la acción de importar", async () => {
  renderBankManager({ banks: bankFixtures })
  await userEvent.type(screen.getByRole("searchbox", { name: "Buscar bancos" }), "V4")
  expect(screen.getByText("V4 — Banco Curado Daniel")).toBeVisible()
  expect(screen.queryByText("Daniel 2")).not.toBeInTheDocument()
  expect(screen.getByRole("button", { name: "Importar banco" })).toBeVisible()
})

it("muestra cada banco como una fila con fuente y cantidad", () => {
  renderBankManager({ banks: bankFixtures })
  expect(screen.getByRole("row", { name: /V4 — Banco Curado Daniel.*Daniel.*preguntas/ })).toBeVisible()
})
```

- [ ] **Step 2: Run bank manager tests and verify RED**

Run: `npm.cmd test -- src/components/bank-manager-page.test.tsx --reporter=dot`

Expected: FAIL because search and row semantics do not exist.

- [ ] **Step 3: Implement searchable adaptive rows**

```tsx
function normalize(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
}

const visibleBanks = banks.filter((bank) => {
  const matchesQuery = normalize(`${bank.name} ${bank.sourceFileName}`).includes(normalize(query))
  const matchesSource = source === "all" || bank.sourceWork === source
  return matchesQuery && matchesSource
})
const questionCounts = new Map(banks.map((bank) => [bank.bankId, questions.filter((question) => question.bankId === bank.bankId).length]))

<PageHeader title="Banco de preguntas" description="Administra fuentes y respaldos sin mezclar el progreso de cada banco." action={<Button onClick={openImport}>Importar banco</Button>} />
<div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_14rem]">{search}{sourceFilter}</div>
<div role="table" aria-label="Bancos disponibles" className="divide-y">
  {visibleBanks.map((bank) => {
    const readOnly = bank.bankId === "master-v2" || bank.bankProfileId === "prep-v3" || bank.bankProfileId === "curated-v4"
    return <div role="row" key={bank.bankId} className="grid gap-2 py-4 sm:grid-cols-[minmax(0,1fr)_10rem_8rem_auto] sm:items-center">
      <span role="cell" className="font-medium">{bank.name}</span>
      <span role="cell" className="text-sm text-muted-foreground">{bank.sourceWork}</span>
      <span role="cell" className="text-sm tabular-nums">{questionCounts.get(bank.bankId) ?? 0} preguntas</span>
      <span role="cell" className="flex justify-end gap-2">
        {readOnly ? <Badge variant="secondary">Integrado · solo lectura</Badge> : (
          <>
            <Button variant="outline" onClick={() => selectFiles(bank.bankId)}>Reemplazar</Button>
            <Button variant="ghost" className="text-destructive" onClick={() => { if (window.confirm(`¿Eliminar ${bank.name}? El progreso se conserva separado.`)) void removeBank(bank.bankId) }}>Eliminar</Button>
          </>
        )}
      </span>
    </div>
  })}
</div>
```

Keep the V4 curation summaries as one expandable detail per integrated V4 source. Keep all destructive actions behind the existing confirmation dialog.

- [ ] **Step 4: Run bank and backup tests**

Run: `npm.cmd test -- src/components/bank-manager-page.test.tsx src/domain/backup.test.ts src/storage/storage.test.ts --reporter=dot`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/components/bank-manager-page.tsx src/components/bank-manager-page.test.tsx
git commit -m "feat: ordena gestión de bancos en una lista"
```

---

### Task 7: Progreso, historial y revisión como pantallas de trabajo

**Files:**
- Modify: `src/components/statistics-page.tsx`
- Modify: `src/components/family-mastery-panel.tsx`
- Modify: `src/components/history-page.tsx`
- Modify: `src/components/review-page.tsx`
- Create: `src/components/insight-pages.test.tsx`

**Interfaces:**
- Consumes: `PageHeader`, `MetricStrip`, `SectionHeader`, `EmptyState`.
- Produces: statistics tabs named `Resumen`, `Capítulos`, `Tipos`, `Familias`.
- Produces: file-local `WeaknessSummary({ weakChapters, weakTypes })` using the existing statistics row shapes.
- Produces: history rows labelled with date, mode, accuracy, duration and bank.
- Produces: review filter bar with `Motivo`, `Capítulo` and `Familia`.

- [ ] **Step 1: Write failing insight-page tests**

```tsx
it("muestra una sola vista estadística a la vez", async () => {
  renderStatistics()
  expect(screen.getByRole("tab", { name: "Resumen" })).toHaveAttribute("aria-selected", "true")
  expect(screen.queryByText("Dominio por familia de conocimiento")).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole("tab", { name: "Familias" }))
  expect(screen.getByText("Dominio por familia de conocimiento")).toBeVisible()
})

it("ofrece una acción clara cuando la revisión está vacía", () => {
  renderReview({ reports: [], progress: new Map() })
  expect(screen.getByRole("heading", { name: "No hay preguntas pendientes" })).toBeVisible()
  expect(screen.getByRole("button", { name: "Empezar una ronda" })).toBeVisible()
})
```

- [ ] **Step 2: Run insight tests and verify RED**

Run: `npm.cmd test -- src/components/insight-pages.test.tsx --reporter=dot`

Expected: FAIL because statistics renders sections together and review lacks the specified empty state.

- [ ] **Step 3: Recompose the three pages**

```tsx
<PageHeader title="Progreso" description="Detecta qué sabes, qué falta y dónde conviene practicar." />
<MetricStrip items={summaryMetrics} />
<Tabs defaultValue="summary">
  <TabsList aria-label="Vista estadística">
    <TabsTrigger value="summary">Resumen</TabsTrigger>
    <TabsTrigger value="chapters">Capítulos</TabsTrigger>
    <TabsTrigger value="types">Tipos</TabsTrigger>
    <TabsTrigger value="families">Familias</TabsTrigger>
  </TabsList>
  <TabsContent value="summary"><WeaknessSummary weakChapters={statistics.weakChapters} weakTypes={statistics.weakTypes} /></TabsContent>
  <TabsContent value="chapters"><MetricTable title="Rendimiento por capítulo" description="Ordenado de peor a mejor." rows={statistics.chapters} extraHeader="Capítulo" /></TabsContent>
  <TabsContent value="types"><MetricTable title="Rendimiento por tipo" description="Prioriza los tipos con menor precisión." rows={statistics.types} extraHeader="Tipo" /></TabsContent>
  <TabsContent value="families"><FamilyMasteryPanel questions={questions} progress={progress} /></TabsContent>
</Tabs>
```

Extract `WeaknessSummary({ weakChapters, weakTypes })` as a file-local function in `statistics-page.tsx`; it renders the two existing weak lists in one responsive section and introduces no new data transformation.

Render History as a divided list with compact filter controls and expandable details. Render Review as a prioritized queue; show at most two status indicators in each row and move full explanation into an expandable region.

- [ ] **Step 4: Run insights and statistics tests**

Run: `npm.cmd test -- src/components/insight-pages.test.tsx src/lib/statistics.test.ts src/domain/family-mastery.test.ts --reporter=dot`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/components/statistics-page.tsx src/components/family-mastery-panel.tsx src/components/history-page.tsx src/components/review-page.tsx src/components/insight-pages.test.tsx
git commit -m "feat: convierte progreso y revisión en vistas enfocadas"
```

---

### Task 8: Estados transversales y accesibilidad

**Files:**
- Modify: `src/App.tsx`
- Modify: `src/components/ui/skeleton.tsx`
- Create: `src/components/app-states.test.tsx`
- Modify: `index.html`

**Interfaces:**
- Consumes: `EmptyState`.
- Produces: `LoadingState` with `aria-busy="true"` and skeletons matching the dashboard.
- Preserves: partial availability when `masterBankError` is set.

- [ ] **Step 1: Write failing loading and metadata tests**

```tsx
it("marca la carga como ocupada y muestra estructura anticipada", () => {
  renderApp({ loading: true })
  expect(screen.getByRole("status", { name: "Preparando tus bancos" })).toHaveAttribute("aria-busy", "true")
  expect(screen.getAllByTestId("dashboard-skeleton").length).toBeGreaterThan(1)
})

it("mantiene contenido disponible cuando falla V2", () => {
  renderApp({ masterBankError: "Sin conexión", loading: false })
  expect(screen.getByText("Sin conexión. V1 continúa disponible.")).toBeVisible()
  expect(screen.getByRole("heading", { name: /Entrena con intención/ })).toBeVisible()
})
```

- [ ] **Step 2: Run state tests and verify RED**

Run: `npm.cmd test -- src/components/app-states.test.tsx --reporter=dot`

Expected: FAIL because the loading panel lacks the named status and structural skeletons.

- [ ] **Step 3: Implement skeletons, metadata and accessibility polish**

```tsx
function LoadingState() {
  return (
    <section role="status" aria-label="Preparando tus bancos" aria-busy="true" className="space-y-8">
      <span className="sr-only">Cargando preguntas y progreso desde este dispositivo.</span>
      <Skeleton data-testid="dashboard-skeleton" className="h-28 rounded-2xl" />
      <div className="grid gap-4 sm:grid-cols-2"><Skeleton data-testid="dashboard-skeleton" className="h-44" /><Skeleton data-testid="dashboard-skeleton" className="h-44" /></div>
    </section>
  )
}
```

Add a concrete meta description in `index.html`. Audit icon-only buttons for `aria-label`, ensure feedback text accompanies color, and verify every page has exactly one `h1`.

- [ ] **Step 4: Run state and accessibility-focused tests**

Run: `npm.cmd test -- src/components/app-states.test.tsx src/components/app-shell.test.tsx src/components/quiz-page.test.tsx --reporter=dot`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/App.tsx src/components/ui/skeleton.tsx src/components/app-states.test.tsx index.html
git commit -m "feat: completa estados y accesibilidad visual"
```

---

### Task 9: Responsive E2E and rendered QA

**Files:**
- Create: `e2e/responsive-experience.spec.ts`
- Modify: `e2e/training-modes.spec.ts`
- Modify: `playwright.config.ts`

**Interfaces:**
- Consumes: all accessible names established in Tasks 1–8.
- Produces: desktop and mobile Playwright projects.

- [ ] **Step 1: Add failing responsive E2E checks**

```ts
test("escritorio evita la fila de cinco tarjetas", async ({ page }) => {
  await waitForApp(page)
  const selector = page.getByRole("radiogroup", { name: "Versión del banco" })
  const box = await selector.boundingBox()
  const options = await selector.getByRole("radio").all()
  expect(options).toHaveLength(5)
  expect(box?.width).toBeLessThan(520)
  await expect(page.getByRole("region", { name: "Detalle del banco seleccionado" })).toBeVisible()
})

test("móvil navega sin scroll horizontal", async ({ page }) => {
  await waitForApp(page)
  const sizes = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth }))
  expect(sizes.scroll).toBe(sizes.client)
  await expect(page.getByRole("navigation", { name: "Navegación móvil" })).toBeVisible()
})
```

- [ ] **Step 2: Run desktop and mobile E2E and verify RED where layout is not yet wired**

Run: `npm.cmd run test:e2e -- responsive-experience.spec.ts`

Expected: FAIL until `playwright.config.ts` includes both projects and the final accessible names are present.

- [ ] **Step 3: Add the mobile project and stabilize existing selectors**

```ts
projects: [
  { name: "desktop-chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  { name: "mobile-chromium", use: { ...devices["iPhone 13"] } },
]
```

Update `selectBank` in `training-modes.spec.ts` to use the contextual radio group on desktop and the labelled native selector on mobile. Do not use class selectors for navigation or primary actions.

- [ ] **Step 4: Run all unit tests**

Run: `npm.cmd test -- --exclude ".worktrees/**" --reporter=dot`

Expected: all unit test files pass with zero failures.

- [ ] **Step 5: Run lint, build and all E2E tests**

Run: `npm.cmd run lint -- --ignore-pattern ".worktrees/**"`

Expected: exit code 0.

Run: `npm.cmd run build`

Expected: exit code 0 and a Vite production bundle.

Run: `npm.cmd run test:e2e`

Expected: every scenario passes in `desktop-chromium` and `mobile-chromium`.

- [ ] **Step 6: Validate rendered flows with the Browser plugin**

Flow: Inicio → elegir V4 → Practicar → abrir configuración avanzada → iniciar Aprender → responder → ver feedback → terminar → Resultados.

Verify at 1440 × 900 and 390 × 844:

```text
Page identity: title and URL correct
Not blank: meaningful screen content present
Framework overlay: absent
Console errors/warnings: none relevant
Horizontal overflow: document.scrollWidth equals document.clientWidth
Interaction proof: bank, mode, advanced settings and answer state visibly change
```

Capture screenshots outside the repository for Inicio, Practicar, Quiz, Resultados and one data-list screen at both viewports.

- [ ] **Step 7: Review diff and commit**

Run: `git diff --check`

Expected: no whitespace errors.

```powershell
git add e2e/responsive-experience.spec.ts e2e/training-modes.spec.ts playwright.config.ts
git commit -m "test: valida experiencia responsive completa"
```

---

## Final Integration Gate

After Task 9:

1. Run `npm.cmd test -- --exclude ".worktrees/**" --reporter=dot`.
2. Run `npm.cmd run lint -- --ignore-pattern ".worktrees/**"`.
3. Run `npm.cmd run build`.
4. Run `npm.cmd run test:e2e`.
5. Inspect `git diff origin/main...HEAD --check`.
6. Review rendered desktop and mobile screenshots against all ten acceptance criteria in the spec.
7. Push `codex/redesign-experiencia`, create a PR to `main`, wait for required checks and merge only after explicit user authorization.
