# Reporte del preparador de dosieres V18

Fecha de ejecución: 2026-09-04
Worktree: `codex/operacion-nacional-ultimo-dia-v18`
Alcance: preparación mecánica determinista para Task 3. No se ejecutaron
auditorías Luna/Sol y no se modificaron `public/`, `src/`, ningún manifest de
producto ni `review-index`.

## Resultado del carril `v18-priority-audit`

- Preguntas existentes inspeccionadas en las prioridades `PR39–PR44`, `DAN7–DAN12` y `DAN1–DAN6`: **3,873**.
- Ítems trazables emitidos: **3,633**.
- Lotes emitidos: **182**, con tamaños entre **19 y 20** (todos dentro del rango solicitado 15–20).
- Pares ciegos emitidos: **182** lotes, uno por cada lote de dosier, con **3,633** ítems.
- Ítems fuera del dosier: **240**, todos `INVALID_OUTPUT` por ausencia de `source_unit_id` en la pregunta existente.
- Las filas malformadas y las filas sin capítulo de prioridad se materializan
  en `invalid-items.json` con motivo explícito; no se omiten silenciosamente.
- Ítems con fuente incompleta pero sin respuesta/default: ninguno adicional después de resolver páginas explícitas o localizar la cita/contexto en el OCR canónico.

Distribución de ítems emitidos:

| Unidad | Ítems |
|---|---:|
| PR39 | 343 |
| PR40 | 221 |
| PR41 | 272 |
| PR42 | 206 |
| PR43 | 356 |
| PR44 | 240 |
| DAN7 | 186 |
| DAN8 | 186 |
| DAN9 | 157 |
| DAN10 | 175 |
| DAN11 | 256 |
| DAN12 | 85 |
| DAN1 | 113 |
| DAN2 | 184 |
| DAN3 | 160 |
| DAN4 | 198 |
| DAN5 | 149 |
| DAN6 | 146 |

Los cuatro primeros lotes son PR39 y están listos para despacho al auditor
cuando exista evidencia Sol correspondiente. La puerta del preparador exige
ahora `15 <= batch_min <= batch_max <= 20`, y `verify_artifacts()` comprueba
ese rango, los conteos de cada lote, los IDs de lote y el multiconjunto de
opciones dossier/blind.

Ruling editorial explícito: las preguntas PR39–PR44 sin la cadena literal
`Según Profetas y Reyes` **no se filtran del carril priority**; siguen llegando
al auditor para marcarse como `REWRITE`/reformularse en la etapa editorial.
El hallazgo de delimitación no autoriza a convertir el preparador mecánico en
un filtro semántico. El carril adicional `v18-safe-first`, por su contrato
propio, sí selecciona únicamente stems que ya contienen esa delimitación.

## Carril adicional `v18-safe-first`

Se generó de forma separada, sin reutilizar ni regenerar el conjunto lógico de
selección de `v18-priority-audit`:

- **80 ítems únicos y trazables**, en exactamente **4 lotes de 20**.
- **60 PR39–PR44** con la cadena exacta `Según Profetas y Reyes` en la
  pregunta. La selección round-robin queda distribuida como PR39 **22**,
  PR40 **1**, PR41 **20**, PR42 **7**, PR43 **7** y PR44 **3**; el orden de
  capítulos sigue PR39→PR44.
- **20 Daniel únicamente DAN9/DAN12** con fuente completa. La prioridad
  personal usa solo marcadores textuales explícitos de las zonas personales de
  la especificación (pregunta/referencia/cita de fuente), alternando DAN9 y
  DAN12 cuando ambos tienen candidatos: DAN9 **11**, DAN12 **9**. Si ese pool
  trazable baja de 20, el carril falla cerrado y no hace fallback a DAN7/8/10/11.
- `invalid-items.json` del carril tiene **0** exclusiones; no se inventaron
  páginas, fuentes, respuestas ni dificultades. Las 29 filas PR39 que no
  traían `source_unit_id` propio solo entraron cuando su `source_quote` hizo
  un join exacto y único con una unidad canónica; joins ausentes o ambiguos
  siguen siendo inválidos.

Artefactos:

- Dosieres: `.work/final-day-v18/dossiers/v18-safe-first/`.
- Pares ciegos: `.work/final-day-v18/blind/v18-safe-first/`.
- Manifiesto/hashes: `.work/final-day-v18/dossiers/v18-safe-first/manifest.json`.

El manifiesto safe-first contabiliza `input_question_count=3873`,
`selected_count=80`, `valid_count=80`, `batched_count=80`,
`excluded_count=3793`, `outside_scope_count=1840`,
`outside_priority_count=1840`, `unknown_priority_count=0`,
`pr_without_delimiter_count=1666` y
`safe_first_unselected_candidate_count=287`. `outside_priority_count` ya no se
declara cero por defecto: en este carril representa todos los descartes fuera
del scope safe-first, mientras `unknown_priority_count` conserva el subconjunto
sin capítulo clasificable. Las filas PR con capítulo permitido pero sin el
delimitador se contabilizan aparte y no se pierden del carril priority.
La procedencia OCR queda trazada como ruta absoluta, `ocr_status=VALID` y el
SHA canónico esperado; estados `MISSING`, `INVALID_JSON`, `INVALID_SCHEMA` o
`INVALID_HASH` se conservan en el manifiesto y no pueden usarse como
localizador cuando la fuente necesita OCR.

