import { ArrowRight, BarChart3, Check, Clock3, Flame, Gauge, RotateCcw, Target } from "lucide-react"
import { useApp } from "@/app/app-state"
import { BankSelector } from "@/components/bank-selector"
import { FinalMissionDashboard } from "@/components/final-mission-dashboard"
import { MetricStrip } from "@/components/layout/metric-strip"
import { SectionHeader } from "@/components/layout/section-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import type { BankSelection, SessionConfig } from "@/domain/types"
import type { FinalMission } from "@/domain/final-mission-plan"
import { formatElapsedMs } from "@/lib/format"

const activeBankLabels: Record<BankSelection, string> = {
  "curated-v4": "V4 — cobertura amplia",
  "prep-v3": "V3 — Preparación intensiva de 4 días",
  "legacy-v1": "V1 — Clásica",
  mixed: "Mixto curado",
  "master-v2": "V2 — Fuente técnica",
  "massive-v5": "V5 — Entrenamiento masivo",
  "consolidation-v5": "V6 — Aprendizaje competitivo",
}

function missionConfig(mission: FinalMission): SessionConfig {
  return {
    mode: mission.mode,
    count: mission.count,
    sourceWorks: ["Daniel", "Profetas y Reyes"],
    chapters: mission.chapters,
    difficulties: [1, 2, 3, 4, 5],
    difficultyBands: ["BASIC", "MEDIUM", "HARD", "EXPERT"],
    types: ["single_choice", "fill_blank", "true_false"],
    statuses: ["all"],
    shuffleQuestions: true,
    shuffleOptions: true,
    perQuestionSeconds: mission.mode === "simulation" ? 25 : null,
    totalSeconds: mission.mode === "simulation" ? mission.count * 25 : null,
    bankSelection: "consolidation-v5",
    strategy: "adaptive",
    trainingPresetId: mission.id,
    includeBlind: mission.blindPool !== null,
    massive: true,
  }
}

