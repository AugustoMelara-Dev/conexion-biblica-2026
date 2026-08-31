import type { Question, QuestionExposure } from "@/domain/types"
import type { FactMastery } from "@/domain/fact-mastery"

function seededRandom(seed: number) {
  let state = seed >>> 0
  return () => {
    state = (Math.imul(state, 1103515245) + 12345) >>> 0
    return state / 0x100000000
  }
}

function shuffle<T>(items: T[], random: () => number) {
  const result = items.slice()
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1))
    ;[result[index], result[swap]] = [result[swap], result[index]]
  }
  return result
}

function factId(question: Question) {
  return question.factId ?? question.factKey
}

function variantId(question: Question) {
  return question.variantId ?? question.id
}

function isRouteNewPreset(presetId: string | undefined) {
  return Boolean(
    presetId && /^\d{4}-\d{2}-\d{2}-(new|adversarial)$/.test(presetId)
  )
}

function isRouteReviewPreset(presetId: string | undefined) {
  return Boolean(presetId && /^\d{4}-\d{2}-\d{2}-review$/.test(presetId))
}

function takeUniqueFacts(
  candidates: Question[],
  count: number,
  usedFacts: Set<string>,
  random: () => number
) {
  const selected: Question[] = []
  for (const question of shuffle(candidates, random)) {
    const key = factId(question)
    if (usedFacts.has(key)) continue
    usedFacts.add(key)
    selected.push(question)
    if (selected.length === count) break
  }
  return selected
}

export function selectAdaptiveSession({
  questions,
  exposures,
  count,
  weakChapters,
  includeBlind,
  seed,
  factMastery = [],
  presetId,
  now = Date.now(),
}: {
  questions: Question[]
  exposures: QuestionExposure[]
  count: number
  weakChapters: number[]
  includeBlind: boolean
  seed: number
  factMastery?: FactMastery[]
  presetId?: string
  now?: number
}) {
  const random = seededRandom(seed)
  const exposureByVariant = new Map(
    exposures.map((exposure) => [exposure.variantId, exposure])
  )
  const exposureByFact = new Map<string, QuestionExposure>()
  for (const exposure of exposures) {
    const current = exposureByFact.get(exposure.factId)
    if (!current || exposure.lastSeenAt > current.lastSeenAt)
      exposureByFact.set(exposure.factId, exposure)
  }
  const masteryByFact = new Map(
    factMastery.map((mastery) => [mastery.factId, mastery])
  )
  const eligible = questions.filter((question) => {
    if (!includeBlind && question.blindFinalPool) return false
    const mastery = masteryByFact.get(factId(question))
    if (
      presetId === "unseen-only" ||
      presetId === "blind-simulation" ||
      isRouteNewPreset(presetId)
    )
      return !mastery || mastery.state === "unseen"
    if (presetId === "slow-correct") return mastery?.state === "fragile"
    if (presetId === "previous-errors") return Boolean(mastery?.failures)
    if (isRouteReviewPreset(presetId))
      return Boolean(mastery?.failures || mastery?.state === "fragile")
    if (presetId !== "spaced-review") return true
    return (
      mastery?.nextDueAt !== null &&
      mastery?.nextDueAt !== undefined &&
      mastery.nextDueAt <= now
    )
  })
  const novel: Question[] = []
  const errors: Question[] = []
  const slow: Question[] = []
  const traps: Question[] = []
  const ordinary: Question[] = []
  const weak = new Set(weakChapters)

  for (const question of eligible) {
    const exposure =
      exposureByVariant.get(variantId(question)) ??
      exposureByFact.get(factId(question))
    if (!exposure) {
      novel.push(question)
      continue
    }
    if (exposure.incorrect > 0 && exposure.incorrect >= exposure.correct) {
      errors.push(question)
      continue
    }
    if (exposure.averageResponseTimeMs > 6000) {
      slow.push(question)
      continue
    }
    if (
      question.trapType === "true_elsewhere" &&
      (weak.size === 0 || weak.has(question.source.chapter))
    ) {
      traps.push(question)
      continue
    }
    ordinary.push(question)
  }

  const quotas = {
    novel: Math.floor(count * 0.6),
    errors: Math.floor(count * 0.2),
    slow: Math.floor(count * 0.1),
  }
  const usedFacts = new Set<string>()
  const selected = [
    ...takeUniqueFacts(novel, quotas.novel, usedFacts, random),
    ...takeUniqueFacts(errors, quotas.errors, usedFacts, random),
    ...takeUniqueFacts(slow, quotas.slow, usedFacts, random),
  ]
  const trapQuota = count - quotas.novel - quotas.errors - quotas.slow
  selected.push(...takeUniqueFacts(traps, trapQuota, usedFacts, random))

  if (selected.length < count) {
    const remaining = [...novel, ...errors, ...slow, ...traps, ...ordinary]
    selected.push(
      ...takeUniqueFacts(remaining, count - selected.length, usedFacts, random)
    )
  }
  return selected.slice(0, count)
}
