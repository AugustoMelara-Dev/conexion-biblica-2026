# Tarea 7 — Progreso, historial y revisión como pantallas de trabajo

Estado: **DONE**

## Cambios

- `statistics-page.tsx`: reorganizado como Progreso con `PageHeader`, `MetricStrip` y una única vista tabulada activa. Conserva Capítulos, Tipos, Familias, Dificultad y Fuentes; Resumen contiene los puntos débiles existentes mediante `WeaknessSummary` sin transformar datos.
- `family-mastery-panel.tsx`: conserva `buildFamilyInsights` y sus filtros, pero muestra familias como lista adaptable sin tabla con desplazamiento horizontal.
- `history-page.tsx`: lista cronológica filtrable por modo y banco, con fecha, modo, precisión, duración y banco en cada sesión; los detalles se expanden en contexto y mantienen respuestas, referencias y estados no respondidos.
- `review-page.tsx`: cola priorizada por dificultad/fallos, filtros nativos de Motivo, Capítulo y Familia, dos indicadores máximos por fila y detalles expandibles para motivo, explicación, respuesta, perfil V1–V4 y acciones de copia.
- `insight-pages.test.tsx`: pruebas de exclusividad de vistas estadísticas y de acción útil al vaciar la revisión.

## TDD

- RED observado con `npm.cmd test -- src/components/insight-pages.test.tsx --reporter=dot`: fallaron las dos pruebas por ausencia de la pestaña `Resumen` y del estado vacío `No hay preguntas pendientes` con acción.
- GREEN observado tras la implementación: las pruebas de insights pasaron.

## Evidencia de verificación

- `npm.cmd test -- src/components/insight-pages.test.tsx src/lib/statistics.test.ts src/domain/family-mastery.test.ts --reporter=dot`: 3 archivos, 9 pruebas aprobadas.
- `npm.cmd run typecheck`: aprobado.
- `npm.cmd run build`: aprobado. Vite conserva una advertencia no bloqueante sobre el bundle JavaScript de 527.69 kB después de minificar.
- `npm.cmd exec eslint -- src/components/statistics-page.tsx src/components/family-mastery-panel.tsx src/components/history-page.tsx src/components/review-page.tsx src/components/insight-pages.test.tsx`: aprobado.
- `git diff --check`: aprobado.
- QA visual local: escritorio y móvil a 390 px. La vista Familias sólo aparece al activar su pestaña; las seis pestañas envuelven sin scroll horizontal. Revisión vacía muestra `Empezar una ronda`; no hubo errores ni advertencias de consola relevantes.

## Incidencia encontrada y corregida

La primera inspección de escritorio detectó que la lista de seis pestañas mantenía la altura de una sola fila y superponía el contenido de Familias. Se corrigió con la variante de altura horizontal del componente Tabs y controles de 44 px; la segunda inspección confirmó que no se superponen.

---

## Fix round 1 — Estado: **DONE**

### Correcciones

- La cobertura ahora cuenta preguntas únicas (`total - sin ver`) y no acumulaciones de `timesSeen`; la tira vuelve a mostrar Favoritas y suma Tendencia como diferencia real de precisión entre las dos últimas sesiones completadas.
- La cola de revisión separa dificultad intrínseca o marcada, fallos, favoritas y reportes. Su prioridad estable pondera explícitamente esos cuatro factores; mantiene sólo Reportada y un segundo estado visible por fila, dejando la taxonomía completa en el detalle.
- Los filtros de familia anuncian el estado con `aria-pressed`. Los encabezados de métricas permanecen accesibles en móvil mediante `sr-only`, y los estados vacíos respetan los hijos válidos de `list` y `rowgroup`.
- Historial y revisión conservan `details` nativo, incorporan un indicador visual de expansión que respeta movimiento reducido y una etiqueta accesible para el resumen.
- La copia maneja portapapeles ausente o rechazado sin promesa no controlada ni confirmación falsa; comunica el error con una región de estado accesible.

### TDD y evidencia

- RED: las nuevas expectativas de cobertura única (`1/1` con una pregunta vista diez veces), tendencia, Favoritas, `aria-pressed` y taxonomía de revisión fallaron antes de las correcciones.
- GREEN: `npm.cmd test -- src/components/insight-pages.test.tsx src/lib/statistics.test.ts src/domain/family-mastery.test.ts --reporter=dot` — **3 archivos, 14 pruebas aprobadas**. Cubre las seis vistas, `WeaknessSummary`, filtros de familia, historial filtrado/no respondido/detalle y cola poblada (orden, filtros, V4, detalle, copia y CTA).
- `npm.cmd run typecheck` — aprobado.
- `npm.cmd run build` — aprobado; permanece sólo la advertencia no bloqueante de Vite por bundle JavaScript mayor a 500 kB.
- `npm.cmd exec eslint -- src/components/statistics-page.tsx src/components/family-mastery-panel.tsx src/components/history-page.tsx src/components/review-page.tsx src/components/insight-pages.test.tsx` — aprobado.
- `git diff --check` — aprobado.
- QA local: resumen de Progreso cargó en escritorio y a 390 px, con las seis pestañas presentes, navegación móvil visible y sin errores de navegador. La interacción de pestañas queda además cubierta por prueba conductual.

---

## Fix round 2 — Estado: **DONE**

### Correcciones y cobertura

- La prueba de familias ahora dispone de una familia Pendiente y otra Dominada. Comprueba inclusión y exclusión al alternar cada filtro, de modo que una implementación que ignore `visible` falla.
- La cobertura de Revisión verifica dificultad manual con nivel bajo, un estado combinado con sólo dos badges visibles y su taxonomía completa en el detalle; también fija el orden de empates con la misma prioridad y fecha.
- Las pruebas de portapapeles cubren tanto ausencia como rechazo de la API y garantizan que ninguno presenta `Copiado` cuando falla.
- La confirmación `Copiado` conserva un único timer por operación: cancela el anterior antes de agendar el nuevo y se limpia al desmontar. La prueba con timers falsos confirma que una segunda copia no pierde su confirmación al expirar la primera.

### Evidencia

- RED: `npm.cmd test -- src/components/insight-pages.test.tsx --reporter=dot` falló porque el timeout de la primera copia borraba la confirmación de la segunda.
- GREEN: `npm.cmd test -- src/components/insight-pages.test.tsx src/lib/statistics.test.ts src/domain/family-mastery.test.ts --reporter=dot` — **3 archivos, 17 pruebas aprobadas**.
- `./node_modules/.bin/tsc.cmd -p tsconfig.app.json --noEmit` — aprobado.
- `npm.cmd run build` — aprobado; únicamente conserva la advertencia no bloqueante de Vite por bundle mayor de 500 kB.
- ESLint focal y `git diff --check` — aprobados.
