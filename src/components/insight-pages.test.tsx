import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { useApp } from "@/app/app-state"
import { ReviewPage } from "@/components/review-page"
import { StatisticsPage } from "@/components/statistics-page"
import { FamilyMasteryPanel } from "@/components/family-mastery-panel"
import { HistoryPage } from "@/components/history-page"
import type {
  AnswerValue,
  Question,
  QuestionProgress,
  QuestionReport,
  Session,
} from "@/domain/types"
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
  questions = [question],
  sessions = [],
}: {
  reports?: ReturnType<typeof useApp>["reports"]
  progress?: Map<string, QuestionProgress>
  questions?: Question[]
  sessions?: Session[]
} = {}) {
  return {
    loading: false,
    error: null,
    masterBankError: null,
    nav: "stats",
    setNav: vi.fn(),
    banks: [],
    questions,
    allQuestions: questions,
    progress,
    sessions,
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
    statistics: buildStatistics(questions, progress),
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

function renderStatistics(overrides: Parameters<typeof createContext>[0] = {}) {
  vi.mocked(useApp).mockReturnValue(createContext(overrides))
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
    expect(screen.getByText("Capítulos con menor precisión")).toBeVisible()

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

  it("mide cobertura única y conserva tendencia y favoritas", () => {
    const repeated = { ...question, id: "repeated", factKey: "repeated" }
    const progress = new Map([
      [
        "curated-v4:repeated",
        {
          ...blankProgress,
          questionKey: "curated-v4:repeated",
          timesSeen: 10,
          timesCorrect: 8,
          timesIncorrect: 2,
          favorite: true,
        },
      ],
    ])
    renderStatistics({
      questions: [repeated],
      progress,
      sessions: [session("previous", 1, false), session("latest", 2, true)],
    })

    expect(screen.getByText("Cobertura")).toBeVisible()
    expect(screen.getByText("1/1")).toBeVisible()
    expect(screen.getByText("Tendencia")).toBeVisible()
    expect(screen.getByText("+100 pp")).toBeVisible()
    expect(screen.getByText("Favoritas")).toBeVisible()
    expect(
      within(screen.getByText("Favoritas").closest("li")!).getByText("1")
    ).toBeVisible()
  })

  it("mantiene las seis vistas estadísticas y sus encabezados accesibles", async () => {
    const user = userEvent.setup()
    renderStatistics()

    for (const [tab, heading] of [
      ["Capítulos", "Rendimiento por capítulo"],
      ["Tipos", "Rendimiento por tipo"],
      ["Familias", "Dominio por familia de conocimiento"],
      ["Dificultad", "Rendimiento por dificultad"],
      ["Fuentes", "Rendimiento por fuente"],
    ] as const) {
      await user.click(screen.getByRole("tab", { name: tab }))
      expect(screen.getByText(heading, { exact: true })).toBeVisible()
    }
    expect(screen.getAllByRole("columnheader").length).toBeGreaterThan(0)
  })

  it("mantiene filtros de familias anunciados y operables", async () => {
    const user = userEvent.setup()
    render(<FamilyMasteryPanel questions={[question]} progress={new Map()} />)

    const all = screen.getByRole("button", { name: /Todas/ })
    const pending = screen.getByRole("button", { name: /Pendiente/ })
    expect(all).toHaveAttribute("aria-pressed", "true")
    expect(pending).toHaveAttribute("aria-pressed", "false")
    await user.click(pending)
    expect(pending).toHaveAttribute("aria-pressed", "true")
    expect(all).toHaveAttribute("aria-pressed", "false")
  })

  it("filtra historial y expande detalles con preguntas no respondidas", async () => {
    const user = userEvent.setup()
    const unanswered = session("unanswered", 1, false, "unanswered")
    const simulation = session("simulation", 2, true, "correct")
    vi.mocked(useApp).mockReturnValue(
      createContext({ sessions: [unanswered, simulation] })
    )
    render(<HistoryPage />)

    expect(
      screen.getByRole("list", { name: "Sesiones guardadas" })
    ).toBeVisible()
    await user.selectOptions(screen.getByLabelText("Modo"), "simulation")
    expect(screen.getByText("Simulacro", { selector: "p" })).toBeVisible()
    expect(
      screen.queryByText("Aprender", { selector: "p" })
    ).not.toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText("Modo"), "learn")
    await user.click(document.querySelector("summary")!)
    expect(document.querySelector("details")).toHaveAttribute("open")
    expect(screen.getByText(/Sin responder/)).toBeVisible()
  })

  it("prioriza y distingue la taxonomía de revisión, filtros, detalle V4 y CTA", async () => {
    const user = userEvent.setup()
    const high: Question = {
      ...question,
      id: "high",
      difficulty: 5,
      question: "Alta dificultad",
      explanation: "Explicación V4",
    }
    const failed: Question = {
      ...question,
      id: "failed",
      difficulty: 2,
      question: "Fallada baja",
      source: { ...question.source, chapter: 2 },
    }
    const favorite: Question = {
      ...question,
      id: "favorite",
      difficulty: 2,
      question: "Favorita",
      factKey: "favorite-family",
    }
    const reported: Question = {
      ...question,
      id: "reported",
      difficulty: 2,
      question: "Solo reportada",
      factKey: "reported-family",
    }
    const reports = [
      report(high, "Ambigua", 4, null),
      report(failed, "Incorrecta", 3),
      report(favorite, "Ambigua", 2),
      report(reported, "Incorrecta", 1),
    ]
    const progress = new Map([
      ["curated-v4:high", { ...blankProgress, questionKey: "curated-v4:high" }],
      [
        "curated-v4:failed",
        {
          ...blankProgress,
          questionKey: "curated-v4:failed",
          timesIncorrect: 2,
        },
      ],
      [
        "curated-v4:favorite",
        {
          ...blankProgress,
          questionKey: "curated-v4:favorite",
          favorite: true,
        },
      ],
      [
        "curated-v4:reported",
        { ...blankProgress, questionKey: "curated-v4:reported" },
      ],
    ])
    const context = createContext({
      questions: [high, failed, favorite, reported],
      reports,
      progress,
    })
    vi.mocked(useApp).mockReturnValue(context)
    render(<ReviewPage />)

    const queue = screen.getByRole("list", {
      name: "Preguntas pendientes de revisión",
    })
    expect(
      within(queue)
        .getAllByRole("listitem")
        .map((item) => item.textContent)
    ).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Alta dificultad"),
        expect.stringContaining("Fallada baja"),
        expect.stringContaining("Favorita"),
        expect.stringContaining("Solo reportada"),
      ])
    )
    const items = within(queue).getAllByRole("listitem")
    expect(items).toHaveLength(4)
    expect(items[0]).toHaveTextContent("Alta dificultad")
    expect(within(items[0]).getByText("Difícil")).toBeVisible()
    expect(within(items[0]).queryByText("Fallada")).not.toBeInTheDocument()
    expect(within(items[1]).getByText("Fallada")).toBeVisible()
    expect(within(items[1]).queryByText("Difícil")).not.toBeInTheDocument()
    expect(
      within(items[2]).getByText("Favorita", { selector: "span" })
    ).toBeVisible()
    expect(within(items[3]).getByText("Reportada")).toBeVisible()
    await user.click(within(items[0]).getByText("Alta dificultad"))
    expect(within(items[0]).getByRole("group")).toHaveAttribute("open")
    expect(screen.getByText("Explicación completa")).toBeVisible()
    expect(
      within(items[0]).getByText(/ · V4 ·/, { selector: "p" })
    ).toBeVisible()
    expect(screen.getByText("Sin respuesta")).toBeVisible()
    const clipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard")
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: undefined,
    })
    await user.click(
      within(items[0]).getByRole("button", { name: "Copiar JSON" })
    )
    expect(screen.getByRole("status")).toHaveTextContent("No se pudo copiar")
    if (clipboard) Object.defineProperty(navigator, "clipboard", clipboard)
    else Reflect.deleteProperty(navigator, "clipboard")
    await user.selectOptions(screen.getByLabelText("Motivo"), "Incorrecta")
    expect(screen.queryByText("Alta dificultad")).not.toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText("Motivo"), "all")
    await user.selectOptions(screen.getByLabelText("Capítulo"), "Daniel:2")
    expect(screen.getByText("Fallada baja")).toBeVisible()
    await user.selectOptions(screen.getByLabelText("Capítulo"), "all")
    await user.selectOptions(
      screen.getByLabelText("Familia"),
      "favorite-family"
    )
    expect(screen.getByText("Favorita", { selector: "p" })).toBeVisible()
    expect(
      screen.queryByText("Solo reportada", { selector: "p" })
    ).not.toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Empezar una ronda" }))
    expect(context.setNav).toHaveBeenCalledWith("practice")
  })
})

