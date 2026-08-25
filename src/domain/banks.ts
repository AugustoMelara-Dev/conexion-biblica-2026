import type { BankProfileId, BankSelection, DifficultyBand, Question } from "@/domain/types"

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
}

export function getQuestionKey(question: Pick<Question, "bankId" | "id">) {
  return `${question.bankId ?? "local"}:${question.id}`
}

export function questionBelongsToSelection(question: Question, selection: BankSelection) {
  if (selection === "mixed") return true
  if (selection === "prep-v3") return question.bankProfileId === "prep-v3"
  return (question.bankProfileId ?? "legacy-v1") === selection
}

export function filterQuestionsForSelection(questions: Question[], selection: BankSelection) {
  return questions.filter((question) => questionBelongsToSelection(question, selection))
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
