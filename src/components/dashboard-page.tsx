import {
  ArrowRight,
  BarChart3,
  Gauge,
  RotateCcw,
} from "lucide-react"
import { useApp } from "@/app/app-state"
import { EmergencyDashboard } from "@/components/emergency-dashboard"
import { SprintDailyTracker } from "@/components/sprint-daily-tracker"
import { FinalMissionDashboard } from "@/components/final-mission-dashboard"
import { SectionHeader } from "@/components/layout/section-header"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import type { Question, SessionConfig } from "@/domain/types"
import type { FinalMission } from "@/domain/final-mission-plan"
import { formatElapsedMs } from "@/lib/format"

function missionConfig(mission: FinalMission): SessionConfig {
  const isNew = mission.kind === "new" || mission.kind === "adversarial"
  const isHardExpert = mission.kind === "hard-expert"
  const isReview = mission.kind === "review"
  const isWarmUp = mission.kind === "warm-up"
  const types =
    mission.id === "27-fill"
      ? (["fill_blank"] as const)
      : mission.id === "27-true-false"
        ? (["true_false"] as const)
        : mission.id === "27-context"
          ? (["single_choice"] as const)
          : (['single_choice', 'fill_blank', 'true_false'] as const)

  return {
    mode: isNew
      ? 'new'
      : isHardExpert
        ? 'difficult'
        : isReview
          ? 'smart-review'
          : mission.mode,
    count: mission.count,
    sourceWorks: ['Daniel', 'Profetas y Reyes'],
    chapters: mission.chapters,
    difficulties: isHardExpert ? [4, 5] : [1, 2, 3, 4, 5],
    difficultyBands: isHardExpert
      ? (["HARD", "EXPERT"] as const)
      : (["BASIC", "MEDIUM", "HARD", "EXPERT"] as const),
    types: [...types],
    statuses: isNew
      ? ['new']
      : isReview
        ? ['all']
        : isWarmUp
          ? ['mastered']
          : ['all'],
    shuffleQuestions: true,
    shuffleOptions: true,
    perQuestionSeconds: mission.mode === 'simulation' ? 25 : null,
    totalSeconds: mission.mode === 'simulation' ? mission.count * 25 : null,
    bankSelection: 'final-v7',
    strategy: 'adaptive',
    trainingPresetId: mission.id,
    includeBlind: mission.blindPool !== null,
    massive: !isWarmUp,
  }
}

