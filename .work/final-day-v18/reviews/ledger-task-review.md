# Revisión Task 2 — ledger canónico V18

## Veredicto

- **SPEC: FAIL**
- **QUALITY: ISSUES**
- Clasificación: **IMPLEMENTED**, pero **no LOCALLY_VERIFIED como cumplimiento de Task 2**. La ejecución focal disponible pasa las invariantes que prueba, pero no prueba las obligaciones editoriales centrales del ledger.

El constructor es reproducible en el mismo checkout, verifica el SHA-256 canónico, cuenta 60 páginas y conserva correctamente los conteos nominales de 3.873 preguntas, 2.217 `fact_id` actuales y 2.606 FACT históricos. Sin embargo, el artefacto no cumple la unidad atómica solicitada y sus decisiones de cobertura reducen la semántica a la mera presencia de un `source_unit_id`. Esto invalida la cifra de 997 unidades `COVERED` como decisión de cobertura del PDF y alimentaría incorrectamente la autoría de Task 4.

## Findings

### Critical 1 — Las unidades de Daniel no son atómicas y la cobertura se decide en el nivel equivocado

**Evidencia:**

- El spec exige para Daniel una “cláusula atómica cuando un versículo contenga varios datos” (`pasted-text.txt:343-349`).
- El extractor conserva un solo ID por versículo (`scripts/lib/source_inventory.py:188-206`) y el builder copia las cláusulas detectadas dentro de `atomic_facts`, sin convertirlas en unidades (`scripts/build_final_day_v18_ledger.py:342-379`).
- El propio ledger contiene 74 unidades de Daniel con más de una entrada en `atomic_facts`: 437 entradas de hechos para solo 357 unidades Daniel. Por ejemplo, `DAN2-V002` contiene dos hechos en un único registro (`content/final-day-v18/source-ledger.json:2287-2297`) y se declara globalmente `COVERED` por tener preguntas enlazadas (`content/final-day-v18/source-ledger.json:2298-2311`).
- Incluso en PR hay proposiciones no separadas: “Honraron a Dios ...; y Dios los honró a ellos” queda como un solo `atomic_fact` (`content/final-day-v18/source-ledger.json:14895-14898`).

**Impacto:** no existe una decisión independiente por hecho/cláusula. Una pregunta enlazada a cualquier aspecto de un versículo basta para cubrir todas sus cláusulas, por lo que no se puede identificar con fidelidad qué detalle explícito requiere autoría. Los conteos de 1.031 unidades y 997 cubiertas no representan el universo atómico pedido.

### Critical 2 — `NEEDS_QUESTION` se asigna a referencias y fragmentos anafóricos; los estados previstos no se usan

**Evidencia:**

- La regla de estado es únicamente: OCR sin coincidencia → `AMBIGUOUS_SOURCE`; cero preguntas enlazadas → `NEEDS_QUESTION`; cualquier enlace → `COVERED` (`scripts/build_final_day_v18_ledger.py:381-401`).
- El ledger solo utiliza tres de los seis estados admitidos: 997 `COVERED`, 27 `AMBIGUOUS_SOURCE` y 7 `NEEDS_QUESTION`; nunca produce `COVERED_MERGED`, `NON_ATOMIC` ni `REFERENCE_ONLY` (`content/final-day-v18/source-ledger.json:80-84`).
- `PR39-P027-P001-S005`, cuyo texto completo es “Y así lo hicieron.”, queda `NEEDS_QUESTION` (`content/final-day-v18/source-ledger.json:14867-14881`). Es un fragmento anafórico que depende de la oración anterior.
- Cinco de los siete supuestos huecos son meras referencias: Proverbios, Jeremías, Isaías, Ezequiel y Daniel. Por ejemplo, `PR40-P037-P004-S002` contiene solo “Proverbios 14:34; 16:12; 20:28” y queda `NEEDS_QUESTION` (`content/final-day-v18/source-ledger.json:21262-21276`). La lista completa del reporte confirma los otros cuatro (`.work/final-day-v18/agents/ledger-v18-report.md:149-154`).

**Impacto:** Task 4 prioriza unidades `NEEDS_QUESTION`; con este ledger intentaría generar preguntas nuevas desde cinco referencias desnudas y un fragmento sin antecedente. Esos casos debían clasificarse, como mínimo, `REFERENCE_ONLY`/`NON_ATOMIC`, o fusionarse explícitamente mediante `COVERED_MERGED` con una unidad autosuficiente.

### Important 1 — `COVERED` solo significa “hay un enlace”, no cobertura real del hecho

**Evidencia:**

