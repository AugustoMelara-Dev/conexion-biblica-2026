function seeded(seed) {
  let state = seed >>> 0
  return () => ((state = (state * 1664525 + 1013904223) >>> 0) / 4294967296)
}

function shuffle(items, rng) {
  const copy = [...items]
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const target = Math.floor(rng() * (index + 1)); [copy[index], copy[target]] = [copy[target], copy[index]]
  }
  return copy
}

const bands = ["EXPERT", "HARD", "MEDIUM", "BASIC"]

function difficultyBand(question) {
  if (question.difficultyBand && question.difficultyBand !== "UNRATED") return question.difficultyBand
  if (question.difficulty >= 5) return "EXPERT"
  if (question.difficulty === 4) return "HARD"
  if (question.difficulty === 3) return "MEDIUM"
  return "BASIC"
}

export function runPilot(questions, options = {}) {
  const rounds = options.rounds ?? 100
  const count = options.count ?? 50
  const rng = seeded(options.seed ?? 2026)
  const targets = { EXPERT: Math.round(count * .4), HARD: Math.round(count * .35), MEDIUM: Math.round(count * .2) }
  targets.BASIC = count - targets.EXPERT - targets.HARD - targets.MEDIUM
  const roundResults = []
  for (let round = 0; round < rounds; round += 1) {
    const selected = []
    for (const band of bands) {
      const bucket = questions.filter((question) => difficultyBand(question) === band)
      selected.push(...shuffle(bucket, rng).slice(0, targets[band]))
    }
    if (selected.length < count) {
      const keys = new Set(selected.map((question) => question.id))
      selected.push(...shuffle(questions.filter((question) => !keys.has(question.id)), rng).slice(0, count - selected.length))
    }
    const mix = { EXPERT: 0, HARD: 0, MEDIUM: 0, BASIC: 0 }
    selected.forEach((question) => { mix[difficultyBand(question)] += 1 })
    const wordCounts = selected.map((question) => `${question.question} ${(question.options ?? []).map((option) => option.text).join(" ")}`.trim().split(/\s+/).length)
    roundResults.push({ round: round + 1, count: selected.length, unique: new Set(selected.map((question) => question.id)).size, families: new Set(selected.map((question) => question.factKey)).size, sources: Object.fromEntries([...new Set(selected.map((question) => question.source.work))].map((work) => [work, selected.filter((question) => question.source.work === work).length])), difficultyMix: mix, averageWords: wordCounts.length ? wordCounts.reduce((sum, value) => sum + value, 0) / wordCounts.length : 0 })
  }
  const averageDifficultyMix = Object.fromEntries(bands.map((band) => [band, Math.round(roundResults.reduce((sum, round) => sum + round.difficultyMix[band], 0) / rounds)]))
  const averageWords = roundResults.reduce((sum, round) => sum + round.averageWords, 0) / Math.max(1, rounds)
  return {
    generatedAt: new Date().toISOString(),
    preset: { count, perQuestionSeconds: 12, totalSeconds: count * 12, scoring: "percentage_correct_0_100" },
    targets,
    summary: { poolSize: questions.length, rounds, completeRounds: roundResults.filter((round) => round.count === count).length, roundsWithDuplicates: roundResults.filter((round) => round.unique !== round.count).length, averageFamilies: Math.round(roundResults.reduce((sum, round) => sum + round.families, 0) / Math.max(1, rounds) * 10) / 10, averageWords: Math.round(averageWords * 10) / 10, averageDifficultyMix },
    rounds: roundResults,
  }
}
