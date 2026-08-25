import { describe, expect, it } from "vitest"
import { classifyMasterQuestion } from "./master-curation.mjs"
import { curateMasterQuestion, repairExplanation, repairPrompt } from "./curated-question.mjs"

const base = {
  QUESTION_ID: "GEN-1", origen: "GENERATED", material: "DANIEL", capitulo: "1",
  tipo: "SELECCIÓN MÚLTIPLE", dificultad: "HARD", pregunta: "¿Quién decidió no contaminarse?",
  A: "A) Daniel", B: "B) Aspenaz", C: "C) Nabucodonosor", D: "D) Darío",
  respuesta_correcta: "A) Daniel", fuente: "Daniel 1:8, RVR95",
  FULL_FACT_IDS: ["FACT-D01-V08-001"], PARTIAL_FACT_IDS: [], INCIDENTAL_FACT_IDS: [],
  habilidad: "identificación", riesgo_objetivo: "HIGH", explicacion: "Daniel decidió no contaminarse.",
  estado_QC: "PASS_10_10", variant_of: "", generation_level: "1", duplicate_group: "DG-1",
  HIST_IDS: [], historical_status: "", fact_support: "Daniel propuso no contaminarse",
  answer_span: "Daniel", answer_category: "PERSON",
}

describe("adaptador de preguntas curadas V4", () => {
  it("repara redacción y explicación sin cambiar respuesta ni fuente", () => {
    const raw = {
      ...base,
      pregunta: "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «Daniel __________».",
      explicacion: "Pregunta histórica validada en FASE 1; cobertura auditada en FASE 3.",
    }
    const decision = classifyMasterQuestion(raw)

    expect(curateMasterQuestion(raw, decision)).toMatchObject({
      id: "V4-GEN-1",
      question: "Completa la afirmación: Daniel __________.",
      correctAnswer: ["A"],
      explanation: "La respuesta se confirma en Daniel 1:8, RVR95.",
      source: { work: "Daniel", chapter: 1, reference: "Daniel 1:8, RVR95" },
      metadata: { masterQuestionId: "GEN-1", curationStatus: "REPAIRED" },
    })
  })

  it("convierte respuesta corta en texto canónico", () => {
    const raw = { ...base, tipo: "RESPUESTA CORTA", A: "", B: "", C: "", D: "", respuesta_correcta: "Daniel" }

    expect(curateMasterQuestion(raw, classifyMasterQuestion(raw))).toMatchObject({
      type: "reference_detail", answerMode: "canonical_text", correctAnswerText: "Daniel",
    })
  })

  it("no genera salida para rechazados", () => {
    const raw = { ...base, respuesta_correcta: "A) Daniel, pero requiere corrección." }

    expect(curateMasterQuestion(raw, classifyMasterQuestion(raw))).toBeNull()
  })

  it("no muta el registro maestro al adaptar una respuesta corta", () => {
    const raw = { ...base, tipo: "RESPUESTA CORTA", A: "", B: "", C: "", D: "", respuesta_correcta: "Daniel" }
    const before = structuredClone(raw)

    curateMasterQuestion(raw, classifyMasterQuestion(raw))

    expect(raw).toEqual(before)
  })

  it("conserva una corrección histórica explícita como texto canónico", () => {
    const raw = {
      ...base,
      QUESTION_ID: "HIST-X",
      historical_status: "CORRECTED",
      respuesta_correcta: "A), pero la forma exacta RVR95 es «Beltsasar».",
    }

    expect(curateMasterQuestion(raw, classifyMasterQuestion(raw))).toMatchObject({
      type: "reference_detail",
      correctAnswer: ["ANSWER"],
      answerMode: "canonical_text",
      correctAnswerText: "Beltsasar",
    })
  })

  it("preserva comillas internas válidas al reparar el prompt", () => {
    const prompt = "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «El rey reiteró: «Decidme, pues, el sueño __________»»."

    expect(repairPrompt(prompt)).toBe("Completa la afirmación: El rey reiteró: «Decidme, pues, el sueño __________».")
  })

  it("quita una apertura exterior huérfana después del encabezado", () => {
    const prompt = "Completa correctamente la afirmación: «Nabucodonosor preguntó si ellos no honraban «a mi __________»."

    expect(repairPrompt(prompt)).toBe("Completa correctamente la afirmación: Nabucodonosor preguntó si ellos no honraban «a mi __________».")
  })

  it("usa el soporte factual para explicar sin inventar contenido", () => {
    const raw = { ...base, fact_support: "Daniel propuso no contaminarse." }

    expect(repairExplanation(raw)).toBe("Dato verificado en Daniel 1:8, RVR95: Daniel propuso no contaminarse.")
  })
})
