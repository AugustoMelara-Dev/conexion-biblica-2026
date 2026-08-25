import { curationFamily } from "./master-curation.mjs"
import { naturalizePrompt, repairVisibleText } from "./editorial.mjs"

const OPTION_IDS = ["A", "B", "C", "D"]

function asText(value) {
  return value == null ? "" : String(value)
}

function stripOptionPrefix(value) {
  return asText(value).trim().replace(/^[A-D]\)\s*/iu, "").replace(/\s+/gu, " ")
}

function normalizedType(raw, answer) {
  if (answer?.mode === "canonical_text") return "reference_detail"
  const type = asText(raw?.tipo).replace(/\s+/gu, " ").trim().toLocaleUpperCase("es")
  if (type.startsWith("VERDADERO")) return "true_false"
  return "single_choice"
}

function normalizedDifficulty(value) {
  if (typeof value === "number" && value >= 1 && value <= 5) return value
  const difficulty = asText(value).trim().toLocaleUpperCase("es")
  if (difficulty === "EXPERT") return 5
  if (difficulty === "HARD") return 4
  return 3
}

function visibleOptions(raw, answer, canonicalText) {
  if (answer?.mode === "canonical_text") return canonicalText == null ? null : [{ id: "ANSWER", text: canonicalText }]
  if (answer?.optionId === "TRUE" || answer?.optionId === "FALSE") {
    return [{ id: "TRUE", text: "Verdadero" }, { id: "FALSE", text: "Falso" }]
  }
  const options = OPTION_IDS
    .map((id) => ({ id, text: stripOptionPrefix(raw?.[id]) }))
    .filter((option) => option.text.length > 0)
  const repaired = []
  for (const option of options) {
    const text = repairVisibleText(option.text)
    if (text == null) return null
    repaired.push({ ...option, text })
  }
  return repaired
}

function trimFactSupport(value) {
  return asText(value).replace(/[.。]+$/gu, "").trim()
}

export function repairPrompt(prompt) {
  return repairVisibleText(naturalizePrompt(prompt))
}

export function repairExplanation(raw) {
  const source = asText(raw?.fuente).trim()
  const factSupport = asText(raw?.fact_support).trim()
  const explanation = asText(raw?.explicacion).replace(/\s+/gu, " ").trim()
  if (/pregunta histórica|fase\s*[1-4]|cobertura auditada/iu.test(explanation)) return `La respuesta se confirma en ${source}.`
  if (factSupport) return `Dato verificado en ${source}: ${trimFactSupport(factSupport)}.`
  return explanation || `La respuesta se confirma en ${source}.`
}

export function curateMasterQuestion(raw, decision) {
  if (!decision || decision.status === "REJECTED" || !decision.answer) return null
  const { factKey, factKeys } = curationFamily(raw)
  const answer = decision.answer
  const work = raw.material === "DANIEL" ? "Daniel" : "Profetas y Reyes"
  const question = repairPrompt(raw.pregunta)
  const canonicalText = answer.mode === "canonical_text" ? repairVisibleText(answer.text) : null
  const options = visibleOptions(raw, answer, canonicalText)
  const explanation = repairVisibleText(repairExplanation(raw))
  const memoryCue = repairVisibleText(`Ancla ${raw.fuente}: ${String(raw.fact_support || canonicalText || answer.text).replace(/[.。]+$/gu, "")}.`)
  if (question == null || options == null || explanation == null || memoryCue == null || (answer.mode === "canonical_text" && canonicalText == null)) return null
  return {
    id: `V4-${raw.QUESTION_ID}`,
    type: normalizedType(raw, answer),
    difficulty: normalizedDifficulty(raw.dificultad),
    source: { work, version: work === "Daniel" ? "RVR95" : "Material PDF", chapter: Number(raw.capitulo), reference: raw.fuente },
    tags: ["v4", raw.habilidad, raw.riesgo_objetivo].filter(Boolean),
    factKey,
    factKeys,
    question,
    options,
    correctAnswer: answer.mode === "option_id" ? [answer.optionId] : ["ANSWER"],
    ...(answer.mode === "canonical_text" ? { answerMode: "canonical_text", correctAnswerText: canonicalText } : {}),
    explanation,
    memoryCue,
    verified: true,
    metadata: {
      masterQuestionId: raw.QUESTION_ID,
      curationStatus: decision.status,
      curationIssues: decision.issues,
      originalDifficulty: raw.dificultad,
      originalType: raw.tipo,
      duplicateGroup: raw.duplicate_group,
      qc: raw.estado_QC,
      historicalStatus: raw.historical_status,
    },
  }
}
