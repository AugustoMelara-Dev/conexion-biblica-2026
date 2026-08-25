# Auditoría, piloto, familias y E2E

## Alcance aprobado

1. Auditar semánticamente las 500 preguntas V3 y producir un reporte de hallazgos reproducible.
2. Ejecutar un simulacro piloto local para calibrar tiempo, mezcla de dificultad y puntuación.
3. Mostrar dominio, debilidad y variantes pendientes por `factKey`.
4. Verificar con Playwright Aprender, Repaso inteligente, Simulacro y recarga.

## Diseño

- La auditoría cruza cada pregunta V3 con su `masterQuestionId`, comprueba fuente, capítulo, respuesta, opciones, referencia y señales de redacción sospechosa. Genera JSON para máquinas y Markdown para revisión humana. Un hallazgo de revisión no se presenta como error bíblico confirmado.
- El piloto analiza muchas rondas deterministas de 50 preguntas. La mezcla objetivo conserva 40% EXPERT, 35% HARD, 20% MEDIUM y 5% BASIC/UNRATED. El preset local será configurable y no se describirá como regla oficial.
- La puntuación del simulacro será un porcentaje de aciertos de 0 a 100, sin penalización adicional por usar Aprender o Repaso. El tiempo se reporta como métrica separada.
- El panel deriva una fila por familia: variantes totales, vistas, pendientes, fallos, dominio y estado. `Dominado` exige dominio 4/5 y ninguna variante pendiente; `Débil` exige evidencia de error o dominio bajo después de verla.
- Los E2E usan almacenamiento aislado por contexto y validan feedback inmediato en Aprender, estrategia adaptativa en Repaso, feedback oculto y preset en Simulacro, y persistencia de una ronda tras recargar.

## Salidas

- `reports/semantic-audit-500.{json,md}`
- `reports/simulation-pilot.{json,md}`
- panel integrado en Estadísticas
- `playwright.config.ts` y especificaciones en `e2e/`

