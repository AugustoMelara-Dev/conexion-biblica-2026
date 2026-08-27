import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { applyProgress } from "@/domain/mastery"
import { applyFactEvidence, emptyFactMastery, type EvidenceKind, type FactMastery } from "@/domain/fact-mastery"
import { scheduleNextRetrieval } from "@/domain/compressed-scheduler"
import {
  createBackupPayload,
  migrateBackupPayload,
  validateBackupPayload,
} from "@/domain/backup"
import {
  filterReportsForSelection,
  filterSessionsForSelection,
  questionBelongsToSelection,
} from "@/domain/banks"
import { validateBank } from "@/domain/validation"
import type {
  ActiveRound,
  AnswerValue,
  Bank,
  BankProfileId,
  BackupPayload,
  BankSelection,
  CoverageCycle,
  EvaluationResult,
  Preferences,
  Question,
  QuestionExposure,
  QuestionProgress,
  QuestionReport,
  Session,
} from "@/domain/types"
import { buildStatistics, type Statistics } from "@/lib/statistics"
import { openAppDb, createRepositories } from "@/storage/db"
import {
  createBankFromRaw,
  getBankIdForSourceFileName,
  getBankQuestionKey,
  getRawBankProfileId,
  isGenericBankImportAllowed,
  isIntegratedBankProfile,
} from "@/storage/seed"
import {
  loadMassiveQuestionPool,
  type MassiveBankManifest,
} from "@/storage/massive-bank"
import {
  loadConsolidationQuestionPool,
  type ConsolidationManifest,
} from "@/storage/consolidation-bank"
import { mapLegacyProgressToFacts } from "@/storage/history-migration"
import {
  loadFinalQuestionPool,
  readFinalManifest,
  type FinalBankManifest,
} from "@/storage/final-bank"

type RepositorySet = ReturnType<typeof createRepositories>
type NavKey =
  "dashboard" | "banks" | "practice" | "stats" | "history" | "review"

export type ImportOutcome = {
  sourceName: string
  valid: boolean
  questionCount: number
  errors: { code: string; path: string; message: string; questionId?: string }[]
  bank?: Bank
}

type AppContextValue = {
  loading: boolean
  error: string | null
  masterBankError: string | null
  massiveBankError: string | null
  nav: NavKey
  setNav: (nav: NavKey) => void
  banks: Bank[]
  questions: Question[]
  allQuestions: Question[]
  progress: Map<string, QuestionProgress>
  sessions: Session[]
  reports: QuestionReport[]
  exposures: QuestionExposure[]
  factMastery?: FactMastery[]
  massiveManifest: MassiveBankManifest | null
  consolidationManifest?: ConsolidationManifest | null
  finalManifest?: FinalBankManifest | null
  preferences: Preferences
  bankSelection: BankSelection
  setBankSelection: (selection: BankSelection) => void
  bankCounts: { legacy: number; master: number; prep: number; curated: number; consolidation?: number; final?: number }
  coverageCycles: Map<string, CoverageCycle>
  activeRound: ActiveRound | null
  statistics: Statistics
  refresh: () => Promise<void>
  loadMassiveQuestions: (config: import("@/domain/types").SessionConfig) => Promise<Question[]>
  importBankFiles: (
    files: File[],
    replaceBankId?: string
  ) => Promise<ImportOutcome[]>
  removeBank: (bankId: string) => Promise<void>
  recordAnswer: (
    question: Question,
    result: EvaluationResult,
    answer: AnswerValue,
    flags?: {
      favorite?: boolean
      markedDifficult?: boolean
      context?: "practice" | "simulation"
      afterFeedback?: boolean
      hintUsed?: boolean
      sessionId?: string
      exposureKind?: EvidenceKind
    }
  ) => Promise<QuestionProgress>
  recordReport: (
    question: Question,
    answer: AnswerValue,
    result: EvaluationResult | null,
    reason: string
  ) => Promise<void>
  saveSession: (session: Session) => Promise<void>
  saveCoverageCycle: (cycle: CoverageCycle) => Promise<void>
  saveActiveRound: (round: ActiveRound) => Promise<void>
  clearActiveRound: () => Promise<void>
  exportBanks: () => Promise<Bank[]>
  exportProgress: () => Promise<QuestionProgress[]>
  exportBackup: () => Promise<BackupPayload>
  importBackup: (file: File) => Promise<{
    valid: boolean
    errors: { code: string; path: string; message: string }[]
  }>
  setPreferences: (next: Partial<Preferences>) => void
  repositories: RepositorySet | null
}

