export const CurationStatus = Object.freeze({
  APPROVED: "APPROVED",
  REPAIRED: "REPAIRED",
  REJECTED: "REJECTED",
})

const OPTION_IDS = ["A", "B", "C", "D"]

const repairRules = [
  ["ARTIFICIAL_PROMPT", (q) => /segunda formulación de alto riesgo|según el hecho/i.test(String(q.pregunta ?? ""))],
  ["PROCESS_EXPLANATION", (q) => /pregunta histórica|fase\s*[1-4]|cobertura auditada/i.test(String(q.explicacion ?? ""))],
  ["EDITORIAL_PREFIX", (q) => /^\[Profetas y Reyes\]/i.test(String(q.pregunta ?? ""))],
  ["UNBALANCED_QUOTES", (q) => (String(q.pregunta ?? "").match(/«/g) ?? []).length !== (String(q.pregunta ?? "").match(/»/g) ?? []).length],
  ["SHORT_ANSWER_TYPE", (q) => /RESPUESTA CORTA/i.test(String(q.tipo ?? ""))],
]

const rejectionRules = [
  ["OUT_OF_SCOPE", (q) => q.material === "DANIEL" ? +q.capitulo < 1 || +q.capitulo > 12 : q.material !== "PR" || +q.capitulo < 39 || +q.capitulo > 44],
  ["UNRESOLVED_CORRECTION", (q) => /requiere corrección|respuesta discutible/i.test(String(q.respuesta_correcta ?? ""))],
]

function asText(value) {
  return value == null ? "" : String(value)
}

function stripOptionPrefix(value) {
  return asText(value).trim().replace(/^[A-D]\)\s*/i, "")
}

function comparable(value) {
  return stripOptionPrefix(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es")
    .replace(/[\p{P}\p{S}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim()
}

function visibleOptions(raw) {
  return OPTION_IDS
    .map((id) => ({ id, text: stripOptionPrefix(raw?.[id]) }))
    .filter((option) => option.text.length > 0)
}

function hasDuplicateOptions(raw) {
  const seen = new Set()
  for (const option of visibleOptions(raw)) {
    const value = comparable(option.text)
    if (!value) continue
    if (seen.has(value)) return true
    seen.add(value)
  }
  return false
}

function isUniqueOption(raw, optionId) {
  const option = visibleOptions(raw).find((candidate) => candidate.id === optionId)
  if (!option) return false
  const value = comparable(option.text)
  return Boolean(value) && visibleOptions(raw).filter((candidate) => comparable(candidate.text) === value).length === 1
}

function isTrueFalseType(raw) {
  return /VERDADERO\s*\/\s*FALSO/i.test(asText(raw?.tipo))
}

function resolveTrueFalse(raw) {
  const answer = comparable(raw?.respuesta_correcta)
  if (["verdadero", "true"].includes(answer)) return { mode: "option_id", optionId: "TRUE", text: "Verdadero" }
  if (["falso", "false"].includes(answer)) return { mode: "option_id", optionId: "FALSE", text: "Falso" }
  return null
}

function resolveOption(raw) {
  const match = /^\s*([A-D])\)\s*/i.exec(asText(raw?.respuesta_correcta))
  if (!match) return null
  const optionId = match[1].toUpperCase()
  if (!isUniqueOption(raw, optionId)) return null
  const option = visibleOptions(raw).find((candidate) => candidate.id === optionId)
  return { mode: "option_id", optionId, text: option.text }
}

function resolveCorrectedHistorical(raw) {
  if (asText(raw?.historical_status) !== "CORRECTED") return null
  const match = asText(raw?.respuesta_correcta).match(/forma exacta RVR95 es «([^»]+)»/)
  const text = match?.[1]?.trim()
  return text ? { mode: "canonical_text", text } : null
}

function isShortAnswerType(raw) {
  return /RESPUESTA CORTA|COMPLET/i.test(asText(raw?.tipo))
}

function hasVisibleOptions(raw) {
  return visibleOptions(raw).length > 0
}

function resolveCanonicalShortAnswer(raw) {
  if (!isShortAnswerType(raw) || hasVisibleOptions(raw)) return null
  const text = stripOptionPrefix(raw?.respuesta_correcta)
  return text ? { mode: "canonical_text", text } : null
}

export function resolveMasterAnswer(raw) {
  if (isTrueFalseType(raw)) return resolveTrueFalse(raw)
  if (asText(raw?.historical_status) === "CORRECTED") return resolveCorrectedHistorical(raw)
  const option = resolveOption(raw)
  if (option) return option
  return resolveCanonicalShortAnswer(raw)
}

export function classifyMasterQuestion(raw) {
  const question = raw ?? {}
  const issues = []
  for (const [code, matches] of rejectionRules) if (matches(question)) issues.push(code)
  const answer = resolveMasterAnswer(question)
  if (!answer) issues.push("UNRESOLVED_ANSWER")
  if (hasDuplicateOptions(question)) issues.push("DUPLICATE_OPTIONS")
  if (issues.length) return { status: CurationStatus.REJECTED, issues, answer }
  for (const [code, matches] of repairRules) if (matches(question)) issues.push(code)
  return { status: issues.length ? CurationStatus.REPAIRED : CurationStatus.APPROVED, issues, answer }
}

function nonEmptyValues(value) {
  if (Array.isArray(value)) return value.map(asText).map((item) => item.trim()).filter(Boolean)
  const item = asText(value).trim()
  return item ? [item] : []
}

function uniqueValues(values) {
  return [...new Set(values)]
}

export function curationFamily(raw) {
  const factKeys = uniqueValues([
    ...nonEmptyValues(raw?.FULL_FACT_IDS),
    ...nonEmptyValues(raw?.PARTIAL_FACT_IDS),
    ...nonEmptyValues(raw?.INCIDENTAL_FACT_IDS),
  ])
  const fallback = nonEmptyValues(raw?.duplicate_group)[0] ?? nonEmptyValues(raw?.QUESTION_ID)[0] ?? ""
  return {
    factKey: factKeys[0] ?? fallback,
    factKeys: factKeys.length > 0 ? factKeys : fallback ? [fallback] : [],
  }
}
