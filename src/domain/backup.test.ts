import { describe, expect, it } from "vitest"
import { createBackupPayload, migrateBackupPayload, validateBackupPayload } from "@/domain/backup"
import type { Preferences } from "@/domain/types"

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
})
