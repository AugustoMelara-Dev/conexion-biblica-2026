# Análisis AAH de rendimiento - Augusto Melara

## Alcance y autoridad

Este artefacto analiza únicamente el reporte secundario de rendimiento de AAH para priorizar recuperación. No es fuente editorial: no resuelve preguntas, no valida citas bíblicas y no modifica bancos. La lista de unidades personales procede del spec adjunto y solo se cruza contra lo visible en el reporte.

Reporte: C:\Users\melar\Downloads\cxb-final-conexion-biblica-aah-2026_augusto-melara_reporte.pdf

SHA-256 del reporte: C6364ADA30789393732BFFDBB64AFE89F5B07709546A17AEEDE7D93F179261A7

Extracción: pypdf 6.14.2 + pdfplumber 0.11.10; Both extractors found 26 pages and 100 question headers.

## Resultado ejecutivo

- **98/100 correctas (98%)**, 2 incorrectas; puntaje reportado **94,480**.
- Tiempo reportado: **3.72 s promedio**, **06:11.787** total; suma de los 100 tiempos: **371.787 s** (3.71787 s promedio).
- Ronda 4 es el cuello de botella: **5.119 s** promedio, 8/20 sobre 5 s y 5/20 sobre 6 s.
- El bloque Daniel 9 es el más lento del mapeo: **6.262 s** promedio y el único capítulo con error; Daniel 8 sigue con **5.505 s**.
- Las dos fallas son tardías y caen en unidades personales: Daniel 9 (12.799 s) y Daniel 12 (6.981 s).

## Priorización operativa

1. **P0 - DAN9 - secuencia posterior a las sesenta y dos semanas** (R4-Q19; p.20): Error explícito y máxima latencia del reporte: 12.799 s. P0 de recuperación inmediata; revisar con contraste de orden y nueva verificación Sol antes de promoción.
2. **P0 - DAN12 - identidad de Miguel como gran príncipe** (R5-Q14; p.24): Error explícito (6.981 s) y confusión con Mesías Príncipe de Daniel 9. P0 de recuperación inmediata; contrastar Daniel 9/12 y volver a verificar Sol antes de promoción.
3. **P1 - DAN9 - frase temporal y llegada de Gabriel** (R4-Q20, R4-Q17; p.20, p.21): Dos correctas lentas: 11.285 s y 5.762 s; el bloque D9 encabeza la media por capítulo. Practicar secuencia y señales temporales; registrar como duda inferida, no como auto-reporte.
4. **P1 - DAN8 - localización y correspondencias del carnero/macho cabrío** (R4-Q8, R4-Q9, R4-Q13; p.18, p.19): Máxima latencia correcta de D8 (9.029 s) y otras dos sobre 5 s. Repasar nombres propios y relaciones de interpretación en presentaciones distintas.
5. **P2 - DAN10 y DAN7 - cronología/actores** (R5-Q1, R4-Q6, R4-Q4; p.17, p.18, p.22): Tiempos altos de 7.826 s, 7.474 s y 5.817 s, todos correctos. Usar recuperación espaciada; no convertir latencia en rechazo factual.
6. **P2 - DAN5 y PR no etiquetado por capítulo** (R3-Q3, R3-Q14, R1-Q15, R2-Q17; p.5, p.10, p.12, p.14): Tekel (6.666 s), PR conversión (6.049 s) y dos ítems PR sobre 5 s. Añadir vigilancia y mapeo posterior; el reporte no autoriza cambios editoriales.

La prioridad es de estudio/recuperación y no implica rechazar una pregunta correcta ni promover contenido sin auditoría V18.

## Errores explícitos

| Ref.               | Capítulo |   Tiempo | Evidencia reportada                                              | Lectura para priorización                                                                                       |
| ------------------ | -------- | -------: | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| R4-Q19 (índice 79) | DAN9     | 12.799 s | PDF p.20 / pie p.19: A correcta en verde; B seleccionada en rojo | Confusión entre la reconstrucción asociada al tramo anterior y el evento posterior a las sesenta y dos semanas. |
| R5-Q14 (índice 94) | DAN12    |  6.981 s | PDF p.24 / pie p.23: A correcta en verde; D seleccionada en rojo | Confusión de identidad entre Miguel (Daniel 12) y Mesías Príncipe (Daniel 9).                                   |

No hay otros errores explícitos en el reporte.

## Ítems lentos (>6 s)

