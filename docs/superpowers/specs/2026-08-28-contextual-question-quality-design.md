# Diseño: contextualización competitiva del banco final

Fecha: 2026-08-28  
Estado: aprobado en conversación; pendiente de revisión del documento  
Banco afectado: `BANCO_UNICO_CONEXION_BIBLICA_2026`

## Objetivo

Eliminar los dos límites editoriales identificados en el banco final sin introducir interpretación libre de la fuente:

1. Reemplazar las 353 V/F verdaderas de comprobación léxica (`atomic_presence`) por afirmaciones de identidad contextual completas, únicas y trazables.
2. Reemplazar las 2,928 preguntas contextuales con plantilla genérica por preguntas conscientes del papel sintáctico y semántico del detalle evaluado.

El banco conservará 12,000 preguntas, 3,000 hechos, las cuatro familias actuales, la distribución de dificultad, la reserva ciega y los contratos de sesiones existentes.

## Fuera de alcance

- No se registrarán decisiones como revisión humana.
- No se generarán paráfrasis libres mediante un modelo externo.
- No se modificarán el texto del PDF, las respuestas correctas ni las referencias fuente.
- No se aumentará el banco por encima de 12,000 preguntas.
- No se cambiará la composición de rondas de 100: 30 completar, 25 V/F y 45 selecciones.

## Principios editoriales

Toda pregunta nueva debe cumplir simultáneamente estas condiciones:

- La respuesta aparece literalmente y una sola vez en la unidad o el contexto utilizado como evidencia.
- El texto visible no contiene la respuesta correcta fuera del lugar donde una afirmación V/F necesita declararla.
- No se inventa causalidad, intención, identidad, cronología ni atribución.
- Los distractores mantienen categoría, morfología y ranura sintáctica, y son verdaderos en otra referencia.
- Una inferencia de papel solo se admite cuando puede derivarse de señales deterministas del texto.
- Si el papel no puede determinarse con confianza, se utiliza una formulación contextual conservadora específica de la categoría; nunca se improvisa una relación.

## V/F verdaderas de identidad contextual

### Problema actual

Cuando varios hechos comparten la misma oración fuente, solo uno puede utilizarla como V/F verdadera sin duplicar el enunciado. Los restantes usan formulaciones como “se emplea la forma verbal”, que comprueban presencia léxica y ofrecen poco valor competitivo.

### Diseño

Las afirmaciones exactas y únicas se conservarán. Para los hechos restantes se generará una afirmación de identidad contextual con tres componentes:

1. La referencia fuente.
2. Un fragmento literal donde la respuesta se sustituye por un marcador neutral (`[…]`).
3. Una proposición que identifica el detalle oculto y su papel.

Ejemplo conceptual:

> Según Daniel 10:14, en la escena «lo que ha de […] a tu pueblo», la acción indicada es «sucederle».

La respuesta aparece una sola vez en la proposición, no dentro de la evidencia enmascarada. El enunciado completo puede evaluarse como verdadero o falso y no se limita a afirmar que una palabra “aparece”.

### Papeles admitidos

- `actor`, `recipient` y `named_entity` para personas.
- `origin`, `destination`, `location` y `direction` para lugares.
- `quantity`, `duration`, `order` y `measure` para números.
- `action`, `state` y `change` para verbos.
- `subject`, `object`, `predicate`, `modifier`, `connector_object` y `concept` para términos.
- `cause`, `purpose`, `consequence`, `description` y `formulation` para frases.

Los nombres visibles se traducirán a español natural; los identificadores internos se conservarán para auditoría.

### Contrato de datos

Las preguntas incorporarán:

- `statement_mode: "contextual_identity"`;
- `contextual_role` con uno de los papeles admitidos;
- `truth_source_statement` con la afirmación de identidad completa;
- `context_evidence` con el fragmento literal enmascarado.

`atomic_presence` dejará de ser un modo válido en el banco generado.

## Selecciones contextuales conscientes del papel

### Problema actual

La plantilla “¿qué opción corresponde específicamente a esta escena?” oculta el detalle, pero repite la mecánica de completar y no expresa qué relación debe recuperar el concursante.

### Diseño

Cada hecho recibirá un `contextual_role` derivado de:

- categoría editorial;
- firma de ranura existente;
- palabras inmediatamente anteriores y posteriores;
- preposiciones y conectores explícitos;
- relaciones conservadoras ya extraídas (`cause`, `purpose`, `consequence`, `speaker`, `recipient`).

Las 72 relaciones explícitas existentes conservarán prioridad. Los demás hechos usarán plantillas deterministas por papel, no una plantilla universal.

Ejemplos conceptuales:

