import type { FactMastery } from "@/domain/fact-mastery"
import type { QuestionExposure } from "@/domain/types"

type AccuracyMetric = { attempts: number; correct: number; accuracy: number }

function metric(attempts: number, correct: number): AccuracyMetric {
  return {
    attempts,
    correct,
    accuracy: attempts ? Math.round((correct / attempts) * 100) : 0,
  }
}

function masteryMetric(
  mastery: FactMastery[],
  attemptsKey: keyof FactMastery,
  correctKey: keyof FactMastery
) {
  const attempts = mastery.reduce((sum, fact) => sum + Number(fact[attemptsKey] ?? 0), 0)
  const correct = mastery.reduce((sum, fact) => sum + Number(fact[correctKey] ?? 0), 0)
  return metric(attempts, correct)
}

export function buildLearningMetrics(
  mastery: FactMastery[],
  exposures: QuestionExposure[]
) {
  const blind = exposures.reduce(
    (sum, exposure) => ({
      attempts: sum.attempts + (exposure.evidence?.blind.attempts ?? 0),
      correct: sum.correct + (exposure.evidence?.blind.correct ?? 0),
    }),
    { attempts: 0, correct: 0 }
  )

  return {
    firstAttempt: masteryMetric(mastery, "firstAttemptAttempts", "firstAttemptCorrect"),
    contextual: masteryMetric(mastery, "contextualAttempts", "contextualCorrect"),
    sixHour: masteryMetric(mastery, "sixHourAttempts", "sixHourCorrect"),
    nextDay: masteryMetric(mastery, "nextDayAttempts", "nextDayCorrect"),
    blind: metric(blind.attempts, blind.correct),
    recurringErrors: mastery.filter((fact) => fact.failures >= 2).length,
  }
}
