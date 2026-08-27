import { useState } from "react"
import { ChevronDown, Clock3, ShieldCheck, Target } from "lucide-react"
import { buildFinal48HourPlan, type ChapterSignal } from "@/domain/final-48h-plan"
import {
  getMassiveTrainingMode,
  MASSIVE_TRAINING_MODES,
  type MassiveTrainingMode,
  type MassiveTrainingModeId,
} from "@/domain/training-modes"
import type { SessionConfig } from "@/domain/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

function configForMode(mode: MassiveTrainingMode, count = mode.count): SessionConfig {
  const competition = [
    "national-final",
    "extreme-championship",
    "cold-mode",
    "speed-mode",
    "blind-simulation",
  ].includes(mode.id)
  return {
    mode: competition ? "simulation" : "smart-review",
    count,
    sourceWorks: mode.sourceWorks,
    chapters: mode.chapters,
    difficulties: mode.difficultyBands.flatMap((band) =>
      band === "BASIC" ? [1] : band === "MEDIUM" ? [2, 3] : band === "HARD" ? [4] : band === "EXPERT" ? [5] : []
    ),
    difficultyBands: mode.difficultyBands,
    types:
      mode.types.length > 0
        ? mode.types
        : ["single_choice", "fill_blank", "true_false"],
    statuses: mode.statuses,
    shuffleQuestions: true,
    // La semilla de la ronda cambia la posición entre sesiones y la conserva al recargar.
    shuffleOptions: true,
    perQuestionSeconds: mode.perQuestionSeconds,
    totalSeconds:
      competition && mode.perQuestionSeconds
        ? mode.perQuestionSeconds * count
        : null,
    bankSelection: "final-v7",
    strategy: "adaptive",
    trainingPresetId: mode.id,
    includeBlind: mode.includeBlind,
    massive: true,
  }
}

export function MassiveTrainingHub({
  onStart,
  signals = [],
}: {
  onStart: (config: SessionConfig) => void
  signals?: ChapterSignal[]
}) {
  const [selectedId, setSelectedId] =
    useState<MassiveTrainingModeId>("national-final")
  const [expanded, setExpanded] = useState(false)
  const selected = getMassiveTrainingMode(selectedId)
  const recommended = getMassiveTrainingMode("national-final")
  const plan = buildFinal48HourPlan(signals)

  return (
    <section className="grid gap-4" aria-label="Modos avanzados">
      <Card className="overflow-hidden border-primary/25 bg-card shadow-none">
        <CardContent className="grid gap-5 p-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:p-6">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-sm font-medium text-primary">
              <Target className="size-4" aria-hidden="true" />
              Próximo paso
            </div>
            <CardTitle id="massive-training-title" className="mt-2 text-xl tracking-tight">
              Ronda recomendada
            </CardTitle>
            <CardDescription className="mt-2 max-w-2xl leading-6">
              Final nacional de 100 preguntas: 30 completar, 25 verdadero/falso y 45 de selección. Sin repetir hechos.
            </CardDescription>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant="secondary">12,000 preguntas GOLD</Badge>
              <Badge variant="outline">3,000 hechos</Badge>
              <Badge variant="outline">Reserva ciega protegida</Badge>
            </div>
          </div>
          <div className="grid gap-2 sm:min-w-56">
            <Button
              className="min-h-12 w-full"
              onClick={() => onStart(configForMode(recommended))}
            >
              Empezar final nacional · 100
            </Button>
            <Button
              variant="ghost"
              className="min-h-11 w-full"
              aria-expanded={expanded}
              aria-controls="training-plan-details"
              onClick={() => setExpanded((current) => !current)}
            >
              {expanded ? "Ocultar plan y modos" : "Ver plan y modos"}
              <ChevronDown
                className={`transition-transform ${expanded ? "rotate-180" : ""}`}
                aria-hidden="true"
              />
            </Button>
          </div>
        </CardContent>
      </Card>

      {expanded ? <div id="training-plan-details" className="grid gap-4">
      <Card className="shadow-none">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Elegir otro modo</CardTitle>
          <CardDescription>Usa esto solo cuando quieras concentrarte en un tipo o capítulo.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <label className="grid gap-2 text-sm font-medium">
            Modo avanzado
            <select
              aria-label="Modo avanzado"
              className="h-11 w-full rounded-lg border bg-background px-3 text-sm text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              value={selectedId}
              onChange={(event) => setSelectedId(event.target.value as MassiveTrainingModeId)}
            >
              {MASSIVE_TRAINING_MODES.map((mode) => (
                <option key={mode.id} value={mode.id}>{mode.label} · {mode.count}</option>
              ))}
            </select>
            <span className="text-xs font-normal leading-5 text-muted-foreground">{selected.description}</span>
          </label>
          <Button className="min-h-11" onClick={() => onStart(configForMode(selected))}>
            Iniciar modo avanzado
          </Button>
        </CardContent>
      </Card>

      <Card className="shadow-none">
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Clock3 className="size-5 text-primary" aria-hidden="true" />
                PLAN FINAL — 48 HORAS
              </CardTitle>
              <CardDescription className="mt-1">
                Diez bloques adaptativos: diagnóstico, corrección, velocidad y cierre ciego.
              </CardDescription>
            </div>
            <Badge className="gap-1">
              <ShieldCheck className="size-3.5" aria-hidden="true" />
              1,100 preguntas
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-5 lg:grid-cols-2">
          {[1, 2].map((day) => (
            <section key={day} aria-labelledby={`final-day-${day}`} className="grid gap-2">
              <h3 id={`final-day-${day}`} className="text-sm font-semibold text-foreground">
                Día {day}
              </h3>
              <div className="grid gap-2">
                {plan
                  .filter((block) => block.day === day)
                  .map((block, index) => {
                    const mode = getMassiveTrainingMode(block.modeId)
                    return (
                      <Button
                        key={block.id}
                        variant="outline"
                        className="h-auto min-h-14 justify-between gap-4 px-3 py-2 text-left whitespace-normal"
                        aria-label={`${block.label} · ${block.count} preguntas`}
                        onClick={() => onStart(configForMode(mode, block.count))}
                      >
                        <span className="flex min-w-0 items-center gap-3">
                          <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-secondary text-xs font-bold text-primary">
                            {index + 1}
                          </span>
                          <span className="font-medium">{block.label}</span>
                        </span>
                        <span className="shrink-0 text-xs text-muted-foreground">
                          {block.count}
                        </span>
                      </Button>
                    )
                  })}
              </div>
            </section>
          ))}
        </CardContent>
      </Card>
      </div> : null}
    </section>
  )
}
