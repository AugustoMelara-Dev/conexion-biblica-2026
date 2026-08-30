import { act, render, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import {
  AppProvider,
  getPreferences,
  loadLegacyMigrationSnapshot,
  resolveLegacyMigration,
  resolveAvailableBankSelection,
  resolveInitialBankSelection,
  useApp,
} from "@/app/app-state"
import { selectAdaptiveSession } from "@/domain/adaptive-session"
import { emptyFactMastery } from "@/domain/fact-mastery"
import { createEmptyProgress } from "@/domain/mastery"
import type { Question, SessionConfig } from "@/domain/types"
import { createRepositories, deleteAppDb, openAppDb } from "@/storage/db"
import type {
  FinalBankManifest,
  FinalRawQuestion,
} from "@/storage/final-bank"
import {
  adaptFinalQuestion,
  finalManifestFingerprint,
} from "@/storage/final-bank"

function finalRaw(overrides: Partial<FinalRawQuestion> = {}): FinalRawQuestion {
  return {
    id: "NEW-1",
    bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
    bank_name: "Banco Maestro Único — Final 2026",
    schema_version: "9.0",
    source_unit_id: "DAN7-V1",
    fact_id: "F-NEW-1",
    variant_id: "V-NEW-1",
    template_id: "test-template",
    family: "single_choice_direct",
    chapter: "DAN7",
    reference: "Daniel 7:1",
    source_ref: "Daniel 7:1",
    verse_or_page: "Daniel 7:1",
    source_span: "span",
    source_quote: "quote",
    context_anchor: "anchor",
    topic: "topic",
    importance: "critical",
    relation_type: "direct",
    option_category: "detail",
    blind_pool: null,
    question: "¿Pregunta?",
    options: ["Sí", "No"],
    correct_option: 0,
    correct_answer: "Sí",
    accepted_answers: ["Sí"],
    answer_mode: "option_id",
    explanation: "Explicación",
    why_distractors_fail: { No: "Incorrecta" },
    trap_type: null,
    final_editorial_status: "GOLD",
    difficulty: "hard",
    ...overrides,
  }
}

describe("preferencias y fallback de perfiles", () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it("activa el Banco Maestro Único cuando no existe preferencia", () => {
    expect(getPreferences().lastBankSelection).toBe("final-v7")
  })

  it("migra una preferencia V4 guardada al banco único", () => {
    localStorage.setItem(
      "conexion-biblica-preferences",
      JSON.stringify({ lastBankSelection: "curated-v4" })
    )

    expect(getPreferences().lastBankSelection).toBe("final-v7")
  })

  it("retrocede a V1 si V4 no está disponible", () => {
    expect(resolveAvailableBankSelection("curated-v4", ["legacy-v1"])).toBe(
      "legacy-v1"
    )
  })

  it("elige el banco único siempre que su manifiesto esté disponible", () => {
    expect(
      resolveInitialBankSelection({
        storedSelection: "prep-v3",
        hasStoredPreferences: false,
        hadExistingBanks: false,
        availableProfiles: ["final-v7", "curated-v4", "prep-v3"],
      })
    ).toBe("final-v7")
  })

  it("migra también una instalación existente al banco único", () => {
    expect(
      resolveInitialBankSelection({
        storedSelection: "prep-v3",
        hasStoredPreferences: false,
        hadExistingBanks: true,
        availableProfiles: ["final-v7", "curated-v4", "prep-v3"],
      })
    ).toBe("final-v7")
  })
})

