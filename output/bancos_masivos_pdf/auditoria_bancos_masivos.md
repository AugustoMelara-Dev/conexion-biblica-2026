# Auditoría de bancos masivos

Fuente única: `MaterialConexionBiblica (1).pdf` (SHA-256 `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`). No se consultó internet ni otra traducción para generar contenido.

## Resultado

- Preguntas estáticas verificadas: 14,000.
- Daniel 1–12: 8,000.
- Profetas y Reyes 39–44: 6,000.
- Hechos atómicos seleccionados: 2,338.
- Variantes por hecho: Daniel [5, 6] (promedio 5.984); PR [5, 6] (promedio 5.994).
- Plantillas: 12 (8 estáticas y 4 de reescritura controlada en tiempo de ejecución).
- Distractores dinámicos únicos: 1,618 (1,704 entradas antes de deduplicar entre bancos).
- Candidatos o spans descartados: 22,700.
- Duplicados textuales o `variant_id` conservados: 0.
- Preguntas sin cita, respuesta o validación: 0.

## Daniel 1–12

- Por capítulo: `{"DAN1": 450, "DAN10": 550, "DAN11": 1050, "DAN12": 450, "DAN2": 650, "DAN3": 550, "DAN4": 650, "DAN5": 500, "DAN6": 500, "DAN7": 900, "DAN8": 900, "DAN9": 850}`.
- Por tipo: `{"multiple_choice": 3600, "fill_blank": 2400, "true_false": 2000}`.
- Por dificultad: `{"hard": 3600, "expert": 2400, "medium": 1600, "easy": 400}`.
- V/F: `{"Verdadero": 1000, "Falso": 1000}`.
- Posiciones A/B/C/D: `{"A": 1500, "B": 1500, "C": 1500, "D": 1500}`.
- Trampas contextuales de selección múltiple: 1440 (40%).
- Reserva ciega: 1201 (15.0%).

## Profetas y Reyes 39–44

- Por capítulo: `{"PR39": 750, "PR40": 850, "PR41": 750, "PR42": 850, "PR43": 1450, "PR44": 1350}`.
- Por tipo: `{"multiple_choice": 2700, "fill_blank": 1800, "true_false": 1500}`.
- Por dificultad: `{"hard": 2700, "expert": 1800, "medium": 1200, "easy": 300}`.
- V/F: `{"Verdadero": 750, "Falso": 750}`.
- Posiciones A/B/C/D: `{"A": 1125, "B": 1125, "C": 1125, "D": 1125}`.
- Trampas contextuales de selección múltiple: 1080 (40%).
- Reserva ciega: 900 (15.0%).

## Pruebas editoriales automáticas

Cada registro pasó comprobación de esquema, fuente y cita no vacías, una sola respuesta marcada, opciones distintas, respuesta presente una sola vez, cuota por capítulo/tipo/dificultad, reserva ciega, identidad única y ausencia de duplicado textual normalizado. Las falsas registran el detalle alterado y la corrección; completar conserva contexto; la selección contextual explica por qué cada distractor pertenece a otra unidad de la fuente.

## Cobertura reforzada

- Daniel 7, 8, 9 y 11 reciben las cuotas más altas; Daniel 11 es el capítulo de mayor tamaño.
- Daniel 1–6 conserva cobertura de todos sus versículos y escenas.
- PR43 mantiene menos de 35 % de su cuota en páginas 47–49 por selección estratificada de unidades; páginas 52–54 permanecen incluidas.
- PR44 mantiene menos de 45 % de su cuota en páginas 55–57; páginas 58–59 permanecen incluidas.

## Límite editorial

El banco se detiene en 14,000 preguntas estáticas porque las siguientes variantes disponibles repetirían la misma capacidad con cambios superficiales de enunciado. La expansión adicional queda en el motor dinámico de distractores y barajado, sin declarar nuevas preguntas estáticas como hechos distintos.