- `_load_current_questions` agrupa exclusivamente por coincidencia exacta de `source_unit_id` (`scripts/build_final_day_v18_ledger.py:219-229`).
- `_build_units` declara `COVERED` ante cualquier `current_ids`, sin comprobar qué `atomic_facts` aborda cada pregunta (`scripts/build_final_day_v18_ledger.py:389-401`).
- El reporte reconoce expresamente que no afirma “cobertura semántica ni suficiencia editorial” (`.work/final-day-v18/agents/ledger-v18-report.md:101-104`), pero el artefacto y el resumen llaman a esos registros `COVERED` y `covered_source_units` (`scripts/build_final_day_v18_ledger.py:513-516`).

**Impacto:** la comparación mecánica es útil, pero no satisface la instrucción de decidir por unidad si el detalle explícito está cubierto o necesita autoría. Debe distinguirse un estado de “enlace existente/no auditado” de una decisión real de cobertura, o comprobar la correspondencia hecho-pregunta antes de usar `COVERED`.

### Important 2 — `nearby_context` cruza capítulos y deja contexto editorialmente incorrecto

**Evidencia:**

- El contexto anterior/posterior solo comprueba que la obra sea igual; no exige mismo capítulo ni mismo párrafo (`scripts/build_final_day_v18_ledger.py:358-371`).
- En `DAN1-V021`, el contexto posterior es Daniel 2:1 (`content/final-day-v18/source-ledger.json:2220-2226`). El inverso ocurre en `DAN2-V001`, cuyo contexto anterior pertenece al capítulo 1.
- El mismo patrón aparece en todas las transiciones de Daniel y PR (por ejemplo, PR39→PR40), porque ambos capítulos comparten el mismo valor de `work`.

**Impacto:** los dosieres posteriores pueden presentar como “contexto cercano” texto de otro capítulo, contaminando la revisión editorial y las candidatas. En límites de capítulo debe omitirse el lado inexistente o conservarse explícitamente como cambio de capítulo, no como vecindad homogénea.

### Important 3 — Las pruebas verdes no validan atomicidad, estados, páginas/párrafos ni cobertura

**Evidencia:**

- El test llamado `...atomic_units` solo fija los conteos 1.031/357/674, unicidad de IDs, presencia de campos, estado permitido, página positiva y cita no vacía (`scripts/test_final_day_v18_ledger.py:56-83`). No verifica que cada unidad tenga exactamente un hecho atómico ni que los IDs representen cláusulas.
- La prueba de comparación fija 3.873/3.633/240 y dos veces el mismo conteo histórico 2.606 (`scripts/test_final_day_v18_ledger.py:85-103`), pero no fija los 2.217 hechos actuales, no comprueba el `declared_fact_count` contra el derivado y no prueba Banco Maestro por capítulo/página/párrafo.
- La prueba OCR valida un solo ambiguo y un solo cubierto (`scripts/test_final_day_v18_ledger.py:105-120`). No hay pruebas para `COVERED_MERGED`, `NON_ATOMIC`, `REFERENCE_ONLY`, fragmentos anafóricos, referencias desnudas, límites de capítulo o semántica de `NEEDS_QUESTION`.
- La prueba CLI sobrescribe los artefactos reales y solo vuelve a comprobar un conteo y dos cabeceras (`scripts/test_final_day_v18_ledger.py:122-137`). No compara bytes/hashes entre dos regeneraciones.

**Impacto:** la suite es parcialmente útil para identidad de fuente y errores básicos, pero ofrece señal insuficiente sobre los requisitos que distinguen un ledger canónico de un inventario mecánico. Su verde no respalda el dictamen de cumplimiento.

### Important 4 — La segmentación “atómica” y restauración textual dependen de heurísticas sin evidencia completa de revisión

**Evidencia:**

- `_split_propositions` decide unidades mediante puntuación, mayúscula inicial y un umbral de cuatro palabras (`scripts/lib/source_inventory.py:115-138`); no es una verificación semántica. Esto explica tanto la unidad doble de PR citada arriba como referencias bíblicas convertidas en unidades.
- `restore_corrupted_glyphs` elige automáticamente un token OCR por similitud de contexto y lo inserta en el texto (`scripts/lib/source_inventory.py:66-112`). El builder después usa ese texto restaurado como `exact_quote` (`scripts/build_final_day_v18_ledger.py:142-170,343-345`).
- El reporte enumera 27 ambigüedades, pero documenta revisión visual únicamente de tres ejemplos (`.work/final-day-v18/agents/ledger-v18-report.md:125-147`). La inspección de esas tres páginas sí confirmó que las observaciones reportadas son plausibles, pero no existe evidencia adjunta de revisión visual de las otras 24 ni de una muestra trazable de restauraciones aceptadas.

