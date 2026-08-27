# Entrenamiento Inteligente V8 — diseño

## Propósito

V8 convierte la aplicación en un entrenador de recuperación activa para la competencia del 29 de agosto de 2026. El objetivo medido deja de ser recordar preguntas, posiciones o referencias editoriales y pasa a ser responder correctamente formulaciones nuevas sobre el contenido de `MaterialConexionBiblica (1).pdf`.

La fuente única sigue siendo el PDF local. Para Daniel se conserva exclusivamente RVR1995; para Profetas y Reyes se conserva la terminología del documento. Una referencia puede orientar el contexto o respaldar el feedback, pero nunca será la respuesta evaluada.

## Problemas confirmados

- Las 1,500 variantes `single_choice_contextual` de V7 preguntan en qué versículo, página o párrafo aparece una expresión. Esa familia mide localización editorial y debe reemplazarse completa.
- El reintento inmediato usa otra variante solo cuando existe `metadata.retryVariants`; en el banco actual normalmente vuelve a materializar la misma pregunta y solo baraja opciones.
- Los selectores evitan hechos repetidos de manera adyacente, pero no garantizan un único `fact_id` durante toda la ronda.
- Si una falla ocurre cerca del final, la separación de 8–15 preguntas no cabe y la reparación puede desaparecer de la ronda sin quedar como obligación explícita para la siguiente.
- `Repetir esta tanda` reutiliza exactamente el mismo subconjunto.
- La pantalla de práctica coloca configuración avanzada y diez bloques antes del inicio manual, aumentando la carga visual.
- Una pestaña abierta puede seguir usando un shell anterior hasta recargar, aunque los bancos sean network-first.

## Contrato editorial V8

### Respuestas prohibidas

Ninguna pregunta GOLD podrá tener como respuesta correcta:

- un número de página;
- un número de párrafo;
- una etiqueta `PRxx, p. x, párrafo y`;
- una referencia bíblica como `Daniel 7:19`;
- la ubicación física de una frase dentro del PDF.

Las referencias aparecen únicamente como ancla opcional en el enunciado y como evidencia después de responder. El validador detendrá el build si detecta una respuesta u opciones formadas por referencias.

### Tipos visibles y capacidades

La interfaz mantiene exactamente tres tipos:

- completar con opciones;
- Verdadero/Falso;
- selección única con cuatro opciones.

`Contextual`, `causa`, `consecuencia`, `comparación`, `secuencia`, `diferencia`, `hablante`, `destinatario` e `identificación de escena` son capacidades semánticas, no tipos adicionales.

La antigua familia contextual se reemplaza por selección contextual de contenido. Sus cuatro opciones serán hechos, acciones, personajes, lugares, números, frases o relaciones plausibles. Dos o tres opciones pueden ser verdaderas en otras escenas, pero solo una debe responder al ancla exacta.

### Inventario y expansión

Se volverán a revisar las 1,030 unidades fuente: 357 versículos de Daniel y 673 proposiciones significativas de PR39–44. Cada unidad se clasificará por hechos atómicos y relaciones expresamente sostenidas por el texto.

El objetivo editorial es entre 2,000 y 2,500 hechos y al menos 8,000 preguntas GOLD. La cifra solo puede crecer cuando la fuente permita una capacidad distinta; no se cuentan cambios de posición, paráfrasis cercanas ni preguntas de localización. Los 18,924 candidatos descartados de V7 no se recuperan automáticamente: deben pasar los nuevos filtros de utilidad y relación.

Prioridad de expansión:

1. Daniel 7, 8, 9 y 11.
2. Daniel 10 y 12.
3. PR43 y PR44.
4. PR39–42 y mantenimiento sólido de Daniel 1–6.

Cada hecho tendrá de tres a seis variantes útiles según lo permita la fuente. Las variantes deberán medir capacidades distintas; no bastará cambiar el prefijo del enunciado.

### Auditoría

Cada pregunta debe demostrar:

- respuesta explícita o inequívoca en la cita;
- una única opción aplicable al contexto exacto;
- distractores de la misma categoría y forma gramatical;
- ausencia de conocimiento externo;
- ausencia de respuestas de referencia o ubicación;
- enunciado completo y natural;
- diferencia semántica respecto de las otras variantes del hecho.

Los posibles errores de extracción se verifican visualmente en la página del PDF. La cobertura registra unidades incluidas, hechos seleccionados, candidatos rechazados y exclusiones justificadas.

## Selector inteligente

### Unicidad de hechos

Una ronda normal contiene como máximo una aparición inicial por `fact_id`. La única excepción es una reparación provocada por una respuesta incorrecta en esa misma ronda.

La selección opera por hecho y luego elige la variante menos expuesta que cumpla el tipo y la capacidad necesarios. Nunca selecciona primero preguntas independientes para deduplicarlas después.

### Composición de una ronda de 100

- 30 completar.
- 25 Verdadero/Falso, equilibradas 12/13 entre verdaderas y falsas.
- 45 selección única.
- Al menos 18 selecciones contextuales reales.
- Al menos 10 preguntas de causa, consecuencia, comparación, diferencia, orden narrativo o identificación de escena.
- Sin hechos duplicados entre las 100 apariciones iniciales.

