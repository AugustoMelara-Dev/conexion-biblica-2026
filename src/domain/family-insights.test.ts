import { describe, expect, it } from "vitest"
import { buildFamilyInsights } from "@/domain/family-insights"
import { createEmptyProgress } from "@/domain/mastery"
import type { Question } from "@/domain/types"

function question(id: string, factKey: string): Question {
  return { id, bankId: "prep", type: "single_choice", difficulty: 3, source: { work: "Daniel", version: "RVR95", chapter: 1, reference: "Daniel 1:1" }, tags: [], factKey, question: id, options: [{ id: "A", text: "A" }], correctAnswer: ["A"] }
}

describe("panel por factKey", () => {
  it("marca como dominada una familia completa con dominio alto", () => {
    const first = createEmptyProgress("prep:a")
    const second = createEmptyProgress("prep:b")
    Object.assign(first, { timesSeen: 3, timesCorrect: 3, masteryScore: 5 })
    Object.assign(second, { timesSeen: 2, timesCorrect: 2, masteryScore: 4 })
    const [row] = buildFamilyInsights([question("a", "fact") , question("b", "fact")], new Map([[first.questionKey, first], [second.questionKey, second]]))
    expect(row).toMatchObject({ status: "mastered", variants: 2, seenVariants: 2, pendingVariants: 0 })
  })

  it("distingue familias débiles de variantes todavía pendientes", () => {
    const failed = createEmptyProgress("prep:a")
    Object.assign(failed, { timesSeen: 2, timesIncorrect: 1, masteryScore: 1 })
    const [row] = buildFamilyInsights([question("a", "fact"), question("b", "fact")], new Map([[failed.questionKey, failed]]))
    expect(row).toMatchObject({ status: "weak", seenVariants: 1, pendingVariants: 1, incorrect: 1 })
  })

  it("mantiene una familia totalmente nueva como pendiente", () => {
    const [row] = buildFamilyInsights([question("a", "fact")], new Map())
    expect(row).toMatchObject({ status: "pending", seenVariants: 0, pendingVariants: 1 })
  })
})

