# Tarea 6 — Bancos como lista escaneable

**Estado:** DONE

**Commit de implementación:** `5f2c107 feat: ordena gestión de bancos en una lista`

## Entregado

- La gestión de bancos usa `PageHeader`, `SectionHeader` y `EmptyState`; «Importar banco» permanece siempre visible, incluso sin resultados.
- Búsqueda accesible «Buscar bancos», normalizada sin tildes, y filtro nativo «Fuente».
- Lista semántica `table`/`row`/`cell`: nombre y archivo, fuente, conteo calculado desde `allQuestions` y acciones por banco.
- V2, V3 y V4 continúan de sólo lectura. Cada V4 con datos de curación presenta un único `details` expandible que conserva resumen, fecha y fingerprint.
- Se conservaron importación por selector y arrastre, reemplazo y eliminación confirmada, exportaciones, respaldo y restauración.
- La cuadrícula de cuatro columnas sólo corresponde a la fila de datos estructurados; en móvil se apila, las acciones envuelven y no crea overflow. El resto de la página no supera tres columnas globales.

## TDD y evidencia

- RED observado: `npm.cmd test -- src/components/bank-manager-page.test.tsx --reporter=dot` falló con la ausencia del `searchbox` «Buscar bancos» y de las filas con rol `row`.
- GREEN: la misma prueba pasó 2/2 después de la implementación.
- Regresión focal: `npm.cmd test -- src/components/bank-manager-page.test.tsx src/domain/backup.test.ts src/storage/storage.test.ts --reporter=dot` pasó 17/17 pruebas en 3 archivos.
- `tsc -p tsconfig.app.json --noEmit` pasó sin diagnósticos.
- ESLint focal sobre los dos archivos pasó sin diagnósticos.
- `npm.cmd run build` pasó; Vite sólo informó el aviso conocido de chunk minificado superior a 500 kB.
- `git diff --cached --check` pasó antes del commit.

## QA visual

- Escritorio 1440 × 900: búsqueda `v4` redujo la tabla a tres bancos cuyo nombre o archivo coincide; «Importar banco» siguió visible, `scrollWidth=1425` y `clientWidth=1425`, sin logs de error o warning.
- Móvil 390 × 844: el menú «Más» abrió «Bancos», la fila V4 expandió sus estadísticas de curación, `scrollWidth=375` y `clientWidth=375`, sin logs de error o warning. Las acciones y los datos se mostraron apilados, sin recorte.

## Decisiones y preocupaciones

- La coincidencia busca tanto `name` como `sourceFileName`, como exige el brief; por eso `v4` también puede encontrar archivos cuyo nombre contiene `v4` aunque el título del banco no lo tenga.
- `e2e/training-modes.spec.ts` de la base todavía espera que todos los resúmenes V4 estén visibles sin expandir. La Tarea 9 es propietaria de estabilizar esos selectores; no se modificó ese archivo para respetar el alcance de esta tarea.

## Fix round 1

**Estado:** DONE

- Las acciones repetidas ahora tienen nombres contextuales globales: «Reemplazar {nombre}» y «Eliminar {nombre}», conservando el texto visual compacto. Reemplazo y eliminación continúan enviando el `bankId` exacto y la eliminación exige confirmación.
- Búsqueda, filtro, acciones de filas y summary V4 tienen objetivo mínimo de 44 px (`min-h-11`); el summary ocupa todo el ancho, conserva el foco visible y mantiene las estadísticas expandibles.
- El conteo de preguntas ahora recorre `allQuestions` una única vez y se memoiza, en vez de filtrar por cada banco y pulsación.
- Cobertura añadida: reemplazo por ID, eliminación confirmada, V2/V3 de sólo lectura, metadatos/fingerprint V4 y restauración de respaldo.

### Evidencia

- RED: el test focal falló porque no existían «Reemplazar Daniel 2» ni «Eliminar Daniel 2» como nombres accesibles globales.
- GREEN y regresión: `npm.cmd test -- src/components/bank-manager-page.test.tsx src/domain/backup.test.ts src/storage/storage.test.ts --reporter=dot` — 20/20 pruebas, 3 archivos.
- `tsc -p tsconfig.app.json --noEmit`, ESLint focal y `npm.cmd run build` aprobaron. El build conserva únicamente el aviso conocido del chunk superior a 500 kB.
- `git diff --check` aprobó.
- QA visual adicional: el navegador externo quedó en «Preparando tus bancos» más de 30 s por su perfil local, antes de abrir la página objetivo. Se restableció el viewport y se detuvo el servidor temporal; la QA previa del navegador interno ya había comprobado la lista móvil y escritorio sin overflow ni consola.
