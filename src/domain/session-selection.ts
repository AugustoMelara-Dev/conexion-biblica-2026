import { getQuestionKey, questionsShareFacts } from "@/domain/banks"
import type { CoverageCycle, Question, SessionConfig } from "@/domain/types"

export type CoverageSelection = {
  questions: Question[]
  cycle: CoverageCycle
  remaining: number
  seen: number
  total: number
  completed: boolean
}

export function createSeededRng(seed: number) {
  let value = seed >>> 0
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0
    return value / 4294967296
  }
}

export function fisherYates<T>(items: readonly T[], rng: () => number = Math.random): T[] {
  const shuffled = [...items]
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const selected = Math.floor(rng() * (index + 1))
    ;[shuffled[index], shuffled[selected]] = [shuffled[selected], shuffled[index]]
  }
  return shuffled
}

function hashString(value: string) {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0).toString(16).padStart(8, "0")
}

function sorted<T extends string | number>(values: readonly T[]) {
  return [...values].sort((left, right) => String(left).localeCompare(String(right), "es", { numeric: true }))
}

export function buildPoolKey(config: SessionConfig) {
  const relevant = {
    bankSelection: config.bankSelection ?? "legacy-v1",
    sourceWorks: sorted(config.sourceWorks),
    chapters: sorted(config.chapters),
    difficulties: sorted(config.difficulties),
    difficultyBands: sorted(config.difficultyBands ?? []),
    types: sorted(config.types),
    statuses: sorted(config.statuses),
    mode: config.mode,
  }
  return `pool-${hashString(JSON.stringify(relevant))}`
}

function bucketKey(question: Question) {
  return `${question.bankProfileId ?? "legacy-v1"}|${question.source.work}|${question.source.chapter}`
}

/**
 * Selects from shuffled buckets before applying spacing. Selection itself is
 * balanced, so scarce chapters/banks participate until their bucket empties.
 */
function selectSpacedBuckets(pool: Question[], count: number, rng: () => number) {
  const buckets = new Map<string, Question[]>()
  pool.forEach((question) => {
    const key = bucketKey(question)
    buckets.set(key, [...(buckets.get(key) ?? []), question])
  })
  const queues = fisherYates([...buckets.entries()], rng).map(([key, questions]) => ({ key, questions: fisherYates(questions, rng) }))
  const result: Question[] = []
  const target = Math.min(Math.max(0, count), pool.length)
  let cursor = 0
  while (result.length < target && queues.some((bucket) => bucket.questions.length > 0)) {
    const available = queues.filter((bucket) => bucket.questions.length > 0)
    const last = result.at(-1)
    const preferred = available.find((bucket, offset) => {
      const question = bucket.questions[0]
      return offset >= cursor % Math.max(1, available.length)
        && question.source.chapter !== last?.source.chapter
        && !questionsShareFacts(question, last)
    }) ?? available.find((bucket) => {
      const question = bucket.questions[0]
      return question.source.chapter !== last?.source.chapter && !questionsShareFacts(question, last)
    }) ?? available.find((bucket) => !questionsShareFacts(bucket.questions[0], last)) ?? available[0]
    result.push(preferred.questions.shift()!)
    cursor = (queues.indexOf(preferred) + 1) % Math.max(1, queues.length)
  }
  return result
}

