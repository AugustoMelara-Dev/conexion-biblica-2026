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

function signature(question: Question) {
  return [
    question.source.work,
    question.source.chapter,
    question.source.reference,
    answerText(question),
    question.sourceQuote ?? question.sourceSpan ?? "",
  ]
    .map(normalize)
    .join("|")
}

export function mapLegacyProgressToFacts(
  legacyQuestions: Question[],
  progress: QuestionProgress[],
  goldQuestions: Question[],
  preservedAt = Date.now(),
): { mapped: MappedLegacyProgress[]; legacy: LegacyHistoryEvent[] } {
  const oldByKey = new Map(legacyQuestions.map((question) => [questionKey(question), question]))
  const goldBySignature = new Map<string, Question[]>()
  for (const question of goldQuestions) {
    const key = signature(question)
    goldBySignature.set(key, [...(goldBySignature.get(key) ?? []), question])
  }
  const mapped: MappedLegacyProgress[] = []
  const legacy: LegacyHistoryEvent[] = []
  for (const item of progress) {
    const question = oldByKey.get(item.questionKey)
    if (!question) {
      legacy.push({ id: `legacy:${item.questionKey}`, sourceQuestionKey: item.questionKey, reason: "missing_question", progress: item, preservedAt })
      continue
    }
    const matches = goldBySignature.get(signature(question)) ?? []
    const facts = [...new Set(matches.map((match) => match.factId).filter(Boolean))] as string[]
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
