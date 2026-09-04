# Progreso — operación nacional último día V18

- Fase: primer incremento verificado desplegado; pendiente auditoría remota; rerevisión contractual independiente `SPEC PASS`.
- Rama/worktree: `codex/operacion-nacional-ultimo-dia-v18` / `.worktrees/operacion-nacional-ultimo-dia-v18`.
- Fuente: PDF oficial confirmado, SHA-256 esperado, 60 páginas.
- Ledger: 1,031 unidades y 1,381 hechos atómicos; 997 enlaces de cobertura mecánica, 27 ambiguas, 1 `NEEDS_QUESTION`, 1 `NON_ATOMIC`, 5 `REFERENCE_ONLY`. La cobertura semántica no se presume.
- Auditoría Sol: 380 dictámenes reales sobre 375 IDs únicos; 307 IDs solo `REWRITE`, 68 con alguna aceptación textual. Los gates ciego/almacenado/conflictos dejan 50 promovibles.
- Reescrituras: 80 procesadas; 75 candidatas nuevas y 5 retiradas como duplicadas; ninguna se considera aceptada hasta repetir A+B.
- Integración safe-first: 80 ítems; 45 pasaron, 25 requieren reescritura y 10 fallaron por `source_unit_id` almacenado ausente. Al endurecer priority, sus 140 salidas procesadas quedaron invalidadas por hash; no condicionan safe-first.
- Paquetes desplegables actuales: A=45 (37 PR, 8 Daniel; 45 hechos distintos), B=0, C=8 (DAN9=4, DAN12=4). Los objetivos 1,000/300 siguen incompletos.
- Reporte AAH: 98/100, 3.72 s; prioridades Daniel 9:26 y Daniel 12:1.
- Cuota: 9% usado, 91% remanente; se conserva holgadamente la reserva mínima de 35%.
- Limitación de evidencia: la plataforma no expone UUID de conversación a los agentes; se registran nombres canónicos reales de tarea, identificados como tales.
- Baseline: Vitest 466/466, TypeScript y build pasan; ESLint ya fallaba en base con 26 errores y 1 warning; unittest editorial bloqueado en base por `source_inventory.json` ausente.
- Gates actuales: 57 pruebas Python, 473 Vitest, TypeScript, build y `git diff --check` pasan; Playwright pasa 10/10 en Chromium escritorio/móvil. ESLint conserva deuda heredada (22 errores y 1 warning, frente a 26+1 en base). `test:final-bank` sigue bloqueado como en base por `public/banks/final-2026/source_inventory.json` ausente.
- Contratos endurecidos: priority excluye 1,666 PR sin delimitador; safe-first traza 3,793 exclusiones fila por fila; OCR se reabre y valida; la publicación usa marcador transaccional que bloquea consumidores; el ledger separó la proposición detectada y valida IDs/textos/orden.
- E2E confirmó carga exacta: el selector pide los IDs V18 auditados sin sustituir presentaciones ni adjuntar variantes no auditadas.
- Commit publicado: `79f229d`. Producción `READY`: `https://conexion-biblica-2026.vercel.app` (`dpl_5W14o9G1vS6ZyfYHKnZi8tkoQWjB`).
- Siguiente acción: auditoría remota y verificación desplegada en escritorio/móvil.
