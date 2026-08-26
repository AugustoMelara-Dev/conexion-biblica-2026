import { describe, expect, it } from "vitest"

import { selectBlindSimulation, selectMissionQuestions } from "@/domain/final-mission-selection"
import type { Question } from "@/domain/types"

const make = (index: number, chapter = 7, blindPool: Question["blindPool"] = null): Question => ({
  id: `Q${index}`,
  bankId: "consolidation-v5",
  bankProfileId: "consolidation-v5",
  type: "single_choice",
  difficulty: 4,
  source: { work: "Daniel", version: "RVR1995", chapter, reference: `Daniel ${chapter}:1` },
  tags: [],
  factKey: `F${index}`,
  factId: `F${index}`,
  variantId: `V${index}`,
  question: "?",
  options: [{ id: "A", text: "a" }, { id: "B", text: "b" }],
  correctAnswer: ["A"],
  blindPool,
  blindFinalPool: blindPool !== null,
  editorialStatus: "gold",
})

describe("final mission selection", () => {
  it("never repeats a fact in a normal session and excludes blind questions", () => {
    const questions = [...Array.from({ length: 20 }, (_, index) => make(index)), make(99, 7, "A")]
    const selected = selectMissionQuestions({ questions, count: 15, seed: 4 })
    expect(new Set(selected.map((item) => item.factId)).size).toBe(selected.length)
    expect(selected.every((item) => !item.blindPool)).toBe(true)
  })

  it("keeps simulations A and B fact-disjoint", () => {
    const questions = [make(1, 7, "A"), make(2, 7, "A"), make(2, 7, "B"), make(3, 7, "B")]
    const a = selectBlindSimulation(questions, "A", 10, 1)
    const b = selectBlindSimulation(questions, "B", 10, 1, new Set(a.map((item) => item.factId!)))
    expect(a.map((item) => item.factId)).toEqual(["F1", "F2"])
    expect(b.map((item) => item.factId)).toEqual(["F3"])
  })
})
