# Auditoría de bancos maestros

Fuente única: `MaterialConexionBiblica (1).pdf` (SHA-256 `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`).

## Resultado general

- Banco PR39–44: 1,000 preguntas verificadas.
- Banco Daniel 7–12: 1,000 preguntas verificadas.
- Todas las preguntas tienen una respuesta única por construcción: una opción reproduce el detalle extraído y las demás alteran ese mismo espacio.
- Ninguna pregunta usa datos históricos, doctrinales o textuales externos al PDF.
- Estado final: cero preguntas no verificadas, cero IDs duplicados y cero citas vacías.

## PR39–44

- Candidatos generados: 1250.
- Seleccionados: 1000.
- Candidatos rechazados: 250.
- Duplicados/variantes superficiales eliminados: 250.
- Hechos atómicos únicos: 625.
- Por capítulo: `{"PR39": 150, "PR40": 140, "PR41": 140, "PR42": 120, "PR43": 250, "PR44": 200}`.
- Por tipo: `{"multiple_choice": 350, "fill_blank": 350, "true_false": 300}`.
- Por dificultad: `{"hard": 450, "medium": 250, "expert": 200, "easy": 100}`.
- Verdadero/Falso: `{"Verdadero": 150, "Falso": 150}`.
- Respuestas A/B/C/D en selección múltiple: `{"A": 88, "B": 88, "C": 87, "D": 87}`.

## Daniel 7–12

- Candidatos generados: 1250.
- Seleccionados: 1000.
- Candidatos rechazados: 250.
- Duplicados/variantes superficiales eliminados: 250.
- Hechos atómicos únicos: 650.
- Por capítulo: `{"DAN10": 100, "DAN11": 240, "DAN12": 100, "DAN7": 190, "DAN8": 190, "DAN9": 180}`.
- Por tipo: `{"fill_blank": 350, "multiple_choice": 350, "true_false": 300}`.
- Por dificultad: `{"easy": 100, "expert": 200, "hard": 450, "medium": 250}`.
- Verdadero/Falso: `{"Falso": 150, "Verdadero": 150}`.
- Respuestas A/B/C/D en selección múltiple: `{"A": 88, "B": 88, "C": 87, "D": 87}`.

## Segunda pasada competitiva

Se rechazaron las variantes adicionales de los hechos usados una sola vez para evitar repetición superficial. Las formulaciones finales incluyen fuente, escena temática y contexto textual; las falsas cambian un solo detalle y registran la corrección completa. Las opciones se validaron como distintas y la respuesta marcada coincide exactamente con una sola opción.

## Preguntas corregidas por ambigüedad

La generación no conserva pronombres aislados como pregunta: cada enunciado añade capítulo/versículo o página, tema y el contexto textual completo. Los candidatos que repetían el mismo hecho sin una capacidad distinta fueron descartados antes de la selección final.

Muestra registrada de correcciones aplicadas durante la segunda pasada:

- `PR39-0060`: se sustituyeron opciones de categorías mezcladas por sustantivos compatibles con el marco ‘su ___ de honrar a Dios’.
- `PR39-0132`: la comparación sobre Nadab y Abiú quedó limitada a un solo sustantivo femenino, con respaldo exacto.
- `PR43-0134`: los distractores de la forma verbal futura quedaron en la misma conjugación que la respuesta.
- `PR44-0104`: las alternativas posteriores a ‘fué’ quedaron como participios equivalentes.
- `DAN10-0079`: se eliminaron nombres propios que hacían a los distractores gramaticalmente imposibles.
- `DAN12-0022`: las cuatro alternativas quedaron como verbos en pasado, sin alterar el resto del enunciado.

## Cobertura crítica confirmada

- PR43 páginas 52–54: 80 preguntas.
- PR44 páginas 58–59: 60 preguntas.
- Daniel 7:19–27: cubierto mediante hechos de cada versículo y sus relaciones.
- Daniel 8:9–27: cubierto mediante hechos de cada versículo y sus relaciones.
- Daniel 9:1–19: 90 preguntas; Daniel 9:20–27: 90 preguntas.
- Daniel 11:21–35: 80 preguntas; Daniel 11:36–45: 40 preguntas.

## OCR y ortografía de fuente

El PDF contiene texto embebido Unicode y no produjo caracteres de reemplazo en las páginas objetivo. Se conservaron grafías históricas visibles de Profetas y Reyes (por ejemplo, formas acentuadas según la edición) y se eliminaron únicamente encabezados, pies de página y saltos de línea de maquetación. No se modernizó el lenguaje.