const defaultPreferences: Preferences = {
  theme: "system",
  lastMode: "training",
  reducedMotion: false,
  lastBankSelection: "final-v7",
}
const AppContext = createContext<AppContextValue | undefined>(undefined)
const PREFERENCES_STORAGE_KEY = "conexion-biblica-preferences"

function emptyQuestionProgress(questionKey: string): QuestionProgress {
  return {
    questionKey,
    timesSeen: 0,
    timesCorrect: 0,
    timesIncorrect: 0,
    timesUnanswered: 0,
    currentCorrectStreak: 0,
    averageResponseTimeMs: 0,
    bestResponseTimeMs: null,
    lastResponseTimeMs: null,
    lastSeenAt: null,
    masteryScore: 0,
    favorite: false,
    markedDifficult: false,
    reported: false,
    history: [],
  }
}

function normalizePreferences(value: Partial<Preferences>): Preferences {
  return {
    ...defaultPreferences,
    ...value,
    lastBankSelection: "final-v7",
  }
}

export function getPreferences(): Preferences {
  try {
    const raw = localStorage.getItem(PREFERENCES_STORAGE_KEY)
    if (!raw) return defaultPreferences
    const parsed = JSON.parse(raw) as unknown
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
      return defaultPreferences
    return normalizePreferences(parsed as Partial<Preferences>)
  } catch {
    return defaultPreferences
  }
}

export function resolveAvailableBankSelection(
  selection: BankSelection,
  availableProfiles: Iterable<BankProfileId>
): BankSelection {
  const available = new Set(availableProfiles)
  if (available.has("final-v7")) return "final-v7"
  if (selection === "mixed") {
    if (
      (["legacy-v1", "prep-v3", "curated-v4"] as const).some((profile) =>
        available.has(profile)
      )
    )
      return selection
  } else if (available.has(selection)) {
    return selection
  }
  for (const fallback of ["legacy-v1", "prep-v3", "master-v2"] as const) {
    if (available.has(fallback)) return fallback
  }
  return selection
}

