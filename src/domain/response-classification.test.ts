import { describe, expect, it } from "vitest"
import {
  classifyLatestProgressResponse,
  classifyResponse,
  reviewPriorityForProgress,
  reviewPriorityForClassification,
  type ResponseClassification,
} from "@/domain/response-classification"
import { createEmptyProgress } from "@/domain/mastery"

describe("clasificación de respuestas", () => {
  it.each<{
    name: string
    input: Parameters<typeof classifyResponse>[0]
    expected: ResponseClassification
  }>([
    {
      name: "correcta segura justo en 6000 ms",
      input: {
        wasAnswered: true,
        isCorrect: true,
        responseTimeMs: 6_000,
        wasDoubted: false,
      },
      expected: "correct_secure",
    },
    {
      name: "correcta lenta desde 6001 ms",
      input: {
        wasAnswered: true,
        isCorrect: true,
        responseTimeMs: 6_001,
        wasDoubted: false,
      },
      expected: "correct_slow",
    },
    {
      name: "correcta con duda aunque también sea lenta",
      input: {
        wasAnswered: true,
        isCorrect: true,
        responseTimeMs: 9_000,
        wasDoubted: true,
      },
      expected: "correct_doubted",
    },
    {
      name: "incorrecta",
      input: {
        wasAnswered: true,
        isCorrect: false,
        responseTimeMs: 2_000,
        wasDoubted: false,
      },
      expected: "incorrect",
    },
    {
      name: "sin responder aunque la corrección recibida sea contradictoria",
      input: {
        wasAnswered: false,
        isCorrect: true,
        responseTimeMs: 0,
        wasDoubted: true,
      },
      expected: "unanswered",
    },
  ])("clasifica una respuesta $name", ({ input, expected }) => {
    expect(classifyResponse(input)).toBe(expected)
  })
})

describe("prioridad de repaso", () => {
  it.each<[ResponseClassification, 0 | 1 | 2]>([
    ["incorrect", 2],
    ["unanswered", 2],
    ["correct_slow", 1],
    ["correct_doubted", 1],
    ["correct_secure", 0],
  ])("asigna a %s la prioridad %i", (classification, expected) => {
    expect(reviewPriorityForClassification(classification)).toBe(expected)
  })

  it("deriva la clasificación y prioridad desde el último intento persistido", () => {
    const progress = createEmptyProgress("final:q1")
    progress.history = [
      {
        timestamp: 1,
        isCorrect: false,
        wasAnswered: true,
        responseTimeMs: 2_000,
        reason: "incorrect",
      },
      {
        timestamp: 2,
        isCorrect: true,
        wasAnswered: true,
        responseTimeMs: 6_001,
        reason: "correct",
      },
    ]

    expect(classifyLatestProgressResponse(progress)).toBe("correct_slow")
    expect(reviewPriorityForProgress(progress)).toBe(1)
  })

  it("no inventa una clasificación para preguntas sin intentos", () => {
    expect(classifyLatestProgressResponse(undefined)).toBeNull()
    expect(reviewPriorityForProgress(createEmptyProgress("final:new"))).toBe(0)
  })
})
