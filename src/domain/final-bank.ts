import type { QuestionOption } from "@/domain/types"

export const FINAL_BANK_ID = "BANCO_UNICO_CONEXION_BIBLICA_2026" as const
export const FINAL_BANK_DISPLAY_NAME = "Banco Maestro Único — Final 2026" as const
export const FINAL_BANK_SCHEMA_VERSION = "9.0" as const

export const FINAL_QUESTION_FAMILIES = [
  "single_choice_direct",
  "fill_choice",
  "true_false",
  "single_choice_contextual",
] as const

export type FinalQuestionFamily = (typeof FINAL_QUESTION_FAMILIES)[number]

type FinalQuestionCandidate = {
  family: string
  options: QuestionOption[]
  correctAnswer: string[]
  finalEditorialStatus: string
}

export function isFinalQuestionFamily(value: string): value is FinalQuestionFamily {
  return FINAL_QUESTION_FAMILIES.includes(value as FinalQuestionFamily)
}

export function validateFinalQuestion(question: FinalQuestionCandidate): string[] {
  const errors: string[] = []
  if (!isFinalQuestionFamily(question.family)) errors.push("invalid_family")
  const expectedOptions = question.family === "true_false" ? 2 : 4
  if (question.options.length !== expectedOptions) errors.push("invalid_option_count")
  if (question.correctAnswer.length !== 1) errors.push("invalid_correct_answer")
  if (question.finalEditorialStatus !== "GOLD") errors.push("not_gold")
  return errors
}
