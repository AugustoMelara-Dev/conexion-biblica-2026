import { getMedian } from "@/domain/evaluation"
import { isMastered } from "@/domain/mastery"
import type { Question, QuestionProgress, QuestionType, SourceWork } from "@/domain/types"
import { normalizedDifficulty } from "@/domain/banks"

export type AggregateMetric = {
  label: string
  key: string
  total: number
  seen: number
  correct: number
  incorrect: number
  unanswered: number
  accuracy: number
  averageResponseTimeMs: number
  mastery: number
}

export type GeneralMetric = {
  total: number
  seen: number
  correct: number
  incorrect: number
  unanswered: number
  accuracy: number
  averageResponseTimeMs: number
  medianResponseTimeMs: number
  bestResponseTimeMs: number
  slowestResponseTimeMs: number
  unseen: number
  mastered: number
  difficult: number
  favorite: number
}

export type Statistics = {
  general: GeneralMetric
  sources: AggregateMetric[]
  chapters: (AggregateMetric & { chapter: number; source: SourceWork })[]
  difficulties: AggregateMetric[]
  types: (AggregateMetric & { type: QuestionType })[]
  weakChapters: AggregateMetric[]
  weakTypes: AggregateMetric[]
  mostFailed: Question[]
  slowest: Question[]
}

function roundPercent(correct: number, total: number) {
  return total === 0 ? 0 : Math.round((correct / total) * 100)
}

function metricFromQuestions(questions: Question[], progress: Map<string, QuestionProgress>, label: string, key: string): AggregateMetric {
  const values = questions.map((question) => progress.get(`${question.bankId ?? "local"}:${question.id}`)).filter(Boolean) as QuestionProgress[]
  const total = values.reduce((sum, item) => sum + item.timesCorrect + item.timesIncorrect, 0)
  const correct = values.reduce((sum, item) => sum + item.timesCorrect, 0)
  const incorrect = values.reduce((sum, item) => sum + item.timesIncorrect, 0)
  const unanswered = values.reduce((sum, item) => sum + item.timesUnanswered, 0)
  const seen = values.reduce((sum, item) => sum + item.timesSeen, 0)
  const responseTimes = values.flatMap((item) => item.history.filter((attempt) => attempt.wasAnswered).map((attempt) => attempt.responseTimeMs))
  const averageResponseTimeMs = responseTimes.length ? Math.round(responseTimes.reduce((sum, item) => sum + item, 0) / responseTimes.length) : 0
  const mastery = values.length ? Math.round(values.reduce((sum, item) => sum + item.masteryScore, 0) / values.length) : 0
  return { label, key, total, seen, correct, incorrect, unanswered, accuracy: roundPercent(correct, total), averageResponseTimeMs, mastery }
}

