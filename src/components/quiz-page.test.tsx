import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react"
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
import { createRepositories, deleteAppDb, openAppDb } from "@/storage/db"

const appState = vi.hoisted(() => ({
  recordAnswer: vi.fn(),
  recordReport: vi.fn(),
}))

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

vi.mock("@/app/app-state", () => ({
  useApp: () => ({
    progress: new Map(),
    recordAnswer: appState.recordAnswer,
    recordReport: appState.recordReport,
  }),
}))

afterEach(cleanup)
afterEach(() => vi.useRealTimers())
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
  appState.recordReport.mockResolvedValue(undefined)
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
  bankSelection: "mixed",
  strategy: "random-balanced",
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
        feedback={{
          isCorrect: false,
          wasAnswered: true,
          responseTimeMs: 10,
          reason: "incorrect",
        }}
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
        feedback={{
          isCorrect: true,
          wasAnswered: true,
          responseTimeMs: 10,
          reason: "correct",
        }}
      />
    )
    expect(screen.getByRole("status")).toHaveTextContent(
      "Tu selección es correcta."
    )
  })

  it("expone las opciones correctas e incorrectas de selección múltiple solo tras evaluar", () => {
    const multiQuestion: Question = {
      ...twoChoiceQuestion,
      id: "feedback-multi",
      type: "multi_select",
      correctAnswer: ["A"],
    }
    const { rerender } = render(
      <QuestionRenderer
        question={multiQuestion}
        value={["B"]}
        onChange={vi.fn()}
      />
    )

    expect(screen.queryByText("Respuesta correcta")).not.toBeInTheDocument()
    expect(
      screen.queryByText("Tu selección fue incorrecta.")
    ).not.toBeInTheDocument()

    rerender(
      <QuestionRenderer
        question={multiQuestion}
        value={["B"]}
        onChange={vi.fn()}
        feedback={{
          isCorrect: false,
          wasAnswered: true,
          responseTimeMs: 10,
          reason: "incorrect",
        }}
      />
    )

    expect(screen.getByText("Respuesta correcta")).toBeInTheDocument()
    expect(screen.queryByRole("status")).not.toBeInTheDocument()
    expect(
      screen.getByRole("checkbox", {
        name: /Segunda.*Tu selección fue incorrecta/i,
      })
    ).toBeVisible()
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
  it("cierra Referencia con Escape antes de salir de la ronda", async () => {
    const user = userEvent.setup()
    const onExit = vi.fn().mockResolvedValue(undefined)
    render(
      <FocusShell>
        <QuizPage
          questions={[twoChoiceQuestion]}
          config={studyConfig}
          onFinish={vi.fn().mockResolvedValue(undefined)}
          onExit={onExit}
        />
      </FocusShell>
    )

    await user.click(screen.getByRole("button", { name: "Referencia" }))
    expect(
      screen.getByRole("dialog", { name: "Volver al texto / referencia" })
    ).toBeVisible()
    await user.keyboard("{Escape}")

    expect(
      screen.queryByRole("dialog", { name: "Volver al texto / referencia" })
    ).not.toBeInTheDocument()
    expect(onExit).not.toHaveBeenCalled()

    await user.keyboard("{Escape}")
    expect(onExit).toHaveBeenCalledTimes(1)
  })

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

  it("finaliza una sola vez aunque se pulse dos veces Ver resultados", async () => {
    const onFinish = vi.fn()
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={onFinish}
        onExit={vi.fn()}
      />
    )

    fireEvent.click(screen.getByRole("radio", { name: /Primera/ }))
    fireEvent.click(screen.getByRole("button", { name: "Confirmar respuesta" }))
    await act(async () => undefined)
    const results = screen.getByRole("button", { name: "Ver resultados" })
    fireEvent.click(results)
    fireEvent.click(results)

    await waitFor(() => expect(onFinish).toHaveBeenCalledTimes(1))
  })

  it("cancela el avance diferido de un timeout cuando se avanza manualmente", async () => {
    vi.useFakeTimers()
    const timedConfig = { ...studyConfig, perQuestionSeconds: 1 }
    render(
      <QuizPage
        questions={[
          twoChoiceQuestion,
          {
            ...twoChoiceQuestion,
            id: "timer-second",
            question: "Pregunta del temporizador",
          },
        ]}
        config={timedConfig}
        onFinish={vi.fn()}
        onExit={vi.fn()}
      />
    )

    await act(async () => {
      vi.advanceTimersByTime(1_100)
      await Promise.resolve()
    })
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }))
    expect(
      screen.getByRole("heading", { name: "Pregunta del temporizador" })
    ).toBeVisible()

    await act(async () => vi.advanceTimersByTime(1_000))
    expect(
      screen.getByRole("heading", { name: "Pregunta del temporizador" })
    ).toBeVisible()
  })

  it("cancela la finalización diferida al desmontarse", async () => {
    vi.useFakeTimers()
    const onFinish = vi.fn()
    const { unmount } = render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={{ ...studyConfig, perQuestionSeconds: 1 }}
        onFinish={onFinish}
        onExit={vi.fn()}
      />
    )

    await act(async () => {
      vi.advanceTimersByTime(1_100)
      await Promise.resolve()
    })
    unmount()
    await act(async () => vi.advanceTimersByTime(1_000))

    expect(onFinish).not.toHaveBeenCalled()
  })

  it("no programa el timeout antiguo al avanzar mientras recordAnswer sigue pendiente", async () => {
    vi.useFakeTimers()
    const pending = deferred<{ timesIncorrect: number }>()
    appState.recordAnswer.mockReturnValueOnce(pending.promise)
    const onFinish = vi.fn()
    const secondQuestion = {
      ...twoChoiceQuestion,
      id: "deferred-second",
      question: "Segunda pregunta diferida",
    }
    render(
      <QuizPage
        questions={[
          twoChoiceQuestion,
          secondQuestion,
          {
            ...secondQuestion,
            id: "deferred-third",
            question: "Tercera pregunta diferida",
          },
        ]}
        config={{ ...studyConfig, mode: "simulation", perQuestionSeconds: 1 }}
        onFinish={onFinish}
        onExit={vi.fn()}
      />
    )

    await act(async () => vi.advanceTimersByTime(1_100))
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }))
    expect(
      screen.getByRole("heading", { name: "Segunda pregunta diferida" })
    ).toBeVisible()

    await act(async () => pending.resolve({ timesIncorrect: 0 }))
    await act(async () => vi.advanceTimersByTime(1_000))

    expect(
      screen.getByRole("heading", { name: "Segunda pregunta diferida" })
    ).toBeVisible()
    expect(onFinish).not.toHaveBeenCalled()
  })

  it("ignora una persistencia pendiente al desmontar la ronda", async () => {
    vi.useFakeTimers()
    const pending = deferred<{ timesIncorrect: number }>()
    appState.recordAnswer.mockReturnValueOnce(pending.promise)
    const onFinish = vi.fn()
    const { unmount } = render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={{ ...studyConfig, mode: "simulation", perQuestionSeconds: 1 }}
        onFinish={onFinish}
        onExit={vi.fn()}
      />
    )

    await act(async () => vi.advanceTimersByTime(1_100))
    unmount()
    await act(async () => pending.resolve({ timesIncorrect: 0 }))
    await act(async () => vi.advanceTimersByTime(1_000))

    expect(onFinish).not.toHaveBeenCalled()
  })

  it("invalida una persistencia pendiente antes de salir con Escape", async () => {
    vi.useFakeTimers()
    const pending = deferred<{ timesIncorrect: number }>()
    appState.recordAnswer.mockReturnValueOnce(pending.promise)
    const onFinish = vi.fn()
    const onExit = vi.fn()
    render(
      <FocusShell onExit={onExit}>
        <QuizPage
          questions={[twoChoiceQuestion]}
          config={{ ...studyConfig, mode: "simulation", perQuestionSeconds: 1 }}
          onFinish={onFinish}
          onExit={onExit}
        />
      </FocusShell>
    )

    await act(async () => vi.advanceTimersByTime(1_100))
    fireEvent.keyDown(window, { key: "Escape" })
    await act(async () => Promise.resolve())
    expect(onExit).toHaveBeenCalledTimes(1)

    await act(async () => pending.resolve({ timesIncorrect: 0 }))
    await act(async () => vi.advanceTimersByTime(1_000))

    expect(onExit).toHaveBeenCalledTimes(1)
    expect(onFinish).not.toHaveBeenCalled()
  })
})

