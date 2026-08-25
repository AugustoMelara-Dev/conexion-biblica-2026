import { buildFamilyMastery } from "@/domain/family-mastery"
import type { Question, QuestionProgress, SourceWork } from "@/domain/types"

export type FamilyStatus = "weak" | "pending" | "mastered" | "learning"

export type FamilyInsight = {
  factKey: string
  label: string
  work: SourceWork
  chapter: number
  variants: number
  seenVariants: number
  pendingVariants: number
  incorrect: number
  mastery: number
  priority: number
  status: FamilyStatus
}

const statusOrder: Record<FamilyStatus, number> = { weak: 0, pending: 1, learning: 2, mastered: 3 }

export function buildFamilyInsights(
  questions: Question[],
  progress: ReadonlyMap<string, QuestionProgress>,
  now = Date.now(),
): FamilyInsight[] {
  const mastery = buildFamilyMastery(questions, progress, now)
  const families = new Map<string, Question[]>()
  questions.forEach((question) => families.set(question.factKey, [...(families.get(question.factKey) ?? []), question]))

  return [...families.entries()].map(([factKey, variants]) => {
    const first = variants[0]
    const metrics = mastery.get(factKey)!
    const seenVariants = variants.filter((question) => (progress.get(`${question.bankId ?? "local"}:${question.id}`)?.timesSeen ?? 0) > 0).length
    const pendingVariants = variants.length - seenVariants
    const status: FamilyStatus = metrics.incorrect > 0 || (seenVariants > 0 && metrics.mastery < 2)
      ? "weak"
      : pendingVariants === variants.length
        ? "pending"
        : pendingVariants === 0 && metrics.mastery >= 4
          ? "mastered"
          : "learning"
    return {
      factKey,
      label: first.question,
      work: first.source.work,
      chapter: first.source.chapter,
      variants: variants.length,
      seenVariants,
      pendingVariants,
      incorrect: metrics.incorrect,
      mastery: Math.round(metrics.mastery * 10) / 10,
      priority: metrics.priority,
      status,
    }
  }).sort((left, right) => statusOrder[left.status] - statusOrder[right.status] || right.priority - left.priority || left.factKey.localeCompare(right.factKey))
}