| Ref.   | Capítulo       |   Tiempo | Estado     | Tema resumido                                                   |   Página |
| ------ | -------------- | -------: | ---------- | --------------------------------------------------------------- | -------: |
| R4-Q19 | DAN9           | 12.799 s | incorrecta | qué ocurre después de las sesenta y dos semanas                 | PDF p.20 |
| R4-Q20 | DAN9           | 11.285 s | correcta   | frase de Gabriel sobre ser muy amado al principio de los ruegos | PDF p.21 |
| R4-Q8  | DAN8           |  9.029 s | correcta   | ubicación de Daniel: Susa y río Ulai                            | PDF p.18 |
| R5-Q1  | DAN10          |  7.826 s | correcta   | tercer año de Ciro                                              | PDF p.22 |
| R4-Q6  | DAN7           |  7.474 s | correcta   | dominio, gloria y reino dados a uno como hijo de hombre         | PDF p.18 |
| R5-Q14 | DAN12          |  6.981 s | incorrecta | identidad del gran príncipe que está de parte del pueblo        | PDF p.24 |
| R3-Q3  | DAN5           |  6.666 s | correcta   | significado de Tekel                                            | PDF p.12 |
| R4-Q13 | DAN8           |  6.408 s | correcta   | macho cabrío como rey de Grecia                                 | PDF p.19 |
| R3-Q14 | PR_UNSPECIFIED |  6.049 s | correcta   | Belsasar desatiende la conversión y curación milagrosa (PR)     | PDF p.14 |

Siete de estos nueve ítems fueron correctos: la latencia es una señal de práctica, no evidencia suficiente para descartar contenido.

## Banda de vigilancia (5-6 s)

- R4-Q4 - DAN7, 5.817 s, tres cuernos arrancados por el cuerno pequeño; PDF p.17.
- R4-Q17 - DAN9, 5.762 s, Gabriel llega mientras Daniel ora para dar sabiduría y entendimiento; PDF p.20.
- R4-Q9 - DAN8, 5.727 s, dos cuernos del carnero; PDF p.18.
- R2-Q17 - PR_UNSPECIFIED, 5.615 s, sabios celosos denuncian a los compañeros de Daniel (PR); PDF p.10.
- R1-Q15 - PR_UNSPECIFIED, 5.594 s, gracia y buena voluntad con el príncipe de los eunucos (PR); PDF p.5.
- R5-Q10 - DAN11, 5.401 s, abominación desoladora en el santuario; PDF p.24.
- R5-Q9 - DAN11, 5.354 s, contienda entre rey del sur y rey del norte; PDF p.23.
- R5-Q5 - DAN10, 5.275 s, príncipe de Persia y veintiún días; PDF p.23.
- R5-Q12 - DAN11, 5.228 s, dios de las fortalezas; PDF p.24.
- R1-Q11 - DAN2, 5.149 s, solicitud de tiempo ante el rey para orar y pedir la interpretación; PDF p.4.
- R2-Q6 - DAN4, 5.144 s, segundo sueño: árbol grande y copa que llega al cielo; PDF p.8.

## Rendimiento por ronda

| Ronda |   N | Correctas | Incorrectas |   Media | Mediana | >5 s | >6 s |     Total | Evidencia |
| ----- | --: | --------: | ----------: | ------: | ------: | ---: | ---: | --------: | --------- |
| 1     |  20 |        20 |           0 | 3.165 s | 2.974 s |    2 |    0 |  63.309 s | PDF p.2   |
| 2     |  20 |        20 |           0 | 3.282 s | 3.088 s |    2 |    0 |  65.632 s | PDF p.7   |
| 3     |  20 |        20 |           0 | 3.038 s | 2.572 s |    2 |    2 |  60.758 s | PDF p.12  |
| 4     |  20 |        19 |           1 | 5.119 s | 4.537 s |    8 |    5 | 102.382 s | PDF p.17  |
| 5     |  20 |        19 |           1 | 3.985 s | 3.958 s |    6 |    2 |  79.706 s | PDF p.22  |

## Rendimiento por capítulo/bloque

El mapeo Daniel se hizo por contenido y secuencia del reporte. Las preguntas PR se dejan como PR_UNSPECIFIED porque el reporte no expone PR39-PR44.

