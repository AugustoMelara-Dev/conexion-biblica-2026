import { useMemo } from "react"
import {
  CheckCircle2,
  Clock3,
  Gauge,
  Play,
  RotateCcw,
  Sparkles,
  Trophy,
} from "lucide-react"
import { useApp } from "@/app/app-state"
import { SPRINT_DAILY_PLANS } from "@/domain/sprint-3x"
import type { SessionConfig } from "@/domain/types"
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

export function SprintDailyTracker({
  onStartSprint,
  onStartSimulation,
}: {
  onStartSprint: (config: SessionConfig) => void | Promise<void>
  onStartSimulation: (config: SessionConfig) => void | Promise<void>
}) {
  const { sessions = [], exposures = [], factMastery = [] } = useApp()

  // Calculate today's date in America/Tegucigalpa or local date
  const todayStr = useMemo(() => {
    try {
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: "America/Tegucigalpa",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).format(Date.now())
    } catch {
      return "2026-09-02"
    }
  }, [])

  const plan = SPRINT_DAILY_PLANS[todayStr] ?? SPRINT_DAILY_PLANS["2026-09-02"]

  // Calculate questions completed today
  const startOfDayMs = useMemo(() => {
    const d = new Date()
    d.setHours(0, 0, 0, 0)
    return d.getTime()
  }, [])

  const todayMetrics = useMemo(() => {
    let completedTotal = 0
    let completedPR = 0
    let completedDaniel = 0
    let errorsCount = 0
    let slowCount = 0

    sessions.forEach((session) => {
      if (session.startedAt >= startOfDayMs) {
        session.answers.forEach((ans) => {
          completedTotal++
          if (ans.questionKey.includes("PR") || ans.questionKey.includes("p-")) {
            completedPR++
          } else {
            completedDaniel++
          }
          if (!ans.result.isCorrect) errorsCount++
          if (ans.responseTimeMs > 6000 && ans.result.isCorrect) slowCount++
        })
      }
    })

    const exp1Count = exposures.filter((e) => e.exposures === 1).length
    const exp2Count = exposures.filter((e) => e.exposures === 2).length
    const exp3Count = exposures.filter((e) => e.exposures >= 3).length
    const masteredCount = factMastery.filter((f) => f.state === "mastered").length

    return {
      completedTotal,
      completedPR,
      completedDaniel,
      errorsCount,
      slowCount,
      exp1Count,
      exp2Count,
      exp3Count,
      masteredCount,
    }
  }, [sessions, exposures, factMastery, startOfDayMs])

  const percentTotal = Math.min(
    100,
    Math.round((todayMetrics.completedTotal / plan.targetTotal) * 100)
  )
  const percentPR = Math.min(
    100,
    Math.round((todayMetrics.completedPR / plan.targetPR) * 100)
  )
  const percentDaniel = Math.min(
    100,
    Math.round((todayMetrics.completedDaniel / plan.targetDaniel) * 100)
  )

  const sprintDirectedConfig: SessionConfig = {
    mode: "smart-review",
    count: 100,
    sourceWorks: ["Daniel", "Profetas y Reyes"],
    chapters: [],
    difficulties: [1, 2, 3, 4, 5],
    difficultyBands: ["BASIC", "MEDIUM", "HARD", "EXPERT"],
    types: ["single_choice", "fill_blank", "true_false"],
    statuses: ["all"],
    shuffleQuestions: true,
    shuffleOptions: true,
    perQuestionSeconds: 12,
    totalSeconds: null,
    bankSelection: "final-v7",
    strategy: "sprint-3x",
    trainingPresetId: "sprint-nacional-3x",
    includeBlind: false,
    massive: true,
  }

  const sprintSimulationConfig: SessionConfig = {
    mode: "simulation",
    count: 100,
    sourceWorks: ["Daniel", "Profetas y Reyes"],
    chapters: [],
    difficulties: [1, 2, 3, 4, 5],
    difficultyBands: ["HARD", "EXPERT"],
    types: ["single_choice", "fill_blank", "true_false"],
    statuses: ["all"],
    shuffleQuestions: true,
    shuffleOptions: true,
    perQuestionSeconds: 12,
    totalSeconds: 1200,
    bankSelection: "final-v7",
    strategy: "sprint-3x",
    trainingPresetId: "sprint-simulation-hidden",
    includeBlind: false,
    massive: true,
  }

  return (
    <Card className="overflow-hidden border-2 border-primary/35 bg-gradient-to-br from-card via-card to-primary/5 shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge variant="default" className="bg-primary text-primary-foreground font-semibold px-3 py-1">
              <Trophy className="mr-1.5 size-3.5" />
              Prioridad Competitiva · {plan.dayName}
            </Badge>
            <Badge variant="outline" className="border-primary/40 text-primary">
              Meta: {plan.targetTotal} preguntas hoy
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground">
            Examen: Sábado 5 de Septiembre 2026
          </div>
        </div>
        <CardTitle className="mt-2 text-2xl font-bold tracking-tight">
          Sprint Nacional 3X — 70% PR / 30% Daniel
        </CardTitle>
        <CardDescription className="text-sm leading-relaxed max-w-3xl">
          {plan.description} Cada bloque de 100 aplica exactamente: 70 preguntas de Profetas y Reyes (PR 39–44), 30 de Daniel (1–12), 45 de selección, 30 de completar y 25 de verdadero/falso.
        </CardDescription>
      </CardHeader>

      <CardContent className="grid gap-6">
        {/* Progress bars */}
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5 rounded-lg border bg-background/60 p-3">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-muted-foreground">Total hoy:</span>
              <span>
                {todayMetrics.completedTotal} / {plan.targetTotal} ({percentTotal}%)
              </span>
            </div>
            <Progress value={percentTotal} className="h-2" />
          </div>

          <div className="space-y-1.5 rounded-lg border bg-background/60 p-3">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-muted-foreground">Profetas y Reyes (70%):</span>
              <span>
                {todayMetrics.completedPR} / {plan.targetPR} ({percentPR}%)
              </span>
            </div>
            <Progress value={percentPR} className="h-2" />
          </div>

          <div className="space-y-1.5 rounded-lg border bg-background/60 p-3">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-muted-foreground">Daniel (30%):</span>
              <span>
                {todayMetrics.completedDaniel} / {plan.targetDaniel} ({percentDaniel}%)
              </span>
            </div>
            <Progress value={percentDaniel} className="h-2" />
          </div>
        </div>

        {/* 3X Spaced Retrieval Status Metrics */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="flex items-center gap-3 rounded-lg border bg-background/40 p-3">
            <Sparkles className="size-5 text-amber-500 shrink-0" />
            <div>
              <div className="text-xs text-muted-foreground">1ª Exposición</div>
              <div className="text-lg font-bold">{todayMetrics.exp1Count} hechos</div>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border bg-background/40 p-3">
            <Clock3 className="size-5 text-blue-500 shrink-0" />
            <div>
              <div className="text-xs text-muted-foreground">2ª Exposición</div>
              <div className="text-lg font-bold">{todayMetrics.exp2Count} confirmados</div>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border bg-background/40 p-3">
            <CheckCircle2 className="size-5 text-emerald-500 shrink-0" />
            <div>
              <div className="text-xs text-muted-foreground">Dominio 3X</div>
              <div className="text-lg font-bold">{todayMetrics.masteredCount} hechos</div>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border bg-background/40 p-3">
            <RotateCcw className="size-5 text-rose-500 shrink-0" />
            <div>
              <div className="text-xs text-muted-foreground">Reparación activa</div>
              <div className="text-lg font-bold">{todayMetrics.errorsCount} en cola</div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-1">
          <Button
            size="lg"
            className="flex-1 font-semibold text-base h-12 shadow-sm bg-primary text-primary-foreground hover:bg-primary/95"
            onClick={() => onStartSprint(sprintDirectedConfig)}
          >
            <Play className="mr-2 size-5 fill-current" />
            Iniciar Sprint Dirigido (100 preguntas · 70/30)
          </Button>

          {plan.includesSimulation ? (
            <Button
              size="lg"
              variant="outline"
              className="flex-1 font-semibold text-base h-12 border-primary/40 hover:bg-primary/5"
              onClick={() => onStartSimulation(sprintSimulationConfig)}
            >
              <Gauge className="mr-2 size-5 text-primary" />
              Simulación 5×20 (Mezcla Oculta)
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
