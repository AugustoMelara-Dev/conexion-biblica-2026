import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest"

import { App } from "@/App"
import { useApp } from "@/app/app-state"
import { ThemeProvider } from "@/components/theme-provider"
import { buildStatistics } from "@/lib/statistics"
import type { ActiveRound, Question, QuestionProgress } from "@/domain/types"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

type AppContext = ReturnType<typeof useApp>

const roundQuestion: Question = {
  id: "app-round-question",
  bankId: "curated-v4",
  bankProfileId: "curated-v4",
  type: "single_choice",
  difficulty: 4,
  source: {
    work: "Daniel",
    version: "RVR95",
    chapter: 1,
    reference: "Daniel 1:1",
  },
  tags: [],
  factKey: "APP-ROUND-1",
  question: "¿Pregunta persistida desde App?",
  options: [{ id: "A", text: "Sí" }],
  correctAnswer: ["A"],
}

const roundProgress: QuestionProgress = {
  questionKey: "curated-v4:app-round-question",
  timesSeen: 0,
  timesCorrect: 0,
  timesIncorrect: 0,
  timesUnanswered: 0,
  currentCorrectStreak: 0,
  averageResponseTimeMs: 0,
  bestResponseTimeMs: null,
  lastResponseTimeMs: null,
  lastSeenAt: null,
  masteryScore: 0,
  favorite: false,
  markedDifficult: false,
  reported: false,
  history: [],
}

const storedRound: ActiveRound = {
  id: "active",
  startedAt: 1,
  updatedAt: 1,
  currentIndex: 0,
  questionKeys: ["curated-v4:app-round-question"],
  answers: [],
  config: {
    mode: "learn",
    count: 1,
    sourceWorks: ["Daniel"],
    chapters: [],
    difficulties: [1, 2, 3, 4, 5],
    types: ["single_choice"],
    statuses: ["all"],
    shuffleQuestions: false,
    shuffleOptions: false,
    perQuestionSeconds: null,
    totalSeconds: null,
    bankSelection: "curated-v4",
  },
}

function activeRoundOverrides(overrides: Partial<AppContext> = {}) {
  return {
    questions: [roundQuestion],
    allQuestions: [roundQuestion],
    progress: new Map([[roundProgress.questionKey, roundProgress]]),
    activeRound: storedRound,
    recordAnswer: vi.fn().mockResolvedValue(roundProgress),
    ...overrides,
  } satisfies Partial<AppContext>
}

function createAppContext(overrides: Partial<AppContext> = {}): AppContext {
  const questions: Question[] = []
  const progress = new Map()

  return {
    loading: false,
    error: null,
    masterBankError: null,
    nav: "dashboard",
    setNav: vi.fn(),
    banks: [],
    questions,
    allQuestions: questions,
    progress,
    sessions: [],
    reports: [],
    preferences: {
      theme: "system",
      lastMode: "learn",
      reducedMotion: false,
      lastBankSelection: "curated-v4",
    },
    bankSelection: "curated-v4",
    setBankSelection: vi.fn(),
    bankCounts: { legacy: 0, master: 0, prep: 0, curated: 0 },
    coverageCycles: new Map(),
    activeRound: null,
    statistics: buildStatistics(questions, progress),
    refresh: async () => undefined,
    importBankFiles: async () => [],
    removeBank: async () => undefined,
    recordAnswer: async () => {
      throw new Error("No se usa en los estados de la aplicación")
    },
    recordReport: async () => undefined,
    saveSession: async () => undefined,
    saveCoverageCycle: async () => undefined,
    saveActiveRound: async () => undefined,
    clearActiveRound: async () => undefined,
    exportBanks: async () => [],
    exportProgress: async () => [],
    exportBackup: async () => ({
      backupVersion: "2.0" as const,
      exportedAt: 0,
      banks: [],
      progress: [],
      sessions: [],
      reports: [],
      preferences: {
        theme: "system" as const,
        lastMode: "learn" as const,
        reducedMotion: false,
        lastBankSelection: "curated-v4" as const,
      },
      coverageCycles: [],
      activeRound: null,
    }),
    importBackup: async () => ({ valid: true, errors: [] }),
    setPreferences: vi.fn(),
    repositories: null,
    ...overrides,
  }
}

function renderApp(overrides: Partial<AppContext> = {}) {
  vi.mocked(useApp).mockReturnValue(createAppContext(overrides))
  return render(
    <ThemeProvider disableTransitionOnChange={false}>
      <App />
    </ThemeProvider>
  )
}

afterEach(cleanup)

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: () => ({
      matches: false,
      media: "",
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    }),
  })
})

