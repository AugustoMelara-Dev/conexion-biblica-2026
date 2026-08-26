import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest"
import { MemoryCue, QuizPage } from "@/components/quiz-page"
import { ResultsPage } from "@/components/results-page"
import { FocusShell } from "@/components/layout/focus-shell"
import { QuestionRenderer } from "@/components/question-renderer"
import type { Question, Session, SessionConfig } from "@/domain/types"

const appState = vi.hoisted(() => ({
  recordAnswer: vi.fn(),
  recordReport: vi.fn(),
}))

vi.mock("@/app/app-state", () => ({
  useApp: () => ({
    progress: new Map(),
    recordAnswer: appState.recordAnswer,
    recordReport: appState.recordReport,
  }),
}))

afterEach(cleanup)
beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, "hasPointerCapture", {
    value: () => false,
    configurable: true,
  })
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
    value: () => undefined,
    configurable: true,
  })
})
beforeEach(() => {
  appState.recordAnswer.mockReset()
  appState.recordAnswer.mockResolvedValue({ timesIncorrect: 0 })
  appState.recordReport.mockReset()
})

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

const twoChoiceQuestion: Question = {
  ...studyQuestion,
  id: "two-choice-question",
  question: "Elige una de dos respuestas.",
  options: [
    { id: "A", text: "Primera" },
    { id: "B", text: "Segunda" },
  ],
  correctAnswer: ["A"],
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

  it("usa una sola parada de tab y flechas que seleccionan la opción única", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <QuestionRenderer
        question={twoChoiceQuestion}
        value="A"
        onChange={onChange}
      />
    )

    const radios = screen.getAllByRole("radio")
    expect(radios[0]).toHaveAttribute("tabindex", "0")
    expect(radios[1]).toHaveAttribute("tabindex", "-1")
    radios[0].focus()
    await user.keyboard("{ArrowRight}")

    expect(onChange).toHaveBeenLastCalledWith("B")
  })

  it("presenta feedback textual para la selección correcta e incorrecta", () => {
    const { rerender } = render(
      <QuestionRenderer
        question={twoChoiceQuestion}
        value="B"
        onChange={vi.fn()}
        feedback={{ isCorrect: false, wasAnswered: true, reason: "incorrect" }}
      />
    )

    expect(screen.getByRole("status")).toHaveTextContent(
      "Tu selección fue incorrecta."
    )
    expect(screen.getByText("Respuesta correcta")).toBeVisible()

    rerender(
      <QuestionRenderer
        question={twoChoiceQuestion}
        value="A"
        onChange={vi.fn()}
        feedback={{ isCorrect: true, wasAnswered: true, reason: "correct" }}
      />
    )
    expect(screen.getByRole("status")).toHaveTextContent(
      "Tu selección es correcta."
    )
  })
})

