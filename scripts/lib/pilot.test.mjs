import { describe, expect, it } from "vitest"
import { runPilot } from "./pilot.mjs"

function questions(band, count) {
  return Array.from({ length: count }, (_, index) => ({ id: `${band}-${index}`, factKey: `${band}-${index}`, difficultyBand: band, question: "Una pregunta con longitud suficiente", options: [{ text: "Respuesta uno" }, { text: "Respuesta dos" }], source: { work: index % 2 ? "Daniel" : "Profetas y Reyes", chapter: (index % 12) + 1 } }))
}

describe("simulacro piloto", () => {
  it("produce rondas completas, sin duplicados y con la mezcla objetivo", () => {
    const pool = [...questions("EXPERT", 80), ...questions("HARD", 80), ...questions("MEDIUM", 80), ...questions("BASIC", 80)]
    const result = runPilot(pool, { rounds: 10, count: 50, seed: 7 })
    expect(result.summary.completeRounds).toBe(10)
    expect(result.summary.roundsWithDuplicates).toBe(0)
    expect(result.summary.averageDifficultyMix).toMatchObject({ EXPERT: 20, HARD: 18, MEDIUM: 10, BASIC: 2 })
  })
})

