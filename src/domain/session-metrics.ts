import type { Session } from "@/domain/types"

export function buildSessionMetrics(session: Session) {
  const correct = session.answers.filter((answer) => answer.result.isCorrect).length
  const accuracy = session.answers.length ? Math.round((correct / session.answers.length) * 100) : 0
  return {
    correct,
    accuracy,
    scoreLabel: session.context === "simulation" ? `${session.score}/100` : `${session.score}/${session.answers.length}`,
  }
}

