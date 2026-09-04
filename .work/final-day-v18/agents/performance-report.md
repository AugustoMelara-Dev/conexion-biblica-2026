# Handoff - análisis de rendimiento AAH

Estado: DONE

Se analizó únicamente el reporte cxb-final-conexion-biblica-aah-2026_augusto-melara_reporte.pdf (26 páginas, 100 preguntas). La extracción pypdf/pdfplumber concordó en 100 cabeceras. La portada reporta 98/100, 94,480 puntos, 3.72 s promedio y 06:11.787 total.

Hallazgos principales:

- P0 Daniel 9 / R4-Q19: incorrecta, 12.799 s; confusión de secuencia después de 62 semanas.
- P0 Daniel 12 / R5-Q14: incorrecta, 6.981 s; confusión Miguel vs Mesías Príncipe.
- Cuello de botella: R4 (5.119 s promedio); D9 (6.262 s) y D8 (5.505 s) son los bloques Daniel más lentos del mapeo.
- 9 ítems superan 6 s; 7 son correctos y deben tratarse como práctica, no rechazo.
- La lista de unidades personales obligatorias se tomó del spec adjunto; se registró evidencia de página cuando aparece y ausencia explícita cuando no aparece.

Archivos propios:

- .work/final-day-v18/performance/aah-analysis.json
- .work/final-day-v18/performance/aah-analysis.md
- .work/final-day-v18/agents/performance-report.md

Limitaciones:

- Es una sola traza AAH de 100 preguntas; no extrapolar a todo el banco.
- No hay auto-reporte de dudas, confianza, segunda opción, referencias canónicas ni etiquetas PR39-44.
- El mapeo de Daniel a capítulo es por contenido/secuencia y el PR queda PR_UNSPECIFIED.
- No se modificaron bancos ni se hicieron commits.

Verificación ejecutada: pdfinfo; pypdf 6.14.2; pdfplumber 0.11.10; pdftoppm de las 26 páginas y revisión visual de portada, ítems lentos y ambos errores.
