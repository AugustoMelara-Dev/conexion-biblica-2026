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
