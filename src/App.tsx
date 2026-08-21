import { useEffect, useState } from "react"
import { AlertCircle, Database, LoaderCircle } from "lucide-react"
import { useApp } from "@/app/app-state"
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
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { AppShell } from "@/components/app-shell"
import { BankManagerPage } from "@/components/bank-manager-page"
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

export function App() {
  const {
    loading,
    error,
    masterBankError,
    nav,
    setNav,
    questions,
    progress,
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
  const [lastRound, setLastRound] = useState<RoundView | null>(null)

  useEffect(() => {
    if (activeRound || !storedActiveRound || questions.length === 0) return
    const questionMap = new Map(
      questions.map((question) => [
        `${question.bankId ?? "local"}:${question.id}`,
        question,
      ])
    )
    const selected = storedActiveRound.questionKeys
      .map((key) => questionMap.get(key))
      .filter((question): question is Question => Boolean(question))
    if (selected.length !== storedActiveRound.questionKeys.length) return
    setActiveRound({
      questions: selected,
      config: storedActiveRound.config,
      persisted: storedActiveRound,
    })
    setNav("practice")
  }, [activeRound, questions, setNav, storedActiveRound])

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
    const eligible =
      subset ?? filterEligibleQuestions(questions, progress, nextConfig)
    const target =
      nextConfig.count === "all"
        ? eligible.length
        : Math.min(nextConfig.count, eligible.length)
    let selected: Question[]
    let selectionSummary: SelectionSummary = { strategy: nextConfig.strategy! }
    if (subset) selected = subset.slice(0, target || subset.length)
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
        questions,
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
    setLastRound(round)
    setActiveRound(round)
    setResult(null)
    setNav("practice")
  }

  const finishRound = (session: Session) => {
    const completed = {
      ...session,
      selectionSummary: activeRound?.persisted.selectionSummary,
    }
    void (async () => {
      await saveSession(completed)
      await clearActiveRound()
      setResult(completed)
      setActiveRound(null)
      setNav("dashboard")
    })()
  }

  const renderPage = () => {
    if (result && nav === "dashboard") {
      const errorKeys = new Set(
        result.answers
          .filter((answer) => !answer.result.isCorrect)
          .map((answer) => answer.questionKey)
      )
      const errorQuestions = questions.filter((question) =>
        errorKeys.has(`${question.bankId ?? "local"}:${question.id}`)
      )
      return (
        <ResultsPage
          session={result}
          questions={questions}
          onErrors={() => {
            setResult(null)
            void startRound(
              {
                ...result.config,
                mode: "errors",
                count: "all",
                statuses: ["failed"],
                strategy: "adaptive",
              },
              errorQuestions
            )
          }}
          onRepeat={() => {
            setResult(null)
            if (lastRound)
              void startRound(lastRound.config, lastRound.questions)
          }}
          onNext={() => {
            setResult(null)
            void startRound({ ...result.config, strategy: "coverage-cycle" })
          }}
          onRandom={() => {
            setResult(null)
            void startRound({
              ...result.config,
              strategy: "random-balanced",
              shuffleQuestions: true,
            })
          }}
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
          onStateChange={(persisted) => {
            setActiveRound((current) =>
              current ? { ...current, persisted } : current
            )
            void saveActiveRound(persisted)
          }}
          onFinish={finishRound}
      onExit={() => {
        void clearActiveRound().then(() => setActiveRound(null))
      }}
        />
      )
    if (nav === "banks") return <BankManagerPage />
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
    if (nav === "review") return <ReviewPage />
    return <DashboardPage />
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
            <AlertTitle>Banco Maestro V2</AlertTitle>
            <AlertDescription>
              {masterBankError}. V1 continúa disponible.
            </AlertDescription>
          </Alert>
        ) : null}
        {loading ? <LoadingState /> : renderPage()}
      </div>
    </AppShell>
  )
}

function LoadingState() {
  return (
    <Card className="shadow-none">
      <CardContent className="flex min-h-72 flex-col items-center justify-center gap-4">
        <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-secondary text-primary">
          <LoaderCircle className="animate-spin" />
        </div>
        <div className="text-center">
          <p className="font-medium">Preparando tus bancos</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Cargando preguntas y progreso desde este dispositivo.
          </p>
        </div>
        <Button variant="outline" disabled>
          <Database data-icon="inline-start" />
          IndexedDB
        </Button>
      </CardContent>
    </Card>
  )
}

export default App