| Bloque         |   N | Correctas | Incorrectas |   Media |     Máx. | >6 s | Páginas                                                 |
| -------------- | --: | --------: | ----------: | ------: | -------: | ---: | ------------------------------------------------------- |
| DAN1           |   7 |         7 |           0 | 2.802 s |  3.935 s |    0 | p.2, p.3                                                |
| DAN2           |   7 |         7 |           0 | 2.897 s |  5.149 s |    0 | p.3, p.4                                                |
| DAN3           |   5 |         5 |           0 | 3.003 s |  3.963 s |    0 | p.7, p.8                                                |
| DAN4           |   5 |         5 |           0 | 2.716 s |  5.144 s |    0 | p.8, p.9                                                |
| DAN5           |   4 |         4 |           0 | 3.102 s |  6.666 s |    1 | p.12                                                    |
| DAN6           |   4 |         4 |           0 | 2.226 s |  3.323 s |    0 | p.13                                                    |
| DAN7           |   7 |         7 |           0 | 3.753 s |  7.474 s |    1 | p.17, p.18                                              |
| DAN8           |   7 |         7 |           0 | 5.505 s |  9.029 s |    2 | p.18, p.19                                              |
| DAN9           |   6 |         5 |           1 | 6.262 s | 12.799 s |    2 | p.20, p.21                                              |
| DAN10          |   6 |         6 |           0 | 4.280 s |  7.826 s |    1 | p.22, p.23                                              |
| DAN11          |   7 |         7 |           0 | 4.116 s |  5.401 s |    0 | p.23, p.24                                              |
| DAN12          |   6 |         5 |           1 | 3.491 s |  6.981 s |    1 | p.24, p.25                                              |
| PR_UNSPECIFIED |  29 |        29 |           0 | 3.592 s |  6.049 s |    1 | p.5, p.6, p.9, p.10, p.11, p.13, p.14, p.15, p.16, p.26 |

## Unidades personales obligatorias

Estas unidades vienen del spec, no del reporte. OBSERVED_OPTION_ONLY significa que el término apareció solo como alternativa; NOT_OBSERVED_IN_SAMPLE significa que no aparece explícitamente en las 100 preguntas visibles.

