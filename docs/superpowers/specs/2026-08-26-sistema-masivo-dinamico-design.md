# Sistema masivo y dinámico de entrenamiento — diseño

## Objetivo

Convertir la aplicación existente en un entrenador competitivo para las próximas 48 horas, conservando todos los bancos e historiales actuales. La única fuente editorial es `MaterialConexionBiblica (1).pdf`: Daniel 1–12 en RVR1995 y Profetas y Reyes 39–44.

## Alcance aprobado

- Generar inicialmente 8,000 preguntas verificadas de Daniel y 6,000 de Profetas y Reyes, sin inflar el banco con paráfrasis equivalentes.
- Mantener las cuotas por capítulo, tipo y dificultad definidas por el usuario.
- Reservar al menos 15 % de hechos/variantes para simulaciones ciegas.
- Implementar variantes, distractores contextuales, barajado, exposición por hecho/variante y selección adaptativa.
- Añadir los 20 modos solicitados y el plan adaptativo “PLAN FINAL — 48 HORAS”.
- Preservar bancos, progreso, sesiones y reportes existentes mediante migración de IndexedDB.
- Dividir el contenido en fragmentos para no cargar el banco completo en memoria.
- Verificar con pruebas unitarias, integración, Playwright, build y despliegue de producción en Vercel.

## Arquitectura

### Canal editorial

`scripts/generate-massive-training-system.py` abre el PDF con PyMuPDF, extrae versículos y párrafos en orden, y construye hechos atómicos. Cada hecho conserva fuente, sujeto, acción, objeto, contexto, relación, importancia y vecinos plausibles. Los candidatos se generan desde familias semánticas controladas: directa, inversa, completar, verdadero/falso de una sola mutación, selección contextual, secuencia y comparación.

La auditoría automática rechaza registros sin respaldo literal, campos obligatorios, respuesta única, distractores suficientes o identidad semántica diferenciada. El resultado se escribe por capítulo en `public/banks/massive-v5/`, junto con hechos, plantillas, distractores, manifiesto, estadísticas y reporte. Los archivos previos permanecen intactos.

### Modelo de aplicación

El dominio amplía `Question` con `factId`, `variantId`, `templateId`, anclaje de contexto, respaldo, explicación de distractores, modo de respuesta, tipo de trampa y reserva ciega. Los campos antiguos siguen válidos y se normalizan durante la importación.

IndexedDB sube de versión y añade índices para banco, capítulo, `factId`, dificultad, tipo y reserva ciega, además de un almacén de exposición por variante. La migración solo añade campos/almacenes e índices; no borra progreso ni sesiones.

### Carga y selección

El manifiesto describe fragmentos y conteos. La aplicación importa fragmentos por capítulo y consulta subconjuntos indexados para una sesión, en lugar de materializar el banco completo. La selección normal aplica 60 % novedad, 20 % errores, 10 % correctas lentas y 10 % trampas de capítulos débiles; elimina `factId` repetidos. La reserva ciega solo se habilita en modos explícitos.

El motor dinámico elige una plantilla compatible, reformula dentro de límites cerrados, selecciona distractores cercanos de la misma categoría y baraja opciones con una semilla de sesión. El `variantId` efectivo incorpora plantilla y combinación de distractores para impedir la memorización de posición.

### Experiencia

Los 20 modos se presentan en grupos compactos, no como una pared de tarjetas. El plan de 48 horas muestra diez bloques, progreso, objetivo y adaptación. Referencia, explicación y razones de distractores se revelan solo después de responder. Estadísticas muestran cobertura de hechos, precisión por capítulo/tema/tipo/dificultad, errores repetidos y lentitud.

### Rendimiento y offline

Los fragmentos son JSON compactos y versionados. El service worker cachea el manifiesto y los fragmentos usados, sin dejar eternamente una versión antigua. La selección usa índices y límites; ninguna pantalla necesita las 14,000 preguntas simultáneamente.

## Reglas de calidad

- Única fuente: el PDF local; ningún contenido web se incorpora al banco.
- Daniel conserva RVR1995 y PR conserva su terminología.
- Una sola respuesta aplicable al contexto exacto.
- Falso = una sola alteración verificable.
- Completar = 1–8 palabras significativas con contexto suficiente.
- Selección múltiple = cuatro opciones equivalentes, A/B/C/D balanceadas al generar y rebarajadas al mostrar.
- 35–45 % de selección múltiple usa distractores verdaderos en otro contexto.
- Cero `id`/`variantId` duplicados y cero repetición de `factId` dentro de una sesión normal.

## Pruebas y aceptación

La generación debe validar conteos, cuotas, campos, referencias, citas, unicidad, duplicados, reserva ciega y distribución. Las pruebas de dominio cubren barajado, selección por cuota, exposición, reserva y sesiones de 50/100/200. Las pruebas de almacenamiento cubren migración e índices. Playwright cubre modos, plan 48 horas, persistencia, móvil y escritorio. Se considera terminado únicamente con generación, integración, pruebas, build, despliegue y URL pública verificada.
