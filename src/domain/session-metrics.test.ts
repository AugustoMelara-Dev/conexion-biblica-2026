import { describe, expect, it } from "vitest"
import { buildSessionMetrics } from "@/domain/session-metrics"
import type { Session } from "@/domain/types"

function session(context: "practice" | "simulation", score: number): Session {
  const answers = [true, true, false, false].map((isCorrect, index) => ({ questionKey: `q:${index}`, answer: "A", responseTimeMs: 1000, result: { isCorrect, wasAnswered: true, responseTimeMs: 1000, reason: isCorrect ? "correct" as const : "incorrect" as const } }))
  return { id: "s", startedAt: 1, completedAt: 2, mode: context === "simulation" ? "simulation" : "learn", context, config: {} as Session["config"], questionKeys: [], answers, score, durationMs: 4000 }
}

describe("métricas de sesión", () => {
  it("no vuelve a dividir la puntuación porcentual de un simulacro", () => {
    expect(buildSessionMetrics(session("simulation", 50))).toMatchObject({ accuracy: 50, scoreLabel: "50/100" })
  })

  it("conserva el conteo tradicional en las prácticas", () => {
    expect(buildSessionMetrics(session("practice", 2))).toMatchObject({ accuracy: 50, scoreLabel: "2/4" })
  })
})

