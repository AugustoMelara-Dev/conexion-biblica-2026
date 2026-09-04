# Inventario mecánico del corpus actual V18

Fecha de corte: 2026-09-04. Worktree: `codex/operacion-nacional-ultimo-dia-v18`.

## Resultado ejecutivo

El paquete público `public/banks/final-2026` tiene 3.873 preguntas, 2.217 `fact_id`, 2.217 centrales, 1.656 variantes y 18 shards. Los 18 conteos, tamaños y SHA-256 declarados en el manifest coinciden con los archivos presentes. No hay IDs duplicados, respuestas seleccionadas inválidas ni `blind_pool` público no nulo.

Este documento es solo inventario mecánico. No declara ninguna pregunta auditada V18. El manifest marca todo como `GOLD`/`passed` por metadatos históricos, pero las filas no contienen `model`, `reasoning_effort`, `conversation_id` ni `reviewed_at`; por tanto, no hay evidencia nueva de una auditoría semántica V18 Sol Medium.

## Fuente canónica

`MaterialConexionBiblica (1).pdf` tiene 14.937.611 bytes, 60 páginas y SHA-256 `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`, que coincide con el hash exigido por `AGENTS.md`. La extracción pypdf produjo 285.825 caracteres y detectó marcadores de Daniel 1–12, RVR95, Profetas y Reyes 39–44 y Elena G. de White. La detección de marcadores solo demuestra presencia textual; no es revisión semántica.

## Conteos públicos observados

| Dimensión | Conteo |
|---|---:|
| Preguntas | 3.873 |
| Hechos únicos (`fact_id`) | 2.217 |
| Centrales | 2.217 |
| Variantes | 1.656 |
| `source_unit_id` no vacío y único | 1.024 |
| Filas con `source_unit_id` vacío | 240 |
| Familias | 4 |
| Shards | 18 |

Material inferido por prefijo de capítulo: Daniel 2.128 preguntas/1.030 hechos; PR 1.745 preguntas/1.187 hechos.

| Familia | Preguntas |
|---|---:|
| `single_choice_contextual` | 1.927 |
| `fill_choice` | 778 |
| `true_false` | 615 |
| `single_choice_direct` | 553 |

| Dificultad | Preguntas |
|---|---:|
| easy | 1.531 |
| medium | 1.260 |
| hard | 626 |
| expert | 456 |

| Plantilla | Preguntas |
|---|---:|
| `ai-authored-v11` | 3.011 |
| `ai-authored-v13-wave1` | 201 |
| `ai-authored-v13-release2` | 240 |
| `ai-authored-v16-wave3` | 240 |
| `ai-authored-v16-wave4` | 181 |

## Capítulos y materiales

`source_units_nonempty` cuenta solo IDs no vacíos. La columna `blank_source_unit_rows` evita contar la cadena vacía como unidad.

| Capítulo | Material | Preguntas | Hechos | Unidades | Vacías | Centrales | Variantes |
|---|---|---:|---:|---:|---:|---:|---:|
| DAN1 | Daniel | 113 | 54 | 21 | 0 | 54 | 59 |
| DAN2 | Daniel | 204 | 102 | 49 | 20 | 102 | 102 |
| DAN3 | Daniel | 200 | 100 | 30 | 40 | 100 | 100 |
| DAN4 | Daniel | 198 | 100 | 37 | 0 | 100 | 98 |
| DAN5 | Daniel | 149 | 100 | 31 | 0 | 100 | 49 |
| DAN6 | Daniel | 146 | 100 | 28 | 0 | 100 | 46 |
| DAN7 | Daniel | 186 | 79 | 28 | 0 | 79 | 107 |
| DAN8 | Daniel | 213 | 93 | 27 | 27 | 93 | 120 |
| DAN9 | Daniel | 203 | 88 | 27 | 46 | 88 | 115 |
| DAN10 | Daniel | 175 | 75 | 21 | 0 | 75 | 100 |
| DAN11 | Daniel | 256 | 103 | 45 | 0 | 103 | 153 |
| DAN12 | Daniel | 85 | 36 | 13 | 0 | 36 | 49 |
| PR39 | Profetas y Reyes | 450 | 225 | 139 | 107 | 225 | 225 |
| PR40 | Profetas y Reyes | 221 | 179 | 100 | 0 | 179 | 42 |
| PR41 | Profetas y Reyes | 272 | 192 | 108 | 0 | 192 | 80 |
| PR42 | Profetas y Reyes | 206 | 142 | 62 | 0 | 142 | 64 |
| PR43 | Profetas y Reyes | 356 | 282 | 158 | 0 | 282 | 74 |
| PR44 | Profetas y Reyes | 240 | 167 | 100 | 0 | 167 | 73 |

El manifest declara 1.025 IDs `source_unit_id` distintos si se conserva la cadena vacía como valor; el conteo útil no vacío es 1.024. La discrepancia corresponde exactamente a 240 filas con cadena vacía.

