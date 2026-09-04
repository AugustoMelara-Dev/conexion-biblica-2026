# Revisión Task 3 — preparador de dosieres V18

## Veredicto

- **SPEC: FAIL**
- **QUALITY: ISSUES**
- Estado: **IMPLEMENTED**, con invariantes mecánicas correctas en los artefactos observados, pero sin aprobación del contrato completo. No se editaron el preparador, los tests ni los artefactos generados; este archivo es el único cambio de la revisión.

La ejecución actual contiene 3.873 preguntas únicas, produce 3.633 dossiers y deja exactamente 240 inválidas. La forma de los dossiers y los pares ciegos, el orden de lotes, la permutación de opciones, los hashes y el determinismo local pasan una auditoría independiente. Sin embargo, hay un incumplimiento editorial actual en los stems de Profetas y Reyes y varias puertas de seguridad/validación que pueden aceptar o exponer una ejecución no conforme.

## Findings

### Critical 1 — La mayoría de las preguntas PR no delimita la fuente en el enunciado

**Evidencia:**

- El spec exige que una pregunta que use un detalle exclusivo de Profetas y Reyes diga explícitamente “Según Profetas y Reyes...” (`C:\Users\melar\.codex\attachments\db52d1cc-8a1d-4039-8cb2-9cdb17463701\pasted-text.txt:284-291`) y establece que la compilación debe fallar si una pregunta PR no delimita la fuente (`...\pasted-text.txt:1112-1121`).
- El preparador copia el stem sin validarlo ni modificarlo (`scripts/prepare_final_day_v18_dossiers.py:422-487`).
- En los artefactos actuales, una comprobación independiente contó **1.588 de 1.638** preguntas PR válidas sin la cadena literal requerida: PR39 331/343, PR40 220/221, PR41 252/272, PR42 199/206, PR43 349/356 y PR44 237/240.
- El primer sample solicitado lo demuestra directamente: `batch-001` tiene `PR39-AUTH-0001` sin el delimitador en el stem (`.work/final-day-v18/dossiers/v18-priority-audit/batch-001.json:8-9`), aunque el dossier declara `material: "Profetas y Reyes"` (`...:16-22`).

**Impacto:** el auditor recibe material PR pero no una frontera editorial conforme al contrato. La auditoría puede mezclar una afirmación de Daniel con comentario PR o no detectar que la pregunta necesita una revisión de fuente. El lote no es aprobable como paquete V18 completo hasta rechazar/reformular esos stems o aplicar una puerta explícita.

### Critical 2 — La procedencia de fuente es fail-open cuando falta `source_sha256`

**Evidencia:**

- El spec exige calcular y confirmar el SHA-256 de la fuente canónica antes de usarla (`pasted-text.txt:211-244`).
- `_load_source_units` solo rechaza un hash declarado que sea distinto; un paquete sin `source_sha256` se acepta (`scripts/prepare_final_day_v18_dossiers.py:186-214`). `_load_ocr_pages` tiene el mismo comportamiento para OCR (`...:217-235`).
- Los tests sintéticos omiten deliberadamente `source_sha256` en los paquetes (`scripts/test_final_day_v18_audit_contract.py:68-73`) y también en el OCR (`...:170-174`), sin esperar `INVALID_OUTPUT`.
- Probe aislado, sin tocar el worktree: al quitar `source_sha256` de un paquete por lo demás trazable, `prepare_dossiers(..., min_batch_size=1, max_batch_size=20)` produjo `valid_count=1`, `invalid_count=0`, `batch_count=1`.

Los paquetes y el OCR actuales sí declaran el SHA esperado y el PDF disponible coincide independientemente con `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`; por tanto no se observó una fuente equivocada en esta ejecución. El defecto es la ausencia de una barrera fail-closed: un paquete alternativo sin hash puede alimentar dossiers que parecen válidos.

### Important 1 — La escritura no es atómica a nivel de ejecución ni valida schema antes del rename

