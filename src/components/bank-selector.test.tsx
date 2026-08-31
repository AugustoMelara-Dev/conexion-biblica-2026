import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { useApp } from "@/app/app-state"
import { BankSelector } from "@/components/bank-selector"
import { DashboardPage } from "@/components/dashboard-page"
import type { SessionConfig } from "@/domain/types"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

describe("selector de versión", () => {
  it("muestra detalle solo para el perfil seleccionado", async () => {
    const onChange = vi.fn()
    render(
      <BankSelector
        value="curated-v4"
        onChange={onChange}
        legacyCount={2360}
        masterCount={3558}
        prepCount={500}
        curatedCount={3220}
      />
    )

    expect(
      screen.getByRole("radiogroup", { name: "Versión del banco" })
    ).toBeInTheDocument()
    expect(screen.getAllByRole("radio")).toHaveLength(6)
    expect(
      screen.getByRole("region", { name: "Detalle del banco seleccionado" })
    ).toHaveTextContent("3,220 preguntas")

    await userEvent.click(
      screen.getByRole("radio", { name: /V3 — Preparación/ })
    )
    expect(onChange).toHaveBeenCalledWith("prep-v3")
  })

  it("no repite advertencias técnicas en opciones no seleccionadas", () => {
    render(
      <BankSelector
        value="curated-v4"
        onChange={vi.fn()}
        legacyCount={2360}
        masterCount={3558}
        prepCount={500}
        curatedCount={3220}
      />
    )

    expect(
      screen.queryByText("Advertencia técnica: conserva el texto original.")
    ).not.toBeInTheDocument()
  })

  it("ofrece el selector nativo etiquetado y conserva los IDs de callback", async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(
      <BankSelector
        value="curated-v4"
        onChange={onChange}
        legacyCount={2360}
        masterCount={3558}
        prepCount={500}
        curatedCount={3220}
      />
    )

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Seleccionar versión del banco" }),
      "master-v2"
    )
    expect(onChange).toHaveBeenCalledWith("master-v2")
  })
})

