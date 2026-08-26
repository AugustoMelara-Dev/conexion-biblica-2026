# Tarea 8 — Estados transversales y accesibilidad

Estado: **DONE**

## Cambios

- `src/App.tsx`: el estado de carga ahora es una región `status` nombrada y ocupada, con un único `h1` para el estado, texto de progreso para lectores de pantalla y tres esqueletos que reservan el encabezado y las dos tarjetas iniciales del resumen. El error de Banco Maestro V2 se conserva como alerta contextual junto al resumen utilizable.
- `src/components/ui/skeleton.tsx`: la pulsación se desactiva con `motion-reduce:animate-none` cuando la persona prefiere reducir el movimiento.
- `src/components/app-states.test.tsx`: cubre anuncio de carga, estructura anticipada, título único y disponibilidad parcial ante fallo de V2.
- `index.html`: añade una descripción concreta para el producto.

## TDD

- RED observado con `npm.cmd test -- src/components/app-states.test.tsx --reporter=dot`: el test de carga falló porque no existía una región `status` con nombre accesible `Preparando tus bancos`.
- GREEN observado con el mismo comando tras el cambio: 1 archivo y 2 pruebas aprobadas.

## Auditoría de accesibilidad

- El estado de carga contiene exactamente un `h1`; el resumen disponible conserva el único `h1` de `DashboardPage`.
- No hay botones sólo con icono dentro de `App.tsx`; los controles de `AppShell` y `FocusShell` se preservan sin modificaciones.
- El aviso de V2 comunica texto explícito (`V1 continúa disponible`), no sólo color.
- Los esqueletos no tienen ancho intrínseco que provoque overflow y heredan tokens de tema claro/oscuro.
- No se identificaron hallazgos que requieran cambios fuera del ownership para Tarea 9.

## Evidencia de verificación

- `npm.cmd test -- src/components/app-states.test.tsx src/components/app-shell.test.tsx src/components/quiz-page.test.tsx --reporter=dot`: 3 archivos, 35 pruebas aprobadas.
- `npm.cmd run typecheck`: aprobado.
- `npm.cmd exec eslint -- src/App.tsx src/components/ui/skeleton.tsx src/components/app-states.test.tsx`: aprobado.
- `npm.cmd run build`: aprobado. Vite mantiene sólo su advertencia no bloqueante de bundle JavaScript mayor a 500 kB.
- `git diff --check`: aprobado.
- QA local con navegador: se observó el `h1` de carga durante la inicialización y, después, el resumen con un único `h1`, navegación principal, enlace de salto y controles nombrados.
