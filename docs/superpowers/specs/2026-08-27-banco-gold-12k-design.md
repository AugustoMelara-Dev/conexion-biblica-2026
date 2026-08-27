# Banco GOLD 12K — Diseño

## Objetivo

Ampliar el Banco Maestro Único desde 8,000 hasta 12,000 preguntas útiles para competencia, basadas exclusivamente en `MaterialConexionBiblica (1).pdf`, sin reintroducir enunciados rotos, sustituciones absurdas ni preguntas sobre la ubicación física de una frase.

## Contrato del banco

- 3,000 hechos atómicos cubriendo las 1,029 unidades útiles del PDF.
- 12,000 preguntas GOLD: 3,000 completar, 3,000 verdadero/falso y 6,000 selección única.
- 600 fáciles, 2,400 medias, 5,400 difíciles y 3,600 expertas.
- Daniel 7, 8, 9 y 11, PR43 y PR44 conservan prioridad reforzada.
- Al menos 15 % de los hechos queda reservado para simulación ciega.
- Ninguna sesión normal repite `fact_id`.

## Arquitectura editorial

La generación tiene tres puertas independientes:

1. **Hechos:** extrae nombres, lugares, números, acciones, términos, expresiones y relaciones explícitas. Rechaza ventanas de palabras sin autonomía semántica y clasificaciones incompatibles con su contexto.
2. **Preguntas:** produce completar, selección directa y selección contextual para cada hecho. V/F se genera únicamente desde hechos con alteración cerrada y segura. Los hechos seguros pueden aportar una variante verdadera y otra falsa; no se fabrican falsedades mediante sustitución libre de sustantivos, adjetivos o expresiones.
3. **Auditor adversarial:** comprueba respaldo literal, respuesta única, contexto suficiente, gramática, ausencia de respuestas regaladas, duplicados, referencias válidas, balance y cuotas. Mantiene una lista explícita de patrones prohibidos y pares de sustitución rechazados.

## Aprendizaje

Las rondas de 100 mantienen 30 completar, 25 V/F y 45 selección única, con al menos 18 trampas contextuales. El selector prioriza hechos nunca vistos, recuperaciones vencidas, errores y respuestas lentas. Una corrección inmediata no cuenta como dominio.

## Verificación

- Pruebas TDD de los errores observados: huecos en V/F, sustituciones incoherentes, conjugaciones incompatibles, preguntas de página/párrafo y duplicados semánticos.
- Auditoría profunda de las 12,000 preguntas.
- Pruebas unitarias, integración, build y Playwright local.
- Despliegue Vercel, auditoría remota y Playwright en escritorio y móvil contra la URL pública.

## Criterio de parada

La cantidad final será exactamente 12,000. Si un candidato no supera todas las puertas, se reemplaza por otro hecho o variante; nunca se reduce una regla de calidad para alcanzar la cuota.
