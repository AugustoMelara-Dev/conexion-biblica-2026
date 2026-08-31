# V10: cobertura pública total y reserva privada de generalización

Fecha: 2026-08-30  
Estado: diseño aprobado en principio; pendiente revisión de esta especificación  
Alcance: banco V10, compilación, QC, simuladores y despliegue

## Objetivo

Conservar V10, su arquitectura, dificultad, mezcla 45/30/25, simuladores, controles de calidad y despliegue, sin eliminar ni reemplazar contenido público existente.

El resultado mínimo antes de auditar los hechos históricos será:

- 2,217 de 2,217 hechos competitivos representados al menos una vez en el entrenamiento público;
- las 250 presentaciones blind actuales incorporadas al banco público;
- 250 presentaciones blind nuevas, privadas e inéditas, distribuidas en A=100, B=100 y emergencia=50;
- los hechos blind serán hechos ya entrenables, no contenido fuente oculto;
- A, B y emergencia medirán generalización frente a nuevas formulaciones;
- el banco combinado crecerá de 2,468 a 2,718 presentaciones antes de cualquier reincorporación derivada de la auditoría histórica.

La segunda meta es reconciliar exhaustivamente los 2,606 FACT del inventario maestro anterior contra los 2,217 hechos competitivos V10. El ledger principal tendrá 2,606 filas, una por cada FACT histórico. La diferencia aritmética de 389 entre ambos inventarios es solo un delta nominal: no se asumirá que representa el número real de omisiones porque los espacios de identificadores y las granularidades difieren. Las cantidades de hechos representados, fusionados, reincorporados y excluidos serán resultados de la reconciliación. La rareza, dificultad o ausencia histórica no son motivos válidos de exclusión.

## Evidencia canónica

El inventario histórico canónico es `Banco_Maestro_CB2026.json`. Declara 2,606 FACT: 1,486 de Daniel y 1,120 de Profetas y Reyes. V10 usa otro espacio de identificadores, por lo que la auditoría no puede basarse en una resta textual de IDs.

Las fuentes autorizadas continúan siendo:

- Daniel 1–12, RVR1995;
- Profetas y Reyes, capítulos 39–44, en el material local oficial;
- los paquetes fuente V10 y sus fragmentos probatorios.

## Alternativas consideradas

### 1. Mantener privadas las 250 actuales y crear 250 públicas paralelas

Cumpliría la cobertura, pero conservaría como “inéditas” preguntas que ya existen en historial y artefactos de trabajo. También obligaría a redactar nuevas preguntas públicas sin aprovechar el contenido competitivo ya producido.

### 2. Publicar las 250 actuales y crear 250 privadas desde cero — elegida

Convierte todo el contenido existente en entrenamiento, aumenta el banco sin reemplazos y garantiza una reserva editorial realmente nueva. Los nuevos blind conservan los mismos hechos y cambian por completo la presentación.

### 3. Reescribir tanto la versión pública como la privada de los 250 hechos

Ofrecería máxima separación editorial, pero reemplazaría contenido público válido y ampliaría innecesariamente el riesgo y el tiempo. Contradice la restricción de no reemplazar contenido público.

## Arquitectura de contenido

### Entrenamiento público

Las 250 filas actualmente asignadas a `blind_pool` se publicarán como preguntas normales de entrenamiento. No se borrará ninguna de las 2,218 presentaciones públicas existentes. Después de la migración, las 2,468 presentaciones actuales serán públicas y cubrirán los 2,217 hechos V10.

Cada FACT histórico explícito y preguntable que no tenga una presentación pública capaz de exigir específicamente ese detalle añadirá como mínimo una presentación pública nueva y conservará su identidad histórica en el ledger de reconciliación. El total final podrá superar 2,718 presentaciones combinadas y 2,217 hechos; nunca disminuirá.

### Reserva privada

Se redactarán 250 preguntas completamente nuevas para los mismos 250 hechos seleccionados. La asignación será:

- A: 100 preguntas, 45 selección, 30 completar, 25 verdadero/falso;
- B: 100 preguntas, 45 selección, 30 completar, 25 verdadero/falso;
- emergencia: 50 preguntas, 23 selección, 15 completar, 12 verdadero/falso.

