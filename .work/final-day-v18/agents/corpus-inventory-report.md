# Reporte de ejecución — `corpus-inventory`

Fecha: 2026-09-04
Worktree: `C:/Users/melar/OneDrive/Desktop/Conexion biblica/.worktrees/operacion-nacional-ultimo-dia-v18`
Rama: `codex/operacion-nacional-ultimo-dia-v18`

## Alcance y límites respetados

Se leyó `AGENTS.md` y la especificación `C:/Users/melar/.codex/attachments/db52d1cc-8a1d-4039-8cb2-9cdb17463701/pasted-text.txt` (SHA-256 `b30bf742f5715b7b59f94ac3d172dc294cf8e0573837a817141826951392112b`; verificación de hash del archivo externo ejecutada). Se inspeccionaron el manifest e índice públicos finales, los 18 shards, contrato de tipos/validadores, scripts de compilación/auditoría, `Banco_Maestro_CB2026.json`, contenido histórico V11/V13, staging, source-ledger y los paquetes ciegos privados V18.

No se modificaron `public`, `src` ni `scripts`; no se usó Sol para tareas mecánicas, no se lanzaron subagentes y no se hizo commit. Antes de editar, `git status --short` ya mostraba como no rastreados `AGENTS.md`, `scripts/prepare_final_day_v18_dossiers.py`, `scripts/test_final_day_v18_audit_contract.py`, `scripts/test_final_day_v18_ledger.py` y `.work/final-day-v18/`; se conservaron sin tocar.

## Entregables escritos

- `.work/final-day-v18/inventory/current-corpus.json`: inventario estructurado, tablas por capítulo, hashes de shards y artefactos, joins y alertas.
- `.work/final-day-v18/inventory/current-corpus.md`: lectura humana del mismo inventario.
- Este reporte de ejecución.

## Resultado verificable

- Público final: 3.873 preguntas, 2.217 hechos únicos, 2.217 centrales, 1.656 variantes y 18 shards.
- Manifest: suma de shards 3.873; 18/18 conteos, bytes y SHA-256 coinciden.
- Índice: 3.873 entradas `passed`, 3.873 aprobadas, 0 firmas humanas; todos los IDs y hashes se unen al corpus.
- IDs repetidos, firmas exactas repetidas, opciones/respuestas inválidas y referencias vacías/desalineadas: 0.
- `blind_pool` no nulo en filas públicas: 0; archivos públicos con nombre blind/private/emergency: 0.
- Fuente PDF: 60 páginas, 14.937.611 bytes, SHA-256 canónico `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`.

## Problemas encontrados

1. **Bloqueo de mapeo/auditoría:** 240 variantes `ai-authored-v16-wave3` tienen `source_unit_id` vacío. Se concentran en DAN2 (20), DAN3 (40), DAN8 (27), DAN9 (46) y PR39 (107). El manifest de dosieres privados selecciona 3.873, pero solo 3.633 son válidas/batcheadas; `invalid-items.json` marca las 240 con `falta source_unit_id`.
2. **Bloqueo de redacción PR:** 1.646 de 1.745 preguntas PR no contienen el delimitador normalizado `Según Profetas y Reyes` exigido por la especificación.
3. **Alerta de trazabilidad textual:** 31 `source_span` no son subcadenas de `source_quote` con normalización de espacios; 12 persisten tras normalizar acentos/comillas. No se interpretó como error doctrinal.
4. **Cobertura de fuente mecánica:** el source-ledger registra 1.031 unidades: 997 `COVERED`, 27 `AMBIGUOUS_SOURCE`, 7 `NEEDS_QUESTION`; esto es mapeo, no juicio semántico.

## Frontera de evidencia V18

No se encontró ningún registro de decisión semántica V18 Sol Medium. El índice final y las etiquetas `gpt-5.6-sol` son metadatos históricos; faltan por fila modelo, esfuerzo de razonamiento, conversación y fecha de revisión V18. El material privado en `.work/final-day-v18/blind`/`dossiers` es preparación de entradas y fuente, sin veredictos. Por ello el inventario registra **0 preguntas auditadas V18** y no infiere cobertura auditada desde `GOLD`/`passed`.

## Comandos ejecutados

Comprobaciones de lectura y conteo:

```powershell
git status --short
Get-FileHash -Algorithm SHA256 'MaterialConexionBiblica (1).pdf'
& 'C:/Users/melar/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdfinfo.exe' -- 'MaterialConexionBiblica (1).pdf'
Get-FileHash -Algorithm SHA256 public/banks/final-2026/manifest.json,public/banks/final-2026/review-index.json,public/banks/final-2026/questions/*.json
node -e "const m=require('./public/banks/final-2026/manifest.json');let n=0;for(const s of m.shards)n+=require('./public/'+s.questions_file).length;console.log({shards:m.shards.length,questions:n,declared:m.gold_questions});"
node -e "const x=require('./.work/final-day-v18/dossiers/v18-priority-audit/manifest.json');console.log({selected:x.selected_count,valid:x.valid_count,invalid:x.invalid_count,batches:x.batch_count});"
python -c "from pypdf import PdfReader; p='MaterialConexionBiblica (1).pdf'; r=PdfReader(p); print(len(r.pages),sum(len(x.extract_text() or '') for x in r.pages))"
```

La validación del formato de los artefactos propios de este inventario fue:

```powershell
node -e "const x=require('./.work/final-day-v18/inventory/current-corpus.json');console.log({schema:x.schema_version,chapters:x.public_bank.chapters.length,shards:x.public_bank.shards.length,findings:x.findings.length});"
```

Resultado observado: JSON válido, 18 capítulos, 18 shards y 6 hallazgos. Un segundo join contra los shards/manifest volvió a obtener 3.873 filas, 2.217 hechos, 2.217 centrales, 1.656 variantes, 18 shards, 3.873 entradas de índice, 0 filas blind públicas y 0 IDs duplicados (`match: true`). También se ejecutaron `node --test scripts/audit-live-final-bank.check.mjs` (34 tests, 34 pass) y tres pruebas de ledger en memoria (`test_real_ledger_has_canonical_source_and_atomic_units`, `test_comparison_keeps_unmapped_current_questions_visible`, `test_ocr_mismatch_is_ambiguous_and_not_silently_repaired`; 3 pass, 0 fail).

No ejecuté el test CLI del builder del source-ledger porque ese comando escribe/reemplaza artefactos fuera de la propiedad exclusiva de este encargo. El check de producción `audit-live-final-bank.check.mjs` queda documentado como comando reproducible, pero no se usó para afirmar auditoría semántica V18.

## Evidencia que falta

Para cerrar V18 todavía hacen falta registros reales por pregunta producidos por el modelo/protocolo autorizado, con identidad de modelo Sol Medium, conversación, esfuerzo, decisión, justificación y trazabilidad verificable. Este encargo solo deja el inventario y los bloqueos mecánicos visibles.