La mezcla adaptativa parte de 60 % hechos o variantes nunca vistos, 20 % errores o reparaciones vencidas, 10 % correctas lentas y 10 % trampas de capítulos débiles. Si una categoría no tiene suficientes elementos, el déficit se redistribuye sin romper la unicidad ni la mezcla de tipos.

### Novedad entre rondas

El ciclo de cobertura se almacena por `fact_id`, no por `question.id`. Después de completar 100 preguntas, `Otra tanda nueva` consume hechos no usados del ciclo antes de volver a ellos. Cuando se agotan los hechos nuevos, se eligen variantes no vistas y luego recuperaciones vencidas.

La repetición exacta seguirá disponible como acción secundaria denominada `Repetir exactamente`, para diagnóstico técnico o decisión deliberada del usuario; no será el CTA principal.

## Reparación y recuperación

Al fallar en Aprender o Repaso inteligente:

1. se muestra la frase correcta, explicación y referencia;
2. se agenda una variante de otra familia después de 8–15 preguntas;
3. se cambian enunciado, distractores y posición de respuesta;
4. si la ronda no tiene espacio, la reparación se persiste como primera prioridad de la siguiente ronda;
5. después de acertar la reparación, se agenda recuperación a 45–90 minutos;
6. siguen recuperaciones a 6–10 horas y al día siguiente;
7. finalmente aparece una variante difícil/contextual o ciega.

Una reparación inmediata se registra como `repaired`, nunca como dominio. El dominio exige recuperaciones en sesiones diferentes, sin pistas, con más de una variante y al menos una evidencia difícil/contextual.

El planificador persistirá una cola explícita con `fact_id`, etapa, `dueAt`, separación mínima, variante anterior y capacidades ya usadas. La selección de una reparación excluye el mismo `variant_id` y, cuando exista alternativa, el mismo tipo.

## Materialización dinámica

La materialización en tiempo de ejecución podrá:

- elegir una plantilla aprobada para la capacidad del hecho;
- elegir distractores compatibles que no hayan formado la combinación reciente;
- barajar A–D con una semilla de sesión;
- mantener exactamente la misma materialización al recargar una ronda activa;
- generar un nuevo `variant_id` de exposición sin perder el `fact_id` original.

No podrá inventar relaciones, parafrasear libremente la fuente ni convertir una pregunta defectuosa en válida solo mediante barajado.

## Interfaz de práctica

La pantalla se reorganiza en este orden:

1. CTA `Entrenar ahora` con el bloque recomendado.
2. Resumen breve: nuevas, vencidas, errores y capítulo prioritario.
3. Aprender, Repaso inteligente y Simulacro.
4. Alcance y cantidad.
5. Plan de 48 horas y modos avanzados dentro de secciones plegables.

Durante la ronda:

- se muestra tipo y propósito, no etiquetas técnicas;
- después de responder se presenta primero el resultado y la frase completa;
- se explica por qué reapareció un hecho: reparación, recuperación vencida, lenta o capítulo débil;
- la referencia se muestra después de responder;
- el footer no tapa contenido en móvil;
- reportar una pregunta conserva la respuesta y el progreso.

Resultados cambia `Repetir esta tanda` por `Otra tanda nueva`. `Repetir exactamente` se mantiene como control secundario y explícito.

## Actualización y compatibilidad

V8 conserva IndexedDB, historial, reportes, favoritos, rondas y evidencias V7. La migración añade la cola de recuperaciones y convierte ciclos por pregunta en ciclos por hecho sin atribuir dominio nuevo.

El service worker comprobará versión al abrir y al recuperar foco. Una actualización activa no interrumpirá una ronda: mostrará `Actualización lista` y se aplicará al terminar o salir. Fuera de una ronda, activará la versión nueva y recargará una sola vez. Nunca exigirá borrar datos de navegación.

## Pruebas de aceptación

### Banco

- cero respuestas u opciones que sean referencias, páginas o párrafos;
- cero preguntas que pidan identificar ubicación editorial;
- cero enunciados incompletos;
- cero ids duplicados y cero preguntas sin respaldo;
- cuotas mínimas por capítulo prioritario, tipo y capacidad;
- revisión semántica duplicada y muestreo adversarial por capítulo y familia;
- hash del PDF local coincidente.

### Algoritmo

- 100 apariciones iniciales implican 100 `fact_id` distintos;
- un error produce otra variante después de 8–15 preguntas;
- la reparación nunca reutiliza el mismo `variant_id`;
- una reparación que no cabe aparece en la siguiente ronda;
- dos tandas consecutivas usan hechos distintos mientras quede cobertura;
- recargar conserva pregunta, opciones, posición y cola;
- reservas ciegas no se filtran a entrenamiento normal.

### Aplicación

- pruebas unitarias, integración, migración y persistencia;
- Playwright en escritorio y 390 px;
- flujo Aprender con error y reparación;
- dos rondas consecutivas de 100 verificando novedad;
- actualización de service worker sin borrar datos;
- build de producción, despliegue y auditoría de los recursos públicos.

## Criterio de finalización

V8 solo se considera terminado cuando el banco regenerado, el selector por hechos, la cola de recuperación, la interfaz simplificada, la migración, las pruebas y la URL pública estén desplegados y verificados. La cantidad publicada se reportará junto con hechos, variantes, candidatos rechazados y cualquier limitación editorial restante.
