import type { ActiveRound, BackupPayload, BankSelection, CoverageCycle, Preferences, ValidationError } from "@/domain/types"
import type { Bank, QuestionProgress, QuestionReport, Session } from "@/domain/types"

export function createBackupPayload(
  data: {
    banks: Bank[]
    progress: QuestionProgress[]
    sessions: Session[]
    reports: QuestionReport[]
    preferences: Preferences
    coverageCycles?: CoverageCycle[]
    activeRound?: ActiveRound | null
  },
  exportedAt = Date.now(),
): BackupPayload {
  return {
    backupVersion: "2.0",
    exportedAt,
    banks: structuredClone(data.banks),
    progress: structuredClone(data.progress),
    sessions: structuredClone(data.sessions),
    reports: structuredClone(data.reports),
    preferences: structuredClone(data.preferences),
    coverageCycles: structuredClone(data.coverageCycles ?? []),
    activeRound: structuredClone(data.activeRound ?? null),
  }
}

export function validateBackupPayload(input: unknown): { valid: boolean; errors: ValidationError[] } {
  const errors: ValidationError[] = []
  if (!input || typeof input !== "object" || Array.isArray(input)) return { valid: false, errors: [{ code: "INVALID_BACKUP", path: "$", message: "El respaldo debe ser un objeto JSON." }] }
  const payload = input as Record<string, unknown>
  if (payload.backupVersion !== "1.0" && payload.backupVersion !== "2.0") errors.push({ code: "UNSUPPORTED_BACKUP_VERSION", path: "$.backupVersion", message: "Se requiere backupVersion 1.0 o 2.0." })
  if (typeof payload.exportedAt !== "number") errors.push({ code: "INVALID_EXPORTED_AT", path: "$.exportedAt", message: "exportedAt debe ser un número." })
  for (const field of ["banks", "progress", "sessions", "reports"] as const) {
    if (!Array.isArray(payload[field])) errors.push({ code: "INVALID_BACKUP_FIELD", path: `$.${field}`, message: `${field} debe ser un arreglo.` })
  }
  if (!payload.preferences || typeof payload.preferences !== "object" || Array.isArray(payload.preferences)) errors.push({ code: "INVALID_BACKUP_PREFERENCES", path: "$.preferences", message: "preferences debe ser un objeto." })
  if (payload.backupVersion === "2.0") {
    if (!Array.isArray(payload.coverageCycles)) errors.push({ code: "INVALID_BACKUP_FIELD", path: "$.coverageCycles", message: "coverageCycles debe ser un arreglo." })
    if (payload.activeRound !== null && (typeof payload.activeRound !== "object" || Array.isArray(payload.activeRound))) errors.push({ code: "INVALID_ACTIVE_ROUND", path: "$.activeRound", message: "activeRound debe ser un objeto o null." })
  }
  if (Array.isArray(payload.banks)) payload.banks.forEach((bank, index) => {
    const schema = bank && typeof bank === "object" ? (bank as Record<string, unknown>).schemaVersion : undefined
    if (!bank || typeof bank !== "object" || (schema !== "1.0" && schema !== "2.0") || typeof (bank as Record<string, unknown>).bankId !== "string") errors.push({ code: "INVALID_BACKUP_BANK", path: `$.banks[${index}]`, message: "Cada banco debe ser una entidad compatible con bankId." })
  })
  return { valid: errors.length === 0, errors }
}

function namespaceLegacyKey(value: unknown) {
  const key = String(value ?? "")
  return key.includes(":") ? key : `legacy-v1:${key}`
}

function isBankSelection(value: unknown): value is BankSelection {
  return value === "legacy-v1" || value === "master-v2" || value === "prep-v3" || value === "curated-v4" || value === "mixed"
}

function normalizePreferences(preferences: Preferences): Preferences {
  return {
    ...preferences,
    lastBankSelection: isBankSelection(preferences.lastBankSelection)
      ? preferences.lastBankSelection
      : "curated-v4",
  }
}

export function migrateBackupPayload(input: unknown): BackupPayload {
  const validation = validateBackupPayload(input)
  if (!validation.valid) throw new Error(validation.errors.map((error) => `${error.path}: ${error.message}`).join("\n"))
  const payload = structuredClone(input) as Record<string, unknown>
  if (payload.backupVersion === "2.0") return normalizeContexts(payload as unknown as BackupPayload)

  const progress = (payload.progress as QuestionProgress[]).map((item) => ({ ...item, questionKey: namespaceLegacyKey(item.questionKey) }))
  const sessions = (payload.sessions as Session[]).map((session) => ({
    ...session,
    questionKeys: session.questionKeys.map(namespaceLegacyKey),
    answers: session.answers.map((answer) => ({ ...answer, questionKey: namespaceLegacyKey(answer.questionKey) })),
    config: { ...session.config, bankSelection: session.config.bankSelection ?? "legacy-v1", strategy: session.config.strategy ?? "adaptive" },
  }))
  const reports = (payload.reports as QuestionReport[]).map((report) => ({ ...report, questionKey: namespaceLegacyKey(report.questionKey) }))
  return normalizeContexts({
    backupVersion: "2.0",
    exportedAt: payload.exportedAt as number,
    banks: payload.banks as Bank[],
    progress,
    sessions,
    reports,
    preferences: payload.preferences as Preferences,
    coverageCycles: [],
    activeRound: null,
  })
}

function normalizeContexts(payload: BackupPayload): BackupPayload {
  return {
    ...payload,
    preferences: normalizePreferences(payload.preferences),
    progress: payload.progress.map((item) => ({
      ...item,
      history: (item.history ?? []).map((attempt) => ({ ...attempt, context: attempt.context ?? "practice" })),
    })),
    sessions: payload.sessions.map((session) => ({ ...session, context: session.context ?? "practice" })),
  }
}
