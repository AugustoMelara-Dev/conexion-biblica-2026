import { selectMandatoryRound } from "@/domain/final-mission-selection"
import { buildMigrationSignature } from "@/storage/history-migration"
import {
  FINAL_BANK_ID,
  FINAL_BANK_DISPLAY_NAME,
  FINAL_BANK_SCHEMA_VERSION,
} from "@/domain/final-bank"
import type {
  DifficultyBand,
  FinalQuestionFamily,
  Question,
  QuestionExposure,
  QuestionType,
  SourceWork,
} from "@/domain/types"

export type FinalRawQuestion = {
  id: string
  bank_id: typeof FINAL_BANK_ID
  bank_name: typeof FINAL_BANK_DISPLAY_NAME
  schema_version: typeof FINAL_BANK_SCHEMA_VERSION | "9.0"
  source_unit_id: string
  fact_id: string
  variant_id: string
  template_id: string
  family: FinalQuestionFamily
  subtype?: string
  chapter: string
  reference: string
  source_ref: string
  verse_or_page: string
  source_span: string
  source_quote: string
  context_anchor: string
  topic: string
  importance: string
  relation_type: string
  option_category: string
  blind_pool: "A" | "B" | "emergency" | null
  question: string
  options: string[]
  correct_option: number
  correct_answer: string
  accepted_answers: string[]
  answer_mode: "option_id"
  explanation: string
  why_distractors_fail: Record<string, string>
  trap_type: string | null
  final_editorial_status: "GOLD"
  difficulty: "easy" | "medium" | "hard" | "expert"
  evidence_excerpt?: string
  false_mutation?: {
    changed_fields: string[]
    local: boolean
    original: string
    replacement: string
  } | null
  ai_review?: {
    status: "passed"
    reviewer_type: "ai_semantic_audit"
    reviewer: string
  }
  validation_adversarial?: {
    reviewer: string
    status: "passed"
    selected_option: number
    rationale: string
    second_defensible_option: boolean
  }
}

export type FinalBankManifest = {
  schema_version: typeof FINAL_BANK_SCHEMA_VERSION | "9.0"
  bank_id: typeof FINAL_BANK_ID
  display_name: typeof FINAL_BANK_DISPLAY_NAME
  build_id?: string
  artifact_revision?: string
  gold_questions: number
  unique_facts: number
  shards: Array<{
    chapter: string
    question_count: number
    training_question_count?: number
    questions_file: string
    sha256?: string
  }>
}

export async function finalManifestFingerprint(manifest: FinalBankManifest) {
  const declaredRevision = manifest.artifact_revision ?? manifest.build_id
  if (declaredRevision)
    return `${manifest.bank_id}:${manifest.schema_version}:build:${declaredRevision}`
  const descriptors = manifest.shards
    .map((shard) => ({
      chapter: shard.chapter,
      questionCount: shard.question_count,
      trainingQuestionCount: shard.training_question_count ?? null,
      questionsFile: shard.questions_file,
      sha256: shard.sha256 ?? null,
    }))
    .sort((left, right) =>
      `${left.chapter}:${left.questionsFile}`.localeCompare(
        `${right.chapter}:${right.questionsFile}`
      )
    )
  const bytes = new TextEncoder().encode(
    JSON.stringify({
      bankId: manifest.bank_id,
      schemaVersion: manifest.schema_version,
      goldQuestions: manifest.gold_questions,
      uniqueFacts: manifest.unique_facts,
      descriptors,
    })
  )
  const digest = await crypto.subtle.digest("SHA-256", bytes)
  return `${manifest.bank_id}:${manifest.schema_version}:sha256:${[
    ...new Uint8Array(digest),
  ]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("")}`
}

const difficulty: Record<
  FinalRawQuestion["difficulty"],
  { value: Question["difficulty"]; band: DifficultyBand }
> = {
  easy: { value: 1, band: "BASIC" },
  medium: { value: 2, band: "MEDIUM" },
  hard: { value: 4, band: "HARD" },
  expert: { value: 5, band: "EXPERT" },
}

const chapterNumber = (chapter: string) =>
  Number(chapter.match(/\d+/)?.[0] ?? 0)

function typeForFamily(family: FinalQuestionFamily): QuestionType {
  if (family === "true_false") return "true_false"
  if (family === "fill_choice") return "fill_blank"
  return "single_choice"
}