## Artefactos

- Código: `scripts/prepare_final_day_v18_dossiers.py`.
- Pruebas TDD: `scripts/test_final_day_v18_audit_contract.py`.
- Dosieres: `.work/final-day-v18/dossiers/v18-priority-audit/`.
- Pares ciegos: `.work/final-day-v18/blind/v18-priority-audit/`.
- Manifiesto y hashes: `dossiers/v18-priority-audit/manifest.json`.
- Exclusiones: `dossiers/v18-priority-audit/invalid-items.json`.

Cada ítem de dosier contiene únicamente los campos de auditoría permitidos:
`audit_run_id`, `question_id`, `question`, `options`, `source_unit_id`,
`source_ref`, `pdf_page`, `exact_quote`, `nearby_context`, `material` y
`chapter`. El orden de opciones usa SHA-256 sobre una semilla estable por
ejecución/etapa/pregunta. El par ciego usa otra semilla y queda con exactamente
`audit_run_id`, `question_id`, `question` y `options`; no contiene fuente,
respuesta, resultados, decisiones, tier ni dificultad previa.

La página se toma de metadata explícita (`pdf_page`/`source_page`/`page`), del
número de página explícito en una referencia PR, o de coincidencia reproducible
de cita/contexto con `scripts/source-cache/final-v7/ocr-pages.json`. Si no hay
localizador único, el ítem se excluye; no se usa `0`, `null` ni otra respuesta
por defecto.

El manifiesto guarda SHA-256 canónicos de cada lote de dosier, cada lote ciego
y `invalid-items.json`, además del SHA esperado de la fuente canónica
(`0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`). Los
paquetes y el OCR sin ese hash, o con un hash distinto, quedan rechazados
(`fail-closed`). Cada ejecución se construye en staging oculto, se valida
antes de publicar y se publica como par dossier/blind; un fallo de escritura
no deja lotes parciales visibles en el destino.

`verify_artifacts()` comprueba esos hashes, el contrato de campos, IDs,
conteos/rango de lotes, multiconjunto de opciones y correspondencia
dosier/ciego; una mutación posterior devuelve `False`.

## Verificación ejecutada

- TDD RED observado antes de la implementación: primero importación ausente y
  después fallos de aserción por conteos/artefactos faltantes; cada ciclo se
  llevó a GREEN con una prueba específica.
- `python -m unittest scripts.test_final_day_v18_audit_contract` — **25 OK**,
  incluyendo RED-GREEN safe-first DAN9/12-only, contabilidad de exclusiones,
  hash/OCR ausente, límites de lote, schema mutado, mutación de multiconjunto
  ciego, desincronización de lote intermedio, payload no-objeto, contabilidad
  safe-first incompleta, ruta OCR ausente, payload no-objeto, valor de fuente
  ausente y lote no listado, además de fallos de escritura/segundo rename en
  staging.
- `python -m py_compile scripts\\prepare_final_day_v18_dossiers.py scripts\\test_final_day_v18_audit_contract.py` — **OK**.
- `python scripts/prepare_final_day_v18_dossiers.py` — **OK**; 3,873 seleccionadas, 3,633 válidas, 182 lotes, 240 inválidas.
- `python scripts/prepare_final_day_v18_dossiers.py --safe-first` — **OK**;
  80 seleccionadas/válidas, 4 lotes de 20, 60 PR y 20 Daniel.
- `verify_artifacts(Path('.work/final-day-v18/dossiers/v18-priority-audit'))` — **True**.
- `verify_artifacts(Path('.work/final-day-v18/dossiers/v18-safe-first'))` —
  **True**.
- Revisión mecánica de todos los lotes — 3,633 IDs únicos; cero violaciones de campos; cero pares ciegos con el mismo orden de opciones.
- Revisión mecánica safe-first — 80 IDs únicos, 60/20 PR/Daniel, prefijo exacto
  en los 60 PR, capítulos Daniel únicamente DAN9/DAN12, campos privados
  exactos y bytes estables al repetir la ejecución.
- Se generó primero una copia staged del carril priority y se compararon los
  182 hashes dossier y 182 hashes blind antes de publicar: **todos idénticos**
  a los existentes, incluidos batches 001–009 ya auditados. Solo cambió el
  manifiesto para incorporar accounting/OCR/schema; `verify_artifacts()` quedó
  **True** en ambos carriles.
- Un OCR declarado con SHA distinto al oficial se rechaza y no se usa como
  localizador de página (prueba de contrato incluida).
- Un paquete de fuente declarado con SHA distinto al oficial se rechaza
  completo y sus preguntas quedan `INVALID_OUTPUT` (prueba de contrato
  incluida).
