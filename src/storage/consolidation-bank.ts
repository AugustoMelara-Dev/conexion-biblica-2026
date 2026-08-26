import type { DifficultyBand, Question, QuestionType, SourceWork } from "@/domain/types"

export type GoldRawQuestion = {
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
  why_each_distractor_fails: Record<string, string>
  source_quote: string
  trap_type: string | null
  blind_final_pool: boolean
  blind_pool: "A" | "B" | "emergency" | null
  validation_status: "gold_audited"
  editorial_status: "gold"
  quality_score: number
  semantic_skill: string
}

export type ConsolidationManifest = {
  schema_version: "5.1"
  profile_id: "consolidation-v5"
  version: string
  gold_questions: number
  gold_facts: number
  shards: Array<{ chapter: string; question_count: number; questions_file: string }>
}

const difficulty: Record<GoldRawQuestion["difficulty"], { value: Question["difficulty"]; band: DifficultyBand }> = {
  easy: { value: 1, band: "BASIC" },
  medium: { value: 2, band: "MEDIUM" },
  hard: { value: 4, band: "HARD" },
  expert: { value: 5, band: "EXPERT" },
}

const chapterNumber = (chapter: string) => Number(chapter.match(/\d+/)?.[0] ?? 0)
const questionType = (type: GoldRawQuestion["type"]): QuestionType => type === "multiple_choice" ? "single_choice" : type

export function adaptGoldQuestion(raw: GoldRawQuestion): Question {
  if (raw.editorial_status !== "gold" || raw.validation_status !== "gold_audited" || raw.quality_score < 85)
    throw new Error(`La pregunta ${raw.id} no cumple la puerta GOLD`)
  const options = raw.options.map((text, index) => ({ id: String.fromCharCode(65 + index), text }))
  if (!options[raw.correct_option]) throw new Error(`Respuesta fuera de rango en ${raw.id}`)
  const work: SourceWork = raw.bank === "DANIEL1-12" ? "Daniel" : "Profetas y Reyes"
  return {
    id: raw.id,
    bankId: "consolidation-v5",
    bankProfileId: "consolidation-v5",
    type: questionType(raw.type),
    difficulty: difficulty[raw.difficulty].value,
    difficultyBand: difficulty[raw.difficulty].band,
    source: {
      work,
      version: work === "Daniel" ? "RVR1995" : "PDF PR39–44",
      chapter: chapterNumber(raw.chapter),
      reference: raw.verse_or_page,
    },
    tags: [raw.topic, raw.semantic_skill],
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
    correctAnswerText: raw.correct_answer,
    acceptedAnswers: raw.accepted_answers,
    answerMode: raw.type === "fill_blank" ? "canonical_text" : "option_id",
    explanation: raw.explanation,
    whyDistractorsFail: raw.why_each_distractor_fails,
    sourceQuote: raw.source_quote,
    trapType: raw.trap_type,
    blindFinalPool: raw.blind_pool !== null,
    blindPool: raw.blind_pool,
    editorialStatus: "gold",
    qualityScore: raw.quality_score,
    semanticSkill: raw.semantic_skill,
    verified: true,
  }
}

function randomGenerator(seed: number) {
  let state = seed >>> 0
  return () => ((state = (Math.imul(state, 1664525) + 1013904223) >>> 0) / 0x100000000)
}

function sample<T>(rows: T[], count: number, seed: number) {
  const result = rows.slice()
  const random = randomGenerator(seed)
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1))
    ;[result[index], result[swap]] = [result[swap], result[index]]
  }
  return result.slice(0, count)
}

export async function readConsolidationManifest(fetcher: typeof fetch = fetch): Promise<ConsolidationManifest> {
  const response = await fetcher("/banks/consolidation-v5/manifest.json")
  if (!response.ok) throw new Error("No se pudo leer el manifiesto GOLD")
  return response.json() as Promise<ConsolidationManifest>
}

export async function loadConsolidationQuestionPool(input: {
  manifest: ConsolidationManifest
  chapters: number[]
  count: number
  seed: number
  blindPool?: "A" | "B" | "emergency"
  difficultyBands?: DifficultyBand[]
  types?: QuestionType[]
  fetcher?: typeof fetch
}): Promise<Question[]> {
  const fetcher = input.fetcher ?? fetch
  const allowed = new Set(input.chapters)
  const shards = input.manifest.shards.filter((shard) => allowed.has(chapterNumber(shard.chapter)))
  const candidates: Question[] = []
  for (const shard of shards) {
    const response = await fetcher(`/${shard.questions_file}`)
    if (!response.ok) throw new Error(`No se pudo leer ${shard.chapter}`)
    const raw = (await response.json()) as GoldRawQuestion[]
    candidates.push(...raw
      .filter((question) => input.blindPool ? question.blind_pool === input.blindPool : question.blind_pool === null)
      .map(adaptGoldQuestion)
      .filter((question) => !input.difficultyBands?.length || (
        question.difficultyBand !== undefined && input.difficultyBands.includes(question.difficultyBand)
      ))
      .filter((question) => !input.types?.length || input.types.includes(question.type)))
  }
  const ordered = sample(candidates, candidates.length, input.seed)
  const usedFacts = new Set<string>()
  return ordered.filter((question) => {
    const fact = question.factId ?? question.factKey
    if (usedFacts.has(fact)) return false
    usedFacts.add(fact)
    return true
  }).slice(0, input.count)
}
