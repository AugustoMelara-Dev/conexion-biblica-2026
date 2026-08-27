import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import { describe, expect, it, vi } from "vitest"
import { useApp } from "@/app/app-state"
import { AdvancedSettings } from "@/components/practice/advanced-settings"
import {
  SequentialBlockPicker,
  SessionBuilderPage,
  StudyDayQuickStart,
} from "@/components/session-builder-page"
import { getQuestionKey } from "@/domain/banks"
import { buildPoolKey } from "@/domain/session-selection"
import type {
  CoverageCycle,
  Question,
  QuestionProgress,
  SessionConfig,
} from "@/domain/types"
import { buildStatistics } from "@/lib/statistics"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

type AppContext = ReturnType<typeof useApp>
type StartRound = (config: SessionConfig, resetCycle?: boolean) => void

const question: Question = {
  id: "session-builder-question",
  bankId: "BANCO_UNICO_CONEXION_BIBLICA_2026",
  bankProfileId: "final-v7",
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
  question: "¿Pregunta de prueba?",
  options: [{ id: "A", text: "Respuesta" }],
  correctAnswer: ["A"],
}

const defaultSessionConfig: SessionConfig = {
  mode: "learn",
  count: 10,
  sourceWorks: ["Daniel", "Profetas y Reyes"],
  chapters: [],
  difficulties: [1, 2, 3, 4, 5],
  types: [
    "single_choice",
    "fill_blank",
    "true_false",
  ],
  statuses: ["all"],
  shuffleQuestions: true,
  shuffleOptions: true,
  perQuestionSeconds: null,
  totalSeconds: null,
  bankSelection: "final-v7",
  strategy: "coverage-cycle",
  difficultyBands: ["BASIC", "MEDIUM", "HARD", "EXPERT", "UNRATED"],
}

function getQuestionProgress(input: Question): QuestionProgress {
  return {
    questionKey: getQuestionKey(input),
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
}

function createAppContext({
  coverageCycles,
  setBankSelection,
  questions = [question],
}: {
  coverageCycles: Map<string, CoverageCycle>
  setBankSelection: AppContext["setBankSelection"]
  questions?: Question[]
}): AppContext {
  const progress = new Map<string, QuestionProgress>()

  return {
    loading: false,
    error: null,
    masterBankError: null,
    massiveBankError: null,
    nav: "practice",
    setNav: vi.fn<AppContext["setNav"]>(),
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
      lastBankSelection: "final-v7",
    },
    bankSelection: "final-v7",
    setBankSelection,
    bankCounts: { legacy: 1, master: 0, prep: 0, curated: 0 },
    coverageCycles,
    activeRound: null,
    statistics: buildStatistics([question], progress),
    massiveManifest: null,
    finalManifest: {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 300,
      unique_facts: 75,
      shards: [
        {
          chapter: "DAN1",
          question_count: 300,
          training_question_count: 252,
          questions_file: "banks/final-2026/questions/DAN1.json",
        },
      ],
    },
    refresh: async () => undefined,
    importBankFiles: async () => [],
    removeBank: async () => undefined,
    recordAnswer: async (answeredQuestion) =>
      getQuestionProgress(answeredQuestion),
    recordReport: async () => undefined,
    saveSession: async () => undefined,
    saveCoverageCycle: async () => undefined,
    saveActiveRound: async () => undefined,
    clearActiveRound: async () => undefined,
    loadMassiveQuestions: async () => [],
    exportBanks: async () => [],
    exportProgress: async () => [],
    exportBackup: async () => ({
      backupVersion: "2.0",
      exportedAt: 0,
      banks: [],
      progress: [],
      sessions: [],
      reports: [],
      preferences: {
        theme: "system",
        lastMode: "learn",
        reducedMotion: false,
        lastBankSelection: "final-v7",
      },
      coverageCycles: [],
      activeRound: null,
    }),
    importBackup: async () => ({ valid: true, errors: [] }),
    setPreferences: vi.fn<AppContext["setPreferences"]>(),
    repositories: null,
  }
}

function renderSessionBuilder({
  onStart = vi.fn<StartRound>(),
  coverageCycles = new Map<string, CoverageCycle>(),
}: {
  onStart?: StartRound
  coverageCycles?: Map<string, CoverageCycle>
} = {}) {
  const setBankSelection = vi.fn<AppContext["setBankSelection"]>()
  vi.mocked(useApp).mockReturnValue(
    createAppContext({ coverageCycles, setBankSelection })
  )

  return {
    ...render(<SessionBuilderPage onStart={onStart} />),
    onStart,
    setBankSelection,
  }
}

