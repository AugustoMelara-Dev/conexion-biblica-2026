import { createHash } from "node:crypto"
import { access, mkdir, readFile, rename, rm as rmFile, unlink, writeFile } from "node:fs/promises"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { classifyMasterQuestion, curationFamily, CurationStatus } from "./lib/master-curation.mjs"
import { curateMasterQuestion } from "./lib/curated-question.mjs"

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const TECHNICAL_LANGUAGE = /segunda formulación|fase\s*[1-4]|cobertura auditada|requiere corrección|respuesta discutible/i

function asText(value) {
  return value == null ? "" : String(value)
}

function hashText(value) {
  return createHash("sha256").update(value).digest("hex")
}

export function fingerprintMaster(master) {
  return hashText(JSON.stringify(master))
}

export function fingerprintText(raw) {
  return hashText(raw)
}

function countBy(values) {
  const counts = {}
  for (const value of values) {
    const key = asText(value) || "(sin dato)"
    counts[key] = (counts[key] ?? 0) + 1
  }
  return Object.fromEntries(Object.entries(counts).sort(([left], [right]) => left.localeCompare(right, "es")))
}

function increment(map, key) {
  const normalized = asText(key) || "(sin dato)"
  map[normalized] = (map[normalized] ?? 0) + 1
}

function addIssueCounts(decisions) {
  const counts = {}
  for (const decision of decisions) for (const issue of decision.issues) increment(counts, issue)
  return Object.fromEntries(Object.entries(counts).sort(([left], [right]) => left.localeCompare(right, "es")))
}

function decisionRecord(raw, decision, curated) {
  return {
    masterQuestionId: raw.QUESTION_ID ?? null,
    status: decision.status,
    issues: [...decision.issues],
    originalQuestion: raw.pregunta ?? null,
    curatedQuestion: curated?.question ?? null,
    originalExplanation: raw.explicacion ?? null,
    curatedExplanation: curated?.explanation ?? null,
    originalAnswer: raw.respuesta_correcta ?? null,
    curatedAnswer: curated?.correctAnswerText ?? curated?.correctAnswer ?? null,
    material: raw.material ?? null,
    chapter: Number.isFinite(Number(raw.capitulo)) ? Number(raw.capitulo) : null,
    reference: raw.fuente ?? null,
  }
}

function curationSummary(rawQuestions, decisions) {
  const statuses = new Map(rawQuestions.map((raw, index) => [raw.QUESTION_ID, decisions[index].status]))
  const total = rawQuestions.length
  const approved = rawQuestions.filter((raw) => statuses.get(raw.QUESTION_ID) === CurationStatus.APPROVED).length
  const repaired = rawQuestions.filter((raw) => statuses.get(raw.QUESTION_ID) === CurationStatus.REPAIRED).length
  const rejected = rawQuestions.filter((raw) => statuses.get(raw.QUESTION_ID) === CurationStatus.REJECTED).length
  return { total, approved, repaired, rejected, included: approved + repaired }
}

function createBank(sourceWork, sourceVersion, chapter, description, rawQuestions, decisions, questions) {
  return {
    schemaVersion: "1.0",
    bank: {
      competition: "Conexion Biblica 2026",
      profileId: "curated-v4",
      sourceWork,
      sourceVersion,
      chapter,
      description,
      curationSummary: curationSummary(rawQuestions, decisions),
    },
    questions,
  }
}

function issue(findings, question, code, message) {
  findings.push({
    severity: "blocker",
    code,
    questionId: question?.id ?? question?.metadata?.masterQuestionId ?? null,
    masterQuestionId: question?.metadata?.masterQuestionId ?? null,
    message,
  })
}

function optionText(question, optionId) {
  return question.options?.find((option) => option.id === optionId)?.text ?? ""
}

function quoteDifference(value) {
  return (asText(value).match(/«/gu) ?? []).length - (asText(value).match(/»/gu) ?? []).length
}

