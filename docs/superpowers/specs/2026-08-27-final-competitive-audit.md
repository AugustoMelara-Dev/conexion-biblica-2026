# Especificación: auditoría competitiva final

## Objetivo

Validar y corregir la última capa de preparación competitiva antes de ampliar el banco más allá de 12,000 preguntas.

## Requisitos

1. Auditar manualmente una muestra estratificada grande de Daniel 7–12 y PR39–44, con énfasis en selección contextual, verdadero/falso falso y completar.
2. Confirmar en una ronda real de producción que 100 preguntas contienen 30 completar, 25 verdadero/falso y 45 selecciones; no repiten `fact_id`; incluyen suficientes trampas contextuales; excluyen la reserva ciega; y priorizan hechos fallados o lentos en rondas posteriores.
3. Validar durante rondas consecutivas que cambian las posiciones, las variantes y los distractores; que los errores reaparecen con separación; que una corrección inmediata no cuenta como dominio; y que la reserva ciega no aparece en entrenamiento normal.
4. Corregir cualquier hallazgo sin generar más preguntas ni desplegar sin autorización adicional.

## Evidencia mínima

- Pruebas automatizadas con banco real.
- Auditoría profunda contra el PDF fuente.
- Inspección de una ronda activa en producción.
- Informe reproducible con tamaño de muestra, hallazgos y riesgos residuales.
