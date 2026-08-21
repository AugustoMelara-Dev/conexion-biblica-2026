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
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"

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
  const accuracy = session.answers.length
    ? Math.round((correct / session.answers.length) * 100)
    : 0
  const fastest = answeredTimes.length ? Math.min(...answeredTimes) : 0
  const slowest = answeredTimes.length ? Math.max(...answeredTimes) : 0
  const questionMap = new Map(
    questions.map((question) => [
      `${question.bankId ?? "local"}:${question.id}`,
      question,
    ])
  )
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-7">
      <section className="text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
          <Trophy />
        </div>
        <p className="mt-4 text-sm font-medium text-muted-foreground">
          {modeLabel(session.mode)} · ronda terminada
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          Buen trabajo bajo presión.
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Tu resultado quedó guardado localmente.
        </p>
      </section>
      <Card className="shadow-none">
        <CardContent className="grid gap-5 p-5 sm:grid-cols-2 lg:grid-cols-4">
          <ResultMetric
            label="Puntuación"
            value={`${correct} / ${session.answers.length}`}
          />
          <ResultMetric label="Precisión" value={`${accuracy}%`} />
          <ResultMetric
            label="Tiempo promedio"
            value={formatElapsedMs(
              answeredTimes.length
                ? Math.round(
                    answeredTimes.reduce((sum, value) => sum + value, 0) /
                      answeredTimes.length
                  )
                : 0
            )}
          />
          <ResultMetric
            label="Mediana"
            value={formatElapsedMs(getMedian(answeredTimes))}
          />
        </CardContent>
      </Card>
      {session.selectionSummary?.strategy === "coverage-cycle" ? (
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>Ciclo de cobertura</CardTitle>
            <CardDescription>
              {session.selectionSummary.seen} / {session.selectionSummary.total}{" "}
              recorridas · {session.selectionSummary.remaining} pendientes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Progress
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
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="shadow-none">
          <CardContent className="flex items-center gap-3 p-4">
            <Check className="text-chart-2" />
            <div>
              <p className="text-xs tracking-[0.12em] text-muted-foreground uppercase">
                Correctas
              </p>
              <p className="mt-1 text-2xl font-semibold">{correct}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="shadow-none">
          <CardContent className="flex items-center gap-3 p-4">
            <X className="text-destructive" />
            <div>
              <p className="text-xs tracking-[0.12em] text-muted-foreground uppercase">
                Incorrectas
              </p>
              <p className="mt-1 text-2xl font-semibold">{incorrect}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="shadow-none">
          <CardContent className="flex items-center gap-3 p-4">
            <Clock3 className="text-primary" />
            <div>
              <p className="text-xs tracking-[0.12em] text-muted-foreground uppercase">
                Sin responder
              </p>
              <p className="mt-1 text-2xl font-semibold">{unanswered}</p>
            </div>
          </CardContent>
        </Card>
      </div>
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>Ritmo de la ronda</CardTitle>
          <CardDescription>
            Más rápida {formatElapsedMs(fastest)} · más lenta{" "}
            {formatElapsedMs(slowest)} · duración total{" "}
            {formatElapsedMs(session.durationMs)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Progress value={accuracy} />
        </CardContent>
      </Card>
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>Lista completa</CardTitle>
          <CardDescription>
            Revisa qué ocurrió en cada pregunta.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="flex flex-col">
            {session.answers.map((answer, index) => {
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
                      <Check className="size-4" />
                    ) : (
                      <X className="size-4" />
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
          variant="outline"
          onClick={onErrors}
          disabled={correct === session.answers.length}
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
            <Button onClick={onNext}>
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

function ResultMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border bg-muted/25 p-4">
      <p className="text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
    </div>
  )
}
