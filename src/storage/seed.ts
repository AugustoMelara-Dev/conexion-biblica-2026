import { validateBank } from "@/domain/validation"
import type { Bank, BankProfileId, Question, QuestionType, SourceWork } from "@/domain/types"

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

export function getBankIdForSourceFileName(sourceFileName: string) {
  return `bank-${slug(sourceFileName)}`
}

function resolveBankProfileId(value: unknown): BankProfileId {
  switch (value) {
    case "legacy-v1":
    case "master-v2":
    case "prep-v3":
    case "curated-v4":
    case "massive-v5":
      return value
    default:
      return "legacy-v1"
  }
}

export function getRawBankProfileId(raw: Record<string, unknown>): BankProfileId {
  const metadata = raw.bank && typeof raw.bank === "object" && !Array.isArray(raw.bank)
    ? raw.bank as Record<string, unknown>
    : {}
  return resolveBankProfileId(metadata.profileId)
}

export function isIntegratedBankProfile(value: unknown): value is "master-v2" | "prep-v3" | "curated-v4" | "massive-v5" {
  return value === "master-v2" || value === "prep-v3" || value === "curated-v4" || value === "massive-v5"
}

export function isGenericBankImportAllowed(
  incomingProfileId: unknown,
  replaceBankId?: string,
  replaceBankProfileId?: unknown,
) {
  return !isIntegratedBankProfile(incomingProfileId)
    && replaceBankId !== "master-v2"
    && !isIntegratedBankProfile(replaceBankProfileId)
}

export function createBankFromRaw(raw: Record<string, unknown>, sourceFileName: string, importedAt = Date.now()): Bank {
  const validation = validateBank(raw, sourceFileName)
  if (!validation.valid) throw new Error(validation.errors.map((error) => `${error.path}: ${error.message}`).join("\n"))
  const metadata = raw.bank as Record<string, unknown>
  const rawQuestions = raw.questions as Record<string, unknown>[]
  const firstSource = rawQuestions[0].source as Record<string, unknown>
  const sourceWork = String(metadata.sourceWork ?? firstSource.work) as SourceWork
  const sourceVersion = String(metadata.sourceVersion ?? firstSource.version)
  const bankId = getBankIdForSourceFileName(sourceFileName)
  const bankProfileId = getRawBankProfileId(raw)
  const questions = rawQuestions.map((question) => ({
    ...question,
    bankId,
    bankProfileId,
    type: question.type as QuestionType,
    difficulty: question.difficulty as Question["difficulty"],
    source: question.source,
    tags: Array.isArray(question.tags) ? question.tags.map(String) : [],
    options: Array.isArray(question.options) ? question.options : [],
    correctAnswer: Array.isArray(question.correctAnswer) ? question.correctAnswer.map(String) : [],
  })) as unknown as Question[]
  return {
    bankId,
    bankProfileId,
    name: bankProfileId === "prep-v3"
      ? `V3 — Preparación ${sourceWork}`
      : bankProfileId === "curated-v4"
        ? `V4 — Banco Curado ${sourceWork}`
        : bankProfileId === "massive-v5"
          ? `V5 — Banco Masivo ${sourceWork}`
        : sourceWork === "Daniel"
          ? `Daniel ${metadata.chapter ?? firstSource.chapter}`
          : `Profetas y Reyes ${metadata.chapter ?? firstSource.chapter}`,
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

export function shouldReplaceBundledBank(
  existing: { fingerprint: string } | undefined,
  incoming: { fingerprint: string },
) {
  return !existing || existing.fingerprint !== incoming.fingerprint
}
