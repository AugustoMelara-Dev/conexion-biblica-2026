# Tarea 9 — E2E responsive y QA renderizado

Estado: **DONE**

Base verificada: `6aec5c0f8a79f85c16ba4589266f214c412dd75b`

Commit inicial de Tarea 9: `b31da2c07b41b7752927f2f69685f32d6171250d`

Commit de Fix round 1: se informa en el handoff posterior al commit; el SHA no
puede autorreferenciarse dentro del mismo árbol del commit.

## Resultado

La configuración Playwright expone `desktop-chromium` (1440 × 900) y
`mobile-chromium` (Chromium con perfil iPhone 13 y viewport 390 × 844). Los
artefactos automáticos se escriben en `%TEMP%/conexion-biblica-playwright`, nunca
dentro del repositorio.

La cobertura E2E:

- usa `radiogroup`/`radio` en escritorio y `combobox` nativo en móvil para
  seleccionar banco, sin depender de clases;
- acota navegación por landmark y nombre accesible;
- prueba a 1024 px que los cinco radios tienen cajas con Y estrictamente
  descendente, que el detalle V4 es visible/legible y que no hay overflow;
- enfoca el botón Practicar, pulsa `Enter` mediante `page.keyboard` y espera el
  H1 de práctica, tanto en desktop como en mobile;
- comprueba mediante `toHaveCount(0)` que Simulacro no renderiza la solución y
  que el loading eliminado tras recargar tampoco permanece en el DOM;
- abre Configuración avanzada antes de consultar controles y expande los
  `details` de curación V4;
- evita ambigüedades entre navegación, recomendación, texto visible y anuncios
  `sr-only`.

El setup global de Vitest ahora ejecuta `cleanup` tras cada prueba, conservando
`jest-dom` y `fake-indexeddb`. Los archivos que además llaman cleanup localmente
siguen siendo inocuos: la suite completa pasa.

No se modificó código de producción.

## TDD: RED → GREEN

### RED responsive/selectores

Con la configuración original de un solo proyecto, la prueba móvil no encontró
`Navegación móvil`. Las primeras corridas de training reprodujeron selectores
obsoletos o ambiguos (`Practicar`, `Pregunta 1 de 10`, controles avanzados
ocultos, pestaña Familias y nombre de Revisión). Se corrigieron únicamente los
tests/configuración dentro del ownership.

### RED de integración

Comando:

`npm.cmd test -- --exclude ".worktrees/**" --reporter=dot`

La corrida estructurada previa al fix obtuvo 193/215: 22 fallos en 5 archivos.
Los mismos archivos pasaron aislados, 34/34, y el DOM de los fallos contenía
controles, filas y encabezados de renders anteriores. Esto confirmó
contaminación cross-file por ausencia de cleanup global.

### GREEN de integración

Después de registrar `afterEach(cleanup)` en `src/test/setup.ts`, el mismo
comando obtuvo:

- 37/37 archivos;
- 215/215 tests;
- duración 14.76 s.

### Focused Fix round 1

Comando:

`npx.cmd playwright test e2e/responsive-experience.spec.ts e2e/training-modes.spec.ts --grep "(1024 px|activa Practicar|Simulacro|recarga)" --reporter=line`

Resultado final: 7 pasaron, 3 se omitieron por pertenecer al proyecto opuesto,
1.9 min. Esto demuestra que `Enter` sí activa Practicar en ambos viewports con un
browser Playwright real; la limitación observada en el controlador Browser no
es un bug de producción.

## Verificación final

| Gate | Resultado |
|---|---|
| Focused responsive/teclado/Simulacro/recarga | PASS: 7 pasaron, 3 skips esperados, 1.9 min |
| `npx.cmd playwright test --reporter=line` | PASS: 20 pasaron, 4 skips esperados, 5.4 min |
| `npm.cmd test -- --exclude ".worktrees/**" --reporter=dot` | PASS: 215/215 en 37/37 archivos |
| `npm.cmd run typecheck` | PASS, exit 0 (`tsc --noEmit`) |
| `npm.cmd run lint` | PASS, exit 0 |
| `npm.cmd run build` | PASS, exit 0; 1732 módulos transformados |
| `git diff --check` | PASS antes del commit |

