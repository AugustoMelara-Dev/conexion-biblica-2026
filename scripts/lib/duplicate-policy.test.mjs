import { describe, expect, it } from "vitest"
import { applyDuplicatePolicy, duplicatePromptKey, resolvedAnswerKey } from "./duplicate-policy.mjs"

function entry(id, answer) {
  const question = {
    id: `V4-${id}`,
    question: "¿Pregunta exacta?",
    options: [{ id: "A", text: answer }],
    correctAnswer: ["A"],
  }
  return { raw: { QUESTION_ID: id }, decision: { status: "APPROVED", issues: [] }, curated: question }
}

describe("ruling de duplicados exactos V4", () => {
  it("conserva el menor QUESTION_ID cuando las respuestas resueltas equivalen", () => {
    const entries = applyDuplicatePolicy([entry("GEN-10", "Daniel."), entry("GEN-2", "Dániel")])

    expect(entries[0].decision.status).toBe("REJECTED")
    expect(entries[0].decision.issues).toContain("DUPLICATE_PROMPT_NON_CANONICAL")
    expect(entries[1].decision.status).toBe("APPROVED")
    expect(entries[1].curated).not.toBeNull()
  })

  it("rechaza todo el grupo cuando las respuestas resueltas difieren", () => {
    const entries = applyDuplicatePolicy([entry("GEN-1", "Daniel"), entry("GEN-2", "Nabucodonosor")])

    expect(entries.every((item) => item.decision.status === "REJECTED")).toBe(true)
    expect(entries.every((item) => item.decision.issues.includes("DUPLICATE_PROMPT_CONFLICT"))).toBe(true)
    expect(entries.every((item) => item.curated === null)).toBe(true)
  })

  it("mantiene auditable un duplicado ya rechazado junto a uno utilizable", () => {
    const rejected = { raw: { QUESTION_ID: "GEN-1", pregunta: "¿Pregunta exacta?" }, decision: { status: "REJECTED", issues: ["UNRESOLVED_ANSWER"], answer: null }, curated: null }
    const entries = applyDuplicatePolicy([rejected, entry("GEN-2", "Daniel")])

    expect(entries[0].decision.status).toBe("REJECTED")
    expect(entries[0].decision.issues).toContain("DUPLICATE_PROMPT_CONFLICT")
    expect(entries[1].decision.status).toBe("REJECTED")
    expect(entries[1].curated).toBeNull()
  })

  it("normaliza sólo Unicode y espacios para identidad textual", () => {
    expect(duplicatePromptKey("¿Pregunta\nexacta? ")).toBe("¿Pregunta exacta?")
    expect(resolvedAnswerKey({ options: [{ id: "A", text: "Dániel." }], correctAnswer: ["A"] })).toBe("daniel")
  })
})
