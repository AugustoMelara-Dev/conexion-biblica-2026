import { act, fireEvent, render, screen, within } from "@testing-library/react"
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
vi.mock("@/components/editorial-audit-panel", () => ({
  EditorialAuditPanel: () => <h2>Auditoría humana final</h2>,
}))

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
    massiveBankError: null,
    nav: "stats",
    setNav: vi.fn(),
    banks: [],
    questions,
    allQuestions: questions,
    progress,
    exposures: [],
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
    massiveManifest: null,
    refresh: async () => undefined,
    importBankFiles: async () => [],
    removeBank: async () => undefined,
    recordAnswer: async () => blankProgress,
    recordReport: async () => undefined,
    saveSession: async () => undefined,
    saveCoverageCycle: async () => undefined,
    saveActiveRound: async () => undefined,
    clearActiveRound: async () => undefined,
    loadMassiveQuestions: async () => [],
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

function renderReview(
  overrides: Parameters<typeof createContext>[0] = {},
  onPracticeQueue = vi.fn().mockResolvedValue(undefined)
) {
  vi.mocked(useApp).mockReturnValue(createContext(overrides))
  return {
    ...render(<ReviewPage onPracticeQueue={onPracticeQueue} />),
    onPracticeQueue,
  }
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
      screen.getByRole("heading", { name: "Auditoría humana final" }),
    ).toBeVisible()
    expect(
      screen.getByRole("heading", { name: "No hay preguntas pendientes" })
    ).toBeVisible()
    expect(
      screen.getByRole("button", { name: "Empezar una ronda" })
    ).toBeVisible()
  })

  it("forma la cola sin reportes con preguntas difíciles, falladas y favoritas", () => {
    const difficult = {
      ...question,
      id: "difficult-without-report",
      difficulty: 4 as const,
      question: "Difícil sin reporte",
    }
    const failed = {
      ...question,
      id: "failed-without-report",
      question: "Fallada sin reporte",
    }
    const favorite = {
      ...question,
      id: "favorite-without-report",
      question: "Favorita sin reporte",
    }
    renderReview({
      reports: [],
      questions: [difficult, failed, favorite],
      progress: new Map([
        [
          "curated-v4:failed-without-report",
          {
            ...blankProgress,
            questionKey: "curated-v4:failed-without-report",
            timesIncorrect: 1,
          },
        ],
        [
          "curated-v4:favorite-without-report",
          {
            ...blankProgress,
            questionKey: "curated-v4:favorite-without-report",
            favorite: true,
          },
        ],
      ]),
    })

    const rows = within(
      screen.getByRole("list", { name: "Preguntas pendientes de revisión" })
    ).getAllByRole("listitem")
    expect(rows).toHaveLength(3)
    expect(rows[0]).toHaveTextContent("Difícil sin reporte")
    expect(rows[1]).toHaveTextContent("Fallada sin reporte")
    expect(rows[2]).toHaveTextContent("Favorita sin reporte")
    expect(
      screen.queryByRole("heading", { name: "No hay preguntas pendientes" })
    ).not.toBeInTheDocument()
  })

  it("deduplica por questionKey, conserva filtros y entrega la cola enfocada al CTA", async () => {
    const user = userEvent.setup()
    const failed = {
      ...question,
      id: "union-failed",
      question: "Unión fallada",
      factKey: "union-family",
    }
    const reported = {
      ...question,
      id: "union-reported",
      question: "Unión reportada",
      factKey: "reported-family",
    }
    const onPracticeQueue = vi.fn().mockResolvedValue(undefined)
    renderReview(
      {
        questions: [failed, reported],
        reports: [
          report(failed, "Ambigua", 2),
          { ...report(failed, "Incorrecta", 3), id: "second-union-report" },
          report(reported, "Incorrecta", 1),
        ],
        progress: new Map([
          [
            "curated-v4:union-failed",
            {
              ...blankProgress,
              questionKey: "curated-v4:union-failed",
              timesIncorrect: 1,
            },
          ],
        ]),
      },
      onPracticeQueue
    )

    expect(
      within(
        screen.getByRole("list", { name: "Preguntas pendientes de revisión" })
      ).getAllByRole("listitem")
    ).toHaveLength(2)
    await user.selectOptions(screen.getByLabelText("Motivo"), "Ambigua")
    expect(screen.getByText("Unión fallada")).toBeVisible()
    expect(screen.queryByText("Unión reportada")).not.toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText("Motivo"), "all")
    await user.click(
      screen.getByRole("button", { name: "Practicar esta cola" })
    )

    expect(onPracticeQueue).toHaveBeenCalledTimes(1)
    expect(
      onPracticeQueue.mock.calls[0][0].map((item: Question) => item.id)
    ).toEqual(["union-failed", "union-reported"])
  })

  it("bloquea el doble inicio de la cola, anuncia el rechazo y permite reintentar", async () => {
    const pending = deferred<void>()
    const onPracticeQueue = vi
      .fn()
      .mockReturnValueOnce(pending.promise)
      .mockResolvedValueOnce(undefined)
    renderReview(
      {
        questions: [{ ...question, difficulty: 4 }],
        reports: [],
      },
      onPracticeQueue
    )
    const start = screen.getByRole("button", { name: "Practicar esta cola" })

    fireEvent.click(start)
    fireEvent.click(start)

    expect(onPracticeQueue).toHaveBeenCalledTimes(1)
    expect(start).toBeDisabled()
    await act(async () => pending.reject(new Error("storage denied")))
    expect(screen.getByRole("alert")).toHaveTextContent(
      "No se pudo iniciar la cola"
    )
    expect(start).toBeEnabled()

    await userEvent.click(start)
    expect(onPracticeQueue).toHaveBeenCalledTimes(2)
    expect(onPracticeQueue).toHaveBeenLastCalledWith([
      { ...question, difficulty: 4 },
    ])
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
    const pending: Question = {
      ...question,
      id: "pending-family",
      factKey: "pending-family",
      question: "Familia pendiente",
    }
    const mastered: Question = {
      ...question,
      id: "mastered-family",
      factKey: "mastered-family",
      question: "Familia dominada",
    }
    const progress = new Map([
      [
        "curated-v4:mastered-family",
        {
          ...blankProgress,
          questionKey: "curated-v4:mastered-family",
          timesSeen: 5,
          timesCorrect: 5,
          masteryScore: 5,
        },
      ],
    ])
    render(
      <FamilyMasteryPanel questions={[pending, mastered]} progress={progress} />
    )

    const all = screen.getByRole("button", { name: /Todas/ })
    const pendingButton = screen.getByRole("button", { name: /Pendiente/ })
    const masteredButton = screen.getByRole("button", { name: /Dominado/ })
    expect(all).toHaveAttribute("aria-pressed", "true")
    expect(pendingButton).toHaveAttribute("aria-pressed", "false")
    await user.click(pendingButton)
    expect(pendingButton).toHaveAttribute("aria-pressed", "true")
    expect(all).toHaveAttribute("aria-pressed", "false")
    expect(
      screen.getByText("Familia pendiente", { selector: "p" })
    ).toBeVisible()
    expect(
      screen.queryByText("Familia dominada", { selector: "p" })
    ).not.toBeInTheDocument()
    await user.click(masteredButton)
    expect(
      screen.getByText("Familia dominada", { selector: "p" })
    ).toBeVisible()
    expect(
      screen.queryByText("Familia pendiente", { selector: "p" })
    ).not.toBeInTheDocument()
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
    const answers = screen.getByRole("list", {
      name: "Respuestas de Aprender",
    })
    expect(within(answers).getAllByRole("listitem")).toHaveLength(1)
  })

  it("prioriza y distingue la taxonomía de revisión, historial migrado y CTA", async () => {
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
    const onPracticeQueue = vi.fn().mockResolvedValue(undefined)
    render(<ReviewPage onPracticeQueue={onPracticeQueue} />)

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
      within(items[0]).getByText(/ · Historial migrado ·/, { selector: "p" })
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
    expect(
      screen.queryByRole("button", { name: "Copiado" })
    ).not.toBeInTheDocument()
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
    await user.click(
      screen.getByRole("button", { name: "Practicar esta cola" })
    )
    expect(onPracticeQueue).toHaveBeenCalledWith([
      high,
      failed,
      favorite,
      reported,
    ])
  })

  it("expone dificultad manual, limita badges y conserva empates de revisión", async () => {
    const user = userEvent.setup()
    const manual: Question = {
      ...question,
      id: "manual",
      difficulty: 2,
      question: "Dificultad manual",
    }
    const combined: Question = {
      ...question,
      id: "combined",
      difficulty: 2,
      question: "Estado combinado",
    }
    const firstTie: Question = {
      ...question,
      id: "first-tie",
      difficulty: 2,
      question: "Empate primero",
    }
    const secondTie: Question = {
      ...question,
      id: "second-tie",
      difficulty: 2,
      question: "Empate segundo",
    }
    const progress = new Map([
      [
        "curated-v4:manual",
        {
          ...blankProgress,
          questionKey: "curated-v4:manual",
          markedDifficult: true,
        },
      ],
      [
        "curated-v4:combined",
        {
          ...blankProgress,
          questionKey: "curated-v4:combined",
          markedDifficult: true,
          timesIncorrect: 1,
          favorite: true,
        },
      ],
    ])
    renderReview({
      questions: [manual, combined, firstTie, secondTie],
      reports: [
        report(manual, "Ambigua", 4),
        report(combined, "Ambigua", 3),
        report(firstTie, "Ambigua", 1),
        report(secondTie, "Ambigua", 1),
      ],
      progress,
    })

    const rows = within(
      screen.getByRole("list", { name: "Preguntas pendientes de revisión" })
    ).getAllByRole("listitem")
    expect(rows[0]).toHaveTextContent("Estado combinado")
    expect(rows[1]).toHaveTextContent("Dificultad manual")
    expect(rows[1]).toHaveTextContent("Difícil")
    expect(rows[1]).not.toHaveTextContent("Fallada")
    expect(rows[0].querySelectorAll('[data-slot="badge"]')).toHaveLength(2)
    await user.click(within(rows[0]).getByText("Estado combinado"))
    expect(rows[0]).toHaveTextContent(
      "Estado: Difícil · Fallada · Favorita · Reportada"
    )
    expect(rows[2]).toHaveTextContent("Empate primero")
    expect(rows[3]).toHaveTextContent("Empate segundo")
  })

  it("muestra error de copia rechazada sin confirmar Copiado", async () => {
    const user = userEvent.setup()
    const clipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard")
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
    })
    try {
      renderReview({ reports: [report(question, "Ambigua", 1)] })
      await user.click(screen.getByText(question.question))
      await user.click(screen.getByRole("button", { name: "Copiar JSON" }))
      expect(screen.getByRole("status")).toHaveTextContent("No se pudo copiar")
      expect(
        screen.queryByRole("button", { name: "Copiado" })
      ).not.toBeInTheDocument()
    } finally {
      if (clipboard) Object.defineProperty(navigator, "clipboard", clipboard)
      else Reflect.deleteProperty(navigator, "clipboard")
    }
  })

  it("no limpia una confirmación nueva cuando se copia dos veces seguidas", async () => {
    vi.useFakeTimers()
    const clipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard")
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    })
    try {
      renderReview({ reports: [report(question, "Ambigua", 1)] })
      act(() => fireEvent.click(screen.getByText(question.question)))
      const copy = screen.getByRole("button", { name: "Copiar JSON" })
      await act(async () => {
        fireEvent.click(copy)
        await Promise.resolve()
      })
      act(() => vi.advanceTimersByTime(1_000))
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Copiado" }))
        await Promise.resolve()
      })
      act(() => vi.advanceTimersByTime(800))
      expect(screen.getByRole("button", { name: "Copiado" })).toBeVisible()
      act(() => vi.advanceTimersByTime(1_000))
      expect(screen.getByRole("button", { name: "Copiar JSON" })).toBeVisible()
    } finally {
      if (clipboard) Object.defineProperty(navigator, "clipboard", clipboard)
      else Reflect.deleteProperty(navigator, "clipboard")
      vi.useRealTimers()
    }
  })

  it("no actualiza ni agenda copia si el componente se desmonta con solicitudes pendientes", async () => {
    vi.useFakeTimers()
    const first = deferred<void>()
    const second = deferred<void>()
    const clipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard")
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: vi
          .fn()
          .mockReturnValueOnce(first.promise)
          .mockReturnValueOnce(second.promise),
      },
    })
    try {
      const { unmount } = renderReview({
        reports: [report(question, "Ambigua", 1)],
      })
      act(() => fireEvent.click(screen.getByText(question.question)))
      const copy = screen.getByRole("button", { name: "Copiar JSON" })
      fireEvent.click(copy)
      fireEvent.click(copy)
      unmount()
      const timerCount = vi.getTimerCount()
      await act(async () => {
        first.resolve()
        second.reject(new Error("denied"))
        await Promise.allSettled([first.promise, second.promise])
      })
      expect(vi.getTimerCount()).toBe(timerCount)
    } finally {
      if (clipboard) Object.defineProperty(navigator, "clipboard", clipboard)
      else Reflect.deleteProperty(navigator, "clipboard")
      vi.useRealTimers()
    }
  })

  it("conserva la segunda copia cuando la primera resuelve tarde", async () => {
    vi.useFakeTimers()
    const first = deferred<void>()
    const second = deferred<void>()
    const clipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard")
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: vi
          .fn()
          .mockReturnValueOnce(first.promise)
          .mockReturnValueOnce(second.promise),
      },
    })
    try {
      renderReview({ reports: [report(question, "Ambigua", 1)] })
      act(() => fireEvent.click(screen.getByText(question.question)))
      const copy = screen.getByRole("button", { name: "Copiar JSON" })
      fireEvent.click(copy)
      fireEvent.click(copy)
      const timerCount = vi.getTimerCount()
      await act(async () => {
        second.resolve()
        await second.promise
      })
      expect(screen.getByRole("button", { name: "Copiado" })).toBeVisible()
      expect(vi.getTimerCount()).toBe(timerCount + 1)
      await act(async () => {
        first.resolve()
        await first.promise
      })
      expect(screen.getByRole("button", { name: "Copiado" })).toBeVisible()
      expect(vi.getTimerCount()).toBe(timerCount + 1)
    } finally {
      if (clipboard) Object.defineProperty(navigator, "clipboard", clipboard)
      else Reflect.deleteProperty(navigator, "clipboard")
      vi.useRealTimers()
    }
  })

  it("ignora el rechazo tardío de una copia anterior", async () => {
    const first = deferred<void>()
    const second = deferred<void>()
    const clipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard")
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: vi
          .fn()
          .mockReturnValueOnce(first.promise)
          .mockReturnValueOnce(second.promise),
      },
    })
    try {
      renderReview({ reports: [report(question, "Ambigua", 1)] })
      act(() => fireEvent.click(screen.getByText(question.question)))
      const copy = screen.getByRole("button", { name: "Copiar JSON" })
      fireEvent.click(copy)
      fireEvent.click(copy)
      await act(async () => {
        second.resolve()
        await second.promise
      })
      await act(async () => {
        first.reject(new Error("late denied"))
        await first.promise.catch(() => undefined)
      })
      expect(screen.getByRole("button", { name: "Copiado" })).toBeVisible()
      expect(screen.queryByRole("status")).not.toBeInTheDocument()
    } finally {
      if (clipboard) Object.defineProperty(navigator, "clipboard", clipboard)
      else Reflect.deleteProperty(navigator, "clipboard")
    }
  })
})

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((nextResolve, nextReject) => {
    resolve = nextResolve
    reject = nextReject
  })
  return { promise, resolve, reject }
}

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