describe("fixture de contexto", () => {
  it("crea progreso aislado y derivado de cada pregunta respondida", async () => {
    const context = createAppContext({
      coverageCycles: new Map(),
      setBankSelection: vi.fn<AppContext["setBankSelection"]>(),
    })
    const secondQuestion: Question = {
      ...question,
      id: "second-session-builder-question",
      factKey: "DAN-1-2",
    }
    const result = {
      isCorrect: true,
      wasAnswered: true,
      responseTimeMs: 1000,
      reason: "correct" as const,
    }

    const firstProgress = await context.recordAnswer(question, result, "A")
    const secondProgress = await context.recordAnswer(
      secondQuestion,
      result,
      "A"
    )

    expect(firstProgress).not.toBe(secondProgress)
    expect(firstProgress.history).not.toBe(secondProgress.history)
    expect(firstProgress.questionKey).toBe(getQuestionKey(question))
    expect(secondProgress.questionKey).toBe(getQuestionKey(secondQuestion))
  })
})

describe("controles de preparación V3", () => {
  it("conserva el bloque 2 como índice interno 1", async () => {
    const onChange = vi.fn()
    function ControlledPicker() {
      const [value, setValue] = useState(0)
      return (
        <SequentialBlockPicker
          blockCount={4}
          value={value}
          onChange={(next) => {
            onChange(next)
            setValue(next)
          }}
        />
      )
    }
    render(<ControlledPicker />)

    const picker = screen.getByRole("combobox", {
      name: "Bloque de preguntas",
    })
    await userEvent.selectOptions(picker, "2")

    expect(picker).toHaveValue("2")
    expect(onChange).toHaveBeenCalledWith(1)
  })

  it("emite el día elegido para iniciar una ruta V3", async () => {
    const onSelect = vi.fn()
    render(<StudyDayQuickStart onSelect={onSelect} />)

    await userEvent.click(screen.getByRole("button", { name: /Día 2/i }))

    expect(onSelect).toHaveBeenCalledWith(2)
  })

  it("mantiene la ruta rápida en un máximo de dos columnas editoriales", () => {
    render(<StudyDayQuickStart onSelect={vi.fn()} />)

    const grid = screen
      .getByRole("button", { name: /Día 1/i })
      .closest("[data-slot='card-content']")

    expect(grid).toHaveClass("md:grid-cols-2")
    expect(grid).not.toHaveClass("lg:grid-cols-4")
  })
})

