import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Check,
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
import { evaluateAnswer } from "@/domain/evaluation"
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
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { QuestionRenderer } from "@/components/question-renderer"

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
  onStateChange?: (round: ActiveRound) => void
  onFinish: (session: Session) => void
  onExit: () => void
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
  const questionHeadingRef = useRef<HTMLHeadingElement>(null)
  const focusedQuestionKeyRef = useRef<string | null>(null)
  const isSubmittingRef = useRef(false)
  const isAdvancingRef = useRef(false)
  const hasFinishedRef = useRef(false)
  const deferredTransitionRef = useRef<number | null>(null)
  const question = queue[index]
  const progressRef = useRef(progress)
  const queueRef = useRef(queue)
  const stateChangeRef = useRef(onStateChange)
  const selectionSummaryRef = useRef(resume?.selectionSummary)
  const isSilent = !showsImmediateFeedback(config.mode)
  const showFeedback =
    showsImmediateFeedback(config.mode) && submitted && feedback
  const displayedQuestion = useMemo(
    () => shuffleQuestionOptions(question, config.shuffleOptions),
    [config.shuffleOptions, question]
  )

  const clearDeferredTransition = useCallback(() => {
    if (deferredTransitionRef.current === null) return
    window.clearTimeout(deferredTransitionRef.current)
    deferredTransitionRef.current = null
  }, [])

  const scheduleDeferredTransition = useCallback(
    (callback: () => void, delay: number) => {
      clearDeferredTransition()
      deferredTransitionRef.current = window.setTimeout(() => {
        deferredTransitionRef.current = null
        callback()
      }, delay)
    },
    [clearDeferredTransition]
  )

  useEffect(() => {
    progressRef.current = progress
  }, [progress])

  useEffect(() => {
    queueRef.current = queue
  }, [queue])

  useEffect(() => {
    stateChangeRef.current = onStateChange
  }, [onStateChange])

  useEffect(() => {
    stateChangeRef.current?.({
      id: "active",
      startedAt,
      updatedAt: Date.now(),
      currentIndex: index,
      questionKeys: queue.map((item) => `${item.bankId ?? "local"}:${item.id}`),
      answers,
      config,
      selectionSummary: selectionSummaryRef.current,
    })
  }, [answers, config, index, queue, startedAt])

  useEffect(() => {
    const itemProgress = progressRef.current.get(
      `${question.bankId ?? "local"}:${question.id}`
    )
    setValue(initialAnswer(displayedQuestion))
    setSubmitted(false)
    setFeedback(null)
    setQuestionStartedAt(Date.now())
    setRemaining(config.perQuestionSeconds)
    setFavorite(Boolean(itemProgress?.favorite))
    setDifficult(Boolean(itemProgress?.markedDifficult))
    setReportReason("")
    clearDeferredTransition()
    isSubmittingRef.current = false
    isAdvancingRef.current = false
    const questionKey = `${question.bankId ?? "local"}:${question.id}`
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
    clearDeferredTransition,
  ])

  const finish = useCallback(
    (nextAnswers: SessionAnswer[]) => {
      if (hasFinishedRef.current) return
      hasFinishedRef.current = true
      clearDeferredTransition()
      const session: Session = {
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
      }
      onFinish(session)
    },
    [clearDeferredTransition, config, onFinish, startedAt]
  )

  const advance = useCallback(
    (lastAnswer?: SessionAnswer) => {
      if (isAdvancingRef.current || hasFinishedRef.current) return
      isAdvancingRef.current = true
      clearDeferredTransition()
      const nextAnswers = lastAnswer ? [...answers, lastAnswer] : answers
      if (index >= queueRef.current.length - 1) finish(nextAnswers)
      else setIndex((current) => current + 1)
    },
    [answers, clearDeferredTransition, finish, index]
  )

  const submit = useCallback(
    async (
      forcedReason?: "timeout" | "unanswered",
      finishRoundOnSubmit = false
    ) => {
      if (submitted || isSubmittingRef.current || !question) return
      isSubmittingRef.current = true
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
      const nextProgress = await recordAnswer(question, result, value, {
        favorite,
        markedDifficult: difficult,
        context: sessionContextForMode(config.mode),
      })
      if (
        !result.isCorrect &&
        (config.mode === "training" || config.mode === "learn")
      ) {
        const retryGap = Math.min(
          8 + Math.max(0, nextProgress.timesIncorrect - 1) * 4,
          20
        )
        setQueue((current) =>
          scheduleTrainingRetry(current, question, index, retryGap)
        )
      }
      if (finishRoundOnSubmit) {
        scheduleDeferredTransition(
          () => finish([...answers, sessionAnswer]),
          isSilent ? 250 : 900
        )
      } else if (forcedReason) {
        scheduleDeferredTransition(
          () => advance(sessionAnswer),
          isSilent ? 250 : 900
        )
      }
    },
    [
      advance,
      answers,
      config.mode,
      difficult,
      favorite,
      finish,
      index,
      isSilent,
      question,
      questionStartedAt,
      recordAnswer,
      scheduleDeferredTransition,
      submitted,
      value,
    ]
  )

  useEffect(() => {
    const seconds = config.perQuestionSeconds
    if (submitted || seconds === null) return undefined
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
  }, [config.perQuestionSeconds, questionStartedAt, submit, submitted])

  useEffect(() => {
    if (config.totalSeconds === null) return undefined
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
  }, [answers, config.totalSeconds, finish, scheduleDeferredTransition, startedAt, submit, submitted])

  useEffect(() => clearDeferredTransition, [clearDeferredTransition])

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      if (
        target?.closest(
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
  const correctText =
    question.answerMode === "canonical_text"
      ? question.correctAnswerText
      : question.type === "matching"
        ? "Consulta los pares indicados en la referencia."
        : question.options
            .filter((option) => question.correctAnswer.includes(option.id))
            .map((option) => option.text)
            .join(", ")
  const liveCorrect = answers.filter((answer) => answer.result.isCorrect).length
  const liveIncorrect = answers.filter(
    (answer) => !answer.result.isCorrect
  ).length
  const liveAverage = answers.length
    ? answers.reduce((sum, answer) => sum + answer.responseTimeMs, 0) /
      answers.length
    : 0
  const completion = ((index + (submitted ? 1 : 0)) / queue.length) * 100
  const instruction =
    question.answerMode === "canonical_text"
      ? "Escribe la respuesta canónica y confirma."
      : question.type === "multi_select"
        ? "Selecciona todas las correctas y confirma."
        : question.type === "ordering"
          ? "Ordena con los botones accesibles."
          : question.type === "matching"
            ? "Relaciona cada elemento con su correspondencia."
            : "Elige una respuesta y confirma."

  return (
    <article className="mx-auto flex min-h-screen w-full max-w-3xl flex-col px-4 py-5 pb-28 sm:px-6 sm:py-6">
      <header className="grid grid-cols-[auto_1fr_auto] items-center gap-3">
        <Button variant="ghost" onClick={() => { clearDeferredTransition(); onExit() }}>
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
          size="icon"
          variant="outline"
          className="size-11"
          onClick={() => {
            if (document.fullscreenElement) void document.exitFullscreen()
            else void document.documentElement.requestFullscreen?.()
          }}
        >
          <Maximize2 data-icon="inline-start" />
        </Button>
      </header>

      <section
        aria-labelledby="question-title"
        className="my-auto py-8 sm:py-12"
      >
        <div className="mb-5 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Badge variant="secondary">{modeLabel(config.mode)}</Badge>
          <Badge
            data-bank-profile={question.bankProfileId ?? "legacy-v1"}
            variant="outline"
          >
            {question.bankProfileId === "prep-v3"
              ? "V3"
              : question.bankProfileId === "master-v2"
                ? "V2"
                : question.bankProfileId === "curated-v4"
                  ? "V4"
                  : "V1"}
          </Badge>
          <span>{question.source.reference}</span>
          <span>· {typeLabel(question.type)}</span>
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
            onChange={setValue}
            disabled={submitted}
            feedback={showFeedback ? feedback : null}
          />
        </div>
        <div className="mt-5 space-y-4">
          {showFeedback ? (
            <Alert variant={feedback.isCorrect ? "default" : "destructive"}>
              <AlertTitle className="flex items-center gap-2">
                {feedback.isCorrect ? <Check /> : <X />}
                {feedback.isCorrect
                  ? "Respuesta correcta"
                  : feedback.reason === "timeout"
                    ? "Tiempo agotado"
                    : "Respuesta incorrecta"}
              </AlertTitle>
              <AlertDescription className="flex flex-col gap-2">
                <span>
                  Respuesta correcta: <strong>{correctText}</strong>
                </span>
                {question.explanation ? (
                  <span>{question.explanation}</span>
                ) : null}
                <span>
                  Fuente: <strong>{question.source.reference}</strong>
                </span>
              </AlertDescription>
            </Alert>
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
              <Input
                value={reportReason}
                onChange={(event) => setReportReason(event.target.value)}
                placeholder="Motivo opcional"
                aria-label="Motivo del reporte"
              />
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={async () => {
                    await recordReport(
                      question,
                      value,
                      feedback,
                      reportReason || "Sin motivo indicado"
                    )
                    setReportOpen(false)
                  }}
                >
                  Guardar reporte
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
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
            onClick={() => setFavorite((current) => !current)}
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
            onClick={() => setDifficult((current) => !current)}
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
            onClick={() => setReportOpen((current) => !current)}
          >
            <Flag data-icon="inline-start" />
            Reportar
          </Button>
          <Dialog>
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
        </div>
      </section>

      <footer className="fixed right-0 bottom-0 left-0 z-10 border-t bg-background/95 px-4 py-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] backdrop-blur sm:static sm:mt-auto sm:border-0 sm:bg-transparent sm:p-0">
        <div className="mx-auto max-w-3xl sm:flex sm:justify-end">
          <Button
            className="min-h-11 w-full sm:w-auto sm:min-w-40"
            disabled={!submitted && isEmptyAnswer(value)}
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

function typeLabel(type: Question["type"]) {
  const labels: Record<Question["type"], string> = {
    single_choice: "Opción única",
    multi_select: "Selección múltiple",
    ordering: "Ordenamiento",
    matching: "Relacionar",
    true_false: "Verdadero o falso",
    fill_blank: "Completar",
    negative_choice: "Opción negativa",
    who_said_it: "Quién lo dijo",
    to_whom: "A quién",
    reference_detail: "Detalle de referencia",
    sequence_choice: "Secuencia",
    precision: "Precisión",
  }
  return labels[type]
}

function shuffleQuestionOptions(question: Question, shuffle: boolean) {
  if (!shuffle || question.options.length < 2) return question
  const options = [...question.options]
  const offset =
    question.id
      .split("")
      .reduce((sum, character) => sum + character.charCodeAt(0), 0) %
    options.length
  return {
    ...question,
    options: options.map(
      (_, index) => options[(index + offset) % options.length]
    ),
  }
}