describe("estados transversales de App", () => {
  it("anuncia la carga ocupada con una estructura anticipada del resumen", () => {
    renderApp({ loading: true })

    expect(
      screen.getByRole("status", { name: "Preparando tus bancos" })
    ).toHaveAttribute("aria-busy", "true")
    expect(
      screen.getByText("Cargando preguntas y progreso desde este dispositivo.")
    ).toHaveClass("sr-only")
    expect(screen.getAllByTestId("dashboard-skeleton")).toHaveLength(3)
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1)
  })

  it("mantiene el resumen usable cuando la carga de V2 falla", () => {
    renderApp({ masterBankError: "Sin conexión" })

    expect(
      screen.getByText("Sin conexión. V1 continúa disponible.")
    ).toBeVisible()
    expect(
      screen.getByRole("heading", { name: "Entrena con intención." })
    ).toBeVisible()
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1)
  })

  it("inicia desde Revisión una ronda formada por la cola exacta", async () => {
    const user = userEvent.setup()
    const favorite = {
      ...roundQuestion,
      id: "app-favorite-question",
      difficulty: 2 as const,
      question: "Pregunta favorita desde App",
    }
    const saveActiveRound = vi.fn().mockResolvedValue(undefined)
    renderApp({
      nav: "review",
      questions: [roundQuestion, favorite],
      allQuestions: [roundQuestion, favorite],
      progress: new Map([
        [
          "curated-v4:app-favorite-question",
          {
            ...roundProgress,
            questionKey: "curated-v4:app-favorite-question",
            favorite: true,
          },
        ],
      ]),
      saveActiveRound,
    })

    await user.click(
      screen.getByRole("button", { name: "Practicar esta cola" })
    )

    await waitFor(() => expect(saveActiveRound).toHaveBeenCalled())
    expect(saveActiveRound).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        questionKeys: [
          "curated-v4:app-round-question",
          "curated-v4:app-favorite-question",
        ],
        config: expect.objectContaining({
          mode: "smart-review",
          count: "all",
        }),
      })
    )
  })

  it("propaga el fallo de finish al Quiz y reintenta la misma sesión", async () => {
    const user = userEvent.setup()
    const saveSession = vi
      .fn()
      .mockRejectedValueOnce(new Error("session denied"))
      .mockResolvedValueOnce(undefined)
    const clearActiveRound = vi.fn().mockResolvedValue(undefined)
    renderApp(
      activeRoundOverrides({
        saveSession,
        clearActiveRound,
      })
    )
    await screen.findByRole("heading", { name: roundQuestion.question })
    await user.click(screen.getByRole("radio", { name: /Sí/ }))
    await user.click(
      screen.getByRole("button", { name: "Confirmar respuesta" })
    )
    await user.click(screen.getByRole("button", { name: "Ver resultados" }))

    expect(
      await screen.findByText(/No se pudieron guardar los resultados/)
    ).toBeVisible()
    expect(clearActiveRound).not.toHaveBeenCalled()
    await user.click(screen.getByRole("button", { name: "Ver resultados" }))

    await waitFor(() => expect(saveSession).toHaveBeenCalledTimes(2))
    expect(saveSession.mock.calls[1][0].id).toBe(
      saveSession.mock.calls[0][0].id
    )
    expect(clearActiveRound).toHaveBeenCalledTimes(1)
  })

  it("propaga el fallo de exit al Quiz y permite reintentar", async () => {
    const user = userEvent.setup()
    const clearActiveRound = vi
      .fn()
      .mockRejectedValueOnce(new Error("clear denied"))
      .mockResolvedValueOnce(undefined)
    renderApp(activeRoundOverrides({ clearActiveRound }))
    await screen.findByRole("heading", { name: roundQuestion.question })

    await user.click(screen.getByRole("button", { name: "Salir" }))
    expect(
      await screen.findByText(/No se pudo salir de la ronda/)
    ).toBeVisible()
    await user.click(screen.getByRole("button", { name: "Salir" }))

    await waitFor(() => expect(clearActiveRound).toHaveBeenCalledTimes(2))
  })

  it("propaga el fallo de autosave y reintenta sin abandonar la ronda", async () => {
    const user = userEvent.setup()
    const saveActiveRound = vi
      .fn()
      .mockRejectedValueOnce(new Error("autosave denied"))
      .mockResolvedValueOnce(undefined)
    renderApp(activeRoundOverrides({ saveActiveRound }))

    expect(
      await screen.findByText(/No se pudo guardar el avance/)
    ).toBeVisible()
    expect(
      screen.getByRole("heading", { name: roundQuestion.question })
    ).toBeVisible()
    await user.click(
      screen.getByRole("button", { name: "Reintentar guardado" })
    )

    await waitFor(() => expect(saveActiveRound).toHaveBeenCalledTimes(2))
    expect(
      screen.queryByRole("button", { name: "Reintentar guardado" })
    ).not.toBeInTheDocument()
  })
})