**Evidencia:**

- `_atomic_write_json` escribe un `.tmp` y hace `os.replace`, pero no valida schema antes del rename (`scripts/prepare_final_day_v18_dossiers.py:111-117`).
- `prepare_dossiers` borra batches previos primero (`...:509-519`) y luego escribe cada dossier y su blind por separado (`...:648-672`). `main` no llama a `verify_artifacts` antes de devolver éxito (`...:814-827`).
- Probe aislado con una excepción inyectada en la segunda escritura dejó `dossier_files_after_crash=['batch-001.json']` y `blind_files_after_crash=[]`. El consumidor puede observar un lote sin su pareja ciega o una ejecución incompleta.

El rename por archivo es correcto para visibilidad de ese archivo, pero no satisface el flujo requerido de `archivo.tmp → validación de schema → rename atómico` ni protege el conjunto completo frente a un fallo a mitad de ejecución.

### Important 2 — La puerta de lotes permite producir y aprobar tamaños fuera de 15–20

**Evidencia:**

- El spec fija lotes de 15–20 (`...\pasted-text.txt:428-435`).
- `prepare_dossiers` expone `min_batch_size` y `max_batch_size` sin imponer 15 y 20 (`scripts/prepare_final_day_v18_dossiers.py:528-538`); la CLI también permite cambiarlos (`...:801-810`).
- `verify_artifacts` no comprueba `batch_min`, `batch_max`, `item_count` ni que cada tamaño esté en el rango (`...:741-773`).
- Probe aislado: con `min_batch_size=1, max_batch_size=2`, el preparador generó `[2, 1]` y `verify_artifacts` devolvió `True`.

La ejecución actual sí cumple: el manifest declara 182 lotes, todos 19 o 20 (175 de 20 y 7 de 19; `.work/final-day-v18/dossiers/v18-priority-audit/manifest.json:24-33`). El contrato, no obstante, puede ser bypassado por una llamada o configuración distinta.

### Important 3 — El verificador no comprueba que el blind conserve el mismo conjunto de opciones

**Evidencia:**

- El par ciego se genera desde las opciones del dossier con otro seed (`scripts/prepare_final_day_v18_dossiers.py:628-641`), pero `verify_artifacts` solo rechaza que las listas sean idénticas; no comprueba igualdad como multiconjuntos (`...:774-786`).
- Probe aislado: sustituir las opciones blind de un item por `['X','Y','Z','W']`, recalcular el hash de ese payload en el manifest y ejecutar `verify_artifacts` devolvió `True`.
- El test repite la misma comprobación débil en un solo item (`scripts/test_final_day_v18_audit_contract.py:102-108`).

Los pares actuales sí son correctos: 3.633/3.633 items tienen IDs alineados, multiconjuntos iguales y órdenes distintos. Falta una comprobación independiente que garantice esa relación después de una mutación o de un cambio futuro del generador.

### Important 4 — La suite de contrato es parcialmente tautológica y cubre solo una muestra mínima

**Evidencia:**

- El test importa desde producción `DOSSIER_ITEM_FIELDS`, `BLIND_ITEM_FIELDS` y `PROHIBITED_FIELDS` (`scripts/test_final_day_v18_audit_contract.py:15-20`) y luego compara los artefactos contra esos mismos símbolos (`...:99-107`). Si se altera el contrato y la constante a la vez, la prueba sigue verde; no existe un schema literal/independiente.
- Solo comprueba la primera batch para campos, prohibiciones y orden ciego (`...:92-108`), y solo compara bytes de la primera batch al repetir (`...:110-119`). No prueba todos los 182 lotes ni el manifest/invalid-items completos.
- El fixture usa únicamente PR39, DAN7 y DAN1 (`...:35-73`), por lo que no prueba la prioridad completa de 18 capítulos. Tampoco fija de manera independiente 3.873 filas/240 inválidas, ni exige que todos los motivos inválidos sean exactamente `source_unit_id` ausente.
- La ejecución focal de la versión inicial revisada fue verde (**6 tests OK**), pero ese resultado no cubre las obligaciones omitidas. En el estado concurrente actual, el test ya importa `prepare_safe_first_dossiers` (`scripts/test_final_day_v18_audit_contract.py:15-22`), símbolo que no existe en `scripts/prepare_final_day_v18_dossiers.py` (la última definición es `main` en `...:814-831`): una nueva ejecución termina con `ImportError` antes de correr casos.

