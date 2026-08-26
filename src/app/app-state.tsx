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
import {
  createBackupPayload,
  migrateBackupPayload,
  validateBackupPayload,
} from "@/domain/backup"
import { adaptMasterBank } from "@/domain/master-bank"
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
  shouldReplaceBundledBank,
} from "@/storage/seed"

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
  nav: NavKey
  setNav: (nav: NavKey) => void
  banks: Bank[]
  questions: Question[]
  allQuestions: Question[]
  progress: Map<string, QuestionProgress>
  sessions: Session[]
  reports: QuestionReport[]
  preferences: Preferences
  bankSelection: BankSelection
  setBankSelection: (selection: BankSelection) => void
  bankCounts: { legacy: number; master: number; prep: number; curated: number }
  coverageCycles: Map<string, CoverageCycle>
  activeRound: ActiveRound | null
  statistics: Statistics
  refresh: () => Promise<void>
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
  lastBankSelection: "prep-v3",
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

function isBankSelection(value: unknown): value is BankSelection {
  return (
    value === "legacy-v1" ||
    value === "master-v2" ||
    value === "prep-v3" ||
    value === "curated-v4" ||
    value === "mixed"
  )
}

function normalizePreferences(value: Partial<Preferences>): Preferences {
  return {
    ...defaultPreferences,
    ...value,
    lastBankSelection: isBankSelection(value.lastBankSelection)
      ? value.lastBankSelection
      : defaultPreferences.lastBankSelection,
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
  if (!hasStoredPreferences && !hadExistingBanks && available.has("curated-v4"))
    return "curated-v4"
  return resolveAvailableBankSelection(storedSelection, available)
}

async function readBundledBank(fileName: string) {
  const response = await fetch(`/banks/${encodeURIComponent(fileName)}`)
  if (!response.ok) throw new Error(`No se pudo leer ${fileName}`)
  return (await response.json()) as Record<string, unknown>
}

const MASTER_BANK_URL = new URL(
  "../../Banco_Maestro_CB2026.json",
  import.meta.url
).href
const MASTER_CACHE = "conexion-biblica-master-v1"

async function readMasterBank() {
  try {
    const response = await fetch(MASTER_BANK_URL)
    if (!response.ok)
      throw new Error(`No se pudo leer el Banco Maestro (${response.status})`)
    if ("caches" in globalThis) {
      const cache = await caches.open(MASTER_CACHE)
      await cache.put(MASTER_BANK_URL, response.clone())
    }
    return (await response.json()) as Record<string, unknown>
  } catch (loadError) {
    if ("caches" in globalThis) {
      const cached = await caches.match(MASTER_BANK_URL)
      if (cached) return (await cached.json()) as Record<string, unknown>
    }
    throw loadError
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [masterBankError, setMasterBankError] = useState<string | null>(null)
  const [nav, setNav] = useState<NavKey>("dashboard")
  const [banks, setBanks] = useState<Bank[]>([])
  const [questions, setQuestions] = useState<Question[]>([])
  const [progress, setProgress] = useState<Map<string, QuestionProgress>>(
    new Map()
  )
  const [sessions, setSessions] = useState<Session[]>([])
  const [reports, setReports] = useState<QuestionReport[]>([])
  const [coverageCycles, setCoverageCycles] = useState<
    Map<string, CoverageCycle>
  >(new Map())
  const [activeRound, setActiveRound] = useState<ActiveRound | null>(null)
  const [preferences, setPreferencesState] =
    useState<Preferences>(getPreferences)
  const [repositories, setRepositories] = useState<RepositorySet | null>(null)

  const loadState = useCallback(async (seed = true) => {
    setLoading(true)
    setError(null)
    setMasterBankError(null)
    try {
      const db = await openAppDb()
      const nextRepositories = createRepositories(db)
      setRepositories(nextRepositories)
      let existingBanks = await nextRepositories.banks.list()
      const hadStoredPreferences =
        typeof localStorage !== "undefined" &&
        localStorage.getItem(PREFERENCES_STORAGE_KEY) !== null
      const hadExistingBanks = existingBanks.length > 0
      if (seed) {
        try {
          const manifestResponse = await fetch("/banks/manifest.json")
          const manifest = manifestResponse.ok
            ? ((await manifestResponse.json()) as { files?: string[] })
            : { files: [] }
          for (const fileName of manifest.files ?? []) {
            try {
              const raw = await readBundledBank(fileName)
              const validation = validateBank(raw, fileName)
              if (validation.valid) {
                const incoming = createBankFromRaw(raw, fileName)
                const existing = existingBanks.find(
                  (bank) => bank.bankId === incoming.bankId
                )
                if (shouldReplaceBundledBank(existing, incoming))
                  await nextRepositories.banks.save(incoming)
              }
            } catch {
              continue
            }
          }
          existingBanks = await nextRepositories.banks.list()
        } catch (seedError) {
          if (existingBanks.length === 0)
            setError(
              seedError instanceof Error
                ? seedError.message
                : "No se pudieron cargar los bancos iniciales"
            )
        }
      }
      try {
        const masterRaw = await readMasterBank()
        const masterBank = adaptMasterBank(masterRaw)
        const existingMaster = existingBanks.find(
          (bank) => bank.bankId === "master-v2"
        )
        if (
          !existingMaster ||
          existingMaster.fingerprint !== masterBank.fingerprint
        ) {
          await nextRepositories.banks.save(masterBank)
          existingBanks = await nextRepositories.banks.list()
        }
      } catch (masterError) {
        setMasterBankError(
          masterError instanceof Error
            ? masterError.message
            : "V2 no pudo cargarse"
        )
      }
      const [
        nextQuestions,
        nextProgress,
        nextSessions,
        nextReports,
        nextCycles,
        nextActiveRound,
      ] = await Promise.all([
        nextRepositories.questions.list(),
        nextRepositories.progress.list(),
        nextRepositories.sessions.list(),
        nextRepositories.reports.list(),
        nextRepositories.coverage.list(),
        nextRepositories.activeRound.get(),
      ])
      const availableProfiles = new Set<BankProfileId>(
        nextQuestions.map((question) => question.bankProfileId ?? "legacy-v1")
      )
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
      setCoverageCycles(
        new Map(nextCycles.map((cycle) => [cycle.poolKey, cycle]))
      )
      setActiveRound(nextActiveRound ?? null)
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

  const refresh = useCallback(() => loadState(false), [loadState])

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
      _answer: AnswerValue,
      flags: {
        favorite?: boolean
        markedDifficult?: boolean
        context?: "practice" | "simulation"
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
      return next
    },
    [repositories]
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
      await repositories.reports.add(report)
      const next = await repositories.progress.update(key, (existing) => ({
        ...(existing ?? emptyQuestionProgress(key)),
        reported: true,
      }))
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
    return createBackupPayload({
      banks: completeBanks,
      progress: [...progress.values()],
      sessions,
      reports,
      preferences,
      coverageCycles: [...coverageCycles.values()],
      activeRound,
    })
  }, [
    activeRound,
    banks,
    coverageCycles,
    preferences,
    progress,
    questions,
    reports,
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
        setPreferencesState(payload.preferences)
        localStorage.setItem(
          "conexion-biblica-preferences",
          JSON.stringify(payload.preferences)
        )
        await loadState(true)
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
      const updated = { ...current, ...next }
      localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(updated))
      return updated
    })
  }, [])

  const bankSelection = preferences.lastBankSelection
  const setBankSelection = useCallback(
    (selection: BankSelection) => {
      setPreferences({ lastBankSelection: selection })
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
      nav,
      setNav,
      banks,
      questions: scopedQuestions,
      allQuestions: questions,
      progress,
      sessions: scopedSessions,
      reports: scopedReports,
      preferences,
      bankSelection,
      setBankSelection,
      bankCounts,
      coverageCycles,
      activeRound,
      statistics,
      refresh,
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
      nav,
      preferences,
      progress,
      questions,
      recordAnswer,
      recordReport,
      refresh,
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
