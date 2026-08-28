# Diseño: reautoría competitiva total del banco Conexión Bíblica 2026

Fecha: 2026-08-28  
Estado: aprobado por el usuario  
Alcance: Daniel 1–12 (RVR1995), *Profetas y Reyes* 39–44 y la plataforma de entrenamiento

## Objetivo

Sustituir el banco actual de 12,000 preguntas por un banco de preparación competitiva que examine conocimiento real del material oficial y no reconocimiento de citas, páginas o plantillas. La redacción será realizada y revisada por agentes de IA a partir del material local. El código se limitará a compilar, validar y publicar los registros; no redactará preguntas mediante plantillas masivas.

El resultado debe conservar 12,000 preguntas útiles, ofrecer rondas de 100 con la mezcla vigente y entrenar recuperación precisa, comprensión narrativa, relaciones causales, secuencias, personajes, discursos, símbolos, profecías y enseñanzas de *Profetas y Reyes*.

## Diagnóstico que motiva el reemplazo

La medición del banco vigente encontró:

- 9,000 enunciados que comienzan con «Según…»;
- 4,940 enunciados que convierten páginas o párrafos de *Profetas y Reyes* en parte de la pregunta;
- 568 V/F falsas que colocan una afirmación verdadera de otro pasaje bajo una referencia incorrecta;
- 3,000 preguntas contextuales construidas principalmente como variaciones de completar;
- cuatro variantes mecánicas por hecho, aunque el hecho no siempre admite cuatro evaluaciones pedagógicamente distintas.

Estos patrones se eliminarán, no se maquillarán.

## Autoridad de las fuentes

La única autoridad semántica será el material oficial local:

1. Daniel 1–12 en Reina-Valera 1995.
2. *Profetas y Reyes*, capítulos 39–44, en el PDF suministrado.

Fuentes web oficiales o cuestionarios históricos solo orientarán el estilo competitivo. No podrán introducir respuestas, interpretaciones o datos que no estén respaldados por el material local.

## Principios editoriales obligatorios

Cada pregunta deberá cumplir simultáneamente estas reglas:

1. Ser comprensible sin mostrar capítulo, versículo, página o párrafo en el enunciado.
2. Evaluar un conocimiento relevante: hecho, personaje, acción, motivo, consecuencia, secuencia, discurso, contraste, símbolo, número, profecía o enseñanza.
3. Tener una respuesta inequívoca y una evidencia textual suficiente.
4. Mantener la cita y el fragmento probatorio ocultos hasta después de responder.
5. Usar lenguaje natural, preciso y competitivo; se prohíben las fórmulas «según el párrafo», «según Daniel X» y equivalentes como mecanismo de dificultad.
6. Usar distractores plausibles, paralelos y de la misma categoría semántica que la respuesta.
7. Evitar pistas por longitud, gramática, especificidad, repetición o posición.
8. No trasladar una declaración verdadera entre capítulos para volverla falsa.
9. No depender de una negación trivial como única diferencia de una V/F falsa.
10. No duplicar una pregunta mediante cambios cosméticos.
11. No inferir intenciones, causalidad, cronología o doctrina que la fuente no afirme o sostenga de manera inequívoca.
12. Redactar explicaciones que indiquen por qué la respuesta es correcta sin revelar contenido fuera del alcance oficial.

## Arquitectura de autoría

### Unidades editoriales

El corpus se dividirá en 18 unidades independientes:

- Daniel 1 a Daniel 12: una unidad por capítulo.
- PR39 a PR44: una unidad por capítulo.

Cada unidad tendrá un archivo de autoría legible, versionable y revisable. Los agentes recibirán propiedad editorial no superpuesta por unidad y no modificarán el compilador ni los archivos de otras unidades.

### Registro canónico de pregunta

Cada registro incluirá como mínimo:

- `id` estable y único;
- `source_unit` y referencia exacta;
- `prompt`;
- `question_type`;
- `subtype` o habilidad evaluada;
- opciones y respuesta correcta cuando corresponda;
- `evidence_excerpt`;
- explicación posterior a la respuesta;
- dificultad;
- etiquetas de personaje, tema y profecía cuando apliquen;
- `fact_id` o grupo semántico para impedir repeticiones dentro de una ronda;
- estado y huella de auditoría de IA.

Las referencias y la evidencia son metadatos de comprobación y retroalimentación, no pistas visibles antes de contestar.

### Papel del código

El código podrá:

- validar el esquema;
- comprobar conteos, unicidad y distribución;
- detectar patrones prohibidos;
- validar que la evidencia respalda la respuesta;
- detectar respuestas filtradas en el enunciado;
- compilar los archivos editoriales en shards públicos;
- generar reportes reproducibles;
- seleccionar y mezclar preguntas durante una sesión.

El código no podrá redactar enunciados, explicaciones o distractores mediante plantillas repetidas para completar el cupo.

## Taxonomía competitiva

El banco cubrirá, según la disponibilidad real de cada unidad:

- recuerdo factual: quién, qué, dónde, cuándo y cuánto;
- hablante y destinatario;
- motivo, propósito y consecuencia;
- orden y secuencia de acontecimientos;
- identificación desde una descripción significativa;
- relaciones entre personas, reyes, reinos, decretos y acontecimientos;
- palabras o expresiones relevantes;
- comparación y contraste;
- símbolos, visiones e interpretaciones;
- períodos, números y detalles proféticos;
- argumentos, advertencias, principios y lecciones explícitas de PR39–44;
- integración entre Daniel y *Profetas y Reyes* únicamente cuando ambas fuentes respalden la relación.

No se impondrá el mismo número de subtipos a todos los capítulos. La cobertura seguirá el contenido real para evitar preguntas artificiales.

