# Conexión Bíblica 2026

Aplicación web de estudio adaptativo, precisión textual y memoria para **Daniel 1–12** y **Profetas y Reyes 39–44**.

## Estado del banco

- Preguntas creadas: **2082**
- Preguntas válidas: **2033**
- Preguntas corregidas durante la auditoría: **28**
- Preguntas excluidas: **49**
- Cobertura: **514 de 514 unidades**
- Tipos permitidos: seleccionar una respuesta, verdadero/falso y completar frase con opciones
- Funcionamiento: un solo `index.html`, sin backend, sin solicitudes de red y con persistencia local

## Uso

Abre `index.html` directamente en Chrome, Edge o Android. El progreso se guarda en `localStorage`; también puede exportarse e importarse como JSON.

## Desarrollo

```bash
python3 build_full_app.py
python3 tests/static_audit.py
python3 tests/browser_smoke.py
python3 tests/logic_test.py
python3 tests/persistence_test.py
```

También puedes ejecutar `npm test`. Las pruebas de navegador requieren Chromium y Playwright para Python.

## Publicación en Vercel

El repositorio ya incluye `vercel.json` y `.vercelignore`. Vercel debe publicar únicamente el `index.html` de la raíz, sin comando de compilación ni backend.

```bash
vercel --prod
```

La aplicación mantiene su diseño y su banco integrados dentro del HTML. Los iconos SVG de estilo Lucide están incluidos localmente para no depender de CDN ni romper el uso offline.

## Metas por capítulo

| Capítulo | Preguntas | Complejidad | Meta de ronda | Evidencia exigida |
|---|---:|---:|---:|---|
| Daniel 1 | 84 | 80/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 2 | 194 | 83/100 | 98% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 3 | 120 | 86/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 4 | 147 | 84/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 5 | 120 | 82/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 6 | 112 | 93/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 7 | 108 | 84/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 8 | 105 | 83/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 9 | 106 | 85/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 10 | 80 | 82/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 11 | 172 | 77/100 | 98% | Tres rondas en días distintos y una comprobación retrasada |
| Daniel 12 | 50 | 81/100 | 100% | Tres rondas en días distintos y una comprobación retrasada |
| Profetas y Reyes 39 | 144 | 73/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Profetas y Reyes 40 | 101 | 91/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Profetas y Reyes 41 | 92 | 93/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Profetas y Reyes 42 | 76 | 92/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Profetas y Reyes 43 | 128 | 93/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |
| Profetas y Reyes 44 | 94 | 95/100 | 99% | Tres rondas en días distintos y una comprobación retrasada |

## Fuentes y alcance

Las preguntas evaluables se construyen exclusivamente desde los TXT incluidos en `src/`. Los números de página y encabezados duplicados de extracción se excluyen del banco. La numeración técnica de párrafos de Profetas y Reyes 40–44 existe solo para navegación y cobertura estable.

No se declara una licencia sobre los textos fuente incluidos.
