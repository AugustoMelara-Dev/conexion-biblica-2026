import { describe, expect, it } from "vitest"

import { scheduleNextRetrieval } from "@/domain/compressed-scheduler"

describe("compressed retrieval scheduler", () => {
  it("schedules a failed fact after intervening questions", () => {
    expect(scheduleNextRetrieval({ outcome: "incorrect", now: 1_000, tier: "A" })).toMatchObject({
      queueGap: 12,
      dueAt: null,
      reason: "repair",
    })
  })

  it("schedules a repaired fact 45 to 90 minutes later", () => {
    const next = scheduleNextRetrieval({ outcome: "repaired", now: 1_000, tier: "A" })
    expect(next.dueAt).toBe(1_000 + 60 * 60_000)
  })

  it("schedules a slow correct fact in four hours", () => {
    const next = scheduleNextRetrieval({ outcome: "slow_correct", now: 1_000, tier: "A" })
    expect(next.dueAt).toBe(1_000 + 4 * 3_600_000)
  })

  it("schedules a fast tier A fact in six hours", () => {
    const next = scheduleNextRetrieval({ outcome: "fast_correct", now: 1_000, tier: "A" })
    expect(next.dueAt).toBe(1_000 + 6 * 3_600_000)
  })
})
