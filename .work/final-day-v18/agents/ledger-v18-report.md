# Reporte de construcción — ledger de fuente V18

Fecha de cierre: 2026-09-04
Worktree: `C:\Users\melar\OneDrive\Desktop\Conexion biblica\.worktrees\operacion-nacional-ultimo-dia-v18`

## Resultado

Se construyeron los tres artefactos del ledger V18 y el constructor/verificador
determinista. El ledger contiene 1.031 unidades de fuente: 357 versículos de
Daniel y 674 proposiciones de *Profetas y Reyes*. La ronda 1 añadió 1.380
registros de hechos atómicos hijos, reclasificó referencias/fragmentos y limitó
el contexto a la misma obra y capítulo. El constructor valida la identidad del
PDF y de la caché OCR antes de extraer o comparar datos, y no redacta preguntas
ni decide su calidad.

## Fuente e integridad

- PDF verificado: `MaterialConexionBiblica (1).pdf`.
- SHA-256 del PDF: `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`.
- Páginas PDF comprobadas: `60`.
- Caché usada: `scripts/source-cache/final-v7/ocr-pages.json`.
- `ocr-pages.json.source_sha256` coincide exactamente con el SHA-256 del PDF.
- SHA-256 de la caché: `9b12a3d1ab7618526c6c3cf0e245478c13c2161b18795fb8770bc2b77537c4d1`.
- La caché contiene 56 páginas de contenido (`3–25` y `27–59`); las páginas
  `1`, `2`, `26` y `60` no están en la caché por ser portada, páginas en blanco
  o cierre sin unidad textual.
- La segmentación e identificación de unidades reutiliza el extractor estable
  de `scripts/lib/source_inventory.py`. El texto se conserva tal como resulta
  de la fuente verificada; la caché homóloga se usa para restauraciones
  estrictamente limitadas de glifos dañados y para una comprobación independiente
  de soporte OCR. Cuando la cita completa no aparece en el OCR, el registro se
  marca `AMBIGUOUS_SOURCE`; no se hace corrección editorial automática.

## Desarrollo TDD

1. **RED** — se escribió primero `scripts/test_final_day_v18_ledger.py` y se
   ejecutó:

   ```text
   python -m unittest scripts.test_final_day_v18_ledger
   ```

   Resultado inicial: `Ran 5 tests`, `FAILED (failures=5)`, por faltar el
   módulo/constructor y sus artefactos esperados.

2. **GREEN** — se implementó el mínimo en
   `scripts/build_final_day_v18_ledger.py` y se volvió a ejecutar el mismo
   comando:

   ```text
   .....
   ----------------------------------------------------------------------
   Ran 5 tests in 14.636s

   OK
   ```

3. Verificación final de sintaxis:

   ```text
   python -m py_compile scripts/build_final_day_v18_ledger.py scripts/test_final_day_v18_ledger.py
   ```

   Resultado: código `0`, sin salida.

4. Regeneración final de los artefactos:

   ```text
   python scripts/build_final_day_v18_ledger.py
   ```

   Resultado:

   ```json
   {"coverage_status_counts":{"AMBIGUOUS_SOURCE":27,"COVERED":723,"COVERED_MERGED":274,"NEEDS_QUESTION":1,"NON_ATOMIC":1,"REFERENCE_ONLY":5},"current_questions":3873,"historical_fact_ids":2606,"source_units":1031}
   ```

5. Se confirmó que la regeneración es determinista. SHA-256 de los artefactos
   finales:

   | Artefacto | SHA-256 |
   | --- | --- |
   | `source-ledger.json` | `7083D6CB1156DC80229F071EA4A57D62AD84D0E6512AF2C7DAFFF0E74E45D86E` |
   | `source-ledger.csv` | `BD35AAEC56CB0995FB7F946BF52596A4638B47CE769EC6122E18B02357B6D118` |
   | `source-ledger.md` | `083EDF0240890D7F2B78AC3AD793AFFC6820CA476B54C0735A3D23225866A09E` |

## Conteos del ledger

