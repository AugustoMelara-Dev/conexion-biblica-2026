const artificialPrefix = "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? "

export function naturalizePrompt(prompt) {
  const value = String(prompt ?? "").trim()
  if (!value.startsWith(artificialPrefix)) return value
  let clause = value.slice(artificialPrefix.length).trim()
  if (clause.startsWith("«") && clause.endsWith("».")) clause = clause.slice(1, -2)
  else if (clause.startsWith("«") && clause.endsWith("»")) clause = clause.slice(1, -1)
  const openingQuotes = (clause.match(/«/g) ?? []).length
  const closingQuotes = (clause.match(/»/g) ?? []).length
  if (openingQuotes === 0 && closingQuotes > 0) clause = clause.replaceAll("»", "")
  if (closingQuotes === 0 && openingQuotes > 0) clause = clause.replaceAll("«", "")
  return `Completa la afirmación: ${clause}${/[.!?]$/.test(clause) ? "" : "."}`
}
