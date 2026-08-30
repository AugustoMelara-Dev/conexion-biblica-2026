import type {
  LegacyHistoryEvent,
  Question,
  QuestionProgress,
} from "@/domain/types"

export type MappedLegacyProgress = {
  factId: string
  sourceQuestionKey: string
  progress: QuestionProgress
}

const normalize = (value: unknown) =>
  String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()

function questionKey(question: Question) {
  return `${question.bankId ?? "local"}:${question.id}`
}

function answerText(question: Question) {
  if (question.correctAnswerText) return question.correctAnswerText
  return question.correctAnswer
    .map((id) => question.options.find((option) => option.id === id)?.text ?? id)
    .join("|")
}

export function buildMigrationSignature(parts: {
  work: string
  chapter: number
  reference: string
  answer: string
  sourceText: string
}) {
  return [parts.work, parts.chapter, parts.reference, parts.answer, parts.sourceText]
    .map(normalize)
    .join("|")
}

export function migrationSignature(question: Question) {
  return buildMigrationSignature({
    work: question.source.work,
    chapter: question.source.chapter,
    reference: question.source.reference,
    answer: answerText(question),
    sourceText: question.sourceQuote ?? question.sourceSpan ?? "",
  })
}

export function mapLegacyProgressToFacts(
  legacyQuestions: Question[],
  progress: QuestionProgress[],
  goldQuestions: Question[],
  preservedAt = Date.now(),
): { mapped: MappedLegacyProgress[]; legacy: LegacyHistoryEvent[] } {
  const goldBySignature = new Map<string, Question[]>()
  for (const question of goldQuestions) {
    const key = migrationSignature(question)
    goldBySignature.set(key, [...(goldBySignature.get(key) ?? []), question])
  }
  return mapLegacyProgressFromSignatureIndex(
    legacyQuestions,
    progress,
    new Map(
      [...goldBySignature].map(([key, questions]) => [
        key,
        new Set(
          questions.map((question) => question.factId).filter(Boolean) as string[]
        ),
      ])
    ),
    preservedAt
  )
}

export function mapLegacyProgressFromSignatureIndex(
  legacyQuestions: Question[],
  progress: QuestionProgress[],
  factsBySignature: ReadonlyMap<string, ReadonlySet<string>>,
  preservedAt = Date.now()
): { mapped: MappedLegacyProgress[]; legacy: LegacyHistoryEvent[] } {
  const oldByKey = new Map(legacyQuestions.map((question) => [questionKey(question), question]))
  const mapped: MappedLegacyProgress[] = []
  const legacy: LegacyHistoryEvent[] = []
  for (const item of progress) {
    const question = oldByKey.get(item.questionKey)
    if (!question) {
      legacy.push({ id: `legacy:${item.questionKey}`, sourceQuestionKey: item.questionKey, reason: "missing_question", progress: item, preservedAt })
      continue
    }
    const facts = [...(factsBySignature.get(migrationSignature(question)) ?? [])]
    if (facts.length === 1) mapped.push({ factId: facts[0], sourceQuestionKey: item.questionKey, progress: item })
    else legacy.push({
      id: `legacy:${item.questionKey}`,
      sourceQuestionKey: item.questionKey,
      reason: facts.length ? "ambiguous_match" : "no_match",
      progress: item,
      preservedAt,
    })
  }
  return { mapped, legacy }
}
