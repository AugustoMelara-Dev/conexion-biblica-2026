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
import { questionBelongsToSelection } from "@/domain/banks"
import { validateBank } from "@/domain/validation"
import type {
  ActiveRound,
  AnswerValue,
  Bank,
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
import { createBankFromRaw, getBankQuestionKey } from "@/storage/seed"

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
  bankCounts: { legacy: number; master: number }
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
    flags?: { favorite?: boolean; markedDifficult?: boolean }
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
  importBackup: (
    file: File
  ) => Promise<{
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
  lastBankSelection: "legacy-v1",
}
const AppContext = createContext<AppContextValue | undefined>(undefined)

function getPreferences(): Preferences {
  try {
    const raw = localStorage.getItem("conexion-biblica-preferences")
    if (!raw) return defaultPreferences
    return { ...defaultPreferences, ...JSON.parse(raw) } as Preferences
  } catch {
    return defaultPreferences
  }
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
      if (seed) {
        try {
          const manifestResponse = await fetch("/banks/manifest.json")
          const manifest = manifestResponse.ok
            ? ((await manifestResponse.json()) as { files?: string[] })
            : { files: [] }
          const existingIds = new Set(existingBanks.map((bank) => bank.bankId))
          for (const fileName of manifest.files ?? []) {
            try {
              const bankId = `bank-${fileName
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/^-|-$/g, "")}`
              if (existingIds.has(bankId)) continue
              const raw = await readBundledBank(fileName)
              const validation = validateBank(raw, fileName)
              if (validation.valid) {
                await nextRepositories.banks.save(
                  createBankFromRaw(raw, fileName)
                )
                existingIds.add(bankId)
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
    [refresh, repositories]
  )

  const removeBank = useCallback(
    async (bankId: string) => {
      if (!repositories) return
      if (bankId === "master-v2") return
      await repositories.banks.remove(bankId)
      await refresh()
    },
    [refresh, repositories]
  )

  const recordAnswer = useCallback(
    async (
      question: Question,
      result: EvaluationResult,
      _answer: AnswerValue,
      flags: { favorite?: boolean; markedDifficult?: boolean } = {}
    ) => {
      if (!repositories)
        throw new Error("El almacenamiento local aún no está listo")
      const key = getBankQuestionKey(question.bankId ?? "local", question.id)
      const previous = progress.get(key)
      const next = applyProgress(previous, result, Date.now())
      next.questionKey = key
      if (flags.favorite !== undefined) next.favorite = flags.favorite
      if (flags.markedDifficult !== undefined)
        next.markedDifficult = flags.markedDifficult
      await repositories.progress.put(next)
      setProgress((current) => new Map(current).set(key, next))
      return next
    },
    [progress, repositories]
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
      const existing = progress.get(key)
      const next = existing
        ? { ...existing, reported: true }
        : {
            ...applyProgress(
              undefined,
              result ?? {
                isCorrect: false,
                wasAnswered: false,
                responseTimeMs: 0,
                reason: "unanswered",
              },
              Date.now()
            ),
            questionKey: key,
            reported: true,
          }
      await repositories.progress.put(next)
      setProgress((current) => new Map(current).set(key, next))
      setReports((current) => [report, ...current])
    },
    [progress, repositories]
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
      localStorage.setItem(
        "conexion-biblica-preferences",
        JSON.stringify(updated)
      )
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
    }),
    [questions]
  )
  const scopedQuestionKeys = useMemo(
    () =>
      new Set(
        scopedQuestions.map(
          (question) => `${question.bankId ?? "local"}:${question.id}`
        )
      ),
    [scopedQuestions]
  )
  const scopedSessions = useMemo(
    () =>
      bankSelection === "mixed"
        ? sessions
        : sessions.filter((session) =>
            session.questionKeys.some((key) => scopedQuestionKeys.has(key))
          ),
    [bankSelection, scopedQuestionKeys, sessions]
  )
  const scopedReports = useMemo(
    () =>
      bankSelection === "mixed"
        ? reports
        : reports.filter((report) =>
            scopedQuestionKeys.has(report.questionKey)
          ),
    [bankSelection, reports, scopedQuestionKeys]
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
