import type { SessionAnswer, SessionMode } from "@/domain/types"

export const SIMULATION_PRESET = {
  count: 50,
  perQuestionSeconds: 12,
  totalSeconds: 600,
} as const

export function calculateSessionScore(mode: SessionMode, answers: SessionAnswer[]) {
  const correct = answers.filter((answer) => answer.result.isCorrect).length
  if (mode !== "simulation") return correct
  return answers.length ? Math.round((correct / answers.length) * 100) : 0
}

