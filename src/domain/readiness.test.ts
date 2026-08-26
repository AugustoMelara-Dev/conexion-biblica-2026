import { describe, expect, it } from "vitest"

import { calculateChapterReadiness } from "@/domain/readiness"

describe("chapter readiness", () => {
  it("uses deferred, blind/new, fact coverage and time stability weights", () => {
    expect(calculateChapterReadiness({
      deferredAccuracy: 0.9,
      blindOrNovelAccuracy: 0.8,
      factCoverage: 0.7,
      timeStability: 0.6,
    })).toBe(80)
  })

  it("cannot reach one hundred from exposure coverage alone", () => {
    expect(calculateChapterReadiness({
      deferredAccuracy: 0,
      blindOrNovelAccuracy: 0,
      factCoverage: 1,
      timeStability: 1,
    })).toBe(30)
  })
})
