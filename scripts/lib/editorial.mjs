function quoteCount(value, quote) {
  return (value.match(new RegExp(quote, "g")) ?? []).length
}

/**
 * Remove exactly one unmatched Spanish quote when its repair is mechanical.
 * Adding a quote could change a source fragment, so inputs with more than one
 * unmatched mark are left for the curation policy to reject.
 */
export function repairVisibleText(value) {
  const normalized = String(value ?? "").replace(/\s+/gu, " ").trim()
  const openings = []
  const unmatchedClosings = []
  for (let index = 0; index < normalized.length; index += 1) {
    if (normalized[index] === "«") openings.push(index)
    if (normalized[index] === "»") {
      if (openings.length) openings.pop()
      else unmatchedClosings.push(index)
    }
  }
  if (openings.length === 0 && unmatchedClosings.length === 0) return normalized
  if (openings.length + unmatchedClosings.length !== 1) return null
  const removeAt = openings[0] ?? unmatchedClosings[0]
  return `${normalized.slice(0, removeAt)}${normalized.slice(removeAt + 1)}`.replace(/\s+/gu, " ").trim()
}

function splitTrailingPunctuation(value) {
  const match = /([.!?…;]+)$/u.exec(value)
  if (!match) return { body: value, punctuation: "" }
  return { body: value.slice(0, -match[1].length), punctuation: match[1] }
}

function wrapperStart(value) {
  if (value.startsWith("«")) return 0
  const marker = /:\s*«/u.exec(value)
  if (marker && value.slice(0, marker.index).includes("«")) return -1
  if (!marker || !/(?:completa|afirmación|enunciado)/iu.test(value.slice(0, marker.index))) return -1
  return marker.index + marker[0].length - 1
}

function matchingOuterClose(value) {
  let depth = 0
  for (let index = 0; index < value.length; index += 1) {
    if (value[index] === "«") depth += 1
    if (value[index] !== "»") continue
    if (depth === 0) return -1
    depth -= 1
    if (depth === 0) return index
  }
  return -1
}

function normalizeWrapperQuotes(value, { unwrap = false, allowOrphanOpening = false } = {}) {
  let { body, punctuation } = splitTrailingPunctuation(value)
  const start = wrapperStart(body)
  if (start < 0) return value

  let prefix = body.slice(0, start)
  let quoted = body.slice(start)
  let openings = quoteCount(quoted, "«")
  let closings = quoteCount(quoted, "»")
  let removedOrphanOpening = false

  if (!quoted.endsWith("»") && !(allowOrphanOpening && openings === 1 && closings === 0)) return value

  if (closings > openings) {
    const extras = closings - openings
    for (let count = 0; count < extras; count += 1) quoted = quoted.slice(0, -1).trimEnd()
    closings = openings
  }

  if (openings > closings) {
    const remainder = quoted.slice(1)
    if (quoteCount(remainder, "«") !== quoteCount(remainder, "»")) return value
    quoted = remainder
    openings -= 1
    removedOrphanOpening = true
  }

  if (!removedOrphanOpening && unwrap && openings === closings && matchingOuterClose(quoted) === quoted.length - 1) {
    quoted = quoted.slice(1, -1).trim()
  }

  prefix = prefix.trimEnd()
  return `${prefix}${prefix ? " " : ""}${quoted}${punctuation}`
}

function balanceOrphanOuterQuotes(value) {
  return normalizeWrapperQuotes(value)
}

function unwrapArtificialClause(value) {
  return normalizeWrapperQuotes(value, { unwrap: true, allowOrphanOpening: true })
}

export function naturalizePrompt(prompt) {
  let value = String(prompt ?? "").replace(/\s+/gu, " ").trim()
  value = value.replace(/^\[Profetas y Reyes\]\s*/iu, "")
  const artificial = /^¿Qué dato completa correctamente (?:esta segunda formulación de alto riesgo|según el hecho)\?\s*/iu.exec(value)
  if (!artificial) return balanceOrphanOuterQuotes(value)
  const clause = unwrapArtificialClause(value.slice(artificial[0].length).trim())
  return `Completa la afirmación: ${clause}${/[.!?…]$/u.test(clause) ? "" : "."}`
}
