import { act, render, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import {
  AppProvider,
  getPreferences,
  resolveAvailableBankSelection,
  resolveInitialBankSelection,
  useApp,
} from "@/app/app-state"
import type { Question } from "@/domain/types"
import { deleteAppDb } from "@/storage/db"

describe("preferencias y fallback de perfiles", () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it("mantiene el default histórico para una instalación existente sin preferencia", () => {
    expect(getPreferences().lastBankSelection).toBe("prep-v3")
  })

  it("conserva una preferencia V4 guardada", () => {
    localStorage.setItem(
      "conexion-biblica-preferences",
      JSON.stringify({ lastBankSelection: "curated-v4" })
    )

    expect(getPreferences().lastBankSelection).toBe("curated-v4")
  })

  it("retrocede a V1 si V4 no está disponible", () => {
    expect(resolveAvailableBankSelection("curated-v4", ["legacy-v1"])).toBe(
      "legacy-v1"
    )
  })

  it("recomienda V4 sólo en una instalación nueva cuando carga", () => {
    expect(
      resolveInitialBankSelection({
        storedSelection: "prep-v3",
        hasStoredPreferences: false,
        hadExistingBanks: false,
        availableProfiles: ["curated-v4", "prep-v3"],
      })
    ).toBe("curated-v4")
  })

  it("conserva el default histórico de una instalación existente", () => {
    expect(
      resolveInitialBankSelection({
        storedSelection: "prep-v3",
        hasStoredPreferences: false,
        hadExistingBanks: true,
        availableProfiles: ["curated-v4", "prep-v3"],
      })
    ).toBe("prep-v3")
  })
})

describe("persistencia concurrente de progreso", () => {
  beforeEach(async () => {
    localStorage.clear()
    await deleteAppDb()
  })

  afterEach(async () => {
    await deleteAppDb()
  })

  it("conserva contadores de respuesta y bandera de reporte para la misma pregunta", async () => {
    let context: ReturnType<typeof useApp> | undefined
    function Probe() {
      const value = useApp()
      if (!value.loading && value.repositories) context = value
      return null
    }
    render(
      <AppProvider>
        <Probe />
      </AppProvider>
    )
    await waitFor(() => expect(context).toBeDefined())
    const question: Question = {
      id: "concurrent-progress",
      bankId: "curated-v4",
      bankProfileId: "curated-v4",
      type: "single_choice",
      difficulty: 3,
      source: {
        work: "Daniel",
        version: "RVR95",
        chapter: 1,
        reference: "Daniel 1:1",
      },
      tags: [],
      factKey: "CONCURRENT-1",
      question: "¿Se preservan ambos cambios?",
      options: [{ id: "A", text: "Sí" }],
      correctAnswer: ["A"],
    }

    await act(async () => {
      await Promise.all([
        context!.recordAnswer(
          question,
          {
            isCorrect: true,
            wasAnswered: true,
            responseTimeMs: 250,
            reason: "correct",
          },
          "A"
        ),
        context!.recordReport(question, "A", null, "Ambigua"),
      ])
    })

    expect(
      await context!.repositories!.progress.get(
        "curated-v4:concurrent-progress"
      )
    ).toMatchObject({
      timesSeen: 1,
      timesCorrect: 1,
      timesIncorrect: 0,
      timesUnanswered: 0,
      reported: true,
    })
  })
})
