import { describe, expect, it } from "vitest"
import { buildSimulationStatistics, buildStatistics } from "@/lib/statistics"
import type { Question, QuestionProgress, Session } from "@/domain/types"

const question = (id: string, chapter: number): Question => ({
  id,
  bankId: "bank",
  type: "single_choice",
  difficulty: 3,
  source: { work: "Daniel", version: "RVR95", chapter, reference: `Daniel ${chapter}:1` },
  tags: ["detalle"],
  factKey: id,
  question: "¿Pregunta?",
  options: [{ id: "A", text: "A" }, { id: "B", text: "B" }],
  correctAnswer: ["A"],
})

const progress = (questionKey: string, correct: number, incorrect: number, average: number): QuestionProgress => ({
  questionKey,
  timesSeen: correct + incorrect,
  timesCorrect: correct,
  timesIncorrect: incorrect,
  timesUnanswered: 0,
  currentCorrectStreak: correct,
  averageResponseTimeMs: average,
  bestResponseTimeMs: average,
  lastResponseTimeMs: average,
  lastSeenAt: 1,
  masteryScore: Math.min(5, correct),
  favorite: false,
  markedDifficult: incorrect > 0,
  reported: false,
  history: Array.from({ length: correct + incorrect }, (_, index) => ({ timestamp: index, isCorrect: index < correct, wasAnswered: true, responseTimeMs: average, reason: index < correct ? "correct" : "incorrect" })),
})

describe("estadísticas agregadas", () => {
  it("los errores de práctica no reducen el resultado de simulacro", () => {
    const answer = (isCorrect: boolean) => ({ questionKey: "bank:q1", answer: "A", result: { isCorrect, wasAnswered: true, responseTimeMs: 1000, reason: isCorrect ? "correct" as const : "incorrect" as const }, responseTimeMs: 1000 })
    const session = (id: string, context: "practice" | "simulation", answers: ReturnType<typeof answer>[]): Session => ({
      id, context, startedAt: 1, completedAt: 2, mode: context === "simulation" ? "simulation" : "learn",
      config: { mode: context === "simulation" ? "simulation" : "learn", count: 1, sourceWorks: ["Daniel"], chapters: [], difficulties: [], types: [], statuses: ["all"], shuffleQuestions: true, shuffleOptions: true, perQuestionSeconds: null, totalSeconds: null },
      questionKeys: ["bank:q1"], answers, score: answers.filter((item) => item.result.isCorrect).length, durationMs: 1000,
    })
    const result = buildSimulationStatistics([
      session("practice", "practice", [answer(false), answer(false), answer(false)]),
      session("simulation", "simulation", [answer(true)]),
    ])
    expect(result).toMatchObject({ sessions: 1, answers: 1, correct: 1, accuracy: 100 })
  })

  it("calcula métricas generales y ordena capítulos de peor a mejor", () => {
    const stats = buildStatistics(
      [question("q1", 1), question("q2", 2)],
      new Map([
        ["bank:q1", progress("bank:q1", 1, 1, 4_000)],
        ["bank:q2", progress("bank:q2", 2, 0, 2_000)],
      ]),
    )
    expect(stats.general.total).toBe(4)
    expect(stats.general.correct).toBe(3)
    expect(stats.general.accuracy).toBe(75)
    expect(stats.chapters[0]).toMatchObject({ chapter: 1, accuracy: 50 })
    expect(stats.general.medianResponseTimeMs).toBe(3_000)
  })

  it("no mezcla progreso de bancos fuera del scope solicitado", () => {
    const stats = buildStatistics(
      [question("q1", 1)],
      new Map([
        ["bank:q1", progress("bank:q1", 1, 0, 1_000)],
        ["master-v2:outside", progress("master-v2:outside", 0, 20, 9_000)],
      ]),
    )

    expect(stats.general.total).toBe(1)
    expect(stats.general.accuracy).toBe(100)
    expect(stats.general.unseen).toBe(0)
  })

  it("mantiene separado el progreso V4 aunque comparta el id de pregunta con V2", () => {
    const v2Question = { ...question("shared-id", 1), bankId: "master-v2", bankProfileId: "master-v2" as const }
    const v4Question = { ...question("shared-id", 1), bankId: "curated-v4", bankProfileId: "curated-v4" as const }
    const stats = buildStatistics(
      [v2Question, v4Question],
      new Map([
        ["master-v2:shared-id", progress("master-v2:shared-id", 1, 0, 1_000)],
        ["curated-v4:shared-id", progress("curated-v4:shared-id", 0, 1, 2_000)],
      ]),
    )

    expect(stats.general).toMatchObject({ total: 2, correct: 1, incorrect: 1, accuracy: 50 })
  })

  it("agrupa V2 por bandas nativas en vez de niveles numéricos derivados", () => {
    const medium = { ...question("v2-medium", 1), bankId: "master-v2", bankProfileId: "master-v2" as const, difficultyBand: "MEDIUM" as const, originalDifficulty: "MEDIUM" }
    const unrated = { ...question("v2-historical", 2), bankId: "master-v2", bankProfileId: "master-v2" as const, difficultyBand: "UNRATED" as const, originalDifficulty: "HISTORICAL_UNRATED" }
    const stats = buildStatistics([medium, unrated], new Map())

    expect(stats.difficulties.map((item) => item.label)).toEqual(["MEDIUM", "Histórica / sin clasificar"])
  })
})