function semanticSkill(raw: FinalRawQuestion) {
  if (raw.subtype) return raw.subtype
  if (raw.family === "single_choice_contextual") return "scene_identification"
  if (/cause|consequence/.test(raw.relation_type)) return "cause_consequence"
  if (/comparison|difference/.test(raw.relation_type)) return "comparison"
  if (/sequence|order/.test(raw.relation_type)) return "narrative_order"
  if (raw.family === "true_false") return "detail_discrimination"
  if (raw.family === "fill_choice") return "text_recall"
  return "contextual_precision"
}

function rawMigrationSignature(raw: FinalRawQuestion) {
  return buildMigrationSignature({
    work: raw.chapter.startsWith("DAN") ? "Daniel" : "Profetas y Reyes",
    chapter: chapterNumber(raw.chapter),
    reference: raw.reference,
    answer: raw.correct_answer,
    sourceText: raw.source_quote ?? raw.source_span,
  })
}

function isCanonicalFinalRaw(raw: FinalRawQuestion) {
  return (
    raw.bank_id === FINAL_BANK_ID &&
    (raw.schema_version === FINAL_BANK_SCHEMA_VERSION ||
      raw.schema_version === "9.0") &&
    raw.final_editorial_status === "GOLD" &&
    (!raw.validation_adversarial ||
      (raw.validation_adversarial.status === "passed" &&
        !raw.validation_adversarial.second_defensible_option)) &&
    (!raw.ai_review || raw.ai_review.status === "passed") &&
    raw.correct_option >= 0 &&
    raw.correct_option < raw.options.length
  )
}

export async function resolveFinalMigrationSignatures(input: {
  manifest: FinalBankManifest
  signatures: ReadonlySet<string>
  fetcher?: typeof fetch
}) {
  const matches = new Map<string, Set<string>>()
  if (input.signatures.size === 0) return matches
  const fetcher = input.fetcher ?? fetch
  for (const shard of input.manifest.shards) {
    const response = await fetcher(`/${shard.questions_file}`)
    if (!response.ok) throw new Error(`No se pudo leer ${shard.chapter}`)
    const rows = (await response.json()) as FinalRawQuestion[]
    for (const row of rows) {
      if (!isCanonicalFinalRaw(row)) continue
      const signature = rawMigrationSignature(row)
      if (!input.signatures.has(signature)) continue
      const facts = matches.get(signature) ?? new Set<string>()
      facts.add(row.fact_id)
      matches.set(signature, facts)
    }
  }
  return matches
}

export function adaptFinalQuestion(raw: FinalRawQuestion): Question {
  if (!isCanonicalFinalRaw(raw))
    throw new Error(`La pregunta ${raw.id} no cumple las puertas canónicas`)
  const options = raw.options.map((text, index) => ({
    id: String.fromCharCode(65 + index),
    text,
  }))
  const work: SourceWork = raw.chapter.startsWith("DAN")
    ? "Daniel"
    : "Profetas y Reyes"
  const level = difficulty[raw.difficulty]
  return {
    id: raw.id,
    bankId: FINAL_BANK_ID,
    bankProfileId: "final-v7",
    type: typeForFamily(raw.family),
    family: raw.family,
    difficulty: level.value,
    difficultyBand: level.band,
    originalDifficulty: raw.difficulty,
    source: {
      work,
      version: work === "Daniel" ? "RVR1995" : "PDF PR39–44",
      chapter: chapterNumber(raw.chapter),
      reference: raw.reference,
    },
    tags: [raw.topic, raw.importance, raw.option_category],
    factKey: raw.fact_id,
    factKeys: [raw.fact_id],
    factId: raw.fact_id,
    variantId: raw.variant_id,
    templateId: raw.template_id,
    verseOrPage: raw.verse_or_page,
    sourceSpan: raw.source_span,
    sourceQuote: raw.source_quote,
    contextAnchor: raw.context_anchor,
    question: raw.question,
    options,
    correctAnswer: [options[raw.correct_option].id],
    correctAnswerText: raw.correct_answer,
    acceptedAnswers: raw.accepted_answers,
    answerMode: "option_id",
    explanation: raw.explanation,
    whyDistractorsFail: raw.why_distractors_fail,
    trapType:
      raw.family === "single_choice_contextual"
        ? "true_elsewhere"
        : raw.trap_type,
    trapReason:
      raw.family === "single_choice_contextual"
        ? "Los distractores proceden de contextos distintos de la fuente."
        : undefined,
    blindFinalPool: raw.blind_pool !== null,
    blindPool: raw.blind_pool,
    editorialStatus: "gold",
    qualityScore: 100,
    semanticSkill: semanticSkill(raw),
    verified: true,
    metadata: {
      sourceUnitId: raw.source_unit_id,
      relationType: raw.relation_type,
      validationReviewer:
        raw.validation_adversarial?.reviewer ?? raw.ai_review?.reviewer,
      evidenceExcerpt: raw.evidence_excerpt,
      aiReviewer: raw.ai_review?.reviewer,
      aiReviewerType: raw.ai_review?.reviewer_type,
      falseMutation: raw.false_mutation,
    },
  }
}

