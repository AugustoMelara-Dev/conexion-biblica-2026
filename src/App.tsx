import { useEffect, useState } from "react"
import { AlertCircle } from "lucide-react"
import { useApp } from "@/app/app-state"
import { filterQuestionsForSelection } from "@/domain/banks"
import { selectAdaptiveSession } from "@/domain/adaptive-session"
import { materializeDynamicQuestion } from "@/domain/dynamic-question"
import {
  filterEligibleQuestions,
  selectSessionQuestions,
} from "@/domain/session-selector"
import {
  buildPoolKey,
  selectBalancedRandom,
  selectCoverageCycle,
  selectSequentialBlock,
} from "@/domain/session-selection"
import type {
  ActiveRound,
  Question,
  SelectionSummary,
  Session,
  SessionConfig,
} from "@/domain/types"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { AppShell } from "@/components/app-shell"
import { BankManagerPage } from "@/components/bank-manager-page"
import { FocusShell } from "@/components/layout/focus-shell"
import { DashboardPage } from "@/components/dashboard-page"
import { HistoryPage } from "@/components/history-page"
import { QuizPage } from "@/components/quiz-page"
import { ResultsPage } from "@/components/results-page"
import { ReviewPage } from "@/components/review-page"
import { SessionBuilderPage } from "@/components/session-builder-page"
import { StatisticsPage } from "@/components/statistics-page"

type RoundView = {
  questions: Question[]
  config: SessionConfig
  persisted: ActiveRound
}

function timestamp() {
  return Date.now()
}

function reviewQueueConfig(
  questions: Question[],
  bankSelection: SessionConfig["bankSelection"]
): SessionConfig {
  return {
    mode: "smart-review",
    count: "all",
    sourceWorks: [
      ...new Set(questions.map((question) => question.source.work)),
    ],
    chapters: [],
    difficulties: [],
    types: [],
    statuses: ["all"],
    shuffleQuestions: false,
    shuffleOptions: true,
    perQuestionSeconds: null,
    totalSeconds: null,
    bankSelection,
    strategy: "adaptive",
  }
}

function questionsForSession(session: Session, questions: Question[]) {
  const byKey = new Map(
    questions.map((question) => [
      `${question.bankId ?? "local"}:${question.id}`,
      question,
    ])
  )
  return session.questionKeys
    .map((key) => byKey.get(key))
    .filter((question): question is Question => Boolean(question))
}

function shuffleExactSubset(
  questions: Question[],
  rng: () => number = Math.random
) {
  const shuffled = questions.slice()
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(rng() * (index + 1))
    const current = shuffled[index]
    shuffled[index] = shuffled[swapIndex]
    shuffled[swapIndex] = current
  }
  return shuffled
}

