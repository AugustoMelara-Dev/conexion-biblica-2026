import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest"

import { App } from "@/App"
import { useApp } from "@/app/app-state"
import { ThemeProvider } from "@/components/theme-provider"
import { buildStatistics } from "@/lib/statistics"
import type {
  ActiveRound,
  Question,
  QuestionProgress,
  SessionAnswer,
} from "@/domain/types"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

type AppContext = ReturnType<typeof useApp>

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

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
    exposures: [],
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
    massiveManifest: null,
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
    ...overrides,
    massiveBankError: overrides.massiveBankError ?? null,
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

function createBankQuestion(
  index: number,
  difficulty: Question["difficulty"] = 4
) {
  return {
    ...roundQuestion,
    id: `review-${index}`,
    difficulty,
    factKey: `APP-REVIEW-${index}`,
    question: `Pregunta de revisión ${index}`,
    options: [
      { id: "A", text: "Sí" },
      { id: "B", text: "No" },
    ],
  } satisfies Question
}

function keyOf(question: Question) {
  return `${question.bankId ?? "local"}:${question.id}`
}

function storedReviewRound(questions: Question[]): ActiveRound {
  return {
    id: "active",
    startedAt: 1,
    updatedAt: 1,
    currentIndex: questions.length - 1,
    questionKeys: questions.map(keyOf),
    answers: [],
    config: {
      mode: "smart-review",
      count: 20,
      sourceWorks: ["Daniel"],
      chapters: [],
      difficulties: [],
      types: [],
      statuses: ["all"],
      shuffleQuestions: false,
      shuffleOptions: false,
      perQuestionSeconds: null,
      totalSeconds: null,
      bankSelection: "curated-v4",
      strategy: "adaptive",
    },
    selectionSummary: { strategy: "adaptive" },
  }
}

function storedAnswer(question: Question, isCorrect: boolean): SessionAnswer {
  return {
    questionKey: keyOf(question),
    answer: isCorrect ? "A" : "B",
    result: {
      isCorrect,
      wasAnswered: true,
      responseTimeMs: 20,
      reason: isCorrect ? "correct" : "incorrect",
    },
    responseTimeMs: 20,
  }
}