describe("inicio", () => {
  const dashboardState = (completedMissionIds: string[] = []) => ({
    statistics: {
      general: {
        total: 0,
        seen: 0,
        correct: 0,
        incorrect: 0,
        unanswered: 0,
        accuracy: 0,
        averageResponseTimeMs: 0,
        medianResponseTimeMs: 0,
        bestResponseTimeMs: 0,
        slowestResponseTimeMs: 0,
        unseen: 2_468,
        mastered: 0,
        difficult: 0,
        favorite: 0,
      },
      sources: [],
      chapters: [],
      difficulties: [],
      types: [],
      weakChapters: [],
      weakTypes: [],
      mostFailed: [],
      slowest: [],
    },
    banks: [],
    questions: [],
    sessions: completedMissionIds.map((trainingPresetId) => ({
      config: { trainingPresetId },
    })),
    progress: new Map(),
    setNav: vi.fn(),
    bankSelection: "final-v7",
    setBankSelection: vi.fn(),
    bankCounts: {},
  })

  async function startNextMission(
    now: string,
    completedMissionIds: string[] = []
  ) {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    vi.setSystemTime(new Date(now))
    vi.mocked(useApp).mockReturnValue(
      dashboardState(completedMissionIds) as never
    )
    const onStartMission = vi.fn<(config: SessionConfig) => void>()
    const view = render(<DashboardPage onStartMission={onStartMission} />)

    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    await user.click(screen.getByRole("button", { name: "CONTINUAR MI RUTA" }))

    expect(onStartMission).toHaveBeenCalledOnce()
    const config = onStartMission.mock.calls[0][0]
    view.unmount()
    vi.useRealTimers()
    return config
  }

  it("cablea nuevas y HARD/EXPERT a filtros ejecutables del selector", async () => {
    const unseen = await startNextMission("2026-08-31T08:00:00-06:00")
    expect(unseen).toMatchObject({
      mode: "new",
      statuses: ["new"],
      chapters: [1, 2, 3, 4, 5, 6, 39, 40, 41],
      trainingPresetId: "2026-08-31-new",
      massive: true,
    })

    const hardExpert = await startNextMission("2026-08-31T08:00:00-06:00", [
      "2026-08-31-new",
    ])
    expect(hardExpert).toMatchObject({
      mode: "difficult",
      difficulties: [4, 5],
      difficultyBands: ["HARD", "EXPERT"],
      statuses: ["all"],
      trainingPresetId: "2026-08-31-hard-expert",
    })
  })

  it("cablea repaso priorizado y simulación cronometrada sin falsear filtros", async () => {
    const review = await startNextMission("2026-08-31T08:00:00-06:00", [
      "2026-08-31-new",
      "2026-08-31-hard-expert",
    ])
    expect(review).toMatchObject({
      mode: "smart-review",
      statuses: ["all"],
      trainingPresetId: "2026-08-31-review",
    })

    const simulation = await startNextMission("2026-08-31T08:00:00-06:00", [
      "2026-08-31-new",
      "2026-08-31-hard-expert",
      "2026-08-31-review",
    ])
    expect(simulation).toMatchObject({
      mode: "simulation",
      count: 100,
      perQuestionSeconds: 25,
      totalSeconds: 2_500,
      trainingPresetId: "2026-08-31-simulation",
    })
  })

  it("usa solo los filtros realmente disponibles para adversariales, ruido y mezcla", async () => {
    const adversarial = await startNextMission("2026-09-03T08:00:00-06:00")
    expect(adversarial).toMatchObject({
      mode: "new",
      statuses: ["new"],
      sourceWorks: ["Daniel", "Profetas y Reyes"],
    })

    const translationNoise = await startNextMission(
      "2026-09-03T08:00:00-06:00",
      ["2026-09-03-adversarial"]
    )
    expect(translationNoise).toMatchObject({
      mode: "smart-review",
      statuses: ["all"],
      sourceWorks: ["Daniel", "Profetas y Reyes"],
    })

    const mixedSimulation = await startNextMission(
      "2026-09-03T08:00:00-06:00",
      [
        "2026-09-03-adversarial",
        "2026-09-03-translation-noise",
        "2026-09-03-review",
      ]
    )
    expect(mixedSimulation).toMatchObject({
      mode: "simulation",
      sourceWorks: ["Daniel", "Profetas y Reyes"],
      trainingPresetId: "2026-09-03-simulation-60-40",
    })
    expect(mixedSimulation).not.toHaveProperty("sourceMix")
  })

  it("limita el calentamiento a preguntas dominadas ya cargadas", async () => {
    const warmUp = await startNextMission("2026-09-05T08:00:00-06:00")
    expect(warmUp).toMatchObject({
      count: 15,
      statuses: ["mastered"],
      massive: false,
      trainingPresetId: "2026-09-05-warm-up",
    })
  })

  it("conserva el resumen de puntos débiles con acceso a práctica enfocada", async () => {
    const setNav = vi.fn()
    vi.mocked(useApp).mockReturnValue({
      statistics: {
        general: {
          total: 12,
          seen: 12,
          correct: 8,
          incorrect: 4,
          unanswered: 0,
          accuracy: 67,
          averageResponseTimeMs: 4000,
          medianResponseTimeMs: 4000,
          bestResponseTimeMs: 2500,
          slowestResponseTimeMs: 6000,
          unseen: 3,
          mastered: 2,
          difficult: 4,
          favorite: 0,
        },
        sources: [
          {
            key: "Daniel",
            label: "Daniel",
            total: 6,
            seen: 6,
            correct: 4,
            incorrect: 2,
            unanswered: 0,
            accuracy: 67,
            averageResponseTimeMs: 4000,
            mastery: 2,
          },
          {
            key: "Profetas y Reyes",
            label: "Profetas y Reyes",
            total: 6,
            seen: 6,
            correct: 4,
            incorrect: 2,
            unanswered: 0,
            accuracy: 67,
            averageResponseTimeMs: 4000,
            mastery: 2,
          },
        ],
        chapters: [],
        difficulties: [],
        types: [],
        weakChapters: [
          {
            key: "Daniel:2",
            label: "Daniel 2",
            total: 4,
            seen: 4,
            correct: 2,
            incorrect: 2,
            unanswered: 0,
            accuracy: 50,
            averageResponseTimeMs: 4500,
            mastery: 1,
            chapter: 2,
            source: "Daniel",
          },
        ],
        weakTypes: [
          {
            key: "single_choice",
            label: "Selección única",
            total: 4,
            seen: 4,
            correct: 2,
            incorrect: 2,
            unanswered: 0,
            accuracy: 50,
            averageResponseTimeMs: 4500,
            mastery: 1,
            type: "single_choice",
          },
        ],
        mostFailed: [{ id: "q-1" }, { id: "q-2" }],
        slowest: [],
      },
      banks: [],
      questions: [{ id: "q-1" }, { id: "q-2" }, { id: "q-3" }],
      sessions: [],
      progress: new Map(),
      setNav,
      bankSelection: "curated-v4",
      setBankSelection: vi.fn(),
      bankCounts: { legacy: 2360, master: 3558, prep: 500, curated: 3220 },
    } as never)

    render(<DashboardPage />)

    expect(
      screen.getByRole("heading", { name: "Mis puntos débiles" })
    ).toBeVisible()
    expect(
      screen.getByRole("progressbar", { name: "Precisión de Daniel" })
    ).toBeVisible()
    expect(
      screen.getByRole("progressbar", { name: "Precisión de Profetas y Reyes" })
    ).toBeVisible()
    expect(screen.getByText("Daniel 2")).toBeVisible()
    expect(screen.getByText("Selección única")).toBeVisible()
    expect(screen.getByText("2 preguntas detectadas")).toBeVisible()
    const weaknessSummary = screen
      .getByRole("region", { name: "Mis puntos débiles" })
      .querySelector(":scope > div")
    expect(weaknessSummary).toHaveClass("lg:grid-cols-3")
    expect(weaknessSummary).not.toHaveClass("sm:grid-cols-3")

    await userEvent.click(
      screen.getByRole("button", { name: "Abrir práctica enfocada" })
    )
    expect(setNav).toHaveBeenCalledWith("practice")
  })
})
