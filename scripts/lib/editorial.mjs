const artificialPrefix = "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? "

function quoteCount(value, quote) {
  return (value.match(new RegExp(quote, "g")) ?? []).length
}

function splitTrailingPunctuation(value) {
  const match = /([.!?…]+)$/u.exec(value)
  if (!match) return { body: value, punctuation: "" }
  return { body: value.slice(0, -match[1].length), punctuation: match[1] }
}

function balanceOrphanOuterQuotes(value) {
  let { body, punctuation } = splitTrailingPunctuation(value)
  let openings = quoteCount(body, "«")
  let closings = quoteCount(body, "»")

  while (openings > closings) {
    const orphanIndex = body.indexOf("«")
    if (orphanIndex < 0) break
    body = `${body.slice(0, orphanIndex)}${body.slice(orphanIndex + 1)}`
    openings -= 1
  }
  while (body.endsWith("»") && closings > openings) {
    body = body.slice(0, -1).trimEnd()
    closings -= 1
  }

  return `${body}${punctuation}`
}

function unwrapArtificialClause(value) {
  let { body, punctuation } = splitTrailingPunctuation(value)
  const openings = quoteCount(body, "«")
  const closings = quoteCount(body, "»")
  if (body.startsWith("«")) {
    body = body.slice(1).trimStart()
    if (openings === closings && body.endsWith("»")) body = body.slice(0, -1).trimEnd()
  }
  return balanceOrphanOuterQuotes(`${body}${punctuation}`)
}

export function naturalizePrompt(prompt) {
  let value = String(prompt ?? "").replace(/\s+/gu, " ").trim()
  value = value.replace(/^\[Profetas y Reyes\]\s*/iu, "")
  if (!value.startsWith(artificialPrefix)) return balanceOrphanOuterQuotes(value)
  const clause = unwrapArtificialClause(value.slice(artificialPrefix.length).trim())
  return `Completa la afirmación: ${clause}${/[.!?…]$/u.test(clause) ? "" : "."}`
}