describe("persistencia concurrente de progreso", () => {
  beforeEach(async () => {
    localStorage.clear()
    await deleteAppDb()
  })

  afterEach(async () => {
    await deleteAppDb()
  })

  it("conserva contadores de respuesta y bandera de reporte para la misma pregunta", async () => {
    let context: ReturnType<typeof useApp> | undefined
    function Probe() {
      const value = useApp()
      if (!value.loading && value.repositories) context = value
      return null
    }
    render(
      <AppProvider>
        <Probe />
      </AppProvider>
    )
    await waitFor(() => expect(context).toBeDefined())
    const question: Question = {
      id: "concurrent-progress",
      bankId: "curated-v4",
      bankProfileId: "curated-v4",
      type: "single_choice",
      difficulty: 3,
      source: {
        work: "Daniel",
        version: "RVR95",
        chapter: 1,
        reference: "Daniel 1:1",
      },
      tags: [],
      factKey: "CONCURRENT-1",
      question: "¿Se preservan ambos cambios?",
      options: [{ id: "A", text: "Sí" }],
      correctAnswer: ["A"],
    }

    await act(async () => {
      await Promise.all([
        context!.recordAnswer(
          question,
          {
            isCorrect: true,
            wasAnswered: true,
            responseTimeMs: 250,
            reason: "correct",
          },
          "A"
        ),
        context!.recordReport(question, "A", null, "Ambigua"),
      ])
    })

    expect(
      await context!.repositories!.progress.get(
        "curated-v4:concurrent-progress"
      )
    ).toMatchObject({
      timesSeen: 1,
      timesCorrect: 1,
      timesIncorrect: 0,
      timesUnanswered: 0,
      reported: true,
    })
  })

  it("aborta report y flag juntos si falla el segundo write y el retry crea un solo reporte", async () => {
    let context: ReturnType<typeof useApp> | undefined
    function Probe() {
      const value = useApp()
      if (!value.loading && value.repositories) context = value
      return null
    }
    render(
      <AppProvider>
        <Probe />
      </AppProvider>
    )
    await waitFor(() => expect(context).toBeDefined())
    const question: Question = {
      id: "atomic-report",
      bankId: "curated-v4",
      bankProfileId: "curated-v4",
      type: "single_choice",
      difficulty: 3,
      source: {
        work: "Daniel",
        version: "RVR95",
        chapter: 1,
        reference: "Daniel 1:1",
      },
      tags: [],
      factKey: "ATOMIC-REPORT-1",
      question: "¿Se confirma todo o nada?",
      options: [{ id: "A", text: "Sí" }],
      correctAnswer: ["A"],
    }
    const originalPut = IDBObjectStore.prototype.put
    let failProgressWrite = true
    const put = vi
      .spyOn(IDBObjectStore.prototype, "put")
      .mockImplementation(function (this: IDBObjectStore, value, key) {
        if (this.name === "progress" && failProgressWrite) {
          failProgressWrite = false
          throw new DOMException("forced second write failure", "DataError")
        }
        return Reflect.apply(
          originalPut,
          this,
          key === undefined ? [value] : [value, key]
        ) as IDBRequest<IDBValidKey>
      })
    try {
      await expect(
        context!.recordReport(question, "A", null, "Ambigua")
      ).rejects.toBeDefined()
      expect(await context!.repositories!.reports.list()).toEqual([])
      expect(
        await context!.repositories!.progress.get("curated-v4:atomic-report")
      ).toBeUndefined()

      await act(async () => {
        await context!.recordReport(question, "A", null, "Ambigua")
      })

      expect(await context!.repositories!.reports.list()).toHaveLength(1)
      expect(
        await context!.repositories!.progress.get("curated-v4:atomic-report")
      ).toMatchObject({ reported: true, timesSeen: 0 })
    } finally {
      put.mockRestore()
    }
  })

  it("clasifica la velocidad contra el baseline previo al intento actual", async () => {
    let context: ReturnType<typeof useApp> | undefined
    function Probe() {
      const value = useApp()
      if (!value.loading && value.repositories) context = value
      return null
    }
    render(
      <AppProvider>
        <Probe />
      </AppProvider>
    )
    await waitFor(() => expect(context).toBeDefined())
    const question: Question = {
      id: "baseline-before-attempt",
      bankId: "curated-v4",
      bankProfileId: "curated-v4",
      type: "single_choice",
      difficulty: 4,
      source: {
        work: "Daniel",
        version: "RVR95",
        chapter: 7,
        reference: "Daniel 7:1",
      },
      tags: [],
      factKey: "FACT-BASELINE-1",
      factId: "FACT-BASELINE-1",
      variantId: "baseline-v1",
      question: "¿Se usa el promedio anterior?",
      options: [{ id: "A", text: "Sí" }],
      correctAnswer: ["A"],
    }
    const now = Date.UTC(2026, 7, 30, 12)
    await context!.repositories!.exposures.record({
      factId: question.factId!,
      variantId: "baseline-v0",
      questionKey: "curated-v4:baseline-previous-variant",
      timestamp: now - 1_000,
      isCorrect: true,
      responseTimeMs: 2_000,
      selectedAnswer: "Sí",
      errorType: null,
      exposureKind: "practice",
    })
    const nowSpy = vi.spyOn(Date, "now").mockReturnValue(now)
    try {
      await act(async () => {
        await context!.recordAnswer(
          question,
          {
            isCorrect: true,
            wasAnswered: true,
            responseTimeMs: 6_000,
            reason: "correct",
          },
          "A"
        )
      })
    } finally {
      nowSpy.mockRestore()
    }

    expect(
      await context!.repositories!.factMastery.get(question.factId!)
    ).toMatchObject({
      state: "fragile",
      nextDueAt: now + 4 * 3_600_000,
    })
  })

  it("carga candidatos adaptativos antes de limitar la ronda solicitada", async () => {
    const now = Date.UTC(2026, 7, 30, 12)
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 20,
      unique_facts: 20,
      shards: [
        {
          chapter: "DAN7",
          question_count: 20,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ],
    }
    const rows = [
      finalRaw(),
      ...Array.from({ length: 18 }, (_, index) =>
        finalRaw({
          id: `NEW-${index + 2}`,
          fact_id: `F-NEW-${index + 2}`,
          variant_id: `V-NEW-${index + 2}`,
        })
      ),
      finalRaw({ id: "DUE", fact_id: "F-DUE", variant_id: "V-DUE" }),
    ]
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input) =>
        ({
          ok: true,
          json: async () =>
            String(input).endsWith("manifest.json") ? manifest : rows,
        }) as Response
    )
    const repositories = createRepositories(await openAppDb())
    await repositories.exposures.record({
      factId: "F-DUE",
      variantId: "V-DUE-OLDER",
      questionKey: "BANCO_UNICO_CONEXION_BIBLICA_2026:DUE-OLDER",
      timestamp: now - 10_000,
      isCorrect: true,
      responseTimeMs: 2_000,
      selectedAnswer: "Sí",
      errorType: null,
      exposureKind: "practice",
    })
    await repositories.factMastery.put({
      ...emptyFactMastery("F-DUE"),
      state: "stable",
      attempts: 1,
      nextDueAt: now - 1,
    })

    let context: ReturnType<typeof useApp> | undefined
    function Probe() {
      const value = useApp()
      if (!value.loading && value.repositories) context = value
      return null
    }
    render(
      <AppProvider>
        <Probe />
      </AppProvider>
    )
    await waitFor(() => expect(context?.finalManifest).toEqual(manifest))
    try {
      let pool: Question[] = []
      await act(async () => {
        pool = await context!.loadMassiveQuestions({
          mode: "smart-review",
          count: 2,
          sourceWorks: ["Daniel"],
          chapters: [7],
          difficulties: [4],
          difficultyBands: ["HARD"],
          types: ["single_choice"],
          statuses: ["all"],
          shuffleQuestions: true,
          shuffleOptions: true,
          perQuestionSeconds: null,
          totalSeconds: null,
          bankSelection: "final-v7",
          strategy: "adaptive",
          trainingPresetId: "spaced-review",
          massive: true,
        })
      })
      const selected = selectAdaptiveSession({
        questions: pool,
        exposures: context!.exposures ?? [],
        factMastery: context!.factMastery ?? [],
        presetId: "spaced-review",
        now,
        count: 2,
        weakChapters: [],
        includeBlind: false,
        seed: 9,
      })

      expect(selected.map((question) => question.factId)).toEqual(["F-DUE"])
      expect(pool.length).toBeLessThanOrEqual(8)
      expect(
        (await context!.repositories!.questions.list()).length
      ).toBeLessThanOrEqual(8)
      const nothingDue = selectAdaptiveSession({
        questions: pool,
        exposures: context!.exposures ?? [],
        factMastery: [
          {
            ...emptyFactMastery("F-DUE"),
            state: "stable",
            attempts: 1,
            nextDueAt: now + 1,
          },
        ],
        presetId: "spaced-review",
        now,
        count: 2,
        weakChapters: [],
        includeBlind: false,
        seed: 9,
      })
      expect(nothingDue).toEqual([])
    } finally {
      fetchSpy.mockRestore()
    }
  })

  it("usa la migración por factId en la primera ronda sin refresh", async () => {
    const now = Date.UTC(2026, 7, 30, 12)
    const migratedRaw = finalRaw({
      id: "MIGRATED",
      fact_id: "F-MIGRATED",
      variant_id: "V-MIGRATED",
    })
    const filteredRaw = finalRaw({
      id: "FILTERED-LEGACY",
      fact_id: "F-FILTERED-LEGACY",
      variant_id: "V-FILTERED-LEGACY",
      reference: "Daniel 7:99",
      family: "true_false",
      type: "true_false",
      options: ["Verdadero", "Falso"],
    })
    const overflowRaws = Array.from({ length: 5 }, (_, index) =>
      finalRaw({
        id: `OVERFLOW-${index}`,
        fact_id: `F-OVERFLOW-${index}`,
        variant_id: `V-OVERFLOW-${index}`,
        reference: `Daniel 7:${30 + index}`,
      })
    )
    const difficultyFilteredRaw = finalRaw({
      id: "DIFFICULTY-FILTERED",
      fact_id: "F-DIFFICULTY-FILTERED",
      variant_id: "V-DIFFICULTY-FILTERED",
      reference: "Daniel 7:98",
      difficulty: "easy",
    })
    const chapterFilteredRaw = finalRaw({
      id: "CHAPTER-FILTERED",
      fact_id: "F-CHAPTER-FILTERED",
      variant_id: "V-CHAPTER-FILTERED",
      chapter: "DAN8",
      reference: "Daniel 8:1",
    })
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      build_id: "migration-test-build",
      gold_questions: 20,
      unique_facts: 20,
      shards: [
        {
          chapter: "DAN7",
          question_count: 20,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
        {
          chapter: "DAN8",
          question_count: 1,
          questions_file: "banks/final-2026/questions/DAN8.json",
        },
      ],
    }
    const rows = [
      ...Array.from({ length: 19 }, (_, index) =>
        finalRaw({
          id: `UNRELATED-${index}`,
          fact_id: `F-UNRELATED-${index}`,
          variant_id: `V-UNRELATED-${index}`,
          reference: `Daniel 7:${index + 2}`,
        })
      ),
      ...overflowRaws,
      difficultyFilteredRaw,
      filteredRaw,
      migratedRaw,
    ]
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(
      async (input) =>
        ({
          ok: true,
          json: async () =>
            String(input).endsWith("manifest.json")
              ? manifest
              : String(input).endsWith("DAN8.json")
                ? [chapterFilteredRaw]
                : rows,
        }) as Response
    )
    const repositories = createRepositories(await openAppDb())
    await repositories.factMastery.put({
      ...emptyFactMastery("F-UNRELATED-0"),
      state: "due",
      attempts: 1,
      failures: 1,
      nextDueAt: now - 1,
    })
    const legacy = {
      ...adaptFinalQuestion(migratedRaw),
      id: "legacy-migrated",
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }
    const filteredLegacy = {
      ...adaptFinalQuestion(filteredRaw),
      id: "legacy-filtered",
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }
    const overflowLegacy = overflowRaws.map((row, index) => ({
      ...adaptFinalQuestion(row),
      id: `legacy-overflow-${index}`,
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }))
    const difficultyFilteredLegacy = {
      ...adaptFinalQuestion(difficultyFilteredRaw),
      id: "legacy-difficulty-filtered",
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }
    const chapterFilteredLegacy = {
      ...adaptFinalQuestion(chapterFilteredRaw),
      id: "legacy-chapter-filtered",
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }
    const unmatchedLegacy = {
      ...adaptFinalQuestion(
        finalRaw({
          id: "UNMATCHED-LEGACY",
          fact_id: "F-UNMATCHED-LEGACY",
          variant_id: "V-UNMATCHED-LEGACY",
          reference: "Daniel 7:404",
          source_quote: "firma sin equivalente canónico",
        })
      ),
      id: "legacy-unmatched",
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }
    await repositories.questions.putMany([
      legacy,
      filteredLegacy,
      difficultyFilteredLegacy,
      chapterFilteredLegacy,
      unmatchedLegacy,
      ...overflowLegacy,
    ])
    await repositories.progress.put({
      ...createEmptyProgress("curated-v4:legacy-migrated"),
      timesSeen: 1,
      timesIncorrect: 1,
      lastSeenAt: now - 1_000,
    })
    for (let index = 0; index < overflowLegacy.length; index += 1)
      await repositories.progress.put({
        ...createEmptyProgress(`curated-v4:legacy-overflow-${index}`),
        timesSeen: 1,
        timesIncorrect: 1,
        lastSeenAt: now - 1_000,
      })
    for (const questionKey of [
      "curated-v4:legacy-difficulty-filtered",
      "curated-v4:legacy-chapter-filtered",
    ])
      await repositories.progress.put({
        ...createEmptyProgress(questionKey),
        timesSeen: 1,
        timesIncorrect: 1,
        lastSeenAt: now - 1_000,
      })
    await repositories.progress.put({
      ...createEmptyProgress("curated-v4:legacy-filtered"),
      timesSeen: 1,
      timesIncorrect: 1,
      lastSeenAt: now - 1_000,
    })
    await repositories.progress.put({
      ...createEmptyProgress("curated-v4:missing-legacy-question"),
      timesSeen: 1,
      timesIncorrect: 1,
      lastSeenAt: now - 1_000,
    })
    await repositories.progress.put({
      ...createEmptyProgress("curated-v4:legacy-unmatched"),
      timesSeen: 1,
      timesIncorrect: 1,
      lastSeenAt: now - 1_000,
    })

    let context: ReturnType<typeof useApp> | undefined
    function Probe() {
      const value = useApp()
      if (!value.loading && value.repositories) context = value
      return null
    }
    render(
      <AppProvider>
        <Probe />
      </AppProvider>
    )
    await waitFor(() => expect(context?.finalManifest).toEqual(manifest))
    const nowSpy = vi.spyOn(Date, "now").mockReturnValue(now)
    try {
      const baseConfig: SessionConfig = {
        mode: "smart-review",
        count: 1,
        sourceWorks: ["Daniel"],
        chapters: [7],
        difficulties: [4],
        difficultyBands: ["HARD"],
        types: ["single_choice"],
        statuses: ["failed"],
        shuffleQuestions: true,
        shuffleOptions: true,
        perQuestionSeconds: null,
        totalSeconds: null,
        bankSelection: "final-v7",
        strategy: "adaptive",
        trainingPresetId: "previous-errors",
        massive: true,
      }
      let pool: Question[] = []
      await act(async () => {
        pool = await context!.loadMassiveQuestions(baseConfig)
      })
      const selected = selectAdaptiveSession({
        questions: pool,
        exposures: context!.exposures ?? [],
        factMastery: context!.factMastery ?? [],
        presetId: "previous-errors",
        now,
        count: 1,
        weakChapters: [],
        includeBlind: false,
        seed: 10,
      })

      expect(selected).toHaveLength(1)
      expect(pool.map((question) => question.factId)).toContain(
        selected[0].factId
      )
      expect(context!.factMastery).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ factId: "F-MIGRATED", failures: 1 }),
        ])
      )
      const unseen = selectAdaptiveSession({
          questions: pool,
          exposures: context!.exposures ?? [],
          factMastery: context!.factMastery ?? [],
          presetId: "unseen-only",
          now,
          count: 1,
          weakChapters: [],
          includeBlind: false,
          seed: 10,
        })
      const migratedFacts = new Set(
        context!.factMastery?.map((item) => item.factId) ?? []
      )
      expect(
        unseen.every((question) => !migratedFacts.has(question.factId!))
      ).toBe(true)
      expect(
        await context!.repositories!.settings.get(
          "v7-history-migration-summary",
          null
        )
      ).toMatchObject({
        status: "complete",
        unresolved: 0,
        mapped: 9,
        preservedLegacy: 2,
        profileVersion:
          "BANCO_UNICO_CONEXION_BIBLICA_2026:9.0:build:migration-test-build",
      })
      expect(await context!.repositories!.legacyEvents.list()).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            sourceQuestionKey: "curated-v4:missing-legacy-question",
            reason: "missing_question",
          }),
          expect.objectContaining({
            sourceQuestionKey: "curated-v4:legacy-unmatched",
            reason: "no_match",
          }),
        ])
      )

      const questionsList = vi.spyOn(context!.repositories!.questions, "list")
      const progressList = vi.spyOn(context!.repositories!.progress, "list")
      await act(async () => {
        await context!.loadMassiveQuestions(baseConfig)
      })
      expect(questionsList).not.toHaveBeenCalled()
      expect(progressList).not.toHaveBeenCalled()
    } finally {
      nowSpy.mockRestore()
      fetchSpy.mockRestore()
    }
  })

  it("V5 cierra no_match terminal y luego no relee preguntas ni progreso", async () => {
    const repositories = createRepositories(await openAppDb())
    const legacy = {
      ...adaptFinalQuestion(
        finalRaw({
          id: "V5-NO-MATCH",
          reference: "Daniel 7:505",
          source_quote: "sin equivalente V5",
        })
      ),
      id: "v5-no-match",
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }
    await repositories.questions.putMany([legacy])
    await repositories.progress.put({
      ...createEmptyProgress("curated-v4:v5-no-match"),
      timesSeen: 1,
      timesIncorrect: 1,
    })
    const questionsList = vi.spyOn(repositories.questions, "list")
    const progressList = vi.spyOn(repositories.progress, "list")

    const snapshot = await loadLegacyMigrationSnapshot(
      repositories,
      "v5-history-migration-summary",
      "consolidation-v5:test"
    )
    expect(questionsList).toHaveBeenCalledTimes(1)
    expect(progressList).toHaveBeenCalledTimes(1)
    await resolveLegacyMigration({
      repositories,
      snapshot,
      bankProfileId: "consolidation-v5",
      summaryKey: "v5-history-migration-summary",
      profileVersion: "consolidation-v5:test",
      resolveSignatures: async () => new Map(),
    })
    expect(await repositories.factMastery.list()).toEqual([])
    expect(await repositories.legacyEvents.list()).toEqual([
      expect.objectContaining({ reason: "no_match" }),
    ])

    const second = await loadLegacyMigrationSnapshot(
      repositories,
      "v5-history-migration-summary",
      "consolidation-v5:test"
    )
    expect(second.complete).toBe(true)
    expect(questionsList).toHaveBeenCalledTimes(1)
    expect(progressList).toHaveBeenCalledTimes(1)
  })

  it("V7 reescanea sólo cuando cambia el build del mismo schema", async () => {
    const repositories = createRepositories(await openAppDb())
    const baseManifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      build_id: "build-a",
      gold_questions: 0,
      unique_facts: 0,
      shards: [],
    }
    const buildA = await finalManifestFingerprint(baseManifest)
    const buildB = await finalManifestFingerprint({
      ...baseManifest,
      build_id: "build-b",
    })
    await repositories.settings.put("v7-history-migration-summary", {
      status: "complete",
      profileVersion: buildA,
    })
    const questionsList = vi.spyOn(repositories.questions, "list")
    const progressList = vi.spyOn(repositories.progress, "list")

    const sameBuild = await loadLegacyMigrationSnapshot(
      repositories,
      "v7-history-migration-summary",
      buildA
    )
    expect(sameBuild.complete).toBe(true)
    expect(questionsList).not.toHaveBeenCalled()
    expect(progressList).not.toHaveBeenCalled()

    const changedBuild = await loadLegacyMigrationSnapshot(
      repositories,
      "v7-history-migration-summary",
      buildB
    )
    expect(changedBuild.complete).toBe(false)
    expect(questionsList).toHaveBeenCalledTimes(1)
    expect(progressList).toHaveBeenCalledTimes(1)
  })
})
