import { describe, expect, it } from "vitest"
import {
  computeSprintQuotas,
  emptyFactExposure,
  recordAttempt3x,
  buildSprintSimulationRounds,
} from "./sprint-3x"
import type { Question } from "./types"

function createMockQuestion(id: string, factId: string, work: "Daniel" | "Profetas y Reyes", chapter: number, type: "single_choice" | "fill_blank" | "true_false" = "single_choice"): Question {
  return {
    id,
    factId,
    factKey: factId,
    type,
    difficulty: 3,
    source: {
      work,
      chapter,
      version: "RVR1995",
      reference: `${work} ${chapter}:1`,
    },
    tags: [work, `ch${chapter}`],
    question: `Pregunta de prueba para ${factId}`,
    options: [
      { id: "0", text: "Opción A" },
      { id: "1", text: "Opción B" },
      { id: "2", text: "Opción C" },
      { id: "3", text: "Opción D" },
    ],
    correctAnswer: ["0"],
  }
}

describe("Sprint Nacional 3X Engine", () => {
  it("computes exact 70/30 distribution and chapter quotas for 100 questions", () => {
    const quotas = computeSprintQuotas(100, "70-30")
    expect(quotas.prTarget).toBe(70)
    expect(quotas.danTarget).toBe(30)
    
    // PR distribution: PR39 15%, PR40 15%, PR41 15%, PR42 15%, PR43 20%, PR44 20%
    expect(quotas.prByChapter[39]).toBe(11) // 70 * 0.15 = 10.5 -> 11
    expect(quotas.prByChapter[40]).toBe(11)
    expect(quotas.prByChapter[41]).toBe(11)
    expect(quotas.prByChapter[42]).toBe(11)
    expect(quotas.prByChapter[43]).toBe(14) // 70 * 0.20 = 14
    expect(quotas.prByChapter[44]).toBe(12) // 70 - 58 = 12

    // Daniel chapters: sum to 30
    const danTotal = Object.values(quotas.danByChapter).reduce((sum, v) => sum + v, 0)
    expect(danTotal).toBe(30)
    // No chapter left behind (Daniel 1-12 all present)
    for (let c = 1; c <= 12; c++) {
      expect(quotas.danByChapter[c]).toBeGreaterThan(0)
    }
  })

  it("handles alternative hidden mixes: 50/50 and 30/70", () => {
    const q50 = computeSprintQuotas(100, "50-50")
    expect(q50.prTarget).toBe(50)
    expect(q50.danTarget).toBe(50)

    const q30 = computeSprintQuotas(100, "30-70")
    expect(q30.prTarget).toBe(30)
    expect(q30.danTarget).toBe(70)
  })

  it("progresses through the 3-Exposure Contract and marks mastery only when eligible", () => {
    const now = Date.now()
    let progress = emptyFactExposure("DAN1-001")
    expect(progress.exposures_completed).toBe(0)
    expect(progress.mastery_3x).toBe(false)

    // Exposure 1: Fast correct
    progress = recordAttempt3x(progress, "Q-DAN1-001-A", true, false, 3500, now)
    expect(progress.exposures_completed).toBe(1)
    expect(progress.distinct_presentations_seen).toEqual(["Q-DAN1-001-A"])
    expect(progress.mastery_3x).toBe(false)

    // Exposure 2: Seen 4 hours later with second variant
    const timeExp2 = now + 4 * 60 * 60 * 1000
    progress = recordAttempt3x(progress, "Q-DAN1-001-B", true, false, 4200, timeExp2)
    expect(progress.exposures_completed).toBe(2)
    expect(progress.distinct_presentations_seen).toEqual(["Q-DAN1-001-A", "Q-DAN1-001-B"])
    expect(progress.mastery_3x).toBe(false)

    // Exposure 3: Seen next day (24h later) with third variant
    const timeExp3 = timeExp2 + 24 * 60 * 60 * 1000
    progress = recordAttempt3x(progress, "Q-DAN1-001-C", true, false, 3100, timeExp3)
    expect(progress.exposures_completed).toBe(3)
    expect(progress.distinct_presentations_seen).toEqual(["Q-DAN1-001-A", "Q-DAN1-001-B", "Q-DAN1-001-C"])
    expect(progress.mastery_3x).toBe(true)
  })

  it("delays mastery on errors, doubts, and slow responses (>6s)", () => {
    const now = Date.now()
    let progress = emptyFactExposure("PR39-001")

    // Slow response (>6s)
    progress = recordAttempt3x(progress, "Q-PR39-001-A", true, false, 8500, now)
    expect(progress.last_result).toBe("correct")
    expect(progress.mastery_3x).toBe(false)

    // Incorrect response
    progress = recordAttempt3x(progress, "Q-PR39-001-B", false, false, 2500, now + 1000)
    expect(progress.last_result).toBe("incorrect")
    expect(progress.mastery_3x).toBe(false)

    // Doubted correct response (treated almost as error)
    progress = recordAttempt3x(progress, "Q-PR39-001-C", true, true, 3000, now + 2000)
    expect(progress.last_result).toBe("doubted")
    expect(progress.mastery_3x).toBe(false)
  })

  it("selects a 100-question round with zero duplicate factIds and 5x20 simulation structure", () => {
    // Generate pool of 300 mock questions across all 18 chapters
    const pool: Question[] = []

    // PR chapters (39-44)
    for (let ch = 39; ch <= 44; ch++) {
      for (let i = 1; i <= 30; i++) {
        pool.push(createMockQuestion(`Q-PR-${ch}-${i}`, `F-PR-${ch}-${i}`, "Profetas y Reyes", ch))
      }
    }
    // Daniel chapters (1-12)
    for (let ch = 1; ch <= 12; ch++) {
      for (let i = 1; i <= 15; i++) {
        pool.push(createMockQuestion(`Q-DAN-${ch}-${i}`, `F-DAN-${ch}-${i}`, "Daniel", ch))
      }
    }

    const sim = buildSprintSimulationRounds(pool, 42)
    expect(sim.rounds).toHaveLength(5)
    expect(sim.rounds[0]).toHaveLength(20)
    expect(sim.rounds[1]).toHaveLength(20)
    expect(sim.rounds[2]).toHaveLength(20)
    expect(sim.rounds[3]).toHaveLength(20)
    expect(sim.rounds[4]).toHaveLength(20)

    const allSelected = sim.rounds.flat()
    expect(allSelected).toHaveLength(100)

    // Check no duplicate factId
    const seenFacts = new Set<string>()
    for (const q of allSelected) {
      expect(seenFacts.has(q.factId!)).toBe(false)
      seenFacts.add(q.factId!)
    }
  })
})
