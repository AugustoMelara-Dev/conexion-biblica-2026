import { beforeEach, describe, expect, it } from "vitest"
import { openAppDb, createRepositories, deleteAppDb, DB_NAME } from "@/storage/db"
import type { ActiveRound, Bank, CoverageCycle, Question, Session } from "@/domain/types"

const question: Question = {
  id: "D03-0001",
  bankId: "bank-1",
  bankProfileId: "legacy-v1",
  type: "single_choice",
  difficulty: 2,
  source: { work: "Daniel", version: "RVR95", chapter: 3, reference: "Daniel 3:1" },
  tags: ["detalle"],
  factKey: "fact-1",
  question: "¿Pregunta?",
  options: [{ id: "A", text: "Sí" }, { id: "B", text: "No" }],
  correctAnswer: ["A"],
}

const bank: Bank = {
  bankId: "bank-1",
  bankProfileId: "legacy-v1",
  name: "Banco de prueba",
  sourceWork: "Daniel",
  sourceVersion: "RVR95",
  schemaVersion: "1.0",
  importedAt: 1,
  fingerprint: "fingerprint-1",
  questions: [question],
}

beforeEach(async () => {
  await deleteAppDb()
})

describe("repositorios IndexedDB", () => {
  it("guarda y consulta bancos y preguntas sin mezclar el progreso", async () => {
    const db = await openAppDb()
    const repositories = createRepositories(db)
    await repositories.banks.save(bank)
    expect(await repositories.banks.list()).toHaveLength(1)
    expect(await repositories.questions.list()).toEqual([question])

    await repositories.progress.put({
      questionKey: "bank-1:D03-0001",
      timesSeen: 1,
      timesCorrect: 1,
      timesIncorrect: 0,
      timesUnanswered: 0,
      currentCorrectStreak: 1,
      averageResponseTimeMs: 2000,
      bestResponseTimeMs: 2000,
      lastResponseTimeMs: 2000,
      lastSeenAt: 100,
      masteryScore: 1,
      favorite: false,
      markedDifficult: false,
      reported: false,
      history: [],
    })
    expect(await repositories.progress.get("bank-1:D03-0001")).toMatchObject({ timesCorrect: 1 })
    expect(await repositories.banks.list()).toHaveLength(1)
  })

  it("persiste sesiones y las devuelve ordenadas de reciente a antigua", async () => {
    const db = await openAppDb()
    const repositories = createRepositories(db)
    const session = (id: string, startedAt: number): Session => ({
      id,
      startedAt,
      completedAt: startedAt + 100,
      mode: "training",
      config: {
        mode: "training",
        count: 1,
        sourceWorks: ["Daniel"],
        chapters: [3],
        difficulties: [1, 2, 3, 4, 5],
        types: ["single_choice"],
        statuses: ["all"],
        shuffleQuestions: true,
        shuffleOptions: true,
        perQuestionSeconds: null,
        totalSeconds: null,
      },
      questionKeys: [],
      answers: [],
      score: 0,
      durationMs: 100,
    })
    await repositories.sessions.add(session("old", 1))
    await repositories.sessions.add(session("new", 2))
    expect((await repositories.sessions.list()).map((item) => item.id)).toEqual(["new", "old"])
  })

  it("persiste ciclos de cobertura y una ronda activa exacta", async () => {
    const db = await openAppDb()
    const repositories = createRepositories(db)
    const cycle: CoverageCycle = {
      poolKey: "pool-a", cycleId: "cycle-1", remainingQuestionKeys: ["bank-1:D03-0002"],
      seenQuestionKeys: ["bank-1:D03-0001"], totalPoolSize: 2, createdAt: 1, updatedAt: 2,
    }
    const activeRound: ActiveRound = {
      id: "active", startedAt: 10, updatedAt: 20, currentIndex: 1,
      questionKeys: ["bank-1:D03-0001", "bank-1:D03-0002"], answers: [],
      config: {
        mode: "training", count: 2, sourceWorks: ["Daniel"], chapters: [3], difficulties: [1, 2, 3, 4, 5],
        types: ["single_choice"], statuses: ["all"], shuffleQuestions: true, shuffleOptions: true,
        perQuestionSeconds: null, totalSeconds: null, bankSelection: "legacy-v1", strategy: "coverage-cycle",
      },
    }

    await repositories.coverage.put(cycle)
    await repositories.activeRound.put(activeRound)
    expect(await repositories.coverage.get("pool-a")).toEqual(cycle)
    expect(await repositories.activeRound.get()).toEqual(activeRound)

    await repositories.activeRound.clear()
    expect(await repositories.activeRound.get()).toBeUndefined()
  })

  it("migra progreso V1 sin namespace al actualizar la DB sin borrar datos", async () => {
    await deleteAppDb()
    await new Promise<void>((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1)
      request.onupgradeneeded = () => request.result.createObjectStore("progress", { keyPath: "questionKey" })
      request.onsuccess = () => {
        const db = request.result
        const tx = db.transaction("progress", "readwrite")
        tx.objectStore("progress").put({
          questionKey: "D03-legacy", timesSeen: 1, timesCorrect: 1, timesIncorrect: 0, timesUnanswered: 0,
          currentCorrectStreak: 1, averageResponseTimeMs: 10, bestResponseTimeMs: 10,
          lastResponseTimeMs: 10, lastSeenAt: 1, masteryScore: 1, favorite: false,
          markedDifficult: false, reported: false, history: [],
        })
        tx.oncomplete = () => { db.close(); resolve() }
        tx.onerror = () => reject(tx.error)
      }
      request.onerror = () => reject(request.error)
    })

    const db = await openAppDb()
    const progress = await createRepositories(db).progress.list()
    expect(progress.map((item) => item.questionKey)).toEqual(["legacy-v1:D03-legacy"])
  })
})
