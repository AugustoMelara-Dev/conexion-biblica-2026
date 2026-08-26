# V5 - Consolidacion Final Design

## Objetivo

Convertir el perfil masivo existente en un sistema de consolidación guiada para la competencia del 29 de agosto de 2026. El éxito se mide por recuperación fría, diferida y ciega de hechos de calidad, no por cantidad bruta de preguntas.

## Decisiones de arquitectura

1. Los 14,000 registros originales permanecen inmutables en `public/banks/massive-v5`. Un proceso reproducible los clasifica en GOLD, SILVER y QUARANTINE y publica shards separados bajo `public/banks/consolidation-v5`.
2. `mc-sequence-v1` queda automáticamente en cuarentena. Los V/F falsos generados por sustitución libre también quedan en cuarentena salvo reglas editoriales explícitas; no se intentará inferir gramática fiable mediante heurísticas permisivas.
3. GOLD exige 85/100 y cero rechazos automáticos. Se limita a variantes con habilidades semánticas distintas por `fact_id`; duplicados y source spans repetidos se conservan en trazabilidad, no en entrenamiento.
4. IndexedDB sube de versión sin eliminar stores existentes. Se agregan dominio por hecho, eventos legados, respaldo de migración, plan final y consumo ciego. El mapeo inseguro se conserva como historial legado sin sumar dominio.
5. La selección normal carga shards GOLD paginados y excluye todo blind pool. Las simulaciones A y B usan listas de hechos disjuntas generadas editorialmente.
6. La portada se convierte en una misión guiada: cuenta regresiva, próxima misión, duración y un único CTA primario. Los modos manuales quedan secundarios.

## Calidad editorial

La puntuación suma fidelidad 25, respuesta única 20, español 15, valor competitivo 15, distractores 10, novedad 10 y referencia 5. Los rechazos automáticos prevalecen sobre la puntuación. El reporte publica conteos por capítulo, razón y template, muestra estratificada y ejemplos antes/después.

## Dominio y agenda

Cada intento genera evidencia sobre un `fact_id`. Un acierto inmediato tras feedback produce `repaired` y cero evidencia. `mastered` requiere tres aciertos de primer intento, tres habilidades semánticas, dos sesiones, recuperación de seis horas, recuperación al día siguiente, una variante difícil/experta, cero pistas y tiempo razonable. Los errores y respuestas lentas programan intervalos comprimidos; fallar un hecho dominado produce `lapsed`.

## Migración

Antes de migrar se guarda una instantánea en IndexedDB. Se enlazan eventos V1-V4 mediante ID, capítulo, referencia, respuesta y cita normalizados. Solo coincidencias inequívocas alteran dominio; las demás quedan en `legacyEvents`. Exportar/restaurar incluye los nuevos stores y mantiene compatibilidad con respaldos 2.0.

## Plan guiado

El plan usa `America/Tegucigalpa` y misiones fechadas del 26 al 29. Si no hay configuración usa seis horas diarias, competencia el 29 y cierre pesado a las 21:00 del 28. La mezcla inicial es 40% vencidas/falladas rojas, 25% nuevas prioritarias, 15% trampas, 10% lentas y 10% mantenimiento. El 28 consume blind A y B sin hechos comunes; el 29 solo activa conocimiento conocido.

## Verificación

Las puertas son: auditoría editorial automática, muestra estratificada, unitarias del dominio y almacenamiento, E2E móvil/escritorio, build, consola y desbordamiento, service worker, despliegue y comprobación de la URL pública.
