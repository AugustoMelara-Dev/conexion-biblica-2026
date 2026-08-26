import { useState } from "react"
import {
  ArrowRight,
  Check,
  Clock3,
  RotateCcw,
  Settings2,
  Trophy,
  X,
} from "lucide-react"
import { type Question, type Session } from "@/domain/types"
import { getMedian } from "@/domain/evaluation"
import { formatElapsedMs, modeLabel } from "@/lib/format"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card"
import { MetricStrip } from "@/components/layout/metric-strip"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"

export function ResultsPage({
  session,
  questions,
  onErrors,
  onRepeat,
  onNext,
  onRandom,
  onNew,
}: {
  session: Session
  questions: Question[]
  onErrors: () => void
  onRepeat: () => void
  onNext: () => void
  onRandom: () => void
  onNew: () => void
}) {
  const [onlyIncorrect, setOnlyIncorrect] = useState(false)
  const answeredTimes = session.answers
    .filter((item) => item.result.wasAnswered)
    .map((item) => item.responseTimeMs)
  const correct = session.answers.filter((item) => item.result.isCorrect).length
  const incorrect = session.answers.filter(
    (item) => !item.result.isCorrect && item.result.wasAnswered
  ).length
  const unanswered = session.answers.filter(
    (item) => !item.result.wasAnswered
  ).length
  const hasErrors = session.answers.some((item) => !item.result.isCorrect)
  const accuracy = session.answers.length
    ? Math.round((correct / session.answers.length) * 100)
    : 0
  const fastest = answeredTimes.length ? Math.min(...answeredTimes) : 0
  const slowest = answeredTimes.length ? Math.max(...answeredTimes) : 0
  const average = answeredTimes.length
    ? Math.round(
        answeredTimes.reduce((sum, value) => sum + value, 0) /
          answeredTimes.length
      )
    : 0
  const questionMap = new Map(
    questions.map((question) => [
      `${question.bankId ?? "local"}:${question.id}`,
      question,
    ])
  )
  const displayedAnswers = onlyIncorrect
    ? session.answers.filter((answer) => !answer.result.isCorrect)
    : session.answers
  const recommendation = hasErrors
    ? `Repasa las ${incorrect + unanswered} preguntas que necesitan refuerzo antes de repetir la tanda.`
    : "Consolidaste esta tanda sin errores. Repite la práctica más adelante para afianzarla."

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-7 px-4 pb-8 sm:px-6">
      <section className="text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
          <Trophy aria-hidden="true" />
        </div>
        <p className="mt-4 text-sm font-medium text-muted-foreground">
          {modeLabel(session.mode)} · ronda terminada
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          {hasErrors ? "Tu siguiente paso está claro." : "Ronda completada."}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {session.context === "simulation"
            ? "Este resultado cuenta sólo para tus simulacros."
            : "Esta práctica mejora tu dominio sin alterar tus simulacros."}
        </p>
      </section>

      <Card className="shadow-none">
        <CardHeader>
          <h2 className="text-xl font-semibold tracking-tight">Resultado</h2>
          <p className="text-3xl font-semibold tracking-tight">
            {session.context === "simulation"
              ? `${session.score} / 100`
              : `${correct} / ${session.answers.length}`}
          </p>
        </CardHeader>
      </Card>

      <MetricStrip
        items={[
          { label: "Correctas", value: correct },
          { label: "Incorrectas", value: incorrect },
          { label: "Sin responder", value: unanswered },
          { label: "Precisión", value: `${accuracy}%` },
          {
            label: "Tiempo promedio",
            value: formatElapsedMs(average),
            icon: Clock3,
          },
        ]}
      />

      <Card className="border-primary/20 bg-primary/[0.035] shadow-none">
        <CardHeader>
          <h2 className="text-xl font-semibold tracking-tight">
            Recomendación
          </h2>
          <CardDescription>{recommendation}</CardDescription>
        </CardHeader>
      </Card>

      {session.selectionSummary?.strategy === "coverage-cycle" ? (
        <Card className="shadow-none">
          <CardHeader>
            <h2 className="text-xl font-semibold tracking-tight">
              Ciclo de cobertura
            </h2>
            <CardDescription>
              {session.selectionSummary.seen} / {session.selectionSummary.total}{" "}
              recorridas · {session.selectionSummary.remaining} pendientes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Progress
              aria-label="Progreso del ciclo de cobertura"
              value={
                session.selectionSummary.total
                  ? ((session.selectionSummary.seen ?? 0) /
                      session.selectionSummary.total) *
                    100
                  : 0
              }
            />
          </CardContent>
        </Card>
      ) : null}

      <Card className="shadow-none">
        <CardHeader>
          <h2 className="text-xl font-semibold tracking-tight">
            Ritmo de la ronda
          </h2>
          <CardDescription>
            Más rápida {formatElapsedMs(fastest)} · más lenta{" "}
            {formatElapsedMs(slowest)} · mediana{" "}
            {formatElapsedMs(getMedian(answeredTimes))} · duración total{" "}
            {formatElapsedMs(session.durationMs)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Progress aria-label="Precisión de la ronda" value={accuracy} />
        </CardContent>
      </Card>

      <Card className="shadow-none">
        <CardHeader className="gap-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">
              {onlyIncorrect ? "Respuestas incorrectas" : "Lista completa"}
            </h2>
            <CardDescription>
              Revisa qué ocurrió en cada pregunta.
            </CardDescription>
          </div>
          <label className="flex min-h-11 cursor-pointer items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm font-medium">
            Solo incorrectas
            <Switch
              checked={onlyIncorrect}
              onCheckedChange={setOnlyIncorrect}
              aria-label="Solo incorrectas"
              disabled={!hasErrors}
            />
          </label>
          {!hasErrors ? (
            <p className="text-sm text-muted-foreground">
              No hay respuestas incorrectas para filtrar.
            </p>
          ) : null}
        </CardHeader>
        <CardContent className="p-0">
          <div className="flex flex-col">
            {displayedAnswers.map((answer, index) => {
              const question = questionMap.get(answer.questionKey)
              return (
                <div
                  key={`${answer.questionKey}-${index}`}
                  className="flex items-start gap-3 border-t px-5 py-4 first:border-t-0"
                >
                  <div
                    className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full ${answer.result.isCorrect ? "bg-chart-2/15 text-chart-2" : "bg-destructive/10 text-destructive"}`}
                  >
                    {answer.result.isCorrect ? (
                      <Check className="size-4" aria-hidden="true" />
                    ) : (
                      <X className="size-4" aria-hidden="true" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm leading-5 font-medium">
                      {question?.question ?? answer.questionKey}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {question?.source.reference ?? "Referencia no disponible"}{" "}
                      ·{" "}
                      {answer.result.wasAnswered
                        ? formatElapsedMs(answer.responseTimeMs)
                        : "No respondida"}
                    </p>
                  </div>
                  <Badge
                    variant={
                      answer.result.isCorrect ? "default" : "destructive"
                    }
                  >
                    {answer.result.isCorrect
                      ? "Correcta"
                      : answer.result.reason === "timeout"
                        ? "Vencida"
                        : "Incorrecta"}
                  </Badge>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Separator />
      <div className="flex flex-col gap-3">
        <Button
          variant={hasErrors ? "default" : "outline"}
          onClick={onErrors}
          disabled={!hasErrors}
        >
          <RotateCcw data-icon="inline-start" />
          Repasar errores
        </Button>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={onRepeat}>
            Repetir esta tanda
          </Button>
          {session.selectionSummary?.strategy === "coverage-cycle" &&
          (session.selectionSummary.remaining ?? 0) > 0 ? (
            <Button variant="outline" onClick={onNext}>
              Siguiente tanda sin repetir <ArrowRight data-icon="inline-end" />
            </Button>
          ) : null}
          <Button variant="outline" onClick={onRandom}>
            Otra tanda aleatoria
          </Button>
          <Button variant="outline" onClick={onNew}>
            <Settings2 data-icon="inline-start" />
            Nueva configuración
          </Button>
        </div>
      </div>
    </div>
  )
}
