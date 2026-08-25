# V4 — Banco Curado

## Propósito

Crear un banco amplio y apto para estudiar a partir de las 3,558 preguntas del Banco Maestro, sin modificar ni ocultar el archivo fuente. V4 será la opción recomendada para cobertura amplia; V3 seguirá siendo la preparación intensiva de cuatro días y V2 quedará disponible como fuente técnica auditable.

## Objetivos

- Clasificar cada pregunta maestra como `APPROVED`, `REPAIRED` o `REJECTED`.
- Reparar automáticamente sólo defectos deterministas y trazables.
- Rechazar toda pregunta con respuesta discutible, ambigüedad estructural o corrección no resoluble.
- Conservar identidad, fuente, capítulo, hechos y vínculo con `QUESTION_ID`.
- Evitar que variantes de la misma familia aparezcan demasiado cerca.
- Producir reportes JSON y Markdown con todas las decisiones y sus motivos.
- Mantener V2 intacto y fuera de las prácticas mixtas normales.

## No objetivos

- No sobrescribir `Banco_Maestro_CB2026.json`.
- No inventar respuestas, citas, hechos o explicaciones no sustentadas.
- No presentar una reparación automática como verificación bíblica independiente.
- No eliminar V1, V2 o V3.
- No migrar silenciosamente el progreso histórico de V2 a V4; ambos perfiles conservarán estadísticas separadas.

## Alternativas consideradas

### 1. Capa V4 independiente — elegida

Genera archivos nuevos y un reporte de curación. Conserva V2 como evidencia y permite regenerar V4 de forma determinista.

### 2. Limpiar V2 durante la carga

Reduce archivos, pero mezcla la fuente con su presentación, dificulta auditar reparaciones y vuelve inestable el progreso existente.

### 3. Ocultar V2 y usar sólo V3

Elimina las rarezas visibles, pero deja fuera demasiados hechos y no resuelve la calidad del corpus amplio.

## Arquitectura

El flujo tendrá cuatro unidades independientes:

1. `master-curation-policy`: inspecciona una pregunta maestra y produce estado, códigos y evidencia.
2. `master-question-repair`: aplica únicamente transformaciones permitidas y devuelve una pregunta normalizada.
3. `build-curated-v4`: recorre las 3,558 preguntas, valida el resultado completo y escribe los bancos sólo si no existen bloqueadores.
4. `audit-curated-v4`: vuelve a cruzar V4 con el Banco Maestro y genera reportes para revisión humana y automatizada.

El generador será determinista: el mismo Banco Maestro y la misma política deben producir exactamente los mismos JSON, excepto la fecha del reporte.

## Estados de curación

### `APPROVED`

La pregunta se puede adaptar sin cambiar contenido y no activa ninguna regla de reparación o rechazo.

### `REPAIRED`

El hecho y la respuesta son resolubles, pero se aplica al menos una transformación permitida. Cada cambio queda registrado en `curationIssues` y en el reporte.

### `REJECTED`

La pregunta no entra en V4. Permanece en V2 y aparece en el reporte con sus razones. Ningún rechazo se descarta silenciosamente.

## Reglas de rechazo

Una pregunta se rechaza si cumple cualquiera de estas condiciones:

- Falta `QUESTION_ID`, material, capítulo, pregunta, respuesta o fuente.
- Está fuera de Daniel 1–12 o Profetas y Reyes 39–44.
- El material declarado contradice la fuente o el capítulo.
- Una selección múltiple no permite determinar una única opción correcta.
- Hay opciones duplicadas después de normalizar texto.
- La respuesta contiene una nota no resuelta como “requiere corrección”, “respuesta discutible” o equivalente.
- `historical_status` indica corrección, pero la forma canónica no puede extraerse de forma inequívoca.
- La pregunta contradice su respuesta, sus hechos asociados o su referencia.
- No existe ningún `FULL_FACT_ID`, `PARTIAL_FACT_ID`, `INCIDENTAL_FACT_ID`, `duplicate_group` ni identificador utilizable como familia.

