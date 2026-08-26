import type {
  ActiveRound,
  Bank,
  CoverageCycle,
  Question,
  QuestionProgress,
  QuestionReport,
  Session,
} from "@/domain/types"

export const DB_NAME = "conexion-biblica-2026"
export const DB_VERSION = 2

type StoredQuestion = Question & { questionKey: string }
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
    Object.entries(question).filter(([key]) => key !== "questionKey")
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
