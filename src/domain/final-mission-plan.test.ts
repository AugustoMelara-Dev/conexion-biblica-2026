import { describe, expect, it } from "vitest"

import { buildFinalMissionPlan, getNextMission } from "@/domain/final-mission-plan"

describe("PLAN FINAL — GANAR EL 29", () => {
  it("starts on August 26 with the required 150-question cold diagnosis", () => {
    const plan = buildFinalMissionPlan(new Date("2026-08-26T08:00:00-06:00"))
    expect(plan[0]).toMatchObject({
      id: "26-cold-tier-a",
      date: "2026-08-26",
      count: 150,
      exposureKind: "cold",
      chapters: [43, 44, 7, 8, 9, 11],
    })
  })

  it("keeps the complete Day 2 plan available on August 28", () => {
    const plan = buildFinalMissionPlan(new Date("2026-08-28T08:00:00-06:00"))
    expect(plan.map((mission) => mission.id)).toEqual([
      "27-morning",
      "27-context",
      "27-fill",
      "27-true-false",
      "27-blind-a",
      "27-repair",
      "27-blind-b",
      "27-red-sheet",
    ])
    expect(plan.filter((mission) => mission.blindPool).map((mission) => mission.blindPool)).toEqual(["A", "B"])
  })

  it("uses a short activation and no blind pool on competition day", () => {
    const plan = buildFinalMissionPlan(new Date("2026-08-29T07:00:00-06:00"))
    expect(plan).toHaveLength(1)
    expect(plan[0]).toMatchObject({ id: "29-activation", count: 50, blindPool: null })
  })

  it("returns the first unfinished mission for today", () => {
    const now = new Date("2026-08-26T09:00:00-06:00")
    const next = getNextMission(buildFinalMissionPlan(now), new Set(["26-cold-tier-a"]), now)
    expect(next?.id).toBe("26-guided-repair")
  })
})
