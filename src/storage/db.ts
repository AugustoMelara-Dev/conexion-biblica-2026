import type {
  ActiveRound,
  BackupPayload,
  Bank,
  CoverageCycle,
  Question,
  QuestionExposure,
  QuestionSessionQuery,
  ExposureAttempt,
  BlindUsage,
  LegacyHistoryEvent,
  MigrationBackup,
  QuestionProgress,
  QuestionReport,
  Session,
} from "@/domain/types"
import type { FactMastery } from "@/domain/fact-mastery"

export const DB_NAME = "conexion-biblica-2026"
export const DB_VERSION = 4

type StoredQuestion = Question & { questionKey: string; blindPoolKey: 0 | 1 }
type StoredSetting = { key: string; value: unknown }

let activeDb: IDBDatabase | null = null

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () =>
      reject(request.error ?? new Error("IndexedDB request failed"))
  })
}

function transactionDone(transaction: IDBTransaction) {
  return new Promise<void>((resolve, reject) => {
    transaction.oncomplete = () => resolve()
    transaction.onerror = () =>
      reject(transaction.error ?? new Error("IndexedDB transaction failed"))
    transaction.onabort = () =>
      reject(transaction.error ?? new Error("IndexedDB transaction aborted"))
  })
}

export function openAppDb(): Promise<IDBDatabase> {
  if (activeDb) return Promise.resolve(activeDb)
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = (event) => {
      const db = request.result
      if (!db.objectStoreNames.contains("banks"))
        db.createObjectStore("banks", { keyPath: "bankId" })
      if (!db.objectStoreNames.contains("questions")) {
        const questions = db.createObjectStore("questions", {
          keyPath: "questionKey",
        })
        questions.createIndex("bankId", "bankId", { unique: false })
        questions.createIndex("sourceChapter", ["source", "chapter"], {
          unique: false,
        })
      }
      const questions = request.transaction!.objectStore("questions")
      const questionIndexes: Array<[string, string | string[]]> = [
        ["bankId", "bankId"],
        ["sourceChapterV3", "source.chapter"],
        ["factId", "factId"],
        ["difficultyBand", "difficultyBand"],
        ["type", "type"],
        ["blindFinalPool", "blindPoolKey"],
      ]
      for (const [name, keyPath] of questionIndexes)
        if (!questions.indexNames.contains(name))
          questions.createIndex(name, keyPath, { unique: false })
      if (!db.objectStoreNames.contains("progress"))
        db.createObjectStore("progress", { keyPath: "questionKey" })
      if (!db.objectStoreNames.contains("sessions"))
        db.createObjectStore("sessions", { keyPath: "id" })
      if (!db.objectStoreNames.contains("reports"))
        db.createObjectStore("reports", { keyPath: "id" })
      if (!db.objectStoreNames.contains("settings"))
        db.createObjectStore("settings", { keyPath: "key" })
      if (!db.objectStoreNames.contains("coverageCycles"))
        db.createObjectStore("coverageCycles", { keyPath: "poolKey" })
      if (!db.objectStoreNames.contains("activeRound"))
        db.createObjectStore("activeRound", { keyPath: "id" })
      if (!db.objectStoreNames.contains("exposures")) {
        const exposures = db.createObjectStore("exposures", {
          keyPath: "exposureKey",
        })
        exposures.createIndex("factId", "factId", { unique: false })
        exposures.createIndex("variantId", "variantId", { unique: false })
        exposures.createIndex("lastSeenAt", "lastSeenAt", { unique: false })
      }
      if (!db.objectStoreNames.contains("factMastery")) {
        const mastery = db.createObjectStore("factMastery", { keyPath: "factId" })
        mastery.createIndex("state", "state", { unique: false })
        mastery.createIndex("nextDueAt", "nextDueAt", { unique: false })
        mastery.createIndex("chapter", "chapter", { unique: false })
      }
      if (!db.objectStoreNames.contains("legacyEvents"))
        db.createObjectStore("legacyEvents", { keyPath: "id" })
      if (!db.objectStoreNames.contains("migrationBackups"))
        db.createObjectStore("migrationBackups", { keyPath: "id" })
      if (!db.objectStoreNames.contains("missionPlan"))
        db.createObjectStore("missionPlan", { keyPath: "id" })
      if (!db.objectStoreNames.contains("blindUsage")) {
        const blind = db.createObjectStore("blindUsage", { keyPath: ["factId", "pool"] })
        blind.createIndex("pool", "pool", { unique: false })
        blind.createIndex("consumedAt", "consumedAt", { unique: false })
      }
      if (event.oldVersion < 2 && db.objectStoreNames.contains("progress")) {
        const store = request.transaction!.objectStore("progress")
        const cursorRequest = store.openCursor()
        cursorRequest.onsuccess = () => {
          const cursor = cursorRequest.result
          if (!cursor) return
          const item = cursor.value as QuestionProgress
          if (
            typeof item.questionKey === "string" &&
            !item.questionKey.includes(":")
          ) {
            cursor.delete()
            store.put({ ...item, questionKey: `legacy-v1:${item.questionKey}` })
          }
          cursor.continue()
        }
      }
    }
    request.onsuccess = () => {
      activeDb = request.result
      activeDb.onversionchange = () => activeDb?.close()
      resolve(activeDb)
    }
    request.onerror = () =>
      reject(request.error ?? new Error("Unable to open IndexedDB"))
  })
}

