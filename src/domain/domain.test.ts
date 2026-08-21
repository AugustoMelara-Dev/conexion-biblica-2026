import { describe, expect, it } from "vitest"
import {
  evaluateAnswer,
  getMedian,
  isCorrectAnswer,
} from "@/domain/evaluation"
import { applyProgress, isMastered } from "@/domain/mastery"
import { scheduleTrainingRetry, selectSessionQuestions } from "@/domain/session-selector"
import { validateBank } from "@/domain/validation"
import type { Question } from "@/domain/types"

const source = {
  work: "Daniel",
  version: "RVR95",
  chapter: 3,
  reference: "Daniel 3:1",
} as const

function choiceQuestion(overrides: Partial<Question> = {}): Question {
  return {
    id: "D03-0001",
    type: "single_choice",
    difficulty: 3,
    source,
    tags: ["detalle"],
    factKey: "fact-1",
    question: "¿Pregunta?",
    options: [
      { id: "A", text: "Uno" },
      { id: "B", text: "Dos" },
      { id: "C", text: "Tres" },
    ],
    correctAnswer: ["B"],
    explanation: "Porque sí.",
    ...overrides,
  }
}

describe("evaluación de respuestas", () => {
  it("evalúa elección, verdadero/falso, fill_blank y tipos de opción", () => {
    expect(isCorrectAnswer(choiceQuestion(), "B")).toBe(true)
    expect(isCorrectAnswer(choiceQuestion(), "A")).toBe(false)
    expect(
      isCorrectAnswer(
        choiceQuestion({ type: "true_false", correctAnswer: ["A"] }),
        "A",
      ),
    ).toBe(true)
    expect(
      isCorrectAnswer(
        choiceQuestion({ type: "fill_blank", correctAnswer: ["C"] }),
        "C",
      ),
    ).toBe(true)
    expect(
      isCorrectAnswer(
        choiceQuestion({ type: "negative_choice", correctAnswer: ["C"] }),
        "C",
      ),
    ).toBe(true)
  })

  it("compara multi_select sin depender del orden", () => {
    const question = choiceQuestion({
      type: "multi_select",
      correctAnswer: ["A", "C"],
    })
    expect(isCorrectAnswer(question, ["C", "A"])).toBe(true)
    expect(isCorrectAnswer(question, ["A"])).toBe(false)
  })

  it("compara ordering y matching exactamente", () => {
    const ordering = choiceQuestion({
      type: "ordering",
      correctAnswer: ["C", "A", "B"],
    })
    expect(isCorrectAnswer(ordering, ["C", "A", "B"])).toBe(true)
    expect(isCorrectAnswer(ordering, ["A", "C", "B"])).toBe(false)

    const matching = choiceQuestion({
      type: "matching",
      options: [],
      correctAnswer: [],
      leftItems: [
        { id: "L1", text: "Uno" },
        { id: "L2", text: "Dos" },
      ],
      rightItems: [
        { id: "R1", text: "A" },
        { id: "R2", text: "B" },
      ],
      correctMatches: [
        { left: "L1", right: "R2" },
        { left: "L2", right: "R1" },
      ],
    })
    expect(isCorrectAnswer(matching, { L1: "R2", L2: "R1" })).toBe(true)
    expect(isCorrectAnswer(matching, { L1: "R1", L2: "R2" })).toBe(false)
  })

  it("marca una respuesta vencida como incorrecta y conserva el motivo", () => {
    const result = evaluateAnswer(choiceQuestion(), undefined, "timeout", 5_000)
    expect(result).toMatchObject({ isCorrect: false, wasAnswered: false, reason: "timeout" })
  })
})

describe("validación JSON schemaVersion 1.0", () => {
  it("rechaza IDs duplicados, tipos no soportados y respuestas inexistentes", () => {
    const valid = {
      schemaVersion: "1.0",
      bank: { competition: "Conexion Biblica 2026", sourceWork: "Daniel", sourceVersion: "RVR95", chapter: "3" },
      questions: [
        {
          ...choiceQuestion(),
          id: "D03-0001",
        },
        {
          ...choiceQuestion({ id: "D03-0001", type: "unknown_type" as Question["type"] }),
        },
      ],
    }
    const result = validateBank(valid, "duplicado.json")
    expect(result.valid).toBe(false)
    expect(result.errors.map((error) => error.code)).toEqual(
      expect.arrayContaining(["DUPLICATE_ID", "UNSUPPORTED_TYPE"]),
    )

    const invalidAnswer = validateBank(
      {
        ...valid,
        questions: [choiceQuestion({ correctAnswer: ["Z"] })],
      },
      "respuesta.json",
    )
    expect(invalidAnswer.errors).toEqual(
      expect.arrayContaining([expect.objectContaining({ code: "INVALID_CORRECT_ANSWER" })]),
    )
  })

  it("valida matching con correctMatches y no muta el banco recibido", () => {
    const question = choiceQuestion({
      type: "matching",
      options: [],
      correctAnswer: [],
      leftItems: [{ id: "L1", text: "A" }],
      rightItems: [{ id: "R1", text: "B" }],
      correctMatches: [{ left: "L1", right: "R1" }],
    })
    const input = { schemaVersion: "1.0", bank: { sourceWork: "Daniel", sourceVersion: "RVR95" }, questions: [question] }
    const before = JSON.stringify(input)
    expect(validateBank(input, "matching.json").valid).toBe(true)
    expect(JSON.stringify(input)).toBe(before)
  })
})