### Important 5 — Tests y preparador están desincronizados en el estado actual del worktree

**Evidencia:**

- `scripts/test_final_day_v18_audit_contract.py:15-22` importa `prepare_safe_first_dossiers` y los casos nuevos lo invocan (`...:306-395`).
- `scripts/prepare_final_day_v18_dossiers.py` no define ese símbolo; solo expone `prepare_dossiers`, `verify_artifacts` y `main` (`...:528-538, 727-831`).
- La última ejecución fresca fue: `python -m unittest scripts.test_final_day_v18_audit_contract -q` → `ImportError: cannot import name 'prepare_safe_first_dossiers'`; **0 tests ejecutados**. Esto apareció después de la ejecución inicial 6/6 y no fue causado por esta revisión.

**Impacto:** el contrato actualmente no tiene una suite ejecutable. Hasta que el cambio concurrente se integre de forma consistente o se retire del test, no hay señal verde reproducible para Task 3.

### Minor 1 — Registros fuera de prioridad o malformados se omiten sin entrar a `invalid-items`

**Evidencia:**

- Una fila sin código de prioridad se cuenta en `outside_priority` y se descarta con `continue` (`scripts/prepare_final_day_v18_dossiers.py:553-560`); errores de lectura/tipo quedan solo en `question_errors` (`...:159-183`). Ninguno se materializa como `INVALID_OUTPUT` con `question_id`.

En los inputs actuales `outside_priority_count=0` y `question_errors=[]`, por lo que no produjo una pérdida observada. Si aparece una pregunta sin capítulo/ID reconocible, el manifest puede seguir pareciendo válido aunque la pregunta no haya sido inventariada como inválida ni dosificada.

## Comprobaciones conformes en esta ejecución

| Contrato | Resultado y evidencia |
| --- | --- |
| Inventario | **PASS mecánico**: 3.873 filas y 3.873 IDs únicos; manifest `selected_count=3873`, `outside_priority_count=0` (`manifest.json:26-31`). |
| Invalidación | **PASS mecánico**: 240/240 entradas tienen `status=INVALID_OUTPUT`, `reason=falta source_unit_id`; no hubo otros motivos ni `OUT_OF_BATCH` (`invalid-items.json:5-13`; manifest `:27-31`). Cada uno de los 3.633 IDs con source presente mapea a una única fila de las 1.024 unidades de fuente (sin IDs de fuente duplicados). |
| Lotes | **PASS actual**: 182 lotes; 175 de 20 y 7 de 19; el primer, intermedio y último sample tienen 20, 20 y 19 items (`batch-001.json:2-5`, `batch-091.json:2-5`, `batch-182.json:2-5`). |
| Prioridad | **PASS actual**: `priority_order` es PR39→PR44, DAN7→DAN12, DAN1→DAN6 (`manifest.json:4-22`) y la secuencia real de 3.633 items es monótona con esas 18 transiciones. |
| Frontera del auditor | **PASS estructural**: el builder reconstruye explícitamente solo los 11 campos del dossier (`scripts/prepare_final_day_v18_dossiers.py:472-486`); auditoría independiente encontró cero campos prohibidos en 3.633 items. No aparece `correct_option`, `correct_answer` ni equivalente top-level. |
| Blind | **PASS actual**: cada uno de los 3.633 items tiene exactamente `audit_run_id`, `question_id`, `question`, `options`; el primer item de cada sample lo muestra (`blind/batch-001.json:7-15`, `blind/batch-091.json:7-15`, `blind/batch-182.json:7-15`). |
| Opciones | **PASS actual**: todos los pares conservan el multiconjunto y tienen orden distinto. El primer PR sample cambia `Babilonia,Damasco,Nínive,Jerusalén` a `Jerusalén,Nínive,Damasco,Babilonia` (`dossiers/batch-001.json:10-15`; `blind/batch-001.json:10-15`). El mismo patrón aparece en batch-091 y batch-182. |
| Hashes | **PASS actual**: la auditoría independiente recomputó sin fallos los hashes de las 182 batches dossier, 182 blind y `invalid-items`; el manifest conserva SHA por batch (`manifest.json:221-224`, `:761-764`, `:2401-2408`). `verify_artifacts` sobre los artefactos reales devolvió `True`. |
| Determinismo | **PASS local**: regeneración completa en directorios temporales, con los mismos inputs/run ID, produjo bytes idénticos en 184 archivos dossier y 182 blind; no hubo diferencias. |
| Defaults/semántica de respuesta | **PASS dentro del alcance**: no se encontró `output.get("correct_option", 0)` ni equivalente; el generador no selecciona respuesta, no asigna decisión/dificultad y no copia metadata de respuesta. La permutación usa únicamente hashes de seed/opción (`...:402-419`). |

