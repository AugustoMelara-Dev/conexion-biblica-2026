import { describe, expect, it } from "vitest"
import { calculateSessionScore, SIMULATION_PRESET } from "@/domain/simulation-calibration"
import type { SessionAnswer } from "@/domain/types"

function answer(isCorrect: boolean): SessionAnswer {
  return { questionKey: "bank:q", answer: "A", responseTimeMs: 5000, result: { isCorrect, wasAnswered: true, responseTimeMs: 5000, reason: isCorrect ? "correct" : "incorrect" } }
}

describe("calibración del simulacro", () => {
  it("usa un preset de 50 preguntas y diez minutos con margen de lectura", () => {
    expect(SIMULATION_PRESET).toEqual({ count: 50, perQuestionSeconds: 12, totalSeconds: 600 })
  })

  it("puntúa el simulacro de 0 a 100 y mantiene el conteo en práctica", () => {
    const answers = [answer(true), answer(true), answer(false), answer(false)]
    expect(calculateSessionScore("simulation", answers)).toBe(50)
    expect(calculateSessionScore("learn", answers)).toBe(2)
    expect(calculateSessionScore("simulation", [])).toBe(0)
  })
})

