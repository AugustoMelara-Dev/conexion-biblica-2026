import { beforeEach, describe, expect, it } from "vitest"
import { openAppDb, createRepositories, deleteAppDb, DB_NAME, DB_VERSION } from "@/storage/db"
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
  it("crea índices masivos y consulta un subconjunto sin cargar toda la tienda", async () => {
    expect(DB_VERSION).toBeGreaterThanOrEqual(4)
    const db = await openAppDb()
    const repositories = createRepositories(db)
    const massiveQuestions: Question[] = Array.from({ length: 6 }, (_, index) => ({
      ...question,
      id: `D07-${index + 1}`,
      bankId: "massive-v5",
      bankProfileId: "massive-v5",
      factKey: `DAN7-V01-F${index + 1}`,
      factId: `DAN7-V01-F${index + 1}`,
      variantId: `variant-${index + 1}`,
      templateId: "mc-contextual-v1",
      blindFinalPool: index === 5,
      source: { ...question.source, chapter: 7, reference: `Daniel 7:${index + 1}` },
      difficultyBand: index < 3 ? "HARD" : "EXPERT",
    }))
    await repositories.questions.putMany(massiveQuestions)
    const selected = await repositories.questions.listForSession({
      bankId: "massive-v5",
      chapters: [7],
      difficultyBands: ["EXPERT"],
      includeBlind: false,
      limit: 2,
    })
    expect(selected).toHaveLength(2)
    expect(selected.every((item) => item.difficultyBand === "EXPERT" && !item.blindFinalPool)).toBe(true)
    const tx = db.transaction("questions", "readonly")
    const indexes = Array.from(tx.objectStore("questions").indexNames)
    expect(indexes).toEqual(expect.arrayContaining(["factId", "difficultyBand", "type", "blindFinalPool"]))
  })

  it("crea stores de consolidación sin eliminar el historial existente", async () => {
    const db = await openAppDb()
    expect(Array.from(db.objectStoreNames)).toEqual(expect.arrayContaining([
      "factMastery",
      "legacyEvents",
      "migrationBackups",
      "missionPlan",
      "blindUsage",
      "progress",
      "sessions",
    ]))
    const masteryIndexes = Array.from(
      db.transaction("factMastery", "readonly").objectStore("factMastery").indexNames,
    )
    expect(masteryIndexes).toEqual(expect.arrayContaining(["state", "nextDueAt", "chapter"]))
  })

  it("acumula exposición por hecho y variante", async () => {
    const db = await openAppDb()
    const repositories = createRepositories(db)
    await repositories.exposures.record({
      factId: "DAN7-V01-F01",
      variantId: "variant-1",
      questionKey: "massive-v5:D07-1",
      timestamp: 100,
      isCorrect: false,
      responseTimeMs: 8000,
      selectedAnswer: "B",
      errorType: "context-confusion",
      exposureKind: "cold",
    })
    await repositories.exposures.record({
      factId: "DAN7-V01-F01",
      variantId: "variant-1",
      questionKey: "massive-v5:D07-1",
      timestamp: 200,
      isCorrect: true,
      responseTimeMs: 3000,
      selectedAnswer: "A",
      errorType: null,
      exposureKind: "deferred",
    })
    expect(await repositories.exposures.get("DAN7-V01-F01", "variant-1")).toMatchObject({
      exposures: 2,
      correct: 1,
      incorrect: 1,
      lastSeenAt: 200,
      lastSelectedAnswer: "A",
      evidence: {
        cold: { attempts: 1, correct: 0 },
        deferred: { attempts: 1, correct: 1 },
      },
    })
  })

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
