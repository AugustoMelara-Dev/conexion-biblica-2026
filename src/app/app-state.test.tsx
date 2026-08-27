import { act, render, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
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

  it("activa el Banco Maestro Único cuando no existe preferencia", () => {
    expect(getPreferences().lastBankSelection).toBe("final-v7")
  })

  it("migra una preferencia V4 guardada al banco único", () => {
    localStorage.setItem(
      "conexion-biblica-preferences",
      JSON.stringify({ lastBankSelection: "curated-v4" })
    )

    expect(getPreferences().lastBankSelection).toBe("final-v7")
  })

  it("retrocede a V1 si V4 no está disponible", () => {
    expect(resolveAvailableBankSelection("curated-v4", ["legacy-v1"])).toBe(
      "legacy-v1"
    )
  })

  it("elige el banco único siempre que su manifiesto esté disponible", () => {
    expect(
      resolveInitialBankSelection({
        storedSelection: "prep-v3",
        hasStoredPreferences: false,
        hadExistingBanks: false,
        availableProfiles: ["final-v7", "curated-v4", "prep-v3"],
      })
    ).toBe("final-v7")
  })

  it("migra también una instalación existente al banco único", () => {
    expect(
      resolveInitialBankSelection({
        storedSelection: "prep-v3",
        hasStoredPreferences: false,
        hadExistingBanks: true,
        availableProfiles: ["final-v7", "curated-v4", "prep-v3"],
      })
    ).toBe("final-v7")
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

  it("aborta report y flag juntos si falla el segundo write y el retry crea un solo reporte", async () => {
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
      id: "atomic-report",
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
      factKey: "ATOMIC-REPORT-1",
      question: "¿Se confirma todo o nada?",
      options: [{ id: "A", text: "Sí" }],
      correctAnswer: ["A"],
    }
    const originalPut = IDBObjectStore.prototype.put
    let failProgressWrite = true
    const put = vi
      .spyOn(IDBObjectStore.prototype, "put")
      .mockImplementation(function (this: IDBObjectStore, value, key) {
        if (this.name === "progress" && failProgressWrite) {
          failProgressWrite = false
          throw new DOMException("forced second write failure", "DataError")
        }
        return Reflect.apply(
          originalPut,
          this,
          key === undefined ? [value] : [value, key]
        ) as IDBRequest<IDBValidKey>
      })
    try {
      await expect(
        context!.recordReport(question, "A", null, "Ambigua")
      ).rejects.toBeDefined()
      expect(await context!.repositories!.reports.list()).toEqual([])
      expect(
        await context!.repositories!.progress.get("curated-v4:atomic-report")
      ).toBeUndefined()

      await act(async () => {
        await context!.recordReport(question, "A", null, "Ambigua")
      })

      expect(await context!.repositories!.reports.list()).toHaveLength(1)
      expect(
        await context!.repositories!.progress.get("curated-v4:atomic-report")
      ).toMatchObject({ reported: true, timesSeen: 0 })
    } finally {
      put.mockRestore()
    }
  })
})