Las reglas de rechazo tienen prioridad sobre las reparaciones.

## Reparaciones permitidas

Las reparaciones nunca cambian el hecho evaluado:

- Sustituir encabezados técnicos como “segunda formulación de alto riesgo” por lenguaje natural.
- Eliminar prefijos editoriales redundantes como `[Profetas y Reyes]`.
- Sustituir explicaciones sobre fases, cobertura o auditoría por una explicación prudente basada en `fact_support` o, si no existe, por “La respuesta se confirma en <fuente>”.
- Balancear puntuación y comillas sin alterar las palabras del enunciado.
- Convertir `RESPUESTA CORTA` o una pregunta canónica sin espacio en `reference_detail` con `answerMode: canonical_text`, en vez de presentarla falsamente como completar.
- Aplicar una corrección histórica sólo cuando el Banco Maestro declara explícitamente la forma exacta corregida.
- Quitar prefijos `A)`, `B)`, `C)` o `D)` de los textos visibles, conservando el identificador de opción.
- Normalizar espacios, puntos finales y variantes tipográficas sin cambiar palabras significativas.

## Familias y variantes

La familia se determina en este orden:

1. Primer `FULL_FACT_ID`.
2. Primer `PARTIAL_FACT_ID`.
3. Primer `INCIDENTAL_FACT_ID`.
4. `duplicate_group`.
5. `QUESTION_ID` como último recurso válido.

`factKeys` conservará todos los identificadores de hechos disponibles. `duplicate_group` se guardará en metadata aunque no sea la familia principal.

V4 no eliminará automáticamente variantes válidas sólo por compartir grupo. El selector existente las espaciará mediante `factKey`; el auditor señalará duplicados textuales exactos como bloqueadores.

## Modelo de salida

Se generarán dos bancos de sólo lectura:

- `public/banks/v4_daniel.json`
- `public/banks/v4_profetas_reyes.json`

Cada pregunta incluirá:

- `id`: el `QUESTION_ID` original con prefijo V4 estable.
- `bankProfileId`: `curated-v4` al cargarse.
- `factKey` y `factKeys`.
- pregunta, opciones, respuesta, explicación y fuente curadas.
- `metadata.masterQuestionId`.
- `metadata.curationStatus`.
- `metadata.curationIssues`.
- `metadata.originalDifficulty`, `originalType`, `duplicateGroup` y estados QC relevantes.

Los rechazados no se incluyen en los bancos, pero sí en los reportes.

## Reportes

Se crearán:

- `reports/curated-v4-audit.json`
- `reports/curated-v4-audit.md`

El resumen mostrará total analizado, aprobado, reparado y rechazado; distribución por fuente, capítulo, tipo y dificultad; conteo por código; y una entrada por pregunta reparada o rechazada.

El reporte JSON conservará texto original y texto final para reparaciones. El Markdown mostrará una síntesis y los rechazos completos, sin duplicar miles de reparaciones idénticas en la sección principal.

## Escritura segura

El generador construirá y validará todo en memoria. Sólo reemplazará los archivos V4 cuando:

- las 3,558 entradas hayan recibido un estado;
- `APPROVED + REPAIRED + REJECTED = 3,558`;
- no haya IDs repetidos en V4;
- todas las respuestas V4 sean resolubles;
- todas las referencias y capítulos coincidan con el maestro;
- no quede lenguaje administrativo, comillas desbalanceadas ni notas de corrección;
- el auditor termine sin bloqueadores.

Si falla una condición, el proceso sale con error y conserva los últimos archivos V4 válidos.

## Integración con la aplicación