function correctAnswerText(question) {
  if (question.correctAnswerText != null) return question.correctAnswerText
  return (question.correctAnswer ?? []).map((answerId) => optionText(question, answerId)).join(" | ")
}

function validateCuratedQuestion(question, raw, expectedWork, findings, seenIds, seenMasterIds) {
  if (!question || typeof question !== "object") {
    issue(findings, question, "MISSING_CURATED_QUESTION", "La decisión aprobada o reparada no produjo una pregunta.")
    return
  }

  if (seenIds.has(question.id)) issue(findings, question, "DUPLICATE_ID", "El identificador V4 aparece más de una vez.")
  seenIds.add(question.id)
  const expectedMasterId = raw?.QUESTION_ID
  if (!expectedMasterId) issue(findings, question, "MISSING_MASTER_ID", "La pregunta maestra no tiene QUESTION_ID.")
  if (seenMasterIds.has(expectedMasterId)) issue(findings, question, "DUPLICATE_MASTER_ID", "El vínculo al Banco Maestro aparece más de una vez.")
  seenMasterIds.add(expectedMasterId)

  const expectedStatus = raw?._curationDecision?.status
  if (![CurationStatus.APPROVED, CurationStatus.REPAIRED].includes(question.metadata?.curationStatus)) issue(findings, question, "INVALID_CURATION_STATUS", "V4 sólo admite estados APPROVED o REPAIRED.")
  if (expectedStatus && question.metadata?.curationStatus !== expectedStatus) issue(findings, question, "STATUS_NOT_TRACEABLE", "El estado V4 no coincide con la clasificación del Banco Maestro.")
  if (question.metadata?.masterQuestionId !== expectedMasterId) issue(findings, question, "MASTER_ID_MISMATCH", "El masterQuestionId no coincide con QUESTION_ID.")
  if (question.source?.work !== expectedWork) issue(findings, question, "SOURCE_WORK_MISMATCH", "La obra declarada no coincide con el material maestro.")
  if (question.source?.reference !== raw?.fuente) issue(findings, question, "REFERENCE_MISMATCH", "La referencia V4 no es idéntica a la del Banco Maestro.")
  if (question.source?.chapter !== Number(raw?.capitulo)) issue(findings, question, "CHAPTER_MISMATCH", "El capítulo V4 no coincide con el Banco Maestro.")
  const expectedVersion = expectedWork === "Daniel" ? "RVR95" : "Material PDF"
  if (question.source?.version !== expectedVersion) issue(findings, question, "SOURCE_VERSION_MISMATCH", "La versión V4 no coincide con la fuente estudiada.")
  if (!question.factKey) issue(findings, question, "MISSING_FACT_KEY", "La pregunta V4 no tiene familia factual.")
  if (!question.question || !question.explanation) issue(findings, question, "MISSING_VISIBLE_TEXT", "La pregunta V4 carece de enunciado o explicación.")
  if (TECHNICAL_LANGUAGE.test(`${question.question} ${question.explanation} ${question.correctAnswerText ?? ""}`)) issue(findings, question, "TECHNICAL_LANGUAGE", "La salida V4 conserva lenguaje de generación, auditoría o corrección pendiente.")

  const visibleTexts = [
    ["enunciado", question.question],
    ["explicación", question.explanation],
    ["memoryCue", question.memoryCue],
    ["respuesta canónica", question.correctAnswerText],
    ...(question.options ?? []).map((option) => [`opción ${option.id}`, option.text]),
  ]
  for (const [label, text] of visibleTexts) if (quoteDifference(text) !== 0) issue(findings, question, "UNBALANCED_VISIBLE_TEXT", `El texto visible (${label}) tiene comillas desbalanceadas.`)
  if (quoteDifference(`${question.question} ${correctAnswerText(question)}`) !== 0) issue(findings, question, "UNBALANCED_QUESTION_ANSWER", "La composición pregunta-respuesta tiene comillas desbalanceadas.")

  const optionIds = new Set()
  for (const option of question.options ?? []) {
    if (!option?.id || optionIds.has(option.id)) issue(findings, question, "DUPLICATE_OPTION_ID", "Las opciones V4 tienen identificadores repetidos o vacíos.")
    optionIds.add(option?.id)
  }
  const answerIds = question.correctAnswer ?? []
  if (!answerIds.length || answerIds.some((answerId) => !optionIds.has(answerId))) issue(findings, question, "INVALID_CORRECT_OPTION", "La respuesta V4 no se puede resolver entre sus opciones.")
  if (question.answerMode === "canonical_text" && (!question.correctAnswerText || !optionText(question, "ANSWER"))) issue(findings, question, "MISSING_CANONICAL_ANSWER", "La respuesta canónica V4 no tiene texto resoluble.")
  if (!question.verified) issue(findings, question, "NOT_VERIFIED", "La salida V4 no está marcada como verificada.")
}

