# Tarea 9 — E2E responsive y QA renderizado

Estado: **NEEDS_CONTEXT**

Base verificada: `6aec5c0f8a79f85c16ba4589266f214c412dd75b`

Commit de la tarea: se informa en el handoff posterior al commit único; el SHA no puede autorreferenciarse dentro del mismo árbol del commit.

## Resultado

La configuración Playwright ahora expone `desktop-chromium` (1440 × 900) y `mobile-chromium` (Chromium con perfil iPhone 13 y viewport 390 × 844). Los artefactos automáticos se escriben en `%TEMP%/conexion-biblica-playwright`, nunca dentro del repositorio.

Se añadió cobertura responsive específica por proyecto y se actualizaron los flujos de entrenamiento para:

- usar `radiogroup`/`radio` en escritorio y `combobox` nativo en móvil al elegir banco;
- acotar navegación por su landmark accesible y resolver el menú móvil `Más`;
- validar Configuración avanzada antes de consultar estrategia o temporizadores;
- abrir explícitamente la pestaña Familias y los `details` de curación V4;
- evitar ambigüedades entre texto visible y anuncios `sr-only`;
- comprobar la etiqueta V4 dentro del reporte específico, sin una aserción global vacua.

No se modificó código de producción.

## TDD: RED → GREEN

### RED responsive

Comando: `npm.cmd run test:e2e -- responsive-experience.spec.ts`

Con la configuración original de un solo proyecto `chromium`:

- escritorio: 1 pasó;
- móvil: 1 falló;
- fallo esperado: `getByRole('navigation', { name: 'Navegación móvil' })`, esperado 1, recibido 0.

El primer intento dentro del sandbox produjo `Error: spawn EPERM`; se repitió fuera del sandbox, como autoriza el brief, para obtener el RED conductual real.

### GREEN responsive

Comando: `npm.cmd run test:e2e -- responsive-experience.spec.ts`

- 2 pasaron;
- 2 se omitieron por pertenecer al proyecto opuesto.

### RED de selectores heredados

La primera corrida de `training-modes.spec.ts` reprodujo selectores obsoletos/ambiguos:

- `Practicar` resolvía dos botones (navegación y recomendación);
- `Pregunta 1 de 10` resolvía texto visible y anuncio `sr-only`;
- las expectativas `Adaptativa`, `12 segundos` y `10 minutos` consultaban controles todavía ocultos;
- Estadísticas consultaba Familias sin activar su pestaña;
- Revisión conservaba el nombre antiguo `Revisar preguntas`.

Tras acotar por roles, landmarks, pestañas y disclosure, los flujos focales pasaron en ambos viewports.

## Verificación automatizada

| Gate | Resultado |
|---|---|
| `npm.cmd run typecheck` | PASS, exit 0 (`tsc --noEmit`) |
| `npm.cmd run lint -- --ignore-pattern ".worktrees/**"` | PASS, exit 0 |
| `npm.cmd run build` | PASS, exit 0; 1732 módulos transformados |
| `npm.cmd run test:e2e` | PASS: 18 pasaron, 2 omitidos por proyecto, 4.9 min |
| `git diff --check` | PASS antes del commit |

El build mantiene la advertencia preexistente de un chunk minificado mayor de 500 kB (`index-*.js`, ~530 kB). No pertenece al alcance de esta tarea.

## Bloqueo de suite unitaria

Comando requerido: `npm.cmd test -- --exclude ".worktrees/**" --reporter=dot`

Dos corridas globales reprodujeron contaminación DOM dependiente del orden:

- corrida 1: 194/215 pasaron, 21 fallaron;
- corrida JSON final: 193/215 pasaron, 22 fallaron, 5 archivos afectados.

Archivos de la corrida JSON final:

- `src/components/app-states.test.tsx`: 1 fallo;
- `src/components/bank-selector.test.tsx`: 2 fallos;
- `src/components/insight-pages.test.tsx`: 10 fallos;
- `src/components/session-builder-page.test.tsx`: 8 fallos;
- `src/components/layout/layout-primitives.test.tsx`: 1 fallo.

Evidencia: aparecen múltiples `h1`, filas, listas y controles de renders anteriores. Los cinco archivos pasan cuando se ejecutan en procesos aislados: 34/34 pruebas (2 + 4 + 13 + 12 + 3). El cambio de 21 a 22 fallos entre corridas también confirma dependencia del orden/cleanup.

