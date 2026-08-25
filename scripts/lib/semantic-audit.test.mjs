import { describe, expect, it } from "vitest"
import { auditQuestions } from "./semantic-audit.mjs"

const master = { QUESTION_ID: "GEN-1", material: "DANIEL", capitulo: "1", pregunta: "¿Qué ocurrió?", A: "A) Sí", B: "B) No", respuesta_correcta: "A) Sí", fuente: "Daniel 1:1", estado_QC: "PASS_10_10" }
const valid = { id: "V3-1", factKey: "FACT-1", type: "single_choice", source: { work: "Daniel", version: "RVR95", chapter: 1, reference: "Daniel 1:1" }, question: "¿Qué ocurrió?", options: [{ id: "A", text: "Sí" }, { id: "B", text: "No" }], correctAnswer: ["A"], verified: true, metadata: { masterQuestionId: "GEN-1" } }

describe("auditoría semántica", () => {
  it("acepta una pregunta trazable y marca contradicciones estructurales", () => {
    expect(auditQuestions([valid], [master]).summary.blockers).toBe(0)
    const broken = { ...valid, id: "V3-2", source: { ...valid.source, chapter: 2 }, correctAnswer: ["Z"] }
    const result = auditQuestions([broken], [master])
    expect(result.summary.blockers).toBeGreaterThanOrEqual(2)
    expect(result.findings.map((item) => item.code)).toEqual(expect.arrayContaining(["MASTER_CHAPTER_MISMATCH", "INVALID_CORRECT_OPTION"]))
  })

  it("separa las integradoras sin maestro y detecta señales que requieren revisión", () => {
    const integrative = { ...valid, id: "INT", integrative: true, metadata: undefined, question: "Corta" }
    const result = auditQuestions([integrative], [master])
    expect(result.findings.map((item) => item.code)).not.toContain("MISSING_MASTER_ID")
    expect(result.findings.map((item) => item.code)).toContain("PROMPT_TOO_SHORT")
  })

  it("bloquea un enunciado que ya no es trazable al maestro", () => {
    const changed = { ...valid, question: "¿Qué personaje completamente distinto aparece aquí?" }
    const result = auditQuestions([changed], [master])
    expect(result.findings.map((item) => item.code)).toContain("PROMPT_NOT_TRACEABLE")
  })
})
