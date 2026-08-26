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

La aplicación guarda bancos, progreso, sesiones y reportes en IndexedDB. No requiere login, no usa APIs externas, telemetría, analytics ni servicios cloud.

## Banco activo V6

La experiencia recomendada usa el banco **V6 — Aprendizaje competitivo**:

- 5,000 preguntas GOLD verificadas: 1,500 de completar, 1,250 de Verdadero/Falso y 2,250 de selección única.
- 1,851 hechos atómicos con variantes por `fact_id`, sin repetir el mismo hecho en una ronda normal.
- Rondas competitivas de 100 con mezcla 30/25/45 y al menos 18 trampas contextuales.
- Recuperación espaciada, métricas de primer intento, seis horas, día siguiente, contextual y ciega.
- Reservas ciegas A, B y de emergencia que no aparecen durante el entrenamiento normal.

Los 14,000 candidatos V5 y los bancos V1–V4 se conservan para trazabilidad y compatibilidad; no se cuentan como preguntas GOLD activas.

## Bancos históricos y Mixto

- **V1 — Clásica** carga los bancos declarados en `public/banks/manifest.json` y mantiene sus IDs y progreso existentes.
- **V2 — Banco Maestro** carga `Banco_Maestro_CB2026.json` como asset local canónico de solo lectura. Su adaptador valida 3,558 IDs únicos: 2,211 de Daniel, 1,347 de Profetas y Reyes, 888 históricas y 2,670 generadas.
- **V3 — Preparación 4 días** contiene un banco curado de 500 preguntas por familias: 28 por cada capítulo de Daniel 1–12, 27 por cada capítulo de Profetas y Reyes 39–44 y 2 integradoras. Incluye explicación, referencia, trampa y pista de memoria.
- **V4 — Banco Curado** ofrece cobertura amplia a partir del Banco Maestro, con preguntas aprobadas o reparadas y trazabilidad de cada decisión de curación.
- **Mixto curado** crea un pool virtual con V1, V3 y V4; V2 queda excluido por diseño. No copia preguntas ni crea progreso duplicado.

### Perfiles de banco

- **V4 — Banco Curado:** cobertura amplia recomendada.
- **V3 — Preparación intensiva de cuatro días.**
- **V2 — Fuente técnica auditable:** no participa en Mixto curado.
- **Mixto curado:** combina V1, V3 y V4 sin iniciar preguntas V2.

Regenerar y auditar V4:

```bash
npm run build:v4
npm run audit:v4
```

La identidad persistente es `bankId:questionId`. El adaptador V2 conserva dificultad original, banda derivada, respuesta canónica, `FULL_FACT_IDS` y toda la metadata del objeto fuente. Para actualizar V2, reemplaza únicamente el JSON raíz por una revisión válida y vuelve a compilar; el arranque reconcilia los mismos IDs sin borrar progreso.

## Selector de sesiones

El generador presenta tres experiencias principales:

- **Aprender**: feedback inmediato, explicación, referencia y pista; repetir mejora el dominio sin afectar simulacros.
- **Repaso inteligente**: prioriza familias débiles y agota redacciones no vistas antes de reciclar.
- **Simulacro**: usa presión de tiempo y feedback diferido; su precisión y récords se calculan aparte.

El generador ofrece cuatro estrategias:

- **Cobertura sin repetir**: guarda una cola por combinación de filtros y no repite hasta agotar el pool. Un pool de 120 con tandas de 50 produce 50, 50 y 20.
- **Aleatoria equilibrada**: Fisher–Yates con selección por bancos, fuentes y capítulos.
- **Bloques secuenciales**: permite elegir explícitamente el bloque 1, 2, etc.
- **Adaptativa**: prioriza familias falladas, lentas, antiguas y de dominio bajo.

El selector de bloques usa numeración visible desde 1. Si un índice queda fuera de rango, la aplicación no lo convierte silenciosamente en el último bloque.

## Ruta rápida de 4 días

La V3 distribuye el material así:

- **Día 1:** Daniel 1–3 y Profetas y Reyes 39 — recuerdo activo y anclas numéricas.
- **Día 2:** Daniel 4–6 y Profetas y Reyes 40–41 — intercalado entre ambos libros.
- **Día 3:** Daniel 7–9 y Profetas y Reyes 42–43 — comparación de símbolos y repaso de errores.
- **Día 4:** Daniel 10–12 y Profetas y Reyes 44 — recuerdo activo y simulacro final.

Cada día inicia una sesión de 50 preguntas con cobertura sin repetir; también puedes usar el generador manual para practicar por capítulos, dificultad o bloques.

Los ciclos y la ronda activa se guardan en IndexedDB. Recargar restaura los mismos IDs, cursor y respuestas ya registradas.

## Persistencia y respaldos

IndexedDB v2 añade `coverageCycles` y `activeRound` mediante upgrade transaccional. El progreso V1 existente no se elimina. Los respaldos actuales usan `backupVersion: "2.0"`; los respaldos 1.0 siguen siendo aceptados y se migran en memoria antes de restaurar.

Los bancos se entregan como assets locales fragmentados por capítulo. El service worker `conexion-biblica-shell-v8` elimina automáticamente cachés anteriores durante la activación, por lo que una recarga normal basta para recibir una versión nueva sin borrar los datos de navegación ni el progreso.

## Verificación

```bash
npm run test
npm run lint
npm run typecheck
npm run build
npm run test:e2e
```

## Despliegue en Vercel

El sitio publicado es https://conexion-biblica-2026.vercel.app (proyecto `conexion-biblica-2026`). El repositorio también genera previews de Vercel para cada pull request. Si la promoción automática de `main` no está disponible, se despliega manualmente con la CLI:

```bash
npx vercel login                                       # solo la primera vez
npx vercel link --project conexion-biblica-2026 --yes  # vincula al proyecto existente (una vez)
npm run deploy                                         # construye y publica en producción
```

Si `vercel link` no encuentra el proyecto por nombre, omítelo y ejecuta `npx vercel --prod`, eligiendo el proyecto existente `conexion-biblica-2026` cuando lo pregunte.

Después de desplegar, una recarga normal activa el service worker nuevo y conserva el historial local.