- Se añade `curated-v4` a `BankProfileId` y `BankSelection`.
- V4 aparece como “V4 — Banco Curado” y “Recomendado para cobertura amplia”.
- V3 aparece como “Preparación intensiva de 4 días”.
- V2 aparece como “Fuente técnica · puede contener redacción de auditoría”.
- En instalaciones nuevas, V4 será la selección predeterminada cuando esté disponible.
- Preferencias existentes se conservan; no se cambia silenciosamente la selección guardada.
- “Mixto curado” combina V1 + V3 + V4 y excluye V2.
- V2 se puede seleccionar expresamente desde Banco de preguntas o el selector avanzado.
- Los bancos V4 son integrados, regenerables y de sólo lectura.
- Estadísticas, respaldo, recarga y ciclos de cobertura deben aceptar el nuevo perfil.

## Progreso y compatibilidad

V4 utiliza IDs de banco propios, por lo que su progreso se mide por separado de V2. El respaldo incluirá V4 y seguirá aceptando respaldos anteriores sin ese perfil. La migración añadirá valores predeterminados cuando una preferencia antigua no conozca `curated-v4`.

No se copiarán aciertos de V2 a V4 automáticamente: una pregunta reparada puede exigir una respuesta distinta de la que el usuario vio en V2.

## Interfaz de auditoría

Banco de preguntas mostrará una tarjeta V4 con:

- preguntas utilizables;
- aprobadas y reparadas;
- rechazadas;
- fecha o huella de generación;
- enlace para descargar el reporte JSON/Markdown cuando el entorno lo permita.

Las preguntas V4 reparadas no mostrarán etiquetas técnicas durante la práctica. Sus códigos de curación permanecerán disponibles en Revisar preguntas y exportaciones.

## Pruebas

### Unitarias

- Una pregunta limpia queda `APPROVED` sin cambios semánticos.
- Cada regla permitida produce `REPAIRED` con su código.
- Cada regla no resoluble produce `REJECTED`.
- Las correcciones históricas explícitas se aplican; las ambiguas se rechazan.
- Las respuestas de opción se resuelven exactamente una vez.
- Las preguntas canónicas usan texto canónico y tipo adecuado.
- La familia respeta el orden definido.
- El generador es determinista.
- La suma de estados siempre coincide con la entrada.

### Auditoría completa

- Procesa las 3,558 preguntas reales.
- Verifica trazabilidad individual y capítulos.
- Exige cero bloqueadores en la salida V4.
- Confirma que el Banco Maestro no cambió.

### E2E

- V4 aparece y queda recomendado en una instalación nueva.
- Una ronda V4 no presenta lenguaje técnico ni notas de corrección.
- Mixto curado no selecciona preguntas de V2.
- Aprender, Repaso inteligente, Simulacro y recarga funcionan con V4.
- Respaldo y restauración conservan la selección V4.

## Criterios de aceptación

1. Todas las preguntas maestras reciben exactamente un estado.
2. V4 contiene sólo preguntas aprobadas o reparadas.
3. El reporte enumera todos los rechazos y reparaciones.
4. La auditoría V4 termina con cero bloqueadores.
5. No queda lenguaje de generación, explicación administrativa, corrección pendiente ni puntuación desbalanceada en V4.
6. Las respuestas, hechos y referencias reparables conservan trazabilidad al maestro.
7. V2 permanece byte por byte sin cambios.
8. La aplicación carga V1, V2, V3 y V4 sin perder respaldos anteriores.
9. Mixto curado excluye V2.
10. Pruebas unitarias, E2E, lint, tipos y build terminan correctamente.

## Riesgos

- Algunas preguntas históricas pueden ser formalmente válidas pero pedagógicamente débiles. Permanecerán reparadas o aprobadas sólo si la respuesta es inequívoca; el reporte permitirá endurecer la política después.
- La cantidad final de V4 no se fija por anticipado. Se informará después de ejecutar la política; forzar una cuota podría aceptar preguntas defectuosas.
- La primera carga será mayor que V3. Los archivos se dividen por obra y se reutiliza IndexedDB para evitar reprocesarlos en cada navegación.

