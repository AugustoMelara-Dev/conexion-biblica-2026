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

export type IndexedHumanReviewEntry = HumanReviewEntry & {
  questions_file: string
}

export type HumanReviewIndex = {
  bank_questions: number
  entries: IndexedHumanReviewEntry[]
}

export type HumanReviewQuestion = {
  id: string
  family?: string
  chapter?: string
  reference?: string
  question: string
  options: string[]
  correct_answer: string
  source_quote: string
  why_distractors_fail: Record<string, string>
}

const REVIEW_UNIT_SOURCE = "(?:DAN(?:[1-9]|1[0-2])|PR(?:39|4[0-4]))"
const CHAPTER_PATTERN = new RegExp(`^${REVIEW_UNIT_SOURCE}$`)
const SCHEMA_10_QUESTION_ID_PATTERN = new RegExp(
  `^(?:(?:Q|PV)-)?${REVIEW_UNIT_SOURCE}-[A-Z0-9]+(?:-[A-Z0-9]+)*(?:::PRESENTATION-[0-9]+)?$`
)
const SCHEMA_10_QUESTION_CHAPTER_PATTERN = new RegExp(
  `^(?:(?:Q|PV)-)?(${REVIEW_UNIT_SOURCE})-`
)
const QUESTIONS_FILE_PATTERN = new RegExp(
  `^banks/final-2026/questions/${REVIEW_UNIT_SOURCE}\\.json$`
)

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}

function asString(value: unknown) {
  return typeof value === "string" ? value : ""
}

function asStringArray(value: unknown) {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : []
}

function chapterFromQuestionId(questionId: string) {
  if (!SCHEMA_10_QUESTION_ID_PATTERN.test(questionId)) return ""
  return questionId.match(SCHEMA_10_QUESTION_CHAPTER_PATTERN)?.[1] ?? ""
}

function invalidIndex(message: string): never {
  throw new Error(`Índice editorial inválido: ${message}`)
}

function parseQuestionsFile(value: unknown, chapter: string) {
  const questionsFile = asString(value)
  if (questionsFile) {
    if (!QUESTIONS_FILE_PATTERN.test(questionsFile))
      invalidIndex("questions_file no es compatible.")
    if (!questionsFile.endsWith(`/${chapter}.json`))
      invalidIndex("questions_file no coincide con el capítulo.")
    return questionsFile
  }
  return `banks/final-2026/questions/${chapter}.json`
}

export function parseHumanReviewIndex(payload: unknown): HumanReviewIndex {
  if (!isRecord(payload)) invalidIndex("el documento no es un objeto.")
  const source = payload
  const schemaVersion = source.schema_version
  const isSchema10 = schemaVersion === "10.0"
  if (schemaVersion !== undefined && !isSchema10)
    invalidIndex("esquema no compatible.")
  if (!Array.isArray(source.entries))
    invalidIndex("entries debe ser un arreglo.")
  const rawEntries = source.entries
  const declaredTotal = isSchema10
    ? source.total_reviewed
    : (source.bank_questions ?? rawEntries.length)
  if (
    !Number.isInteger(declaredTotal) ||
    (declaredTotal as number) < 0 ||
    declaredTotal !== rawEntries.length
  )
    invalidIndex(
      isSchema10
        ? "total_reviewed no coincide con entries."
        : "bank_questions no coincide con entries."
    )

  const entries = rawEntries.map((raw, entryIndex): IndexedHumanReviewEntry => {
    if (!isRecord(raw))
      invalidIndex(`entrada ${entryIndex + 1} no es un objeto.`)
    let id: string
    let chapter: string
    if (isSchema10) {
      id = asString(raw.question_id)
      if (!id)
        invalidIndex(`entrada ${entryIndex + 1} no contiene question_id.`)
      if (raw.id !== undefined && asString(raw.id) !== id)
        invalidIndex(
          `entrada ${entryIndex + 1}: id no coincide con question_id.`
        )
      chapter = chapterFromQuestionId(id)
      if (raw.chapter !== undefined && asString(raw.chapter) !== chapter)
        invalidIndex(
          `entrada ${entryIndex + 1}: chapter no coincide con question_id.`
        )
    } else {
      id = asString(raw.id)
      chapter = asString(raw.chapter)
    }
    const contentSha256 = asString(raw.content_sha256)
    if (!id || !contentSha256 || !CHAPTER_PATTERN.test(chapter))
      invalidIndex(`entrada ${entryIndex + 1} incompleta.`)
    if (isSchema10) {
      if (!SCHEMA_10_QUESTION_ID_PATTERN.test(id))
        invalidIndex(`entrada ${entryIndex + 1} tiene question_id inválido.`)
      if (!["passed", "requires_attention"].includes(asString(raw.decision)))
        invalidIndex(`entrada ${entryIndex + 1} tiene decision inválida.`)
    }
    const questionsFile = parseQuestionsFile(raw.questions_file, chapter)

    const riskScore =
      typeof raw.risk_score === "number" && Number.isFinite(raw.risk_score)
        ? raw.risk_score
        : 0
    if (
      raw.risk_score !== undefined &&
      (typeof raw.risk_score !== "number" || !Number.isFinite(raw.risk_score))
    )
      invalidIndex(`entrada ${entryIndex + 1} tiene risk_score inválido.`)
    if (
      raw.automatic_flags !== undefined &&
      (!Array.isArray(raw.automatic_flags) ||
        raw.automatic_flags.some((flag) => typeof flag !== "string"))
    )
      invalidIndex(`entrada ${entryIndex + 1} tiene automatic_flags inválidos.`)
    if (
      raw.automatic_status !== undefined &&
      raw.automatic_status !== "passed" &&
      raw.automatic_status !== "requires_attention"
    )
      invalidIndex(`entrada ${entryIndex + 1} tiene automatic_status inválido.`)

    return {
      id,
      fact_id: asString(raw.fact_id),
      chapter,
      family: asString(raw.family),
      reference: asString(raw.reference),
      content_sha256: contentSha256,
      risk_score: riskScore,
      automatic_flags: asStringArray(raw.automatic_flags),
      automatic_status:
        raw.automatic_status === "requires_attention" ||
        raw.decision === "requires_attention"
          ? "requires_attention"
          : "passed",
      questions_file: questionsFile,
    }
  })
  return { bank_questions: declaredTotal as number, entries }
}

