import { describe, expect, it } from "vitest"

import {
  buildFinalMissionPlan,
  getNextMission,
} from "@/domain/final-mission-plan"

const totalQuestions = (date: Date) =>
  buildFinalMissionPlan(date, { carryMissedNew: false }).reduce(
    (total, mission) => total + mission.count,
    0
  )

describe("Ruta del Día", () => {
  it("programa el lunes 31 con lectura y los cuatro bloques que suman 1,400", () => {
    const plan = buildFinalMissionPlan(new Date("2026-08-31T08:00:00-06:00"), {
      carryMissedNew: false,
    })

    expect(plan.map(({ kind, count }) => ({ kind, count }))).toEqual([
      { kind: "reading", count: 0 },
      { kind: "new", count: 850 },
      { kind: "hard-expert", count: 300 },
      { kind: "review", count: 150 },
      { kind: "simulation", count: 100 },
    ])
    expect(plan[0]).toMatchObject({
      reading: ["Daniel 1–6", "Profetas y Reyes 39–41"],
    })
    expect(plan.at(-1)?.description).toContain("5 × 20")
    expect(totalQuestions(new Date("2026-08-31T08:00:00-06:00"))).toBe(1_400)
  })

  it("programa el martes 1 con la segunda mitad del material y 1,400 preguntas", () => {
    const plan = buildFinalMissionPlan(new Date("2026-09-01T08:00:00-06:00"), {
      carryMissedNew: false,
    })

    expect(plan[0]).toMatchObject({
      kind: "reading",
      reading: ["Daniel 7–12", "Profetas y Reyes 42–44"],
    })
    expect(plan.slice(1).map(({ count }) => count)).toEqual([
      850, 300, 150, 100,
    ])
    expect(totalQuestions(new Date("2026-09-01T08:00:00-06:00"))).toBe(1_400)
  })

  it("conserva el enfoque y las simulaciones exigidas el miércoles y jueves", () => {
    const wednesday = buildFinalMissionPlan(
      new Date("2026-09-02T08:00:00-06:00"),
      {
        carryMissedNew: false,
      }
    )
    const thursday = buildFinalMissionPlan(
      new Date("2026-09-03T08:00:00-06:00"),
      {
        carryMissedNew: false,
      }
    )

    expect(wednesday.map((mission) => mission.kind)).toEqual([
      "reading",
      "new",
      "hard-expert",
      "review",
      "simulation",
      "simulation",
    ])
    expect(
      wednesday.filter((mission) => mission.kind === "simulation")
    ).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          count: 100,
          description: expect.stringContaining("5 × 20"),
        }),
      ])
    )
    expect(wednesday.reduce((sum, mission) => sum + mission.count, 0)).toBe(
      1_400
    )

    expect(thursday.map((mission) => mission.kind)).toEqual([
      "reading",
      "adversarial",
      "translation-noise",
      "review",
      "simulation",
      "simulation",
      "simulation",
    ])
    expect(
      thursday
        .filter((mission) => mission.kind === "simulation")
        .map((mission) => mission.sourceMix)
    ).toEqual([
      { daniel: 60, profetasReyes: 40 },
      { daniel: 50, profetasReyes: 50 },
      { daniel: 40, profetasReyes: 60 },
    ])
    expect(thursday.reduce((sum, mission) => sum + mission.count, 0)).toBe(
      1_400
    )
    expect(wednesday[0].reading).toEqual([
      "Daniel 1–12",
      "Profetas y Reyes 39–44",
    ])
    expect(thursday[0].reading).toEqual([
      "Daniel 1–12",
      "Profetas y Reyes 39–44",
    ])
  })

  it("traslada las nuevas vencidas al siguiente día en hora de Tegucigalpa", () => {
    const beforeMidnight = buildFinalMissionPlan(
      new Date("2026-09-01T05:59:59Z")
    )
    const afterMidnight = buildFinalMissionPlan(
      new Date("2026-09-01T06:00:00Z")
    )

    expect(
      beforeMidnight.find((mission) => mission.kind === "new")?.count
    ).toBe(850)
    expect(afterMidnight.find((mission) => mission.kind === "new")?.count).toBe(
      1_700
    )
    expect(afterMidnight.reduce((sum, mission) => sum + mission.count, 0)).toBe(
      2_250
    )
  })

  it("no traslada un bloque nuevo anterior que ya fue completado", () => {
    const plan = buildFinalMissionPlan(new Date("2026-09-01T08:00:00-06:00"), {
      completedMissionIds: ["2026-08-31-new"],
    })

    expect(plan.find((mission) => mission.kind === "new")?.count).toBe(850)
  })

  it("el viernes nunca supera 500 y termina temprano aunque haya nuevas vencidas", () => {
    const plan = buildFinalMissionPlan(new Date("2026-09-04T08:00:00-06:00"))

    expect(plan.map(({ kind, count }) => ({ kind, count }))).toEqual([
      { kind: "adversarial", count: 200 },
      { kind: "simulation", count: 100 },
      { kind: "review", count: 200 },
    ])
    expect(plan.reduce((sum, mission) => sum + mission.count, 0)).toBe(500)
    expect(
      plan.every(
        (mission) =>
          mission.description.includes("fallos") ||
          mission.kind === "simulation"
      )
    ).toBe(true)
    expect(
      plan.some((mission) => mission.description.includes("Termina temprano"))
    ).toBe(true)
  })

  it("el sábado solo ofrece un calentamiento opcional de 10–15 conocidas", () => {
    const plan = buildFinalMissionPlan(new Date("2026-09-05T08:00:00-06:00"))

    expect(plan).toHaveLength(1)
    expect(plan[0]).toMatchObject({
      kind: "warm-up",
      count: 15,
      optional: true,
      familiarity: "known",
    })
    expect(plan[0].description).toContain("Nada nuevo")
    expect(plan[0].description).toContain("sin maratón")
  })

  it("omite la lectura informativa y devuelve el primer bloque elegible pendiente", () => {
    const now = new Date("2026-08-31T09:00:00-06:00")
    const plan = buildFinalMissionPlan(now)
    const next = getNextMission(plan, new Set(), now)

    expect(next?.id).toBe("2026-08-31-new")
  })

  it("no repite el último bloque cuando toda la ruta está completa", () => {
    const now = new Date("2026-08-31T09:00:00-06:00")
    const plan = buildFinalMissionPlan(now)
    const completed = new Set(
      plan
        .filter((mission) => mission.kind !== "reading")
        .map((mission) => mission.id)
    )

    expect(getNextMission(plan, completed, now)).toBeNull()
  })
})