Los primeros intentos sandboxed de Playwright y Vitest fallaron al crear
procesos con `Error: spawn EPERM`; se repitieron fuera del sandbox, tal como
autoriza el brief, y completaron normalmente. Ningún comando quedó colgado.

El build mantiene la advertencia no bloqueante de un chunk minificado mayor de
500 kB (`index-*.js`, ~530 kB). No pertenece al alcance de esta tarea.

## Browser QA

Browser plugin: **Available**. Se usó Codex In-app Browser primero para el flujo
renderizado completo; Playwright no reemplazó ese QA visual, sino que aportó la
prueba automatizada fiable de teclado que el controlador Browser no pudo
concluir.

URL: `http://127.0.0.1:4173/`

Título: `Conexión Bíblica 2026`

Flujo validado en escritorio y móvil:

`Inicio → cambiar V4/V3/V4 → Practicar → Aprender → Configuración avanzada → Comenzar ronda → responder → feedback → terminar → Resultados → Banco de preguntas`.

| Check | Escritorio | Móvil |
|---|---|---|
| Page identity / DOM significativo | PASS | PASS |
| Framework overlay | Ausente | Ausente |
| Console error/warn | 0 | 0 |
| Overflow horizontal | `scrollWidth === clientWidth` | `scrollWidth === clientWidth` |
| Cambio de banco | V3 y vuelta a V4 | `prep-v3` y vuelta a `curated-v4` |
| Avanzada | expandida y visible | expandida y visible |
| Quiz | feedback/fuente visibles | feedback/fuente visibles |
| Resultados | resultado y recomendación visibles | resultado y recomendación visibles |
| Listas | Bancos: 29 filas | Bancos: 29 filas; Historial/Revisión sin overflow |

Las respuestas incorrectas activaron los reintentos intencionales de Aprender,
por lo que los resultados finalizaron en 14 preguntas en escritorio y 18 en
móvil aunque la ronda iniciara en 10. Es el comportamiento esperado de
`scheduleTrainingRetry`.

### Capturas fuera del repositorio

Directorio: `C:/Users/melar/AppData/Local/Temp/conexion-biblica-task9-browser`

- `desktop-inicio.png`
- `desktop-practicar-avanzada.png`
- `desktop-quiz-feedback.png`
- `desktop-resultados.png`
- `desktop-bancos-claro.png`
- `mobile-inicio.png`
- `mobile-practicar-avanzada.png`
- `mobile-quiz-feedback.png`
- `mobile-resultados.png`
- `mobile-bancos-lista.png`

No quedaron capturas ni artefactos Playwright dentro del repositorio, y no quedó
servidor local escuchando en el puerto 4173.

## Criterios de aceptación

1. PASS: desktop muestra cinco radios verticales, no una fila de tarjetas.
2. PASS: a 1024 px las cajas de los radios respetan orden vertical, el detalle
   V4 es visible y no hay overflow horizontal.
3. PASS: FocusShell elimina navegación global y conserva lectura/acción.
4. PASS: Configuración avanzada inicia cerrada y aparece tras el disclosure.
5. PASS: Bancos, Historial y Revisión no desbordan a 390 px.
6. PASS: estados y flujos pasan en la suite global 215/215.
7. PASS: roles/nombres/foco y activación con Enter están probados en ambos
   proyectos Playwright.
8. PASS: recarga y flujos usan contextos independientes.
9. PASS: unit, typecheck, lint, build y E2E completo están verdes.
10. PASS: las diez capturas revisadas no muestran solapamientos, recortes ni
    overflow horizontal observable.

## Bugs reales y concerns

- No se encontró un bug de producción en el alcance autorizado.
- El blocker test-only de cleanup quedó corregido y verificado globalmente.
- Concern no bloqueante: advertencia de chunk >500 kB en build.
