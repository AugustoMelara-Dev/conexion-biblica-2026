function asText(value) {
  return value == null ? "" : String(value)
}

/**
 * Exact prompt identity is stable across line endings, Unicode compatibility
 * forms and incidental whitespace, while preserving punctuation and wording.
 */
export function duplicatePromptKey(value) {
  return asText(value).normalize("NFKC").replace(/\s+/gu, " ").trim()
}

function equivalentAnswerText(value) {
  return asText(value)
    .normalize("NFKC")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/gu, "")
    .toLocaleLowerCase("es")
    .replace(/[\p{P}\p{S}]+/gu, " ")
    .replace(/\s+/gu, " ")
    .trim()
}

function resolvedAnswerText(question) {
  if (!question) return ""
  if (question.answerMode === "canonical_text") return asText(question.correctAnswerText)
  const options = new Map((question.options ?? []).map((option) => [option.id, option.text]))
  return (question.correctAnswer ?? []).map((answerId) => options.get(answerId) ?? answerId).join(" | ")
}

export function resolvedAnswerKey(question) {
  return equivalentAnswerText(resolvedAnswerText(question))
}

function entryAnswerKey(entry) {
  return entry.curated
    ? resolvedAnswerKey(entry.curated)
    : equivalentAnswerText(entry.decision?.answer?.text)
}

function compareQuestionIds(left, right) {
  return asText(left).localeCompare(asText(right), "en", { numeric: true, sensitivity: "base" })
}

function addIssue(decision, issue) {
  return [...new Set([...(decision?.issues ?? []), issue])]
}

/**
 * Apply the final-review ruling to already curated entries. Every input entry
 * remains in the returned list and receives a decision; only the V4 payload
 * (`curated`) is removed from rejected duplicates.
 */
export function applyDuplicatePolicy(entries) {
  const output = entries.map((entry) => ({ ...entry }))
  const groups = new Map()
  for (const entry of output) {
    const key = duplicatePromptKey(entry.curated?.question ?? entry.raw?.pregunta)
    if (!key) continue
    const group = groups.get(key) ?? []
    group.push(entry)
    groups.set(key, group)
  }

  for (const group of groups.values()) {
    if (group.length < 2) continue
    const answerKeys = new Set(group.map(entryAnswerKey))
    const canonicalCandidates = group.filter((entry) => entry.curated)
    if (answerKeys.size > 1 || answerKeys.has("") || canonicalCandidates.length === 0) {
      for (const entry of group) {
        entry.decision = {
          ...entry.decision,
          status: "REJECTED",
          issues: addIssue(entry.decision, "DUPLICATE_PROMPT_CONFLICT"),
        }
        entry.curated = null
      }
      continue
    }

    const canonical = [...canonicalCandidates].sort((left, right) => compareQuestionIds(left.raw?.QUESTION_ID, right.raw?.QUESTION_ID))[0]
    for (const entry of group) {
      if (entry === canonical) continue
      entry.decision = {
        ...entry.decision,
        status: entry.curated ? "REJECTED" : entry.decision.status,
        issues: addIssue(entry.decision, "DUPLICATE_PROMPT_NON_CANONICAL"),
      }
      if (entry.curated) entry.curated = null
    }
  }

  return output
}
