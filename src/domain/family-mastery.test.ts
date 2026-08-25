import { describe, expect, it } from "vitest"
import { buildFamilyMastery } from "@/domain/family-mastery"
import { createEmptyProgress } from "@/domain/mastery"
import type { Question } from "@/domain/types"

function question(id: string, factKey: string): Question {
  return { id, bankId: "prep", type: "single_choice", difficulty: 3, source: { work: "Daniel", version: "RVR95", chapter: 1, reference: "Daniel 1:1" }, tags: [], factKey, question: id, options: [{ id: "A", text: "A" }], correctAnswer: ["A"] }
}

describe("dominio por familia", () => {
  it("prioriza una familia fallada y lenta sobre una dominada", () => {
    const weak = createEmptyProgress("prep:weak")
    Object.assign(weak, { timesSeen: 4, timesIncorrect: 3, averageResponseTimeMs: 18000, masteryScore: 1, lastSeenAt: 10 })
    const strong = createEmptyProgress("prep:strong")
    Object.assign(strong, { timesSeen: 5, timesCorrect: 5, averageResponseTimeMs: 2000, masteryScore: 5, lastSeenAt: 100 })
    const mastery = buildFamilyMastery([question("weak", "fact-weak"), question("strong", "fact-strong")], new Map([[weak.questionKey, weak], [strong.questionKey, strong]]), 1000)
    expect(mastery.get("fact-weak")!.priority).toBeGreaterThan(mastery.get("fact-strong")!.priority)
  })

  it("mantiene las familias nuevas en el repaso", () => {
    const mastery = buildFamilyMastery([question("new", "fact-new")], new Map(), 1000)
    expect(mastery.get("fact-new")?.unseen).toBe(1)
    expect(mastery.get("fact-new")!.priority).toBeGreaterThan(0)
  })
})