## Familias visibles y composición de rondas

La interfaz conservará tres familias visibles:

### Selección: 45 por ronda

Incluirá una mezcla de recuerdo directo, relaciones, causa/consecuencia, secuencia, hablante/destinatario, comparación, símbolos, profecía y síntesis. Cada pregunta tendrá cuatro opciones paralelas y una sola defendible.

### Completar: 30 por ronda

Ocultará una palabra o expresión significativa dentro de suficiente contexto. No evaluará partículas irrelevantes ni fragmentos ambiguos. Las opciones deberán encajar gramaticalmente y pertenecer al mismo campo semántico.

### Verdadero/falso: 25 por ronda

Mantendrá equilibrio aproximado entre verdaderas y falsas. Una falsa modificará un solo dato local —persona, acción, objeto, lugar, número, secuencia o consecuencia— y seguirá siendo plausible. Se prohíben las falsedades construidas con hechos de otro capítulo atribuidos a una cita visible.

Cada ronda de 100 deberá contener exactamente 45 selecciones, 30 completar y 25 V/F, sin repetir `fact_id`.

## Volumen y cobertura

El objetivo contractual continúa siendo 12,000 preguntas aceptadas. El número no autoriza relleno. Si un registro falla la revisión, será reemplazado por otro conocimiento verificable; no se suavizará el criterio para conservar el conteo.

La distribución deberá:

- cubrir las 18 unidades;
- impedir que capítulos extensos o fáciles monopolicen las sesiones;
- reforzar Daniel 7–12 y PR39–44 por su densidad profética y argumentativa;
- incluir dificultad básica, intermedia, avanzada y competitiva;
- mantener una reserva ciega que no aparezca en entrenamiento normal.

## Flujo editorial y auditoría

1. Extraer y fijar paquetes de fuente por unidad desde el material local.
2. Redactar preguntas manualmente mediante agentes, una por una o en lotes pequeños revisables.
3. Ejecutar validaciones estructurales y léxicas.
4. Realizar una segunda revisión semántica independiente que no vea la decisión del autor.
5. Corregir o reemplazar cualquier pregunta dudosa.
6. Ejecutar una revisión adversarial de distractores y ambigüedad.
7. Compilar únicamente registros aprobados.
8. Auditar muestras estratificadas y todos los patrones de alto riesgo.
9. Invalidar la huella de auditoría ante cualquier modificación del contenido.

Una revisión de IA se declarará como revisión de IA. Las 12,000 firmas humanas seguirán pendientes hasta que una persona realmente revise cada registro; nunca se falsificarán.

## Validadores de rechazo obligatorio

La compilación deberá fallar ante cualquiera de estos casos:

- enunciado vacío, duplicado o casi duplicado;
- comienzo prohibido o referencia visible usada como muleta;
- respuesta ausente de la evidencia o evidencia insuficiente;
- más de una opción defendible;
- distractor de categoría incompatible;
- opción correcta revelada por el enunciado;
- explicación contradictoria con la respuesta;
- V/F falsa con más de una alteración o con trasplante de pasaje;
- completar con hueco trivial o ambiguo;
- identificador, referencia o huella inválidos;
- repetición de `fact_id` en una ronda;
- uso de la reserva ciega en entrenamiento normal.

Los errores deberán incluir el identificador y la causa; no habrá reparación silenciosa.

## Aprendizaje y selección de sesiones

El motor de sesiones conservará y comprobará:

- aleatorización independiente de posiciones;
- variación de enunciados y distractores sin repetir el mismo hecho en una ronda;
- prioridad espaciada para errores y respuestas lentas;
- separación antes de reintroducir un error;
- corrección inmediata sin otorgar dominio;
- exclusión de la reserva ciega;
- persistencia y recuperación segura del progreso.

## Verificación de la plataforma

La validación no terminará al compilar el banco. Se probará la aplicación real:

1. pruebas unitarias y editoriales;
2. esquema y compilación completa de las 12,000 preguntas;
3. análisis de duplicados y patrones prohibidos;
4. simulaciones masivas de rondas de 100;
5. pruebas de aprendizaje en varias rondas consecutivas;
6. build y lint;
7. flujos E2E de todos los botones, navegación, teclado, respuesta, corrección, reinicio y persistencia;
8. escritorio y móvil en Chromium, Firefox y WebKit;
9. comprobación del despliegue por contenido y comportamiento.

## Criterios de aceptación

- 12,000 preguntas aceptadas y trazables a las fuentes locales.
- Cero enunciados que dependan de «según capítulo/página/párrafo».
- Cero falsedades por trasplante de otro pasaje.
- Cero duplicados exactos o normalizados y umbral estricto de similitud semántica.
- Cero respuestas filtradas y cero preguntas con más de una respuesta defendible.
- Las 18 unidades y todos los subtipos aplicables tienen cobertura.
- Las rondas cumplen exactamente 45/30/25 y no repiten `fact_id`.
- La reserva ciega permanece ausente del entrenamiento.
- La priorización de errores y lentitud funciona en sesiones consecutivas.
- Todas las pruebas automatizadas, auditorías editoriales, build y flujos E2E pasan.
- Todos los botones y recorridos críticos funcionan en producción.
- Los informes distinguen claramente revisión de IA y revisión humana pendiente.

## Entrega y despliegue

El trabajo se integrará por etapas verificables para evitar publicar un banco parcial. La aplicación continuará usando el banco vigente hasta que el reemplazo completo apruebe los criterios anteriores. Después se actualizarán los artefactos públicos, se desplegará la versión aprobada y se ejecutará nuevamente la matriz crítica contra producción.

No se afirmará perfección absoluta. La entrega informará evidencia medible, cualquier limitación residual y el estado real de la revisión humana.
