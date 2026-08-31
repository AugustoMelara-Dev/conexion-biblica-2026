import { describe, expect, it } from "vitest"
import { selectAdaptiveSession } from "@/domain/adaptive-session"
import { emptyFactMastery } from "@/domain/fact-mastery"
import type { Question, QuestionExposure } from "@/domain/types"

function makeQuestion(
  index: number,
  overrides: Partial<Question> = {}
): Question {
  return {
    id: `Q-${index}`,
    bankId: "massive-v5",
    bankProfileId: "massive-v5",
    type: "single_choice",
    difficulty: 4,
    source: {
      work: "Daniel",
      version: "RVR1995",
      chapter: index % 2 ? 7 : 8,
      reference: `Daniel 7:${index}`,
    },
    tags: [],
    factKey: `fact-${index}`,
    factId: `fact-${index}`,
    variantId: `variant-${index}`,
    templateId: "mc-contextual-v1",
    question: `Pregunta ${index}`,
    options: [
      { id: "A", text: "Sí" },
      { id: "B", text: "No" },
    ],
    correctAnswer: ["A"],
    ...overrides,
  }
}

function exposure(
  index: number,
  overrides: Partial<QuestionExposure>
): QuestionExposure {
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
    const questions = Array.from({ length: 20 }, (_, index) =>
      makeQuestion(index)
    )
    questions.push(
      makeQuestion(50, {
        factKey: "fact-1",
        factId: "fact-1",
        variantId: "variant-extra",
      })
    )
    questions.push(makeQuestion(60, { blindFinalPool: true }))
    const selected = selectAdaptiveSession({
      questions,
      exposures: [],
      count: 20,
      weakChapters: [7],
      includeBlind: false,
      seed: 1,
    })
    expect(new Set(selected.map((item) => item.factId)).size).toBe(
      selected.length
    )
    expect(selected.some((item) => item.blindFinalPool)).toBe(false)
  })

  it("aplica la mezcla 60/20/10/10 cuando hay candidatos suficientes", () => {
    const novel = Array.from({ length: 60 }, (_, index) => makeQuestion(index))
    const failed = Array.from({ length: 20 }, (_, index) =>
      makeQuestion(100 + index)
    )
    const slow = Array.from({ length: 10 }, (_, index) =>
      makeQuestion(200 + index)
    )
    const traps = Array.from({ length: 10 }, (_, index) =>
      makeQuestion(300 + index, { trapType: "true_elsewhere" })
    )
    const exposures = [
      ...failed.map((_, index) =>
        exposure(100 + index, { correct: 0, incorrect: 2 })
      ),
      ...slow.map((_, index) =>
        exposure(200 + index, {
          averageResponseTimeMs: 12000,
          totalResponseTimeMs: 12000,
        })
      ),
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
    expect(
      selected.filter(
        (item) =>
          item.id.startsWith("Q-1") &&
          Number(item.id.slice(2)) >= 100 &&
          Number(item.id.slice(2)) < 200
      )
    ).toHaveLength(20)
    expect(
      selected.filter(
        (item) =>
          Number(item.id.slice(2)) >= 200 && Number(item.id.slice(2)) < 300
      )
    ).toHaveLength(10)
    expect(
      selected.filter((item) => Number(item.id.slice(2)) >= 300)
    ).toHaveLength(10)
    expect(
      selected.filter((item) => Number(item.id.slice(2)) < 100)
    ).toHaveLength(60)
  })

  it("incluye en repaso espaciado solo hechos cuyo nextDueAt ya venció", () => {
    const now = Date.UTC(2026, 7, 30, 12)
    const due = {
      ...emptyFactMastery("fact-1"),
      state: "due" as const,
      nextDueAt: now - 1,
    }
    const future = {
      ...emptyFactMastery("fact-2"),
      state: "stable" as const,
      nextDueAt: now + 1,
    }

    const selected = selectAdaptiveSession({
      questions: [makeQuestion(1), makeQuestion(2)],
      exposures: [exposure(1, {}), exposure(2, {})],
      factMastery: [due, future],
      presetId: "spaced-review",
      now,
      count: 2,
      weakChapters: [],
      includeBlind: false,
      seed: 3,
    })

    expect(selected.map((question) => question.factId)).toEqual(["fact-1"])
  })

  it("trata como visto todo el hecho aunque la variante concreta sea nueva", () => {
    const seenFact = {
      ...emptyFactMastery("fact-1"),
      state: "learning" as const,
      attempts: 1,
      variantIds: ["different-variant"],
    }

    const selected = selectAdaptiveSession({
      questions: [makeQuestion(1), makeQuestion(2)],
      exposures: [],
      factMastery: [seenFact],
      presetId: "unseen-only",
      count: 2,
      weakChapters: [],
      includeBlind: false,
      seed: 4,
    })

    expect(selected.map((question) => question.factId)).toEqual(["fact-2"])
  })

  it("aplica el filtro de no vistas a los presets fechados de nuevas", () => {
    const seenFact = {
      ...emptyFactMastery("fact-1"),
      state: "learning" as const,
      attempts: 1,
    }

    const selected = selectAdaptiveSession({
      questions: [makeQuestion(1), makeQuestion(2)],
      exposures: [],
      factMastery: [seenFact],
      presetId: "2026-08-31-new",
      count: 2,
      weakChapters: [],
      includeBlind: false,
      seed: 41,
    })

    expect(selected.map((question) => question.factId)).toEqual(["fact-2"])
  })

  it("limita el repaso fechado a errores y correctas lentas sobre seis segundos", () => {
    const failed = {
      ...emptyFactMastery("fact-1"),
      state: "due" as const,
      failures: 1,
    }
    const fragile = {
      ...emptyFactMastery("fact-2"),
      state: "fragile" as const,
    }
    const stable = {
      ...emptyFactMastery("fact-3"),
      state: "stable" as const,
    }

    const selected = selectAdaptiveSession({
      questions: [makeQuestion(1), makeQuestion(2), makeQuestion(3)],
      exposures: [
        exposure(1, { correct: 0, incorrect: 1 }),
        exposure(2, {
          averageResponseTimeMs: 6_001,
          totalResponseTimeMs: 6_001,
        }),
        exposure(3, {}),
      ],
      factMastery: [failed, fragile, stable],
      presetId: "2026-08-31-review",
      count: 3,
      weakChapters: [],
      includeBlind: false,
      seed: 42,
    })

    expect(new Set(selected.map((question) => question.factId))).toEqual(
      new Set(["fact-1", "fact-2"])
    )
  })

  it("limita correctas lentas a hechos frágiles", () => {
    const fragile = {
      ...emptyFactMastery("fact-1"),
      state: "fragile" as const,
      attempts: 1,
    }
    const stable = {
      ...emptyFactMastery("fact-2"),
      state: "stable" as const,
      attempts: 2,
    }

    const selected = selectAdaptiveSession({
      questions: [makeQuestion(1), makeQuestion(2)],
      exposures: [
        exposure(1, { averageResponseTimeMs: 12_000 }),
        exposure(2, { averageResponseTimeMs: 2_000 }),
      ],
      factMastery: [fragile, stable],
      presetId: "slow-correct",
      count: 2,
      weakChapters: [],
      includeBlind: false,
      seed: 5,
    })

    expect(selected.map((question) => question.factId)).toEqual(["fact-1"])
  })

  it("recupera errores por factId aunque se seleccione otra variante", () => {
    const failedFact = {
      ...emptyFactMastery("fact-1"),
      state: "due" as const,
      attempts: 1,
      failures: 1,
      variantIds: ["different-variant"],
    }

    const selected = selectAdaptiveSession({
      questions: [makeQuestion(1), makeQuestion(2)],
      exposures: [],
      factMastery: [failedFact],
      presetId: "previous-errors",
      count: 2,
      weakChapters: [],
      includeBlind: false,
      seed: 6,
    })

    expect(selected.map((question) => question.factId)).toEqual(["fact-1"])
  })

  it("mantiene la simulación ciega en hechos no vistos al omitir el filtro legado", () => {
    const seenFact = {
      ...emptyFactMastery("fact-1"),
      state: "stable" as const,
      attempts: 2,
    }

    const selected = selectAdaptiveSession({
      questions: [
        makeQuestion(1, { blindFinalPool: true }),
        makeQuestion(2, { blindFinalPool: true }),
      ],
      exposures: [],
      factMastery: [seenFact],
      presetId: "blind-simulation",
      count: 2,
      weakChapters: [],
      includeBlind: true,
      seed: 7,
    })

    expect(selected.map((question) => question.factId)).toEqual(["fact-2"])
  })
})
