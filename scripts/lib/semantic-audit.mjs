import { naturalizePrompt } from "./editorial.mjs"

function normalize(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/^\s*[a-d]\)\s*/, "").replace(/[^a-z0-9]+/g, " ").trim()
}

function correctText(question) {
  if (question.answerMode === "canonical_text") return question.correctAnswerText ?? ""
  return (question.options ?? []).filter((option) => question.correctAnswer?.includes(option.id)).map((option) => option.text).join(" | ")
}

export function auditQuestions(questions, masterQuestions) {
  const findings = []
  const masterById = new Map(masterQuestions.map((question) => [question.QUESTION_ID, question]))
  const ids = new Set()
  const add = (question, severity, code, message) => findings.push({ questionId: question.id, factKey: question.factKey ?? null, severity, code, message, source: question.source?.reference ?? null })

  for (const question of questions) {
    if (ids.has(question.id)) add(question, "blocker", "DUPLICATE_ID", "El identificador aparece más de una vez.")
    ids.add(question.id)
    if (!question.factKey) add(question, "blocker", "MISSING_FACT_KEY", "La pregunta no tiene factKey.")
    if (!question.verified) add(question, "review", "NOT_MARKED_VERIFIED", "La pregunta no está marcada como verificada.")
    const version = String(question.source?.version ?? "")
    const validVersion = question.source?.work === "Daniel" ? version.includes("RVR95") : /Material PDF|Profetas y Reyes/i.test(version)
    if (!validVersion) add(question, "blocker", "SOURCE_VERSION_MISMATCH", "La versión declarada no coincide con la fuente estudiada.")
    if (String(question.question ?? "").trim().length < 12) add(question, "review", "PROMPT_TOO_SHORT", "El enunciado es demasiado corto para ser inequívoco.")
    if (String(question.question ?? "").length > 320) add(question, "review", "PROMPT_TOO_LONG", "El enunciado puede ser demasiado lento bajo presión.")
    if (/formulaci[oó]n|alto riesgo|verificaci[oó]n|seg[uú]n el hecho/i.test(question.question ?? "")) add(question, "review", "GENERATION_LANGUAGE", "El enunciado contiene lenguaje de generación o auditoría.")
    if (/pregunta hist[oó]rica|fase\s*[1234]|cobertura auditada/i.test(question.explanation ?? "")) add(question, "review", "GENERIC_EXPLANATION", "La explicación describe el proceso y no enseña el contenido.")

    const optionIds = new Set((question.options ?? []).map((option) => option.id))
    for (const answer of question.correctAnswer ?? []) if (!optionIds.has(answer)) add(question, "blocker", "INVALID_CORRECT_OPTION", `La respuesta ${answer} no existe entre las opciones.`)
    const normalizedOptions = (question.options ?? []).map((option) => normalize(option.text)).filter(Boolean)
    if (new Set(normalizedOptions).size !== normalizedOptions.length) add(question, "blocker", "DUPLICATE_OPTION_TEXT", "Hay opciones equivalentes después de normalizar.")
    const masterId = question.metadata?.masterQuestionId
    if (!masterId) {
      if (!question.integrative) add(question, "blocker", "MISSING_MASTER_ID", "No existe trazabilidad al Banco Maestro.")
      continue
    }
    const master = masterById.get(masterId)
    if (!master) {
      add(question, "blocker", "MASTER_NOT_FOUND", `No se encontró ${masterId} en el Banco Maestro.`)
      continue
    }
    const expectedMaterial = question.source?.work === "Daniel" ? "DANIEL" : "PR"
    if (master.material !== expectedMaterial) add(question, "blocker", "MASTER_SOURCE_MISMATCH", `El maestro declara ${master.material}, pero V3 declara ${expectedMaterial}.`)
    if (Number(master.capitulo) !== Number(question.source?.chapter)) add(question, "blocker", "MASTER_CHAPTER_MISMATCH", `El maestro está en el capítulo ${master.capitulo} y V3 en ${question.source?.chapter}.`)
    if (normalize(question.question) !== normalize(naturalizePrompt(master.pregunta))) add(question, "blocker", "PROMPT_NOT_TRACEABLE", "El enunciado no coincide con la versión editorial trazable del Banco Maestro.")
    const v3Answer = normalize(correctText(question))
    const masterAnswer = normalize(master.respuesta_correcta)
    const correctedMatch = String(master.respuesta_correcta ?? "").match(/forma exacta RVR95 es [«\"]([^»\"]+)/i)
    const expectedCorrection = normalize(correctedMatch?.[1])
    if (master.historical_status === "CORRECTED" && expectedCorrection && v3Answer !== expectedCorrection) add(question, "blocker", "MASTER_CORRECTION_NOT_APPLIED", `La corrección maestra exige «${correctedMatch[1]}», pero V3 conserva otra forma.`)
    else if (v3Answer && masterAnswer && v3Answer !== masterAnswer && !v3Answer.includes(masterAnswer) && !masterAnswer.includes(v3Answer)) add(question, "review", "ANSWER_NOT_TRACEABLE", "La respuesta V3 no coincide textualmente con la respuesta del maestro; requiere revisión semántica.")
    if (!String(master.estado_QC ?? "").includes("PASS") && !["VERIFIED_CORRECT", "CORRECTED"].includes(master.historical_status)) add(question, "review", "MASTER_QC_UNCLEAR", `Estado de control maestro: ${master.estado_QC ?? "sin estado"}.`)
  }

  const counts = (severity) => findings.filter((finding) => finding.severity === severity).length
  const suspiciousQuestions = new Set(findings.map((finding) => finding.questionId)).size
  return {
    generatedAt: new Date().toISOString(),
    summary: { questions: questions.length, traced: questions.filter((question) => question.metadata?.masterQuestionId).length, integrative: questions.filter((question) => question.integrative).length, suspiciousQuestions, blockers: counts("blocker"), reviews: counts("review"), warnings: counts("warning") },
    findings,
  }
}
