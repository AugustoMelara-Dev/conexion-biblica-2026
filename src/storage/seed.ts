import { validateBank } from "@/domain/validation"
import type { Bank, Question, QuestionType, SourceWork } from "@/domain/types"

function slug(value: string) {
  return value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")
}

function hashString(value: string) {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0).toString(16)
}

export function createBankFromRaw(raw: Record<string, unknown>, sourceFileName: string, importedAt = Date.now()): Bank {
  const validation = validateBank(raw, sourceFileName)
  if (!validation.valid) throw new Error(validation.errors.map((error) => `${error.path}: ${error.message}`).join("\n"))
  const metadata = raw.bank as Record<string, unknown>
  const rawQuestions = raw.questions as Record<string, unknown>[]
  const firstSource = rawQuestions[0].source as Record<string, unknown>
  const sourceWork = String(metadata.sourceWork ?? firstSource.work) as SourceWork
  const sourceVersion = String(metadata.sourceVersion ?? firstSource.version)
  const bankId = `bank-${slug(sourceFileName)}`
  const questions = rawQuestions.map((question) => ({
    ...question,
    bankId,
    bankProfileId: "legacy-v1",
    type: question.type as QuestionType,
    difficulty: question.difficulty as Question["difficulty"],
    source: question.source,
    tags: Array.isArray(question.tags) ? question.tags.map(String) : [],
    options: Array.isArray(question.options) ? question.options : [],
    correctAnswer: Array.isArray(question.correctAnswer) ? question.correctAnswer.map(String) : [],
  })) as unknown as Question[]
  return {
    bankId,
    bankProfileId: "legacy-v1",
    name: sourceWork === "Daniel" ? `Daniel ${metadata.chapter ?? firstSource.chapter}` : `Profetas y Reyes ${metadata.chapter ?? firstSource.chapter}`,
    sourceWork,
    sourceVersion,
    schemaVersion: "1.0",
    importedAt,
    fingerprint: hashString(JSON.stringify(raw)),
    sourceFileName,
    raw: structuredClone(raw),
    questions,
  }
}

export function getBankQuestionKey(bankId: string, questionId: string) {
  return `${bankId}:${questionId}`
}