## Invariantes mecánicos

Pasaron sin discrepancias los checks siguientes:

- IDs de pregunta duplicados: 0.
- `variant_id` duplicados: 0.
- Firmas exactas repetidas de pregunta + opciones: 0.
- `correct_option` inválido o ausente: 0; respuesta correcta distinta de la opción seleccionada: 0.
- Respuesta correcta vacía: 0; opciones no-array: 0; número de opciones incorrecto: 0.
- Opciones duplicadas después de NFKC/minúsculas/espacios: 0.
- `accepted_answers` ausente/vacío: 0; respuesta correcta fuera de `accepted_answers`: 0.
- Explicación faltante para alguna opción incorrecta en `why_distractors_fail`: 0.
- `source_ref`/`reference` ausentes: 0; ambos desalineados: 0.
- `source_quote` o `source_span` vacíos: 0.
- Recalculo de `row_content_sha256`: 3.873/3.873 coinciden.

Como señal para la futura revisión semántica, 1.390 `fact_id` se reutilizan con más de una cadena `correct_answer`; esto corresponde a preguntas centrales y variantes con distinto alcance, y no se clasifica automáticamente como error de respuesta.

### Alertas de trazabilidad

Hay 31 filas cuyo `source_span` no es subcadena de `source_quote` tras normalizar solo espacios. Doce siguen sin ser subcadena después de normalizar acentos, comillas y espacios. IDs: `R2-C6-DAN4-014`, `R2-C6-DAN4-022`, `R2-C6-DAN4-024`, `R2-C9-DAN4-004`, `R2-C8-DAN5-002`, `R2-C8-DAN5-013`, `R2-C10-DAN6-009`, `R2-C10-DAN6-012`, `R2-C10-DAN6-016`, `R2-C10-DAN6-020`, `V13-R2-DAN6-C13-001`, `V13-R2-DAN6-C13-005`, `V13-R2-DAN7-C15-001`, `V13-R2-DAN9-C15-001`, `V13-R2-DAN9-C15-002`, `V13-R2-DAN9-C15-004`, `V13-R2-DAN10-C14-001`, `V13-R2-DAN10-C15-004`, `R2-C7-DAN12-001`, `R2-C7-DAN12-005`, `R2-C7-DAN12-006`, `V13-R2-PR39-C14-001`, `V13-R2-PR39-C14-003`, `V13-R2-PR40-C14-002`, `V13-R2-PR41-C12-008`, `V13-R2-PR42-C12-002`, `V13-R2-PR42-C12-005`, `V13-R2-PR42-C12-006`, `V13-R2-PR42-C12-008`, `V13-R2-PR44-P056-P006-S003-F01`, `V13-R2-PR44-P056-P007-S003-F01`. Es una alerta mecánica, no una conclusión doctrinal.

### Delimitador PR requerido

La especificación exige que toda pregunta PR delimite la fuente con “Según Profetas y Reyes”. Solo 99/1.745 contienen la frase normalizada; 1.646 no la contienen:

| Capítulo | Sin delimitador |
|---|---:|
| PR39 | 397 |
| PR40 | 219 |
| PR41 | 249 |
| PR42 | 197 |
| PR43 | 349 |
| PR44 | 235 |

Los faltantes por rol son 1.187 centrales y 459 variantes. Por familia: contextual 650, fill 398, true/false 319, direct 279. Es un bloqueo de contrato de redacción y no se corrige en este inventario.

## Índice de revisión público: metadata histórica

`review-index.json` tiene SHA-256 `b4fe2520a8bc488b39fb09644ef4d41a77d77c9b5ed86fa93d5eaed4988cb194`, 3.873 entradas, 3.873 `passed`, 3.873 aprobadas y 0 firmas humanas. Todos los IDs se unen con el corpus, y todos los hashes de contenido/fuente del índice coinciden.

Las filas públicas tienen 3.873 `final_editorial_status=GOLD`, 3.873 `ai_review.status=passed` y 3.873 `validation_adversarial.status=passed`. `reviewer_type=ai_semantic_audit` aparece 3.873 veces; 3.489 filas no tienen protocolo y 384 declaran `independent_semantic_review_v13`. No hay `model`, `reasoning_effort`, `conversation_id` ni `reviewed_at` por fila. Hay 1.431 etiquetas que contienen literalmente `gpt-5.6-sol`, pero una etiqueta no constituye evidencia V18 y no se cuenta como auditoría.

## Frontera blind

En `public/banks/final-2026` no hay filas con `blind_pool` distinto de nulo, ni archivos públicos cuyo nombre contenga `blind`, `private` o `emergency`. El manifest conserva el contrato histórico `private-blind-artifact-v1`, `artifact_id=competitive-v11-blind`, revisión `26a0b48a...5530d4`, y pools A/B/emergency con conteo 0; esos son metadatos, no contenido blind público.