function sourceMatchesMaterial(raw) {
  const chapter = Number(raw.capitulo)
  const source = asText(raw.fuente)
  if (raw.material === "DANIEL") return new RegExp(`\\bDaniel\\s+${chapter}\\b`, "iu").test(source)
  if (raw.material === "PR") return new RegExp(`(?:\\bPR${chapter}\\b|cap[ií]tulo\\s+${chapter}\\b)`, "iu").test(source)
  return false
}

function visibleQuoteRepairRequired(raw, decision) {
  const optionTexts = [raw.A, raw.B, raw.C, raw.D]
  const canonicalText = decision.answer?.mode === "canonical_text" ? decision.answer.text : null
  return [...optionTexts, canonicalText, raw.fact_support].some((text) => quoteDifference(text) !== 0)
}

function classifyForBuild(raw) {
  const decision = classifyMasterQuestion(raw)
  const additionalIssues = []
  const repairIssues = visibleQuoteRepairRequired(raw, decision) ? ["VISIBLE_TEXT_QUOTES"] : []
  const required = ["QUESTION_ID", "material", "capitulo", "pregunta", "respuesta_correcta", "fuente"]
  if (required.some((field) => raw?.[field] == null || (typeof raw[field] === "string" && !raw[field].trim()))) additionalIssues.push("MISSING_REQUIRED_FIELD")
  if (!curationFamily(raw).factKey) additionalIssues.push("MISSING_FACT_FAMILY")
  if (raw.material !== "DANIEL" && raw.material !== "PR") additionalIssues.push("SOURCE_MATERIAL_MISMATCH")
  else if (!sourceMatchesMaterial(raw)) additionalIssues.push("SOURCE_CHAPTER_MISMATCH")
  if (!additionalIssues.length && !repairIssues.length) return decision
  if (!additionalIssues.length) {
    return {
      ...decision,
      status: decision.status === CurationStatus.APPROVED ? CurationStatus.REPAIRED : decision.status,
      issues: [...new Set([...decision.issues, ...repairIssues])],
    }
  }
  return {
    status: CurationStatus.REJECTED,
    issues: [...new Set([...decision.issues, ...repairIssues, ...additionalIssues])],
    answer: decision.answer,
  }
}

function expectedQuestions(master) {
  return master.questions.map((raw) => {
    const initialDecision = classifyForBuild(raw)
    const curated = curateMasterQuestion(raw, initialDecision)
    if (initialDecision.status !== CurationStatus.REJECTED && !curated) {
      return {
        raw,
        decision: {
          status: CurationStatus.REJECTED,
          issues: [...new Set([...initialDecision.issues, "UNSAFE_VISIBLE_TEXT"])],
          answer: initialDecision.answer,
        },
        curated: null,
      }
    }
    return { raw, decision: initialDecision, curated }
  })
}

/**
 * Re-cross a pair of generated banks with the immutable master. The optional
 * expectedBanks argument is used by audit:v4 to detect stale or edited files.
 */
