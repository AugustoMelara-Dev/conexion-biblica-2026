# Piloto competitivo V11 — 100 preguntas

Fecha de cierre: 2026-08-30

## Resultado

El piloto añade 100 conocimientos nuevos y 100 preguntas centrales: 40 de Daniel 7 y 60 de PR43. La prosa fue redactada directamente por IA desde los paquetes fuente; el código únicamente enriqueció citas, validó, calculó hashes, equilibró posiciones y compiló los archivos de unidad.

| Familia | Cantidad |
|---|---:|
| Selección | 45 |
| Completar | 30 |
| Verdadero/Falso | 25 |
| **Total** | **100** |

Las V/F quedaron equilibradas en 12 verdaderas y 13 falsas. Las posiciones correctas también quedaron equilibradas: selección 12/11/11/11 y completar 8/8/7/7.

La dificultad declarada es 29 fáciles, 53 medias y 18 difíciles. Las habilidades cubiertas incluyen recuerdo factual, causa y consecuencia, comparación, secuencia narrativa, identificación, símbolos, detalles proféticos, principios y hablante/destinatario.

## Auditoría

- 100 de 100 preguntas pasan el contrato estructural y de evidencia.
- 100 de 100 tienen revisión semántica enlazada al hash vigente.
- 100 `fact_id` distintos; no se infló el piloto con variantes automáticas.
- Cero prompts exactos o normalizados duplicados.
- Cero muletas de página, párrafo, capítulo o referencia.
- Cero falsedades trasladadas desde otro pasaje.
- Cada V/F falsa cambia un solo dato local declarado.
- Cero revisiones vencidas y cero preguntas sin revisión.
- Auditoría global después del piloto: 1,375 preguntas, 1,124 hechos, cero bloqueos.

La revisión fue realizada por IA en el flujo en línea y no se presenta como revisión humana ni como una segunda IA independiente. Se hizo una segunda pasada semántica y adversarial sobre respuesta, distractores, pistas y dificultad. Tres V/F se reescribieron como proposiciones verdaderas para corregir el desequilibrio 9/16 inicial; las opciones de selección y completar se reordenaron mecánicamente para eliminar el sesgo de posición. Ninguna pregunta rechazada permanece en el corpus.

## Veinte ejemplos estratificados

| ID | Tipo | Habilidad | Enunciado abreviado |
|---|---|---|---|
| DAN7-V11-PILOT-001 | Selección | Tiempo | Año del reinado de Belsasar en que Daniel recibió el sueño |
| DAN7-V11-PILOT-003 | Selección | Secuencia | Transformación posterior al arranque de las alas |
| DAN7-V11-PILOT-009 | Selección | Comparación | Comparación del cabello del Anciano de días |
| DAN7-V11-PILOT-021 | Selección | Comparación | Multitud que estaba delante del Juez |
| DAN7-V11-PILOT-027 | Selección | Detalle profético | Dos cosas que el poder pensaría cambiar |
| DAN7-V11-PILOT-012 | Completar | Escenario | Lugar donde combatían los cuatro vientos |
| DAN7-V11-PILOT-030 | Completar | Imagen profética | Sustancia del río que salía del Juez |
| DAN7-V11-PILOT-033 | Completar | Comparación | Aspecto del cuerno frente a sus compañeros |
| DAN7-V11-PILOT-037 | V/F | Duración | Permanencia del reino del hijo de hombre |
| DAN7-V11-PILOT-039 | V/F | Origen | Reino del que surgirían los diez reyes |
| PR43-V11-PILOT-003 | Selección | Causa | Defectos de Belsasar vinculados con la caída |
| PR43-V11-PILOT-009 | Selección | Identificación | Parentesco y función militar de Ciro |
| PR43-V11-PILOT-024 | Selección | Responsabilidad | Razón de la responsabilidad mayor de Belsasar |
| PR43-V11-PILOT-046 | Selección | Interpretación | Acciones divinas resumidas por MENE |
| PR43-V11-PILOT-048 | Selección | Causa | Maniobra que permitió entrar en Babilonia |
| PR43-V11-PILOT-031 | Completar | Reacción | Facultad moral despertada en Belsasar |
| PR43-V11-PILOT-052 | Completar | Recuerdo textual | Cuarta palabra de la inscripción |
| PR43-V11-PILOT-053 | Completar | Comparación | Imagen usada para la multitud de soldados |
| PR43-V11-PILOT-057 | V/F | Consecuencia | Honores recibidos por Daniel tras interpretar |
| PR43-V11-PILOT-059 | V/F | Simultaneidad | Relación temporal entre el banquete y la invasión |

## Regla fijada para las siguientes olas

Se mantiene el estándar del piloto: una pregunta nueva debe aportar un conocimiento distinto, tener respaldo local, conservar distractores homogéneos y plausibles, evitar pistas de posición o longitud, y superar tanto la validación contractual como una revisión semántica explícita. El volumen nunca justifica degradar estas reglas.
