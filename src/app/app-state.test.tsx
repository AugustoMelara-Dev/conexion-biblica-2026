import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { getPreferences, resolveAvailableBankSelection, resolveInitialBankSelection } from "@/app/app-state"

describe("preferencias y fallback de perfiles", () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it("mantiene el default histórico para una instalación existente sin preferencia", () => {
    expect(getPreferences().lastBankSelection).toBe("prep-v3")
  })

  it("conserva una preferencia V4 guardada", () => {
    localStorage.setItem("conexion-biblica-preferences", JSON.stringify({ lastBankSelection: "curated-v4" }))

    expect(getPreferences().lastBankSelection).toBe("curated-v4")
  })

  it("retrocede a V1 si V4 no está disponible", () => {
    expect(resolveAvailableBankSelection("curated-v4", ["legacy-v1"])).toBe("legacy-v1")
  })

  it("recomienda V4 sólo en una instalación nueva cuando carga", () => {
    expect(resolveInitialBankSelection({
      storedSelection: "prep-v3",
      hasStoredPreferences: false,
      hadExistingBanks: false,
      availableProfiles: ["curated-v4", "prep-v3"],
    })).toBe("curated-v4")
  })

  it("conserva el default histórico de una instalación existente", () => {
    expect(resolveInitialBankSelection({
      storedSelection: "prep-v3",
      hasStoredPreferences: false,
      hadExistingBanks: true,
      availableProfiles: ["curated-v4", "prep-v3"],
    })).toBe("prep-v3")
  })
})
