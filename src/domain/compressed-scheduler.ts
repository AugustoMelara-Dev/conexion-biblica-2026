export type SchedulerOutcome = "incorrect" | "repaired" | "slow_correct" | "fast_correct"
export type ContentTier = "A" | "B" | "C"
export type RetrievalStage = "initial" | "hour" | "six_hour" | "next_day"

export type RetrievalSchedule = {
  dueAt: number | null
  queueGap: number | null
  reason: "repair" | "deferred" | "maintenance"
}

const HOUR = 3_600_000

export function scheduleNextRetrieval(input: {
  outcome: SchedulerOutcome
  now: number
  tier: ContentTier
  stage?: RetrievalStage
}): RetrievalSchedule {
  if (input.outcome === "incorrect") return { dueAt: null, queueGap: 12, reason: "repair" }
  if (input.outcome === "repaired") return { dueAt: input.now + HOUR, queueGap: null, reason: "deferred" }
  if (input.outcome === "slow_correct") return { dueAt: input.now + 4 * HOUR, queueGap: 30, reason: "deferred" }
  if (input.stage === "six_hour") return { dueAt: input.now + 18 * HOUR, queueGap: null, reason: "maintenance" }
  if (input.stage === "next_day") return { dueAt: input.now + 12 * HOUR, queueGap: null, reason: "maintenance" }
  return {
    dueAt: input.now + (input.tier === "A" ? 6 : input.tier === "B" ? 8 : 10) * HOUR,
    queueGap: null,
    reason: input.tier === "C" ? "maintenance" : "deferred",
  }
}
