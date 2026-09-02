import { describe, expect, it, vi } from "vitest"
import { selectSprintNacionalRound } from "./sprint-3x"
import * as adaptiveModule from "./adaptive-session"
import type { Question } from "./types"

function createFullMockBank(): Question[] {
  const questions: Question[] = []
  const families: Array<"single_choice" | "fill_blank" | "true_false"> = [
    "single_choice",
    "single_choice",
    "fill_blank",
    "true_false",
  ]

  // PR 39-44
  for (let ch = 39; ch <= 44; ch++) {
    for (let i = 1; i <= 60; i++) {
      const fam = families[i % families.length]
      questions.push({
        id: `Q-PR-${ch}-${i}`,
        factId: `F-PR-${ch}-${i}`,
        factKey: `F-PR-${ch}-${i}`,
        sourceUnitId: `SU-PR-${ch}-${Math.ceil(i / 2)}`,
        type: fam,
        family: fam === "single_choice" ? "single_choice_contextual" : fam === "fill_blank" ? "fill_choice" : "true_false",
        difficulty: 3,
        source: {
          work: "Profetas y Reyes",
          chapter: ch,
          version: "RVR1995",
          reference: `PR ${ch}:${i}`,
        },
        tags: ["PR"],
        question: `Pregunta PR ${ch} #${i}`,
        options: [
          { id: "0", text: "Correcta" },
          { id: "1", text: "Distractor 1" },
          { id: "2", text: "Distractor 2" },
          { id: "3", text: "Distractor 3" },
        ],
        correctAnswer: ["0"],
      })
    }
  }

  // Daniel 1-12
  for (let ch = 1; ch <= 12; ch++) {
    for (let i = 1; i <= 35; i++) {
      const fam = families[i % families.length]
      questions.push({
        id: `Q-DAN-${ch}-${i}`,
        factId: `F-DAN-${ch}-${i}`,
        factKey: `F-DAN-${ch}-${i}`,
        sourceUnitId: `SU-DAN-${ch}-${Math.ceil(i / 2)}`,
        type: fam,
        family: fam === "single_choice" ? "single_choice_contextual" : fam === "fill_blank" ? "fill_choice" : "true_false",
        difficulty: 3,
        source: {
          work: "Daniel",
          chapter: ch,
          version: "RVR1995",
          reference: `Daniel ${ch}:${i}`,
        },
        tags: ["Daniel"],
        question: `Pregunta Daniel ${ch} #${i}`,
        options: [
          { id: "0", text: "Correcta" },
          { id: "1", text: "Distractor 1" },
          { id: "2", text: "Distractor 2" },
          { id: "3", text: "Distractor 3" },
        ],
        correctAnswer: ["0"],
      })
    }
  }

  return questions
}

describe("Sprint 3X Integration & Real Path Verification", () => {
  it("executes selectSprintNacionalRound and bypasses selectAdaptiveSession for sprint-nacional-3x", () => {
    const adaptiveSpy = vi.spyOn(adaptiveModule, "selectAdaptiveSession")
    const pool = createFullMockBank()

    const { questions, summary } = selectSprintNacionalRound(pool, 100, 12345)

    // Verify adaptive session selector was NOT invoked
    expect(adaptiveSpy).not.toHaveBeenCalled()

    // Verify exact contract specifications
    expect(questions).toHaveLength(100)
    expect(summary.strategy).toBe("sprint-3x")
    expect(summary.prCount).toBe(70)
    expect(summary.danielCount).toBe(30)
    expect(summary.familyCounts.single_choice).toBe(45)
    expect(summary.familyCounts.fill_blank).toBe(30)
    expect(summary.familyCounts.true_false).toBe(25)

    // PR distribution check
    expect(summary.chapterCounts["PR39"]).toBeGreaterThanOrEqual(10)
    expect(summary.chapterCounts["PR40"]).toBeGreaterThanOrEqual(10)
    expect(summary.chapterCounts["PR41"]).toBeGreaterThanOrEqual(10)
    expect(summary.chapterCounts["PR42"]).toBeGreaterThanOrEqual(10)
    expect(summary.chapterCounts["PR43"]).toBeGreaterThanOrEqual(13)
    expect(summary.chapterCounts["PR44"]).toBeGreaterThanOrEqual(13)

    // Daniel chapters: all 12 chapters represented
    for (let c = 1; c <= 12; c++) {
      expect(summary.chapterCounts[`DAN${c}`]).toBeGreaterThan(0)
    }

    // Zero duplicate facts
    expect(summary.distinctFacts).toBe(100)
    const factSet = new Set(questions.map((q) => q.factId))
    expect(factSet.size).toBe(100)

    adaptiveSpy.mockRestore()
  })

  it("strictly excludes blind and provisional questions from Sprint selection", () => {
    const pool = createFullMockBank()
    // Inject a blind question and a provisional question
    pool.push({
      ...pool[0],
      id: "Q-BLIND-001",
      factId: "F-BLIND-001",
      blindPool: "A",
    })
    pool.push({
      ...pool[1],
      id: "Q-PROV-001",
      factId: "F-PROV-001",
      metadata: { provisional: true },
    })

    const { questions } = selectSprintNacionalRound(pool, 100, 999)
    expect(questions.some((q) => q.blindPool !== undefined && q.blindPool !== null)).toBe(false)
    expect(questions.some((q) => q.metadata?.provisional === true)).toBe(false)
  })
})
