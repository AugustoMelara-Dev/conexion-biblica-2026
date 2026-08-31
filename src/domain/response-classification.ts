export type ResponseClassification =
  | "correct_secure"
  | "correct_slow"
  | "correct_doubted"
  | "incorrect"
  | "unanswered"

export type ResponseClassificationInput = {
  wasAnswered: boolean
  isCorrect: boolean
  responseTimeMs: number
  wasDoubted: boolean
}

export type ReviewPriority = 0 | 1 | 2

export function classifyResponse(
  input: ResponseClassificationInput
): ResponseClassification {
  if (!input.wasAnswered) return "unanswered"
  if (!input.isCorrect) return "incorrect"
  if (input.wasDoubted) return "correct_doubted"
  if (input.responseTimeMs > 6_000) return "correct_slow"
  return "correct_secure"
}

export function reviewPriorityForClassification(
  classification: ResponseClassification
): ReviewPriority {
  if (classification === "incorrect" || classification === "unanswered")
    return 2
  if (classification === "correct_slow" || classification === "correct_doubted")
    return 1
  return 0
}

export function classifyLatestProgressResponse(
  progress: QuestionProgress | undefined
): ResponseClassification | null {
  const latest = progress?.history.at(-1)
  if (!latest) return null
  return classifyResponse({
    wasAnswered: latest.wasAnswered,
    isCorrect: latest.isCorrect,
    responseTimeMs: latest.responseTimeMs,
    wasDoubted: false,
  })
}

export function reviewPriorityForProgress(
  progress: QuestionProgress | undefined
): ReviewPriority {
  const classification = classifyLatestProgressResponse(progress)
  return classification === null
    ? 0
    : reviewPriorityForClassification(classification)
}
import type { QuestionProgress } from "@/domain/types"