export function auditCuratedV4(banks, master, expectedBanks = null) {
  const findings = []
  const sourceBanks = [
    ["daniel", banks?.daniel, "Daniel", "RVR95"],
    ["prophets", banks?.prophets, "Profetas y Reyes", "Material PDF"],
  ]
  const expected = expectedQuestions(master)
  const expectedById = new Map(expected.filter(({ curated }) => curated).map(({ raw, curated }) => [curated.id, { raw, curated }]))
  const expectedIncludedIds = new Set(expectedById.keys())
  const actualById = new Map()
  const seenIds = new Set()
  const seenMasterIds = new Set()

  for (const [bankKey, bank, expectedWork, expectedVersion] of sourceBanks) {
    if (!bank) {
      issue(findings, null, "MISSING_BANK", `No existe el banco V4 ${bankKey}.`)
      continue
    }
    if (bank.schemaVersion !== "1.0") issue(findings, null, "SCHEMA_VERSION_MISMATCH", `El banco ${bankKey} no usa schemaVersion 1.0.`)
    if (bank.bank?.profileId !== "curated-v4") issue(findings, null, "PROFILE_MISMATCH", `El banco ${bankKey} no declara profileId curated-v4.`)
    if (bank.bank?.sourceWork !== expectedWork || bank.bank?.sourceVersion !== expectedVersion) issue(findings, null, "BANK_SOURCE_MISMATCH", `La metadata de ${bankKey} no coincide con la fuente.`)
    for (const question of bank.questions ?? []) {
      const masterQuestion = master.questions.find((raw) => raw.QUESTION_ID === question.metadata?.masterQuestionId)
      if (!masterQuestion) {
        issue(findings, question, "MASTER_NOT_FOUND", "No se encontró el masterQuestionId en el Banco Maestro.")
        continue
      }
      const classified = expected.find(({ raw }) => raw.QUESTION_ID === masterQuestion.QUESTION_ID)
      if (!classified?.curated) issue(findings, question, "REJECTED_INCLUDED", "Una pregunta REJECTED fue incluida en V4.")
      const enrichedRaw = { ...masterQuestion, _curationDecision: classified?.decision }
      validateCuratedQuestion(question, enrichedRaw, expectedWork, findings, seenIds, seenMasterIds)
      actualById.set(question.id, question)
      const expectedQuestion = expectedById.get(question.id)?.curated
      if (!expectedQuestion) issue(findings, question, "UNEXPECTED_QUESTION", "El banco V4 contiene una pregunta que la política no produce.")
      else if (JSON.stringify(question) !== JSON.stringify(expectedQuestion)) issue(findings, question, "BANK_CONTENT_MISMATCH", "El contenido V4 no coincide con la adaptación reproducible del maestro.")
    }
  }

  for (const expectedId of expectedIncludedIds) if (!actualById.has(expectedId)) issue(findings, null, "MISSING_QUESTION", `Falta en V4 la pregunta esperada ${expectedId}.`)
  if (expectedBanks) {
    const expectedActualIds = Object.values(expectedBanks).flatMap((bank) => bank.questions ?? []).map((question) => question.id)
    if (expectedActualIds.length !== expectedIncludedIds.size) issue(findings, null, "EXPECTED_BANK_COUNT_MISMATCH", "La cantidad esperada de preguntas V4 no coincide con la política.")
  }

  return {
    summary: { blockers: findings.length },
    findings,
  }
}

function distributions(entries) {
  return {
    bySource: countBy(entries.map(({ raw }) => raw.material === "DANIEL" ? "Daniel" : raw.material === "PR" ? "Profetas y Reyes" : raw.material)),
    byChapter: countBy(entries.map(({ raw }) => `${raw.material}:${raw.capitulo}`)),
    byType: countBy(entries.map(({ raw }) => raw.tipo)),
    byDifficulty: countBy(entries.map(({ raw }) => raw.dificultad)),
  }
}

