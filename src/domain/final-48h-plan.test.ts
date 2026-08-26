import { describe, expect, it } from "vitest"
import { buildFinal48HourPlan } from "@/domain/final-48h-plan"

describe("PLAN FINAL — 48 HORAS", () => {
  it("crea los diez bloques y conserva sus cantidades oficiales", () => {
    const plan = buildFinal48HourPlan([])
    expect(plan.map((block) => block.count)).toEqual([
      150, 150, 100, 100, 50, 150, 100, 100, 100, 100,
    ])
    expect(plan.filter((block) => block.day === 1)).toHaveLength(5)
    expect(plan.filter((block) => block.day === 2)).toHaveLength(5)
    expect(plan.at(-1)?.modeId).toBe("blind-simulation")
  })

  it("prioriza capítulos con más errores sin cambiar el tamaño del bloque", () => {
    const plan = buildFinal48HourPlan([
      { work: "Daniel", chapter: 11, incorrect: 20, slow: 3 },
      { work: "Profetas y Reyes", chapter: 44, incorrect: 15, slow: 5 },
      { work: "Daniel", chapter: 7, incorrect: 2, slow: 1 },
    ])
    const adaptive = plan.find((block) => block.id === "d1-errors-slow")
    expect(adaptive?.count).toBe(50)
    expect(adaptive?.focus).toEqual(
      expect.arrayContaining([
        { work: "Daniel", chapter: 11 },
        { work: "Profetas y Reyes", chapter: 44 },
      ])
    )
  })
})