export function selectBalancedRandom(pool: Question[], count: number, rng: () => number = Math.random) {
  const unique = [...new Map(pool.map((question) => [getQuestionKey(question), question])).values()]
  const target = Math.min(Math.max(0, count), unique.length)
  const groupedByProfile = new Map<string, Question[]>()
  unique.forEach((question) => {
    const profile = question.bankProfileId ?? "legacy-v1"
    groupedByProfile.set(profile, [...(groupedByProfile.get(profile) ?? []), question])
  })
  const profileGroups = fisherYates(
    [...groupedByProfile.entries()],
    rng,
  )

  if (profileGroups.length <= 1) return selectSpacedBuckets(unique, target, rng)

  const allocations = profileGroups.map(([profile, questions], index) => ({
    profile,
    questions,
    count: Math.min(questions.length, Math.floor(target / profileGroups.length) + (index < target % profileGroups.length ? 1 : 0)),
  }))
  let unallocated = target - allocations.reduce((sum, allocation) => sum + allocation.count, 0)
  while (unallocated > 0) {
    const receiver = allocations.find((allocation) => allocation.count < allocation.questions.length)
    if (!receiver) break
    receiver.count += 1
    unallocated -= 1
  }

  const queues = allocations.map((allocation) => ({
    profile: allocation.profile,
    questions: selectSpacedBuckets(allocation.questions, allocation.count, rng),
  }))
  const result: Question[] = []
  let cursor = 0
  while (result.length < target && queues.some((queue) => queue.questions.length > 0)) {
    const available = queues.filter((queue) => queue.questions.length > 0)
    const last = result.at(-1)
    const preferred = available.find((queue, offset) =>
      offset >= cursor % Math.max(1, available.length) && !questionsShareFacts(queue.questions[0], last),
    ) ?? available.find((queue) => !questionsShareFacts(queue.questions[0], last)) ?? available[0]
    result.push(preferred.questions.shift()!)
    cursor = (queues.indexOf(preferred) + 1) % Math.max(1, queues.length)
  }
  return result
}

function createCycle(pool: Question[], poolKey: string, rng: () => number, now: number): CoverageCycle {
  return {
    poolKey,
    cycleId: `${poolKey}:${now}`,
    remainingQuestionKeys: selectBalancedRandom(pool, pool.length, rng).map(getQuestionKey),
    seenQuestionKeys: [],
    totalPoolSize: new Set(pool.map(getQuestionKey)).size,
    createdAt: now,
    updatedAt: now,
  }
}

function reconcileCycle(cycle: CoverageCycle, pool: Question[], rng: () => number, now: number): CoverageCycle {
  const available = new Set(pool.map(getQuestionKey))
  const seen = cycle.seenQuestionKeys.filter((key) => available.has(key))
  const remaining = cycle.remainingQuestionKeys.filter((key) => available.has(key) && !seen.includes(key))
  const known = new Set([...seen, ...remaining])
  const additions = selectBalancedRandom(pool.filter((question) => !known.has(getQuestionKey(question))), pool.length, rng).map(getQuestionKey)
  return {
    ...cycle,
    remainingQuestionKeys: [...remaining, ...additions],
    seenQuestionKeys: seen,
    totalPoolSize: available.size,
    updatedAt: now,
  }
}

export function selectCoverageCycle(input: {
  pool: Question[]
  count: number
  poolKey: string
  cycle?: CoverageCycle | null
  reset?: boolean
  rng?: () => number
  now?: number
}): CoverageSelection {
  const rng = input.rng ?? Math.random
  const now = input.now ?? Date.now()
  const shouldCreate = input.reset || !input.cycle || input.cycle.poolKey !== input.poolKey
  const current = shouldCreate
    ? createCycle(input.pool, input.poolKey, rng, now)
    : reconcileCycle(input.cycle!, input.pool, rng, now)
  const take = Math.min(Math.max(0, input.count), current.remainingQuestionKeys.length)
  const selectedKeys = current.remainingQuestionKeys.slice(0, take)
  const questionMap = new Map(input.pool.map((question) => [getQuestionKey(question), question]))
  const questions = selectedKeys.map((key) => questionMap.get(key)).filter((question): question is Question => Boolean(question))
  const cycle: CoverageCycle = {
    ...current,
    remainingQuestionKeys: current.remainingQuestionKeys.slice(take),
    seenQuestionKeys: [...current.seenQuestionKeys, ...selectedKeys],
    updatedAt: now,
  }
  return {
    questions,
    cycle,
    remaining: cycle.remainingQuestionKeys.length,
    seen: cycle.seenQuestionKeys.length,
    total: cycle.totalPoolSize,
    completed: cycle.remainingQuestionKeys.length === 0,
  }
}

export function selectSequentialBlock(pool: Question[], count: number, blockIndex: number) {
  const unique = [...new Map(pool.map((question) => [getQuestionKey(question), question])).values()]
  const safeCount = Math.max(1, count)
  const blockCount = Math.ceil(unique.length / safeCount)
  const index = Math.max(0, Math.min(blockIndex, Math.max(0, blockCount - 1)))
  return {
    questions: unique.slice(index * safeCount, (index + 1) * safeCount),
    blockIndex: index,
    blockCount,
  }
}