| Métrica | Conteo |
| --- | ---: |
| Unidades de fuente | 1.031 |
| Daniel | 357 |
| Profetas y Reyes | 674 |
| Hechos atómicos hijos | 1.380 |
| `COVERED` (enlace de una unidad atómica) | 723 |
| `COVERED_MERGED` (padre con hijos) | 274 |
| `AMBIGUOUS_SOURCE` | 27 |
| `NEEDS_QUESTION` (unidad autosuficiente) | 1 |
| `NON_ATOMIC` | 1 |
| `REFERENCE_ONLY` | 5 |
| Preguntas del banco actual | 3.873 |
| Preguntas actuales vinculadas por `source_unit_id` | 3.633 |
| Preguntas actuales sin `source_unit_id` utilizable | 240 |
| Unidades con alguna pregunta actual vinculada | 1.024 |
| Fact IDs únicos del banco actual | 2.217 |

Los 240 registros no asignables son conservados como comparación mecánica, no
se les adjudica una unidad por semejanza. La cobertura de unidad se considera
solo cuando existe el vínculo explícito `source_unit_id`; el inventario no
afirma cobertura semántica ni suficiencia editorial.

## Comparación histórica

La fuente histórica disponible en el repositorio fue
`Banco_Maestro_CB2026.json` (3.558 preguntas). Se derivaron mecánicamente los
IDs únicos de `FULL_FACT_IDS`, `PARTIAL_FACT_IDS` e `INCIDENTAL_FACT_IDS`:

| Métrica | Conteo |
| --- | ---: |
| Fact IDs declarados/derivados | 2.606 |
| Fact IDs Daniel | 1.486 |
| Fact IDs Profetas y Reyes | 1.120 |
| Fact IDs enlazados estructuralmente a una unidad | 1.604 |
| Fact IDs sin enlace estructural único | 1.002 |

Para Daniel se usó la forma del ID (`FACT-Dxx-Vyy-*`). Para PR solo se
conservó un enlace cuando capítulo, página, párrafo y proposición producen una
coincidencia única. Los 1.002 restantes permanecen explícitamente sin mapear;
no se hizo asignación semántica ni inferencia de texto.

## Registros conservadores de ambigüedad

Las 27 unidades siguientes tienen `coverage_status=AMBIGUOUS_SOURCE` porque la
cita normalizada no aparece completa en las páginas OCR vecinas o porque el
marcador OCR observado es conflictivo:

```text
DAN1-V014, DAN1-V020, DAN2-V003, DAN2-V004, DAN2-V005, DAN2-V024,
DAN3-V009, DAN3-V018, DAN4-V015, DAN5-V010, DAN5-V018, DAN6-V006,
DAN6-V013, DAN6-V015, DAN6-V016, DAN6-V020, DAN6-V021, DAN9-V019,
DAN11-V040, DAN11-V045, PR39-P027-P002-S002, PR39-P028-P004-S002,
PR40-P037-P002-S002, PR42-P043-P005-S001, PR42-P044-P006-S001,
PR43-P051-P006-S002, PR43-P051-P008-S001
```

Ejemplos comprobados visualmente en el PDF renderizado:

- Página PDF 3: `DAN1-V014` muestra “Consintió”, mientras el OCR conserva una
  lectura incompatible; se deja ambiguo.
- Página PDF 13: `DAN5-V018` conserva el marcador OCR observado `8`; no se
  corrige automáticamente a `18`.
- Página PDF 27: `PR39-P027-P002-S002` muestra una diferencia OCR en
  “Israel/lsrael”; se deja ambiguo.

La única unidad autosuficiente sin pregunta actual es:

```text
PR40-P036-P001-S004
```

`PR39-P027-P001-S005` se conserva como `NON_ATOMIC` por ser el fragmento
anafórico “Y así lo hicieron.”. Las otras cinco unidades que inicialmente
parecían huecos son `REFERENCE_ONLY` porque contienen únicamente referencias
bíblicas: `PR40-P037-P004-S002`, `PR43-P050-P006-S004`,
`PR43-P051-P001-S004`, `PR43-P052-P004-S005` y `PR44-P058-P003-S006`.

## Archivos entregados

- `scripts/test_final_day_v18_ledger.py` — pruebas de contrato, integridad,
  conteos, estados, CLI y rechazo de caché con SHA incorrecto.