| Bloque  | Unidad                               | Estado en el reporte         | Ref.                                          |               Página |
| ------- | ------------------------------------ | ---------------------------- | --------------------------------------------- | -------------------: |
| DAN7    | Anciano de días                      | observed direct              | R4-Q5                                         |                 p.18 |
| DAN7    | hijo de hombre                       | observed direct              | R4-Q6                                         |                 p.18 |
| DAN7    | dominio, gloria y reino              | observed direct              | R4-Q6                                         |                 p.18 |
| DAN7    | cuatro bestias                       | observed direct              | R4-Q1, R4-Q7                                  |           p.17, p.18 |
| DAN7    | cuernos                              | observed direct              | R4-Q3, R4-Q4                                  |                 p.17 |
| DAN7    | juicio                               | not observed in sample       | -                                             |                    - |
| DAN8    | Susa                                 | observed direct              | R4-Q8                                         |                 p.18 |
| DAN8    | río Ulai                             | observed direct              | R4-Q8                                         |                 p.18 |
| DAN8    | carnero                              | observed direct              | R4-Q8, R4-Q9, R4-Q12                          |           p.18, p.19 |
| DAN8    | macho cabrío                         | observed direct              | R4-Q8, R4-Q10, R4-Q11, R4-Q12, R4-Q13, R4-Q14 |           p.18, p.19 |
| DAN8    | Media y Persia                       | observed direct              | R4-Q12                                        |                 p.19 |
| DAN8    | Grecia                               | observed direct              | R4-Q13                                        |                 p.19 |
| DAN8    | Gabriel                              | observed direct              | R4-Q14                                        |                 p.19 |
| DAN9    | setenta años                         | observed direct              | R4-Q15                                        |                 p.20 |
| DAN9    | setenta semanas                      | observed direct              | R4-Q18                                        |                 p.20 |
| DAN9    | siete semanas                        | observed option only         | R4-Q18                                        |                 p.20 |
| DAN9    | sesenta y dos semanas                | observed direct              | R4-Q18, R4-Q19                                |                 p.20 |
| DAN9    | reconstrucción                       | observed option only         | R4-Q19                                        |                 p.20 |
| DAN9    | Mesías Príncipe                      | observed partial option only | R4-Q19, R5-Q14                                |           p.20, p.24 |
| DAN9    | después de las sesenta y dos semanas | observed direct error        | R4-Q19                                        |                 p.20 |
| DAN9    | pacto                                | not observed in sample       | -                                             |                    - |
| DAN9    | ciudad y santuario                   | not observed in sample       | -                                             |                    - |
| DAN10   | tercer año de Ciro                   | observed direct slow         | R5-Q1                                         |                 p.22 |
| DAN10   | tres semanas                         | observed direct              | R5-Q2                                         |                 p.22 |
| DAN10   | Hidekel                              | observed direct              | R5-Q3                                         |                 p.22 |
| DAN10   | príncipe de Persia                   | observed direct              | R5-Q5, R5-Q6                                  |                 p.23 |
| DAN10   | veintiún días                        | observed direct              | R5-Q5                                         |                 p.23 |
| DAN10   | Miguel                               | observed direct              | R5-Q6                                         |                 p.23 |
| DAN10   | varón vestido de lino                | observed direct              | R5-Q3, R5-Q4                                  |                 p.22 |
| DAN11   | norte y sur                          | observed direct              | R5-Q9                                         |                 p.23 |
| DAN11   | secuencias                           | observed partial             | R5-Q7, R5-Q8, R5-Q9                           |                 p.23 |
| DAN11   | santuario                            | observed direct slow         | R5-Q10                                        |                 p.24 |
| DAN11   | abominación desoladora               | observed direct              | R5-Q10                                        |                 p.24 |
| DAN11   | lisonjas                             | not observed in sample       | -                                             |                    - |
| DAN11   | dios de las fortalezas               | observed direct              | R5-Q12                                        |                 p.24 |
| DAN11   | monte glorioso                       | observed direct              | R5-Q13                                        |                 p.24 |
| DAN11   | direcciones y orden                  | observed partial             | R5-Q9, R5-Q13                                 |           p.23, p.24 |
| DAN12   | Miguel, el gran príncipe             | observed direct error        | R5-Q14                                        |                 p.24 |
| DAN12   | tiempo de angustia                   | not observed in sample       | -                                             |                    - |
| DAN12   | resurrección                         | observed direct              | R5-Q15                                        |                 p.25 |
| DAN12   | sellar el libro                      | observed direct              | R5-Q16                                        |                 p.25 |
| DAN12   | 1,290                                | observed direct              | R5-Q17                                        |                 p.25 |
| DAN12   | 1,335                                | observed option only         | R5-Q17                                        |                 p.25 |
| DAN12   | heredad de Daniel                    | observed direct              | R5-Q18                                        |                 p.25 |
| DAN5    | Mene                                 | observed option only         | R3-Q12                                        |                 p.14 |
| DAN5    | Tekel                                | observed direct slow         | R3-Q3                                         |                 p.12 |
| DAN5    | Peres                                | not observed in sample       | -                                             |                    - |
| DAN5    | recompensa                           | observed direct              | R3-Q16                                        |                 p.15 |
| DAN5    | caída de Belsasar                    | observed direct              | R3-Q4                                         |                 p.12 |
| PR39_44 | frases exactas                       | observed direct              | R1-Q15, R1-Q16, R2-Q12, R2-Q16, R3-Q14        |      p.5, p.10, p.14 |
| PR39_44 | quién dijo o hizo                    | observed direct              | R2-Q17, R3-Q13, R3-Q15                        |     p.10, p.14, p.15 |
| PR39_44 | por qué                              | observed direct              | R1-Q16, R2-Q16, R3-Q17                        |      p.5, p.10, p.15 |
| PR39_44 | qué ocurrió primero                  | observed direct              | R2-Q11, R2-Q13                                |                  p.9 |
| PR39_44 | propósito                            | observed direct              | R2-Q16                                        |                 p.10 |
| PR39_44 | consecuencia                         | observed direct              | R2-Q19                                        |                 p.10 |
| PR39_44 | detalles exclusivos de PR            | observed direct              | R1-Q15, R2-Q11, R3-Q9, R5-Q20                 | p.5, p.9, p.13, p.26 |
| PR39_44 | diferencias entre los seis capítulos | partial no pr chapter label  | R1-Q15, R2-Q11, R3-Q9, R5-Q20                 | p.5, p.9, p.13, p.26 |

## Patrones y límites

- 2/2 errores están en rondas 4-5; rondas 1-3 quedaron 60/60.
- Hay cola larga: 20/100 sobre 5 s, 9/100 sobre 6 s, 3/100 sobre 8 s y 2/100 sobre 10 s.
- La interferencia Daniel 9/12 es una hipótesis útil para priorización, no un diagnóstico causal.
- El reporte no ofrece dudas declaradas, confianza, segunda opción ni capítulo PR; los tiempos lentos son proxies.
- Se renderizaron las 26 páginas; se verificaron visualmente portada/resumen y páginas con lentitud/errores (PDF pp. 1, 12, 14, 18, 20, 21, 22 y 24). Poppler avisó de fuentes ausentes, pero las páginas relevantes fueron legibles.
- No se hicieron cambios en bancos, contenido editorial ni producción.

## Verificación reproducible

- pdfinfo sobre el reporte -> 26 páginas.
- pypdf 6.14.2 y pdfplumber 0.11.10 -> 26 páginas y 100 cabeceras de pregunta.
- pdftoppm -png -r 120 -f 1 -l 26 -> 26 PNG renderizados; spot-check visual de páginas indicadas.