- Round 2: `safe-first` exige exactamente 20 candidatos trazables de DAN9/12
  y falla cerrado cuando el pool es menor; no usa DAN7/8/10/11 como fallback.
  `verify_artifacts()` valida el `schema_version` exacto de cada payload, la
  contabilidad seleccionada/válida/batcheada/inválida/excluida, la trazabilidad
  OCR (ruta, estado y SHA), la desincronización de un lote intermedio y un
  fallo durante el segundo rename del par sin publicar un solo lado.
- Round 2 solo regeneró el carril `v18-safe-first`; no se volvió a escribir
  `v18-priority-audit`, por lo que los bytes/SHA de sus batches 001–009 ya
  auditados permanecen intactos. La corrección de contabilidad afecta al
  manifiesto safe-first, no a los lotes priority.

## Bloqueos y evidencia pendiente

- Las 240 preguntas `V16-R2-*` listadas en `invalid-items.json` no se pueden
  asociar a una unidad de fuente porque el material existente carece de
  `source_unit_id`; quedan fuera del lote hasta una vinculación editorial
  explícita.
- Este entregable no demuestra corrección de respuestas ni estados de
  auditoría: esas decisiones requieren los dictámenes reales Luna/Sol de las
  siguientes etapas. No se promovió ningún ítem a producción.

## Auditoría Sol Medium — priority batch-018

- Se publicó únicamente `.work/final-day-v18/audits/v18-priority-audit/sol-medium/batch-018.json` mediante archivo temporal y `os.replace`; no quedaron temporales de `batch-018` y no se modificaron lotes vecinos.
- Validación literal `final-day-v18-sol-audit-1.0` con `_validate_agent_output()` — **OK**; comprobación independiente de IDs, índice/texto, citas exactas, análisis por opción y hashes — **OK**.
- Conteos: **20** ítems, **20 ACCEPT_COVERAGE**, 0 `ACCEPT_COMPETITIVE`, 0 `REWRITE`, 0 `REJECT`, 0 `INVALID_OUTPUT`; todos con evidencia exclusiva de Daniel 8 (`DANIEL_ONLY`).
- `input_sha256`: `c70b8b386c771314f014088ee58dcb346e99a8001453b5063712fa6894de473f`; SHA del payload publicado: `ccf63e7baa1a598075d313377e96be8ce2b8e0ee1f7ce06b605b5c2d2e72c686`.
- Verificación adicional: `python -m unittest scripts.test_compile_final_day_v18 -v` — **9 OK**; `python -m py_compile scripts/compile_final_day_v18.py` — **OK**; `verify_artifacts()` del carril priority — **True**.

## Auditoría Sol Medium — priority batch-025

- Se publicó únicamente `.work/final-day-v18/audits/v18-priority-audit/sol-medium/batch-025.json` mediante staging temporal y `os.replace`; no se sobrescribieron lotes vecinos.
- Validación literal `final-day-v18-sol-audit-1.0` con `_validate_agent_output()` — **OK**; comprobación independiente de IDs, índice/texto, citas exactas, análisis por opción y hashes — **OK**.
- Conteos: **20** ítems, **3 ACCEPT_COVERAGE**, **17 REWRITE** por variantes superficiales documentadas, 0 `ACCEPT_COMPETITIVE`, 0 `REJECT`, 0 `INVALID_OUTPUT`; todos con evidencia de Daniel 9 (`DANIEL_ONLY`).
- `input_sha256`: `9ced1a74ace06efc382f10cb07c632690ff7cf512a9fc3adf61d9157e1ee327f`; SHA del payload publicado: `f79853ee9717444c905b76875408a9928fee7d3d5baa2b5d153f41f7235f15f3`.
- Verificación adicional: comprobaciones independientes de contrato/evidencia/privacidad — **OK**. La promoción posterior requiere el resultado ciego correspondiente.

## Auditoría Sol Medium — priority batch-036

- Se publicó únicamente `.work/final-day-v18/audits/v18-priority-audit/sol-medium/batch-036.json` mediante staging temporal y `os.replace`; no se sobrescribieron lotes vecinos.
- Validación literal `final-day-v18-sol-audit-1.0` con `_validate_agent_output()` — **OK**; comprobación independiente de IDs, índice/texto, citas exactas, análisis por opción y hashes — **OK**.
- Conteos: **20** ítems, **6 ACCEPT_COVERAGE**, **14 REWRITE** por variantes superficiales documentadas, 0 `ACCEPT_COMPETITIVE`, 0 `REJECT`, 0 `INVALID_OUTPUT`; todos con evidencia de Daniel 10 (`DANIEL_ONLY`).
- `input_sha256`: `49ef2fd877c73870f43f17922fdb9d4a097d3a9ebaf029a140ec4f842eabf339`; SHA del payload publicado: `2955c1ab9fb3f1e9e864c5099a69d11e0be081e556d5c5996c15d0088612a63b`.
- Verificación adicional: `python -m unittest scripts.test_compile_final_day_v18 -v` — **9 OK**; `python -m py_compile scripts/compile_final_day_v18.py` — **OK**. La promoción posterior requiere el resultado ciego correspondiente.