describe("interacciones de QuestionRenderer", () => {
  it("actualiza y deshabilita respuestas de texto y selección múltiple", async () => {
    const user = userEvent.setup()
    const onText = vi.fn()
    const textQuestion: Question = {
      ...studyQuestion,
      id: "text-question",
      answerMode: "canonical_text",
      correctAnswerText: "Daniel",
    }
    const { rerender } = render(
      <QuestionRenderer question={textQuestion} value="" onChange={onText} />
    )
    await user.type(
      screen.getByRole("textbox", { name: "Escribe la respuesta" }),
      "D"
    )
    expect(onText).toHaveBeenLastCalledWith("D")
    rerender(
      <QuestionRenderer
        question={textQuestion}
        value="D"
        onChange={onText}
        disabled
      />
    )
    expect(
      screen.getByRole("textbox", { name: "Escribe la respuesta" })
    ).toBeDisabled()

    const multiQuestion: Question = {
      ...twoChoiceQuestion,
      id: "multi-question",
      type: "multi_select",
      correctAnswer: ["A", "B"],
    }
    const onMulti = vi.fn()
    rerender(
      <QuestionRenderer
        question={multiQuestion}
        value={[]}
        onChange={onMulti}
      />
    )
    await user.click(screen.getByRole("checkbox", { name: /Primera/ }))
    expect(onMulti).toHaveBeenLastCalledWith(["A"])

    rerender(
      <QuestionRenderer
        question={multiQuestion}
        value={[]}
        onChange={onMulti}
        disabled
      />
    )
    expect(screen.getByRole("checkbox", { name: /Primera/ })).toBeDisabled()
  })

  it("permite ordenar por teclado y relacionar elementos", async () => {
    const user = userEvent.setup()
    const orderingQuestion: Question = {
      ...twoChoiceQuestion,
      id: "ordering-question",
      type: "ordering",
      correctAnswer: ["B", "A"],
    }
    const onOrder = vi.fn()
    const { rerender } = render(
      <QuestionRenderer
        question={orderingQuestion}
        value={["A", "B"]}
        onChange={onOrder}
      />
    )
    const down = screen.getByRole("button", { name: "Mover Primera abajo" })
    down.focus()
    await user.keyboard("{Enter}")
    expect(onOrder).toHaveBeenLastCalledWith(["B", "A"])
    rerender(
      <QuestionRenderer
        question={orderingQuestion}
        value={["A", "B"]}
        onChange={onOrder}
        disabled
      />
    )
    expect(
      screen.getByRole("button", { name: "Mover Primera abajo" })
    ).toBeDisabled()

    const matchingQuestion: Question = {
      ...studyQuestion,
      id: "matching-question",
      type: "matching",
      options: [],
      correctAnswer: [],
      leftItems: [{ id: "left", text: "Uno" }],
      rightItems: [{ id: "right", text: "Uno relacionado" }],
      correctMatches: [{ left: "left", right: "right" }],
    }
    const onMatch = vi.fn()
    rerender(
      <QuestionRenderer
        question={matchingQuestion}
        value={{}}
        onChange={onMatch}
      />
    )
    await user.click(screen.getByRole("combobox", { name: "Relacionar Uno" }))
    await user.click(screen.getByRole("option", { name: "Uno relacionado" }))
    expect(onMatch).toHaveBeenLastCalledWith({ left: "right" })

    rerender(
      <QuestionRenderer
        question={matchingQuestion}
        value={{}}
        onChange={onMatch}
        disabled
      />
    )
    expect(
      screen.getByRole("combobox", { name: "Relacionar Uno" })
    ).toBeDisabled()
  })
})

