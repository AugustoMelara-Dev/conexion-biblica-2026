import { describe, expect, it } from "vitest"
import { selectAdaptiveSession } from "@/domain/adaptive-session"
import type { Question, QuestionExposure } from "@/domain/types"

function makeQuestion(index: number, overrides: Partial<Question> = {}): Question {
  return {
    id: `Q-${index}`,
    bankId: "massive-v5",
    bankProfileId: "massive-v5",
    type: "single_choice",
    difficulty: 4,
    source: { work: "Daniel", version: "RVR1995", chapter: index % 2 ? 7 : 8, reference: `Daniel 7:${index}` },
    tags: [],
    factKey: `fact-${index}`,
    factId: `fact-${index}`,
    variantId: `variant-${index}`,
    templateId: "mc-contextual-v1",
    question: `Pregunta ${index}`,
    options: [{ id: "A", text: "Sí" }, { id: "B", text: "No" }],
    correctAnswer: ["A"],
    ...overrides,
  }
}

function exposure(index: number, overrides: Partial<QuestionExposure>): QuestionExposure {
  return {
    exposureKey: `fact-${index}:variant-${index}`,
    factId: `fact-${index}`,
    variantId: `variant-${index}`,
    questionKey: `massive-v5:Q-${index}`,
    exposures: 1,
    correct: 1,
    incorrect: 0,
    totalResponseTimeMs: 2000,
    averageResponseTimeMs: 2000,
    lastSeenAt: index,
    lastSelectedAnswer: "A",
    lastErrorType: null,
    ...overrides,
  }
}

describe("selector adaptativo anti-memorización", () => {
  it("evita repetir factId y reserva preguntas ciegas", () => {
    const questions = Array.from({ length: 20 }, (_, index) => makeQuestion(index))
    questions.push(makeQuestion(50, { factKey: "fact-1", factId: "fact-1", variantId: "variant-extra" }))
    questions.push(makeQuestion(60, { blindFinalPool: true }))
    const selected = selectAdaptiveSession({ questions, exposures: [], count: 20, weakChapters: [7], includeBlind: false, seed: 1 })
    expect(new Set(selected.map((item) => item.factId)).size).toBe(selected.length)
    expect(selected.some((item) => item.blindFinalPool)).toBe(false)
  })

  it("aplica la mezcla 60/20/10/10 cuando hay candidatos suficientes", () => {
    const novel = Array.from({ length: 60 }, (_, index) => makeQuestion(index))
    const failed = Array.from({ length: 20 }, (_, index) => makeQuestion(100 + index))
    const slow = Array.from({ length: 10 }, (_, index) => makeQuestion(200 + index))
    const traps = Array.from({ length: 10 }, (_, index) => makeQuestion(300 + index, { trapType: "true_elsewhere" }))
    const exposures = [
      ...failed.map((_, index) => exposure(100 + index, { correct: 0, incorrect: 2 })),
      ...slow.map((_, index) => exposure(200 + index, { averageResponseTimeMs: 12000, totalResponseTimeMs: 12000 })),
      ...traps.map((_, index) => exposure(300 + index, {})),
    ]
    const selected = selectAdaptiveSession({
      questions: [...novel, ...failed, ...slow, ...traps],
      exposures,
      count: 100,
      weakChapters: [7, 8],
      includeBlind: false,
      seed: 2,
    })
    expect(selected.filter((item) => item.id.startsWith("Q-1") && Number(item.id.slice(2)) >= 100 && Number(item.id.slice(2)) < 200)).toHaveLength(20)
    expect(selected.filter((item) => Number(item.id.slice(2)) >= 200 && Number(item.id.slice(2)) < 300)).toHaveLength(10)
    expect(selected.filter((item) => Number(item.id.slice(2)) >= 300)).toHaveLength(10)
    expect(selected.filter((item) => Number(item.id.slice(2)) < 100)).toHaveLength(60)
  })
})