describe("configuración progresiva de práctica", () => {
  it("habilita la ronda desde el manifiesto antes de cargar preguntas por capítulos", async () => {
    const user = userEvent.setup()
    const onStart = vi.fn<StartRound>()
    const setBankSelection = vi.fn<AppContext["setBankSelection"]>()
    vi.mocked(useApp).mockReturnValue(
      createAppContext({
        coverageCycles: new Map(),
        setBankSelection,
        questions: [],
      })
    )

    render(<SessionBuilderPage onStart={onStart} />)
    await user.click(
      screen.getByRole("button", { name: "Configuración avanzada" })
    )

    expect(screen.getByRole("button", { name: /D1\s+252/ })).toBeEnabled()
    expect(screen.getByRole("button", { name: "D2" })).toBeDisabled()
    expect(screen.getByText("252 preguntas disponibles con los filtros actuales.")).toBeVisible()
    await user.click(screen.getByRole("button", { name: "Comenzar ronda" }))
    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        bankSelection: "final-v7",
        massive: true,
      }),
      false
    )
  })

  it("oculta filtros secundarios hasta abrir configuración avanzada", async () => {
    const user = userEvent.setup()
    renderSessionBuilder()

    expect(screen.queryByText("Dificultad")).not.toBeInTheDocument()

    await user.click(
      screen.getByRole("button", { name: "Configuración avanzada" })
    )

    expect(screen.getByText("Dificultad")).toBeVisible()
    expect(screen.getByText("Tipos de pregunta")).toBeVisible()
  })

  it("mantiene visibles el banco canónico, cantidad y resumen", () => {
    renderSessionBuilder()

    expect(screen.getByText(/dentro del Banco Maestro Único/)).toBeVisible()
    expect(
      screen.queryByRole("combobox", { name: "Banco de preguntas" })
    ).not.toBeInTheDocument()
    expect(screen.getByRole("combobox", { name: "Cantidad" })).toBeVisible()
    expect(screen.getByText(/preguntas disponibles/)).toBeVisible()
    expect(screen.getByRole("button", { name: "Comenzar ronda" })).toBeEnabled()
  })

  it("expone nombres accesibles para los interruptores avanzados", async () => {
    const user = userEvent.setup()
    renderSessionBuilder()

    await user.click(
      screen.getByRole("button", { name: "Configuración avanzada" })
    )

    expect(
      screen.getByRole("switch", { name: "Temporizador total" })
    ).toBeVisible()
    expect(
      screen.getByRole("switch", { name: "Usar selección no secuencial" })
    ).toBeVisible()
    expect(
      screen.getByRole("switch", { name: "Aleatorizar opciones" })
    ).toBeVisible()
  })

  it("conserva filtros avanzados al cerrar y reabrir el disclosure", async () => {
    const user = userEvent.setup()
    const onStart = vi.fn<StartRound>()
    renderSessionBuilder({ onStart })

    const disclosure = screen.getByRole("button", {
      name: "Configuración avanzada",
    })
    await user.click(disclosure)
    await user.click(screen.getByRole("button", { name: "BASIC" }))
    await user.click(disclosure)
    await user.click(disclosure)
    await user.click(screen.getByRole("button", { name: "Comenzar ronda" }))

    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        difficultyBands: ["MEDIUM", "HARD", "EXPERT", "UNRATED"],
      }),
      false
    )
  })

  it("inicia un simulacro con su preset completo", async () => {
    const user = userEvent.setup()
    const onStart = vi.fn<StartRound>()
    renderSessionBuilder({ onStart })

    await user.click(screen.getByRole("button", { name: /Simulacro/ }))
    await user.click(screen.getByRole("button", { name: "Comenzar ronda" }))

    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        ...defaultSessionConfig,
        mode: "simulation",
        count: 50,
        perQuestionSeconds: 12,
        totalSeconds: 600,
      }),
      false
    )
  })

  it("mantiene el banco único en el payload de inicio", async () => {
    const user = userEvent.setup()
    const onStart = vi.fn<StartRound>()
    const { setBankSelection } = renderSessionBuilder({ onStart })

    await user.click(screen.getByRole("button", { name: "Comenzar ronda" }))

    expect(setBankSelection).not.toHaveBeenCalled()
    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        ...defaultSessionConfig,
        bankSelection: "final-v7",
      }),
      false
    )
  })

  it("preserva el payload completo y reinicia el ciclo agotado", async () => {
    const user = userEvent.setup()
    const onStart = vi.fn<StartRound>()
    const exhaustedCycle: CoverageCycle = {
      poolKey: buildPoolKey(defaultSessionConfig),
      cycleId: "exhausted-cycle",
      remainingQuestionKeys: [],
      seenQuestionKeys: [
        "BANCO_UNICO_CONEXION_BIBLICA_2026:session-builder-question",
      ],
      totalPoolSize: 1,
      createdAt: 1,
      updatedAt: 1,
    }
    renderSessionBuilder({
      onStart,
      coverageCycles: new Map([[exhaustedCycle.poolKey, exhaustedCycle]]),
    })

    await user.click(screen.getByRole("button", { name: "Comenzar ronda" }))

    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining(defaultSessionConfig),
      true
    )
  })
})

describe("AdvancedSettings", () => {
  it("asocia cada disclosure con un panel único", () => {
    render(
      <>
        <AdvancedSettings open onOpenChange={vi.fn()}>
          <p>Primer panel</p>
        </AdvancedSettings>
        <AdvancedSettings open onOpenChange={vi.fn()}>
          <p>Segundo panel</p>
        </AdvancedSettings>
      </>
    )

    const [first, second] = screen.getAllByRole("button", {
      name: "Configuración avanzada",
    })

    expect(first).toHaveAttribute("aria-controls")
    expect(second).toHaveAttribute("aria-controls")
    expect(first.getAttribute("aria-controls")).not.toBe(
      second.getAttribute("aria-controls")
    )
    expect(
      document.getElementById(first.getAttribute("aria-controls") ?? "")
    ).toBeVisible()
    expect(
      document.getElementById(second.getAttribute("aria-controls") ?? "")
    ).toBeVisible()
  })
})