function session(
  id: string,
  completedAt: number,
  correct: boolean,
  reason: "correct" | "unanswered" = "correct"
): Session {
  return {
    id,
    startedAt: completedAt - 1,
    completedAt,
    mode: correct ? "simulation" : "learn",
    context: correct ? "simulation" : "practice",
    config: {
      mode: correct ? "simulation" : "learn",
      count: 1,
      sourceWorks: ["Daniel"],
      chapters: [],
      difficulties: [],
      types: [],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      bankSelection: "curated-v4",
    },
    questionKeys: ["curated-v4:insight-question"],
    answers: [
      {
        questionKey: "curated-v4:insight-question",
        answer: reason === "unanswered" ? undefined : "A",
        responseTimeMs: 1_000,
        result: {
          isCorrect: correct,
          wasAnswered: reason !== "unanswered",
          responseTimeMs: 1_000,
          reason,
        },
      },
    ],
    score: correct ? 1 : 0,
    durationMs: 1_000,
  }
}

function report(
  nextQuestion: Question,
  reason: string,
  reportedAt: number,
  answer: AnswerValue = "A"
): QuestionReport {
  return {
    id: `report-${nextQuestion.id}`,
    questionKey: `${nextQuestion.bankId ?? "local"}:${nextQuestion.id}`,
    question: nextQuestion,
    reportedAt,
    answer,
    response: null,
    reason,
  }
}
