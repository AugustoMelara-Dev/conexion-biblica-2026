# Operacion nacional - ultimo dia V18

## Mision

Preparar una version estable y verificable de Conexión Bíblica para la final nacional del 5 de septiembre de 2026. La prioridad editorial es Profetas y Reyes 39-44, seguida de Daniel 7-12 y Daniel 1-6.

## Autoridad editorial

- Fuente canónica única: `C:\Users\melar\OneDrive\Desktop\MaterialConexionBiblica (1).pdf`.
- SHA-256 obligatorio: `0eea35deeaaa951c52e1e21af6a313f305335e3288d21316690922020e744be3`.
- El reporte AAH de `C:\Users\melar\Downloads\cxb-final-conexion-biblica-aah-2026_augusto-melara_reporte.pdf` solo informa prioridades de rendimiento.
- No usar Internet, otras Biblias, comentarios externos ni material privado para redactar o decidir respuestas.
- Una pregunta de Profetas y Reyes debe delimitarlo en el enunciado con “Según Profetas y Reyes...”.

## Integridad de auditoría

- Solo un dictamen textual realmente emitido por GPT-5.6 Sol Medium en esta operación puede producir evidencia V18 de auditoría Sol.
- No heredar, convertir ni inferir auditorías V18 desde metadata histórica o reglas de código.
- Scripts pueden validar esquemas, hashes, conteos e invariantes; nunca resolver preguntas, inventar distractores, dificultad, confianza, timestamps o identidad de agente.
- Campos editoriales requeridos ausentes producen `INVALID_OUTPUT`; nunca se rellenan con defaults.
- Toda discrepancia de respuesta requiere adjudicación, no corrección silenciosa.

## Propiedad de archivos

- Agentes de ledger: `content/final-day-v18/ledger-work/` y reportes asignados.
- Auditores: `.work/final-day-v18/audits/<audit_run_id>/` exclusivamente.
- Autores: `.work/final-day-v18/authors/<author_id>/` exclusivamente.
- Competidores ciegos: `.work/final-day-v18/blind/<run_id>/` exclusivamente.
- Solo el integrador principal modifica `public/banks/final-2026/`, manifest, review-index, catálogos y presets de producción.
- Ningún agente revierte cambios de otro agente; el repositorio es compartido.

## Implementación y pruebas

- Preservar IDs y progreso; una reescritura con ID nuevo exige mapping `old_id -> new_id`.
- TDD para comportamiento nuevo: prueba fallando, implementación mínima, prueba verde.
- Paquetes públicos solo admiten preguntas con evidencia V18 y estado `VERIFIED_COVERAGE_SOL` o `VERIFIED_COMPETITIVE_SOL`.
- Adversarial solo admite `VERIFIED_COMPETITIVE_SOL`.
- Antes de cada despliegue: validadores editoriales, tests focales, typecheck, lint, build y smoke desktop/móvil.
- No desplegar ni declarar cobertura completa si la evidencia no lo demuestra.

## Git y cierre

- Rama de trabajo: `codex/operacion-nacional-ultimo-dia-v18`.
- Base: `45d6e1ac6b01108080c21bed3574dc69c98e09cb`.
- No force push, no borrar worktrees ni staging histórico.
- Congelar y publicar únicamente el subconjunto seguro que pase todas las puertas.
