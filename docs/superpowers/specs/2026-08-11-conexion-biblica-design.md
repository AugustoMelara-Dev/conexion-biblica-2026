# Conexión Bíblica 2026 — Diseño

## Objetivo

Aplicación local-first para practicar Daniel 1–12 (RVR95) y Profetas y Reyes 39–44. Importa bancos JSON `schemaVersion: "1.0"`, valida sin alterar los originales, ejecuta sesiones con los doce tipos de pregunta, registra respuestas y conserva el progreso en IndexedDB.

## Decisiones

- React + Vite + TypeScript como SPA instalable y fácil de ejecutar localmente.
- shadcn/ui para controles accesibles y consistentes; CSS propio solo para tokens y layout.
- IndexedDB para bancos, progreso, historial y reportes; `localStorage` únicamente para tema, preferencias de sesión y ruta visual.
- Sin API, telemetría, fuentes remotas, analytics ni dependencia en internet después del build.
- Los 10 JSON presentes en el workspace se sirven como bancos iniciales locales. Se conservarán también los archivos originales en la raíz.
- Un `questionKey` se compone de `bankId` + `question.id`; así se evita colisión entre bancos y nunca se muta una pregunta importada.

## Arquitectura

`src/domain` contiene tipos, validación, evaluación, dominio y algoritmo de selección sin React. `src/storage` encapsula IndexedDB con stores separados para banks, questions, progress, sessions y reports. `src/app` contiene el estado de la aplicación y casos de uso. `src/components` contiene el shell, dashboard, configuración, quiz, resultados y tablas. `src/components/ui` contiene los componentes shadcn/ui generados/compuestos.

El arranque lee los bancos integrados solo si no existe el banco con el mismo fingerprint. La importación de varios archivos se valida en lote y muestra errores por archivo/pregunta; un reemplazo solo se confirma después de una validación completa. El respaldo exporta un sobre versionado con bancos, progreso, preferencias, historial y reportes; la restauración valida todo antes de reemplazar.

## Modelo de práctica

Cada respuesta actualiza `QuestionProgress`: `timesSeen`, aciertos/fallos, rachas, tiempos, `masteryScore` 0–5, favoritos, difícil, reportado y `history`. Acierto suma 1 (máximo 5), fallo resta 1 (mínimo 0). Dominada requiere score ≥4, al menos 3 aciertos y ninguna de las últimas 3 apariciones fallada. Los fallos entran en una cola de repetición con separación de 8–20 preguntas y nunca se repiten dentro de la misma sesión.

El selector filtra primero por la configuración y después puntúa por modo: errores prioriza fallos, recencia, lentitud y dificultad; campeonato usa distribución objetivo 40/35/20/5 para dificultades 5/4/3/1–2 con redistribución si falta una categoría. La mezcla usa ventanas de candidatos, penalización por capítulo/fuente/factKey reciente y un RNG con semilla por sesión para que sea reproducible en tests.

## Flujos UI

1. Dashboard: métricas generales, cobertura de bancos, rendimiento por capítulo y accesos a modos.
2. Banco de preguntas: dropzone multiarchivo, lista de bancos, reemplazar/eliminar, exportar bancos y respaldos, importación detallada de errores.
3. Configurar sesión: fuente, capítulos, dificultad, tipos, estado, cantidad, temporizadores y aleatorización.
4. Quiz: una pregunta por vista, reloj, progreso, respuesta accesible por teclado, controles por tipo, favoritos/reportes y navegación segura.
5. Resultados: puntuación, precisión, media/mediana, extremos, desglose y acciones para errores, repetición o nueva configuración.
6. Estadísticas: general, fuente, capítulo, dificultad, tipo, puntos débiles e historial revisable.
7. Revisar preguntas: reportes con pregunta original, respuesta registrada, referencia, motivo y copia del JSON.

## Tipos de pregunta

El evaluador soporta `single_choice`, `true_false`, `fill_blank`, `multi_select`, `ordering`, `matching`, `who_said_it`, `to_whom`, `reference_detail`, `negative_choice`, `sequence_choice` y `precision`. Para bancos que representan `fill_blank` como opciones, la UI usa selección y el evaluador compara el ID; `matching` acepta pares de IDs y `ordering` compara la secuencia exacta. Los tipos desconocidos se rechazan durante la importación.

## Verificación

Tests unitarios de validación, evaluación de los tipos complejos, temporizador, dominio, selección equilibrada, deduplicación y respaldo. Build de producción, pruebas de UI con Playwright si el Browser integrado no está disponible, smoke test desktop/móvil, persistencia tras reload y comprobación offline del bundle.