- Persona/actor: “¿Quién realiza la acción descrita en «[…] entregó en sus manos…»?”
- Persona/destinatario: “¿A quién se dirige la orden presentada en «dijo el rey a […]»?”
- Lugar/destino: “¿Qué destino completa el movimiento descrito en «vino … a […]»?”
- Número/duración: “¿Qué duración precisa el período descrito en «durante […] años»?”
- Acción: “¿Qué acción mantiene la secuencia exacta de «Daniel […] en su corazón…»?”
- Término/objeto: “¿Qué objeto completa la relación expresada en «la casa del […]»?”
- Frase/causa: se conserva la pregunta causal explícita ya validada.

Todas las preguntas contextuales conservarán `trap_type: "true_in_other_context"`, tres explicaciones individuales y cuatro opciones de la misma ranura.

### Fallback conservador

Cuando no exista un papel más específico, se utilizará una plantilla propia de la categoría:

- persona: “¿Qué personaje completa la relación descrita…?”
- lugar: “¿Qué lugar completa la relación espacial descrita…?”
- número: “¿Qué dato cuantitativo precisa la escena…?”
- acción: “¿Qué acción completa la secuencia descrita…?”
- término: “¿Qué concepto completa la relación literal…?”
- frase: “¿Qué formulación completa la relación literal…?”

Este fallback sigue siendo contextual y específico; la frase genérica actual queda prohibida.

## Componentes y flujo

1. `final_editorial.py` derivará una estructura `ContextualRole` para cada hecho después de seleccionar los 3,000 hechos.
2. El rol alimentará dos renderizadores puros:
   - afirmación V/F de identidad contextual;
   - pregunta de selección contextual.
3. Los renderizadores devolverán texto y metadatos, sin modificar respuestas ni fuentes.
4. La validación adversarial comprobará respaldo literal, ocultamiento, unicidad y opción defendible.
5. `audit-final-bank-deep.py` verificará los nuevos modos y rechazará los antiguos.
6. El banco y los paquetes de auditoría se regenerarán de manera determinista.

## Rechazos y manejo de errores

La generación debe fallar con un mensaje que incluya `fact_id` cuando ocurra cualquiera de estos casos:

- evidencia sin exactamente una ocurrencia de la respuesta;
- evidencia enmascarada que todavía revela la respuesta normalizada;
- rol no admitido;
- afirmación o pregunta visible duplicada;
- distractor incompatible con la firma de ranura;
- afirmación contextual que no puede ser seleccionada correctamente por la revisión adversarial;
- reaparición de `atomic_presence` o de la plantilla contextual genérica.

No habrá reparación silenciosa ni fallback a presencia léxica.

## Estrategia TDD

La implementación seguirá ciclos rojo-verde separados:

1. Prueba que exige cero V/F `atomic_presence` y 1,500 V/F verdaderas únicas.
2. Prueba unitaria de renderizado de identidad contextual para persona, lugar, número, acción, término y frase.
3. Prueba que exige cero apariciones de la plantilla contextual genérica.
4. Pruebas unitarias de clasificación de papeles con casos representativos y fallback conservador.
5. Prueba de ocultamiento: la respuesta no aparece en la evidencia enmascarada.
6. Prueba de unicidad y selección adversarial sobre las 12,000 preguntas.
7. Pruebas de auditoría profunda para los nuevos campos y modos.

Cada prueba se ejecutará primero en rojo por ausencia del comportamiento y después en verde con la implementación mínima.

## Criterios de aceptación

- 12,000 preguntas y 3,000 hechos exactos.
- 3,000 preguntas por familia.
- 1,500 V/F verdaderas y 1,500 falsas.
- `atomic_presence = 0` en verdaderas y falsas.
- Plantilla “¿qué opción corresponde específicamente a esta escena?” = 0.
- 3,000 contextuales con `contextual_role` válido y tres explicaciones de distractores.
- Cero respuestas reveladas en preguntas contextuales.
- Cero duplicados visibles o normalizados.
- Auditoría profunda con cero errores.
- Auditoría competitiva estratificada sin banderas automáticas.
- 27/27 pruebas editoriales y 339/339 pruebas web, o los nuevos totales superiores correspondientes.
- Build, lint y auditoría de producción aprobados.
- Matriz de producción aprobada en Chromium, Firefox y WebKit, escritorio y móvil.

## Despliegue y trazabilidad

Después de la verificación local se actualizarán:

- shards de preguntas y manifiestos públicos;
- índice y paquete exhaustivo de revisión;
- auditoría competitiva;
- informe de revisión IA.

El cambio se versionará en `main`, se desplegará mediante la integración conectada y se comprobarán por contenido los 24 recursos públicos. Las firmas humanas continuarán pendientes y cualquier cambio de contenido invalidará sus huellas anteriores por diseño.
