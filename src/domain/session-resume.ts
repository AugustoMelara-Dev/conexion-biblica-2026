export function resumeQuestionIndex(savedIndex: number, answerCount: number, questionCount: number) {
  if (questionCount <= 0) return 0
  return Math.min(Math.max(savedIndex, answerCount), questionCount - 1)
}
