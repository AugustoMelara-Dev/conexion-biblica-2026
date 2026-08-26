export type FactMasteryState =
  | "unseen"
  | "exposed"
  | "repaired"
  | "fragile"
  | "learning"
  | "due"
  | "stable"
  | "mastered"
  | "lapsed"

export type EvidenceKind = "practice" | "cold" | "deferred" | "blind"

export type FactEvidenceEvent = {
  factId: string
  variantId: string
  semanticSkill: string
  sessionId: string
  occurredAt: number
  isCorrect: boolean
  firstAttempt: boolean
  hintUsed: boolean
  afterFeedback: boolean
  responseTimeMs: number
  personalMedianMs: number
  difficulty: 1 | 2 | 3 | 4 | 5
  exposureKind: EvidenceKind
}

export type FactMastery = {
  factId: string
  chapter: string
  state: FactMasteryState
  evidencePoints: number
  qualifyingFirstAttempts: number
  attempts: number
  failures: number
  variantIds: string[]
  semanticSkills: string[]
  sessionIds: string[]
  firstSeenAt: number | null
  lastSeenAt: number | null
  lastQualifyingAt: number | null
  hasSixHourRetrieval: boolean
  hasNextDayRetrieval: boolean
  hasHardRetrieval: boolean
  nextDueAt: number | null
  firstAttemptAttempts?: number
  firstAttemptCorrect?: number
  contextualAttempts?: number
  contextualCorrect?: number
  sixHourAttempts?: number
  sixHourCorrect?: number
  nextDayAttempts?: number
  nextDayCorrect?: number
}

const HOUR = 3_600_000

function tegucigalpaDay(timestamp: number) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Tegucigalpa",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(timestamp)
}

export function emptyFactMastery(factId: string): FactMastery {
  return {
    factId,
    chapter: factId.match(/^(?:DAN\d+|PR\d+)/)?.[0] ?? "UNKNOWN",
    state: "unseen",
    evidencePoints: 0,
    qualifyingFirstAttempts: 0,
    attempts: 0,
    failures: 0,
    variantIds: [],
    semanticSkills: [],
    sessionIds: [],
    firstSeenAt: null,
    lastSeenAt: null,
    lastQualifyingAt: null,
    hasSixHourRetrieval: false,
    hasNextDayRetrieval: false,
    hasHardRetrieval: false,
    nextDueAt: null,
    firstAttemptAttempts: 0,
    firstAttemptCorrect: 0,
    contextualAttempts: 0,
    contextualCorrect: 0,
    sixHourAttempts: 0,
    sixHourCorrect: 0,
    nextDayAttempts: 0,
    nextDayCorrect: 0,
  }
}

function appendUnique(values: string[], value: string) {
  return values.includes(value) ? values : [...values, value]
}

function pointsFor(event: FactEvidenceEvent, interval: number | null) {
  if (event.hintUsed || event.afterFeedback || !event.firstAttempt) return 0
  let points = event.exposureKind === "blind" ? 30 : 24
  if (interval !== null && interval >= 24 * HOUR) points = 25
  else if (interval !== null && interval >= 6 * HOUR) points = 20
  else if (interval !== null && interval >= 45 * 60_000) points = 15
  if (event.responseTimeMs > event.personalMedianMs * 1.4) points = Math.min(points, 10)
  return points
}

export function applyFactEvidence(previous: FactMastery, event: FactEvidenceEvent): FactMastery {
  const interval = previous.lastQualifyingAt === null ? null : event.occurredAt - previous.lastQualifyingAt
  const slow = event.responseTimeMs > event.personalMedianMs * 1.4
  const validFirstAttempt = event.firstAttempt && !event.hintUsed && !event.afterFeedback
  const contextual = /context|scene|comparison|difference|sequence|cause|consequence/.test(event.semanticSkill)
  const sixHourRetrieval = validFirstAttempt && interval !== null && interval >= 6 * HOUR
  const nextDayRetrieval =
    validFirstAttempt &&
    previous.lastQualifyingAt !== null &&
    tegucigalpaDay(previous.lastQualifyingAt) !== tegucigalpaDay(event.occurredAt)
  const base: FactMastery = {
    ...previous,
    attempts: previous.attempts + 1,
    variantIds: appendUnique(previous.variantIds, event.variantId),
    semanticSkills: appendUnique(previous.semanticSkills, event.semanticSkill),
    sessionIds: appendUnique(previous.sessionIds, event.sessionId),
    firstSeenAt: previous.firstSeenAt ?? event.occurredAt,
    lastSeenAt: event.occurredAt,
    firstAttemptAttempts: (previous.firstAttemptAttempts ?? 0) + Number(validFirstAttempt),
    firstAttemptCorrect: (previous.firstAttemptCorrect ?? 0) + Number(validFirstAttempt && event.isCorrect),
    contextualAttempts: (previous.contextualAttempts ?? 0) + Number(validFirstAttempt && contextual),
    contextualCorrect: (previous.contextualCorrect ?? 0) + Number(validFirstAttempt && contextual && event.isCorrect),
    sixHourAttempts: (previous.sixHourAttempts ?? 0) + Number(sixHourRetrieval),
    sixHourCorrect: (previous.sixHourCorrect ?? 0) + Number(sixHourRetrieval && event.isCorrect),
    nextDayAttempts: (previous.nextDayAttempts ?? 0) + Number(nextDayRetrieval),
    nextDayCorrect: (previous.nextDayCorrect ?? 0) + Number(nextDayRetrieval && event.isCorrect),
  }

  if (!event.isCorrect) {
    return {
      ...base,
      state: previous.state === "mastered" ? "lapsed" : "due",
      failures: previous.failures + 1,
      evidencePoints: Math.max(0, previous.evidencePoints - (previous.failures ? 35 : 25)),
      nextDueAt: null,
    }
  }

  if (event.afterFeedback) return { ...base, state: "repaired", nextDueAt: event.occurredAt + HOUR }
  if (event.hintUsed || !event.firstAttempt) return { ...base, state: "exposed" }

  const points = pointsFor(event, interval)
  const qualifyingFirstAttempts = previous.qualifyingFirstAttempts + 1
  const hasSixHourRetrieval = previous.hasSixHourRetrieval || (interval !== null && interval >= 6 * HOUR)
  const hasNextDayRetrieval =
    previous.hasNextDayRetrieval ||
    (previous.lastQualifyingAt !== null &&
      tegucigalpaDay(previous.lastQualifyingAt) !== tegucigalpaDay(event.occurredAt))
  const hasHardRetrieval = previous.hasHardRetrieval || event.difficulty >= 4
  const candidate = {
    ...base,
    evidencePoints: previous.evidencePoints + points,
    qualifyingFirstAttempts,
    lastQualifyingAt: event.occurredAt,
    hasSixHourRetrieval,
    hasNextDayRetrieval,
    hasHardRetrieval,
  }
  const mastered =
    qualifyingFirstAttempts >= 3 &&
    candidate.semanticSkills.length >= 3 &&
    candidate.sessionIds.length >= 2 &&
    hasSixHourRetrieval &&
    hasNextDayRetrieval &&
    hasHardRetrieval &&
    !slow
  const state: FactMasteryState = mastered
    ? "mastered"
    : slow
      ? "fragile"
      : qualifyingFirstAttempts >= 2
        ? "stable"
        : "learning"
  return { ...candidate, state }
}
