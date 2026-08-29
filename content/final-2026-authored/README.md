# Banco Canónico Autorizado — Conexión Bíblica 2026

Este directorio contiene las 18 unidades del banco de preparación competitiva de Conexión Bíblica 2026 (Daniel 1–12 y Profetas y Reyes 39–44), redactadas y auditadas exclusivamente a partir del material local oficial.

## Estructura de Archivos

- `questions/DAN1.json` a `questions/DAN12.json`: Capítulos 1 al 12 del libro de Daniel (RVR1995).
- `questions/PR39.json` a `questions/PR44.json`: Capítulos 39 al 44 de *Profetas y Reyes* (PDF oficial).

## Esquema Canónico de Pregunta (V10)

Cada registro en `questions/<UNIT>.json` debe cumplir estrictamente con los siguientes campos:

```json
{
  "id": "DAN1-AUTH-0001",
  "source_unit_id": "DAN1-V001",
  "fact_id": "DAN1-V001-F01",
  "family": "single_choice_direct",
  "subtype": "factual_recall",
  "question": "¿Quién sitió a Jerusalén en el tercer año del reinado de Joacim?",
  "options": [
    "Nabucodonosor, rey de Babilonia",
    "Ciro, rey de Persia",
    "Belsasar, rey de los caldeos",
    "Darío el medo"
  ],
  "correct_option": 0,
  "correct_answer": "Nabucodonosor, rey de Babilonia",
  "accepted_answers": ["Nabucodonosor, rey de Babilonia"],
  "explanation": "En el tercer año de Joacim, Nabucodonosor vino a Jerusalén y la sitió.",
  "why_distractors_fail": {
    "Ciro, rey de Persia": "Gobernó en un período posterior.",
    "Belsasar, rey de los caldeos": "Reinó hacia el final del cautiverio babilónico.",
    "Darío el medo": "Gobernó tras la caída de Babilonia."
  },
  "source_ref": "Daniel 1:1",
  "source_quote": "En el tercer año del reinado de Joacim, rey de Judá, vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió.",
  "evidence_excerpt": "vino Nabucodonosor, rey de Babilonia, a Jerusalén, y la sitió",
  "difficulty": "medium",
  "importance": "high",
  "relation_type": "event_participant",
  "option_category": "person",
  "false_mutation": null,
  "blind_pool": null,
  "ai_review": {
    "status": "passed",
    "reviewer_type": "ai_semantic_audit",
    "reviewer": "agent-reviewer-1"
  }
}
```

## Subtipos Permitidos

- `factual_recall`: Recuerdo directo (quién, qué, dónde, cuándo, cuánto).
- `speaker_addressee`: Hablante, interlocutor o destinatario de un discurso o decreto.
- `cause_consequence`: Motivo, propósito, resultado o consecuencia causal.
- `narrative_order`: Secuencia cronológica u orden de acontecimientos.
- `identification`: Identificación de personaje, entidad u objeto a partir de rasgos distintivos.
- `relationship`: Relaciones de parentesco, jerarquía, lealtad o asociación.
- `text_recall`: Recuerdo léxico o contextual de cláusulas y expresiones significativas.
- `comparison`: Comparación, contraste o diferenciación explícita.
- `symbol_interpretation`: Símbolos, visiones y sus significados directos.
- `prophetic_detail`: Números, reinos, fases temporales o detalles proféticos.
- `principle`: Principios éticos, doctrinales o lecciones teológicas de PR39–44.
- `cross_source_integration`: Conexión directa entre Daniel y *Profetas y Reyes* explícitamente sustentada en ambas fuentes.

## Reglas Editoriales Obligatorias

1. **Sin muletas de ubicación**: Se prohíbe terminantemente iniciar preguntas con «Según Daniel...», «Según PR...», «Según el párrafo...», etc.
2. **Mutación de Falso Local**: En preguntas `true_false` con respuesta "Falso", `false_mutation` debe especificar un solo cambio local verosímil (`changed_fields`, `original`, `replacement`, `local: true`). Se prohíbe falsificar mediante trasplante de pasaje ajeno.
3. **Distractores Paralelos**: Todos los distractores deben pertenecer a la misma categoría semántica (`option_category`) y tener longitud/estilo equivalente.
4. **Respaldo Textual**: La respuesta correcta debe estar presente o inequívocamente respaldada por `source_quote` y `evidence_excerpt`.
5. **Transparencia**: `ai_review` declara honestamente revisión de IA; no se reclaman firmas humanas hasta que un evaluador humano revise el registro.