export async function deleteAppDb() {
  activeDb?.close()
  activeDb = null
  await new Promise<void>((resolve, reject) => {
    const request = indexedDB.deleteDatabase(DB_NAME)
    request.onsuccess = () => resolve()
    request.onerror = () =>
      reject(request.error ?? new Error("Unable to delete IndexedDB"))
    request.onblocked = () => resolve()
  })
}

function questionKey(question: Question) {
  return `${question.bankId ?? "local"}:${question.id}`
}

function withoutKey(question: StoredQuestion): Question {
  const value = Object.fromEntries(
    Object.entries(question).filter(
      ([key]) => key !== "questionKey" && key !== "blindPoolKey"
    )
  ) as Question
  return {
    ...value,
    bankProfileId:
      value.bankProfileId ??
      (value.bankId === "master-v2" ? "master-v2" : "legacy-v1"),
  }
}

export function createRepositories(db: IDBDatabase) {
  return {
    async restoreBackup(payload: BackupPayload) {
      const stores = [
        "banks",
        "questions",
        "progress",
        "sessions",
        "reports",
        "settings",
        "coverageCycles",
        "activeRound",
        "exposures",
        "factMastery",
        "legacyEvents",
        "migrationBackups",
        "missionPlan",
        "blindUsage",
      ]
      const tx = db.transaction(stores, "readwrite")
      for (const store of stores) tx.objectStore(store).clear()

      const banksStore = tx.objectStore("banks")
      const questionsStore = tx.objectStore("questions")
      for (const bank of payload.banks) {
        banksStore.put({ ...bank, questions: undefined })
        for (const question of bank.questions)
          questionsStore.put({
            ...question,
            bankId: bank.bankId,
            questionKey: questionKey({ ...question, bankId: bank.bankId }),
            blindPoolKey: question.blindFinalPool ? 1 : 0,
          } satisfies StoredQuestion)
      }
      for (const item of payload.progress)
        tx.objectStore("progress").put(item)
      for (const item of payload.sessions)
        tx.objectStore("sessions").put(item)
      for (const item of payload.reports)
        tx.objectStore("reports").put(item)
      for (const item of payload.coverageCycles)
        tx.objectStore("coverageCycles").put(item)
      if (payload.activeRound)
        tx.objectStore("activeRound").put(payload.activeRound)
      for (const item of payload.exposures ?? [])
        tx.objectStore("exposures").put(item)
      for (const item of payload.factMastery ?? [])
        tx.objectStore("factMastery").put(item)
      for (const item of payload.legacyEvents ?? [])
        tx.objectStore("legacyEvents").put(item)
      for (const item of payload.blindUsage ?? [])
        tx.objectStore("blindUsage").put(item)
      tx.objectStore("settings").put({
        key: "v7-history-backup",
        value: `restored-${payload.exportedAt}`,
      } satisfies StoredSetting)
      await transactionDone(tx)
    },
    async resetAll() {
      const stores = [
        "banks",
        "questions",
        "progress",
        "sessions",
        "reports",
        "settings",
        "coverageCycles",
        "activeRound",
        "exposures",
        "factMastery",
        "legacyEvents",
        "migrationBackups",
        "missionPlan",
        "blindUsage",
      ]
      const tx = db.transaction(stores, "readwrite")
      stores.forEach((store) => tx.objectStore(store).clear())
      await transactionDone(tx)
    },
    banks: {
      async save(bank: Bank) {
        const tx = db.transaction(["banks", "questions"], "readwrite")
        const banksStore = tx.objectStore("banks")
        const questionsStore = tx.objectStore("questions")
        banksStore.put({ ...bank, questions: undefined })
        const index = questionsStore.index("bankId")
        const cursorRequest = index.openCursor(IDBKeyRange.only(bank.bankId))
        cursorRequest.onsuccess = () => {
          const cursor = cursorRequest.result
          if (cursor) {
            cursor.delete()
            cursor.continue()
          } else {
            bank.questions.forEach((question) => {
              const record = {
                ...question,
                bankId: bank.bankId,
                questionKey: questionKey({ ...question, bankId: bank.bankId }),
                blindPoolKey: question.blindFinalPool ? 1 : 0,
              }
              questionsStore.put(record)
            })
          }
        }
        await transactionDone(tx)
      },
      async list(): Promise<Bank[]> {
        const tx = db.transaction("banks", "readonly")
        const rows = await requestResult(tx.objectStore("banks").getAll())
        await transactionDone(tx)
        return rows.map((row) => ({ ...row, questions: [] })) as Bank[]
      },
      async get(bankId: string): Promise<Bank | undefined> {
        const tx = db.transaction("banks", "readonly")
        const row = await requestResult(tx.objectStore("banks").get(bankId))
        await transactionDone(tx)
        return row ? ({ ...row, questions: [] } as Bank) : undefined
      },
      async remove(bankId: string) {
        const tx = db.transaction(["banks", "questions"], "readwrite")
        tx.objectStore("banks").delete(bankId)
        const cursorRequest = tx
          .objectStore("questions")
          .index("bankId")
          .openCursor(IDBKeyRange.only(bankId))
        cursorRequest.onsuccess = () => {
          const cursor = cursorRequest.result
          if (cursor) {
            cursor.delete()
            cursor.continue()
          }
        }
        await transactionDone(tx)
      },
    },
    questions: {
      async list(): Promise<Question[]> {
        const tx = db.transaction("questions", "readonly")
        const rows = await requestResult(tx.objectStore("questions").getAll())
        await transactionDone(tx)
        return (rows as StoredQuestion[]).map(withoutKey)
      },
      async get(key: string): Promise<Question | undefined> {
        const tx = db.transaction("questions", "readonly")
        const row = await requestResult(tx.objectStore("questions").get(key))
        await transactionDone(tx)
        return row ? withoutKey(row as StoredQuestion) : undefined
      },
      async putMany(questions: Question[]) {
        if (questions.length === 0) return
        const tx = db.transaction("questions", "readwrite")
        const store = tx.objectStore("questions")
        for (const question of questions)
          store.put({
            ...question,
            questionKey: questionKey(question),
            blindPoolKey: question.blindFinalPool ? 1 : 0,
          } satisfies StoredQuestion)
        await transactionDone(tx)
      },
      async listForSession(query: QuestionSessionQuery): Promise<Question[]> {
        if (query.limit <= 0) return []
        const tx = db.transaction("questions", "readonly")
        const store = tx.objectStore("questions")
        const source: IDBObjectStore | IDBIndex = query.bankId
          ? store.index("bankId")
          : store
        const range = query.bankId ? IDBKeyRange.only(query.bankId) : undefined
        const rows: Question[] = []
        await new Promise<void>((resolve, reject) => {
          const request = source.openCursor(range)
          request.onerror = () => reject(request.error)
          request.onsuccess = () => {
            const cursor = request.result
            if (!cursor || rows.length >= query.limit) {
              resolve()
              return
            }
            const value = withoutKey(cursor.value as StoredQuestion)
            const chapterMatches =
              !query.chapters?.length || query.chapters.includes(value.source.chapter)
            const difficultyMatches =
              !query.difficultyBands?.length ||
              (value.difficultyBand !== undefined &&
                query.difficultyBands.includes(value.difficultyBand))
            const typeMatches =
              !query.types?.length || query.types.includes(value.type)
            const blindMatches = query.includeBlind || !value.blindFinalPool
            if (
              chapterMatches &&
              difficultyMatches &&
              typeMatches &&
              blindMatches
            )
              rows.push(value)
            cursor.continue()
          }
        })
        await transactionDone(tx)
        return rows
      },
    },
    exposures: {
      async get(
        factId: string,
        variantId: string
      ): Promise<QuestionExposure | undefined> {
        const tx = db.transaction("exposures", "readonly")
        const row = await requestResult(
          tx.objectStore("exposures").get(`${factId}:${variantId}`)
        )
        await transactionDone(tx)
        return row as QuestionExposure | undefined
      },
      async list(): Promise<QuestionExposure[]> {
        const tx = db.transaction("exposures", "readonly")
        const rows = await requestResult(tx.objectStore("exposures").getAll())
        await transactionDone(tx)
        return rows as QuestionExposure[]
      },
      async listForFact(factId: string): Promise<QuestionExposure[]> {
        const tx = db.transaction("exposures", "readonly")
        const rows = await requestResult(
          tx.objectStore("exposures").index("factId").getAll(factId)
        )
        await transactionDone(tx)
        return rows as QuestionExposure[]
      },
      async record(attempt: ExposureAttempt): Promise<QuestionExposure> {
        const exposureKey = `${attempt.factId}:${attempt.variantId}`
        const tx = db.transaction("exposures", "readwrite")
        const store = tx.objectStore("exposures")
        let next: QuestionExposure | undefined
        const request = store.get(exposureKey)
        request.onsuccess = () => {
          const current = request.result as QuestionExposure | undefined
          const exposures = (current?.exposures ?? 0) + 1
          const totalResponseTimeMs =
            (current?.totalResponseTimeMs ?? 0) + attempt.responseTimeMs
          const evidence = current?.evidence ?? {
            practice: { attempts: 0, correct: 0 },
            cold: { attempts: 0, correct: 0 },
            deferred: { attempts: 0, correct: 0 },
            blind: { attempts: 0, correct: 0 },
          }
          const exposureKind = attempt.exposureKind ?? "practice"
          const nextEvidence = {
            ...evidence,
            [exposureKind]: {
              attempts: evidence[exposureKind].attempts + 1,
              correct: evidence[exposureKind].correct + (attempt.isCorrect ? 1 : 0),
            },
          }
          next = {
            exposureKey,
            factId: attempt.factId,
            variantId: attempt.variantId,
            questionKey: attempt.questionKey,
            exposures,
            correct: (current?.correct ?? 0) + (attempt.isCorrect ? 1 : 0),
            incorrect:
              (current?.incorrect ?? 0) + (attempt.isCorrect ? 0 : 1),
            totalResponseTimeMs,
            averageResponseTimeMs: totalResponseTimeMs / exposures,
            lastSeenAt: attempt.timestamp,
            lastSelectedAnswer: attempt.selectedAnswer,
            lastErrorType: attempt.errorType,
            evidence: nextEvidence,
          }
          store.put(next)
        }
        request.onerror = () => tx.abort()
        await transactionDone(tx)
        if (!next) throw new Error("No se pudo guardar la exposición")
        return next
      },
    },
    factMastery: {
      async get(factId: string): Promise<FactMastery | undefined> {
        const tx = db.transaction("factMastery", "readonly")
        const row = await requestResult(tx.objectStore("factMastery").get(factId))
        await transactionDone(tx)
        return row as FactMastery | undefined
      },
      async put(value: FactMastery) {
        const tx = db.transaction("factMastery", "readwrite")
        tx.objectStore("factMastery").put(value)
        await transactionDone(tx)
      },
      async list(): Promise<FactMastery[]> {
        const tx = db.transaction("factMastery", "readonly")
        const rows = await requestResult(tx.objectStore("factMastery").getAll())
        await transactionDone(tx)
        return rows as FactMastery[]
      },
    },
    legacyEvents: {
      async putMany(values: LegacyHistoryEvent[]) {
        if (!values.length) return
        const tx = db.transaction("legacyEvents", "readwrite")
        for (const value of values) tx.objectStore("legacyEvents").put(value)
        await transactionDone(tx)
      },
      async list(): Promise<LegacyHistoryEvent[]> {
        const tx = db.transaction("legacyEvents", "readonly")
        const rows = await requestResult(tx.objectStore("legacyEvents").getAll())
        await transactionDone(tx)
        return rows as LegacyHistoryEvent[]
      },
    },
    migrationBackups: {
      async put(value: MigrationBackup) {
        const tx = db.transaction("migrationBackups", "readwrite")
        tx.objectStore("migrationBackups").put(value)
        await transactionDone(tx)
      },
      async list(): Promise<MigrationBackup[]> {
        const tx = db.transaction("migrationBackups", "readonly")
        const rows = await requestResult(tx.objectStore("migrationBackups").getAll())
        await transactionDone(tx)
        return rows as MigrationBackup[]
      },
    },
    blindUsage: {
      async put(value: BlindUsage) {
        const tx = db.transaction("blindUsage", "readwrite")
        tx.objectStore("blindUsage").put(value)
        await transactionDone(tx)
      },
      async list(): Promise<BlindUsage[]> {
        const tx = db.transaction("blindUsage", "readonly")
        const rows = await requestResult(tx.objectStore("blindUsage").getAll())
        await transactionDone(tx)
        return rows as BlindUsage[]
      },
    },
    progress: {
      async get(key: string): Promise<QuestionProgress | undefined> {
        const tx = db.transaction("progress", "readonly")
        const row = await requestResult(tx.objectStore("progress").get(key))
        await transactionDone(tx)
        return row as QuestionProgress | undefined
      },
      async put(progress: QuestionProgress) {
        const tx = db.transaction("progress", "readwrite")
        tx.objectStore("progress").put(progress)
        await transactionDone(tx)
      },
      async update(
        key: string,
        updater: (current: QuestionProgress | undefined) => QuestionProgress
      ) {
        const tx = db.transaction("progress", "readwrite")
        const store = tx.objectStore("progress")
        let next: QuestionProgress | undefined
        const request = store.get(key)
        request.onsuccess = () => {
          next = updater(request.result as QuestionProgress | undefined)
          store.put(next)
        }
        request.onerror = () => tx.abort()
        await transactionDone(tx)
        if (!next) throw new Error("No se pudo actualizar el progreso")
        return next
      },
      async list(): Promise<QuestionProgress[]> {
        const tx = db.transaction("progress", "readonly")
        const rows = await requestResult(tx.objectStore("progress").getAll())
        await transactionDone(tx)
        return rows as QuestionProgress[]
      },
    },
    sessions: {
      async add(session: Session) {
        const tx = db.transaction("sessions", "readwrite")
        tx.objectStore("sessions").put(session)
        await transactionDone(tx)
      },
      async list(): Promise<Session[]> {
        const tx = db.transaction("sessions", "readonly")
        const rows = await requestResult(tx.objectStore("sessions").getAll())
        await transactionDone(tx)
        return (rows as Session[]).sort(
          (left, right) => right.startedAt - left.startedAt
        )
      },
      async get(id: string): Promise<Session | undefined> {
        const tx = db.transaction("sessions", "readonly")
        const row = await requestResult(tx.objectStore("sessions").get(id))
        await transactionDone(tx)
        return row as Session | undefined
      },
    },
    reports: {
      async add(report: QuestionReport) {
        const tx = db.transaction("reports", "readwrite")
        tx.objectStore("reports").put(report)
        await transactionDone(tx)
      },
      async addWithProgress(
        report: QuestionReport,
        updater: (current: QuestionProgress | undefined) => QuestionProgress
      ) {
        const tx = db.transaction(["reports", "progress"], "readwrite")
        const done = transactionDone(tx)
        const reportsStore = tx.objectStore("reports")
        const progressStore = tx.objectStore("progress")
        let next: QuestionProgress | undefined
        reportsStore.put(report)
        const request = progressStore.get(report.questionKey)
        request.onsuccess = () => {
          try {
            next = updater(request.result as QuestionProgress | undefined)
            progressStore.put(next)
          } catch {
            tx.abort()
          }
        }
        request.onerror = () => tx.abort()
        await done
        if (!next) throw new Error("No se pudo guardar el reporte")
        return next
      },
      async list(): Promise<QuestionReport[]> {
        const tx = db.transaction("reports", "readonly")
        const rows = await requestResult(tx.objectStore("reports").getAll())
        await transactionDone(tx)
        return (rows as QuestionReport[]).sort(
          (left, right) => right.reportedAt - left.reportedAt
        )
      },
    },
    coverage: {
      async get(poolKey: string): Promise<CoverageCycle | undefined> {
        const tx = db.transaction("coverageCycles", "readonly")
        const row = await requestResult(
          tx.objectStore("coverageCycles").get(poolKey)
        )
        await transactionDone(tx)
        return row as CoverageCycle | undefined
      },
      async put(cycle: CoverageCycle) {
        const tx = db.transaction("coverageCycles", "readwrite")
        tx.objectStore("coverageCycles").put(cycle)
        await transactionDone(tx)
      },
      async list(): Promise<CoverageCycle[]> {
        const tx = db.transaction("coverageCycles", "readonly")
        const rows = await requestResult(
          tx.objectStore("coverageCycles").getAll()
        )
        await transactionDone(tx)
        return rows as CoverageCycle[]
      },
      async remove(poolKey: string) {
        const tx = db.transaction("coverageCycles", "readwrite")
        tx.objectStore("coverageCycles").delete(poolKey)
        await transactionDone(tx)
      },
    },
    activeRound: {
      async get(): Promise<ActiveRound | undefined> {
        const tx = db.transaction("activeRound", "readonly")
        const row = await requestResult(
          tx.objectStore("activeRound").get("active")
        )
        await transactionDone(tx)
        return row as ActiveRound | undefined
      },
      async put(round: ActiveRound) {
        const tx = db.transaction("activeRound", "readwrite")
        tx.objectStore("activeRound").put(round)
        await transactionDone(tx)
      },
      async clear() {
        const tx = db.transaction("activeRound", "readwrite")
        tx.objectStore("activeRound").delete("active")
        await transactionDone(tx)
      },
    },
    settings: {
      async get<T>(key: string, fallback: T): Promise<T> {
        const tx = db.transaction("settings", "readonly")
        const row = await requestResult(tx.objectStore("settings").get(key))
        await transactionDone(tx)
        return row ? ((row as StoredSetting).value as T) : fallback
      },
      async put(key: string, value: unknown) {
        const tx = db.transaction("settings", "readwrite")
        tx.objectStore("settings").put({ key, value } satisfies StoredSetting)
        await transactionDone(tx)
      },
    },
  }
}
