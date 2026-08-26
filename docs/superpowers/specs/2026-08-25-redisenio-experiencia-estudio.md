# Rediseño integral de la experiencia de estudio

Fecha: 2026-08-25

## Objetivo

Transformar Conexión Bíblica 2026 de un tablero denso basado en tarjetas a un espacio de estudio enfocado, legible y rápido. El rediseño debe cubrir todas las pantallas sin alterar bancos, progreso, sesiones, estadísticas, lógica de selección ni funcionamiento offline.

## Problema observado

- La navegación lateral ocupa demasiado ancho y compite con el contenido.
- El selector principal coloca cinco opciones extensas en una sola fila.
- Hay demasiadas superficies con borde y el mismo peso visual.
- Varias pantallas muestran controles avanzados antes de que el usuario los necesite.
- Las acciones principales y secundarias tienen jerarquías similares.
- Las tablas y métricas pierden legibilidad en anchos intermedios.
- El modo de responder preguntas conserva demasiado contexto de navegación y reduce la concentración.
- Los estados de carga usan un panel genérico en lugar de anticipar la estructura real.

## Dirección visual aprobada

La interfaz se comportará como un espacio de estudio sobrio y espacioso.

- Una sola familia de grises fríos y un acento cian moderado.
- Tipografía de interfaz con personalidad, usando fuentes locales o del sistema sin añadir una dependencia remota obligatoria.
- Títulos con mayor presencia y textos descriptivos cortos.
- Máximo tres columnas; dos columnas para contenido con texto extenso.
- Menos tarjetas: usar secciones abiertas, listas y filas cuando no exista una jerarquía real que justifique una superficie elevada.
- Una acción primaria por pantalla; las demás serán secundarias o enlaces de texto.
- Movimiento breve y funcional, respetando `prefers-reduced-motion`.

## Arquitectura visual común

### Navegación

En escritorio se utilizará un riel lateral compacto y colapsable. El estado compacto mostrará iconos con tooltips accesibles; el expandido mostrará también las etiquetas. La selección activa tendrá contraste suficiente sin rellenar todo el ancho.

En móvil se usará una barra inferior para las cuatro áreas principales: Inicio, Practicar, Progreso y Más. El menú Más contendrá Bancos, Historial y Revisión. Durante una ronda se ocultará la navegación global.

El selector de banco dejará de vivir permanentemente en la barra lateral. Se mostrará como un control contextual en Inicio y Practicar, con acceso secundario desde Bancos.

### Contenedor y ritmo

- Ancho de lectura general: máximo aproximado de 72 rem.
- Ancho del quiz: máximo aproximado de 48 rem.
- Separación entre secciones: 2–3 rem según jerarquía.
- Padding móvil mínimo: 1 rem; escritorio: 2 rem.
- Los bloques no deben depender de anchuras fijas que produzcan saltos de texto excesivos.

### Encabezados de página

Cada pantalla tendrá el mismo patrón:

1. Contexto breve o etiqueta opcional.
2. Título claro en una sola línea cuando sea posible.
3. Descripción de máximo dos líneas.
4. Una acción primaria alineada al final en escritorio y a ancho completo en móvil.

### Componentes compartidos

- `PageHeader`: título, descripción y acción primaria.
- `SectionHeader`: título de sección, ayuda breve y acción secundaria opcional.
- `MetricStrip`: métricas compactas sin convertir cada número en una tarjeta.
- `EmptyState`: explicación, siguiente acción y ausencia de datos claramente diferenciada de un error.
- `Skeleton`: formas equivalentes al contenido de cada pantalla.
- `FocusShell`: contenedor sin navegación para quiz y transiciones de ronda.

Los componentes existentes de botón, tarjeta, badge y tabla conservarán su API siempre que sea posible. Sus estilos base se ajustarán para reducir bordes, mejorar estados de foco y unificar alturas.

## Pantallas

### Inicio

La cabecera mostrará el objetivo de estudio y una única acción: continuar o empezar una ronda.

El banco activo se presentará en un bloque maestro–detalle:

- Columna izquierda: lista compacta de perfiles.
- Columna derecha: nombre, propósito, cantidad de preguntas y advertencias del perfil seleccionado.
- En móvil: selector desplegable seguido del detalle.

Debajo aparecerán una franja de cuatro métricas y dos bloques principales: avance por fuente y siguiente recomendación. La tabla por capítulo y los detalles de debilidad quedarán en una segunda jerarquía, con acceso a Progreso.

### Practicar

Los tres modos —Aprender, Repaso inteligente y Simulacro— aparecerán como opciones amplias, máximo tres columnas.

Tras elegir un modo, se mostrarán únicamente los controles esenciales: banco, cantidad y alcance. Los filtros de capítulo, dificultad, tipo, estado, orden y tiempo estarán dentro de «Configuración avanzada».

Un resumen lateral o inferior indicará cuántas preguntas cumplen los filtros y qué ocurrirá al empezar. El botón de inicio permanecerá visible sin tapar contenido.

### Quiz

El quiz usará `FocusShell` y ocultará navegación, importación y estadísticas.

- Barra superior: salir, progreso y tiempo.
- Referencia y tipo como metadatos discretos.
- Pregunta con ancho de lectura limitado.
- Opciones grandes, con separación suficiente y estados seleccionada/correcta/incorrecta inequívocos.
- En Aprender, la explicación aparecerá después de responder sin desplazar bruscamente la pregunta.
- Acción siguiente fija en móvil y alineada al final en escritorio.

### Resultados