- `scripts/build_final_day_v18_ledger.py` — constructor, validador y CLI
  deterministas; solo enlaces mecánicos a bancos existentes.
- `content/final-day-v18/source-ledger.json` — ledger completo estructurado.
- `content/final-day-v18/source-ledger.csv` — una fila por unidad (`1.032`
  líneas incluyendo encabezado).
- `content/final-day-v18/source-ledger.md` — resumen y tabla legible (`1.064`
  líneas).
- `.work/final-day-v18/agents/ledger-v18-report.md` — este reporte.

## Limitaciones y preocupaciones para integración

- Hay 27 unidades que no deben promoverse automáticamente a contenido seguro:
  requieren revisión visual/curación por la discrepancia OCR registrada.
- Hay 1 unidad autosuficiente sin pregunta actual; el ledger la identifica, pero
  no genera preguntas. Hay además 1 fragmento `NON_ATOMIC` y 5 referencias
  `REFERENCE_ONLY` que no se ofrecen como huecos de autoría.
- Hay 240 preguntas actuales sin vínculo de unidad, principalmente registros
  V16; quedan fuera de la cobertura de unidad hasta que otro proceso les dé un
  vínculo explícito.
- El enlace histórico cubre 1.604 de 2.606 Fact IDs; los 1.002 no mapeables no
  deben usarse como evidencia de ausencia o presencia de cobertura.
- El ledger no ejecuta auditorías Sol/Luna, no evalúa respuestas ni modifica
  `public/`, `src/`, manifests o progreso global. Esos controles quedan fuera
  de la propiedad de este trabajo.
- No se hizo commit, de acuerdo con la instrucción de compartir filesystem.

## Corrección round 1 según `ledger-task-review.md`

La revisión clasificó el primer ledger como `SPEC: FAIL` por tratar 74 unidades
multicláusula como una sola cobertura y por enviar referencias/fragmentos a
autoría. Se aplicaron todos los hallazgos Critical e Important:

El ciclo TDD de esta ronda también tuvo RED verificable: después de añadir las
pruebas nuevas, `python -m unittest scripts.test_final_day_v18_ledger` terminó
con `Ran 10 tests ... FAILED (failures=3, errors=1)` por estados, límites de
contexto y campos de revisión todavía ausentes. Las pruebas de relación
padre-hijo añadidas después produjeron igualmente el fallo esperado (`Ran 3
tests ... FAILED`) antes de completar el builder.

- Se conserva cada `source_unit_id` padre para no romper vínculos existentes y
  se agregan `atomic_fact_records` hijos con IDs estables `-Fnn`, texto, estado,
  padre, alcance y evidencia de enlace. El split reproducible por puntuación se
  marca `ATOMIC_SPLIT_HEURISTIC` y `REVIEW_REQUIRED`.
- La decisión del padre es `COVERED_MERGED` cuando contiene varios hechos con
  enlace actual; cada hijo distingue enlace por sufijo de `fact_id` de un enlace
  solamente por `source_unit_id`. Ningún registro tiene
  `semantic_coverage_verified=true`. El bloque `coverage_semantics` declara
  explícitamente que `COVERED` significa solo enlace verificable, no auditoría
  semántica.
- Referencias bíblicas desnudas pasan a `REFERENCE_ONLY`; el fragmento anafórico
  pasa a `NON_ATOMIC`; `NEEDS_QUESTION` queda reservado para la unidad
  autosuficiente `PR40-P036-P001-S004`.
- `nearby_context` solo toma anterior/posterior de la misma obra y capítulo y
  expone `context_boundary` (`CHAPTER`/`WORK`/documento).
- Se añadieron `review_flags`, `requires_visual_review`,
  `visual_review_status`, `source_inventory_evidence` y el bloque de muestras
  visuales. La evidencia disponible es parcial: páginas PDF revisadas
  `3,13,27,33,59`; quedan 304 unidades con flags sin revisión visual individual.
- Las rutas serializadas del JSON ahora son relativas (`scripts/source-cache/...`
  y `Banco_Maestro_CB2026.json`), para no variar por ubicación del checkout.
