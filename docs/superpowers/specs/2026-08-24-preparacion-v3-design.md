# Preparación Conexión Bíblica 2026 - diseño V3

## Objetivo

Convertir la aplicación offline en un entrenador de dominio para Jóvenes 2026 sobre Daniel 1-12 (RVR95) y Profetas y Reyes 39-44. La práctica debe mejorar precisión, comprensión y velocidad sin castigar la repetición usada para aprender.

## Banco curado de 500 preguntas

El perfil `prep-v3` contendrá exactamente 500 preguntas nuevas y verificables:

- 336 de Daniel: 28 por cada capítulo del 1 al 12.
- 162 de Profetas y Reyes: 27 por cada capítulo del 39 al 44.
- 2 integradoras, marcadas con `integrative: true` y excluidas de los conteos de cuota por capítulo.

Cada registro tendrá identificador único, `factKey`, referencia, explicación, razón de trampa, pista de memoria y estado de verificación. Las familias reutilizarán `factKey` para presentar un mismo conocimiento con redacciones y habilidades distintas: detalle directo, causa-efecto, cronología, comparación, referencia, personajes, símbolos, números y contraste hipotético. Una familia no podrá contener duplicados exactos y sus variantes no podrán tener respuestas contradictorias.

El material fuente será exclusivamente el PDF local, el Banco Maestro y los bancos RVR95 locales. Un validador automatizado comprobará el conteo total y por capítulo, IDs, esquema, opciones, una sola respuesta válida cuando corresponda, referencias, campos pedagógicos, duplicados textuales, similitud excesiva y distractores repetidos u obviamente inválidos. La revisión automatizada no sustituye la trazabilidad: cada pregunta conservará su referencia y su familia.

## Tres experiencias de entrenamiento

### Aprender

Usa feedback inmediato, respuesta correcta, explicación, referencia y pista de memoria. Una respuesta fallida puede reaparecer después de un intervalo, preferiblemente con otra variante de la misma familia. Repetir una sesión de aprendizaje actualiza el dominio, pero no crea ni reduce resultados de simulacro.

### Repaso inteligente

Prioriza familias débiles combinando errores, dominio, lentitud y antigüedad. Evita repetir literalmente una pregunta mientras queden variantes elegibles de su `factKey`, y evita familias o capítulos consecutivos cuando el conjunto lo permita. El selector será puro y determinista con semilla para poder probarlo.

### Simulacro

Usa temporizador, feedback diferido y una mezcla de dificultad semejante al concurso. Sus sesiones y resultados se identifican como `simulation`; las métricas competitivas sólo se calculan con esas sesiones. Las prácticas de Aprender y Repaso inteligente siguen alimentando dominio, pero nunca alteran precisión, puntuación ni récords de simulacro.

## Persistencia y compatibilidad

La identidad persistente seguirá siendo `bankId:questionId`. Las variantes se relacionarán por `factKey` sin fusionar sus historiales individuales. Los intentos nuevos guardarán el contexto `practice` o `simulation`; los respaldos antiguos se aceptarán y sus intentos sin contexto se tratarán como práctica. V1, V2, Mixto, el plan de cuatro días y los bloques secuenciales seguirán disponibles.

## Interfaz

El generador mostrará tres accesos principales: Aprender, Repaso inteligente y Simulacro. Aprender y Repaso inteligente explicarán que no afectan el resultado competitivo. Durante feedback inmediato se mostrará la pista; en Simulacro se ocultará hasta finalizar. Resultados y estadísticas identificarán claramente si una ronda fue práctica o simulacro.

## Verificación

El desarrollo seguirá ciclos TDD. Las pruebas cubrirán contrato y contenido del banco, diversidad y familias, agotamiento de variantes, prioridad adaptativa, feedback por modo, clasificación de intentos, separación de estadísticas, compatibilidad de respaldos y selección de bloques. La entrega requiere pruebas completas, lint, typecheck, build y recorrido real en la interfaz de los tres modos, incluida una recarga durante una ronda.
