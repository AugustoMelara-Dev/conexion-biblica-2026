import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"
import { MemoryCue, QuizPage } from "@/components/quiz-page"
import { ResultsPage } from "@/components/results-page"
import { FocusShell } from "@/components/layout/focus-shell"
import { QuestionRenderer } from "@/components/question-renderer"
import type { Question, Session, SessionConfig } from "@/domain/types"

vi.mock("@/app/app-state", () => ({
  useApp: () => ({
    progress: new Map(),
    recordAnswer: vi.fn(),
    recordReport: vi.fn(),
  }),
}))

afterEach(cleanup)

describe("pista de memoria", () => {
  it("muestra la pista únicamente cuando existe", () => {
    const { rerender } = render(<MemoryCue cue="D1: 10 días y 10 veces." />)
    expect(screen.getByText("Pista para recordar")).toBeInTheDocument()
    expect(screen.getByText("D1: 10 días y 10 veces.")).toBeInTheDocument()

    rerender(<MemoryCue />)
    expect(screen.queryByText("Pista para recordar")).not.toBeInTheDocument()
  })
})

describe("badge de perfil del banco", () => {
  it("expone el ID estable del perfil curado", () => {
    const question: Question = {
      id: "curated-question",
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
      factKey: "FACT-D01-001",
      question: "¿Pregunta de prueba?",
      options: [{ id: "A", text: "Respuesta" }],
      correctAnswer: ["A"],
      answerMode: "option_id",
    }
    const config: SessionConfig = {
      mode: "learn",
      count: 1,
      sourceWorks: ["Daniel"],
      chapters: [1],
      difficulties: [3],
      types: ["single_choice"],
      statuses: ["all"],
      shuffleQuestions: false,
      shuffleOptions: false,
      perQuestionSeconds: null,
      totalSeconds: null,
      bankSelection: "curated-v4",
      strategy: "coverage-cycle",
    }

    render(
      <QuizPage
        questions={[question]}
        config={config}
        onFinish={vi.fn()}
        onExit={vi.fn()}
      />
    )

    expect(screen.getByText("V4", { exact: true })).toHaveAttribute(
      "data-bank-profile",
      "curated-v4"
    )
  })
})

const studyQuestion: Question = {
  id: "study-question",
  type: "single_choice",
  difficulty: 2,
  source: {
    work: "Daniel",
    version: "RVR95",
    chapter: 1,
    reference: "Daniel 1:1",
  },
  tags: [],
  factKey: "FACT-D01-002",
  question: "¿Cuál es la respuesta de prueba?",
  options: [{ id: "A", text: "Respuesta" }],
  correctAnswer: ["A"],
  answerMode: "option_id",
}

const studyConfig: SessionConfig = {
  mode: "learn",
  count: 1,
  sourceWorks: ["Daniel"],
  chapters: [1],
  difficulties: [2],
  types: ["single_choice"],
  statuses: ["all"],
  shuffleQuestions: false,
  shuffleOptions: false,
  perQuestionSeconds: null,
  totalSeconds: null,
  bankSelection: "all",
  strategy: "random",
}

function renderQuiz() {
  return render(
    <FocusShell>
      <QuizPage
        questions={[studyQuestion]}
        config={studyConfig}
        onFinish={vi.fn()}
        onExit={vi.fn()}
      />
    </FocusShell>
  )
}

describe("ronda enfocada", () => {
  it("presenta metadatos, pregunta y acción dentro de la región de estudio", () => {
    renderQuiz()

    expect(screen.getByRole("main", { name: "Ronda de estudio" })).toBeVisible()
    expect(screen.getByText("Pregunta 1 de 1")).toBeVisible()
    expect(
      screen.getByRole("button", { name: "Confirmar respuesta" })
    ).toBeVisible()
  })

  it("expone las opciones únicas como un grupo de radios con su enunciado", () => {
    render(
      <QuestionRenderer
        question={studyQuestion}
        value={undefined}
        onChange={vi.fn()}
      />
    )

    expect(
      screen.getByRole("radiogroup", { name: studyQuestion.question })
    ).toBeVisible()
    expect(screen.getByRole("radio", { name: /Respuesta/ })).toHaveAttribute(
      "aria-checked",
      "false"
    )
  })
})

const sessionWithErrors: Session = {
  id: "results-with-errors",
  startedAt: 0,
  completedAt: 1_000,
  durationMs: 1_000,
  mode: "learn",
  context: "practice",
  config: studyConfig,
  questionKeys: ["local:study-question"],
  score: 0,
  answers: [
    {
      questionKey: "local:study-question",
      answer: "B",
      responseTimeMs: 1_000,
      result: { isCorrect: false, wasAnswered: true, reason: "incorrect" },
    },
  ],
}

describe("acciones de resultados", () => {
  it("prioriza repasar errores cuando hay respuestas incorrectas", () => {
    render(
      <ResultsPage
        session={sessionWithErrors}
        questions={[studyQuestion]}
        onErrors={vi.fn()}
        onRepeat={vi.fn()}
        onNext={vi.fn()}
        onRandom={vi.fn()}
        onNew={vi.fn()}
      />
    )

    expect(
      screen.getByRole("button", { name: "Repasar errores" })
    ).toHaveAttribute("data-variant", "default")
    expect(
      screen.getByRole("button", { name: "Repetir esta tanda" })
    ).toHaveAttribute("data-variant", "outline")
  })

  it("permite filtrar la lista para revisar solo las respuestas incorrectas", async () => {
    const user = userEvent.setup()
    render(
      <ResultsPage
        session={sessionWithErrors}
        questions={[studyQuestion]}
        onErrors={vi.fn()}
        onRepeat={vi.fn()}
        onNext={vi.fn()}
        onRandom={vi.fn()}
        onNew={vi.fn()}
      />
    )

    await user.click(screen.getByRole("switch", { name: "Solo incorrectas" }))

    expect(screen.getByText("Respuestas incorrectas")).toBeVisible()
  })
})
