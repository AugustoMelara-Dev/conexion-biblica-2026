import { describe, expect, it } from "vitest"
import {
  computeSprintQuotas,
  emptyFactExposure,
  recordAttempt3x,
  buildSprintSimulationRounds,
  selectSprintNacionalRound,
  getCanonicalPresentationId,
  distributeByLargestRemainder,
} from "./sprint-3x"
import type { Question } from "./types"

function createMockQuestion(
  id: string,
  factId: string,
  work: "Daniel" | "Profetas y Reyes",
  chapter: number,
  type: "single_choice" | "fill_blank" | "true_false" = "single_choice",
  family?: "single_choice_direct" | "fill_choice" | "true_false" | "single_choice_contextual",
  sourceUnitId = `SU-${work}-${chapter}`
): Question {
  return {
    id,
    factId,
    sourceUnitId,
    factKey: factId,
    type,
    family,
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
  it("computes exact 70/30 distribution and chapter quotas for 100 questions with Largest Remainder Method", () => {
    const quotas = computeSprintQuotas(100, "70-30", 0)
    expect(quotas.prTarget).toBe(70)
    expect(quotas.danTarget).toBe(30)

    // PR distribution: sum = 70
    const prTotal = Object.values(quotas.prByChapter).reduce((sum, v) => sum + v, 0)
    expect(prTotal).toBe(70)
    expect(quotas.prByChapter[43]).toBeGreaterThanOrEqual(14)
    expect(quotas.prByChapter[44]).toBeGreaterThanOrEqual(14)

    // Daniel chapters: sum = 30
    const danTotal = Object.values(quotas.danByChapter).reduce((sum, v) => sum + v, 0)
    expect(danTotal).toBe(30)
    // No chapter left behind (Daniel 1-12 all present)
    for (let c = 1; c <= 12; c++) {
      expect(quotas.danByChapter[c]).toBeGreaterThan(0)
    }

    // Family quotas sum to 100
    expect(quotas.familyQuotas.single_choice).toBe(45)
    expect(quotas.familyQuotas.fill_blank).toBe(30)
    expect(quotas.familyQuotas.true_false).toBe(25)
  })

  it("Largest Remainder Method distributes evenly without bias across tie seeds", () => {
    const items = [
      { key: "A", weight: 0.5 },
      { key: "B", weight: 0.5 },
    ]
    const res0 = distributeByLargestRemainder(3, items, 0)
    const res1 = distributeByLargestRemainder(3, items, 1)
    expect(res0["A"] + res0["B"]).toBe(3)
    expect(res1["A"] + res1["B"]).toBe(3)
    // Rotating tieSeed alternates which gets the odd unit
    expect(res0["A"]).toBe(2)
    expect(res1["A"]).toBe(1)
  })

  it("normalizes canonical presentation ID and ignores runtime option shuffling", () => {
    const q1 = createMockQuestion("V16-DAN1-001", "DAN1-F01", "Daniel", 1)
    const q1Shuffled = {
      ...q1,
      id: "V16-DAN1-001:runtime",
      metadata: { runtimeBaseVariantId: "V16-DAN1-001" },
    }
    expect(getCanonicalPresentationId(q1)).toBe("V16-DAN1-001")
    expect(getCanonicalPresentationId(q1Shuffled)).toBe("V16-DAN1-001")
  })

  it("progresses through 3-Exposure Contract and achieves Mastery 3X only with spaced next-day exposure", () => {
    const now = Date.now()
    const qA = createMockQuestion("Q-DAN1-001-A", "DAN1-001", "Daniel", 1)
    const qB = createMockQuestion("Q-DAN1-001-B", "DAN1-001", "Daniel", 1)
    const qC = createMockQuestion("Q-DAN1-001-C", "DAN1-001", "Daniel", 1)

    let progress = emptyFactExposure("DAN1-001")
    expect(progress.exposures_completed).toBe(0)
    expect(progress.mastery_3x).toBe(false)

    // Exposure 1: Fast correct
    progress = recordAttempt3x(progress, qA, true, false, 3500, now)
    expect(progress.exposures_completed).toBe(1)
    expect(progress.distinct_presentations_seen).toEqual(["Q-DAN1-001-A"])
    expect(progress.mastery_3x).toBe(false)

    // Exposure 2: Seen 4 hours later with second variant
    const timeExp2 = now + 4 * 60 * 60 * 1000
    progress = recordAttempt3x(progress, qB, true, false, 4200, timeExp2)
    expect(progress.exposures_completed).toBe(2)
    expect(progress.distinct_presentations_seen).toEqual(["Q-DAN1-001-A", "Q-DAN1-001-B"])
    expect(progress.mastery_3x).toBe(false)

    // Exposure 3: Seen same day (only 1 hour later) -> NOT yet mastery
    const timeSameDay = timeExp2 + 60 * 60 * 1000
    const progSameDay = recordAttempt3x(progress, qC, true, false, 3100, timeSameDay)
    expect(progSameDay.mastery_3x).toBe(false)

    // Exposure 3 on next day (24h later) -> achieves Mastery 3X!
    const timeNextDay = timeExp2 + 24 * 60 * 60 * 1000
    progress = recordAttempt3x(progress, qC, true, false, 3100, timeNextDay)
    expect(progress.exposures_completed).toBe(3)
    expect(progress.distinct_presentations_seen).toEqual(["Q-DAN1-001-A", "Q-DAN1-001-B", "Q-DAN1-001-C"])
    expect(progress.mastery_3x).toBe(true)
  })

  it("handles Unit Mastery 3X when fact has fewer than 3 public variants", () => {
    const now = Date.now()
    const q1 = createMockQuestion("Q-PR40-001", "PR40-F01", "Profetas y Reyes", 40, "single_choice", undefined, "PR40-P001")
    const q2 = createMockQuestion("Q-PR40-002", "PR40-F01", "Profetas y Reyes", 40, "fill_blank", undefined, "PR40-P001")
    const q3 = createMockQuestion("Q-PR40-003", "PR40-F01", "Profetas y Reyes", 40, "true_false", undefined, "PR40-P001")

    let progress = emptyFactExposure("PR40-F01", "PR40-P001")
    // availableFactVariantsCount = 2 (< 3)
    progress = recordAttempt3x(progress, q1, true, false, 4000, now, 2)
    progress = recordAttempt3x(progress, q2, true, false, 4000, now + 4 * 3600 * 1000, 2)
    progress = recordAttempt3x(progress, q3, true, false, 4000, now + 24 * 3600 * 1000, 2)

    expect(progress.missing_fact_variants).toBe(true)
    expect(progress.mastery_3x).toBe(false)
    expect(progress.unit_mastery_3x).toBe(true)
  })

  it("delays mastery on errors, doubts, and slow responses (>6s)", () => {
    const now = Date.now()
    const q = createMockQuestion("Q-PR39-001", "PR39-001", "Profetas y Reyes", 39)
    let progress = emptyFactExposure("PR39-001")

    // Slow response (>6s)
    progress = recordAttempt3x(progress, q, true, false, 8500, now)
    expect(progress.last_result).toBe("correct")
    expect(progress.mastery_3x).toBe(false)

    // Incorrect response
    progress = recordAttempt3x(progress, q, false, false, 2500, now + 1000)
    expect(progress.last_result).toBe("incorrect")
    expect(progress.mastery_3x).toBe(false)

    // Doubted correct response
    progress = recordAttempt3x(progress, q, true, true, 3000, now + 2000)
    expect(progress.last_result).toBe("doubted")
    expect(progress.mastery_3x).toBe(false)
  })

  it("selectSprintNacionalRound enforces simultaneous 70/30 material and 45/30/25 family quotas with zero duplicate facts", () => {
    // Generate pool of questions with balanced families
    const pool: Question[] = []
    const families: Array<"single_choice" | "fill_blank" | "true_false"> = [
      "single_choice",
      "single_choice",
      "fill_blank",
      "true_false",
    ]

    // PR chapters (39-44): 50 facts each = 300 facts
    for (let ch = 39; ch <= 44; ch++) {
      for (let i = 1; i <= 50; i++) {
        const fam = families[i % families.length]
        pool.push(createMockQuestion(`Q-PR-${ch}-${i}`, `F-PR-${ch}-${i}`, "Profetas y Reyes", ch, fam))
      }
    }
    // Daniel chapters (1-12): 25 facts each = 300 facts
    for (let ch = 1; ch <= 12; ch++) {
      for (let i = 1; i <= 25; i++) {
        const fam = families[i % families.length]
        pool.push(createMockQuestion(`Q-DAN-${ch}-${i}`, `F-DAN-${ch}-${i}`, "Daniel", ch, fam))
      }
    }

    const { questions, summary } = selectSprintNacionalRound(pool, 100, 42)
    expect(questions).toHaveLength(100)

    // Material quotas: exactly 70 PR and 30 Daniel
    expect(summary.prCount).toBe(70)
    expect(summary.danielCount).toBe(30)

    // Family quotas: 45 selection, 30 fill, 25 true/false
    expect(summary.familyCounts.single_choice).toBe(45)
    expect(summary.familyCounts.fill_blank).toBe(30)
    expect(summary.familyCounts.true_false).toBe(25)

    // Strategy recorded in summary
    expect(summary.strategy).toBe("sprint-3x")
    expect(summary.distinctFacts).toBe(100)
    expect(Object.keys(summary.quotaShortfalls)).toHaveLength(0)

    // Zero duplicate factIds
    const seen = new Set<string>()
    for (const q of questions) {
      expect(seen.has(q.factId!)).toBe(false)
      seen.add(q.factId!)
    }
  })

  it("buildSprintSimulationRounds produces 5 rounds of 20 with hidden mix and zero duplicates", () => {
    const pool: Question[] = []
    for (let ch = 39; ch <= 44; ch++) {
      for (let i = 1; i <= 40; i++) {
        pool.push(createMockQuestion(`Q-PR-${ch}-${i}`, `F-PR-${ch}-${i}`, "Profetas y Reyes", ch))
      }
    }
    for (let ch = 1; ch <= 12; ch++) {
      for (let i = 1; i <= 20; i++) {
        pool.push(createMockQuestion(`Q-DAN-${ch}-${i}`, `F-DAN-${ch}-${i}`, "Daniel", ch))
      }
    }

    const sim = buildSprintSimulationRounds(pool, 42)
    expect(["70-30", "50-50", "30-70"]).toContain(sim.mix)
    expect(sim.rounds).toHaveLength(5)
    sim.rounds.forEach((round) => expect(round).toHaveLength(20))

    const all = sim.rounds.flat()
    expect(all).toHaveLength(100)

    const facts = new Set(all.map((q) => q.factId))
    expect(facts.size).toBe(100)
  })
})
