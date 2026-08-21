# Conexión Bíblica 2026

Aplicación local y offline para entrenar con bancos JSON de Conexión Bíblica.

## Ejecutar

```bash
npm install
npm run dev
```

Para probar la compilación de producción:

```bash
npm run build
npm run preview
```

La aplicación guarda bancos, progreso, sesiones y reportes en IndexedDB. No usa APIs externas, telemetría, analytics ni servicios cloud.

## V1, V2 y Mixto

- **V1 — Clásica** carga los bancos declarados en `public/banks/manifest.json` y mantiene sus IDs y progreso existentes.
- **V2 — Banco Maestro** carga `Banco_Maestro_CB2026.json` como asset local canónico de solo lectura. Su adaptador valida 3,558 IDs únicos: 2,211 de Daniel, 1,347 de Profetas y Reyes, 888 históricas y 2,670 generadas.
- **Mixto** crea un pool virtual con V1 y V2. No copia preguntas ni crea progreso duplicado.

La identidad persistente es `bankId:questionId`. El adaptador V2 conserva dificultad original, banda derivada, respuesta canónica, `FULL_FACT_IDS` y toda la metadata del objeto fuente. Para actualizar V2, reemplaza únicamente el JSON raíz por una revisión válida y vuelve a compilar; el arranque reconcilia los mismos IDs sin borrar progreso.

## Selector de sesiones

El generador ofrece cuatro estrategias:

- **Cobertura sin repetir**: guarda una cola por combinación de filtros y no repite hasta agotar el pool. Un pool de 120 con tandas de 50 produce 50, 50 y 20.
- **Aleatoria equilibrada**: Fisher–Yates con selección por bancos, fuentes y capítulos.
- **Bloques secuenciales**: permite elegir explícitamente el bloque 1, 2, etc.
- **Adaptativa**: prioriza falladas, lentas, difíciles y dominio bajo.

Los ciclos y la ronda activa se guardan en IndexedDB. Recargar restaura los mismos IDs, cursor y respuestas ya registradas.

## Persistencia y respaldos

IndexedDB v2 añade `coverageCycles` y `activeRound` mediante upgrade transaccional. El progreso V1 existente no se elimina. Los respaldos actuales usan `backupVersion: "2.0"`; los respaldos 1.0 siguen siendo aceptados y se migran en memoria antes de restaurar.

V2 se entrega como asset de Vite y queda en caché después de cargarse. El service worker `conexion-biblica-shell-v4` conserva el shell y los assets locales para uso offline.

## Verificación

```bash
npm run test
npm run lint
npm run typecheck
npm run build
```

## Despliegue en Vercel

El sitio publicado es https://conexion-biblica-2026.vercel.app (proyecto `conexion-biblica-2026`). No está conectado a GitHub, así que se despliega manualmente con la CLI:

```bash
npx vercel login                                       # solo la primera vez
npx vercel link --project conexion-biblica-2026 --yes  # vincula al proyecto existente (una vez)
npm run deploy                                         # construye y publica en producción
```

Si `vercel link` no encuentra el proyecto por nombre, omítelo y ejecuta `npx vercel --prod`, eligiendo el proyecto existente `conexion-biblica-2026` cuando lo pregunte.

Después de desplegar, recarga con Ctrl+Shift+R. Si el navegador sigue mostrando bancos viejos, limpia los datos del sitio (DevTools → Application → Clear site data) para forzar el service worker `conexion-biblica-shell-v3`.
