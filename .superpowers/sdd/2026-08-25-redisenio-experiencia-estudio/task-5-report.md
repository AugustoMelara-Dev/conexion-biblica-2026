# Tarea 5 — Quiz enfocado y resultados accionables

Estado: **DONE**

Commit de implementación: `dccc62a101d8047478201b7b9e7ad41d2b7a2bd3` (`feat: crea experiencia de ronda enfocada`)

## Entregado

- `FocusShell` conserva `#main-content`, skip link y salida con Escape; su único landmark `main` ahora se llama **Ronda de estudio**. `QuizPage` usa `article` y `section` interiores, sin anidar otro `main`.
- La ronda concentra metadatos, progreso, tiempo, enunciado, opciones, feedback y acciones auxiliares en un ancho máximo `max-w-3xl` (~48rem). La confirmación queda fija y con área segura en móvil, y vuelve al flujo normal desde `sm`.
- `QuestionRenderer` conserva las selecciones y aporta semántica específica: radiogroup/radio para opción única, fieldsets para texto/múltiple/emparejamiento y lista ordenada con controles nominales para ordenamiento.
- Resultados usa `MetricStrip`, una sola recomendación, «Repasar errores» primario cuando corresponde, «Repetir esta tanda» outline y el filtro accesible «Solo incorrectas» antes de la lista. Se preservaron las demás acciones y los datos de cobertura/ritmo.
- Se añadieron estados de foco, `motion-reduce:transition-none` en opciones y controles de al menos 44 px para las acciones de la ronda. Las pruebas de `FocusShell` y Quiz ahora limpian entre renders para no contaminar casos sucesivos.

## Evidencia TDD y validación

- RED observado para el landmark `main` nombrado y la prioridad de acciones; RED observado para radiogroup/radio; RED observado para el toggle «Solo incorrectas».
- GREEN: `npm.cmd test -- src/components/quiz-page.test.tsx src/components/app-shell.test.tsx src/domain/session-resume.test.ts src/domain/evaluation.test.ts --reporter=dot` → 14/14 pruebas, 3 archivos de prueba.
- `npm.cmd run typecheck` → exit 0.
- ESLint focal sobre los 6 archivos modificados → exit 0.
- `git diff --check` → exit 0.

## Revisión manual de código

- Semántica: un único `main` de ronda, progreso nombrado, feedback con alert, grupos/controles de respuesta etiquetados y toggle expuesto como switch.
- Responsive: la acción final tiene `pb` de reserva, safe-area y ancho completo en móvil; en escritorio vuelve al extremo final. No se ejecutó una inspección visual en navegador; la revisión fue estática sobre clases Tailwind y roles.

## Fix round 1

Estado: **DONE**

- El atajo global Enter ahora excluye todo objetivo interactivo (`button`, campos, enlaces y roles ARIA de control) y usa una guarda síncrona para no registrar ni avanzar dos veces. Fuera de controles conserva la confirmación, incluida la respuesta recién seleccionada.
- Opción única usa roving tabindex y flechas en las cuatro direcciones; el renderer muestra feedback textual de selección y marca la respuesta correcta además del color. Texto, múltiple, ordenamiento y emparejamiento cuentan con pruebas de valor, interacción y disabled; los controles de ordenar y relacionar alcanzan 44 px.
- El cambio de pregunta anuncia el nuevo enunciado mediante `aria-live`, enfoca el `h1` y reserva `scroll-padding-bottom` para la barra final.
- Resultados separa «Resultado» como métrica principal; `MetricStrip` muestra correctas, incorrectas, sin responder y secundarias. La siguiente tanda es outline con errores, el filtro perfecto queda deshabilitado y explica el motivo, y las secciones usan `h2` reales.

Evidencia exacta:

- `npm.cmd test -- src/components/quiz-page.test.tsx src/components/app-shell.test.tsx src/domain/session-resume.test.ts src/domain/domain.test.ts --reporter=dot` → **34/34**, 4 archivos de prueba.
- `npm.cmd run typecheck` → exit 0.
- ESLint focal sobre los archivos afectados → exit 0.
- `git diff --check` → exit 0.

## Fix round 2

Estado: **NEEDS_CONTEXT** — la implementación y la batería focal están verificadas; la compilación completa conserva un único error heredado fuera del alcance de Tarea 5.

