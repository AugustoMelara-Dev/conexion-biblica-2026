import { Clock3, Heart, Target, TrendingUp, Trophy } from "lucide-react"
import { useApp } from "@/app/app-state"
import { FamilyMasteryPanel } from "@/components/family-mastery-panel"
import { FactCoveragePanel } from "@/components/fact-coverage-panel"
import { MetricStrip } from "@/components/layout/metric-strip"
import { PageHeader } from "@/components/layout/page-header"
import { SectionHeader } from "@/components/layout/section-header"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { formatElapsedMs } from "@/lib/format"
import {
  buildSimulationStatistics,
  type AggregateMetric,
} from "@/lib/statistics"

export function StatisticsPage() {
  const { statistics, sessions, questions, progress, exposures = [], massiveManifest, consolidationManifest } = useApp()
  const { general } = statistics
  const simulation = buildSimulationStatistics(sessions)
  const uniqueSeen = Math.max(0, questions.length - general.unseen)
  const trend = sessionTrend(sessions)
  const summaryMetrics = [
    {
      label: "Tendencia",
      value: trend ? `${trend.delta > 0 ? "+" : ""}${trend.delta} pp` : "—",
      detail: trend
        ? `Última ronda ${trend.latest}% vs anterior ${trend.previous}%`
        : "Completa dos rondas para compararlas",
      icon: TrendingUp,
    },
    {
      label: "Precisión de práctica",
      value: `${general.accuracy}%`,
      detail: `${general.correct} aciertos · ${general.incorrect} fallos`,
      icon: Target,
    },
    {
      label: "Tiempo medio",
      value: formatElapsedMs(general.averageResponseTimeMs),
      detail: `Mediana ${formatElapsedMs(general.medianResponseTimeMs)}`,
      icon: Clock3,
    },
    {
      label: "Cobertura",
      value: `${uniqueSeen}/${questions.length}`,
      detail: `${general.unseen} sin ver · ${general.mastered} dominadas`,
      icon: Trophy,
    },
    {
      label: "Favoritas",
      value: general.favorite,
      detail: "Marcadas para volver a ellas",
      icon: Heart,
    },
  ]

  return (
    <div className="flex min-w-0 flex-col gap-8">
      <PageHeader
        eyebrow="Evidencia de tu práctica"
        title="Progreso"
        description="Detecta qué sabes, qué falta y dónde conviene practicar. El dominio de práctica y el resultado competitivo se calculan por separado."
      />
      <MetricStrip items={summaryMetrics} />
      <Tabs defaultValue="summary" className="min-w-0">
        <TabsList
          aria-label="Vista estadística"
          className="grid w-full grid-cols-2 gap-1 p-1 group-data-[orientation=horizontal]/tabs:h-auto sm:grid-cols-3"
        >
          <TabsTrigger value="summary" className="h-11 whitespace-normal">
            Resumen
          </TabsTrigger>
          <TabsTrigger value="chapters" className="h-11 whitespace-normal">
            Capítulos
          </TabsTrigger>
          <TabsTrigger value="types" className="h-11 whitespace-normal">
            Tipos
          </TabsTrigger>
          <TabsTrigger value="families" className="h-11 whitespace-normal">
            Familias
          </TabsTrigger>
          <TabsTrigger value="levels" className="h-11 whitespace-normal">
            Dificultad
          </TabsTrigger>
          <TabsTrigger value="sources" className="h-11 whitespace-normal">
            Fuentes
          </TabsTrigger>
        </TabsList>
        <TabsContent value="summary" className="mt-5">
          <div className="flex flex-col gap-6">
            {consolidationManifest || massiveManifest ? (
              <FactCoveragePanel
                totalFacts={consolidationManifest?.gold_facts ?? massiveManifest!.totals.facts}
                exposures={exposures}
              />
            ) : null}
            <Card className="border-primary/20 bg-primary/[0.03] shadow-none">
              <CardHeader>
                <CardTitle>Resultado de simulacros</CardTitle>
                <CardDescription>
                  Sólo incluye rondas de Simulacro; repetir para aprender no
                  cambia estas cifras.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-3">
                <SummaryMetric
                  label="Precisión"
                  value={`${simulation.accuracy}%`}
                  detail={`${simulation.sessions} simulacros · mejor ${simulation.bestAccuracy}%`}
                />
                <SummaryMetric
                  label="Respuestas"
                  value={simulation.answers}
                  detail={`${simulation.correct} correctas · ${simulation.incorrect} incorrectas`}
                />
                <SummaryMetric
                  label="Tiempo promedio"
                  value={formatElapsedMs(simulation.averageResponseTimeMs)}
                  detail={`${simulation.unanswered} sin responder`}
                />
              </CardContent>
            </Card>
            <WeaknessSummary
              weakChapters={statistics.weakChapters}
              weakTypes={statistics.weakTypes}
            />
          </div>
        </TabsContent>
        <TabsContent value="chapters" className="mt-5">
          <MetricTable
            title="Rendimiento por capítulo"
            description="Ordenado de peor a mejor."
            rows={statistics.chapters}
            extraHeader="Capítulo"
          />
        </TabsContent>
        <TabsContent value="types" className="mt-5">
          <MetricTable
            title="Rendimiento por tipo"
            description="Prioriza los tipos con menor precisión."
            rows={statistics.types}
            extraHeader="Tipo"
          />
        </TabsContent>
        <TabsContent value="families" className="mt-5">
          <FamilyMasteryPanel questions={questions} progress={progress} />
        </TabsContent>
        <TabsContent value="levels" className="mt-5">
          <MetricTable
            title="Rendimiento por dificultad"
            description="Compara la presión real de cada nivel."
            rows={statistics.difficulties}
            extraHeader="Dificultad"
          />
        </TabsContent>
        <TabsContent value="sources" className="mt-5">
          <MetricTable
            title="Rendimiento por fuente"
            description="Daniel y Profetas y Reyes por separado."
            rows={statistics.sources}
            extraHeader="Fuente"
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function SummaryMetric({
  label,
  value,
  detail,
}: {
  label: string
  value: React.ReactNode
  detail: string
}) {
  return (
    <div className="min-w-0 border-l-2 border-primary/20 py-2 pl-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
    </div>
  )
}

function MetricTable({
  title,
  description,
  rows,
  extraHeader,
}: {
  title: string
  description: string
  rows: AggregateMetric[]
  extraHeader: string
}) {
  return (
    <section>
      <SectionHeader title={title} description={description} />
      <div
        role="table"
        aria-label={title}
        className="mt-5 divide-y rounded-xl border border-border/70"
      >
        <div role="rowgroup" className="sr-only bg-muted/40 sm:not-sr-only">
          <div
            role="row"
            className="grid grid-cols-[minmax(10rem,1.6fr)_repeat(5,minmax(0,0.7fr))] gap-3 px-4 py-3 text-xs font-medium text-muted-foreground"
          >
            <span role="columnheader">{extraHeader}</span>
            <span role="columnheader">Respondidas</span>
            <span role="columnheader">Precisión</span>
            <span role="columnheader">Tiempo medio</span>
            <span role="columnheader">Fallos</span>
            <span role="columnheader">Dominio</span>
          </div>
        </div>
        <div role="rowgroup">
          {rows.map((row) => (
            <div
              key={row.key}
              role="row"
              className="grid gap-x-4 gap-y-2 px-4 py-4 sm:grid-cols-[minmax(10rem,1.6fr)_repeat(5,minmax(0,0.7fr))] sm:items-center"
            >
              <span role="cell" className="font-medium">
                {row.label}
              </span>
              <MetricCell label="Respondidas" value={row.total} />
              <MetricCell
                label="Precisión"
                value={
                  <span
                    className={
                      row.accuracy < 70
                        ? "font-semibold text-destructive"
                        : "font-medium"
                    }
                  >
                    {row.accuracy}%
                  </span>
                }
              />
              <MetricCell
                label="Tiempo medio"
                value={formatElapsedMs(row.averageResponseTimeMs)}
              />
              <MetricCell label="Fallos" value={row.incorrect} />
              <div
                role="cell"
                className="flex items-center justify-between gap-2 text-sm tabular-nums sm:block"
              >
                <span className="text-muted-foreground sm:hidden">Dominio</span>
                <Badge variant={row.mastery >= 4 ? "default" : "secondary"}>
                  {row.mastery}/5
                </Badge>
              </div>
            </div>
          ))}
          {rows.length === 0 ? (
            <div
              role="row"
              className="px-4 py-10 text-center text-sm text-muted-foreground"
            >
              <span role="cell">Sin datos todavía.</span>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}

function sessionTrend(sessions: ReturnType<typeof useApp>["sessions"]) {
  const recent = [...sessions]
    .sort((left, right) => right.completedAt - left.completedAt)
    .slice(0, 2)
  if (recent.length < 2) return null
  const latest = sessionAccuracy(recent[0])
  const previous = sessionAccuracy(recent[1])
  return { latest, previous, delta: latest - previous }
}

function sessionAccuracy(
  session: ReturnType<typeof useApp>["sessions"][number]
) {
  return session.answers.length === 0
    ? 0
    : Math.round(
        (session.answers.filter((answer) => answer.result.isCorrect).length /
          session.answers.length) *
          100
      )
}

function MetricCell({
  label,
  value,
}: {
  label: string
  value: React.ReactNode
}) {
  return (
    <span
      role="cell"
      className="flex items-center justify-between gap-2 text-sm tabular-nums sm:block"
    >
      <span className="text-muted-foreground sm:hidden">{label}</span>
      {value}
    </span>
  )
}

function WeaknessSummary({
  weakChapters,
  weakTypes,
}: {
  weakChapters: AggregateMetric[]
  weakTypes: AggregateMetric[]
}) {
  return (
    <section
      aria-label="Prioridades de práctica"
      className="grid gap-5 lg:grid-cols-2"
    >
      <WeakCard title="Capítulos con menor precisión" rows={weakChapters} />
      <WeakCard title="Tipos con menor precisión" rows={weakTypes} />
    </section>
  )
}

function WeakCard({ title, rows }: { title: string; rows: AggregateMetric[] }) {
  return (
    <Card className="shadow-none">
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>Prioriza los tres primeros.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {rows.map((row, index) => (
          <div
            key={row.key}
            className="grid grid-cols-[1.75rem_minmax(0,1fr)_auto] items-center gap-3"
          >
            <span className="flex size-7 items-center justify-center rounded-full bg-muted text-xs font-semibold">
              {index + 1}
            </span>
            <span className="min-w-0 text-sm font-medium">{row.label}</span>
            <span className="text-right text-sm">
              <strong className="text-destructive tabular-nums">
                {row.accuracy}%
              </strong>
              <span className="ml-2 text-xs text-muted-foreground">
                {row.incorrect} fallos
              </span>
            </span>
          </div>
        ))}
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Aparecerán después de tus primeras respuestas.
          </p>
        ) : null}
      </CardContent>
    </Card>
  )
}