- Las pruebas nuevas verifican hechos hijos, referencias/fragmentos, límites de
  contexto, identidad PR página/párrafo, flags visuales, 2.217 hechos actuales,
  2.606 declarados/derivados y regeneración byte-determinista en directorios
  temporales sin sobrescribir los artefactos del worktree.

### Verificación de la ronda 1

```text
python -m py_compile scripts/build_final_day_v18_ledger.py scripts/test_final_day_v18_ledger.py
```

Resultado: código `0`, sin salida.

```text
python -m unittest scripts.test_final_day_v18_ledger
```

Resultado final: `Ran 11 tests in 53.363s`, `OK`.

```text
python scripts/build_final_day_v18_ledger.py
```

Resultado final: `source_units=1031`,
`AMBIGUOUS_SOURCE=27`, `COVERED=723`, `COVERED_MERGED=274`,
`NEEDS_QUESTION=1`, `NON_ATOMIC=1`, `REFERENCE_ONLY=5`,
`current_questions=3873`, `historical_fact_ids=2606`.

## Corrección round 2 según la re-revisión

La re-revisión pidió endurecer `validate_ledger()` y hacer explícita la
aritmética de revisión visual. Se añadieron pruebas negativas independientes
para: ID atómico duplicado, `parent_source_unit_id` incorrecto, texto atómico
vacío y texto atómico que no pertenece a `exact_quote`. El validador ahora
rechaza cada mutación con un error específico (`atomic_fact_id_duplicate`,
`atomic_parent`, `atomic_text_empty` o `atomic_text_not_in_quote`) y valida
también la consistencia de los contadores visuales.

La métrica visual final queda definida así:

- `flagged_unit_count=307`: total de unidades con `requires_visual_review=true`.
- `total_sample_count=5`: muestras PDF declaradas (`3,13,27,33,59`).
- `reviewed_flagged_sample_count=3`: de esas cinco muestras, tres corresponden a
  unidades que sí tienen flag (`DAN1-V014`, `DAN5-V018` y
  `PR39-P027-P002-S002`); las páginas 33 y 59 son controles de maquetación sin
  flag.
- `unreviewed_flagged_unit_count=304`: `307 - 3`; no se resta el total de cinco
  muestras, porque dos muestras no eran unidades flagged.

### Verificación round 2

RED de las nuevas pruebas:

```text
python -m unittest scripts.test_final_day_v18_ledger.FinalDayV18LedgerTests.test_heuristic_units_carry_visual_review_evidence scripts.test_final_day_v18_ledger.FinalDayV18LedgerTests.test_validate_rejects_duplicate_atomic_fact_id scripts.test_final_day_v18_ledger.FinalDayV18LedgerTests.test_validate_rejects_atomic_child_parent_mismatch scripts.test_final_day_v18_ledger.FinalDayV18LedgerTests.test_validate_rejects_empty_atomic_child_text scripts.test_final_day_v18_ledger.FinalDayV18LedgerTests.test_validate_rejects_atomic_text_not_in_parent_quote
```

Resultado RED: `Ran 5 tests ... FAILED (failures=3, errors=1)`; el caso de
parent incorrecto ya estaba protegido por la ronda 1.

GREEN focal:

```text
Ran 5 tests in 18.854s

OK
```

GREEN completo:

```text
python -m py_compile scripts/build_final_day_v18_ledger.py scripts/test_final_day_v18_ledger.py
python -m unittest scripts.test_final_day_v18_ledger
```

Resultados: `py_compile` código `0`; `Ran 15 tests in 57.146s`, `OK`.

Regeneración final:

```text
python scripts/build_final_day_v18_ledger.py
```

Código `0`; produjo los tres artefactos con los conteos del bloque anterior.
SHA-256 finales: JSON
`7083D6CB1156DC80229F071EA4A57D62AD84D0E6512AF2C7DAFFF0E74E45D86E`, CSV
`BD35AAEC56CB0995FB7F946BF52596A4638B47CE769EC6122E18B02357B6D118`, Markdown
`083EDF0240890D7F2B78AC3AD793AFFC6820CA476B54C0735A3D23225866A09E`.
