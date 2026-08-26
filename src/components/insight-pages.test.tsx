import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { useApp } from "@/app/app-state"
import { ReviewPage } from "@/components/review-page"
import { StatisticsPage } from "@/components/statistics-page"
import type { Question, QuestionProgress } from "@/domain/types"
import { buildStatistics } from "@/lib/statistics"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

const question: Question = {
  id: "insight-question",
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
  factKey: "DAN-1-1",
  question: "¿Pregunta para probar las vistas?",
  options: [{ id: "A", text: "Respuesta" }],
  correctAnswer: ["A"],
}

const blankProgress: QuestionProgress = {
  questionKey: "curated-v4:insight-question",
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

function createContext({
  reports = [],
  progress = new Map<string, QuestionProgress>(),
}: {
  reports?: ReturnType<typeof useApp>["reports"]
  progress?: Map<string, QuestionProgress>
} = {}) {
  return {
    loading: false,
    error: null,
    masterBankError: null,
    nav: "stats",
    setNav: vi.fn(),
    banks: [],
    questions: [question],
    allQuestions: [question],
    progress,
    sessions: [],
    reports,
    preferences: {
      theme: "system",
      lastMode: "learn",
      reducedMotion: false,
      lastBankSelection: "curated-v4",
    },
    bankSelection: "curated-v4",
    setBankSelection: vi.fn(),
    bankCounts: { legacy: 0, master: 0, prep: 0, curated: 1 },
    coverageCycles: new Map(),
    activeRound: null,
    statistics: buildStatistics([question], progress),
    refresh: async () => undefined,
    importBankFiles: async () => [],
    removeBank: async () => undefined,
    recordAnswer: async () => blankProgress,
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
  } as ReturnType<typeof useApp>
}

function renderStatistics() {
  vi.mocked(useApp).mockReturnValue(createContext())
  return render(<StatisticsPage />)
}

function renderReview(overrides: Parameters<typeof createContext>[0] = {}) {
  vi.mocked(useApp).mockReturnValue(createContext(overrides))
  return render(<ReviewPage />)
}

describe("vistas de progreso y revisión", () => {
  it("muestra una sola vista estadística a la vez", async () => {
    const user = userEvent.setup()
    renderStatistics()

    expect(screen.getByRole("tab", { name: "Resumen" })).toHaveAttribute(
      "aria-selected",
      "true"
    )
    expect(
      screen.queryByText("Dominio por familia de conocimiento")
    ).not.toBeInTheDocument()

    await user.click(screen.getByRole("tab", { name: "Familias" }))

    expect(
      screen.getByText("Dominio por familia de conocimiento")
    ).toBeVisible()
  })

  it("ofrece una acción clara cuando la revisión está vacía", () => {
    renderReview({ reports: [], progress: new Map() })

    expect(
      screen.getByRole("heading", { name: "No hay preguntas pendientes" })
    ).toBeVisible()
    expect(
      screen.getByRole("button", { name: "Empezar una ronda" })
    ).toBeVisible()
  })
})