export function resolveInitialBankSelection({
  storedSelection,
  hasStoredPreferences,
  hadExistingBanks,
  availableProfiles,
}: {
  storedSelection: BankSelection
  hasStoredPreferences: boolean
  hadExistingBanks: boolean
  availableProfiles: Iterable<BankProfileId>
}): BankSelection {
  const available = new Set(availableProfiles)
  if (available.has("final-v7")) return "final-v7"
  if (available.has("consolidation-v5")) return "consolidation-v5"
  if (!hasStoredPreferences && !hadExistingBanks && available.has("curated-v4"))
    return "curated-v4"
  return resolveAvailableBankSelection(storedSelection, available)
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [masterBankError, setMasterBankError] = useState<string | null>(null)
  const [massiveBankError, setMassiveBankError] = useState<string | null>(null)
  const [massiveManifest] =
    useState<MassiveBankManifest | null>(null)
  const [consolidationManifest] =
    useState<ConsolidationManifest | null>(null)
  const [finalManifest, setFinalManifest] =
    useState<FinalBankManifest | null>(null)
  const [nav, setNav] = useState<NavKey>("dashboard")
  const [banks, setBanks] = useState<Bank[]>([])
  const [questions, setQuestions] = useState<Question[]>([])
  const [progress, setProgress] = useState<Map<string, QuestionProgress>>(
    new Map()
  )
  const [sessions, setSessions] = useState<Session[]>([])
  const [reports, setReports] = useState<QuestionReport[]>([])
  const [exposures, setExposures] = useState<QuestionExposure[]>([])
  const [factMastery, setFactMastery] = useState<FactMastery[]>([])
  const [coverageCycles, setCoverageCycles] = useState<
    Map<string, CoverageCycle>
  >(new Map())
  const [activeRound, setActiveRound] = useState<ActiveRound | null>(null)
  const [preferences, setPreferencesState] =
    useState<Preferences>(getPreferences)
  const [repositories, setRepositories] = useState<RepositorySet | null>(null)

  const loadState = useCallback(async () => {
    setLoading(true)
    setError(null)
    setMasterBankError(null)
    setMassiveBankError(null)
    try {
      let loadedFinalManifest: FinalBankManifest | null = null
      const db = await openAppDb()
      const nextRepositories = createRepositories(db)
      setRepositories(nextRepositories)
      const existingBanks = await nextRepositories.banks.list()
      const hadStoredPreferences =
        typeof localStorage !== "undefined" &&
        localStorage.getItem(PREFERENCES_STORAGE_KEY) !== null
      const hadExistingBanks = existingBanks.length > 0
      try {
        loadedFinalManifest = await readFinalManifest()
        setFinalManifest(loadedFinalManifest)
      } catch (finalError) {
        setFinalManifest(null)
        setMassiveBankError(
          finalError instanceof Error
            ? finalError.message
            : "El Banco Maestro Único no pudo cargarse"
        )
      }
      const [
        nextQuestions,
        nextProgress,
        nextSessions,
        nextReports,
        nextCycles,
        nextActiveRound,
        nextExposures,
        nextFactMastery,
      ] = await Promise.all([
        nextRepositories.questions.list(),
        nextRepositories.progress.list(),
        nextRepositories.sessions.list(),
        nextRepositories.reports.list(),
        nextRepositories.coverage.list(),
        nextRepositories.activeRound.get(),
        nextRepositories.exposures.list(),
        nextRepositories.factMastery.list(),
      ])
      const availableProfiles = new Set<BankProfileId>(
        nextQuestions.map((question) => question.bankProfileId ?? "legacy-v1")
      )
      if (loadedFinalManifest) availableProfiles.add("final-v7")
      const storedSelection = getPreferences().lastBankSelection
      const desiredSelection = resolveInitialBankSelection({
        storedSelection,
        hasStoredPreferences: hadStoredPreferences,
        hadExistingBanks,
        availableProfiles,
      })
      if (desiredSelection !== storedSelection) {
        const updatedPreferences = {
          ...getPreferences(),
          lastBankSelection: desiredSelection,
        }
        setPreferencesState(updatedPreferences)
        localStorage.setItem(
          PREFERENCES_STORAGE_KEY,
          JSON.stringify(updatedPreferences)
        )
      }
      setBanks(existingBanks)
      setQuestions(nextQuestions)
      setProgress(new Map(nextProgress.map((item) => [item.questionKey, item])))
      setSessions(nextSessions)
      setReports(nextReports)
      setExposures(nextExposures)
      setFactMastery(nextFactMastery)
      setCoverageCycles(
        new Map(nextCycles.map((cycle) => [cycle.poolKey, cycle]))
      )
      setActiveRound(nextActiveRound ?? null)
      const existingMigration = await nextRepositories.settings.get<string | null>("v7-history-backup", null)
      if (!existingMigration && (nextProgress.length || nextSessions.length || nextReports.length)) {
        const backupId = `pre-v7-${Date.now()}`
        await nextRepositories.migrationBackups.put({
          id: backupId,
          createdAt: Date.now(),
          progress: nextProgress,
          sessions: nextSessions,
          reports: nextReports,
        })
        await nextRepositories.settings.put("v7-history-backup", backupId)
      }
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "No se pudo abrir el almacenamiento local"
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadState()
  }, [loadState])

  const refresh = useCallback(() => loadState(), [loadState])

  const loadMassiveQuestions = useCallback(
    async (config: import("@/domain/types").SessionConfig) => {
      if (!repositories)
        throw new Error("El almacenamiento todavía no está disponible")
      const desiredCount = config.count === "all" ? 200 : config.count
      if (config.bankSelection === "final-v7") {
        if (!finalManifest)
          throw new Error("El Banco Maestro Único todavía no está disponible")
        const works = new Set(config.sourceWorks)
        const manifestChapters = finalManifest.shards
          .filter((shard) =>
            shard.chapter.startsWith("DAN")
              ? works.has("Daniel")
              : works.has("Profetas y Reyes")
          )
          .map((shard) => Number(shard.chapter.match(/\d+/)?.[0]))
        const chapters = config.chapters.length
          ? manifestChapters.filter((chapter) => config.chapters.includes(chapter))
          : manifestChapters
        const blindPool = config.trainingPresetId?.endsWith("blind-a")
          ? "A" as const
          : config.trainingPresetId?.endsWith("blind-b")
            ? "B" as const
            : config.trainingPresetId === "blind-simulation"
              ? "A" as const
              : undefined
        const gold = await loadFinalQuestionPool({
          manifest: finalManifest,
          chapters,
          count: desiredCount,
          blindPool,
          difficultyBands: config.difficultyBands,
          types: config.types,
          family: config.trainingPresetId === "27-context" || config.trainingPresetId === "contextual-traps"
            ? "single_choice_contextual"
            : config.trainingPresetId === "expert-multiple-choice"
              ? "single_choice_direct"
            : config.trainingPresetId === "27-fill"
              ? "fill_choice"
              : config.trainingPresetId === "27-true-false"
                ? "true_false"
                : undefined,
          seed: Date.now(),
        })
        await repositories.questions.putMany(gold)
        const [storedQuestions, storedProgress] = await Promise.all([
          repositories.questions.list(),
          repositories.progress.list(),
        ])
        const legacyQuestions = storedQuestions.filter(
          (question) => question.bankProfileId !== "final-v7"
        )
        const migration = mapLegacyProgressToFacts(
          legacyQuestions,
          storedProgress,
          gold,
        )
        for (const item of migration.mapped) {
          const existing = await repositories.factMastery.get(item.factId)
          if (existing) continue
          const prior = emptyFactMastery(item.factId)
          await repositories.factMastery.put({
            ...prior,
            state: item.progress.timesIncorrect > 0
              ? "due"
              : item.progress.timesCorrect > 0
                ? "exposed"
                : "unseen",
            attempts: item.progress.timesSeen,
            failures: item.progress.timesIncorrect,
            firstSeenAt:
              item.progress.history.at(0)?.timestamp ?? item.progress.lastSeenAt,
            lastSeenAt: item.progress.lastSeenAt,
          })
        }
        await repositories.legacyEvents.putMany(migration.legacy)
        await repositories.settings.put("v7-history-migration-summary", {
          mapped: migration.mapped.length,
          preservedLegacy: migration.legacy.length,
          updatedAt: Date.now(),
        })
        setQuestions((current) => {
          const byKey = new Map(
            current.map((question) => [
              `${question.bankId ?? "local"}:${question.id}`,
              question,
            ])
          )
          for (const question of gold)
            byKey.set(`${question.bankId}:${question.id}`, question)
          return [...byKey.values()]
        })
        return gold
      }
      if (config.bankSelection === "consolidation-v5") {
        if (!consolidationManifest)
          throw new Error("El banco GOLD todavía no está disponible")
        const works = new Set(config.sourceWorks)
        const manifestChapters = consolidationManifest.shards
          .filter((shard) =>
            shard.chapter.startsWith("DAN")
              ? works.has("Daniel")
              : works.has("Profetas y Reyes")
          )
          .map((shard) => Number(shard.chapter.match(/\d+/)?.[0]))
        const chapters = config.chapters.length
          ? manifestChapters.filter((chapter) => config.chapters.includes(chapter))
          : manifestChapters
        const blindPool = config.trainingPresetId === "28-blind-a"
          ? "A" as const
          : config.trainingPresetId === "28-blind-b"
            ? "B" as const
            : config.trainingPresetId === "blind-simulation"
              ? "A" as const
            : undefined
        const gold = await loadConsolidationQuestionPool({
          manifest: consolidationManifest,
          chapters,
          count: desiredCount,
          blindPool,
          difficultyBands: config.difficultyBands,
          types: config.types,
          seed: Date.now(),
        })
        await repositories.questions.putMany(gold)
        const [storedQuestions, storedProgress] = await Promise.all([
          repositories.questions.list(),
          repositories.progress.list(),
        ])
        const legacyQuestions = storedQuestions.filter((question) => question.bankProfileId !== "consolidation-v5")
        const migration = mapLegacyProgressToFacts(legacyQuestions, storedProgress, gold)
        for (const item of migration.mapped) {
          const existing = await repositories.factMastery.get(item.factId)
          if (existing) continue
          const prior = emptyFactMastery(item.factId)
          await repositories.factMastery.put({
            ...prior,
            state: item.progress.timesIncorrect > 0 ? "due" : item.progress.timesCorrect > 0 ? "exposed" : "unseen",
            attempts: item.progress.timesSeen,
            failures: item.progress.timesIncorrect,
            firstSeenAt: item.progress.history.at(0)?.timestamp ?? item.progress.lastSeenAt,
            lastSeenAt: item.progress.lastSeenAt,
          })
        }
        await repositories.legacyEvents.putMany(migration.legacy)
        await repositories.settings.put("v5-history-migration-summary", {
          mapped: migration.mapped.length,
          preservedLegacy: migration.legacy.length,
          updatedAt: Date.now(),
        })
        setQuestions((current) => {
          const byKey = new Map(current.map((question) => [`${question.bankId ?? "local"}:${question.id}`, question]))
          for (const question of gold) byKey.set(`${question.bankId}:${question.id}`, question)
          return [...byKey.values()]
        })
        return gold
      }
      if (!massiveManifest)
        throw new Error("El banco masivo todavía no está disponible")
      const allowedBanks = new Set<"DANIEL1-12" | "PR39-44">(
        config.sourceWorks.map((work) =>
          work === "Daniel" ? "DANIEL1-12" : "PR39-44"
        )
      )
      const manifestChapters = massiveManifest.shards
        .filter((shard) => allowedBanks.has(shard.bank))
        .map((shard) => Number(shard.chapter.match(/\d+/)?.[0]))
        .filter(Number.isFinite)
      const chapters = config.chapters.length
        ? manifestChapters.filter((chapter) => config.chapters.includes(chapter))
        : manifestChapters
      const questions = await loadMassiveQuestionPool({
        manifest: massiveManifest,
        chapters,
        count: desiredCount,
        includeBlind: Boolean(config.includeBlind),
        blindOnly: config.trainingPresetId === "blind-simulation",
        contextualOnly: config.trainingPresetId === "contextual-traps",
        sequenceOnly: config.trainingPresetId === "order-sequence",
        types: config.types,
        difficultyBands: config.difficultyBands,
        seed: Date.now(),
      })
      await repositories.questions.putMany(questions)
      setQuestions((current) => {
        const byKey = new Map(
          current.map((question) => [
            `${question.bankId ?? "local"}:${question.id}`,
            question,
          ])
        )
        for (const question of questions)
          byKey.set(`${question.bankId ?? "local"}:${question.id}`, question)
        return [...byKey.values()]
      })
      return questions
    },
    [consolidationManifest, finalManifest, massiveManifest, repositories]
  )

  const importBankFiles = useCallback(
    async (files: File[], replaceBankId?: string) => {
      if (!repositories) return []
      const outcomes: ImportOutcome[] = []
      for (const file of files) {
        try {
          const raw = JSON.parse(await file.text()) as Record<string, unknown>
          const rawProfileId = getRawBankProfileId(raw)
          const incomingBankId = getBankIdForSourceFileName(file.name)
          const replacementId =
            replaceBankId && files.length === 1 ? replaceBankId : incomingBankId
          const replacementProfileId = banks.find(
            (bank) => bank.bankId === replacementId
          )?.bankProfileId
          if (
            !isGenericBankImportAllowed(
              rawProfileId,
              replacementId,
              replacementProfileId
            )
          ) {
            outcomes.push({
              sourceName: file.name,
              valid: false,
              questionCount: Array.isArray(raw.questions)
                ? raw.questions.length
                : 0,
              errors: [
                {
                  code: "INTEGRATED_PROFILE_IMPORT_BLOCKED",
                  path: isIntegratedBankProfile(rawProfileId)
                    ? "$.bank.profileId"
                    : "$.replaceBankId",
                  message: isIntegratedBankProfile(rawProfileId)
                    ? "Los perfiles integrados V2, V3 y V4 sólo pueden cargarse desde el paquete de la aplicación."
                    : "No se puede sobrescribir un banco integrado.",
                },
              ],
            })
            continue
          }
          const validation = validateBank(raw, file.name)
          if (!validation.valid) {
            outcomes.push({
              sourceName: file.name,
              valid: false,
              questionCount: validation.questionCount,
              errors: validation.errors,
            })
            continue
          }
          const originalBank = createBankFromRaw(raw, file.name)
          const bank =
            replaceBankId && files.length === 1
              ? {
                  ...originalBank,
                  bankId: replaceBankId,
                  questions: originalBank.questions.map((question) => ({
                    ...question,
                    bankId: replaceBankId,
                  })),
                }
              : originalBank
          await repositories.banks.save(bank)
          outcomes.push({
            sourceName: file.name,
            valid: true,
            questionCount: bank.questions.length,
            errors: [],
            bank,
          })
        } catch (importError) {
          outcomes.push({
            sourceName: file.name,
            valid: false,
            questionCount: 0,
            errors: [
              {
                code: "INVALID_JSON",
                path: "$",
                message:
                  importError instanceof Error
                    ? importError.message
                    : "JSON inválido",
              },
            ],
          })
        }
      }
      await refresh()
      return outcomes
    },
    [banks, refresh, repositories]
  )

  const removeBank = useCallback(
    async (bankId: string) => {
      if (!repositories) return
      if (
        bankId === "master-v2" ||
        banks.some(
          (bank) =>
            bank.bankId === bankId &&
            (bank.bankProfileId === "prep-v3" ||
              bank.bankProfileId === "curated-v4")
        )
      )
        return
      await repositories.banks.remove(bankId)
      await refresh()
    },
    [banks, refresh, repositories]
  )

  const recordAnswer = useCallback(
    async (
      question: Question,
      result: EvaluationResult,
      answer: AnswerValue,
      flags: {
        favorite?: boolean
        markedDifficult?: boolean
        context?: "practice" | "simulation"
        afterFeedback?: boolean
        hintUsed?: boolean
        sessionId?: string
        exposureKind?: EvidenceKind
      } = {}
    ) => {
      if (!repositories)
        throw new Error("El almacenamiento local aún no está listo")
      const key = getBankQuestionKey(question.bankId ?? "local", question.id)
      const next = await repositories.progress.update(key, (previous) => {
        const updated = applyProgress(
          previous,
          result,
          Date.now(),
          flags.context ?? "practice"
        )
        updated.questionKey = key
        if (flags.favorite !== undefined) updated.favorite = flags.favorite
        if (flags.markedDifficult !== undefined)
          updated.markedDifficult = flags.markedDifficult
        return updated
      })
      setProgress((current) => new Map(current).set(key, next))
      if (question.factId && question.variantId) {
        const selectedAnswer =
          typeof answer === "string"
            ? (question.options.find((option) => option.id === answer)?.text ??
              answer)
            : Array.isArray(answer)
              ? answer.join(", ")
              : answer && typeof answer === "object"
                ? JSON.stringify(answer)
                : null
        const exposure = await repositories.exposures.record({
          factId: question.factId,
          variantId: question.variantId,
          questionKey: key,
          timestamp: Date.now(),
          isCorrect: result.isCorrect,
          responseTimeMs: result.responseTimeMs,
          selectedAnswer,
          errorType: result.isCorrect
            ? null
            : question.trapType === "true_elsewhere"
              ? "context-confusion"
              : result.reason,
          exposureKind: flags.exposureKind ?? (flags.context === "simulation" ? "cold" : "practice"),
        })
        setExposures((current) => [
          exposure,
          ...current.filter(
            (item) => item.exposureKey !== exposure.exposureKey
          ),
        ])
        const existingMastery = await repositories.factMastery.get(question.factId)
        const median = exposure.averageResponseTimeMs || 5_000
        const evidence = applyFactEvidence(existingMastery ?? emptyFactMastery(question.factId), {
          factId: question.factId,
          variantId: question.variantId,
          semanticSkill: question.semanticSkill ?? question.type,
          sessionId: flags.sessionId ?? `round:${activeRound?.startedAt ?? "legacy"}`,
          occurredAt: Date.now(),
          isCorrect: result.isCorrect,
          firstAttempt: !flags.afterFeedback,
          hintUsed: Boolean(flags.hintUsed),
          afterFeedback: Boolean(flags.afterFeedback),
          responseTimeMs: result.responseTimeMs,
          personalMedianMs: median,
          difficulty: question.difficulty,
          exposureKind: flags.exposureKind ?? (flags.context === "simulation" ? "cold" : "practice"),
        })
        const schedule = scheduleNextRetrieval({
          outcome: !result.isCorrect ? "incorrect" : flags.afterFeedback ? "repaired" : result.responseTimeMs > median * 1.4 ? "slow_correct" : "fast_correct",
          now: Date.now(),
          tier: [43, 44, 7, 8, 9, 11].includes(question.source.chapter) ? "A" : [40, 42, 10, 12].includes(question.source.chapter) ? "B" : "C",
          stage: existingMastery?.state === "repaired"
            ? "hour"
            : evidence.hasNextDayRetrieval
              ? "next_day"
              : evidence.hasSixHourRetrieval
                ? "six_hour"
                : "initial",
        })
        const scheduled = { ...evidence, nextDueAt: schedule.dueAt }
        await repositories.factMastery.put(scheduled)
        setFactMastery((current) => [scheduled, ...current.filter((item) => item.factId !== scheduled.factId)])
      }
      return next
    },
    [activeRound?.startedAt, repositories]
  )

  const recordReport = useCallback(
    async (
      question: Question,
      answer: AnswerValue,
      result: EvaluationResult | null,
      reason: string
    ) => {
      if (!repositories) return
      const key = getBankQuestionKey(question.bankId ?? "local", question.id)
      const report: QuestionReport = {
        id: `${key}:${Date.now()}`,
        questionKey: key,
        bankId: question.bankId ?? "local",
        questionId: question.id,
        question,
        reportedAt: Date.now(),
        answer,
        response: result,
        reason,
      }
      const next = await repositories.reports.addWithProgress(
        report,
        (existing) => ({
          ...(existing ?? emptyQuestionProgress(key)),
          reported: true,
        })
      )
      setProgress((current) => new Map(current).set(key, next))
      setReports((current) => [report, ...current])
    },
    [repositories]
  )

  const saveSession = useCallback(
    async (session: Session) => {
      if (!repositories) return
      await repositories.sessions.add(session)
      setSessions((current) =>
        [session, ...current.filter((item) => item.id !== session.id)].sort(
          (left, right) => right.startedAt - left.startedAt
        )
      )
    },
    [repositories]
  )

  const saveCoverageCycle = useCallback(
    async (cycle: CoverageCycle) => {
      if (!repositories) return
      await repositories.coverage.put(cycle)
      setCoverageCycles((current) => new Map(current).set(cycle.poolKey, cycle))
    },
    [repositories]
  )

  const saveActiveRound = useCallback(
    async (round: ActiveRound) => {
      if (!repositories) return
      await repositories.activeRound.put(round)
      setActiveRound(round)
    },
    [repositories]
  )

  const clearActiveRound = useCallback(async () => {
    if (!repositories) return
    await repositories.activeRound.clear()
    setActiveRound(null)
  }, [repositories])

  const exportBackup = useCallback(async () => {
    const completeBanks = banks.map((bank) => ({
      ...bank,
      questions: questions.filter(
        (question) => question.bankId === bank.bankId
      ),
    }))
    const legacyEvents = repositories ? await repositories.legacyEvents.list() : []
    return createBackupPayload({
      banks: completeBanks,
      progress: [...progress.values()],
      sessions,
      reports,
      preferences,
      coverageCycles: [...coverageCycles.values()],
      activeRound,
      factMastery,
      legacyEvents,
    })
  }, [
    activeRound,
    banks,
    coverageCycles,
    factMastery,
    preferences,
    progress,
    questions,
    reports,
    repositories,
    sessions,
  ])

  const exportBanks = useCallback(
    async () =>
      banks.map((bank) => ({
        ...bank,
        questions: questions.filter(
          (question) => question.bankId === bank.bankId
        ),
      })),
    [banks, questions]
  )
  const exportProgress = useCallback(
    async () => [...progress.values()],
    [progress]
  )

  const importBackup = useCallback(
    async (file: File) => {
      if (!repositories)
        return {
          valid: false,
          errors: [
            {
              code: "STORAGE_NOT_READY",
              path: "$",
              message: "El almacenamiento local aún no está listo.",
            },
          ],
        }
      try {
        const parsed = JSON.parse(await file.text()) as unknown
        const validation = validateBackupPayload(parsed)
        if (!validation.valid) return validation
        const payload = migrateBackupPayload(parsed)
        await repositories.resetAll()
        for (const bank of payload.banks) await repositories.banks.save(bank)
        for (const item of payload.progress)
          await repositories.progress.put(item)
        for (const item of payload.sessions)
          await repositories.sessions.add(item)
        for (const item of payload.reports) await repositories.reports.add(item)
        for (const cycle of payload.coverageCycles)
          await repositories.coverage.put(cycle)
        if (payload.activeRound)
          await repositories.activeRound.put(payload.activeRound)
        for (const item of payload.factMastery ?? [])
          await repositories.factMastery.put(item)
        await repositories.legacyEvents.putMany(payload.legacyEvents ?? [])
        setPreferencesState(payload.preferences)
        localStorage.setItem(
          "conexion-biblica-preferences",
          JSON.stringify(payload.preferences)
        )
        await loadState()
        return validation
      } catch (importError) {
        return {
          valid: false,
          errors: [
            {
              code: "INVALID_JSON",
              path: "$",
              message:
                importError instanceof Error
                  ? importError.message
                  : "Respaldo inválido.",
            },
          ],
        }
      }
    },
    [loadState, repositories]
  )

  const setPreferences = useCallback((next: Partial<Preferences>) => {
    setPreferencesState((current) => {
      const updated = {
        ...current,
        ...next,
        lastBankSelection: "final-v7" as const,
      }
      localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(updated))
      return updated
    })
  }, [])

  const bankSelection = preferences.lastBankSelection
  const setBankSelection = useCallback(
    (selection: BankSelection) => {
      void selection
      setPreferences({ lastBankSelection: "final-v7" })
    },
    [setPreferences]
  )

  const scopedQuestions = useMemo(
    () =>
      questions.filter((question) =>
        questionBelongsToSelection(question, bankSelection)
      ),
    [bankSelection, questions]
  )
  const bankCounts = useMemo(
    () => ({
      legacy: questions.filter(
        (question) => (question.bankProfileId ?? "legacy-v1") === "legacy-v1"
      ).length,
      master: questions.filter(
        (question) => question.bankProfileId === "master-v2"
      ).length,
      prep: questions.filter((question) => question.bankProfileId === "prep-v3")
        .length,
      curated: questions.filter(
        (question) => question.bankProfileId === "curated-v4"
      ).length,
      consolidation: questions.filter(
        (question) => question.bankProfileId === "consolidation-v5"
      ).length,
      final: questions.filter(
        (question) => question.bankProfileId === "final-v7"
      ).length,
    }),
    [questions]
  )
  const scopedSessions = useMemo(
    () => filterSessionsForSelection(sessions, questions, bankSelection),
    [bankSelection, questions, sessions]
  )
  const scopedReports = useMemo(
    () => filterReportsForSelection(reports, questions, bankSelection),
    [bankSelection, questions, reports]
  )
  const statistics = useMemo(
    () => buildStatistics(scopedQuestions, progress),
    [progress, scopedQuestions]
  )
  const value = useMemo<AppContextValue>(
    () => ({
      loading,
      error,
      masterBankError,
      massiveBankError,
      nav,
      setNav,
      banks,
      questions: scopedQuestions,
      allQuestions: questions,
      progress,
      sessions: scopedSessions,
      reports: scopedReports,
      exposures,
      factMastery,
      massiveManifest,
      consolidationManifest,
      finalManifest,
      preferences,
      bankSelection,
      setBankSelection,
      bankCounts,
      coverageCycles,
      activeRound,
      statistics,
      refresh,
      loadMassiveQuestions,
      importBankFiles,
      removeBank,
      recordAnswer,
      recordReport,
      saveSession,
      saveCoverageCycle,
      saveActiveRound,
      clearActiveRound,
      exportBanks,
      exportProgress,
      exportBackup,
      importBackup,
      setPreferences,
      repositories,
    }),
    [
      activeRound,
      bankCounts,
      bankSelection,
      banks,
      clearActiveRound,
      coverageCycles,
      error,
      exportBackup,
      exportBanks,
      exportProgress,
      importBackup,
      importBankFiles,
      loading,
      masterBankError,
      massiveBankError,
      massiveManifest,
      consolidationManifest,
      finalManifest,
      nav,
      preferences,
      progress,
      exposures,
      factMastery,
      questions,
      recordAnswer,
      recordReport,
      refresh,
      loadMassiveQuestions,
      removeBank,
      repositories,
      saveActiveRound,
      saveCoverageCycle,
      saveSession,
      scopedQuestions,
      scopedReports,
      scopedSessions,
      setBankSelection,
      setPreferences,
      statistics,
    ]
  )
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) throw new Error("useApp debe usarse dentro de AppProvider")
  return context
}
