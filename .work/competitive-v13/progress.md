# Conexión Bíblica 2026 — checkpoint competitivo v13

- Actualizado: 2026-08-31 21:32:44 -06:00 (`America/Tegucigalpa`)
- Fase actual: Release 2, autoría IA paralela y construcción de revisión ciega.
- Rama: `codex/emergencia-competitiva-unica-v13`
- Base segura: `24c542fa3d2936c8fd98db706a9db930ba8338a3`
- Worktree: `C:\Users\melar\OneDrive\Desktop\Conexion biblica\.worktrees\emergencia-competitiva-unica-v13`
- PDF: `MaterialConexionBiblica (1).pdf`
- SHA-256 PDF: `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`

## Respaldo WIP

- Rama: `codex/reconciliacion-historica-wip-20260831`
- Commit: `35765b09a7fadd2333258323432e476c6a6fbf15`
- Reconciliación larga preservada además en `codex/expansion-competitiva-v11@004e6f5612bebb3a08fa86f2d6b54319b4be8103`.
- No borrar, limpiar ni podar los worktrees existentes; hay archivos no rastreados y otro trabajo ajeno.

## Release 1

- Corpus fuente auditado: 2,468 preguntas, 2,217 hechos, 18 unidades, cero violaciones.
- Banco público recompilado localmente: 2,468 preguntas y 2,217 hechos; 18/18 hashes de shard válidos; cero filas blind.
- Build ID local: `0964d9c4affc4dd06c322c190d4170dd4740fb026701c80e847efe8a6ca0d33a`.
- Las 250 blind históricas quedaron promovidas; los pools privados nuevos A/B/emergencia todavía no comenzaron.

## Validación actual

- Banco público local: 2,730 preguntas, 2,217 hechos, 18 unidades y cero filas blind/privadas; build ID `1cb318f973eacd4dbd74391bea3e77f77613994faccea42c31af375144a55eb2`.
- Pipeline/contrato R2–R3: 36/36; incluye promoción atómica, HMAC externo, amarre revisor/paquete/decisión y mapeo exacto `fact_id`–`source_unit_id`.
- Vitest: 434/434 pasan, incluida resistencia de 3,000 respuestas y 1,000 simulaciones de selección.
- TypeScript y ESLint: pasan.
- Build Vite: pasa; advertencia no fatal por chunk de 609.67 kB.
- E2E Chromium: 24 pasan en escritorio/móvil y 12 se omiten por diseño de proyecto.
- Inspección visual: Ruta del Día muestra 2,468 GOLD, 1,400 programadas y 0 de 4 bloques accionables sin desbordamiento visible.
- Clasificación activa: segura hasta 6 s; lenta sobre 6 s; error/no respondida con mayor prioridad de repaso.

## Siguiente acción exacta

Release 1 quedó fijado en `7dc70deb08345a9ecfdfdfd2e6a87c0a26c7df35` y desplegado como `dpl_7vbxgG65gXet5pGBp4rVa78ZyLFR`; el alias público pasó 13 pruebas Chromium aplicables.

El incremento estable R2 quedó fijado en `b83cf26fdd363a8717b40de7492ab06c8a6e0109` y desplegado como `dpl_C5VMbaN79tjzAbba1GkZ3iiGDUh8`. El alias público pasó la auditoría remota de 20 recursos/18 shards/2,730 preguntas/2,217 hechos sin fallos y 25 flujos Chromium; 11 se omitieron por diseño de proyecto.

Release 2 tiene 572 variantes candidatas revisadas a ciegas: 364 aprobadas, 208 rechazadas y cero pendientes de revisión. Los ciclos 11–14 agregaron 179 candidatas revisadas cruzadamente: 102 aprobadas y 77 rechazadas. El checkpoint append-only conserva exactamente las 262 aprobaciones publicadas y eleva el total editorial a 364, con hash `258d0a7e6ad228b759b6a03a6c8ec4b77a11c5e0843c3229c9757cfa1d14287e`. Las 102 nuevas todavía no están públicas; se acumularán hasta un siguiente incremento estable de 250. Quedan 1,853 hechos por cubrir para completar R2. Los paquetes ocultan autor, respuesta y explicaciones y usan una clave HMAC fuera del repositorio; como los subagentes comparten filesystem, la independencia demostrable es procedural, no aislamiento criptográfico contra un revisor malicioso.
