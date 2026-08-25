import type { Question, QuestionProgress } from "@/domain/types"

export type FamilyMastery = {
  factKey: string
  questionCount: number
  unseen: number
  incorrect: number
  mastery: number
  averageResponseTimeMs: number
  lastSeenAt: number | null
  priority: number
}

export function buildFamilyMastery(
  questions: Question[],
  progress: ReadonlyMap<string, QuestionProgress>,
  now = Date.now(),
) {
  const groups = new Map<string, Question[]>()
  questions.forEach((question) => groups.set(question.factKey, [...(groups.get(question.factKey) ?? []), question]))
  const result = new Map<string, FamilyMastery>()
  groups.forEach((family, factKey) => {
    const values = family.map((question) => progress.get(`${question.bankId ?? "local"}:${question.id}`)).filter((item): item is QuestionProgress => Boolean(item))
    const unseen = family.length - values.filter((item) => item.timesSeen > 0).length
    const incorrect = values.reduce((sum, item) => sum + item.timesIncorrect, 0)
    const mastery = values.length ? values.reduce((sum, item) => sum + item.masteryScore, 0) / values.length : 0
    const timed = values.filter((item) => item.averageResponseTimeMs > 0)
    const averageResponseTimeMs = timed.length ? timed.reduce((sum, item) => sum + item.averageResponseTimeMs, 0) / timed.length : 0
    const seen = values.map((item) => item.lastSeenAt).filter((value): value is number => value !== null)
    const lastSeenAt = seen.length ? Math.max(...seen) : null
    const ageDays = lastSeenAt === null ? 0 : Math.min(30, Math.max(0, now - lastSeenAt) / 86_400_000)
    const priority = unseen * 30 + incorrect * 50 + Math.min(40, averageResponseTimeMs / 500) + ageDays * 2 - mastery * 12
    result.set(factKey, { factKey, questionCount: family.length, unseen, incorrect, mastery, averageResponseTimeMs, lastSeenAt, priority })
  })
  return result
}
