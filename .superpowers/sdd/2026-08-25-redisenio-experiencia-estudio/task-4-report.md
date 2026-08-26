# Tarea 4 — Práctica con divulgación progresiva

**Estado:** DONE

**Commit de implementación:** `31240d5 feat: enfoca configuración de práctica`

## Entregado

- Extracción de `ModePicker`, `EssentialSettings`, `AdvancedSettings` y `RoundSummary`.
- La pantalla muestra inicialmente modo, banco, fuentes, cantidad, resumen y CTA. Dificultad, capítulos, tipos, estado, estrategia y tiempo sólo se montan al abrir «Configuración avanzada».
- Se mantuvieron en `SessionBuilderPage` los cálculos de elegibilidad/ciclo, el preset de simulacro, la ruta de estudio y la llamada `onStart(config, resetCycle)`.
- El resumen es sticky sólo en `xl`; en móvil sigue el flujo normal y no produce desbordamiento horizontal.

## TDD y evidencia

- RED: se añadieron primero pruebas de divulgación progresiva. El primer intento local quedó bloqueado antes de ejecutar casos por `esbuild`/sandbox (`spawn EPERM`); la ejecución con permiso inició Vitest pero no devolvió el resumen de aserciones. El fallo esperado era que los filtros secundarios aún estaban visibles en la implementación base.
- GREEN: `npm.cmd test -- src/components/session-builder-page.test.tsx --reporter=dot` — 4/4 pruebas aprobadas.
- Regresión focal: `npm.cmd test -- src/components/session-builder-page.test.tsx src/domain/session-selection.test.ts src/domain/session-selector.test.ts --reporter=dot` — 13/13 pruebas, 2 archivos, aprobadas. No existe `src/domain/session-selector.test.ts` en este worktree.
- Tipos: `npm.cmd run typecheck` aprobado.
- ESLint focalizado sobre los seis archivos modificados aprobado sin diagnósticos.
- Diff: `git diff --cached --check` aprobado antes del commit.

## QA visual

- Escritorio (`127.0.0.1:5173`): el resumen queda lateral y el disclosure pasó de `aria-expanded=false` sin «Dificultad» a `true` con «Dificultad» y «Tipos de pregunta» visibles; consola sin advertencias ni errores.
- Móvil (390 × 844): resumen y CTA visibles, filtros secundarios cerrados, `scrollWidth=375` frente a `innerWidth=390` (sin overflow horizontal), consola sin advertencias ni errores.

## Decisiones y preocupaciones

- El selector de banco de los esenciales actualiza tanto el `SessionConfig` como la selección activa de la aplicación, para que el banco visible coincida con el conjunto de preguntas elegibles.
- Se conservaron cantidad personalizada (mínimo y máximo elegible), selección de fuentes, capítulos, bandas/niveles, tipos, estados, estrategia, bloques, temporizadores y ambas aleatorizaciones.
- Única limitación de evidencia: el proceso RED escalado no imprimió el resumen de Vitest después de arrancar; el test se escribió y ejecutó antes de producir los componentes, pero el fallo de aserción no quedó capturado por el runner.
