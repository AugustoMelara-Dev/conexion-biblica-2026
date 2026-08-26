import type { BankProfileId, BankSelection, DifficultyBand, Question, QuestionReport, Session } from "@/domain/types"

export type BankDefinition = {
  id: BankProfileId
  label: string
  description: string
  readOnly: boolean
  version: string
  expectedQuestionCount?: number
}

export const BANK_DEFINITIONS: Record<BankProfileId, BankDefinition> = {
  "legacy-v1": {
    id: "legacy-v1",
    label: "V1 — Clásica",
    description: "Tu banco original",
    readOnly: false,
    version: "1",
  },
  "master-v2": {
    id: "master-v2",
    label: "V2 — Banco Maestro",
    description: "3,558 preguntas canónicas",
    readOnly: true,
    version: "CB2026-FASE4-CIERRE",
    expectedQuestionCount: 3558,
  },
  "prep-v3": {
    id: "prep-v3",
    label: "V3 — Preparación 4 días",
    description: "500 preguntas por familias",
    readOnly: true,
    version: "CB2026-PREP-V3",
  },
  "curated-v4": {
    id: "curated-v4",
    label: "V4 — Banco Curado",
    description: "Cobertura amplia revisada",
    readOnly: true,
    version: "CB2026-CURATED-V4",
  },
  "massive-v5": {
    id: "massive-v5",
    label: "V5 — Sistema Masivo",
    description: "14,000 preguntas verificadas y variantes dinámicas",
    readOnly: true,
    version: "CB2026-MASSIVE-V5",
    expectedQuestionCount: 14000,
  },
  "consolidation-v5": {
    id: "consolidation-v5",
    label: "V5 — Consolidación Final",
    description: "Preguntas GOLD, recuperación por hechos y plan guiado",
    readOnly: true,
    version: "V5-CONSOLIDACION-FINAL-2026-08-26",
    expectedQuestionCount: 2549,
  },
}

export function getQuestionKey(question: Pick<Question, "bankId" | "id">) {
  return `${question.bankId ?? "local"}:${question.id}`
}

export function questionBelongsToSelection(question: Question, selection: BankSelection) {
  if (selection === "mixed") return question.bankProfileId !== "master-v2"
  if (selection === "prep-v3") return question.bankProfileId === "prep-v3"
  return (question.bankProfileId ?? "legacy-v1") === selection
}

export function filterQuestionsForSelection(questions: Question[], selection: BankSelection) {
  return questions.filter((question) => questionBelongsToSelection(question, selection))
}

function questionKeysForSelection(questions: Question[], selection: BankSelection) {
  return new Set(filterQuestionsForSelection(questions, selection).map(getQuestionKey))
}

export function filterSessionsForSelection(sessions: Session[], questions: Question[], selection: BankSelection) {
  const allowedKeys = questionKeysForSelection(questions, selection)
  return sessions.flatMap((session) => {
    const questionKeys = session.questionKeys.filter((key) => allowedKeys.has(key))
    if (questionKeys.length === 0) return []
    if (questionKeys.length === session.questionKeys.length) return [session]
    return [{
      ...session,
      questionKeys,
      answers: session.answers.filter((answer) => allowedKeys.has(answer.questionKey)),
    }]
  })
}

export function filterReportsForSelection(reports: QuestionReport[], questions: Question[], selection: BankSelection) {
  const allowedKeys = questionKeysForSelection(questions, selection)
  return reports.filter((report) => allowedKeys.has(report.questionKey))
}

export function normalizedDifficulty(question: Question): DifficultyBand {
  if (question.difficultyBand) return question.difficultyBand
  if (question.difficulty <= 2) return "BASIC"
  if (question.difficulty === 3) return "MEDIUM"
  if (question.difficulty === 4) return "HARD"
  return "EXPERT"
}

export function questionsShareFacts(left: Question | undefined, right: Question | undefined) {
  if (!left || !right) return false
  const leftFacts = new Set(left.factKeys?.length ? left.factKeys : [left.factKey])
  return (right.factKeys?.length ? right.factKeys : [right.factKey]).some((fact) => leftFacts.has(fact))
}