export function DashboardPage({
  onStartMission,
  onContinueRound,
}: {
  onStartMission?: (config: SessionConfig, questions?: Question[]) => void | Promise<void>
  onContinueRound?: () => void
}) {
  const { setNav, sessions = [], statistics } = useApp()
  const sources = (statistics?.sources ?? []).filter(
    (item) => item.key === "Daniel" || item.key === "Profetas y Reyes"
  )

  return (
    <div className="flex min-w-0 flex-col gap-6">
      <EmergencyDashboard
        onStartEmergencyMode={(cfg, questions) => {
          if (onStartMission) void onStartMission(cfg, questions)
          else setNav("practice")
        }}
        onConfigureRound={() => setNav("practice")}
        onContinueRound={() => {
          if (onContinueRound) onContinueRound()
          else setNav("practice")
        }}
      />

      <details open={import.meta.env?.MODE === "test" ? true : undefined} className="rounded-xl border bg-card/40 p-4 text-xs text-muted-foreground">
        <summary className="cursor-pointer font-medium text-foreground">
          Rutas de práctica adicionales (Sprint Nacional 3X y Misiones)
        </summary>
        <div className="mt-4 space-y-6 pt-3 border-t">
          <SprintDailyTracker
            onStartSprint={(cfg) =>
              onStartMission ? onStartMission(cfg) : setNav("practice")
            }
            onStartSimulation={(cfg) =>
              onStartMission ? onStartMission(cfg) : setNav("practice")
            }
            onConfigureRound={() => setNav("practice")}
          />
          <FinalMissionDashboard
            completedMissionIds={sessions
              .map((session) => session.config.trainingPresetId)
              .filter((id): id is string => Boolean(id))}
            onContinue={(mission) =>
              onStartMission
                ? onStartMission(missionConfig(mission))
                : setNav("practice")
            }
            onManual={() => setNav("practice")}
          />

          {sources.length > 0 ? (
            <section aria-labelledby="sources-progress-title">
              <SectionHeader
                title="Progreso por material"
                description="Rendimiento del participante en Daniel y Profetas y Reyes."
              />
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                {sources.map((source) => (
                  <SourceMetric key={source.key} label={source.label} metric={source} />
                ))}
              </div>
            </section>
          ) : null}

          {statistics ? (
            <section aria-label="Mis puntos débiles" className="min-w-0">
              <SectionHeader
                title="Mis puntos débiles"
                description="Úsalos para elegir una ronda que refuerce lo que más lo necesita."
                action={
                  <Button variant="ghost" size="sm" onClick={() => setNav("stats")}>
                    Ver progreso <ArrowRight data-icon="inline-end" />
                  </Button>
                }
              />
              <div className="mt-5 grid divide-y divide-border/70 rounded-xl border border-border/70 lg:grid-cols-3 lg:divide-x lg:divide-y-0">
                <WeakLine
                  icon={BarChart3}
                  label="Capítulo a reforzar"
                  value={statistics.weakChapters[0]?.label ?? "Todavía no hay datos"}
                  detail={
                    statistics.weakChapters[0]
                      ? `${statistics.weakChapters[0].accuracy}% de precisión`
                      : "Completa una ronda"
                  }
                />
                <WeakLine
                  icon={Gauge}
                  label="Tipo más débil"
                  value={statistics.weakTypes[0]?.label ?? "Todavía no hay datos"}
                  detail={
                    statistics.weakTypes[0]
                      ? `${statistics.weakTypes[0].accuracy}% de precisión`
                      : "Completa una ronda"
                  }
                />
                <div className="flex min-w-0 flex-col justify-between gap-4 p-5">
                  <WeakLine
                    icon={RotateCcw}
                    label="Más falladas"
                    value={`${statistics.mostFailed.length} preguntas detectadas`}
                    detail="Repaso recomendado"
                    compact
                  />
                  <Button
                    className="self-start"
                    variant="outline"
                    onClick={() => setNav("practice")}
                  >
                    Abrir práctica enfocada <ArrowRight data-icon="inline-end" />
                  </Button>
                </div>
              </div>
            </section>
          ) : null}
        </div>
      </details>
    </div>
  )
}

function SourceMetric({
  label,
  metric,
}: {
  label: string
  metric: {
    accuracy: number
    total: number
    correct: number
    averageResponseTimeMs: number
  }
}) {
  return (
    <div className="min-w-0 rounded-xl bg-background/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-2xl font-semibold tabular-nums">
          {metric.accuracy}%
        </span>
      </div>
      <Progress
        aria-label={`Precisión de ${label}`}
        className="mt-4"
        value={metric.accuracy}
      />
      <div className="mt-3 flex justify-between gap-3 text-xs text-muted-foreground">
        <span>
          {metric.correct}/{metric.total} correctas
        </span>
        <span className="shrink-0 tabular-nums">
          {formatElapsedMs(metric.averageResponseTimeMs)} medio
        </span>
      </div>
    </div>
  )
}

function WeakLine({
  icon: Icon,
  label,
  value,
  detail,
  compact = false,
}: {
  icon: typeof BarChart3
  label: string
  value: string
  detail: string
  compact?: boolean
}) {
  return (
    <div className={`flex min-w-0 items-start gap-3 ${compact ? "" : "p-5"}`}>
      <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary">
        <Icon aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold tracking-[0.1em] text-muted-foreground uppercase">
          {label}
        </p>
        <p className="mt-1 truncate text-sm font-medium">{value}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{detail}</p>
      </div>
    </div>
  )
}