describe("dominio y estadísticas de tiempo", () => {
  it("sube dominio, registra historial y reconoce dominada solo con las reglas completas", () => {
    let progress = undefined
    for (let index = 0; index < 3; index += 1) {
      progress = applyProgress(progress, { isCorrect: true, wasAnswered: true, responseTimeMs: 4_000, reason: "correct" }, index + 1)
    }
    expect(progress?.masteryScore).toBe(3)
    expect(isMastered(progress)).toBe(false)

    progress = applyProgress(progress, { isCorrect: true, wasAnswered: true, responseTimeMs: 3_000, reason: "correct" }, 4)
    expect(progress?.masteryScore).toBe(4)
    expect(isMastered(progress)).toBe(true)

    progress = applyProgress(progress, { isCorrect: false, wasAnswered: true, responseTimeMs: 12_000, reason: "incorrect" }, 5)
    expect(progress?.masteryScore).toBe(3)
    expect(isMastered(progress)).toBe(false)
    expect(progress?.timesIncorrect).toBe(1)
    expect(progress?.history).toHaveLength(5)
  })

  it("calcula mediana par e impar", () => {
    expect(getMedian([1, 9, 4])).toBe(4)
    expect(getMedian([1, 9, 4, 8])).toBe(6)
    expect(getMedian([])).toBe(0)
  })
})

describe("selección equilibrada", () => {
  it("no duplica preguntas, evita factKey consecutivo y redistribuye cuotas", () => {
    const questions = Array.from({ length: 20 }, (_, index) =>
      choiceQuestion({
        id: `D03-${String(index + 1).padStart(4, "0")}`,
        difficulty: ((index % 5) + 1) as Question["difficulty"],
        factKey: `fact-${Math.floor(index / 2)}`,
        source: { ...source, chapter: index % 2 === 0 ? 3 : 7 },
      }),
    )
    const selected = selectSessionQuestions(
      questions,
      new Map(),
      {
        mode: "championship",
        count: 12,
        sourceWorks: ["Daniel"],
        chapters: [3, 7],
        difficulties: [1, 2, 3, 4, 5],
        types: ["single_choice"],
        statuses: ["all"],
        shuffleQuestions: true,
        shuffleOptions: true,
        perQuestionSeconds: 10,
        totalSeconds: null,
      },
      42,
    )
    expect(selected).toHaveLength(12)
    expect(new Set(selected.map((question) => question.id)).size).toBe(12)
    for (let index = 1; index < selected.length; index += 1) {
      expect(selected[index].factKey).not.toBe(selected[index - 1].factKey)
    }
  })

  it("programa un reintento de entrenamiento lejos de la pregunta fallada", () => {
    const questions = Array.from({ length: 12 }, (_, index) => choiceQuestion({ id: `D03-${String(index + 1).padStart(4, "0")}` }))
    const failed = questions[0]
    const retryQueue = scheduleTrainingRetry(questions, failed, 0, 8)
    expect(retryQueue).toHaveLength(13)
    expect(retryQueue[1]).not.toBe(failed)
    expect(retryQueue[9]).toBe(failed)
    expect(scheduleTrainingRetry(retryQueue, failed, 0, 8)).toBe(retryQueue)
  })

  it("respeta las cuotas de dificultad del campeonato cuando hay disponibilidad", () => {
    const questions = Array.from({ length: 40 }, (_, index) => choiceQuestion({
      id: `D03-${String(index + 1).padStart(4, "0")}`,
      difficulty: ((index % 5) + 1) as Question["difficulty"],
      factKey: `championship-${index}`,
      source: { ...source, chapter: (index % 5) + 1 },
    }))
    const selected = selectSessionQuestions(questions, new Map(), {
      mode: "championship",
      count: 20,
      sourceWorks: ["Daniel"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: 10,
      totalSeconds: null,
    }, 7)
    expect(selected.filter((question) => question.difficulty === 5)).toHaveLength(8)
    expect(selected.filter((question) => question.difficulty === 4)).toHaveLength(7)
    expect(selected.filter((question) => question.difficulty === 3)).toHaveLength(4)
    expect(selected.filter((question) => question.difficulty <= 2)).toHaveLength(1)
  })
})
