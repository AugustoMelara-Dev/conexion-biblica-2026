import { isMastered, isQuestionNew } from "@/domain/mastery"
import type { Question, QuestionProgress, SessionConfig } from "@/domain/types"
import { selectSequentialBlock } from "@/domain/session-selection"
import { questionsShareFacts } from "@/domain/banks"
import { buildFamilyMastery } from "@/domain/family-mastery"
import { reviewPriorityForProgress } from "@/domain/response-classification"

function createRng(seed: number) {
  let value = seed >>> 0
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0
    return value / 4294967296
  }
}

export function selectNextFamilyVariant(
  family: Question[],
  seenQuestionKeys: ReadonlySet<string>,
  seed: number
) {
  if (family.length === 0) return undefined
  const unseen = family.filter(
    (question) =>
      !seenQuestionKeys.has(`${question.bankId ?? "local"}:${question.id}`)
  )
  const pool = unseen.length > 0 ? unseen : family
  return pool[Math.floor(createRng(seed)() * pool.length)]
}

function normalizedQuestionText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLocaleLowerCase("es")
}

function dedupeSessionCandidates(questions: Question[]) {
  const result: Question[] = []
  const contentIndexes = new Map<string, number>()
  questions.forEach((question) => {
    const optionText = question.options
      .map((option) => normalizedQuestionText(option.text))
      .join("|")
    const contentKey = `${normalizedQuestionText(question.question)}::${optionText}`
    const existingIndex = contentIndexes.get(contentKey)
    if (existingIndex === undefined) {
      contentIndexes.set(contentKey, result.length)
      result.push(question)
      return
    }
    const existing = result[existingIndex]
    if ((existing.bankId ?? "local") === (question.bankId ?? "local")) {
      result.push(question)
    } else if (question.bankProfileId === "prep-v3") {
      result[existingIndex] = question
    }
  })
  return result
}

function statusMatches(
  question: Question,
  progress: QuestionProgress | undefined,
  statuses: SessionConfig["statuses"]
) {
  if (statuses.length === 0 || statuses.includes("all")) return true
  return statuses.some((status) => {
    if (status === "new") return isQuestionNew(progress)
    if (status === "failed")
      return Boolean(progress && progress.timesIncorrect > 0)
    if (status === "difficult")
      return question.difficulty >= 4 || Boolean(progress?.markedDifficult)
    if (status === "mastered") return isMastered(progress)
    if (status === "favorite") return Boolean(progress?.favorite)
    return true
  })
}

function baseScore(
  question: Question,
  progress: QuestionProgress | undefined,
  mode: SessionConfig["mode"],
  recentBonus = 0
) {
  const failed = progress?.timesIncorrect ?? 0
  const slow = Math.min(
    50,
    Math.round((progress?.averageResponseTimeMs ?? 0) / 500)
  )
  const unseen = isQuestionNew(progress) ? 32 : 0
  if (mode === "championship" || mode === "simulation") {
    const difficultyWeight =
      question.difficultyBand === "UNRATED"
        ? 0
        : ({ 5: 100, 4: 82, 3: 60, 2: 25, 1: 10 } as const)[question.difficulty]
    const tagWeight = question.tags.some((tag) =>
      [
        "numero",
        "nombre",
        "detalle",
        "precision",
        "secuencia",
        "declaracion",
        "tiempo",
        "lugar",
        "high",
      ].includes(tag.toLowerCase())
    )
      ? 25
      : 0
    return (
      difficultyWeight + tagWeight + failed * 12 + slow + unseen + recentBonus
    )
  }
  if (mode === "errors")
    return (
      failed * 100 +
      (progress?.markedDifficult ? 60 : 0) +
      slow +
      question.difficulty * 4 +
      recentBonus * 2
    )
  if (mode === "new") return unseen + question.difficulty
  return failed * 40 + slow + question.difficulty * 5 + unseen
}

