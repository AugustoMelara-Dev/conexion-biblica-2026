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

## Fix round 1

**Estado:** DONE

- Los tres `Switch` avanzados se etiquetan mediante `aria-labelledby` y se cubren por rol/nombre accesible.
- La ruta rápida usa como máximo dos columnas editoriales (`md:grid-cols-2`); una prueba protege que no vuelva `lg:grid-cols-4`.
- `EssentialSettings` y `RoundSummary` ahora consumen exactamente las props del brief. El detalle del ciclo se compone desde el padre y el CTA mantiene su semántica `onStart(config, resetCycle)` sin ampliar esas APIs.
- `AdvancedSettings` genera su ID de panel con `useId`, con una prueba que verifica que dos disclosures no colisionen.
- La cobertura adicional confirma persistencia al cerrar/reabrir, preset de simulacro, cambio de banco y payload completo con ciclo agotado.
- Validación: `session-builder-page.test.tsx` (11 pruebas) y la regresión focal con dominio (20 pruebas) aprobadas; typecheck, ESLint focal y diff-check aprobados.
- QA móvil posterior: CTA visible dentro de un `aside` con `position: static`, sin overflow horizontal (`scrollWidth=417`, `innerWidth=434`) y sin errores ni advertencias de consola.

## Fix round 2

**Estado:** DONE

- Se reemplazó la conversión insegura de una fixture parcial por `createAppContext`, que devuelve un `ReturnType<typeof useApp>` completo y tipado.
- La fixture conserva los valores observables de SessionBuilder (preguntas, progreso, banco, ciclos y callback) y completa el resto de contratos de contexto con valores inertes de prueba.
- Validación: `tsc -p tsconfig.app.json --noEmit`, 20 pruebas focales/dominio, ESLint focal y `npm.cmd run build` aprobados. El build conserva únicamente el aviso existente de tamaño de chunk superior a 500 kB.

## Fix round 3

**Estado:** DONE

- `getQuestionProgress` ahora crea un `QuestionProgress` nuevo en cada llamada, con `history` independiente y `questionKey` derivado mediante `getQuestionKey(question)`.
- Los setters de la fixture (`setBankSelection`, `setNav`, `setPreferences`) y el callback `onStart` usan las firmas exactas del contexto o del componente mediante `vi.fn<T>()`; no quedan `ReturnType<typeof vi.fn>` ni casts permisivos.
- Se añadió una prueba de aislamiento para dos respuestas a preguntas distintas. Validación: 21 pruebas focales/dominio, `tsc -p tsconfig.app.json --noEmit`, ESLint focal y build aprobados. El build conserva sólo el aviso conocido de chunk superior a 500 kB.
