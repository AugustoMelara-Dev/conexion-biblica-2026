import { describe, expect, it } from "vitest"
import {
  buildPoolKey,
  createSeededRng,
  selectBalancedRandom,
  selectCoverageCycle,
  selectSequentialBlock,
} from "@/domain/session-selection"
import type { Question, SessionConfig } from "@/domain/types"

function createQuestions(count: number, bankId = "bank-v1"): Question[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `Q-${String(index + 1).padStart(4, "0")}`,
    bankId,
    bankProfileId: bankId === "master-v2" ? "master-v2" : "legacy-v1",
    type: "single_choice",
    difficulty: ((index % 5) + 1) as Question["difficulty"],
    source: {
      work: index % 3 === 0 ? "Profetas y Reyes" : "Daniel",
      version: "test",
      chapter: (index % 6) + 1,
      reference: `Test ${index + 1}`,
    },
    tags: [],
    factKey: `fact-${Math.floor(index / 2)}`,
    factKeys: [`fact-${Math.floor(index / 2)}`],
    question: `Pregunta ${index + 1}`,
    options: [{ id: "A", text: "A" }, { id: "B", text: "B" }],
    correctAnswer: ["A"],
  }))
}

describe("Coverage Cycle", () => {
  it("entrega 50 + 50 sin intersección para un pool de 100", () => {
    const pool = createQuestions(100)
    const first = selectCoverageCycle({ pool, count: 50, poolKey: "same", rng: createSeededRng(7), now: 1 })
    const second = selectCoverageCycle({ pool, count: 50, poolKey: "same", cycle: first.cycle, rng: createSeededRng(8), now: 2 })
    const firstKeys = new Set(first.questions.map((question) => question.id))
    const secondKeys = new Set(second.questions.map((question) => question.id))

    expect(first.questions).toHaveLength(50)
    expect(second.questions).toHaveLength(50)
    expect(firstKeys.size).toBe(50)
    expect(secondKeys.size).toBe(50)
    expect([...firstKeys].filter((key) => secondKeys.has(key))).toEqual([])
    expect(new Set([...firstKeys, ...secondKeys]).size).toBe(100)
    expect(second.remaining).toBe(0)
    expect(second.completed).toBe(true)
  })

  it("entrega 50 + 50 + 20 y no reinicia silenciosamente", () => {
    const pool = createQuestions(120)
    const first = selectCoverageCycle({ pool, count: 50, poolKey: "120", rng: createSeededRng(1), now: 1 })
    const second = selectCoverageCycle({ pool, count: 50, poolKey: "120", cycle: first.cycle, rng: createSeededRng(2), now: 2 })
    const third = selectCoverageCycle({ pool, count: 50, poolKey: "120", cycle: second.cycle, rng: createSeededRng(3), now: 3 })
    const afterComplete = selectCoverageCycle({ pool, count: 50, poolKey: "120", cycle: third.cycle, rng: createSeededRng(4), now: 4 })
    const allKeys = [...first.questions, ...second.questions, ...third.questions].map((question) => question.id)

    expect([first.questions.length, second.questions.length, third.questions.length]).toEqual([50, 50, 20])
    expect(new Set(allKeys).size).toBe(120)
    expect(afterComplete.questions).toEqual([])
    expect(afterComplete.completed).toBe(true)
  })

  it("reinicia explícitamente con un cycleId nuevo", () => {
    const pool = createQuestions(10)
    const first = selectCoverageCycle({ pool, count: 10, poolKey: "reset", rng: createSeededRng(1), now: 1 })
    const reset = selectCoverageCycle({ pool, count: 3, poolKey: "reset", cycle: first.cycle, reset: true, rng: createSeededRng(2), now: 2 })

    expect(reset.questions).toHaveLength(3)
    expect(reset.cycle.cycleId).not.toBe(first.cycle.cycleId)
    expect(reset.remaining).toBe(7)
  })
})

describe("otras estrategias", () => {
  it("Random Balanced no duplica y alterna capítulos cuando el pool lo permite", () => {
    const result = selectBalancedRandom(createQuestions(60), 30, createSeededRng(42))
    expect(result).toHaveLength(30)
    expect(new Set(result.map((question) => `${question.bankId}:${question.id}`)).size).toBe(30)
    let longest = 1
    let run = 1
    for (let index = 1; index < result.length; index += 1) {
      run = result[index].source.chapter === result[index - 1].source.chapter ? run + 1 : 1
      longest = Math.max(longest, run)
    }
    expect(longest).toBeLessThanOrEqual(2)
  })

  it("Random Balanced mantiene V1 y V2 en Mixto y redistribuye una cuota insuficiente", () => {
    const balancedPool = [
      ...createQuestions(20, "bank-v1"),
      ...createQuestions(20, "master-v2"),
    ]
    const balanced = selectBalancedRandom(balancedPool, 20, createSeededRng(91))

    expect(new Set(balanced.map((question) => question.bankProfileId))).toEqual(
      new Set(["legacy-v1", "master-v2"]),
    )
    expect(new Set(balanced.map((question) => `${question.bankId}:${question.id}`)).size).toBe(20)

    const scarceV1Pool = [
      ...createQuestions(2, "bank-v1"),
      ...createQuestions(20, "master-v2"),
    ]
    const redistributed = selectBalancedRandom(scarceV1Pool, 10, createSeededRng(92))

    expect(redistributed).toHaveLength(10)
    expect(redistributed.filter((question) => question.bankProfileId === "legacy-v1")).toHaveLength(2)
    expect(redistributed.filter((question) => question.bankProfileId === "master-v2")).toHaveLength(8)
  })

  it("Sequential Blocks respeta bloques y cursor", () => {
    const pool = createQuestions(100)
    const first = selectSequentialBlock(pool, 50, 0)
    const second = selectSequentialBlock(pool, 50, 1)

    expect(first.questions.map((question) => question.id)).toEqual(pool.slice(0, 50).map((question) => question.id))
    expect(second.questions.map((question) => question.id)).toEqual(pool.slice(50, 100).map((question) => question.id))
    expect(second.blockCount).toBe(2)
  })

  it("poolKey cambia con filtros y es estable ante el orden de arrays", () => {
    const base: SessionConfig = {
      mode: "training", count: 50, sourceWorks: ["Daniel", "Profetas y Reyes"], chapters: [3, 1],
      difficulties: [5, 3], types: ["true_false", "single_choice"], statuses: ["all"],
      shuffleQuestions: true, shuffleOptions: true, perQuestionSeconds: null, totalSeconds: null,
      bankSelection: "master-v2", strategy: "coverage-cycle",
    }
    const reordered = { ...base, chapters: [1, 3], difficulties: [3, 5], types: ["single_choice", "true_false"] } satisfies SessionConfig

    expect(buildPoolKey(base)).toBe(buildPoolKey(reordered))
    expect(buildPoolKey({ ...base, chapters: [1, 4] })).not.toBe(buildPoolKey(base))
    expect(buildPoolKey({ ...base, bankSelection: "legacy-v1" })).not.toBe(buildPoolKey(base))
  })
})
