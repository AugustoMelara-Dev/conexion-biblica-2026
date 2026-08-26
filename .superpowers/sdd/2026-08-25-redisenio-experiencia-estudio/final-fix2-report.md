# Reporte de segunda ola correctiva final

Fecha: 2026-08-26

Estado: **DONE**, con una inestabilidad ambiental de bootstrap E2E documentada en Riesgo residual.

Base recibida: `4844ba5ef79755f1d9213d5744fc362ab430327d`

Commit de implementación y pruebas: `6676560`

## Resultado

Se corrigieron los cuatro hallazgos autorizados de la re-revisión final sin modificar bancos, datos, dependencias, migraciones, scoring ni evaluación.

### Subset exacto desde Resultados y reanudación

- `Repetir esta tanda`, `Otra tanda aleatoria` y `Repasar errores` reconstruyen sus preguntas en el orden de `session.questionKeys`, no desde un nuevo filtrado de las 3,220 preguntas del banco.
- Una ronda rehidratada puede terminar y arrancar inmediatamente una acción de Resultados sin depender de `lastRound` ni duplicar la sesión guardada.
- Un subset explícito siempre conserva todas sus preguntas aunque `config.count` sea menor. La acción aleatoria cambia la estrategia a `random-balanced` y el orden, pero conserva exactamente el conjunto recibido y el resto de la configuración.
- Resultados ya no se descarta antes de confirmar que la nueva ronda se pudo persistir; una acción fallida no deja la pantalla en no-op.

### Drenaje seguro de autosave

- Quiz conserva la Promise de escritura activa, invalida el último snapshot y descarta cualquier snapshot en cola antes de finish/exit.
- Finish/exit esperan la escritura ya iniciada antes de delegar el borrado de `activeRound`; ningún `put` en cola puede ejecutarse después del `clear`.
- Los rechazos del write drenado quedan absorbidos por la ruta accesible existente y no producen unhandled rejection.
- Escape no puede iniciar exit mientras finish ya tomó el guard; finish/exit mantienen bloqueo de doble acción y sus reintentos existentes.

### CTA de Cola de Revisión

- `Practicar esta cola` espera el callback async, usa guard sincrónico contra doble click, deshabilita el control mientras está pendiente y anuncia el fallo con `role=alert`.
- Un rechazo no se descarta con `void`; el botón se rehabilita y el reintento recibe nuevamente la cola exacta.

### Atomicidad reporte + flag

- El reporte y `progress.reported=true` se escriben en una sola transacción IndexedDB `readwrite` sobre los stores `reports` y `progress`.
- La serialización por store preserva las actualizaciones concurrentes de respuesta/reporte.
- React se actualiza solo después del commit. Un abort en el segundo write no deja reporte huérfano ni progreso parcial; el retry genera un único reporte.

## Evidencia TDD RED -> GREEN

- Resultados/CTA RED inicial: **4 fallos esperados** (repeat rehidratado no-op, random 3,220 en vez de 2,138, errores fuera de orden y doble CTA); GREEN combinado: **25/25**.
- Autosave/atomicidad RED inicial: **5 fallos esperados** (resurrección en exit, finish antes del drain, rechazo drenado, Escape solapado y reporte huérfano); GREEN combinado: **45/45**.
- Endurecimiento final de subset exacto con `config.count=20`: RED **2 fallos** (repeat/random truncados a 20); GREEN **9/9**, conservando 2,138.
- Focal final conjunto: **5 archivos, 74/74 passed**.

## Gates finales

| Gate | Evidencia |
| --- | --- |
| Focales | 5 archivos, **74/74 passed** |
| Suite global Vitest | 37 archivos, **238/238 passed** |
| TypeScript | `tsc -p tsconfig.app.json --noEmit`, exit 0 |
| ESLint | `eslint .`, exit 0 |
| Build | Vite 8.2.1, 1,732 módulos, exit 0 |
| E2E completo verde | **20 passed, 4 skipped, 0 failed** (5.6 min), ejecutado tras la implementación funcional |
| E2E final adicional | 14 passed, 4 skipped, 6 timeouts de bootstrap; todos quedaron en `Preparando tus bancos`, antes de entrar al flujo probado |
| Rerun móvil diagnóstico | 3 passed, 5 timeouts intermitentes en el mismo bootstrap (5.1 min) |
| `git diff --check` | exit 0; solo avisos CRLF de Git |

El build conserva la advertencia previa, no bloqueante, por un chunk minificado de 535.73 kB.

## Browser QA focal

- En la cola V4 de 2,138 preguntas se inyectó una única falla reversible al persistir `activeRound`: apareció el mensaje accesible `No se pudo iniciar la cola...`, no hubo doble inicio y el retry abrió `Pregunta 1 de 2138`.
- Se terminó una ronda rehidratada de 2,138 claves y desde Resultados se accionó `Otra tanda aleatoria`.
- La lectura posterior del snapshot real de IndexedDB devolvió: `length=2138`, `originalLength=2138`, `exactSet=true`, `orderChanged=true`, `strategy=random-balanced`, `currentIndex=0`.
- Consola final: **0 errores, 0 warnings**. Navegador y servidores 4173/4174 quedaron cerrados.
- Artefactos de QA y E2E permanecen fuera del repositorio bajo `%TEMP%\conexion-biblica-final-qa` y `%TEMP%\conexion-biblica-playwright`.

## Riesgo residual

- El rerun E2E final sufrió degradación intermitente al cargar el banco JSON de 4.8 MB: la captura, el árbol accesible y los traces muestran únicamente el skeleton `Preparando tus bancos`; algunos casos idénticos pasaron entre timeouts y el full run anterior terminó 20/4. No hay una aserción de producto fallida ni relación observable con los archivos cambiados, pero el bootstrap móvil bajo carga sigue siendo un riesgo ambiental conocido.
- No se amplió el alcance hacia carga de bancos, configuración E2E o timeouts porque están fuera de ownership y la suite global, build, QA focal y un full E2E ya aportan evidencia funcional directa.