export function App() {
  const {
    loading,
    error,
    masterBankError,
    massiveBankError,
    nav,
    setNav,
    allQuestions,
    progress,
    exposures,
    loadMassiveQuestions,
    saveSession,
    coverageCycles,
    saveCoverageCycle,
    activeRound: storedActiveRound,
    saveActiveRound,
    clearActiveRound,
    bankSelection,
  } = useApp()
  const [activeRound, setActiveRound] = useState<RoundView | null>(null)
  const [result, setResult] = useState<Session | null>(null)

  useEffect(() => {
    if (activeRound || !storedActiveRound || allQuestions.length === 0) return
    const questionMap = new Map(
      allQuestions.map((question) => [
        `${question.bankId ?? "local"}:${question.id}`,
        question,
      ])
    )
    const selected =
      storedActiveRound.questionSnapshots?.length === storedActiveRound.questionKeys.length
        ? storedActiveRound.questionSnapshots
        : storedActiveRound.questionKeys
            .map((key) => questionMap.get(key))
            .filter((question): question is Question => Boolean(question))
    if (selected.length !== storedActiveRound.questionKeys.length) return
    setActiveRound({
      questions: selected,
      config: storedActiveRound.config,
      persisted: storedActiveRound,
    })
    setNav("practice")
  }, [activeRound, allQuestions, setNav, storedActiveRound])

  const startRound = async (
    config: SessionConfig,
    subset?: Question[],
    resetCycle = false
  ) => {
    const nextConfig: SessionConfig = {
      ...config,
      bankSelection: config.bankSelection ?? bankSelection,
      strategy:
        config.strategy ??
        (config.shuffleQuestions ? "coverage-cycle" : "sequential-blocks"),
    }
    const roundQuestions = nextConfig.massive
      ? await loadMassiveQuestions(nextConfig)
      : filterQuestionsForSelection(
          allQuestions,
          nextConfig.bankSelection ?? bankSelection
        )
    const eligible =
      subset ?? filterEligibleQuestions(roundQuestions, progress, nextConfig)
    const target =
      nextConfig.count === "all"
        ? eligible.length
        : Math.min(nextConfig.count, eligible.length)
    let selected: Question[]
    let selectionSummary: SelectionSummary = { strategy: nextConfig.strategy! }
    if (nextConfig.massive) {
      const weakChapters = [...new Set(
        roundQuestions
          .filter((question) => {
            const key = `${question.bankId ?? "local"}:${question.id}`
            return (progress.get(key)?.timesIncorrect ?? 0) > 0
          })
          .map((question) => question.source.chapter)
      )]
      const adaptive = selectAdaptiveSession({
        questions: eligible,
        exposures,
        count: target,
        weakChapters,
        includeBlind: Boolean(nextConfig.includeBlind),
        seed: timestamp(),
      })
      const exposureByFact = new Map<string, number>()
      for (const exposure of exposures)
        exposureByFact.set(
          exposure.factId,
          (exposureByFact.get(exposure.factId) ?? 0) + exposure.exposures
        )
      selected = adaptive.map((question, index) =>
        materializeDynamicQuestion(question, {
          seed: timestamp() + index,
          exposure: exposureByFact.get(question.factId ?? question.factKey) ?? 0,
        })
      )
      selectionSummary = { strategy: "adaptive" }
    } else if (subset)
      selected =
        nextConfig.strategy === "random-balanced"
          ? shuffleExactSubset(subset)
          : subset.slice()
    else if (nextConfig.strategy === "coverage-cycle") {
      const poolKey = buildPoolKey(nextConfig)
      const selection = selectCoverageCycle({
        pool: eligible,
        count: target,
        poolKey,
        cycle: coverageCycles.get(poolKey),
        reset: resetCycle,
      })
      selected = selection.questions
      await saveCoverageCycle(selection.cycle)
      selectionSummary = {
        strategy: "coverage-cycle",
        poolKey,
        cycleId: selection.cycle.cycleId,
        seen: selection.seen,
        remaining: selection.remaining,
        total: selection.total,
      }
    } else if (nextConfig.strategy === "random-balanced")
      selected = selectBalancedRandom(eligible, target)
    else if (nextConfig.strategy === "sequential-blocks")
      selected = selectSequentialBlock(
        eligible,
        target,
        nextConfig.sequentialBlock ?? 0
      ).questions
    else
      selected = selectSessionQuestions(
        roundQuestions,
        progress,
        nextConfig,
        timestamp()
      )
    if (selected.length === 0) return

    const startedAt = timestamp()
    const persisted: ActiveRound = {
      id: "active",
      startedAt,
      updatedAt: startedAt,
      currentIndex: 0,
      questionKeys: selected.map(
        (question) => `${question.bankId ?? "local"}:${question.id}`
      ),
      questionSnapshots: nextConfig.massive ? selected : undefined,
      answers: [],
      config: nextConfig,
      selectionSummary,
    }
    await saveActiveRound(persisted)
    const round: RoundView = {
      questions: selected,
      config: nextConfig,
      persisted,
    }
    setActiveRound(round)
    setResult(null)
    setNav("practice")
  }

  const finishRound = async (session: Session) => {
    const completed = {
      ...session,
      selectionSummary: activeRound?.persisted.selectionSummary,
    }
    await saveSession(completed)
    await clearActiveRound()
    setResult(completed)
    setActiveRound(null)
    setNav("dashboard")
  }

  const exitRound = async () => {
    await clearActiveRound()
    setActiveRound(null)
  }

  const renderPage = () => {
    if (result && nav === "dashboard") {
      const resultQuestions = questionsForSession(result, allQuestions)
      const errorKeys = new Set(
        result.answers
          .filter((answer) => !answer.result.isCorrect)
          .map((answer) => answer.questionKey)
      )
      const errorQuestions = resultQuestions.filter((question) =>
        errorKeys.has(`${question.bankId ?? "local"}:${question.id}`)
      )
      return (
        <ResultsPage
          session={result}
          questions={allQuestions}
          onErrors={() =>
            startRound(
              {
                ...result.config,
                mode: "errors",
                count: "all",
                statuses: ["failed"],
                strategy: "adaptive",
              },
              errorQuestions
            )
          }
          onRepeat={() => startRound(result.config, resultQuestions)}
          onNext={() =>
            startRound({ ...result.config, strategy: "coverage-cycle" })
          }
          onRandom={() =>
            startRound(
              { ...result.config, strategy: "random-balanced" },
              result.config.massive ? undefined : resultQuestions
            )
          }
          onNew={() => {
            setResult(null)
            setNav("practice")
          }}
        />
      )
    }
    if (activeRound)
      return (
        <QuizPage
          questions={activeRound.questions}
          config={activeRound.config}
          resume={activeRound.persisted}
          onStateChange={async (persisted) => {
            setActiveRound((current) =>
              current ? { ...current, persisted } : current
            )
            await saveActiveRound(persisted)
          }}
          onFinish={finishRound}
          onExit={exitRound}
        />
      )
    if (nav === "banks")
      return <BankManagerPage />
    if (nav === "practice")
      return (
        <SessionBuilderPage
          onStart={(config, resetCycle) => {
            void startRound(config, undefined, resetCycle)
          }}
        />
      )
    if (nav === "stats") return <StatisticsPage />
    if (nav === "history") return <HistoryPage />
    if (nav === "review")
      return (
        <ReviewPage
          onPracticeQueue={(queue) =>
            startRound(reviewQueueConfig(queue, bankSelection), queue)
          }
        />
      )
    return <DashboardPage onStartMission={(config) => void startRound(config)} />
  }

  if (activeRound) {
    return <FocusShell>{renderPage()}</FocusShell>
  }

  return (
    <AppShell>
      <div className="flex flex-col gap-4">
        {error ? (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertTitle>Almacenamiento local</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        {masterBankError ? (
          <Alert>
            <AlertCircle />
            <AlertTitle>Banco Maestro Único</AlertTitle>
            <AlertDescription>{masterBankError}</AlertDescription>
          </Alert>
        ) : null}
        {massiveBankError ? (
          <Alert>
            <AlertCircle />
            <AlertTitle>Banco Maestro Único</AlertTitle>
            <AlertDescription>{massiveBankError}</AlertDescription>
          </Alert>
        ) : null}
        {loading ? <LoadingState /> : renderPage()}
      </div>
    </AppShell>
  )
}

function LoadingState() {
  return (
    <section
      aria-busy="true"
      aria-label="Preparando tu banco maestro"
      className="min-w-0 space-y-8"
      role="status"
    >
      <h1 className="sr-only">Preparando tu banco maestro</h1>
      <span className="sr-only">
        Cargando preguntas y progreso desde este dispositivo.
      </span>
      <div aria-hidden="true" className="space-y-5">
        <Skeleton
          data-testid="dashboard-skeleton"
          className="h-32 rounded-2xl"
        />
        <div className="grid min-w-0 gap-4 sm:grid-cols-2">
          <Skeleton
            data-testid="dashboard-skeleton"
            className="h-44 rounded-2xl"
          />
          <Skeleton
            data-testid="dashboard-skeleton"
            className="h-44 rounded-2xl"
          />
        </div>
      </div>
    </section>
  )
}

export default App