export function parseHumanReviewQuestionShard(
  payload: unknown,
  expectedChapter?: string
): HumanReviewQuestion[] {
  if (expectedChapter !== undefined && !CHAPTER_PATTERN.test(expectedChapter))
    throw new Error("Capítulo editorial inválido: unidad solicitada inválida.")
  if (!Array.isArray(payload))
    throw new Error("Capítulo editorial inválido: debe ser un arreglo.")
  return payload.map((raw, questionIndex) => {
    const label = `pregunta ${questionIndex + 1}`
    if (!isRecord(raw))
      throw new Error(`Capítulo editorial inválido: ${label} no es un objeto.`)
    const id = asString(raw.id)
    const question = asString(raw.question)
    const correctAnswer = asString(raw.correct_answer)
    const sourceQuote = asString(raw.source_quote)
    const options = raw.options
    const optionalText = (field: "family" | "chapter" | "reference") => {
      if (!(field in raw)) return undefined
      const value = raw[field]
      if (typeof value !== "string" || !value.trim())
        throw new Error(
          `Capítulo editorial inválido: ${label} tiene ${field} inválido.`
        )
      return value
    }
    const family = optionalText("family")
    const chapter = optionalText("chapter")
    const reference = optionalText("reference")
    if (chapter && expectedChapter && chapter !== expectedChapter)
      throw new Error(
        `Capítulo editorial inválido: ${label} no coincide con la unidad solicitada.`
      )
    if (
      !id ||
      !question ||
      !sourceQuote ||
      !Array.isArray(options) ||
      options.length < 2 ||
      options.some((option) => typeof option !== "string" || !option.trim()) ||
      new Set(options).size !== options.length ||
      !correctAnswer ||
      !options.includes(correctAnswer)
    )
      throw new Error(`Capítulo editorial inválido: ${label} está incompleta.`)
    const whyDistractorsFail = raw.why_distractors_fail
    if (
      whyDistractorsFail !== undefined &&
      (!isRecord(whyDistractorsFail) ||
        Array.isArray(whyDistractorsFail) ||
        Object.values(whyDistractorsFail).some(
          (explanation) => typeof explanation !== "string"
        ))
    )
      throw new Error(
        `Capítulo editorial inválido: ${label} tiene distractores inválidos.`
      )
    return {
      id,
      family,
      chapter,
      reference,
      question,
      options,
      correct_answer: correctAnswer,
      source_quote: sourceQuote,
      why_distractors_fail: isRecord(whyDistractorsFail)
        ? (whyDistractorsFail as Record<string, string>)
        : {},
    }
  })
}

export function reconcileHumanReview(
  entries: HumanReviewEntry[],
  decisions: HumanReviewDecision[]
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
  }
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
  filters: { family?: string; chapter?: string }
) {
  const decisionsById = new Map(decisions.map((item) => [item.id, item]))
  const reviewed = new Set(
    entries.flatMap((entry) =>
      decisionsById.get(entry.id)?.content_sha256 === entry.content_sha256
        ? [entry.id]
        : []
    )
  )
  return entries
    .filter(
      (entry) =>
        !reviewed.has(entry.id) &&
        (!filters.family || entry.family === filters.family) &&
        (!filters.chapter || entry.chapter === filters.chapter)
    )
    .sort(
      (left, right) =>
        (Number.isFinite(right.risk_score) ? right.risk_score : 0) -
          (Number.isFinite(left.risk_score) ? left.risk_score : 0) ||
        String(left.id ?? "").localeCompare(String(right.id ?? ""))
    )[0]
}
