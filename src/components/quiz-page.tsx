import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Clock3,
  Flag,
  Heart,
  Info,
  Lightbulb,
  LockKeyhole,
  Maximize2,
  Star,
  TimerOff,
  X,
} from "lucide-react"
import { useApp } from "@/app/app-state"
import { materializeDynamicQuestion } from "@/domain/dynamic-question"
import { evaluateAnswer } from "@/domain/evaluation"
import { scheduleNextRetrieval } from "@/domain/compressed-scheduler"
import { scheduleTrainingRetry } from "@/domain/session-selector"
import {
  sessionContextForMode,
  showsImmediateFeedback,
} from "@/domain/session-context"
import { resumeQuestionIndex } from "@/domain/session-resume"
import { calculateSessionScore } from "@/domain/simulation-calibration"
import {
  type ActiveRound,
  type AnswerValue,
  type EvaluationResult,
  type Question,
  type Session,
  type SessionAnswer,
  type SessionConfig,
} from "@/domain/types"
import { formatElapsedMs, modeLabel } from "@/lib/format"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { QuestionRenderer } from "@/components/question-renderer"
import { AnswerLearningFeedback } from "@/components/answer-learning-feedback"

export function QuizPage({
  questions,
  config,
  resume,
  onStateChange,
  onFinish,
  onExit,
}: {
  questions: Question[]
  config: SessionConfig
  resume?: ActiveRound
  onStateChange?: (round: ActiveRound) => Promise<void>
  onFinish: (session: Session) => Promise<void>
  onExit: () => Promise<void>
}) {
  const { progress, recordAnswer, recordReport } = useApp()
  const initialIndex = resumeQuestionIndex(
    resume?.currentIndex ?? 0,
    resume?.answers.length ?? 0,
    questions.length
  )
  const [queue, setQueue] = useState<Question[]>(questions)
  const [index, setIndex] = useState(initialIndex)
  const [value, setValue] = useState<AnswerValue>(() =>
    initialAnswer(questions[initialIndex])
  )
  const [submitted, setSubmitted] = useState(false)
  const [feedback, setFeedback] = useState<EvaluationResult | null>(null)
  const [answers, setAnswers] = useState<SessionAnswer[]>(resume?.answers ?? [])
  const [startedAt] = useState(() => resume?.startedAt ?? Date.now())
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now)
  const [remaining, setRemaining] = useState(config.perQuestionSeconds)
  const [totalRemaining, setTotalRemaining] = useState(config.totalSeconds)
  const [favorite, setFavorite] = useState(false)
  const [difficult, setDifficult] = useState(false)
  const [reportReason, setReportReason] = useState("")
  const [reportOpen, setReportOpen] = useState(false)
  const [reportPending, setReportPending] = useState(false)
  const [reportError, setReportError] = useState<string | null>(null)
  const [referenceOpen, setReferenceOpen] = useState(false)
  const [transitionPending, setTransitionPending] = useState<
    "finish" | "exit" | null
  >(null)
  const [transitionError, setTransitionError] = useState<string | null>(null)
  const [autosaveError, setAutosaveError] = useState<string | null>(null)
  const [fullscreenPending, setFullscreenPending] = useState(false)
  const [fullscreenUnsupported, setFullscreenUnsupported] = useState(false)
  const [fullscreenError, setFullscreenError] = useState<string | null>(null)
  const questionHeadingRef = useRef<HTMLHeadingElement>(null)
  const focusedQuestionKeyRef = useRef<string | null>(null)
  const isSubmittingRef = useRef(false)
  const isAdvancingRef = useRef(false)
  const hasFinishedRef = useRef(false)
  const deferredTransitionRef = useRef<number | null>(null)
  const transitionGenerationRef = useRef(0)
  const isMountedRef = useRef(false)
  const isExitingRef = useRef(false)
  const finishSessionRef = useRef<Session | null>(null)
  const isReportingRef = useRef(false)
  const reportSequenceRef = useRef(0)
  const latestRoundRef = useRef<ActiveRound | null>(null)
  const autosaveInFlightRef = useRef<Promise<void> | null>(null)
  const autosaveQueuedRef = useRef(false)
  const autosaveStoppedRef = useRef(false)
  const stopAutosaveAndDrainRef = useRef<() => Promise<ActiveRound | null>>(
    async () => null
  )
  const resumeAutosaveRef = useRef<(round: ActiveRound | null) => void>(
    () => undefined
  )
  const currentQuestionKeyRef = useRef<string | null>(null)
  const question = queue[index]
  const progressRef = useRef(progress)
  const queueRef = useRef(queue)
  const stateChangeRef = useRef(onStateChange)
  const selectionSummaryRef = useRef(resume?.selectionSummary)
  const isSilent = !showsImmediateFeedback(config.mode)
  const showFeedback =
    showsImmediateFeedback(config.mode) && submitted && feedback
  const displayedQuestion = useMemo(
    () => shuffleQuestionOptions(question, config.shuffleOptions, startedAt),
    [config.shuffleOptions, question, startedAt]
  )

  const clearDeferredTransition = useCallback(() => {
    if (deferredTransitionRef.current === null) return
    window.clearTimeout(deferredTransitionRef.current)
    deferredTransitionRef.current = null
  }, [])

  const invalidateTransition = useCallback(() => {
    transitionGenerationRef.current += 1
    clearDeferredTransition()
  }, [clearDeferredTransition])

  const isCurrentTransition = useCallback(
    (generation: number, questionKey: string) =>
      isMountedRef.current &&
      !isExitingRef.current &&
      transitionGenerationRef.current === generation &&
      currentQuestionKeyRef.current === questionKey,
    []
  )

  const scheduleDeferredTransition = useCallback(
    (
      callback: () => void,
      delay: number,
      generation = transitionGenerationRef.current,
      questionKey = currentQuestionKeyRef.current
    ) => {
      if (!questionKey || !isCurrentTransition(generation, questionKey)) return
      clearDeferredTransition()
      deferredTransitionRef.current = window.setTimeout(() => {
        deferredTransitionRef.current = null
        if (isCurrentTransition(generation, questionKey)) callback()
      }, delay)
    },
    [clearDeferredTransition, isCurrentTransition]
  )

  const exitSafely = useCallback(async () => {
    if (isExitingRef.current || hasFinishedRef.current) return
    isExitingRef.current = true
    invalidateTransition()
    setTransitionError(null)
    setTransitionPending("exit")
    let stoppedRound: ActiveRound | null = null
    try {
      stoppedRound = await stopAutosaveAndDrainRef.current()
      await onExit()
    } catch {
      if (!isMountedRef.current) return
      resumeAutosaveRef.current(stoppedRound)
      isExitingRef.current = false
      setTransitionPending(null)
      setTransitionError(
        "No se pudo salir de la ronda. Tu avance sigue disponible; inténtalo de nuevo."
      )
    }
  }, [invalidateTransition, onExit])

  const toggleFullscreen = useCallback(async () => {
    const isExitingFullscreen = Boolean(document.fullscreenElement)
    const action = isExitingFullscreen
      ? document.exitFullscreen?.bind(document)
      : document.documentElement.requestFullscreen?.bind(
          document.documentElement
        )
    if (!action) {
      setFullscreenUnsupported(true)
      setFullscreenError(
        "La pantalla completa no está disponible en este navegador. Puedes continuar la ronda normalmente."
      )
      return
    }

    setFullscreenError(null)
    setFullscreenPending(true)
    try {
      await action()
    } catch {
      if (!isMountedRef.current) return
      setFullscreenError(
        isExitingFullscreen
          ? "El navegador no permitió cerrar la pantalla completa. Puedes continuar la ronda normalmente."
          : "El navegador no permitió abrir la pantalla completa. Puedes continuar la ronda normalmente."
      )
    } finally {
      if (isMountedRef.current) setFullscreenPending(false)
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      reportSequenceRef.current += 1
      autosaveStoppedRef.current = true
      autosaveQueuedRef.current = false
      latestRoundRef.current = null
      invalidateTransition()
    }
  }, [invalidateTransition])

  useEffect(() => {
    progressRef.current = progress
  }, [progress])

  useEffect(() => {
    queueRef.current = queue
  }, [queue])

  useEffect(() => {
    stateChangeRef.current = onStateChange
  }, [onStateChange])

  const persistLatestRound = useCallback(() => {
    if (autosaveInFlightRef.current) return autosaveInFlightRef.current
    if (
      autosaveStoppedRef.current ||
      !stateChangeRef.current ||
      !latestRoundRef.current
    )
      return Promise.resolve()
    const persistence = (async () => {
      while (
        isMountedRef.current &&
        !autosaveStoppedRef.current &&
        latestRoundRef.current
      ) {
        const round: ActiveRound = latestRoundRef.current
        const stateChange = stateChangeRef.current
        if (!stateChange) return
        autosaveQueuedRef.current = false
        try {
          await stateChange(round)
        } catch {
          if (isMountedRef.current && !autosaveStoppedRef.current)
            setAutosaveError(
              "No se pudo guardar el avance. La ronda sigue abierta y puedes reintentar."
            )
          return
        }
        if (autosaveStoppedRef.current) return
        if (isMountedRef.current) setAutosaveError(null)
        if (!autosaveQueuedRef.current || latestRoundRef.current === round)
          return
      }
    })()
    autosaveInFlightRef.current = persistence
    void persistence.then(() => {
      if (autosaveInFlightRef.current === persistence)
        autosaveInFlightRef.current = null
    })
    return persistence
  }, [])

  const stopAutosaveAndDrain = useCallback(async () => {
    const stoppedRound = latestRoundRef.current
    autosaveStoppedRef.current = true
    autosaveQueuedRef.current = false
    latestRoundRef.current = null
    if (isMountedRef.current) setAutosaveError(null)
    await autosaveInFlightRef.current
    return stoppedRound
  }, [])

  const resumeAutosave = useCallback(
    (round: ActiveRound | null) => {
      if (!isMountedRef.current) return
      autosaveStoppedRef.current = false
      if (!round) return
      latestRoundRef.current = round
      autosaveQueuedRef.current = true
      void persistLatestRound()
    },
    [persistLatestRound]
  )

  useEffect(() => {
    stopAutosaveAndDrainRef.current = stopAutosaveAndDrain
    resumeAutosaveRef.current = resumeAutosave
  }, [resumeAutosave, stopAutosaveAndDrain])

  useEffect(() => {
    if (autosaveStoppedRef.current) return
    latestRoundRef.current = {
      id: "active",
      startedAt,
      updatedAt: Date.now(),
      currentIndex: index,
      questionKeys: queue.map((item) => `${item.bankId ?? "local"}:${item.id}`),
      questionSnapshots: config.massive ? queue : undefined,
      answers,
      config,
      selectionSummary: selectionSummaryRef.current,
    }
    autosaveQueuedRef.current = true
    void persistLatestRound()
  }, [answers, config, index, persistLatestRound, queue, startedAt])

  useEffect(() => {
    const questionKey = `${question.bankId ?? "local"}:${question.id}`
    currentQuestionKeyRef.current = questionKey
    invalidateTransition()
    const itemProgress = progressRef.current.get(questionKey)
    setValue(initialAnswer(displayedQuestion))
    setSubmitted(false)
    setFeedback(null)
    setQuestionStartedAt(Date.now())
    setRemaining(config.perQuestionSeconds)
    setFavorite(Boolean(itemProgress?.favorite))
    setDifficult(Boolean(itemProgress?.markedDifficult))
    reportSequenceRef.current += 1
    isReportingRef.current = false
    setReportReason("")
    setReportOpen(false)
    setReferenceOpen(false)
    setReportPending(false)
    setReportError(null)
    isSubmittingRef.current = false
    isAdvancingRef.current = false
    if (
      focusedQuestionKeyRef.current !== null &&
      focusedQuestionKeyRef.current !== questionKey
    ) {
      questionHeadingRef.current?.focus()
    }
    focusedQuestionKeyRef.current = questionKey
  }, [
    config.perQuestionSeconds,
    displayedQuestion,
    question.bankId,
    question.id,
    invalidateTransition,
  ])

  const finish = useCallback(
    async (nextAnswers: SessionAnswer[]) => {
      if (
        hasFinishedRef.current ||
        isExitingRef.current ||
        !isMountedRef.current
      )
        return
      hasFinishedRef.current = true
      invalidateTransition()
      setTransitionError(null)
      setTransitionPending("finish")
      const session =
        finishSessionRef.current ??
        ({
          id:
            typeof crypto !== "undefined" && "randomUUID" in crypto
              ? crypto.randomUUID()
              : `session-${Date.now()}`,
          startedAt,
          completedAt: Date.now(),
          mode: config.mode,
          context: sessionContextForMode(config.mode),
          config,
          questionKeys: queueRef.current.map(
            (item) => `${item.bankId ?? "local"}:${item.id}`
          ),
          answers: nextAnswers,
          score: calculateSessionScore(config.mode, nextAnswers),
          durationMs: Date.now() - startedAt,
        } satisfies Session)
      finishSessionRef.current = session
      let stoppedRound: ActiveRound | null = null
      try {
        stoppedRound = await stopAutosaveAndDrain()
        await onFinish(session)
      } catch {
        if (!isMountedRef.current) return
        resumeAutosave(stoppedRound)
        hasFinishedRef.current = false
        isAdvancingRef.current = false
        setTransitionPending(null)
        setTransitionError(
          "No se pudieron guardar los resultados. La ronda sigue disponible; inténtalo de nuevo."
        )
      }
    },
    [
      config,
      invalidateTransition,
      onFinish,
      resumeAutosave,
      startedAt,
      stopAutosaveAndDrain,
    ]
  )

  const advance = useCallback(
    (lastAnswer?: SessionAnswer) => {
      if (
        isAdvancingRef.current ||
        hasFinishedRef.current ||
        isExitingRef.current
      )
        return
      isAdvancingRef.current = true
      invalidateTransition()
      const nextAnswers = lastAnswer ? [...answers, lastAnswer] : answers
      if (index >= queueRef.current.length - 1) void finish(nextAnswers)
      else setIndex((current) => current + 1)
    },
    [answers, finish, index, invalidateTransition]
  )

  const submit = useCallback(
    async (
      forcedReason?: "timeout" | "unanswered",
      finishRoundOnSubmit = false
    ) => {
      if (
        submitted ||
        isSubmittingRef.current ||
        isExitingRef.current ||
        hasFinishedRef.current ||
        !question
      )
        return
      isSubmittingRef.current = true
      setTransitionError(null)
      const transitionGeneration = transitionGenerationRef.current
      const submittedQuestionKey = `${question.bankId ?? "local"}:${question.id}`
      const responseTimeMs = Date.now() - questionStartedAt
      const result = evaluateAnswer(
        question,
        value,
        forcedReason,
        responseTimeMs
      )
      const sessionAnswer: SessionAnswer = {
        questionKey: `${question.bankId ?? "local"}:${question.id}`,
        answer: value,
        result,
        responseTimeMs,
        favorite,
        markedDifficult: difficult,
      }
      setAnswers((current) => [...current, sessionAnswer])
      setFeedback(result)
      setSubmitted(true)
      let nextProgress
      try {
        nextProgress = await recordAnswer(question, result, value, {
          favorite,
          markedDifficult: difficult,
          context: sessionContextForMode(config.mode),
          afterFeedback: answers.some((answer) => {
            const earlier = queue.find(
              (item) =>
                `${item.bankId ?? "local"}:${item.id}` === answer.questionKey
            )
            return earlier?.factId === question.factId
          }),
          sessionId: `round:${resume?.startedAt ?? questionStartedAt}`,
          exposureKind: config.trainingPresetId?.includes("blind")
            ? "blind"
            : config.trainingPresetId?.includes("night") ||
                config.trainingPresetId?.includes("deferred")
              ? "deferred"
              : config.mode === "simulation"
                ? "cold"
                : "practice",
        })
      } catch {
        if (isCurrentTransition(transitionGeneration, submittedQuestionKey)) {
          setAnswers((current) =>
            current.at(-1)?.questionKey === sessionAnswer.questionKey
              ? current.slice(0, -1)
              : current
          )
          setFeedback(null)
          setSubmitted(false)
          isSubmittingRef.current = false
          setTransitionError(
            "No se pudo guardar la respuesta. Tu ronda sigue abierta; inténtalo de nuevo."
          )
        }
        return
      }
      if (!isCurrentTransition(transitionGeneration, submittedQuestionKey))
        return
      if (
        !result.isCorrect &&
        (config.mode === "training" ||
          config.mode === "learn" ||
          config.mode === "smart-review")
      ) {
        const retryGap = scheduleNextRetrieval({
          outcome: "incorrect",
          now: Date.now(),
          tier: "A",
        }).queueGap
        const retryVariants = Array.isArray(question.metadata?.retryVariants)
          ? (question.metadata.retryVariants as Question[])
          : []
        const retryBase = retryVariants.length
          ? retryVariants[
              Math.max(0, nextProgress.timesIncorrect - 1) %
                retryVariants.length
            ]
          : question
        const retryQuestion = question.factId
          ? materializeDynamicQuestion(retryBase, {
              seed: questionStartedAt + nextProgress.timesIncorrect,
              exposure: Math.max(1, nextProgress.timesSeen),
            })
          : question
        setQueue((current) =>
          scheduleTrainingRetry(current, retryQuestion, index, retryGap ?? 0)
        )
      }
      if (finishRoundOnSubmit) {
        scheduleDeferredTransition(
          () => finish([...answers, sessionAnswer]),
          isSilent ? 250 : 900,
          transitionGeneration,
          submittedQuestionKey
        )
      } else if (forcedReason) {
        scheduleDeferredTransition(
          () => advance(sessionAnswer),
          isSilent ? 250 : 900,
          transitionGeneration,
          submittedQuestionKey
        )
      }
    },
    [
      advance,
      answers,
      config.mode,
      config.trainingPresetId,
      difficult,
      favorite,
      finish,
      index,
      isSilent,
      question,
      questionStartedAt,
      queue,
      recordAnswer,
      resume,
      scheduleDeferredTransition,
      isCurrentTransition,
      submitted,
      value,
    ]
  )

  const saveReport = useCallback(async () => {
    if (
      !question ||
      isReportingRef.current ||
      isExitingRef.current ||
      hasFinishedRef.current
    )
      return
    const capturedQuestion = question
    const capturedQuestionKey = `${question.bankId ?? "local"}:${question.id}`
    const capturedValue = value
    const capturedFeedback = feedback
    const capturedReason = reportReason || "Sin motivo indicado"
    const request = reportSequenceRef.current + 1
    reportSequenceRef.current = request
    isReportingRef.current = true
    setReportPending(true)
    setReportError(null)
    try {
      await recordReport(
        capturedQuestion,
        capturedValue,
        capturedFeedback,
        capturedReason
      )
      if (
        !isMountedRef.current ||
        reportSequenceRef.current !== request ||
        currentQuestionKeyRef.current !== capturedQuestionKey
      )
        return
      setReportOpen(false)
      setReportReason("")
    } catch {
      if (
        isMountedRef.current &&
        reportSequenceRef.current === request &&
        currentQuestionKeyRef.current === capturedQuestionKey
      )
        setReportError(
          "No se pudo guardar el reporte. Revisa el almacenamiento e inténtalo de nuevo."
        )
    } finally {
      if (
        isMountedRef.current &&
        reportSequenceRef.current === request &&
        currentQuestionKeyRef.current === capturedQuestionKey
      ) {
        isReportingRef.current = false
        setReportPending(false)
      }
    }
  }, [feedback, question, recordReport, reportReason, value])

  useEffect(() => {
    const seconds = config.perQuestionSeconds
    if (transitionPending !== null || submitted || seconds === null)
      return undefined
    const interval = window.setInterval(() => {
      const next = Math.max(
        0,
        seconds * 1000 - (Date.now() - questionStartedAt)
      )
      setRemaining(Math.ceil(next / 1000))
      if (next <= 0) {
        window.clearInterval(interval)
        void submit("timeout")
      }
    }, 100)
    return () => window.clearInterval(interval)
  }, [
    config.perQuestionSeconds,
    questionStartedAt,
    submit,
    submitted,
    transitionPending,
  ])

  useEffect(() => {
    if (transitionPending !== null || config.totalSeconds === null)
      return undefined
    const interval = window.setInterval(() => {
      const next = Math.max(
        0,
        config.totalSeconds! * 1000 - (Date.now() - startedAt)
      )
      setTotalRemaining(Math.ceil(next / 1000))
      if (next <= 0) {
        window.clearInterval(interval)
        if (!submitted) void submit("timeout", true)
        else scheduleDeferredTransition(() => finish(answers), 250)
      }
    }, 250)
    return () => window.clearInterval(interval)
  }, [
    answers,
    config.totalSeconds,
    finish,
    scheduleDeferredTransition,
    startedAt,
    submit,
    submitted,
    transitionPending,
  ])

  useEffect(() => clearDeferredTransition, [clearDeferredTransition])

  useEffect(() => {
    const handleExitKey = (event: KeyboardEvent) => {
      if (
        event.key !== "Escape" ||
        event.defaultPrevented ||
        referenceOpen ||
        document.fullscreenElement
      )
        return
      event.preventDefault()
      void exitSafely()
    }
    window.addEventListener("keydown", handleExitKey)
    return () => window.removeEventListener("keydown", handleExitKey)
  }, [exitSafely, referenceOpen])

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (
        event.defaultPrevented ||
        isExitingRef.current ||
        hasFinishedRef.current
      )
        return
      const target = event.target
      if (
        target instanceof Element &&
        target.closest(
          "button,input,textarea,select,a,[role='button'],[role='radio'],[role='checkbox'],[role='switch'],[role='combobox'],[role='option'],[contenteditable='true']"
        )
      )
        return
      if (event.key.toLowerCase() === "f") {
        setFavorite((current) => !current)
        return
      }
      if (event.key === "Enter") {
        if (!submitted) void submit()
        return
      }
      if (
        submitted ||
        question.type === "multi_select" ||
        question.type === "ordering" ||
        question.type === "matching"
      )
        return
      const number = Number(event.key)
      const letterIndex =
        number >= 1 && number <= 4
          ? number - 1
          : "abcd".indexOf(event.key.toLowerCase())
      const option = displayedQuestion.options[letterIndex]
      if (option) setValue(option.id)
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  })

  if (!question)
    return (
      <Card>
        <CardContent className="p-8 text-center">
          No hay preguntas para esta configuración.
        </CardContent>
      </Card>
    )
  const liveCorrect = answers.filter((answer) => answer.result.isCorrect).length
  const liveIncorrect = answers.filter(
    (answer) => !answer.result.isCorrect
  ).length
  const liveAverage = answers.length
    ? answers.reduce((sum, answer) => sum + answer.responseTimeMs, 0) /
      answers.length
    : 0
  const completion = ((index + (submitted ? 1 : 0)) / queue.length) * 100
  const instruction = "Elige una respuesta y confirma."

  return (
    <article className="mx-auto flex min-h-screen w-full max-w-3xl flex-col px-4 py-5 pb-28 sm:px-6 sm:py-6">
      <header className="grid grid-cols-[auto_1fr_auto] items-center gap-3">
        <Button
          variant="ghost"
          disabled={transitionPending !== null}
          onClick={() => void exitSafely()}
        >
          <X data-icon="inline-start" />
          Salir
        </Button>
        <div className="min-w-0">
          <div className="mb-2 flex items-center justify-between gap-3 text-xs font-medium text-muted-foreground">
            <span>
              Pregunta {index + 1} de {queue.length}
            </span>
            <span>{Math.round(completion)}%</span>
          </div>
          <Progress aria-label="Progreso de la ronda" value={completion} />
        </div>
        <p className="sr-only" aria-live="polite" aria-atomic="true">
          Pregunta {index + 1} de {queue.length}: {question.question}
        </p>
        <Button
          aria-label="Pantalla completa"
          disabled={fullscreenPending || fullscreenUnsupported}
          size="icon"
          variant="outline"
          className="size-11"
          onClick={() => void toggleFullscreen()}
        >
          <Maximize2 data-icon="inline-start" />
        </Button>
      </header>

      <section
        aria-labelledby="question-title"
        className="my-auto py-8 sm:py-12"
      >
        {fullscreenError ? (
          <Alert variant="destructive" className="mb-5">
            <AlertTitle>Pantalla completa</AlertTitle>
            <AlertDescription>{fullscreenError}</AlertDescription>
          </Alert>
        ) : null}
        {transitionError ? (
          <Alert variant="destructive" className="mb-5">
            <AlertTitle>Persistencia de la ronda</AlertTitle>
            <AlertDescription>{transitionError}</AlertDescription>
          </Alert>
        ) : null}
        {autosaveError ? (
          <Alert variant="destructive" className="mb-5">
            <AlertTitle>Guardado local</AlertTitle>
            <AlertDescription>
              <span>{autosaveError}</span>
              <Button
                size="sm"
                variant="outline"
                className="mt-2 min-h-11"
                onClick={() => void persistLatestRound()}
              >
                Reintentar guardado
              </Button>
            </AlertDescription>
          </Alert>
        ) : null}
        <div className="mb-5 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Badge variant="secondary">{modeLabel(config.mode)}</Badge>
          <Badge
            data-bank-profile={question.bankProfileId ?? "legacy-v1"}
            variant="outline"
          >
            Banco Maestro Único
          </Badge>
          {showFeedback ? <span>{question.source.reference}</span> : null}
          <span>· {familyLabel(question)}</span>
          {config.perQuestionSeconds !== null ? (
            <span
              className={`ml-auto flex items-center gap-1 font-semibold ${remaining && remaining <= 3 ? "text-destructive" : "text-primary"}`}
            >
              <TimerOff className="size-4" aria-hidden="true" />
              {remaining}s
            </span>
          ) : (
            <span className="ml-auto flex items-center gap-1 text-xs">
              <LockKeyhole className="size-4" />
              Sin límite
            </span>
          )}
          {config.totalSeconds !== null ? (
            <span
              className={
                totalRemaining && totalRemaining < 30
                  ? "font-semibold text-destructive"
                  : ""
              }
            >
              <Clock3 className="mr-1 inline size-4" />
              {totalRemaining}s total
            </span>
          ) : null}
        </div>
        {config.mode === "speed" ? (
          <div className="mb-5 grid grid-cols-3 gap-2 rounded-xl border bg-card p-3 text-center text-sm">
            <div>
              <p className="text-xs text-muted-foreground">Correctas</p>
              <p className="mt-1 font-semibold text-emerald-600 dark:text-emerald-400">
                {liveCorrect}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Incorrectas</p>
              <p className="mt-1 font-semibold text-destructive">
                {liveIncorrect}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Promedio</p>
              <p className="mt-1 font-semibold">
                {formatElapsedMs(liveAverage)}
              </p>
            </div>
          </div>
        ) : null}
        <h1
          id="question-title"
          ref={questionHeadingRef}
          tabIndex={-1}
          className="text-2xl leading-tight font-semibold text-pretty sm:text-3xl"
        >
          {question.question}
        </h1>
        <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
          <Info className="size-4 shrink-0" />
          {instruction}
        </p>
        <div className="mt-7">
          <QuestionRenderer
            question={displayedQuestion}
            value={value}
            onChange={(nextValue) => {
              if (isExitingRef.current || hasFinishedRef.current) return
              setValue(nextValue)
            }}
            disabled={submitted || transitionPending !== null}
            feedback={showFeedback ? feedback : null}
          />
        </div>
        <div className="mt-5 space-y-4">
          {showFeedback ? (
            <AnswerLearningFeedback
              question={question}
              selectedAnswer={value}
              isCorrect={feedback.isCorrect}
              onUnderstood={() => advance()}
              onConfused={() => setDifficult(true)}
            />
          ) : null}
          {showFeedback ? <MemoryCue cue={question.memoryCue} /> : null}
          {submitted && !showFeedback ? (
            <div className="rounded-lg border bg-muted/35 px-4 py-3 text-sm text-muted-foreground">
              Respuesta registrada. La solución se revelará al finalizar la
              ronda.
            </div>
          ) : null}
          {reportOpen ? (
            <div className="flex flex-col gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
              <p className="text-sm font-medium">¿Qué quieres auditar?</p>
              <select
                value={reportReason}
                onChange={(event) => setReportReason(event.target.value)}
                aria-label="Motivo del reporte"
                disabled={reportPending || transitionPending !== null}
                className="h-11 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="">Selecciona un motivo</option>
                <option value="Respuesta ambigua">Respuesta ambigua</option>
                <option value="Referencia incorrecta">Referencia incorrecta</option>
                <option value="Redacción confusa">Redacción confusa</option>
                <option value="Posible error de fuente">Posible error de fuente</option>
              </select>
              {reportPending ? (
                <p role="status" aria-live="polite" className="text-sm">
                  Guardando reporte…
                </p>
              ) : null}
              {reportError ? (
                <p role="alert" className="text-sm text-destructive">
                  {reportError}
                </p>
              ) : null}
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="destructive"
                  className="min-h-11"
                  disabled={reportPending || transitionPending !== null}
                  onClick={() => void saveReport()}
                >
                  Guardar reporte
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="min-h-11"
                  disabled={reportPending || transitionPending !== null}
                  onClick={() => setReportOpen(false)}
                >
                  Cancelar
                </Button>
              </div>
            </div>
          ) : null}
        </div>
        <Separator className="my-6" />
        <div className="flex flex-wrap gap-2">
          <Button
            aria-pressed={favorite}
            size="sm"
            className="min-h-11"
            variant={favorite ? "secondary" : "outline"}
            disabled={transitionPending !== null}
            onClick={() => {
              if (isExitingRef.current || hasFinishedRef.current) return
              setFavorite((current) => !current)
            }}
          >
            <Heart
              data-icon="inline-start"
              className={favorite ? "fill-current" : undefined}
            />
            Favorita
          </Button>
          <Button
            aria-pressed={difficult}
            size="sm"
            className="min-h-11"
            variant={difficult ? "secondary" : "outline"}
            disabled={transitionPending !== null}
            onClick={() => {
              if (isExitingRef.current || hasFinishedRef.current) return
              setDifficult((current) => !current)
            }}
          >
            <Star
              data-icon="inline-start"
              className={difficult ? "fill-current" : undefined}
            />
            Marcar difícil
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="min-h-11"
            disabled={transitionPending !== null}
            onClick={() => {
              if (isExitingRef.current || hasFinishedRef.current) return
              setReportOpen((current) => !current)
            }}
          >
            <Flag data-icon="inline-start" />
            Reportar
          </Button>
          {showFeedback ? (
            <Dialog open={referenceOpen} onOpenChange={setReferenceOpen}>
              <DialogTrigger asChild>
                <Button size="sm" variant="ghost" className="min-h-11">
                  <Info data-icon="inline-start" />
                  Referencia
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Volver al texto / referencia</DialogTitle>
                  <DialogDescription>
                    Busca manualmente esta cita en tu Biblia RVR95.
                  </DialogDescription>
                </DialogHeader>
                <div className="rounded-xl bg-muted/40 p-4 text-sm font-medium">
                  {question.source.reference}
                </div>
              </DialogContent>
            </Dialog>
          ) : null}
        </div>
      </section>

      <footer className="fixed right-0 bottom-0 left-0 z-10 border-t bg-background/95 px-4 py-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] backdrop-blur sm:static sm:mt-auto sm:border-0 sm:bg-transparent sm:p-0">
        <div className="mx-auto max-w-3xl sm:flex sm:justify-end">
          <Button
            className="min-h-11 w-full sm:w-auto sm:min-w-40"
            disabled={
              transitionPending !== null || (!submitted && isEmptyAnswer(value))
            }
            onClick={() => {
              if (submitted) advance()
              else void submit()
            }}
          >
            {submitted
              ? index === queue.length - 1
                ? "Ver resultados"
                : "Siguiente"
              : "Confirmar respuesta"}
          </Button>
        </div>
      </footer>
    </article>
  )
}

