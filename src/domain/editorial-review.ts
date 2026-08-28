export type HumanReviewDisposition = "approved" | "corrected" | "rejected"

export type HumanReviewEntry = {
  id: string
  fact_id: string
  chapter: string
  family: string
  reference: string
  content_sha256: string
  risk_score: number
  automatic_flags: string[]
  automatic_status: "passed" | "requires_attention"
}

export type HumanReviewDecision = {
  id: string
  content_sha256: string
  reviewer: string
  reviewed_at: string
  disposition: HumanReviewDisposition
  notes: string
}

export function reconcileHumanReview(
  entries: HumanReviewEntry[],
  decisions: HumanReviewDecision[],
) {
  const decisionsById = new Map(decisions.map((item) => [item.id, item]))
  const reviewed: HumanReviewEntry[] = []
  const accepted: HumanReviewEntry[] = []
  const rejected: HumanReviewEntry[] = []
  const pending: HumanReviewEntry[] = []
  const stale: HumanReviewEntry[] = []

  for (const entry of entries) {
    const decision = decisionsById.get(entry.id)
    if (decision?.content_sha256 === entry.content_sha256) {
      reviewed.push(entry)
      if (decision.disposition === "rejected") rejected.push(entry)
      else accepted.push(entry)
    } else {
      pending.push(entry)
      if (decision) stale.push(entry)
    }
  }
  return { reviewed, accepted, rejected, pending, stale }
}

export function buildHumanReviewDecision(
  entry: HumanReviewEntry,
  input: {
    reviewer: string
    disposition: HumanReviewDisposition
    notes: string
    reviewedAt?: Date
  },
): HumanReviewDecision {
  const reviewer = input.reviewer.trim()
  if (!reviewer) throw new Error("Escribe el nombre del revisor.")
  return {
    id: entry.id,
    content_sha256: entry.content_sha256,
    reviewer,
    reviewed_at: (input.reviewedAt ?? new Date()).toISOString(),
    disposition: input.disposition,
    notes: input.notes.trim(),
  }
}

export function selectNextHumanReview(
  entries: HumanReviewEntry[],
  decisions: HumanReviewDecision[],
  filters: { family?: string; chapter?: string },
) {
  const decisionsById = new Map(decisions.map((item) => [item.id, item]))
  const reviewed = new Set(
    entries.flatMap((entry) =>
      decisionsById.get(entry.id)?.content_sha256 === entry.content_sha256
        ? [entry.id]
        : [],
    ),
  )
  return entries
    .filter(
      (entry) =>
        !reviewed.has(entry.id) &&
        (!filters.family || entry.family === filters.family) &&
        (!filters.chapter || entry.chapter === filters.chapter),
    )
    .sort(
      (left, right) =>
        right.risk_score - left.risk_score || left.id.localeCompare(right.id),
    )[0]
}
