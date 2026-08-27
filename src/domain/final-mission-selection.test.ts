import { describe, expect, it } from "vitest"

import { selectBlindSimulation, selectMissionQuestions } from "@/domain/final-mission-selection"
import type { Question } from "@/domain/types"

const make = (
  index: number,
  chapter = 7,
  blindPool: Question["blindPool"] = null,
  overrides: Partial<Question> = {},
): Question => ({
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
  family: "single_choice_direct",
  ...overrides,
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

  it("builds every general round of 100 with 25 questions from each family", () => {
    let cursor = 0
    const fill = Array.from({ length: 45 }, () =>
      make(cursor++, 7, null, {
        type: "fill_blank",
        family: "fill_choice",
      }),
    )
    const trueFalse = Array.from({ length: 40 }, (_, index) => make(cursor++, 7, null, {
      type: "true_false",
      family: "true_false",
      correctAnswerText: index % 2 === 0 ? "Verdadero" : "Falso",
    }))
    const direct = Array.from({ length: 45 }, (_, index) => make(cursor++, 7, null, {
      type: "single_choice",
      family: "single_choice_direct",
      semanticSkill: index < 20 ? "cause_consequence" : "contextual_precision",
    }))
    const contextual = Array.from({ length: 45 }, () => make(cursor++, 7, null, {
      type: "single_choice",
      family: "single_choice_contextual",
      trapType: "true_elsewhere",
      semanticSkill: "scene_identification",
    }))

    const selected = selectMissionQuestions({ questions: [...fill, ...trueFalse, ...direct, ...contextual], count: 100, seed: 91 })
    const types = selected.reduce<Record<string, number>>((counts, item) => {
      counts[item.type] = (counts[item.type] ?? 0) + 1
      return counts
    }, {})
    const tfAnswers = selected
      .filter((item) => item.type === "true_false")
      .reduce<Record<string, number>>((counts, item) => {
        const answer = item.correctAnswerText ?? ""
        counts[answer] = (counts[answer] ?? 0) + 1
        return counts
      }, {})

    expect(types).toEqual({ fill_blank: 25, true_false: 25, single_choice: 50 })
    expect(
      Object.fromEntries(
        [
          "single_choice_direct",
          "fill_choice",
          "true_false",
          "single_choice_contextual",
        ].map((family) => [
          family,
          selected.filter((item) => item.family === family).length,
        ]),
      ),
    ).toEqual({
      single_choice_direct: 25,
      fill_choice: 25,
      true_false: 25,
      single_choice_contextual: 25,
    })
    expect([tfAnswers.Verdadero, tfAnswers.Falso].sort()).toEqual([12, 13])
    expect(selected.filter((item) => item.trapType === "true_elsewhere").length).toBe(25)
    expect(selected.filter((item) => item.semanticSkill === "scene_identification").length).toBeGreaterThanOrEqual(10)
    expect(new Set(selected.map((item) => item.factId)).size).toBe(100)
  })
})
