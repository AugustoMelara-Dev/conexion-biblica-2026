import type {
  DifficultyBand,
  Question,
  QuestionType,
  SourceWork,
} from "@/domain/types"

export type MassiveBankShard = {
  chapter: string
  bank: "DANIEL1-12" | "PR39-44"
  question_count: number
  fact_count: number
  questions_file: string
  facts_file: string
  questions_sha256: string
  facts_sha256: string
  bytes: number
}

export type MassiveBankManifest = {
  schema_version: "5.0"
  profile_id: "massive-v5"
  totals: {
    questions: number
    facts: number
    templates: number
    distractors: number
  }
  shards: MassiveBankShard[]
  source?: { file: string; sha256: string; pages: number }
  banks?: Record<string, unknown>
  templates_file?: string
  distractors_file?: string
}

export type MassiveRawQuestion = {
  id: string
  fact_id: string
  variant_id: string
  template_id: string
  bank: "DANIEL1-12" | "PR39-44"
  chapter: string
  verse_or_page: string
  source_span: string
  type: "true_false" | "fill_blank" | "multiple_choice"
  difficulty: "easy" | "medium" | "hard" | "expert"
  topic: string
  context_anchor: string
  question: string
  options: string[]
  correct_option: number
  correct_answer: string
  accepted_answers: string[]
  answer_mode: string
  explanation: string
  why_distractors_fail: Record<string, string>
  source_quote: string
  trap_type: string | null
  blind_final_pool: boolean
  validation_status: "verified"
  incorrect_detail?: string | null
  correction?: string | null
}

const DIFFICULTY: Record<
  MassiveRawQuestion["difficulty"],
  { numeric: Question["difficulty"]; band: DifficultyBand }
> = {
  easy: { numeric: 1, band: "BASIC" },
  medium: { numeric: 2, band: "MEDIUM" },
  hard: { numeric: 4, band: "HARD" },
  expert: { numeric: 5, band: "EXPERT" },
}

function chapterNumber(chapter: string) {
  const match = chapter.match(/\d+/)
  if (!match) throw new Error(`Capítulo masivo inválido: ${chapter}`)
  return Number(match[0])
}

function questionType(type: MassiveRawQuestion["type"]): QuestionType {
  return type === "multiple_choice" ? "single_choice" : type
}

export function adaptMassiveQuestion(raw: MassiveRawQuestion): Question {
  if (raw.validation_status !== "verified")
    throw new Error(`La pregunta ${raw.id} no está verificada`)
  if (raw.correct_option < 0 || raw.correct_option >= raw.options.length)
    throw new Error(`Respuesta fuera de rango en ${raw.id}`)
  const chapter = chapterNumber(raw.chapter)
  const sourceWork: SourceWork =
    raw.bank === "DANIEL1-12" ? "Daniel" : "Profetas y Reyes"
  const options = raw.options.map((text, index) => ({
    id: String.fromCharCode(65 + index),
    text,
  }))
  const difficulty = DIFFICULTY[raw.difficulty]
  return {
    id: raw.id,
    bankId: "massive-v5",
    bankProfileId: "massive-v5",
    type: questionType(raw.type),
    difficulty: difficulty.numeric,
    difficultyBand: difficulty.band,
    originalDifficulty: raw.difficulty,
    source: {
      work: sourceWork,
      version: sourceWork === "Daniel" ? "RVR1995" : "PDF PR39–44",
      chapter,
      reference: raw.verse_or_page,
    },
    tags: [raw.topic, raw.trap_type ?? "directa"],
    factKey: raw.fact_id,
    factKeys: [raw.fact_id],
    factId: raw.fact_id,
    variantId: raw.variant_id,
    templateId: raw.template_id,
    verseOrPage: raw.verse_or_page,
    sourceSpan: raw.source_span,
    contextAnchor: raw.context_anchor,
    question: raw.question,
    options,
    correctAnswer: [options[raw.correct_option].id],
    answerMode: "option_id",
    correctAnswerText: raw.correct_answer,
    acceptedAnswers: raw.accepted_answers,
    explanation: raw.explanation,
    whyDistractorsFail: raw.why_distractors_fail,
    sourceQuote: raw.source_quote,
    trapType: raw.trap_type,
    trapReason:
      raw.trap_type === "true_elsewhere"
        ? "Los distractores son datos verdaderos en otro contexto del PDF."
        : undefined,
    blindFinalPool: raw.blind_final_pool,
    verified: true,
    metadata: {
      bank: raw.bank,
      chapter: raw.chapter,
      answerMode: raw.answer_mode,
      incorrectDetail: raw.incorrect_detail ?? null,
      correction: raw.correction ?? null,
    },
  }
}

function seededRandom(seed: number) {
  let state = seed >>> 0
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0
    return state / 0x100000000
  }
}

function sample<T>(items: T[], count: number, random: () => number) {
  if (items.length <= count) return items
  const reservoir = items.slice(0, count)
  for (let index = count; index < items.length; index += 1) {
    const replacement = Math.floor(random() * (index + 1))
    if (replacement < count) reservoir[replacement] = items[index]
  }
  return reservoir
}

export async function readMassiveManifest(
  fetcher: typeof fetch = fetch
): Promise<MassiveBankManifest> {
  const response = await fetcher("/banks/massive-v5/manifest.json")
  if (!response.ok) throw new Error("No se pudo leer el manifiesto masivo")
  return (await response.json()) as MassiveBankManifest
}

export async function loadMassiveQuestionPool({
  manifest,
  chapters,
  count,
  includeBlind,
  fetcher = fetch,
  seed,
  types,
  difficultyBands,
  contextualOnly = false,
  blindOnly = false,
  sequenceOnly = false,
}: {
  manifest: MassiveBankManifest
  chapters: number[]
  count: number
  includeBlind: boolean
  fetcher?: typeof fetch
  seed: number
  types?: QuestionType[]
  difficultyBands?: DifficultyBand[]
  contextualOnly?: boolean
  blindOnly?: boolean
  sequenceOnly?: boolean
}): Promise<Question[]> {
  const allowed = new Set(chapters)
  const shards = manifest.shards.filter((shard) =>
    allowed.has(chapterNumber(shard.chapter))
  )
  if (shards.length === 0 || count <= 0) return []
  const random = seededRandom(seed)
  const candidateLimit = Math.max(count, count * 4)
  const perShardLimit = Math.max(1, Math.ceil(candidateLimit / shards.length))
  const candidates: Question[] = []
  for (const shard of shards) {
    const response = await fetcher(`/${shard.questions_file}`)
    if (!response.ok) throw new Error(`No se pudo leer ${shard.chapter}`)
    const raw = (await response.json()) as MassiveRawQuestion[]
    const eligible = raw
      .filter((question) => (blindOnly ? question.blind_final_pool : includeBlind || !question.blind_final_pool))
      .map(adaptMassiveQuestion)
      .filter(
        (question) =>
          (!types?.length || types.includes(question.type)) &&
          (!difficultyBands?.length ||
            (question.difficultyBand !== undefined &&
              difficultyBands.includes(question.difficultyBand))) &&
          (!contextualOnly || question.trapType === "true_elsewhere")
          && (!sequenceOnly || question.trapType === "order_sequence")
      )
    candidates.push(...sample(eligible, perShardLimit, random))
  }
  return sample(candidates, candidateLimit, random)
}