- `QuizPage` ahora protege de forma síncrona avance y finalización, cancela toda transición diferida al avanzar, cambiar de pregunta, salir o desmontar, y no permite que un timeout antiguo avance o finalice la ronda después de una acción manual. La guarda de avance se restablece al preparar la nueva pregunta.
- El `main` de `FocusShell` es el contenedor de scroll de la ronda (`h-dvh`, `overflow-y-auto` y reserva inferior); se mantienen el landmark nombrado, skip link, Escape y la reserva de la acción móvil fija.
- Los metadatos cubren exhaustivamente los 12 tipos de pregunta. Las fixtures de resultados incluyen `responseTimeMs` y los cinco tipos antes ausentes tienen pruebas representativas.
- La selección múltiple comunica después de evaluar tanto las opciones correctas como la selección incorrecta mediante texto para tecnologías asistivas y estados visuales; antes del envío no revela respuestas. Para texto, ordenamiento y emparejamiento, el `Alert` de Quiz comunica el resultado global. Los `SelectItem` de emparejamiento también respetan 44 px.
- El filtro de resultados deshabilitado usa cursor de estado no disponible.

Evidencia exacta:

- RED: `npm.cmd test -- src/components/quiz-page.test.tsx src/components/app-shell.test.tsx --reporter=dot` → 7 fallos esperados: contrato de scroll, feedback de múltiple y las cinco etiquetas de tipo.
- GREEN: `npm.cmd test -- src/components/quiz-page.test.tsx src/components/app-shell.test.tsx --reporter=dot` → **30/30**, 2 archivos de prueba.
- `npm.cmd test -- src/components/quiz-page.test.tsx src/components/app-shell.test.tsx src/domain/session-resume.test.ts src/domain/domain.test.ts --reporter=dot` → **43/43**, 4 archivos de prueba.
- `npm.cmd exec -- tsc -p tsconfig.app.json --noEmit` → único residual: `src/components/session-builder-page.test.tsx:73:37`, conversión incompleta a `AppContextValue` (faltan `loading`, `error`, `masterBankError`, `nav` y 24 más). No pertenece a los archivos de Tarea 5.
- `npm.cmd run typecheck` → exit 0, pero es vacuo para referencias: `tsconfig.json` tiene `files: []` y no usa modo build; el chequeo real anterior es el aplicable.
- `npm.cmd run build` → bloqueado por el mismo único residual heredado de `session-builder-page.test.tsx` antes de ejecutar Vite.
- ESLint focal sobre los 6 archivos de producción/prueba modificados → exit 0.
- `git diff --check` → exit 0.

## Fix round 3

Estado: **NEEDS_CONTEXT** — la carrera de transición está cubierta y la batería focal pasa; el único bloqueo de compilación continúa siendo la fixture heredada de otra tarea.

- `QuizPage` usa una generación de transición junto con refs de montaje, salida y clave de pregunta. `submit` captura generación y pregunta antes de `recordAnswer`; al resolver, descarta la continuación si hubo avance manual, cambio de pregunta, salida o desmontaje.
- Avanzar, cambiar de pregunta, salir y desmontar invalidan la generación incluso cuando todavía no existe un timeout. Los callbacks diferidos también validan generación y pregunta antes de ejecutar.
- Escape se captura en `QuizPage`, invalida primero y realiza una única salida. `FocusShell` conserva su fallback para otros children porque ya respeta `event.defaultPrevented`.
- El feedback de selección múltiple conserva el texto accesible de correcta/incorrecta, pero elimina su `role=status` duplicado: el `Alert` de la ronda anuncia el resultado global.

Evidencia exacta:

- RED: el caso aislado de avance durante `recordAnswer` pendiente llegó incorrectamente a «Tercera pregunta diferida». Los casos de desmontaje y Escape también invocaban `onFinish` después de resolver la promesa pendiente.
- GREEN: `npm.cmd test -- src/components/quiz-page.test.tsx -t "no programa el timeout antiguo|ignora una persistencia pendiente|invalida una persistencia pendiente|selección múltiple solo" --reporter=verbose` → **4/4**.
- `npm.cmd test -- src/components/quiz-page.test.tsx src/components/app-shell.test.tsx src/domain/session-resume.test.ts src/domain/domain.test.ts --reporter=dot` → **46/46**, 4 archivos de prueba.
- `npm.cmd exec -- tsc -p tsconfig.app.json --noEmit` → único residual heredado: `src/components/session-builder-page.test.tsx:73:37`, fixture incompleta de `AppContextValue`.
- `npm.cmd run typecheck` → exit 0, vacuo para referencias (`tsconfig.json` tiene `files: []` y no usa modo build).
- `npm.cmd run build` → bloqueado por el mismo único residual heredado antes de Vite.
- ESLint focal sobre los archivos modificados → exit 0.
- `git diff --check` → exit 0.