La corrección exige cleanup global/configuración Vitest o editar unit tests fuera del ownership exclusivo de Tarea 9. Por instrucción del integrador, no se tocaron esos archivos. Ésta es la única razón del estado **NEEDS_CONTEXT**.

Reporte JSON temporal: `C:/Users/melar/AppData/Local/Temp/conexion-biblica-task9-vitest.json`.

## Browser QA

Browser plugin: **Available**. Se usó Codex In-app Browser; no hubo fallback a Playwright para el flujo renderizado.

URL: `http://127.0.0.1:4173/`
Título: `Conexión Bíblica 2026`

Flujo validado en escritorio y móvil:

`Inicio → cambiar V4/V3/V4 → Practicar → Aprender → Configuración avanzada → Comenzar ronda → responder → feedback → terminar → Resultados → Banco de preguntas`.

Las respuestas de prueba incorrectas activaron los reintentos intencionales de Aprender (`scheduleTrainingRetry`), por lo que los resultados terminaron en 14 preguntas en escritorio y 18 en móvil aunque la ronda iniciara en 10. No es un bug de producción.

| Check | Escritorio | Móvil |
|---|---|---|
| Page identity | PASS | PASS |
| Contenido significativo / no blank | PASS | PASS |
| Framework overlay | Ausente | Ausente |
| Console error/warn | 0 | 0 |
| Overflow horizontal | `scrollWidth === clientWidth` | `scrollWidth === clientWidth` |
| Cambio de banco | V3 y vuelta a V4 comprobados | `prep-v3` y vuelta a `curated-v4` comprobados |
| Avanzada | `aria-expanded=true`, contenido visible | `aria-expanded=true`, contenido visible |
| Quiz | navegación global ausente, feedback/fuente visibles | navegación global ausente, feedback/fuente visibles |
| Resultados | Resultado y recomendación visibles | Resultado y recomendación visibles |
| Listas | Bancos: 29 filas, sin overflow | Bancos: 29 filas; Historial y Revisión sin overflow |

Viewport solicitado por Browser: 1440 × 900 y 390 × 844. El ancho de contenido reportado fue 1425/375 px cuando la barra de scroll vertical ocupó 15 px; durante FocusShell móvil fue 390 px. Los proyectos Playwright usan exactamente 1440 × 900 y 390 × 844.

Limitación de QA: `locator.press("Enter")` y CUA `ENTER` enfocaron el botón móvil Practicar, pero no activaron la navegación; ambos intentos agotaron el timeout esperando el `h1` `Configura tu próxima ronda`. La navegación por click y los nombres/roles accesibles sí fueron verificados. La activación por teclado queda sin evidencia Browser concluyente.

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

Se verificó tema oscuro en el flujo inicial y tema claro en la pantalla de Bancos. El viewport Browser se restauró al finalizar y no quedó servidor local escuchando en el puerto 4173.

## Criterios de aceptación

1. PASS: el selector desktop es una lista vertical de cinco radios; no una fila de cinco tarjetas.
2. PARCIAL: la geometría se comprobó a 1440 y la variante compacta a 390; no hubo captura manual adicional a 1024.
3. PASS: FocusShell elimina navegación y conserva lectura/acción sin overflow.
4. PASS: avanzada inicia cerrada y sólo aparece tras activar el disclosure.
5. PASS: Bancos, Historial y Revisión no desbordan a 390; Bancos muestra filas apiladas.
6. PASS en los flujos renderizados; los unit tests de estados pasan aislados, pero el gate global está bloqueado por cleanup.
7. PARCIAL: roles/nombres/foco visible comprobados; activación Browser por teclado no fue concluyente.
8. PASS: E2E de recarga y flujos en contextos independientes.
9. NEEDS_CONTEXT: typecheck, lint, build y E2E pasan; suite unitaria global falla por contaminación cross-file.
10. PASS en las diez capturas revisadas: sin solapamientos, recortes ni overflow horizontal observable.

## Bugs reales y concerns

- No se encontró un bug de producción dentro del flujo autorizado.
- Bloqueo test-only: cleanup global/cross-file fuera de ownership.
- Concern no bloqueante: advertencia de chunk >500 kB en build.
- Cobertura pendiente: prueba Browser de teclado fiable y revisión manual específica a 1024 px.
