import { describe, expect, it } from "vitest"
import { MASSIVE_TRAINING_MODES, getMassiveTrainingMode } from "@/domain/training-modes"

describe("catálogo de modos masivos", () => {
  it("define exactamente los modos solicitados incluyendo sprint nacional 3x", () => {
    expect(MASSIVE_TRAINING_MODES).toHaveLength(22)
    expect(new Set(MASSIVE_TRAINING_MODES.map((mode) => mode.id)).size).toBe(22)
    expect(getMassiveTrainingMode("sprint-nacional-3x").count).toBe(100)
    expect(getMassiveTrainingMode("sprint-simulation-hidden").count).toBe(100)
    expect(getMassiveTrainingMode("national-final").count).toBe(100)
    expect(getMassiveTrainingMode("extreme-championship").count).toBe(200)
  })

  it("mantiene la reserva ciega fuera de práctica normal", () => {
    expect(getMassiveTrainingMode("blind-simulation").includeBlind).toBe(true)
    expect(
      MASSIVE_TRAINING_MODES.filter((mode) => mode.id !== "blind-simulation").every(
        (mode) => !mode.includeBlind
      )
    ).toBe(true)
  })
})
