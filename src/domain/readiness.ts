export type ChapterReadinessInput = {
  deferredAccuracy: number
  blindOrNovelAccuracy: number
  factCoverage: number
  timeStability: number
}

const clamp = (value: number) => Math.max(0, Math.min(1, value))

export function calculateChapterReadiness(input: ChapterReadinessInput) {
  const score =
    clamp(input.deferredAccuracy) * 0.4 +
    clamp(input.blindOrNovelAccuracy) * 0.3 +
    clamp(input.factCoverage) * 0.2 +
    clamp(input.timeStability) * 0.1
  return Math.round(score * 100)
}