export function buildCuratedV4(master, { generatedAt = new Date().toISOString(), masterFingerprint = fingerprintMaster(master) } = {}) {
  if (!master || !Array.isArray(master.questions)) throw new Error("El Banco Maestro debe contener un arreglo questions.")
  const entries = expectedQuestions(master)
  const decisions = entries.map(({ raw, decision, curated }) => decisionRecord(raw, decision, curated))
  const danielEntries = entries.filter(({ raw }) => raw.material === "DANIEL")
  const prophetsEntries = entries.filter(({ raw }) => raw.material === "PR")
  const daniel = danielEntries.filter(({ curated }) => curated).map(({ curated }) => curated)
  const prophets = prophetsEntries.filter(({ curated }) => curated).map(({ curated }) => curated)
  const counts = {
    total: entries.length,
    approved: entries.filter(({ decision }) => decision.status === CurationStatus.APPROVED).length,
    repaired: entries.filter(({ decision }) => decision.status === CurationStatus.REPAIRED).length,
    rejected: entries.filter(({ decision }) => decision.status === CurationStatus.REJECTED).length,
    blockers: 0,
  }
  if (counts.approved + counts.repaired + counts.rejected !== counts.total) throw new Error("La suma de estados de curación no coincide con el total maestro.")

  const banks = {
    daniel: createBank("Daniel", "RVR95", "1-12", "Banco V4 curado por clasificación y reparación trazable", danielEntries.map(({ raw }) => raw), danielEntries.map(({ decision }) => decision), daniel),
    prophets: createBank("Profetas y Reyes", "Material PDF", "39-44", "Banco V4 curado por clasificación y reparación trazable", prophetsEntries.map(({ raw }) => raw), prophetsEntries.map(({ decision }) => decision), prophets),
  }
  const audit = {
    generatedAt,
    masterFingerprint,
    summary: counts,
    countsByIssue: addIssueCounts(decisions),
    distribution: distributions(entries),
    decisions,
    findings: [],
  }
  const crossAudit = auditCuratedV4(banks, master)
  audit.summary.blockers = crossAudit.summary.blockers
  audit.findings = crossAudit.findings
  if (crossAudit.summary.blockers > 0) {
    const details = crossAudit.findings.map((finding) => `${finding.code}: ${finding.message}`).join(" | ")
    throw new Error(`La auditoría V4 encontró ${crossAudit.summary.blockers} bloqueadores: ${details}`)
  }
  return { banks, audit }
}

function markdownValue(value) {
  return asText(value).replace(/\r?\n/gu, " ").replace(/\|/gu, "\\|").trim() || "(sin dato)"
}