Todas tendrán dificultad HARD o EXPERT. Los tres pools serán particiones disjuntas también por hecho: se seleccionarán 250 `fact_id` únicos, 100 para A, 100 para B y 50 para emergencia, sin reutilizar un hecho entre pools. Dentro de cada simulación habrá una sola pregunta por `fact_id`. La distribución por material, capítulo, habilidad, riesgo y dificultad mantendrá el balance competitivo de V10. Así, usar A no expone hechos blind de B y usar A+B no expone los de emergencia.

### Contrato de ineditud

La separación ya no se validará por hechos disjuntos. El nuevo contrato será:

- todo `fact_id` blind debe existir en el entrenamiento público;
- ningún ID o `variant_id` blind puede aparecer en el banco público;
- ningún enunciado blind normalizado puede coincidir con un enunciado público;
- ningún fingerprint editorial de presentación blind puede coincidir con uno público;
- para selección y completar, el conjunto o patrón reconocible de distractores no puede reutilizar el público correspondiente;
- las formulaciones no podrán ser paráfrasis mecánicas que preserven la misma estructura sintáctica;
- la respuesta correcta no podrá sobresalir por longitud, concordancia, precisión o nivel de detalle;
- los distractores se tomarán de hechos cercanos del mismo material y de la misma categoría semántica, sin crear una segunda respuesta defendible;
- la fuente exacta, el fragmento probatorio y el `fact_id` permanecerán trazables en el artefacto privado.

El fingerprint editorial de presentación incluirá la formulación, estructura sintáctica, opciones, distractores y patrones editoriales. Excluirá deliberadamente `fact_id`, respuesta canónica, referencia y fragmento probatorio, porque esos campos deben coincidir entre el entrenamiento y la reserva cuando describen el mismo conocimiento. La coincidencia legítima de una respuesta factual aislada, como un nombre propio, no constituirá filtración.

Además de las comprobaciones exactas, una revisión adversarial evaluará semejanza semántica entre cada variante blind y todas las presentaciones públicas del mismo hecho.

## Reconciliación de los 2,606 FACT

### Método

Se construirá un ledger con una fila por FACT histórico. La correspondencia con V10 se resolverá en este orden:

1. referencia o unidad fuente;
2. fragmento textual exacto o normalizado;
3. proposición atómica examinada;
4. respuesta o dato objetivo;
5. relación semántica: persona, acción, lugar, cantidad, tiempo, causa, consecuencia, secuencia, hablante, destinatario, símbolo o enseñanza explícita.

Un mismo hecho puede haber sido renombrado, fusionado o expresado con otra granularidad. Solo podrá marcarse como `represented_rekeyed` o `represented_merged` si la proposición objetiva histórica está íntegramente preservada y existe al menos una presentación pública que pueda exigir específicamente ese detalle. Que el dato esté implícito en un hecho V10 más amplio no basta. Si el entrenamiento público no prueba ese conocimiento concreto, el FACT se marcará `reincorporated` y se generará al menos una pregunta pública.

### Decisión individual

Cada uno de los 2,606 FACT recibirá exactamente uno de estos resultados:

- `represented_exact`: la misma proposición está preservada y una presentación pública exige específicamente el detalle;
- `reincorporated`: detalle explícito, verificable y razonablemente preguntable; se añade al entrenamiento público;
- `represented_rekeyed`: ya cubierto bajo otra identidad, con proposición íntegra y una presentación pública que exige ese detalle;
- `represented_merged`: integrado en otro hecho V10 sin pérdida de la proposición y con una presentación pública que exige específicamente el detalle histórico;
- `excluded_non_atomic`: fragmento sin proposición independiente o dependiente de anáfora irresoluble;
- `excluded_reference_only`: lista de referencias sin afirmación examinable;
- `excluded_ambiguous`: no admite una sola respuesta aun con el contexto oficial;
- `excluded_source_defect`: error de extracción o errata que no puede afirmarse con seguridad desde la fuente oficial;
- `excluded_out_of_scope`: contenido fuera de Daniel 1–12 RVR95 o PR39–44;
- `excluded_not_factual`: comentario o rótulo sin dato comprobable.

No se permitirá una razón genérica por lote. Cada exclusión tendrá explicación humana específica y evidencia.

### Reportes

Se producirán:

- un ledger JSON exhaustivo y validable por máquinas;
- un CSV filtrable con las 2,606 decisiones;
- un informe Markdown legible con resumen por capítulo, material y razón;
- una sección derivada de casos especiales —reincorporaciones, fusiones, reidentificaciones y exclusiones— cuyo tamaño no se decidirá de antemano;
- una sección separada con todos los hechos reincorporados y sus nuevas preguntas públicas.

Cada fila incluirá como mínimo: FACT histórico, material, capítulo, fuente, texto o soporte, respuesta, hecho V10 relacionado, estado, código de razón, explicación individual, evidencia y pregunta reincorporada cuando corresponda.

## Cambios de compilación y privacidad

El compilador dejará de exigir disyunción entre hechos públicos y blind. En su lugar exigirá cobertura pública total y disyunción de presentaciones. La asignación blind dejará de “extraer” preguntas públicas y pasará a compilar un corpus privado separado.

Los artefactos A, B y emergencia:

- no se escribirán bajo `public/`;
- no serán importados por código cliente;
- no aparecerán en manifiestos públicos, estadísticas, paneles de cobertura, service workers, source maps ni bundles;
- no serán servidos por rutas o APIs públicas;
- se verificarán mediante búsqueda de IDs de presentación, `variant_id`, stems, opciones, distractores, fingerprints editoriales y nombres de pool en el artefacto de producción.

La aplicación pública solo conocerá la cobertura entrenable. La información privada se mantendrá en artefactos de entrega separados y excluidos del despliegue público. No se considerará filtración que `fact_id`, respuesta canónica, fuente o soporte textual coincidan legítimamente con el conocimiento público.

## QC y criterios de aceptación

La compilación fallará si ocurre cualquiera de estos casos:

- menos del 100% de los hechos competitivos aceptados tiene presentación pública;
- un hecho blind no está entrenado públicamente;
- se pierde una pregunta pública preexistente;
- se repite un hecho dentro de una simulación;
- se repite un `fact_id` entre A, B y emergencia;
- una pregunta blind no es HARD/EXPERT;
- se altera la mezcla 45/30/25 o los tamaños A/B/emergencia;
- existe reutilización exacta o reconocible de enunciado, estructura sintáctica, opciones, distractores, patrón de distractores o fingerprint editorial;
- una pregunta tiene más de una respuesta defendible o carece de soporte exacto;
- un dato blind aparece en el frontend, bundle, API, estadísticas o archivos públicos;
- alguno de los 2,606 FACT carece de decisión, evidencia y razón individual;
- un FACT explícito, verificable y preguntable queda excluido por rareza, dificultad o historial.

La verificación final incluirá:

1. auditoría estructural y de hashes;
2. auditoría factual contra la fuente exacta;
3. auditoría semántica y adversarial de preguntas y distractores;
4. revisión de las 2,606 decisiones, del subconjunto derivado de casos especiales y de todas las reincorporaciones;
5. 1,000 simulaciones nacionales con invariantes de tamaño, mezcla, dificultad, unicidad y cobertura;
6. pruebas de repetición espaciada, dominio y errores recurrentes;
7. pruebas unitarias, integración y E2E del sitio;
8. inspección del build y de las rutas desplegadas para detectar filtraciones;
9. verificación en producción de botones, sesiones, navegación, manejo de errores y cobertura pública.

## Despliegue y reversibilidad

La implementación se hará sobre la rama V10 existente. Primero se compilará y verificará localmente; después se revisará el diff completo y se desplegará únicamente con todas las puertas en verde. El despliegue no contendrá los artefactos privados.

La versión previa seguirá identificable por Git y por el deployment actual. No se modificará producción hasta contar con evidencia fresca de compilación, QC, simulaciones, E2E y prueba de no filtración.

## Resultado esperado

El resultado base será:

- 2,468 preguntas públicas existentes, sin eliminaciones;
- 2,217/2,217 hechos V10 entrenables;
- 250 preguntas privadas nuevas sobre hechos entrenables;
- 2,718 presentaciones combinadas antes de reincorporaciones;
- 2,606 decisiones históricas individualizadas y un subconjunto de casos especiales derivado de la evidencia;
- todas las reincorporaciones necesarias añadidas al entrenamiento;
- V10 preservado con su dificultad, mezcla, simuladores, QC y experiencia pública.