describe("persistencia acotada de reportes", () => {
  it("bloquea el doble envío y anuncia el reporte pendiente", async () => {
    const pending = deferred<void>()
    appState.recordReport.mockReturnValueOnce(pending.promise)
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={vi.fn().mockResolvedValue(undefined)}
        onExit={vi.fn().mockResolvedValue(undefined)}
      />
    )
    fireEvent.click(screen.getByRole("button", { name: "Reportar" }))
    const save = screen.getByRole("button", { name: "Guardar reporte" })

    fireEvent.click(save)
    fireEvent.click(save)

    expect(appState.recordReport).toHaveBeenCalledTimes(1)
    expect(save).toBeDisabled()
    expect(save).toHaveClass("min-h-11")
    expect(screen.getByRole("status")).toHaveTextContent("Guardando reporte")

    await act(async () => pending.resolve())
    expect(
      screen.queryByRole("button", { name: "Guardar reporte" })
    ).not.toBeInTheDocument()
  })

  it("no deja que un reporte pendiente cierre el formulario de otra pregunta", async () => {
    const pending = deferred<void>()
    appState.recordReport
      .mockReturnValueOnce(pending.promise)
      .mockResolvedValueOnce(undefined)
    render(
      <QuizPage
        questions={[
          twoChoiceQuestion,
          {
            ...twoChoiceQuestion,
            id: "report-second",
            question: "Segunda pregunta para reporte",
          },
        ]}
        config={studyConfig}
        onFinish={vi.fn().mockResolvedValue(undefined)}
        onExit={vi.fn().mockResolvedValue(undefined)}
      />
    )

    fireEvent.click(screen.getByRole("button", { name: "Reportar" }))
    fireEvent.change(screen.getByLabelText("Motivo del reporte"), {
      target: { value: "Primera pregunta" },
    })
    fireEvent.click(screen.getByRole("button", { name: "Guardar reporte" }))
    fireEvent.click(screen.getByRole("radio", { name: /Primera/ }))
    fireEvent.click(screen.getByRole("button", { name: "Confirmar respuesta" }))
    await act(async () => undefined)
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }))
    expect(
      screen.getByRole("heading", { name: "Segunda pregunta para reporte" })
    ).toBeVisible()
    expect(
      screen.queryByRole("button", { name: "Guardar reporte" })
    ).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Reportar" }))
    expect(
      screen.getByRole("button", { name: "Guardar reporte" })
    ).toBeVisible()

    await act(async () => pending.resolve())

    expect(
      screen.getByRole("button", { name: "Guardar reporte" })
    ).toBeVisible()
    expect(appState.recordReport).toHaveBeenNthCalledWith(
      1,
      twoChoiceQuestion,
      undefined,
      null,
      "Primera pregunta"
    )
  })

  it("muestra el rechazo y permite reintentar el mismo reporte", async () => {
    const user = userEvent.setup()
    appState.recordReport
      .mockRejectedValueOnce(new Error("storage denied"))
      .mockResolvedValueOnce(undefined)
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={vi.fn().mockResolvedValue(undefined)}
        onExit={vi.fn().mockResolvedValue(undefined)}
      />
    )

    await user.click(screen.getByRole("button", { name: "Reportar" }))
    await user.click(screen.getByRole("button", { name: "Guardar reporte" }))

    expect(screen.getByRole("alert")).toHaveTextContent(
      "No se pudo guardar el reporte"
    )
    const retry = screen.getByRole("button", { name: "Guardar reporte" })
    expect(retry).toBeEnabled()
    await user.click(retry)

    expect(appState.recordReport).toHaveBeenCalledTimes(2)
    expect(
      screen.queryByRole("button", { name: "Guardar reporte" })
    ).not.toBeInTheDocument()
  })
})