export function renderAuditMarkdown(audit) {
  const lines = [
    "# Auditoría del Banco Curado V4",
    "",
    `Generado: ${audit.generatedAt}`,
    `Huella SHA-256 del Banco Maestro: \`${audit.masterFingerprint}\``,
    "",
    "## Resumen",
    "",
    `- Total analizado: ${audit.summary.total}`,
    `- APPROVED: ${audit.summary.approved}`,
    `- REPAIRED: ${audit.summary.repaired}`,
    `- REJECTED: ${audit.summary.rejected}`,
    `- Bloqueadores: ${audit.summary.blockers}`,
    "",
    "## Conteo por código",
    "",
    "| Código | Preguntas |",
    "| --- | ---: |",
  ]
  for (const [code, count] of Object.entries(audit.countsByIssue)) lines.push(`| ${markdownValue(code)} | ${count} |`)
  if (!Object.keys(audit.countsByIssue).length) lines.push("| Ninguno | 0 |")
  for (const [title, values] of [["Fuente", audit.distribution?.bySource], ["Capítulo", audit.distribution?.byChapter], ["Tipo", audit.distribution?.byType], ["Dificultad", audit.distribution?.byDifficulty]]) {
    lines.push("", `## Distribución por ${title.toLocaleLowerCase("es")}`, "", "| Valor | Preguntas |", "| --- | ---: |")
    for (const [value, count] of Object.entries(values ?? {})) lines.push(`| ${markdownValue(value)} | ${count} |`)
  }

  const rejected = audit.decisions.filter((decision) => decision.status === CurationStatus.REJECTED)
  lines.push("", "## Rechazos completos", "")
  if (!rejected.length) lines.push("Ninguno.")
  for (const decision of rejected) {
    lines.push(`### ${markdownValue(decision.masterQuestionId)} · ${markdownValue(decision.issues.join(", "))}`, "", `- Fuente: ${markdownValue(decision.reference)}`, `- Capítulo: ${markdownValue(decision.chapter)}`, `- Pregunta original: ${markdownValue(decision.originalQuestion)}`, `- Respuesta original: ${markdownValue(decision.originalAnswer)}`, "")
  }

  const repairsByCode = new Map()
  for (const decision of audit.decisions.filter((item) => item.status === CurationStatus.REPAIRED)) {
    for (const code of decision.issues) {
      const sample = repairsByCode.get(code) ?? []
      if (sample.length < 20) sample.push(decision)
      repairsByCode.set(code, sample)
    }
  }
  lines.push("## Muestra de reparaciones (máximo 20 por código)", "")
  if (!repairsByCode.size) lines.push("Ninguna.")
  for (const [code, sample] of [...repairsByCode.entries()].sort(([left], [right]) => left.localeCompare(right, "es"))) {
    lines.push(`### ${markdownValue(code)}`, "", "| ID | Original | Curada |", "| --- | --- | --- |")
    for (const decision of sample) lines.push(`| ${markdownValue(decision.masterQuestionId)} | ${markdownValue(decision.originalQuestion)} | ${markdownValue(decision.curatedQuestion)} |`)
    lines.push("")
  }
  if (audit.findings?.length) {
    lines.push("## Bloqueadores de auditoría", "")
    for (const finding of audit.findings) lines.push(`- **${markdownValue(finding.code)}** — ${markdownValue(finding.message)}`)
  }
  return `${lines.join("\n").trimEnd()}\n`
}

async function pathExists(path) {
  try {
    await access(path)
    return true
  } catch {
    return false
  }
}

async function removeIfExists(path, unlinkOperation = unlink, rmOperation = rmFile) {
  try {
    await unlinkOperation(path)
  } catch (error) {
    if (error?.code === "ENOENT") return
    await rmOperation(path, { force: true })
  }
}

async function cleanup(paths, operations = {}) {
  const unlinkOperation = operations.unlink ?? unlink
  const rmOperation = operations.rm ?? rmFile
  const errors = []
  for (const path of paths) {
    try {
      await removeIfExists(path, unlinkOperation, rmOperation)
    } catch (error) {
      errors.push({ path, error })
    }
  }
  return errors
}

export class AtomicCommitCleanupError extends Error {
  constructor({ targets, remainingBackups, cleanupErrors }) {
    super(`Los payloads nuevos quedaron instalados, pero la limpieza permanente de respaldos falló; se conservan ${remainingBackups.length} copias de recuperación.`)
    this.name = "AtomicCommitCleanupError"
    this.committed = true
    this.targets = [...targets]
    this.remainingBackups = [...remainingBackups]
    this.cleanupErrors = cleanupErrors.map(({ path, error }) => ({ path, code: error?.code ?? null, message: error?.message ?? String(error) }))
    this.cause = cleanupErrors[0]?.error
  }
}

/**
 * Stage every payload before moving an existing destination. If any rename
 * fails, newly installed files are removed and all moved originals are put
 * back. Temp and backup paths are generated only for the supplied targets.
 */
