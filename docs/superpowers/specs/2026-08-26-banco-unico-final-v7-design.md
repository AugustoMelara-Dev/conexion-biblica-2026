# Banco Maestro Único — Final 2026

## Propósito

La aplicación ofrecerá un solo sistema público de entrenamiento para Daniel 1–12 RVR1995 y Profetas y Reyes 39–44, usando exclusivamente `MaterialConexionBiblica (1).pdf`. La versión técnica V7 no será visible como perfil. El usuario entra, pulsa **CONTINUAR MI MISIÓN** y recibe la siguiente actividad del plan adaptativo de 48 horas.

## Identidad canónica

- `bank_id`: `BANCO_UNICO_CONEXION_BIBLICA_2026`
- Nombre público: `Banco Maestro Único — Final 2026`
- Esquema interno: `7.0`
- Resumen, práctica, plan, estadísticas, historial, revisión y reservas ciegas consumen el mismo manifiesto, hechos e historial.
- Los bancos anteriores permanecen únicamente como fuentes de migración y respaldo; no aparecen en la interfaz.

## Inventario y cobertura

Un extractor independiente basado en PyMuPDF crea cuatro artefactos bajo `public/banks/final-2026/`:

- `source_inventory.json`: 357 versículos completos y todas las unidades de PR39–44 divididas por página, párrafo y proposición significativa.
- `fact_inventory.json`: hechos atómicos derivados con sujeto, acción, objeto, relaciones, categorías y trazabilidad literal.
- `coverage_manifest.json`: unidad → hechos → preguntas GOLD → familias.
- `source_extraction_issues.json`: correcciones de extracción confirmadas y evidencia; ninguna unidad ilegible puede entrar a GOLD.

El validador termina con error salvo que `uncovered_source_units`, `fact_without_gold_question` y `unmapped_source_units` sean cero. Las unidades de Daniel se contabilizan por versículo, aunque un versículo denso contenga varias proposiciones. PR se contabiliza por proposición significativa y conserva su párrafo padre.

## Banco GOLD

El banco contendrá entre 6,500 y 8,000 preguntas si la fuente permite sostenerlas. Habrá exactamente cuatro familias, todas respondidas por selección:

- `single_choice_direct`: cuatro opciones A–D.
- `fill_choice`: frase contextual con espacio y cuatro opciones A–D.
- `true_false`: botones Verdadero/Falso.
- `single_choice_contextual`: cuatro opciones; una sola aplicable al contexto exacto.

Cada familia representará 25 % ±2 % y tendrá al menos 1,500 preguntas. La dificultad objetivo será 5 % fácil, 20 % media, 45 % difícil y 30 % experta. Cada pregunta guarda unidad, hecho, variante, plantilla, referencia, cita literal, explicación, descarte de distractores y tres resultados de validación. Solo `final_editorial_status = GOLD` se publica.

La revisión adversarial recibe enunciado, opciones, referencia y fuente sin recibir el índice esperado. Debe reconstruir la respuesta desde la cita, justificar descartes y rechazar cualquier segunda respuesta defendible. Las verificaciones automáticas impiden duplicados, fugas por longitud, referencias inválidas, texto roto, secuencias léxicas y conocimiento externo.

## Rondas y aprendizaje

- 100: 25 directa, 25 completar, 25 V/F y 25 contextual.
- 50: 13 directa, 12 completar, 12 V/F y 13 contextual.
- 20: 5 de cada familia.
- No se repite `fact_id` en rondas normales.
- Una ronda de 100 añade al menos 15 interferencias altas, 10 causas/consecuencias, 10 comparaciones/diferencias y como máximo 15 básicas.

Una falla muestra respuesta, referencia, cita y explicación; programa otra variante y preferentemente otra familia después de 8–15 preguntas, luego 45–90 minutos, 6–10 horas y al día siguiente. Una corrección inmediata no domina. El dominio requiere primeros intentos, variantes y sesiones distintas, recuperación de horas y día siguiente, y una evidencia contextual o difícil sin pistas.

Las reservas A y B son conjuntos disjuntos de hechos, invisibles antes de su simulación y sin feedback inmediato. Emergencia es una tercera reserva del mismo banco.

## Persistencia y migración

Antes de migrar IndexedDB se guarda un respaldo V7 restaurable. El mapeo usa `fact_id`, identificador anterior, referencia, respuesta, cita y firma exacta; coincidencias inseguras permanecen como eventos legado y no alteran dominio. Cada exposición conserva texto y opciones mostradas, orden, posición correcta, respuesta, tiempo, fecha, intervalo, modo y pistas. La ronda activa persiste sus snapshots exactos.

## Interfaz

La portada muestra una misión principal y métricas por hechos. No contiene versiones, perfiles ni selectores de banco. Se eliminan del flujo activo `textarea`, respuestas escritas, multi-select, matching y ordering. Los modos manuales quedan secundarios y filtran el mismo banco. La interfaz debe funcionar sin desbordamiento a 390 px y conservar soporte offline.

## Puertas de aceptación

El pipeline, el build y CI comprueban cobertura completa, cuatro familias, 6,500 GOLD mínimos, respaldo/migración, scheduler, reservas, mezcla de rondas, ausencia de campos escritos y consistencia del banco. La entrega exige Vitest, TypeScript, ESLint, build, Playwright escritorio/móvil, offline, consola limpia, PR fusionado y verificación manual de producción.