function randomGenerator(seed: number) {
  let state = seed >>> 0
  return () =>
    (state = (Math.imul(state, 1664525) + 1013904223) >>> 0) / 0x100000000
}

function shuffle<T>(rows: T[], seed: number) {
  const result = rows.slice()
  const random = randomGenerator(seed)
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1))
    ;[result[index], result[swap]] = [result[swap], result[index]]
  }
  return result
}

export async function readFinalManifest(
  fetcher: typeof fetch = fetch
): Promise<FinalBankManifest> {
  const response = await fetcher("/banks/final-2026/manifest.json")
  if (!response.ok) throw new Error("No se pudo leer el banco maestro único")
  const manifest = (await response.json()) as FinalBankManifest
  if (
    manifest.bank_id !== FINAL_BANK_ID ||
    (manifest.schema_version !== FINAL_BANK_SCHEMA_VERSION &&
      manifest.schema_version !== "9.0")
  )
    throw new Error("El manifiesto del banco único no es compatible")
  return manifest
}

export async function loadFinalQuestionPool(input: {
  manifest: FinalBankManifest
  chapters: number[]
  count: number
  seed: number
  blindPool?: "A" | "B" | "emergency"
  difficultyBands?: DifficultyBand[]
  types?: QuestionType[]
  family?: FinalQuestionFamily
  seenFactIds?: Set<string>
  exposures?: QuestionExposure[]
  factFilter?: (factId: string) => boolean
  preferredMigrationSignatures?: ReadonlySet<string>
  fetcher?: typeof fetch
}) {
  const fetcher = input.fetcher ?? fetch
  const allowed = new Set(input.chapters)
  const shards = input.manifest.shards.filter((shard) =>
    allowed.has(chapterNumber(shard.chapter))
  )
  const candidates: Question[] = []
  const retryCandidates: Question[] = []
  const shardRows = await Promise.all(
    shards.map(async (shard) => {
      const response = await fetcher(`/${shard.questions_file}`)
      if (!response.ok) throw new Error(`No se pudo leer ${shard.chapter}`)
      return (await response.json()) as FinalRawQuestion[]
    })
  )
  if (input.factFilter || input.preferredMigrationSignatures?.size) {
    const rawCandidates = shardRows
      .flat()
      .filter((row) =>
        input.blindPool
          ? row.blind_pool === input.blindPool
          : row.blind_pool === null
      )
      .filter(
        (row) =>
          input.preferredMigrationSignatures?.has(rawMigrationSignature(row)) ||
          !input.factFilter ||
          input.factFilter(row.fact_id)
      )
      .filter((row) => {
        const level = difficulty[row.difficulty]
        return (
          (!input.difficultyBands?.length ||
            input.difficultyBands.includes(level.band)) &&
          (!input.family || row.family === input.family) &&
          (!input.types?.length ||
            input.types.includes(typeForFamily(row.family)))
        )
      })
    const shuffledCandidates = shuffle(rawCandidates, input.seed)
    const preferred = input.preferredMigrationSignatures
      ? shuffledCandidates.filter((row) =>
          input.preferredMigrationSignatures?.has(rawMigrationSignature(row))
        )
      : []
    const preferredIds = new Set(preferred.map((row) => row.id))
    const seenFacts = new Set<string>()
    const selectedRows = [
      ...preferred,
      ...shuffledCandidates.filter((row) => !preferredIds.has(row.id)),
    ]
      .filter((row) => {
        if (seenFacts.has(row.fact_id)) return false
        seenFacts.add(row.fact_id)
        return true
      })
      .slice(0, input.count)
    const selectedFacts = new Set(selectedRows.map((row) => row.fact_id))
    const selected = selectedRows.map(adaptFinalQuestion)
    const retryRows = shardRows
      .flat()
      .filter((row) => selectedFacts.has(row.fact_id))
      .filter((row) =>
        input.blindPool
          ? row.blind_pool === input.blindPool
          : row.blind_pool === null
      )
      .map(adaptFinalQuestion)
    return attachRetryVariants(selected, retryRows)
  }
  for (const rows of shardRows) {
    const eligibleRows = rows
      .filter((row) =>
        input.blindPool
          ? row.blind_pool === input.blindPool
          : row.blind_pool === null
      )
      .filter((row) => !input.factFilter || input.factFilter(row.fact_id))
      .map(adaptFinalQuestion)
      .filter(
        (question) =>
          !input.difficultyBands?.length ||
          (question.difficultyBand !== undefined &&
            input.difficultyBands.includes(question.difficultyBand))
      )
    retryCandidates.push(...eligibleRows)
    candidates.push(
      ...eligibleRows
        .filter((question) => !input.family || question.family === input.family)
        .filter(
          (question) =>
            !input.types?.length || input.types.includes(question.type)
        )
    )
  }
  const ordered = shuffle(candidates, input.seed)
  const seenFactIds = new Set(input.seenFactIds ?? [])
  const exposureByFact = new Map<
    string,
    { correct: number; incorrect: number; totalMs: number; attempts: number }
  >()
  for (const exposure of input.exposures ?? []) {
    seenFactIds.add(exposure.factId)
    const summary = exposureByFact.get(exposure.factId) ?? {
      correct: 0,
      incorrect: 0,
      totalMs: 0,
      attempts: 0,
    }
    summary.correct += exposure.correct
    summary.incorrect += exposure.incorrect
    summary.totalMs += exposure.totalResponseTimeMs
    summary.attempts += exposure.exposures
    exposureByFact.set(exposure.factId, summary)
  }
  const priorityByFact = new Map<string, number>()
  for (const question of ordered) {
    const fact = question.factId ?? question.factKey
    const exposure = exposureByFact.get(fact)
    const failed = Boolean(
      exposure &&
      exposure.incorrect > 0 &&
      exposure.incorrect >= exposure.correct
    )
    const slow = Boolean(
      exposure &&
      exposure.attempts > 0 &&
      exposure.totalMs / exposure.attempts > 6_000
    )
    priorityByFact.set(
      fact,
      failed ? 400 : slow ? 300 : seenFactIds.has(fact) ? 0 : 200
    )
  }
  const prioritized = ordered
    .slice()
    .sort(
      (left, right) =>
        (priorityByFact.get(right.factId ?? right.factKey) ?? 0) -
        (priorityByFact.get(left.factId ?? left.factKey) ?? 0)
    )
  const supportsMandatoryMix =
    !input.types?.length ||
    (["fill_blank", "true_false", "single_choice"] as QuestionType[]).every(
      (type) => input.types?.includes(type)
    )
  if (
    (input.count === 20 || input.count === 50 || input.count === 100) &&
    supportsMandatoryMix &&
    !input.family
  ) {
    const selected = selectMandatoryRound(
      ordered,
      input.count,
      input.seed,
      new Set<string>(),
      priorityByFact
    )
    return attachRetryVariants(selected, retryCandidates)
  }
  const facts = new Set<string>()
  return attachRetryVariants(
    prioritized
      .filter((question) => {
        const fact = question.factId ?? question.factKey
        if (facts.has(fact)) return false
        facts.add(fact)
        return true
      })
      .slice(0, input.count),
    retryCandidates
  )
}

function attachRetryVariants(selected: Question[], candidates: Question[]) {
  const byFact = new Map<string, Question[]>()
  for (const question of candidates) {
    const fact = question.factId ?? question.factKey
    const rows = byFact.get(fact) ?? []
    rows.push(question)
    byFact.set(fact, rows)
  }
  return selected.map((question) => {
    const fact = question.factId ?? question.factKey
    const alternatives = (byFact.get(fact) ?? []).filter(
      (candidate) =>
        candidate.id !== question.id && candidate.family !== question.family
    )
    return {
      ...question,
      metadata: {
        ...question.metadata,
        retryVariants: alternatives.slice(0, 3),
      },
    }
  })
}
