import type { AnswerValue, EvaluationResult, Question } from "@/domain/types"

function asArray(value: AnswerValue): string[] {
  if (Array.isArray(value)) return value.map(String)
  if (typeof value === "string") return [value]
  return []
}

function sameMembers(left: string[], right: string[]) {
  if (left.length !== right.length) return false
  const leftSet = new Set(left)
  const rightSet = new Set(right)
  return leftSet.size === rightSet.size && [...leftSet].every((value) => rightSet.has(value))
}

function sameSequence(left: string[], right: string[]) {
  return left.length === right.length && left.every((value, index) => value === right[index])
}

function canonicalText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLocaleLowerCase("es")
}

function sameMatches(question: Question, value: AnswerValue) {
  if (!value || Array.isArray(value) || typeof value !== "object") return false
  const expected = new Map((question.correctMatches ?? []).map((match) => [match.left, match.right]))
  const actual = value as Record<string, string>
  return expected.size === Object.keys(actual).length && [...expected].every(([left, right]) => actual[left] === right)
}

export function isCorrectAnswer(question: Question, answer: AnswerValue): boolean {
  if (answer === null || answer === undefined) return false
  if (question.answerMode === "canonical_text") {
    return typeof answer === "string"
      && Boolean(question.correctAnswerText)
      && canonicalText(answer) === canonicalText(question.correctAnswerText ?? "")
  }
  if (question.type === "matching") return sameMatches(question, answer)
  const expected = question.correctAnswer.map(String)
  const actual = asArray(answer)
  if (question.type === "multi_select") return sameMembers(actual, expected)
  if (question.type === "ordering") return sameSequence(actual, expected)
  return actual.length === 1 && expected.length === 1 && actual[0] === expected[0]
}

export function evaluateAnswer(
  question: Question,
  answer: AnswerValue,
  suppliedReason?: "timeout" | "unanswered",
  responseTimeMs = 0,
): EvaluationResult {
  const wasAnswered = answer !== null && answer !== undefined && suppliedReason !== "timeout" && suppliedReason !== "unanswered"
  const reason = suppliedReason ?? (wasAnswered ? (isCorrectAnswer(question, answer) ? "correct" : "incorrect") : "unanswered")
  return {
    isCorrect: reason === "correct",
    wasAnswered,
    responseTimeMs: Math.max(0, responseTimeMs),
    reason,
  }
}

export function getMedian(values: number[]): number {
  if (values.length === 0) return 0
  const sorted = [...values].sort((left, right) => left - right)
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0 ? (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle]
}