export function selectSessionQuestions(
  questions: Question[],
  progress: Map<string, QuestionProgress>,
  config: SessionConfig,
  seed: number
): Question[] {
  const rng = createRng(seed)
  const candidates = filterEligibleQuestions(questions, progress, config)
  const uniqueById = [
    ...new Map(
      candidates.map((question) => [
        `${question.bankId ?? "local"}:${question.id}`,
        question,
      ])
    ).values(),
  ]
  const unique = dedupeSessionCandidates(uniqueById)
  const target =
    config.count === "all"
      ? unique.length
      : Math.min(config.count, unique.length)
  if (!config.shuffleQuestions)
    return selectSequentialBlock(unique, target, config.sequentialBlock ?? 0)
      .questions
  const progressFor = (question: Question) =>
    progress.get(`${question.bankId ?? "local"}:${question.id}`) ??
    progress.get(question.id)
  const familyMastery =
    config.mode === "smart-review" ? buildFamilyMastery(unique, progress) : null
  const seenAt = unique
    .map((question) => progressFor(question)?.lastSeenAt)
    .filter((timestamp): timestamp is number => typeof timestamp === "number")
  const oldestSeenAt = seenAt.length ? Math.min(...seenAt) : 0
  const newestSeenAt = seenAt.length ? Math.max(...seenAt) : 0
  const recentBonusFor = (question: Question) => {
    const timestamp = progressFor(question)?.lastSeenAt
    if (timestamp === null || timestamp === undefined) return 0
    if (newestSeenAt === oldestSeenAt) return 20
    return ((timestamp - oldestSeenAt) / (newestSeenAt - oldestSeenAt)) * 20
  }
  const pool = unique.map((question) => ({
    question,
    reviewPriority:
      config.mode === "smart-review"
        ? reviewPriorityForProgress(progressFor(question))
        : 0,
    score:
      baseScore(
        question,
        progressFor(question),
        config.mode,
        recentBonusFor(question)
      ) +
      (familyMastery?.get(question.factKey)?.priority ?? 0) +
      rng() * 20,
  }))
  const result: Question[] = []
  let lastQuestion: Question | undefined
  let lastChapter = -1
  const championshipQuotas =
    config.mode === "championship" || config.mode === "simulation"
      ? [
          {
            matches: (question: Question) => question.difficulty === 5,
            remaining: Math.round(target * 0.4),
          },
          {
            matches: (question: Question) => question.difficulty === 4,
            remaining: Math.round(target * 0.35),
          },
          {
            matches: (question: Question) => question.difficulty === 3,
            remaining: Math.round(target * 0.2),
          },
          {
            matches: (question: Question) => question.difficulty <= 2,
            remaining: Math.max(
              0,
              target -
                Math.round(target * 0.4) -
                Math.round(target * 0.35) -
                Math.round(target * 0.2)
            ),
          },
        ]
      : null
  while (result.length < target && pool.length > 0) {
    let eligiblePool = pool
    const preferredQuota = championshipQuotas?.find(
      (quota) =>
        quota.remaining > 0 &&
        pool.some((candidate) => quota.matches(candidate.question))
    )
    const redistributedQuota =
      preferredQuota ??
      championshipQuotas?.find((quota) =>
        pool.some((candidate) => quota.matches(candidate.question))
      )
    if (redistributedQuota) {
      eligiblePool = pool.filter((candidate) =>
        redistributedQuota.matches(candidate.question)
      )
      if (preferredQuota) preferredQuota.remaining -= 1
    }
    eligiblePool.sort(
      (left, right) =>
        right.reviewPriority - left.reviewPriority || right.score - left.score
    )
    const preferred = eligiblePool.find(
      (candidate) =>
        !questionsShareFacts(candidate.question, lastQuestion) &&
        candidate.question.source.chapter !== lastChapter
    )
    const fallback = eligiblePool.find(
      (candidate) => !questionsShareFacts(candidate.question, lastQuestion)
    )
    const selected = preferred ?? fallback ?? eligiblePool[0]
    const index = pool.indexOf(selected)
    const [{ question }] = pool.splice(index, 1)
    result.push(question)
    lastQuestion = question
    lastChapter = question.source.chapter
  }
  return result
}

export function filterEligibleQuestions(
  questions: Question[],
  progress: Map<string, QuestionProgress>,
  config: SessionConfig
) {
  return questions.filter((question) => {
    const itemProgress =
      progress.get(`${question.bankId ?? "local"}:${question.id}`) ??
      progress.get(question.id)
    if (
      config.sourceWorks.length &&
      !config.sourceWorks.includes(question.source.work)
    )
      return false
    if (
      config.chapters.length &&
      !config.chapters.includes(question.source.chapter)
    )
      return false
    if (!config.includeBlind && (question.blindPool || question.blindFinalPool))
      return false
    if (question.metadata?.provisional) return false
    if (
      config.difficulties.length &&
      !config.difficulties.includes(question.difficulty)
    )
      return false
    if (config.tierFilter === "competitive") {
      if (
        question.tier !== "COMPETITIVE_ACCEPT" ||
        (question.difficultyBand !== "HARD" && question.difficultyBand !== "EXPERT")
      )
        return false
    } else if (config.tierFilter === "coverage") {
      if (question.tier !== "COVERAGE_ACCEPT")
        return false
    } else if (
      config.difficultyBands?.length &&
      question.difficultyBand &&
      !config.difficultyBands.includes(question.difficultyBand)
    ) {
      return false
    }
    if (config.types.length && !config.types.includes(question.type))
      return false
    if (
      (!config.massive || !config.trainingPresetId) &&
      !statusMatches(question, itemProgress, config.statuses)
    )
      return false
    if (
      config.mode === "errors" &&
      !(
        itemProgress &&
        (itemProgress.timesIncorrect > 0 || itemProgress.markedDifficult)
      )
    )
      return false
    if (config.mode === "difficult" && question.difficulty < 4) return false
    if (config.mode === "new" && !isQuestionNew(itemProgress)) return false
    return true
  })
}

/**
 * Reinsert a failed training question only after a meaningful cooldown.
 * Short rounds without enough room keep the question for a future session.
 */
export function scheduleTrainingRetry(
  queue: Question[],
  question: Question,
  currentIndex: number,
  waitFor: number
): Question[] {
  const key = `${question.bankId ?? "local"}:${question.id}`
  if (
    queue.some(
      (item, index) =>
        index > currentIndex && `${item.bankId ?? "local"}:${item.id}` === key
    )
  )
    return queue
  const insertAt = currentIndex + Math.max(1, waitFor) + 1
  if (insertAt > queue.length) return queue
  return [...queue.slice(0, insertAt), question, ...queue.slice(insertAt)]
}