## Verificación ejecutada

1. Lectura completa de `AGENTS.md`, spec adjunto, `scripts/prepare_final_day_v18_dossiers.py`, `scripts/test_final_day_v18_audit_contract.py`, manifest, `invalid-items` y samples `batch-001`, `batch-091`, `batch-182` de dossier/blind.
2. `PYTHONDONTWRITEBYTECODE=1 python -m unittest scripts.test_final_day_v18_audit_contract -v` en la versión inicial → **6/6 OK**; reejecución fresca en el estado concurrente actual → **IMPORT ERROR**, 0 casos ejecutados (`prepare_safe_first_dossiers` ausente).
3. Auditoría Python independiente de inputs/outputs → **3.873/3.873 IDs**, 240 faltantes, 3.633 válidos, 182 batches, prioridad monótona, cero fallos de campos/hashes/permutaciones.
4. `verify_artifacts` sobre dossier/blind reales → **True**.
5. Regeneración completa en `TemporaryDirectory` y comparación byte a byte → dossier **184/184 idénticos**, blind **182/182 idénticos**.
6. Probes negativos aislados para hash ausente, tamaño de lote fuera de rango, crash entre escrituras y opciones blind incompatibles; los resultados se citan en Findings y no modificaron el worktree.

## Condiciones para aprobación

1. Añadir una puerta que exija “Según Profetas y Reyes...” en cada stem PR aplicable y falle la preparación/compilación si falta.
2. Exigir `source_sha256` presente y exactamente igual en cada paquete/OCR, o verificar directamente el PDF canónico antes de aceptar unidades; registrar la procedencia en el manifest.
3. Preparar en un staging de ejecución, validar todos los schemas y ambas ramas dossier/blind, y publicar el conjunto mediante un commit/rename de ejecución atómico; no borrar la ejecución anterior antes de completar.
4. Fijar 15–20 en el contrato (no solo como defaults) y hacer que `verify_artifacts` valide IDs de batch, `item_count`, tamaños y conteos manifestados.
5. Comprobar igualdad de multiconjuntos de opciones entre dossier y blind y añadir pruebas negativas independientes.
6. Reescribir los tests de schema con campos literales del spec/fixtures, verificar los 18 capítulos y ejecutar determinismo, campos, hashes y motivos inválidos sobre todos los artefactos generados.
7. Materializar como `INVALID_OUTPUT` cualquier fila que hoy quede fuera por prioridad o error de carga, evitando omisiones silenciosas.