async function finishRehydratedReviewRound(
  bank: Question[],
  subset: Question[],
  stored = storedReviewRound(subset),
  answerName: RegExp = /Sí/,
  overrides: Partial<AppContext> = {}
) {
  const user = userEvent.setup()
  const saveActiveRound = vi.fn().mockResolvedValue(undefined)
  const saveSession = vi.fn().mockResolvedValue(undefined)
  const clearActiveRound = vi.fn().mockResolvedValue(undefined)
  renderApp(
    activeRoundOverrides({
      questions: bank,
      allQuestions: bank,
      activeRound: stored,
      saveActiveRound,
      saveSession,
      clearActiveRound,
      ...overrides,
    })
  )
  await screen.findByRole("heading", { name: subset.at(-1)!.question })
  await user.click(screen.getByRole("radio", { name: answerName }))
  await user.click(screen.getByRole("button", { name: "Confirmar respuesta" }))
  await user.click(screen.getByRole("button", { name: "Ver resultados" }))
  await screen.findByRole("heading", {
    name: answerName.source.includes("Sí")
      ? "Ronda completada."
      : "Tu siguiente paso está claro.",
  })
  return { user, saveActiveRound, saveSession, clearActiveRound }
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
      screen.getByRole("status", { name: "Preparando tu banco maestro" })
    ).toHaveAttribute("aria-busy", "true")
    expect(
      screen.getByText("Cargando preguntas y progreso desde este dispositivo.")
    ).toHaveClass("sr-only")
    expect(screen.getAllByTestId("dashboard-skeleton")).toHaveLength(3)
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1)
  })

  it("mantiene el resumen usable cuando falla una carga histórica", () => {
    renderApp({ masterBankError: "Sin conexión" })

    expect(
      screen.getByText("Sin conexión")
    ).toBeVisible()
    expect(
      screen.getByRole("heading", { name: "PLAN FINAL — GANAR EL 29" })
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

  it("rehidrata, termina y repite exactamente las 2138 preguntas de la cola", async () => {
    const bank = Array.from({ length: 3_220 }, (_, index) =>
      createBankQuestion(index)
    )
    const subset = bank.slice(0, 2_138)
    const { user, saveActiveRound, saveSession } =
      await finishRehydratedReviewRound(bank, subset)
    const callsBeforeRepeat = saveActiveRound.mock.calls.length

    await user.click(screen.getByRole("button", { name: "Repetir esta tanda" }))

    await waitFor(() =>
      expect(saveActiveRound.mock.calls.length).toBeGreaterThan(
        callsBeforeRepeat
      )
    )
    const repeated = saveActiveRound.mock.calls
      .slice(callsBeforeRepeat)
      .map(([round]) => round as ActiveRound)
      .find((round) => round.currentIndex === 0)
    expect(repeated?.questionKeys).toEqual(subset.map(keyOf))
    expect(saveSession).toHaveBeenCalledTimes(1)
    expect(
      await screen.findByRole("heading", { name: subset[0].question })
    ).toBeVisible()
  })

  it("ordena aleatoriamente solo las 2138 preguntas del resultado y cambia solo strategy", async () => {
    const bank = Array.from({ length: 3_220 }, (_, index) =>
      createBankQuestion(index)
    )
    const subset = bank.slice(0, 2_138)
    const stored = storedReviewRound(subset)
    const { user, saveActiveRound } = await finishRehydratedReviewRound(
      bank,
      subset,
      stored
    )
    const callsBeforeRandom = saveActiveRound.mock.calls.length
    const random = vi.spyOn(Math, "random").mockReturnValue(0)
    try {
      await user.click(
        screen.getByRole("button", { name: "Otra tanda aleatoria" })
      )

      await waitFor(() =>
        expect(saveActiveRound.mock.calls.length).toBeGreaterThan(
          callsBeforeRandom
        )
      )
      const randomized = saveActiveRound.mock.calls
        .slice(callsBeforeRandom)
        .map(([round]) => round as ActiveRound)
        .find((round) => round.currentIndex === 0)!
      expect(randomized.questionKeys).toHaveLength(2_138)
      expect(new Set(randomized.questionKeys)).toEqual(
        new Set(subset.map(keyOf))
      )
      expect(randomized.questionKeys).not.toEqual(subset.map(keyOf))
      expect(randomized.config).toEqual({
        ...stored.config,
        strategy: "random-balanced",
      })
    } finally {
      random.mockRestore()
    }
  })

  it("solicita preguntas nuevas al banco masivo para otra tanda aleatoria", async () => {
    const previous = Array.from({ length: 20 }, (_, index) =>
      createBankQuestion(index)
    )
    const replacement = Array.from({ length: 40 }, (_, index) => ({
      ...createBankQuestion(1_000 + index),
      bankId: "final-v7",
      bankProfileId: "final-v7" as const,
      factId: `NEW-FACT-${index}`,
      variantId: `NEW-VARIANT-${index}`,
    }))
    const stored = {
      ...storedReviewRound(previous),
      config: {
        ...storedReviewRound(previous).config,
        bankSelection: "final-v7" as const,
        massive: true,
      },
    }
    const loadMassiveQuestions = vi.fn().mockResolvedValue(replacement)
    const { user, saveActiveRound } = await finishRehydratedReviewRound(
      previous,
      previous,
      stored,
      /Sí/,
      { loadMassiveQuestions },
    )
    const callsBeforeRandom = saveActiveRound.mock.calls.length

    await user.click(
      screen.getByRole("button", { name: "Otra tanda aleatoria" }),
    )

    await waitFor(() => expect(loadMassiveQuestions).toHaveBeenCalledTimes(1))
    const randomized = saveActiveRound.mock.calls
      .slice(callsBeforeRandom)
      .map(([round]) => round as ActiveRound)
      .find((round) => round.currentIndex === 0)!
    expect(randomized.questionKeys).toHaveLength(20)
    expect(
      randomized.questionKeys.every((key) => key.startsWith("final-v7:")),
    ).toBe(true)
    expect(new Set(randomized.questionKeys)).not.toEqual(
      new Set(previous.map(keyOf)),
    )
  })

  it("conserva todas las ocurrencias repetidas al ordenar aleatoriamente el subset", async () => {
    const bank = Array.from({ length: 3 }, (_, index) =>
      createBankQuestion(index)
    )
    const subset = [bank[0], bank[1], bank[0], bank[2], bank[1]]
    const stored = storedReviewRound(subset)
    const { user, saveActiveRound } = await finishRehydratedReviewRound(
      bank,
      subset,
      stored
    )
    const callsBeforeRandom = saveActiveRound.mock.calls.length
    const random = vi.spyOn(Math, "random").mockReturnValue(0)
    try {
      await user.click(
        screen.getByRole("button", { name: "Otra tanda aleatoria" })
      )

      await waitFor(() =>
        expect(saveActiveRound.mock.calls.length).toBeGreaterThan(
          callsBeforeRandom
        )
      )
      const randomized = saveActiveRound.mock.calls
        .slice(callsBeforeRandom)
        .map(([round]) => round as ActiveRound)
        .find((round) => round.currentIndex === 0)!
      expect(randomized.questionKeys).toHaveLength(5)
      expect(
        randomized.questionKeys.filter((key) => key === keyOf(bank[0]))
      ).toHaveLength(2)
      expect(
        randomized.questionKeys.filter((key) => key === keyOf(bank[1]))
      ).toHaveLength(2)
      expect(
        randomized.questionKeys.filter((key) => key === keyOf(bank[2]))
      ).toHaveLength(1)
      expect(randomized.questionKeys).not.toEqual(subset.map(keyOf))
      expect(randomized.config).toEqual({
        ...stored.config,
        strategy: "random-balanced",
      })
    } finally {
      random.mockRestore()
    }
  })

  it("mantiene Resultados ante un rechazo, bloquea doble acción y permite reintentar", async () => {
    const bank = [createBankQuestion(0)]
    const pending = deferred<void>()
    const { user, saveActiveRound } = await finishRehydratedReviewRound(
      bank,
      bank
    )
    const callsBeforeRepeat = saveActiveRound.mock.calls.length
    saveActiveRound
      .mockImplementationOnce(() => pending.promise)
      .mockResolvedValueOnce(undefined)
    const repeat = screen.getByRole("button", { name: "Repetir esta tanda" })

    fireEvent.click(repeat)
    fireEvent.click(repeat)
    expect(repeat).toBeDisabled()
    expect(saveActiveRound).toHaveBeenCalledTimes(callsBeforeRepeat + 1)

    await act(async () => pending.reject(new Error("storage denied")))
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No se pudo iniciar la práctica"
    )
    expect(
      screen.getByRole("heading", { name: "Ronda completada." })
    ).toBeVisible()
    expect(repeat).toBeEnabled()

    await user.click(repeat)
    await waitFor(() =>
      expect(saveActiveRound.mock.calls.length).toBeGreaterThan(
        callsBeforeRepeat + 1
      )
    )
    expect(
      await screen.findByRole("heading", { name: bank[0].question })
    ).toBeVisible()
  })

  it("repasa errores en el orden exacto de questionKeys del resultado", async () => {
    const bank = Array.from({ length: 5 }, (_, index) =>
      createBankQuestion(index, 2)
    )
    const subset = [bank[4], bank[0], bank[2]]
    const stored = {
      ...storedReviewRound(subset),
      answers: [storedAnswer(subset[0], false), storedAnswer(subset[1], true)],
    }
    const { user, saveActiveRound } = await finishRehydratedReviewRound(
      bank,
      subset,
      stored,
      /No/
    )
    const callsBeforeErrors = saveActiveRound.mock.calls.length

    await user.click(screen.getByRole("button", { name: "Repasar errores" }))

    await waitFor(() =>
      expect(saveActiveRound.mock.calls.length).toBeGreaterThan(
        callsBeforeErrors
      )
    )
    const errorsRound = saveActiveRound.mock.calls
      .slice(callsBeforeErrors)
      .map(([round]) => round as ActiveRound)
      .find((round) => round.currentIndex === 0)
    expect(errorsRound?.questionKeys).toEqual([keyOf(bank[4]), keyOf(bank[2])])
  })
})
