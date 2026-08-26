# Reporte final — V6 Aprendizaje competitivo

Fecha: 26 de agosto de 2026  
Fuente única preservada: `MaterialConexionBiblica (1).pdf`  
Producción: https://conexion-biblica-2026.vercel.app/

## Banco GOLD activo

- Registros V5 preservados: 14,000.
- Reemplazos editoriales V6: 5,000.
- Hechos atómicos: 1,851.
- Promedio: 2.70 variantes por hecho.
- Tipos: 1,500 completar; 1,250 Verdadero/Falso; 2,250 selección única.
- Balance V/F: 625 verdaderas y 625 falsas.
- Dificultad: 1,987 medias; 1,311 difíciles; 1,702 expertas.
- Reserva ciega: A 100 hechos; B 100; emergencia 78; pools disjuntos.
- SILVER conservadas para edición: 2,136.
- Cuarentena fuera de producción: 11,864 candidatos.
- Errores del contrato automático: 0.

## GOLD por capítulo

| Capítulo | GOLD | Capítulo | GOLD |
|---|---:|---|---:|
| Daniel 1 | 220 | Daniel 10 | 200 |
| Daniel 2 | 300 | Daniel 11 | 350 |
| Daniel 3 | 260 | Daniel 12 | 200 |
| Daniel 4 | 300 | PR39 | 280 |
| Daniel 5 | 240 | PR40 | 200 |
| Daniel 6 | 240 | PR41 | 260 |
| Daniel 7 | 350 | PR42 | 200 |
| Daniel 8 | 350 | PR43 | 350 |
| Daniel 9 | 350 | PR44 | 350 |

Cada capítulo prioritario (Daniel 7, 8, 9, 11; PR43 y PR44) contiene exactamente 100 completar, 80 V/F y 170 selección única. Daniel 10, Daniel 12, PR40 y PR42 contienen 200 preguntas cada uno.

## Aprendizaje y protección contra memoria de interfaz

- Toda ronda general V6 de 100 usa 30 completar, 25 V/F y 45 selección.
- Los 25 V/F alternan 12/13 verdaderas y 12/13 falsas.
- Cada ronda incluye al menos 18 trampas contextuales y 10 relaciones, comparaciones, diferencias u escenas.
- Ningún `fact_id` se repite dentro de una ronda normal.
- A/B ciega producen 100 hechos únicos y cumplen la misma mezcla.
- La corrección inmediata queda como `repaired`; no suma dominio.
- Recuperaciones programadas: 8–15 preguntas, 45–90 minutos, 6–10 horas y día siguiente.
- Dominio exige sesiones, variantes y habilidades distintas, recuperación de seis horas, recuperación al día siguiente y al menos una recuperación difícil.
- Métricas separadas: tipo, contextual, primer intento, seis horas, día siguiente, ciega y errores recurrentes.
- Service worker V8 revalida manifiesto y shards y elimina cachés de shell anteriores.

## Auditoría editorial

- Los V/F falsos cambian un solo nombre, número, lugar, acción u otro detalle compatible.
- Completar oculta de una a tres palabras significativas con contexto suficiente.
- Las trampas muestran el texto íntegro alrededor del detalle; cada distractor registra la referencia donde sí es verdadero.
- Se rechazaron secuencias léxicas, sustituciones libres, fragmentos débiles, respuestas sin respaldo y distractores incompatibles.
- Los reemplazos conservan cita, respuesta, explicación, `fact_id`, variante, plantilla y estado GOLD.
- La auditoría estratificada revisa 100 registros de cada capítulo prioritario y 20 de cada capítulo restante.

## Verificación

- Auditoría Python: 13/13 pruebas y contrato de 5,000 sin errores.
- Vitest: 55 archivos, 293/293 pruebas.
- Prueba real de pools ciegos A/B: aprobada.
- ESLint: aprobado.
- TypeScript y build Vite: aprobados; 1,748 módulos.
- Playwright: verificación completa y capturas de escritorio/móvil.
- Producción: se completa tras merge y comprobación pública.

## Evidencia visual

- `04-plan-final-produccion.png`
- `05-feedback-aprendizaje.png`
- `06-progreso-por-hechos.png`
- `07-simulacion-ciega-a.png`