export function buildStatistics(questions: Question[], progress: Map<string, QuestionProgress>): Statistics {
  const scopedKeys = new Set(questions.map((question) => `${question.bankId ?? "local"}:${question.id}`))
  const values = [...progress.values()].filter((item) => scopedKeys.has(item.questionKey))
  const total = values.reduce((sum, item) => sum + item.timesCorrect + item.timesIncorrect, 0)
  const correct = values.reduce((sum, item) => sum + item.timesCorrect, 0)
  const incorrect = values.reduce((sum, item) => sum + item.timesIncorrect, 0)
  const unanswered = values.reduce((sum, item) => sum + item.timesUnanswered, 0)
  const seen = values.reduce((sum, item) => sum + item.timesSeen, 0)
  const responseTimes = values.flatMap((item) => item.history.filter((attempt) => attempt.wasAnswered).map((attempt) => attempt.responseTimeMs))
  const bestValues = values.map((item) => item.bestResponseTimeMs).filter((item): item is number => item !== null)
  const general: GeneralMetric = {
    total,
    seen,
    correct,
    incorrect,
    unanswered,
    accuracy: roundPercent(correct, total),
    averageResponseTimeMs: responseTimes.length ? Math.round(responseTimes.reduce((sum, item) => sum + item, 0) / responseTimes.length) : 0,
    medianResponseTimeMs: getMedian(responseTimes),
    bestResponseTimeMs: bestValues.length ? Math.min(...bestValues) : 0,
    slowestResponseTimeMs: responseTimes.length ? Math.max(...responseTimes) : 0,
    unseen: Math.max(0, questions.length - new Set(values.filter((item) => item.timesSeen > 0).map((item) => item.questionKey)).size),
    mastered: values.filter((item) => isMastered(item)).length,
    difficult: questions.filter((question) => question.difficulty >= 4 || progress.get(`${question.bankId ?? "local"}:${question.id}`)?.markedDifficult).length,
    favorite: values.filter((item) => item.favorite).length,
  }
  const sourceWorks: SourceWork[] = ["Daniel", "Profetas y Reyes"]
  const sources = sourceWorks.map((work) => metricFromQuestions(questions.filter((question) => question.source.work === work), progress, work, work))
  const chapterMap = new Map<string, { source: SourceWork; chapter: number; questions: Question[] }>()
  questions.forEach((question) => {
    const key = `${question.source.work}:${question.source.chapter}`
    const current = chapterMap.get(key) ?? { source: question.source.work, chapter: question.source.chapter, questions: [] }
    current.questions.push(question)
    chapterMap.set(key, current)
  })
  const chapters = [...chapterMap.values()].map((item) => ({
    ...metricFromQuestions(item.questions, progress, `${item.source === "Daniel" ? "Daniel" : "PR"} ${item.chapter}`, `${item.source}:${item.chapter}`),
    chapter: item.chapter,
    source: item.source,
  })).sort((left, right) => left.accuracy - right.accuracy || left.label.localeCompare(right.label))
  const difficulties = questions.some((question) => question.bankProfileId === "master-v2")
    ? (["BASIC", "MEDIUM", "HARD", "EXPERT", "UNRATED"] as const)
      .filter((band) => questions.some((question) => normalizedDifficulty(question) === band))
      .map((band) => metricFromQuestions(questions.filter((question) => normalizedDifficulty(question) === band), progress, band === "UNRATED" ? "Histórica / sin clasificar" : band, band))
    : [1, 2, 3, 4, 5].map((difficulty) => metricFromQuestions(questions.filter((question) => question.difficulty === difficulty), progress, `Dificultad ${difficulty}`, String(difficulty)))
  const typeNames = [...new Set(questions.map((question) => question.type))]
  const types = typeNames.map((type) => ({ ...metricFromQuestions(questions.filter((question) => question.type === type), progress, typeLabel(type), type), type })).sort((left, right) => left.accuracy - right.accuracy)
  const mostFailed = [...questions].sort((left, right) => (progress.get(`${right.bankId ?? "local"}:${right.id}`)?.timesIncorrect ?? 0) - (progress.get(`${left.bankId ?? "local"}:${left.id}`)?.timesIncorrect ?? 0)).slice(0, 8)
  const slowest = [...questions].sort((left, right) => (progress.get(`${right.bankId ?? "local"}:${right.id}`)?.averageResponseTimeMs ?? 0) - (progress.get(`${left.bankId ?? "local"}:${left.id}`)?.averageResponseTimeMs ?? 0)).slice(0, 8)
  return { general, sources, chapters, difficulties, types, weakChapters: chapters.slice(0, 3), weakTypes: types.slice(0, 3), mostFailed, slowest }
}

export function typeLabel(type: QuestionType) {
  const labels: Record<QuestionType, string> = {
    single_choice: "Selección única",
    true_false: "Verdadero / falso",
    fill_blank: "Completar",
    multi_select: "Selección múltiple",
    ordering: "Ordenamiento",
    matching: "Relacionar",
    who_said_it: "Quién lo dijo",
    to_whom: "A quién",
    reference_detail: "Detalle de referencia",
    negative_choice: "Elección negativa",
    sequence_choice: "Secuencia",
    precision: "Precisión",
  }
  return labels[type]
}
