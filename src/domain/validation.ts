import { SUPPORTED_QUESTION_TYPES, type QuestionType, type ValidationError } from "@/domain/types"
import type { ValidationResult } from "@/domain/types"

const supported = new Set<string>(SUPPORTED_QUESTION_TYPES)
const sourceWorks = new Set(["Daniel", "Profetas y Reyes"])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0
}

function add(errors: ValidationError[], code: string, path: string, message: string, questionId?: string) {
  errors.push({ code, path, message, questionId })
}

function validateOptions(question: Record<string, unknown>, path: string, errors: ValidationError[], questionId: string) {
  if (!Array.isArray(question.options)) {
    add(errors, "MISSING_OPTIONS", `${path}.options`, "La pregunta debe contener un arreglo options.", questionId)
    return new Set<string>()
  }
  const ids = new Set<string>()
  question.options.forEach((option, index) => {
    if (!isRecord(option) || !isNonEmptyString(option.id) || !isNonEmptyString(option.text)) {
      add(errors, "INVALID_OPTION", `${path}.options[${index}]`, "Cada opción requiere id y text no vacíos.", questionId)
      return
    }
    if (ids.has(option.id)) add(errors, "DUPLICATE_OPTION_ID", `${path}.options[${index}].id`, `La opción ${option.id} está repetida.`, questionId)
    ids.add(option.id)
  })
  return ids
}

export function validateBank(input: unknown, sourceName: string): ValidationResult {
  const errors: ValidationError[] = []
  if (!isRecord(input)) {
    add(errors, "INVALID_ROOT", "$", "El archivo debe contener un objeto JSON.")
    return { valid: false, errors, questionCount: 0, sourceName }
  }
  if (input.schemaVersion !== "1.0") add(errors, "UNSUPPORTED_SCHEMA", "$.schemaVersion", "Se requiere schemaVersion 1.0.")
  if (!isRecord(input.bank)) add(errors, "MISSING_BANK_METADATA", "$.bank", "Falta el objeto bank con metadatos de origen.")
  if (!Array.isArray(input.questions)) {
    add(errors, "MISSING_QUESTIONS", "$.questions", "Falta el arreglo questions.")
    return { valid: false, errors, questionCount: 0, sourceName, raw: input }
  }
  const ids = new Set<string>()
  input.questions.forEach((rawQuestion, index) => {
    const path = `$.questions[${index}]`
    if (!isRecord(rawQuestion)) {
      add(errors, "INVALID_QUESTION", path, "Cada pregunta debe ser un objeto.")
      return
    }
    const questionId = isNonEmptyString(rawQuestion.id) ? rawQuestion.id : undefined
    if (!questionId) add(errors, "MISSING_ID", `${path}.id`, "La pregunta requiere un id.")
    else if (ids.has(questionId)) add(errors, "DUPLICATE_ID", `${path}.id`, `El ID ${questionId} está repetido.`, questionId)
    else ids.add(questionId)
    if (!isNonEmptyString(rawQuestion.type) || !supported.has(rawQuestion.type)) add(errors, "UNSUPPORTED_TYPE", `${path}.type`, `Tipo no soportado: ${String(rawQuestion.type)}.`, questionId)
    if (typeof rawQuestion.difficulty !== "number" || !Number.isInteger(rawQuestion.difficulty) || rawQuestion.difficulty < 1 || rawQuestion.difficulty > 5) add(errors, "INVALID_DIFFICULTY", `${path}.difficulty`, "La dificultad debe ser un entero de 1 a 5.", questionId)
    if (!isRecord(rawQuestion.source)) add(errors, "INVALID_SOURCE", `${path}.source`, "La pregunta requiere source.", questionId)
    else {
      if (!sourceWorks.has(String(rawQuestion.source.work))) add(errors, "UNSUPPORTED_SOURCE", `${path}.source.work`, "La fuente debe ser Daniel o Profetas y Reyes.", questionId)
      if (typeof rawQuestion.source.chapter !== "number" || !Number.isInteger(rawQuestion.source.chapter) || rawQuestion.source.chapter < 1) add(errors, "INVALID_CHAPTER", `${path}.source.chapter`, "El capítulo debe ser un entero positivo.", questionId)
      if (!isNonEmptyString(rawQuestion.source.reference)) add(errors, "INVALID_REFERENCE", `${path}.source.reference`, "La referencia es obligatoria.", questionId)
    }
    if (!isNonEmptyString(rawQuestion.question)) add(errors, "MISSING_PROMPT", `${path}.question`, "El texto de la pregunta es obligatorio.", questionId)
    if (!isNonEmptyString(rawQuestion.factKey)) add(errors, "MISSING_FACT_KEY", `${path}.factKey`, "factKey es obligatorio.", questionId)
    const type = String(rawQuestion.type) as QuestionType
    const optionIds = type === "matching" ? new Set<string>() : validateOptions(rawQuestion, path, errors, questionId ?? "")
    if (!Array.isArray(rawQuestion.correctAnswer)) add(errors, "MISSING_CORRECT_ANSWER", `${path}.correctAnswer`, "correctAnswer debe ser un arreglo.", questionId)
    else if (type !== "matching" && rawQuestion.correctAnswer.length === 0) add(errors, "EMPTY_CORRECT_ANSWER", `${path}.correctAnswer`, "La respuesta correcta no puede estar vacía.", questionId)
    else if (type !== "matching") rawQuestion.correctAnswer.forEach((answer, answerIndex) => {
      if (!isNonEmptyString(answer) || !optionIds.has(answer)) add(errors, "INVALID_CORRECT_ANSWER", `${path}.correctAnswer[${answerIndex}]`, `La respuesta ${String(answer)} no apunta a una opción existente.`, questionId)
    })
    if (type === "matching") {
      const leftIds = validateItems(rawQuestion.leftItems, `${path}.leftItems`, errors, questionId)
      const rightIds = validateItems(rawQuestion.rightItems, `${path}.rightItems`, errors, questionId)
      if (!Array.isArray(rawQuestion.correctMatches) || rawQuestion.correctMatches.length === 0) add(errors, "MISSING_CORRECT_MATCHES", `${path}.correctMatches`, "matching requiere correctMatches.", questionId)
      else rawQuestion.correctMatches.forEach((match, matchIndex) => {
        if (!isRecord(match) || !leftIds.has(String(match.left)) || !rightIds.has(String(match.right))) add(errors, "INVALID_CORRECT_MATCH", `${path}.correctMatches[${matchIndex}]`, "Cada par debe referir a un leftItem y rightItem existentes.", questionId)
      })
    }
  })
  return { valid: errors.length === 0, errors, questionCount: input.questions.length, sourceName, raw: input }
}

function validateItems(value: unknown, path: string, errors: ValidationError[], questionId?: string) {
  const ids = new Set<string>()
  if (!Array.isArray(value) || value.length === 0) {
    add(errors, "MISSING_MATCH_ITEMS", path, "matching requiere listas de items no vacías.", questionId)
    return ids
  }
  value.forEach((item, index) => {
    if (!isRecord(item) || !isNonEmptyString(item.id) || !isNonEmptyString(item.text)) add(errors, "INVALID_MATCH_ITEM", `${path}[${index}]`, "Cada item requiere id y text.", questionId)
    else ids.add(item.id)
  })
  return ids
}
