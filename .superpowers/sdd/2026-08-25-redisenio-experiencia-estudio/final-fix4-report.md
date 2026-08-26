# Reporte de cuarta corrección focal final

Fecha: 2026-08-26

Estado: **DONE**

Base recibida: `a040e3b01943f0ccadfb2a61651f0cd10a88a191`

Commit de implementación y pruebas: `862b6f3`

## Causa raíz

`stopAutosaveAndDrain` capturaba el snapshot más reciente, detenía el autosave y esperaba la escritura activa. Sin embargo, mientras esa Promise estaba pendiente, `submit`, Enter y los temporizadores todavía podían cambiar `answers`, `submitted`, `queue` o `index`.

Como el autosave ya estaba detenido, el efecto no actualizaba `latestRoundRef`. Si `onExit` rechazaba, `resumeAutosave` reponía el snapshot capturado antes de la mutación y el cambio realizado durante el drain quedaba fuera de IndexedDB.

## Solución

Se eligió bloquear mutaciones durante finish/exit porque una transición terminal no debe aceptar una respuesta concurrente:

- `submit` y `advance` consultan sincrónicamente los guards `isExitingRef` y `hasFinishedRef` antes de cambiar la ronda.
- El listener de teclado ignora Enter, atajos de opciones y favorita mientras cualquiera de los guards está activo.
- Los timers por pregunta y total se pausan cuando `transitionPending` no es nulo; al fallar la transición se reanudan con el deadline original.
- `QuestionRenderer`, favorita, difícil, reporte y sus controles quedan deshabilitados de forma accesible mientras la transición está pendiente.
- Los handlers mutables conservan además el guard sincrónico para cerrar la ventana anterior al rerender que aplica `disabled`.
- `saveReport` tampoco inicia una escritura nueva durante finish/exit.

Si exit falla, los guards se liberan, el autosave se reactiva y el usuario puede responder normalmente. Si exit tiene éxito, la transición permanece bloqueada hasta desmontar Quiz y no se crea ningún `put` después del `clear`.

## Evidencia TDD RED -> GREEN

El test se escribió antes de cambiar producción y usa repositorios reales sobre fake IndexedDB:

1. Inicia el primer `put` y lo mantiene pendiente con una Promise diferida.
2. Inicia exit y, durante el drain, intenta enviar con Enter y vencer el timeout.
3. Rechaza el primer `onExit`.
4. Envía con Enter después de reanudar, verifica la respuesta en `activeRound` y reintenta exit con `clear` exitoso.
5. Espera una ventana adicional y confirma que no aparece otro write tras el borrado.

RED observado: la respuesta se registraba en UI durante el drain, pero IndexedDB permanecía con `answers=[]` al reanudar.

GREEN:

- Test de carrera aislado: **1/1 passed**.
- Archivo focal Quiz completo: **40/40 passed**.
- Suite global: **37 archivos, 242/242 passed**.

El test también comprueba que radio y Confirmar están semánticamente disabled durante la transición, `recordAnswer` recibe cero llamadas durante drain, el cambio posterior al rechazo sí se persiste y `activeRound` termina ausente sin writes tardíos.

## Gates finales

| Gate | Resultado |
| --- | --- |
| Focal Quiz | **40/40 passed** |
| Suite global Vitest | **242/242 passed** |
| TypeScript | `tsc -p tsconfig.app.json --noEmit`, exit 0 |
| ESLint | `eslint .`, exit 0 |
| Build | Vite 8.2.1, 1,732 módulos, exit 0 |
| `git diff --check` | exit 0; solo avisos CRLF de Git |

El E2E largo no era requerido para esta corrección y no se ejecutó. El build conserva la advertencia conocida, no bloqueante, por un chunk minificado de 537.04 kB.

## Riesgo residual

- Ningún riesgo funcional nuevo identificado dentro del flujo corregido.
- Los deadlines continúan avanzando durante el tiempo real empleado por una transición fallida; al reanudar, un timer ya vencido actuará inmediatamente. Esto preserva la semántica previa del límite de tiempo y evita aceptar mutaciones durante el drain.
