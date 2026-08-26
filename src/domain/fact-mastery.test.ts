import { describe, expect, it } from "vitest"

import { applyFactEvidence, emptyFactMastery } from "@/domain/fact-mastery"

const HOUR = 3_600_000
const base = {
  factId: "DAN7-V19-F01",
  variantId: "v1",
  semanticSkill: "contextual_precision",
  sessionId: "s1",
  occurredAt: Date.UTC(2026, 7, 26, 8),
  isCorrect: true,
  firstAttempt: true,
  hintUsed: false,
  afterFeedback: false,
  responseTimeMs: 4_000,
  personalMedianMs: 5_000,
  difficulty: 4 as const,
  exposureKind: "cold" as const,
}

describe("fact mastery evidence", () => {
  it("marks an immediate correction as repaired without mastery evidence", () => {
    const next = applyFactEvidence(emptyFactMastery(base.factId), {
      ...base,
      afterFeedback: true,
    })
    expect(next.state).toBe("repaired")
    expect(next.evidencePoints).toBe(0)
    expect(next.qualifyingFirstAttempts).toBe(0)
  })

  it("does not award mastery evidence when a hint was used", () => {
    const next = applyFactEvidence(emptyFactMastery(base.factId), {
      ...base,
      hintUsed: true,
    })
    expect(next.evidencePoints).toBe(0)
    expect(next.state).toBe("exposed")
  })

  it("marks a slow correct response as fragile and caps evidence at ten", () => {
    const next = applyFactEvidence(emptyFactMastery(base.factId), {
      ...base,
      responseTimeMs: 8_000,
    })
    expect(next.state).toBe("fragile")
    expect(next.evidencePoints).toBe(10)
  })

  it("requires semantic and temporal separation before mastered", () => {
    let mastery = emptyFactMastery(base.factId)
    mastery = applyFactEvidence(mastery, base)
    mastery = applyFactEvidence(mastery, {
      ...base,
      variantId: "v2",
      semanticSkill: "comparison",
      sessionId: "s2",
      occurredAt: base.occurredAt + 7 * HOUR,
      exposureKind: "deferred",
    })
    mastery = applyFactEvidence(mastery, {
      ...base,
      variantId: "v3",
      semanticSkill: "exact_text_recall",
      sessionId: "s3",
      occurredAt: base.occurredAt + 25 * HOUR,
      exposureKind: "deferred",
    })
    expect(mastery.state).toBe("mastered")
    expect(mastery.sessionIds).toHaveLength(3)
    expect(mastery.semanticSkills).toHaveLength(3)
  })

  it("moves a mastered fact to lapsed after a failure", () => {
    const mastered = {
      ...emptyFactMastery(base.factId),
      state: "mastered" as const,
      evidencePoints: 90,
    }
    const next = applyFactEvidence(mastered, { ...base, isCorrect: false })
    expect(next.state).toBe("lapsed")
    expect(next.evidencePoints).toBe(65)
  })
})