**Impacto:** no se observó una respuesta o doctrina inventada, pero sí decisiones editoriales de segmentación y restauración producidas por código. Antes de considerar el ledger canónico, las unidades heurísticas —en particular referencias, fragmentos cortos, cláusulas múltiples y restauraciones— necesitan validación humana/modelo trazable.

### Minor 1 — El JSON no es reproducible entre checkouts

**Evidencia:** el builder serializa rutas absolutas de la caché y de Banco Maestro (`scripts/build_final_day_v18_ledger.py:255-259,502-507`). Dos ejecuciones en este mismo checkout fueron byte-a-byte idénticas, pero el `source-ledger.json` cambia al mover el repositorio aunque el PDF, la caché y los bancos sean idénticos.

**Impacto:** el determinismo local está verificado; la reproducibilidad del artefacto y su SHA entre máquinas/worktrees no lo está. Conviene serializar rutas relativas estables.

## Aspectos conformes

- El contrato mínimo solicitado aparece en cada unidad y los seis estados están definidos como permitidos (`scripts/test_final_day_v18_ledger.py:23-43`; `scripts/build_final_day_v18_ledger.py:31-38`).
- El SHA-256 del PDF y la identidad declarada de la caché se rechazan si no coinciden (`scripts/build_final_day_v18_ledger.py:93-139`).
- Los conteos observados coinciden con el baseline: 3.873 preguntas, 2.217 `fact_id` actuales y 2.606 FACT históricos (`content/final-day-v18/source-ledger.json:70-78,196-204,468-478`).
- La comparación histórica conserva 1.002 FACT sin enlace en vez de inventar una correspondencia (`scripts/build_final_day_v18_ledger.py:272-314`; `content/final-day-v18/source-ledger.json:477-479`).
- `AMBIGUOUS_SOURCE` se aplica de manera conservadora cuando el texto completo no aparece en el OCR; las tres páginas citadas por el reporte fueron inspeccionadas visualmente y respaldan el carácter conflictivo de esos ejemplos.
- Dos regeneraciones en directorios temporales produjeron hashes idénticos a los reportados para JSON, CSV y Markdown.

## Verificación ejecutada

| Verificación | Resultado |
| --- | --- |
| Lectura completa de spec, plan Task 2, builder, tests, ledger y reporte | **PASS** |
| Análisis estructural del ledger | **PASS técnico**: 1.031 registros; 1.111 entradas en `atomic_facts`; 74 unidades multicláusula; estados 997/27/7 |
| Conteos banco actual/histórico | **PASS**: 3.873 preguntas; 3.633 mapeadas; 240 no mapeadas; 2.217 actuales; 2.606 históricas; 1.604 históricas mapeadas; 1.002 no mapeadas |
| Pruebas focales que no sobrescriben artefactos | **PASS**: 4 tests, 10.775 s |
| Suite completa `scripts.test_final_day_v18_ledger` | **NOT RUN**: su prueba CLI escribe sobre los tres artefactos reales, fuera del alcance de una revisión sin edición |
| Regeneración doble a directorios temporales y comparación SHA-256 | **PASS**: JSON/CSV/MD idénticos entre ambas ejecuciones y a los hashes del reporte |
| Inspección visual PDF páginas 3, 13 y 27 | **PASS limitado**: confirma los tres ejemplos documentados; las otras 24 ambigüedades quedan sin evidencia visual revisada |

## Condiciones para aprobación

1. Separar cada cláusula/hecho en un `source_unit_id` estable o representar explícitamente la relación padre-hijo y decidir cobertura por hecho, no por versículo.
2. Reclasificar referencias desnudas y fragmentos anafóricos con `REFERENCE_ONLY`, `NON_ATOMIC` o fusión explícita; reservar `NEEDS_QUESTION` para unidades autosuficientes y razonablemente preguntables.
3. Evitar `COVERED` por mera presencia de enlace; introducir una decisión de cobertura por `atomic_fact` o un estado mecánico que no prometa cobertura editorial.
4. Limitar `nearby_context` a fronteras editoriales válidas.
5. Añadir pruebas independientes y negativas para atomicidad, semántica de todos los estados, páginas/párrafos, límites de contexto, 2.217 actuales, 2.606 declarados/derivados y determinismo sin sobrescribir outputs reales.
6. Adjuntar evidencia trazable de revisión de segmentaciones/restauraciones ambiguas antes de promover el ledger como canónico.