La primera vista responderá tres preguntas: cómo fue la ronda, dónde se falló y qué conviene hacer ahora.

Se mostrará una métrica principal, una franja secundaria y una recomendación. La lista completa de respuestas quedará debajo y podrá filtrarse por incorrectas. «Repasar errores» será la acción primaria cuando existan errores; repetir o configurar otra ronda serán secundarias.

### Bancos

Los bancos aparecerán en una lista o tabla adaptable con nombre, perfil, fuente, preguntas y estado. Se podrá buscar y filtrar sin abrir tarjetas individuales.

La importación será una acción secundaria en la cabecera. Las restricciones de V2, V3 y V4 se explicarán cerca de la acción afectada, no repetidas en cada fila. En móvil cada fila se convertirá en un bloque de dos niveles, sin scroll horizontal obligatorio.

### Progreso y estadísticas

La parte superior mostrará tendencia, precisión, tiempo y cobertura mediante `MetricStrip`. Los puntos débiles y la recomendación ocuparán el primer bloque analítico.

Las tablas por fuente, capítulo y tipo estarán separadas mediante pestañas o un selector. No se mostrarán simultáneamente. Los números usarán cifras tabulares y las gráficas mantendrán etiquetas visibles sin depender solo del color.

### Historial

Las sesiones se mostrarán en filas ordenadas cronológicamente con modo, fecha, precisión, duración y banco. Los filtros serán compactos y permanecerán cerca de la lista. El detalle de una sesión se expandirá en contexto o en un panel lateral, evitando una pared de tarjetas.

### Revisión

La pantalla empezará con la cola recomendada y un botón para practicarla. Los filtros por motivo, capítulo y familia estarán en una barra secundaria.

Las preguntas se mostrarán como filas con referencia, familia, estado y acciones. La explicación completa se abrirá bajo demanda. La interfaz distinguirá entre preguntas difíciles, falladas, favoritas y reportadas sin saturar cada fila con badges.

## Estados transversales

### Carga

Se usarán esqueletos con la silueta real de la pantalla. El mensaje «Preparando tus bancos» podrá acompañar la primera carga, pero no ocupará un panel aislado.

### Vacío

Cada pantalla explicará por qué no hay datos y ofrecerá una acción relevante: comenzar una ronda, cambiar filtros o importar un banco.

### Error

Los errores de almacenamiento o bancos aparecerán como alertas inline, con lenguaje directo y una recuperación específica. La existencia de un error no ocultará las áreas que aún funcionan.

### Offline y actualización

Se conservará el indicador de guardado local, pero será discreto. La actualización del service worker, el reemplazo de bancos por huella y la preservación de IndexedDB no cambiarán.

## Responsive

- Menos de 640 px: una columna, barra inferior, acciones primarias de ancho completo y quiz con acción fija.
- De 640 a 1023 px: una o dos columnas según longitud del contenido; navegación compacta.
- Desde 1024 px: riel lateral, dos columnas principales y tres solo para opciones breves.
- Desde 1440 px: aumentar aire exterior, no el número de columnas.

No habrá cinco columnas de selección ni tarjetas con títulos partidos en cuatro o más líneas.

## Accesibilidad

- Navegación completa por teclado y foco visible.
- Objetivos táctiles de al menos 44 px en controles primarios.
- Contraste WCAG AA para texto y estados interactivos.
- `aria-current`, nombres accesibles y relaciones entre ayuda y controles.
- Estados correctos e incorrectos comunicados con texto e icono, no solo color.
- Tablas con encabezados y alternativa apilada legible en móvil.
- Enlace «Saltar al contenido» al inicio de la página.

## Compatibilidad y límites

- No se modificará el modelo de dominio ni el formato de los bancos.
- No se borrarán ni migrarán datos del usuario.
- No se añadirán dependencias visuales salvo que una carencia verificable lo justifique.
- Se mantendrán modos claro y oscuro.
- El rediseño no incluirá autenticación, sincronización en nube ni nuevas funciones de concurso.

## Validación

La implementación deberá conservar las pruebas unitarias y E2E existentes y añadir pruebas dirigidas para navegación responsive, configuración progresiva y modo concentración.

La validación renderizada cubrirá como mínimo:

- Inicio, Practicar, Bancos, Progreso, Historial y Revisión.
- Quiz y Resultados con datos representativos.
- Escritorio aproximado de 1440 × 900.
- Móvil aproximado de 390 × 844.
- Tema oscuro y una comprobación de tema claro.
- Consola sin errores relevantes.
- Navegación por teclado de los controles principales.

## Criterios de aceptación

1. Ninguna pantalla principal presenta cinco tarjetas de contenido en una fila.
2. El selector de banco es legible a 1024 px sin títulos huérfanos ni advertencias deformadas.
3. El quiz oculta la navegación global y mantiene pregunta, opciones y acción principal dentro de un ancho de lectura cómodo.
4. Los controles avanzados de práctica permanecen ocultos hasta solicitarlos.
5. Las listas de Bancos, Historial y Revisión son escaneables y no requieren scroll horizontal en 390 px.
6. Cada pantalla tiene una acción primaria inequívoca y estados de carga, vacío y error coherentes.
7. La interfaz funciona con teclado, foco visible y contraste suficiente.
8. El progreso, las sesiones y las preferencias existentes sobreviven al rediseño.
9. Las pruebas automatizadas, lint y build terminan sin errores.
10. La revisión visual en escritorio y móvil no muestra solapamientos, recortes ni texto excesivamente comprimido.
