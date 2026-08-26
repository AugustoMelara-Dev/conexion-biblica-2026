import { describe, expect, it } from "vitest"
import { materializeDynamicQuestion } from "@/domain/dynamic-question"
import type { Question } from "@/domain/types"

const question: Question = {
  id: "DAN7-1",
  bankId: "massive-v5",
  bankProfileId: "massive-v5",
  type: "single_choice",
  difficulty: 4,
  difficultyBand: "HARD",
  source: { work: "Daniel", version: "RVR1995", chapter: 7, reference: "Daniel 7:1" },
  tags: ["visión"],
  factKey: "fact-1",
  factId: "fact-1",
  variantId: "variant-1",
  templateId: "mc-contextual-v1",
  question: "Según Daniel 7:1, ¿qué ocurrió?",
  options: [
    { id: "A", text: "un sueño" },
    { id: "B", text: "un decreto" },
    { id: "C", text: "un banquete" },
    { id: "D", text: "una guerra" },
  ],
  correctAnswer: ["A"],
  correctAnswerText: "un sueño",
}

describe("materialización dinámica", () => {
  it("es determinista por semilla y conserva la respuesta al barajar", () => {
    const first = materializeDynamicQuestion(question, { seed: 11, exposure: 0 })
    const repeated = materializeDynamicQuestion(question, { seed: 11, exposure: 0 })
    expect(first).toEqual(repeated)
    const correctId = first.correctAnswer[0]
    expect(first.options.find((option) => option.id === correctId)?.text).toBe("un sueño")
    expect(first.variantId).toContain("runtime")
  })

  it("cambia posición o formulación al aumentar la exposición", () => {
    const first = materializeDynamicQuestion(question, { seed: 5, exposure: 0 })
    const next = materializeDynamicQuestion(question, { seed: 5, exposure: 1 })
    expect([next.question, next.options.map((option) => option.text)]).not.toEqual([
      first.question,
      first.options.map((option) => option.text),
    ])
  })

  it("rematerializa un error sin acumular prefijos controlados", () => {
    const first = materializeDynamicQuestion(question, { seed: 5, exposure: 1 })
    const retry = materializeDynamicQuestion(first, { seed: 9, exposure: 2 })

    expect(retry.question).toMatch(/^Sin trasladar datos de otra escena, según/)
    expect(retry.question).not.toContain("Atendiendo al contexto exacto, según")
    expect(retry.variantId).toContain("runtime-3")
    expect(retry.variantId).not.toContain("runtime-2-")
  })
})