describe("recuperación de transiciones persistidas", () => {
  it("restablece finish después de un rechazo y permite reintentar", async () => {
    const user = userEvent.setup()
    const onFinish = vi
      .fn()
      .mockRejectedValueOnce(new Error("session denied"))
      .mockResolvedValueOnce(undefined)
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={onFinish}
        onExit={vi.fn().mockResolvedValue(undefined)}
      />
    )
    await user.click(screen.getByRole("radio", { name: /Primera/ }))
    await user.click(
      screen.getByRole("button", { name: "Confirmar respuesta" })
    )
    await user.click(screen.getByRole("button", { name: "Ver resultados" }))

    expect(
      screen
        .getByText(/No se pudieron guardar los resultados/)
        .closest('[role="alert"]')
    ).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Ver resultados" }))
    expect(onFinish).toHaveBeenCalledTimes(2)
  })

  it("restablece exit después de un rechazo y evita dobles mientras está pendiente", async () => {
    const user = userEvent.setup()
    const pending = deferred<void>()
    const onExit = vi
      .fn()
      .mockRejectedValueOnce(new Error("clear denied"))
      .mockReturnValueOnce(pending.promise)
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={vi.fn().mockResolvedValue(undefined)}
        onExit={onExit}
      />
    )

    await user.click(screen.getByRole("button", { name: "Salir" }))
    expect(screen.getByRole("alert")).toHaveTextContent(
      "No se pudo salir de la ronda"
    )
    const retry = screen.getByRole("button", { name: "Salir" })
    await user.click(retry)
    fireEvent.click(retry)
    expect(onExit).toHaveBeenCalledTimes(2)
    expect(retry).toBeDisabled()
    await act(async () => pending.resolve())
  })

  it("comunica un autosave fallido y permite reintentar sin bloquear la ronda", async () => {
    const user = userEvent.setup()
    const onStateChange = vi
      .fn()
      .mockRejectedValueOnce(new Error("autosave denied"))
      .mockResolvedValueOnce(undefined)
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onStateChange={onStateChange}
        onFinish={vi.fn().mockResolvedValue(undefined)}
        onExit={vi.fn().mockResolvedValue(undefined)}
      />
    )

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No se pudo guardar el avance"
    )
    expect(screen.getByRole("button", { name: "Salir" })).toBeEnabled()
    await user.click(
      screen.getByRole("button", { name: "Reintentar guardado" })
    )

    expect(onStateChange).toHaveBeenCalledTimes(2)
    expect(
      screen.queryByRole("button", { name: "Reintentar guardado" })
    ).not.toBeInTheDocument()
  })

  it("drena el autosave iniciado, descarta el snapshot en cola y luego sale sin resucitar la ronda", async () => {
    await deleteAppDb()
    const repositories = createRepositories(await openAppDb())
    const firstWrite = deferred<void>()
    const firstCommitted = deferred<void>()
    let first = true
    const onStateChange = vi.fn(async (round) => {
      if (first) {
        first = false
        await firstWrite.promise
      }
      await repositories.activeRound.put(round)
      if (round.answers.length === 0) firstCommitted.resolve()
    })
    const onExit = vi.fn(async () => repositories.activeRound.clear())
    const user = userEvent.setup()
    try {
      render(
        <QuizPage
          questions={[twoChoiceQuestion]}
          config={studyConfig}
          onStateChange={onStateChange}
          onFinish={vi.fn().mockResolvedValue(undefined)}
          onExit={onExit}
        />
      )
      await waitFor(() => expect(onStateChange).toHaveBeenCalledTimes(1))
      await user.click(screen.getByRole("radio", { name: /Primera/ }))
      await user.click(
        screen.getByRole("button", { name: "Confirmar respuesta" })
      )
      await user.click(screen.getByRole("button", { name: "Salir" }))

      expect(screen.getByRole("button", { name: "Salir" })).toBeDisabled()
      await act(async () => firstWrite.resolve())
      await firstCommitted.promise
      await waitFor(() => expect(onExit).toHaveBeenCalledTimes(1))

      expect(onStateChange).toHaveBeenCalledTimes(1)
      expect(await repositories.activeRound.get()).toBeUndefined()
    } finally {
      await deleteAppDb()
    }
  })

  it("reactiva el autosave tras un exit fallido y el reintento vuelve a drenar antes del clear", async () => {
    await deleteAppDb()
    const repositories = createRepositories(await openAppDb())
    const onStateChange = vi.fn(async (round) => {
      await repositories.activeRound.put(round)
    })
    const onExit = vi
      .fn()
      .mockRejectedValueOnce(new Error("clear denied"))
      .mockImplementationOnce(async () => repositories.activeRound.clear())
    const user = userEvent.setup()
    try {
      render(
        <QuizPage
          questions={[twoChoiceQuestion, studyQuestion]}
          config={studyConfig}
          onStateChange={onStateChange}
          onFinish={vi.fn().mockResolvedValue(undefined)}
          onExit={onExit}
        />
      )
      await waitFor(() => expect(onStateChange).toHaveBeenCalledTimes(1))

      await user.click(screen.getByRole("button", { name: "Salir" }))
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "No se pudo salir de la ronda"
      )

      await user.click(screen.getByRole("radio", { name: /Primera/ }))
      await user.click(
        screen.getByRole("button", { name: "Confirmar respuesta" })
      )
      await user.click(screen.getByRole("button", { name: "Siguiente" }))

      await waitFor(async () =>
        expect(await repositories.activeRound.get()).toMatchObject({
          currentIndex: 1,
          answers: [{ questionKey: "local:two-choice-question" }],
        })
      )

      await user.click(screen.getByRole("button", { name: "Salir" }))
      await waitFor(() => expect(onExit).toHaveBeenCalledTimes(2))
      expect(await repositories.activeRound.get()).toBeUndefined()
      expect(onStateChange.mock.calls.at(-1)?.[0]).toMatchObject({
        currentIndex: 1,
      })
    } finally {
      await deleteAppDb()
    }
  })

  it("bloquea Enter y timeout mientras exit drena y reanuda sin perder cambios", async () => {
    await deleteAppDb()
    const repositories = createRepositories(await openAppDb())
    const firstWrite = deferred<void>()
    let isFirstWrite = true
    const onStateChange = vi.fn(async (round) => {
      if (isFirstWrite) {
        isFirstWrite = false
        await firstWrite.promise
      }
      await repositories.activeRound.put(round)
    })
    const onExit = vi
      .fn()
      .mockRejectedValueOnce(new Error("clear denied"))
      .mockImplementationOnce(async () => repositories.activeRound.clear())
    let now = 1_000
    const clock = vi.spyOn(Date, "now").mockImplementation(() => now)
    try {
      render(
        <QuizPage
          questions={[twoChoiceQuestion]}
          config={{ ...studyConfig, perQuestionSeconds: 1 }}
          onStateChange={onStateChange}
          onFinish={vi.fn().mockResolvedValue(undefined)}
          onExit={onExit}
        />
      )
      await waitFor(() => expect(onStateChange).toHaveBeenCalledTimes(1))
      const radio = screen.getByRole("radio", { name: /Primera/ })
      fireEvent.click(radio)

      fireEvent.click(screen.getByRole("button", { name: "Salir" }))
      const confirmWasDisabled = screen
        .getByRole("button", {
          name: "Confirmar respuesta",
        })
        .hasAttribute("disabled")
      const answerWasDisabled = radio.hasAttribute("disabled")
      fireEvent.keyDown(window, { key: "Enter" })
      now = 3_000
      await act(
        async () => new Promise((resolve) => window.setTimeout(resolve, 150))
      )
      const answerCallsDuringDrain = appState.recordAnswer.mock.calls.length

      now = 1_000
      await act(async () => firstWrite.resolve())
      expect(
        await screen.findByText(/No se pudo salir de la ronda/)
      ).toBeVisible()

      fireEvent.keyDown(window, { key: "Enter" })
      await waitFor(() =>
        expect(appState.recordAnswer).toHaveBeenCalledTimes(1)
      )
      await waitFor(async () =>
        expect(await repositories.activeRound.get()).toMatchObject({
          answers: [{ questionKey: "local:two-choice-question" }],
        })
      )

      fireEvent.click(screen.getByRole("button", { name: "Salir" }))
      await waitFor(() => expect(onExit).toHaveBeenCalledTimes(2))
      const writesAfterClear = onStateChange.mock.calls.length
      await act(
        async () => new Promise((resolve) => window.setTimeout(resolve, 150))
      )

      expect(confirmWasDisabled).toBe(true)
      expect(answerWasDisabled).toBe(true)
      expect(answerCallsDuringDrain).toBe(0)
      expect(await repositories.activeRound.get()).toBeUndefined()
      expect(onStateChange).toHaveBeenCalledTimes(writesAfterClear)
    } finally {
      clock.mockRestore()
      await deleteAppDb()
    }
  })

  it("drena el autosave iniciado antes de terminar y no rehidrata después del clear", async () => {
    await deleteAppDb()
    const repositories = createRepositories(await openAppDb())
    const firstWrite = deferred<void>()
    const firstCommitted = deferred<void>()
    let first = true
    const onStateChange = vi.fn(async (round) => {
      if (first) {
        first = false
        await firstWrite.promise
      }
      await repositories.activeRound.put(round)
      if (round.answers.length === 0) firstCommitted.resolve()
    })
    const onFinish = vi.fn(async (session: Session) => {
      await repositories.sessions.add(session)
      await repositories.activeRound.clear()
    })
    const user = userEvent.setup()
    try {
      render(
        <QuizPage
          questions={[twoChoiceQuestion]}
          config={studyConfig}
          onStateChange={onStateChange}
          onFinish={onFinish}
          onExit={vi.fn().mockResolvedValue(undefined)}
        />
      )
      await waitFor(() => expect(onStateChange).toHaveBeenCalledTimes(1))
      await user.click(screen.getByRole("radio", { name: /Primera/ }))
      await user.click(
        screen.getByRole("button", { name: "Confirmar respuesta" })
      )
      await user.click(screen.getByRole("button", { name: "Ver resultados" }))

      expect(onFinish).not.toHaveBeenCalled()
      await act(async () => firstWrite.resolve())
      await firstCommitted.promise
      await waitFor(() => expect(onFinish).toHaveBeenCalledTimes(1))

      expect(onStateChange).toHaveBeenCalledTimes(1)
      expect(await repositories.activeRound.get()).toBeUndefined()
      expect(await repositories.sessions.list()).toHaveLength(1)
    } finally {
      await deleteAppDb()
    }
  })

  it("absorbe el rechazo del write drenado y todavía permite finish", async () => {
    const write = deferred<void>()
    const onStateChange = vi.fn(() => write.promise)
    const onFinish = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onStateChange={onStateChange}
        onFinish={onFinish}
        onExit={vi.fn().mockResolvedValue(undefined)}
      />
    )
    await waitFor(() => expect(onStateChange).toHaveBeenCalledTimes(1))
    await user.click(screen.getByRole("radio", { name: /Primera/ }))
    await user.click(
      screen.getByRole("button", { name: "Confirmar respuesta" })
    )
    await user.click(screen.getByRole("button", { name: "Ver resultados" }))

    expect(onFinish).not.toHaveBeenCalled()
    await act(async () => write.reject(new Error("write denied")))
    await waitFor(() => expect(onFinish).toHaveBeenCalledTimes(1))
  })

  it("ignora Escape mientras finish está pendiente", async () => {
    const finishPending = deferred<void>()
    const onFinish = vi.fn(() => finishPending.promise)
    const onExit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(
      <QuizPage
        questions={[twoChoiceQuestion]}
        config={studyConfig}
        onFinish={onFinish}
        onExit={onExit}
      />
    )
    await user.click(screen.getByRole("radio", { name: /Primera/ }))
    await user.click(
      screen.getByRole("button", { name: "Confirmar respuesta" })
    )
    await user.click(screen.getByRole("button", { name: "Ver resultados" }))
    await waitFor(() => expect(onFinish).toHaveBeenCalledTimes(1))

    await user.keyboard("{Escape}")

    expect(onExit).not.toHaveBeenCalled()
    await act(async () => finishPending.resolve())
  })
})

describe("metadatos de preguntas", () => {
  it.each([
    ["who_said_it", "Quién lo dijo"],
    ["to_whom", "A quién"],
    ["reference_detail", "Detalle de referencia"],
    ["sequence_choice", "Secuencia"],
    ["precision", "Precisión"],
  ] as const)("nombra el tipo %s", (type, label) => {
    render(
      <QuizPage
        questions={[{ ...studyQuestion, id: `metadata-${type}`, type }]}
        config={{ ...studyConfig, types: [type] }}
        onFinish={vi.fn()}
        onExit={vi.fn()}
      />
    )

    expect(screen.getByText(new RegExp(label))).toBeVisible()
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
      result: {
        isCorrect: false,
        wasAnswered: true,
        responseTimeMs: 1_000,
        reason: "incorrect",
      },
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
      result: {
        isCorrect: true,
        wasAnswered: true,
        responseTimeMs: 800,
        reason: "correct",
      },
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
    const answers = screen.getByRole("list", { name: "Respuestas de la ronda" })
    expect(answers).toHaveRole("list")
    expect(within(answers).getAllByRole("listitem")).toHaveLength(1)
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