export async function writePayloadsAtomically(payloads, { fsOps = {} } = {}) {
  if (!Array.isArray(payloads) || payloads.length === 0) throw new Error("Se requiere al menos un payload para escritura atómica.")
  const targets = new Set()
  const nonce = `${process.pid}-${Date.now()}`
  const prepared = payloads.map(({ target, value }) => {
    if (!target || targets.has(target)) throw new Error(`Destino duplicado o vacío: ${target}`)
    targets.add(target)
    const content = typeof value === "string" ? value : `${JSON.stringify(value, null, 2)}\n`
    if (!content) throw new Error(`Payload vacío para ${target}`)
    return { target, content, temp: `${target}.tmp`, backup: `${target}.bak-${nonce}`, backedUp: false, installed: false }
  })
  const tempPaths = prepared.map(({ temp }) => temp)
  const backupPaths = prepared.map(({ backup }) => backup)
  const operations = {
    mkdir: fsOps.mkdir ?? mkdir,
    writeFile: fsOps.writeFile ?? writeFile,
    rename: fsOps.rename ?? rename,
    unlink: fsOps.unlink ?? unlink,
    rm: fsOps.rm ?? rmFile,
  }

  try {
    for (const { target, content, temp } of prepared) {
      await operations.mkdir(dirname(target), { recursive: true })
      await operations.writeFile(temp, content, "utf8")
    }
    try {
      for (const item of prepared) {
        if (await pathExists(item.target)) {
          await operations.rename(item.target, item.backup)
          item.backedUp = true
        }
      }
      for (const item of prepared) {
        await operations.rename(item.temp, item.target)
        item.installed = true
      }
    } catch (error) {
      const rollbackErrors = []
      for (const item of [...prepared].reverse()) {
        if (item.installed) {
          try {
            await removeIfExists(item.target, operations.unlink, operations.rm)
          } catch (rollbackError) {
            rollbackErrors.push(rollbackError)
          }
        }
      }
      for (const item of [...prepared].reverse()) {
        if (item.backedUp && await pathExists(item.backup)) {
          try {
            await operations.rename(item.backup, item.target)
            item.backedUp = false
          } catch (rollbackError) {
            rollbackErrors.push(rollbackError)
          }
        }
      }
      const cleanupErrors = await cleanup(tempPaths, operations)
      if (rollbackErrors.length || cleanupErrors.length) {
        throw new Error(`Fallo de escritura atómica y rollback incompleto: ${error.message}; incidencias=${rollbackErrors.length + cleanupErrors.length}`)
      }
      throw error
    }
    const backupCleanupErrors = await cleanup(backupPaths, operations)
    if (backupCleanupErrors.length) {
      const remainingBackups = []
      for (const backup of backupPaths) if (await pathExists(backup)) remainingBackups.push(backup)
      if (remainingBackups.length) {
        throw new AtomicCommitCleanupError({
          targets: prepared.map(({ target }) => target),
          remainingBackups,
          cleanupErrors: backupCleanupErrors,
        })
      }
    }
  } catch (error) {
    await cleanup(tempPaths, operations)
    throw error
  }
}

function payloadsForResult(result) {
  return [
    { target: resolve(ROOT, "public/banks/v4_daniel.json"), value: result.banks.daniel },
    { target: resolve(ROOT, "public/banks/v4_profetas_reyes.json"), value: result.banks.prophets },
    { target: resolve(ROOT, "reports/curated-v4-audit.json"), value: result.audit },
    { target: resolve(ROOT, "reports/curated-v4-audit.md"), value: renderAuditMarkdown(result.audit) },
  ]
}

export async function generateCuratedV4Files({ root = ROOT } = {}) {
  const masterPath = resolve(root, "Banco_Maestro_CB2026.json")
  const rawMaster = await readFile(masterPath, "utf8")
  const master = JSON.parse(rawMaster)
  const result = buildCuratedV4(master, { masterFingerprint: fingerprintText(rawMaster) })
  const payloads = payloadsForResult(result).map((payload) => ({ ...payload, target: payload.target.replace(ROOT, root) }))
  await writePayloadsAtomically(payloads)
  return result
}

async function main() {
  const result = await generateCuratedV4Files()
  console.log(JSON.stringify(result.audit.summary, null, 2))
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error.stack ?? error.message)
    process.exitCode = 1
  })
}
