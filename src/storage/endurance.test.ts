import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { applyProgress } from "@/domain/mastery"
import { createRepositories, deleteAppDb, openAppDb } from "@/storage/db"

describe("resistencia de persistencia", () => {
  beforeEach(async () => {
    await deleteAppDb()
  })

  afterEach(async () => {
    await deleteAppDb()
  })

  it("conserva contadores e historial tras 3,000 respuestas distribuidas", async () => {
    const repositories = createRepositories(await openAppDb())
    const attempts = 3_000
    const facts = 600

    for (let index = 0; index < attempts; index += 1) {
      const factIndex = index % facts
      const variantIndex = Math.floor(index / facts) % 4
      const factId = `DAN7-ENDURANCE-${factIndex}`
      const variantId = `${factId}-V${variantIndex}`
      const questionKey = `final-v7:${variantId}`
      const isCorrect = index % 7 !== 0
      const responseTimeMs = 1_500 + (index % 12) * 750
      const timestamp = 1_800_000_000_000 + index * 1_000

      await repositories.exposures.record({
        factId,
        variantId,
        questionKey,
        timestamp,
        isCorrect,
        responseTimeMs,
        selectedAnswer: isCorrect ? "correcta" : "distractor",
        errorType: isCorrect ? null : "contextual_confusion",
        exposureKind: "practice",
      })
      await repositories.progress.update(questionKey, (current) => ({
        ...applyProgress(
          current,
          {
            isCorrect,
            wasAnswered: true,
            responseTimeMs,
            reason: isCorrect ? "correct" : "incorrect",
          },
          timestamp
        ),
        questionKey,
      }))
    }

    const exposures = await repositories.exposures.list()
    const progress = await repositories.progress.list()
    expect(exposures).toHaveLength(facts * 4)
    expect(progress).toHaveLength(facts * 4)
    expect(exposures.reduce((sum, row) => sum + row.exposures, 0)).toBe(
      attempts
    )
    expect(progress.reduce((sum, row) => sum + row.timesSeen, 0)).toBe(attempts)
    expect(progress.every((row) => row.history.length <= 30)).toBe(true)
    expect(
      exposures.every(
        (row) =>
          row.exposures === row.correct + row.incorrect &&
          Number.isFinite(row.averageResponseTimeMs)
      )
    ).toBe(true)
  }, 120_000)
})
