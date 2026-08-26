import { useState } from "react"
import { Clock3, ShieldCheck, Sparkles } from "lucide-react"
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
    // V5 ya baraja de forma determinista por exposición. Evitamos un segundo
    // barajado para que recargar no cambie la posición durante la ronda activa.
    shuffleOptions: false,
    perQuestionSeconds: mode.perQuestionSeconds,
    totalSeconds:
      competition && mode.perQuestionSeconds
        ? mode.perQuestionSeconds * count
        : null,
    bankSelection: "massive-v5",
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
  const selected = getMassiveTrainingMode(selectedId)
  const plan = buildFinal48HourPlan(signals)

  return (
    <section className="grid gap-5" aria-labelledby="massive-training-title">
      <Card className="overflow-hidden border-primary/25 bg-gradient-to-br from-primary/[0.08] via-card to-card shadow-sm">
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="gap-1">
              <Sparkles className="size-3.5" aria-hidden="true" />
              14,000 verificadas
            </Badge>
            <Badge variant="outline">2,338 hechos</Badge>
            <Badge variant="outline">15 % reserva ciega</Badge>
          </div>
          <div>
            <CardTitle id="massive-training-title">Entrenamiento masivo</CardTitle>
            <CardDescription className="mt-1 max-w-3xl">
              Elige un objetivo; el sistema cambia variantes, distractores y posiciones sin repetir el mismo hecho en la ronda.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <label className="grid gap-2 text-sm font-medium">
            Modo avanzado
            <select
              aria-label="Modo avanzado"
              className="h-11 w-full rounded-lg border bg-background px-3 text-sm text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              value={selectedId}
              onChange={(event) =>
                setSelectedId(event.target.value as MassiveTrainingModeId)
              }
            >
              {MASSIVE_TRAINING_MODES.map((mode) => (
                <option key={mode.id} value={mode.id}>
                  {mode.label} · {mode.count}
                </option>
              ))}
            </select>
            <span className="text-xs font-normal leading-5 text-muted-foreground">
              {selected.description}
            </span>
          </label>
          <Button
            className="min-h-11"
            onClick={() => onStart(configForMode(selected))}
          >
            Iniciar modo avanzado
          </Button>
        </CardContent>
      </Card>

      <Card>
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
    </section>
  )
}
