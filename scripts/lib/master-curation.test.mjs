import { describe, expect, it } from "vitest"
import { classifyMasterQuestion, curationFamily, resolveMasterAnswer } from "./master-curation.mjs"

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

describe("política V4", () => {
  it("aprueba una pregunta inequívoca", () => {
    expect(classifyMasterQuestion(base)).toMatchObject({ status: "APPROVED", issues: [] })
    expect(resolveMasterAnswer(base)).toEqual({ mode: "option_id", optionId: "A", text: "Daniel" })
  })

  it("marca para reparación el lenguaje de generación", () => {
    const raw = { ...base, pregunta: "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «Daniel __________»." }
    expect(classifyMasterQuestion(raw)).toMatchObject({ status: "REPAIRED", issues: ["ARTIFICIAL_PROMPT"] })
  })

  it("rechaza una corrección todavía discutible", () => {
    const raw = { ...base, QUESTION_ID: "HIST-X", respuesta_correcta: "A) Tiro y Egipto, pero la relación requiere corrección." }
    expect(classifyMasterQuestion(raw)).toMatchObject({ status: "REJECTED" })
    expect(classifyMasterQuestion(raw).issues).toContain("UNRESOLVED_CORRECTION")
  })

  it("rechaza una opción correcta inexistente o repetida", () => {
    expect(classifyMasterQuestion({ ...base, respuesta_correcta: "E) Nadie" }).issues).toContain("UNRESOLVED_ANSWER")
    expect(classifyMasterQuestion({ ...base, B: "B) Daniel" }).issues).toContain("DUPLICATE_OPTIONS")
  })

  it.each([
    ["DANIEL", "0"],
    ["DANIEL", "13"],
    ["PR", "38"],
    ["PR", "45"],
  ])("rechaza el alcance %s %s", (material, capitulo) => {
    expect(classifyMasterQuestion({ ...base, material, capitulo }).issues).toContain("OUT_OF_SCOPE")
  })

  it("normaliza verdadero y falso a opciones estables", () => {
    const raw = { ...base, tipo: "VERDADERO / FALSO", A: "", B: "", C: "", D: "", respuesta_correcta: "FALSO" }
    expect(resolveMasterAnswer(raw)).toEqual({ mode: "option_id", optionId: "FALSE", text: "Falso" })
  })

  it("extrae la forma histórica canónica declarada", () => {
    const raw = { ...base, historical_status: "CORRECTED", respuesta_correcta: "A), pero la forma exacta RVR95 es «Beltsasar»." }
    expect(resolveMasterAnswer(raw)).toEqual({ mode: "canonical_text", text: "Beltsasar" })
  })

  it("no resuelve una corrección histórica sin forma canónica explícita", () => {
    const raw = { ...base, historical_status: "CORRECTED", respuesta_correcta: "B) es la intención del ítem; RVR95 dice otra forma." }
    expect(resolveMasterAnswer(raw)).toBeNull()
    expect(classifyMasterQuestion(raw).issues).toContain("UNRESOLVED_ANSWER")
  })

  it("resuelve una respuesta corta sin opciones como texto canónico", () => {
    const raw = { ...base, tipo: "RESPUESTA CORTA", A: "", B: "", C: "", D: "", respuesta_correcta: "Daniel" }
    expect(classifyMasterQuestion(raw)).toMatchObject({ status: "REPAIRED", issues: ["SHORT_ANSWER_TYPE"] })
    expect(resolveMasterAnswer(raw)).toEqual({ mode: "canonical_text", text: "Daniel" })
  })

  it("marca las demás reparaciones deterministas en orden", () => {
    const raw = {
      ...base,
      pregunta: "[Profetas y Reyes] El dato «queda aquí.",
      explicacion: "Pregunta histórica validada en FASE 1; cobertura auditada en FASE 3.",
    }
    expect(classifyMasterQuestion(raw)).toMatchObject({
      status: "REPAIRED",
      issues: ["PROCESS_EXPLANATION", "EDITORIAL_PREFIX", "UNBALANCED_QUOTES"],
    })
  })

  it("detecta opciones equivalentes ignorando acentos y puntuación", () => {
    const raw = { ...base, B: "B) Dániel!" }
    expect(classifyMasterQuestion(raw).issues).toContain("DUPLICATE_OPTIONS")
    expect(resolveMasterAnswer(raw)).toBeNull()
  })
})

describe("familias de curación", () => {
  it("conserva todos los hechos y prioriza FULL, PARTIAL e INCIDENTAL", () => {
    expect(curationFamily({
      QUESTION_ID: "Q-1",
      FULL_FACT_IDS: ["FULL-1"],
      PARTIAL_FACT_IDS: ["PARTIAL-1"],
      INCIDENTAL_FACT_IDS: ["INCIDENTAL-1"],
      duplicate_group: "DG-1",
    })).toEqual({ factKey: "FULL-1", factKeys: ["FULL-1", "PARTIAL-1", "INCIDENTAL-1"] })
  })

  it("usa el primer grupo duplicado y luego el ID como respaldo", () => {
    expect(curationFamily({ QUESTION_ID: "Q-2", duplicate_group: "DG-2" })).toEqual({ factKey: "DG-2", factKeys: ["DG-2"] })
    expect(curationFamily({ QUESTION_ID: "Q-3", duplicate_group: "" })).toEqual({ factKey: "Q-3", factKeys: ["Q-3"] })
  })
})
