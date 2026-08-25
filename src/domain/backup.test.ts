import { describe, expect, it } from "vitest"
import { createBackupPayload, migrateBackupPayload, validateBackupPayload } from "@/domain/backup"
import type { Bank, Preferences } from "@/domain/types"

const preferences: Preferences = { theme: "dark", lastMode: "training", reducedMotion: false, lastBankSelection: "legacy-v1" }

describe("respaldos locales", () => {
  it("crea un sobre versionado y valida su estructura antes de restaurar", () => {
    const payload = createBackupPayload({ banks: [], progress: [], sessions: [], reports: [], preferences }, 123)
    expect(payload).toMatchObject({
      backupVersion: "2.0", exportedAt: 123, preferences,
      coverageCycles: [], activeRound: null,
    })
    expect(validateBackupPayload(payload).valid).toBe(true)
    expect(validateBackupPayload({ ...payload, backupVersion: "0.1" }).valid).toBe(false)
  })

  it("migra respaldos 1.0 y agrega namespace a progreso V1 antiguo", () => {
    const legacy = {
      backupVersion: "1.0", exportedAt: 7, banks: [], sessions: [], reports: [], preferences,
      progress: [{ questionKey: "D03-0001", timesSeen: 1 }],
    }
    const migrated = migrateBackupPayload(legacy)

    expect(migrated.backupVersion).toBe("2.0")
    expect(migrated.progress[0].questionKey).toBe("legacy-v1:D03-0001")
    expect(migrated.coverageCycles).toEqual([])
    expect(migrated.activeRound).toBeNull()
  })

  it("rechaza respaldos incompletos y no acepta bancos con schema incompatible", () => {
    const result = validateBackupPayload({
      backupVersion: "1.0",
      exportedAt: 1,
      banks: [{ schemaVersion: "0.5" }],
      progress: [],
      sessions: [],
      reports: [],
      preferences,
    })
    expect(result.errors.map((error) => error.code)).toEqual(expect.arrayContaining(["INVALID_BACKUP_BANK"]))
  })

  it("conserva la vista V3 y su ronda activa en un respaldo 2.0", () => {
    const bank = {
      bankId: "bank-v3-daniel-json",
      bankProfileId: "prep-v3",
      name: "V3 — Preparación Daniel",
      sourceWork: "Daniel",
      sourceVersion: "Material PDF",
      schemaVersion: "1.0",
      importedAt: 1,
      fingerprint: "v3",
      questions: [],
    } satisfies Bank
    const payload = createBackupPayload({
      banks: [bank],
      progress: [],
      sessions: [],
      reports: [],
      preferences: { ...preferences, lastBankSelection: "prep-v3" },
      activeRound: {
        id: "active",
        startedAt: 1,
        updatedAt: 1,
        currentIndex: 0,
        questionKeys: [],
        answers: [],
        config: {
          mode: "training",
          count: 10,
          sourceWorks: ["Daniel"],
          chapters: [1],
          difficulties: [1, 2, 3, 4, 5],
          types: ["single_choice"],
          statuses: ["all"],
          shuffleQuestions: true,
          shuffleOptions: true,
          perQuestionSeconds: null,
          totalSeconds: null,
          bankSelection: "prep-v3",
          strategy: "coverage-cycle",
        },
      },
    }, 123)

    expect(validateBackupPayload(payload).valid).toBe(true)
    const migrated = migrateBackupPayload(payload)
    expect(migrated.preferences.lastBankSelection).toBe("prep-v3")
    expect(migrated.banks[0].bankProfileId).toBe("prep-v3")
    expect(migrated.activeRound?.config.bankSelection).toBe("prep-v3")
  })

  it("trata intentos y sesiones antiguas sin contexto como práctica", () => {
    const payload = createBackupPayload({ banks: [], progress: [], sessions: [], reports: [], preferences }, 123) as unknown as Record<string, unknown>
    payload.progress = [{ questionKey: "bank:q1", history: [{ timestamp: 1, isCorrect: false, wasAnswered: true, responseTimeMs: 1000, reason: "incorrect" }] }]
    payload.sessions = [{ id: "old", startedAt: 1, completedAt: 2, mode: "final", config: {}, questionKeys: [], answers: [], score: 0, durationMs: 1 }]
    const migrated = migrateBackupPayload(payload)
    expect(migrated.progress[0].history[0].context).toBe("practice")
    expect(migrated.sessions[0].context).toBe("practice")
  })
})