describe("atajos de la ronda", () => {
  it("no confirma al presionar Enter en una opción, botón auxiliar o select", async () => {
    const user = userEvent.setup()
    const matchingQuestion: Question = {
      ...studyQuestion,
      id: "quiz-matching",
      type: "matching",
      options: [],
      correctAnswer: [],
      leftItems: [{ id: "left", text: "Uno" }],
      rightItems: [{ id: "right", text: "Uno relacionado" }],
      correctMatches: [{ left: "left", right: "right" }],
    }
    const { unmount } = render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={vi.fn()}
        onExit={vi.fn()}
      />
    )
    const radio = screen.getByRole("radio", { name: /Primera/ })
    radio.focus()
    await user.keyboard("{Enter}")
    expect(appState.recordAnswer).not.toHaveBeenCalled()

    screen.getByRole("button", { name: "Favorita" }).focus()
    await user.keyboard("{Enter}")
    expect(appState.recordAnswer).not.toHaveBeenCalled()

    unmount()
    render(
      <QuizPage
        questions={[matchingQuestion]}
        config={studyConfig}
        onFinish={vi.fn()}
        onExit={vi.fn()}
      />
    )
    screen.getByRole("combobox", { name: "Relacionar Uno" }).focus()
    await user.keyboard("{Enter}")
    expect(appState.recordAnswer).not.toHaveBeenCalled()
  })

  it("confirma una vez con Enter fuera de controles y enfoca el nuevo enunciado al avanzar", async () => {
    const user = userEvent.setup()
    render(
      <QuizPage
        questions={[
          twoChoiceQuestion,
          {
            ...twoChoiceQuestion,
            id: "second-question",
            question: "Segunda pregunta",
          },
        ]}
        config={studyConfig}
        onFinish={vi.fn()}
        onExit={vi.fn()}
      />
    )
    await user.click(screen.getByRole("radio", { name: /Primera/ }))
    const heading = screen.getByRole("heading", {
      name: twoChoiceQuestion.question,
    })
    heading.focus()
    await user.keyboard("{Enter}{Enter}")
    expect(appState.recordAnswer).toHaveBeenCalledTimes(1)
    expect(appState.recordAnswer).toHaveBeenLastCalledWith(
      twoChoiceQuestion,
      expect.objectContaining({ isCorrect: true }),
      "A",
      expect.any(Object)
    )

    await user.click(screen.getByRole("button", { name: "Siguiente" }))
    expect(
      screen.getByRole("heading", { name: "Segunda pregunta" })
    ).toHaveFocus()
    expect(screen.getByText("Pregunta 2 de 2")).toBeVisible()
  })

  it("finaliza la última pregunta con la respuesta registrada", async () => {
    const user = userEvent.setup()
    const onFinish = vi.fn()
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={onFinish}
        onExit={vi.fn()}
      />
    )

    await user.click(screen.getByRole("radio", { name: /Primera/ }))
    await user.click(
      screen.getByRole("button", { name: "Confirmar respuesta" })
    )
    await user.click(screen.getByRole("button", { name: "Ver resultados" }))

    expect(onFinish).toHaveBeenCalledWith(
      expect.objectContaining({
        answers: [expect.objectContaining({ answer: "A" })],
      })
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

const sessionWithMixedAnswers: Session = {
  ...sessionWithErrors,
  id: "results-mixed",
  questionKeys: ["local:study-question", "local:two-choice-question"],
  answers: [
    ...sessionWithErrors.answers,
    {
      questionKey: "local:two-choice-question",
      answer: "A",
      responseTimeMs: 800,
      result: { isCorrect: true, wasAnswered: true, reason: "correct" },
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
        session={sessionWithMixedAnswers}
        questions={[studyQuestion, twoChoiceQuestion]}
        onErrors={vi.fn()}
        onRepeat={vi.fn()}
        onNext={vi.fn()}
        onRandom={vi.fn()}
        onNew={vi.fn()}
      />
    )

    await user.click(screen.getByRole("switch", { name: "Solo incorrectas" }))

    expect(screen.getByText("Respuestas incorrectas")).toBeVisible()
    expect(screen.getByText(studyQuestion.question)).toBeVisible()
    expect(
      screen.queryByText(twoChoiceQuestion.question)
    ).not.toBeInTheDocument()
  })

  it("deshabilita el filtro de incorrectas cuando la ronda fue perfecta", () => {
    render(
      <ResultsPage
        session={{
          ...sessionWithMixedAnswers,
          answers: [sessionWithMixedAnswers.answers[1]],
        }}
        questions={[twoChoiceQuestion]}
        onErrors={vi.fn()}
        onRepeat={vi.fn()}
        onNext={vi.fn()}
        onRandom={vi.fn()}
        onNew={vi.fn()}
      />
    )

    expect(
      screen.getByRole("switch", { name: "Solo incorrectas" })
    ).toBeDisabled()
    expect(
      screen.getByText("No hay respuestas incorrectas para filtrar.")
    ).toBeVisible()
  })

  it("mantiene la siguiente tanda como acción secundaria cuando hay errores", () => {
    render(
      <ResultsPage
        session={{
          ...sessionWithErrors,
          selectionSummary: {
            strategy: "coverage-cycle",
            seen: 1,
            total: 3,
            remaining: 2,
          },
        }}
        questions={[studyQuestion]}
        onErrors={vi.fn()}
        onRepeat={vi.fn()}
        onNext={vi.fn()}
        onRandom={vi.fn()}
        onNew={vi.fn()}
      />
    )

    expect(
      screen.getByRole("button", { name: /Siguiente tanda sin repetir/ })
    ).toHaveAttribute("data-variant", "outline")
  })
})