En cambio, existe material privado preparado para `v18-priority-audit`: 182 paquetes ciegos con 3.633 IDs únicos, todos pertenecientes al corpus público actual. El manifest de dosieres reporta 3.873 seleccionadas, 3.633 válidas/batcheadas y 240 inválidas; las 240 se rechazan por “falta source_unit_id”. Estos paquetes son insumos sin juicio semántico, no auditorías V18 concluidas.

## Ledger de fuente V18

`content/final-day-v18/source-ledger.json` (1.655.984 bytes, SHA-256 `9f25c34541ccce5fee513afc181de10a22d939e0a6cccfd5f5d1f74b6e4d510a`) registra 1.031 unidades: 997 `COVERED`, 27 `AMBIGUOUS_SOURCE` y 7 `NEEDS_QUESTION`. Mapea mecánicamente 3.633 preguntas actuales y deja 240 sin mapeo; no es evidencia semántica V18.

## Contenido histórico inspeccionado

`Banco_Maestro_CB2026.json` (4.834.875 bytes; SHA-256 `b08ea1efb154a7f9a520e1cc4433cbd18b81e16f37e44cf474dfa3808323a078`) contiene 3.558 preguntas: 888 `HISTORICAL` y 2.670 `GENERATED`. Los estados históricos observados son 842 `VERIFIED_CORRECT`, 46 `CORRECTED` y 2.670 vacíos en las generadas. Declara 2.606 hechos históricos (Daniel 1.486, PR 1.120), cobertura 100% en su propio contrato y QC 2.670/2.670 `PASS_10_10`; nada de eso es auditoría V18.

`content/competitive-v11` contiene 2.468 preguntas y 2.468 revisiones en 18 archivos. Las decisiones históricas son 1.273 `inherited_verified_production`, 1.193 `ai_authored_and_semantically_reviewed` y 2 `corrected_during_v11_import`; las revisiones no exponen campo de modelo. `promoted-blind-v10.json` contiene históricamente 250 presentaciones/250 hechos.

`content/competitive-v13` contiene artefactos históricos separados: evidencia two-stage de 240 ítems; wave 1 de 201 `PASS_STRICT`; wave 2 de 240; staging reviews de 240 aprobadas por metadatos `gemini-3.7-flash`; y snapshots release2 hasta ciclo 50/1.405 aprobadas acumuladas. Las evidencias wave 1/wave 2 identifican `gemini-2.5-pro` en sus propios artefactos. No son Sol Medium V18.

También se inspeccionaron 18 archivos de candidatos `content/final-2026-authored/questions` (12.000 filas); son staging y no el corpus final público.

## Artefactos y hashes clave

Los hashes completos, por shard y por script relevante, están en [`current-corpus.json`](./current-corpus.json). Claves:

| Artefacto | SHA-256 |
|---|---|
| fuente PDF | `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3` |
| manifest final | `106528e90a18605a597ee97a5fd29396a4f735d2b39a04c39cef5cf98f977b5b` |
| review-index final | `b4fe2520a8bc488b39fb09644ef4d41a77d77c9b5ed86fa93d5eaed4988cb194` |
| Banco Maestro histórico | `b08ea1efb154a7f9a520e1cc4433cbd18b81e16f37e44cf474dfa3808323a078` |
| source-ledger V18 mecánico | `9f25c34541ccce5fee513afc181de10a22d939e0a6cccfd5f5d1f74b6e4d510a` |
| manifest de dosieres ciegos | `3abf47b8a1dc83b78680650427bb26568048b05cd7febdcf9c5ab816c433aadb` |
| invalid-items de dosieres | `9bbd439d706e01dbc6fd326b08ee87079d301232c6063891c12d996cfe2e7de0` |

## Comandos reproducibles

Desde la raíz del worktree:

```powershell
Set-Location 'C:/Users/melar/OneDrive/Desktop/Conexion biblica/.worktrees/operacion-nacional-ultimo-dia-v18'
Get-FileHash -Algorithm SHA256 'MaterialConexionBiblica (1).pdf'
& 'C:/Users/melar/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdfinfo.exe' -- 'MaterialConexionBiblica (1).pdf'
Get-FileHash -Algorithm SHA256 public/banks/final-2026/manifest.json,public/banks/final-2026/review-index.json,public/banks/final-2026/questions/*.json
node -e "const m=require('./public/banks/final-2026/manifest.json');let n=0;for(const s of m.shards)n+=require('./public/'+s.questions_file).length;console.log({shards:m.shards.length,questions:n,declared:m.gold_questions});"
node --test scripts/audit-live-final-bank.check.mjs
python -c "from pypdf import PdfReader; p='MaterialConexionBiblica (1).pdf'; r=PdfReader(p); print(len(r.pages),sum(len(x.extract_text() or '') for x in r.pages))"
```

El JSON de este inventario contiene el desglose completo de capítulos, shards, invariantes, historiales y artefactos.
