import type { AttemptContext, EvaluationResult, QuestionProgress } from "@/domain/types"

export function createEmptyProgress(questionKey: string): QuestionProgress {
  return {
    questionKey,
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

export function applyProgress(
  previous: QuestionProgress | undefined,
  result: EvaluationResult,
  now: number,
  context: AttemptContext = "practice",
): QuestionProgress {
  const current = previous ? structuredClone(previous) : createEmptyProgress("")
  current.timesSeen += 1
  current.lastSeenAt = now
  current.lastResponseTimeMs = result.responseTimeMs
  if (result.wasAnswered) {
    const previousAnswered = current.timesSeen - current.timesUnanswered
    current.averageResponseTimeMs =
      (current.averageResponseTimeMs * Math.max(0, previousAnswered - 1) + result.responseTimeMs) / previousAnswered
    current.bestResponseTimeMs = current.bestResponseTimeMs === null ? result.responseTimeMs : Math.min(current.bestResponseTimeMs, result.responseTimeMs)
  }
  if (result.isCorrect) {
    current.timesCorrect += 1
    current.currentCorrectStreak += 1
    current.masteryScore = Math.min(5, current.masteryScore + 1)
  } else {
    current.timesIncorrect += 1
    current.currentCorrectStreak = 0
    current.masteryScore = Math.max(0, current.masteryScore - 1)
  }
  if (!result.wasAnswered) current.timesUnanswered += 1
  current.history = [
    ...current.history,
    {
      timestamp: now,
      isCorrect: result.isCorrect,
      wasAnswered: result.wasAnswered,
      responseTimeMs: result.responseTimeMs,
      reason: result.reason,
      context,
    },
  ].slice(-30)
  return current
}

export function isMastered(progress: QuestionProgress | undefined): boolean {
  if (!progress || progress.masteryScore < 4 || progress.timesCorrect < 3) return false
  const recent = progress.history.slice(-3)
  return recent.length === 3 && recent.every((attempt) => attempt.isCorrect && attempt.wasAnswered)
}

export function isQuestionNew(progress: QuestionProgress | undefined) {
  return !progress || progress.timesSeen === 0
}
