# Reporte de tercera corrección focal final

Fecha: 2026-08-26

Estado: **DONE**

Base recibida: `852e60a`

Commit de implementación y pruebas: `6f80beb`

## Resultado

Se resolvieron los tres hallazgos de la última revisión sin modificar bancos, datos, dependencias, migraciones, scoring ni evaluación.

### Autosave después de exit fallido

- El drenaje conserva el snapshot más reciente antes de detener y vaciar la cola.
- Si `onExit` rechaza, Quiz reactiva el autosave y vuelve a persistir ese snapshot; los cambios posteriores de respuestas/índice vuelven a escribirse normalmente.
- El reintento de exit detiene otra vez, descarta snapshots en cola, espera la escritura activa y solo entonces ejecuta el `clear`.
- Un exit exitoso no reactiva el autosave, por lo que no aparece ningún `put` posterior al borrado.
- Se aplicó la misma restauración segura al fallo de finish para mantener simetría con la política de reintento ya existente.

### Random con ocurrencias repetidas

- Un subset explícito ya no pasa por `selectBalancedRandom`, que por diseño deduplica pools elegibles.
- Resultados usa un Fisher–Yates sobre una copia del subset: conserva longitud, claves repetidas y frecuencia exacta, y cambia únicamente el orden.
- `config.count` no recorta el multiconjunto; el resto de la configuración se conserva y solo cambia `strategy` a `random-balanced`.

### Acciones async de Resultados

- Los callbacks de Resultados aceptan Promises reales y `App` las devuelve en lugar de descartarlas con `void`.
- Un guard sincrónico bloquea doble acción; todos los CTA quedan deshabilitados mientras la operación está pendiente.
- El estado pendiente se anuncia con `role=status`; un rechazo se captura y anuncia con `role=alert` sin unhandled rejection.
- Resultados permanece visible ante el fallo y el mismo CTA queda habilitado para reintentar.

## Evidencia TDD RED -> GREEN

Los tests se escribieron y ejecutaron antes de cambiar producción. El primer run mostró exactamente **3 fallos**:

1. Tras exit fallido, IndexedDB permanecía en `currentIndex=0`, `answers=[]` aunque el usuario continuara hasta la segunda pregunta.
2. Random reducía un subset de 5 ocurrencias (`2 + 2 + 1`) a 3 claves únicas.
3. `Repetir esta tanda` no quedaba disabled y aceptaba doble inicio durante una Promise pendiente.

Después de la implementación:

- Focal final (`app-states` + `quiz-page`): **2 archivos, 50/50 passed**.
- Suite global: **37 archivos, 241/241 passed**.

Los tests de exit usan los repositorios reales sobre fake IndexedDB y verifican persistencia posterior, segundo drenaje y `activeRound` final ausente. Los tests de Resultados ejercitan la integración real `App -> ResultsPage -> startRound` con rechazo, doble click y retry.

## Gates finales

| Gate | Resultado |
| --- | --- |
| Focales | **50/50 passed** |
| Suite global Vitest | **241/241 passed** |
| TypeScript | `tsc -p tsconfig.app.json --noEmit`, exit 0 |
| ESLint | `eslint .`, exit 0 |
| Build | Vite 8.2.1, 1,732 módulos, exit 0 |
| `git diff --check` | exit 0; solo avisos CRLF de Git |

El E2E largo no era requerido para esta ola y no se ejecutó. La cobertura focal combina UI integrada y persistencia real en IndexedDB. El build conserva la advertencia conocida, no bloqueante, por un chunk minificado de 536.73 kB.

## Riesgo residual

- Ningún riesgo funcional nuevo identificado en el alcance corregido.
- La carga del banco grande y la advertencia de tamaño de chunk permanecen sin cambios y fuera del alcance de esta ola.
