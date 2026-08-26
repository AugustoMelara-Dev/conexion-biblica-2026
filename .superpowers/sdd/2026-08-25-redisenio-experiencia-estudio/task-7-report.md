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