export function MemoryCue({ cue }: { cue?: string }) {
  if (!cue) return null
  return (
    <div
      role="note"
      className="flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/[0.04] px-4 py-3"
    >
      <Lightbulb
        className="mt-0.5 size-5 shrink-0 text-primary"
        aria-hidden="true"
      />
      <div>
        <p className="text-sm font-semibold text-primary">
          Pista para recordar
        </p>
        <p className="mt-1 text-sm leading-5 text-foreground/80">{cue}</p>
      </div>
    </div>
  )
}

function initialAnswer(question: Question | undefined): AnswerValue {
  if (!question) return undefined
  if (question.type === "ordering")
    return question.options.map((option) => option.id)
  if (question.type === "matching") return {}
  if (question.type === "multi_select") return []
  return undefined
}

function isEmptyAnswer(value: AnswerValue) {
  return (
    value === undefined ||
    value === null ||
    (typeof value === "string" && !value.trim()) ||
    (Array.isArray(value) && value.length === 0) ||
    (typeof value === "object" &&
      !Array.isArray(value) &&
      Object.keys(value).length === 0)
  )
}

function familyLabel(question: Question) {
  if (question.family === "single_choice_direct") return "Selección única"
  if (question.family === "single_choice_contextual") return "Selección única"
  if (question.family === "fill_choice") return "Completar con opciones"
  if (question.family === "true_false") return "Verdadero o falso"
  return question.type === "true_false"
    ? "Verdadero o falso"
    : question.type === "fill_blank"
      ? "Completar con opciones"
      : "Selección única"
}

export function shuffleQuestionOptions(
  question: Question,
  shuffle: boolean,
  sessionSeed = 0,
) {
  if (!shuffle || question.options.length < 2) return question
  const options = [...question.options]
  const offset =
    (question.id
      .split("")
      .reduce((sum, character) => sum + character.charCodeAt(0), 0) +
      sessionSeed) %
    options.length
  return {
    ...question,
    options: options.map(
      (_, index) => options[(index + offset) % options.length]
    ),
  }
}