export function DashboardPage({ onStartMission }: { onStartMission?: (config: SessionConfig) => void }) {
  const { statistics, banks, questions, sessions, progress, exposures = [], factMastery = [], consolidationManifest, setNav, bankSelection, setBankSelection, bankCounts } = useApp()
  const { general } = statistics
  const sources = statistics.sources.filter((item) => item.key === "Daniel" || item.key === "Profetas y Reyes")
  const currentStreak = progress.size ? Math.max(...[...progress.values()].map((item) => item.currentCorrectStreak), 0) : 0
  const recommendation = general.unseen > 0
    ? `${general.unseen} preguntas nuevas te esperan.`
    : general.difficult > 0
      ? `${general.difficult} preguntas difíciles merecen un repaso.`
      : "Mantén el ritmo con una ronda breve."
  const evidenceAccuracy = (kind: "cold" | "deferred" | "blind") => {
    const totals = exposures.reduce((sum, exposure) => ({
      attempts: sum.attempts + (exposure.evidence?.[kind].attempts ?? 0),
      correct: sum.correct + (exposure.evidence?.[kind].correct ?? 0),
    }), { attempts: 0, correct: 0 })
    return totals.attempts ? Math.round((totals.correct / totals.attempts) * 100) : 0
  }
  const masteredFacts = factMastery.filter((fact) => fact.state === "mastered").length

  return (
    <div className="flex min-w-0 flex-col gap-10">
      <FinalMissionDashboard
        completedMissionIds={sessions.map((session) => session.config.trainingPresetId).filter((id): id is string => Boolean(id))}
        onContinue={(mission) => onStartMission ? onStartMission(missionConfig(mission)) : setNav("practice")}
        onManual={() => setNav("practice")}
      />

      <MetricStrip
        items={[
          { label: "Precisión fría", value: `${evidenceAccuracy("cold")}%`, detail: "Primer intento sin feedback", icon: Target },
          { label: "Precisión diferida", value: `${evidenceAccuracy("deferred")}%`, detail: "Después de un intervalo", icon: Clock3 },
          { label: "Precisión ciega", value: `${evidenceAccuracy("blind")}%`, detail: "Reserva A/B", icon: Gauge },
          { label: "Dominio por hechos", value: masteredFacts, detail: `${factMastery.length} hechos con evidencia`, icon: Check },
        ]}
      />

      <section aria-labelledby="history-config-title">
        <p className="text-sm font-medium text-primary">Historial y configuración</p>
        <h2 id="history-config-title" className="mt-2 text-2xl font-semibold tracking-tight">Tu preparación, sin perder lo anterior.</h2>
        <p className="mt-2 max-w-3xl text-muted-foreground">V1–V5 permanecen disponibles como perfiles históricos; V6 GOLD dirige el plan principal.</p>
      </section>

      <details className="rounded-2xl border border-border/70 p-5">
        <summary className="cursor-pointer text-sm font-semibold">Perfiles históricos y configuración manual</summary>
      <section aria-label="Selección de versión" className="mt-5 flex flex-col gap-4">
        <SectionHeader
          title="Elige tu versión"
          description="Cada pregunta conserva el progreso de su banco de origen."
          action={<Badge variant="outline">Perfil activo: {activeBankLabels[bankSelection]}</Badge>}
        />
        <BankSelector
          value={bankSelection}
          onChange={setBankSelection}
          legacyCount={bankCounts.legacy}
          masterCount={bankCounts.master}
          prepCount={bankCounts.prep}
          curatedCount={bankCounts.curated}
          consolidationCount={consolidationManifest?.gold_questions ?? bankCounts.consolidation ?? 0}
        />
      </section>
      </details>

      <MetricStrip
        items={[
          { label: "Precisión general", value: `${general.accuracy}%`, detail: `${general.correct} correctas de ${general.total}`, icon: Target },
          { label: "Preguntas respondidas", value: general.total, detail: `${general.seen} apariciones registradas` },
          { label: "Tiempo promedio", value: formatElapsedMs(general.averageResponseTimeMs), detail: `Mejor ${formatElapsedMs(general.bestResponseTimeMs)}`, icon: Clock3 },
          { label: "Racha actual", value: currentStreak, detail: `${sessions.length} sesiones realizadas`, icon: Flame },
        ]}
      />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(18rem,0.85fr)]">
        <section aria-label="Rendimiento por fuente" className="min-w-0 rounded-2xl bg-secondary/45 p-6 sm:p-8">
          <SectionHeader
            title="Rendimiento por fuente"
            description="La foto actual de tu preparación."
            action={<Button variant="ghost" size="sm" onClick={() => setNav("stats")}>Ver detalle <ArrowRight data-icon="inline-end" /></Button>}
          />
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {sources.map((source) => <SourceMetric key={source.key} label={source.label} metric={source} />)}
          </div>
        </section>

        <section aria-labelledby="recommendation-title" className="rounded-2xl border border-border/70 p-6 sm:p-8">
          <p className="text-sm font-medium text-primary">Siguiente paso</p>
          <h2 id="recommendation-title" className="mt-2 text-2xl font-semibold tracking-tight">Recomendación para hoy</h2>
          <p className="mt-3 max-w-[38ch] text-muted-foreground">{recommendation}</p>
          <div className="mt-8 flex items-end justify-between gap-4">
            <div>
              <p className="text-3xl font-semibold tabular-nums">{questions.length ? Math.round((general.seen / questions.length) * 100) : 0}%</p>
              <p className="text-sm text-muted-foreground">cobertura del banco</p>
            </div>
            <Button onClick={() => setNav("practice")}>Practicar</Button>
          </div>
        </section>
      </div>

      <section aria-label="Rendimiento por capítulo" className="min-w-0">
        <SectionHeader title="Rendimiento por capítulo" description="Ordenado de peor a mejor precisión." />
        <div className="mt-5 overflow-x-auto rounded-xl border border-border/70">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Capítulo</TableHead>
                <TableHead>Respondidas</TableHead>
                <TableHead>Precisión</TableHead>
                <TableHead>Tiempo medio</TableHead>
                <TableHead>Dominio</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {statistics.chapters.slice(0, 8).map((row) => (
                <TableRow key={row.key}>
                  <TableCell className="font-medium">{row.label}</TableCell>
                  <TableCell className="tabular-nums">{row.total}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2"><span className="tabular-nums">{row.accuracy}%</span><Progress className="w-20" value={row.accuracy} /></div>
                  </TableCell>
                  <TableCell className="tabular-nums">{formatElapsedMs(row.averageResponseTimeMs)}</TableCell>
                  <TableCell><Badge variant={row.mastery >= 4 ? "default" : "secondary"}>{row.mastery}/5</Badge></TableCell>
                </TableRow>
              ))}
              {statistics.chapters.length === 0 ? (
                <TableRow><TableCell colSpan={5} className="h-24 text-center text-muted-foreground">Aún no hay capítulos con preguntas cargadas.</TableCell></TableRow>
              ) : null}
            </TableBody>
          </Table>
        </div>
      </section>

      <section aria-label="Mis puntos débiles" className="min-w-0">
        <SectionHeader
          title="Mis puntos débiles"
          description="Úsalos para elegir una ronda que refuerce lo que más lo necesita."
          action={<Button variant="ghost" size="sm" onClick={() => setNav("stats")}>Ver progreso <ArrowRight data-icon="inline-end" /></Button>}
        />
        <div className="mt-5 grid divide-y divide-border/70 rounded-xl border border-border/70 lg:grid-cols-3 lg:divide-x lg:divide-y-0">
          <WeakLine
            icon={BarChart3}
            label="Capítulo a reforzar"
            value={statistics.weakChapters[0]?.label ?? "Todavía no hay datos"}
            detail={statistics.weakChapters[0] ? `${statistics.weakChapters[0].accuracy}% de precisión` : "Completa una ronda"}
          />
          <WeakLine
            icon={Gauge}
            label="Tipo más débil"
            value={statistics.weakTypes[0]?.label ?? "Todavía no hay datos"}
            detail={statistics.weakTypes[0] ? `${statistics.weakTypes[0].accuracy}% de precisión` : "Completa una ronda"}
          />
          <div className="flex min-w-0 flex-col justify-between gap-4 p-5">
            <WeakLine icon={RotateCcw} label="Más falladas" value={`${statistics.mostFailed.length} preguntas detectadas`} detail="Repaso recomendado" compact />
            <Button className="self-start" variant="outline" onClick={() => setNav("practice")}>Abrir práctica enfocada <ArrowRight data-icon="inline-end" /></Button>
          </div>
        </div>
      </section>

      <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground" role="status">
        <Check className="size-4 text-chart-2" aria-hidden="true" />
        Guardado local: {banks.length} bancos · {questions.length} preguntas · IndexedDB activo.
      </p>
    </div>
  )
}

function SourceMetric({ label, metric }: { label: string; metric: { accuracy: number; total: number; correct: number; averageResponseTimeMs: number } }) {
  return (
    <div className="min-w-0 rounded-xl bg-background/70 p-4">
      <div className="flex items-center justify-between gap-3"><span className="text-sm font-medium">{label}</span><span className="text-2xl font-semibold tabular-nums">{metric.accuracy}%</span></div>
      <Progress className="mt-4" value={metric.accuracy} />
      <div className="mt-3 flex justify-between gap-3 text-xs text-muted-foreground"><span>{metric.correct}/{metric.total} correctas</span><span className="shrink-0 tabular-nums">{formatElapsedMs(metric.averageResponseTimeMs)} medio</span></div>
    </div>
  )
}

function WeakLine({ icon: Icon, label, value, detail, compact = false }: { icon: typeof BarChart3; label: string; value: string; detail: string; compact?: boolean }) {
  return (
    <div className={`flex min-w-0 items-start gap-3 ${compact ? "" : "p-5"}`}>
      <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary"><Icon aria-hidden="true" /></div>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">{label}</p>
        <p className="mt-1 truncate text-sm font-medium">{value}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{detail}</p>
      </div>
    </div>
  )
}
