import { useState } from "react"
import { Clock3, Flag, LoaderCircle, ShieldCheck, Target } from "lucide-react"

import {
  buildFinalMissionPlan,
  getNextMission,
  type FinalMission,
} from "@/domain/final-mission-plan"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

export function FinalMissionDashboard({
  now = new Date(),
  completedMissionIds = [],
  onContinue,
  onManual,
}: {
  now?: Date
  completedMissionIds?: string[]
  onContinue: (mission: FinalMission) => void | Promise<void>
  onManual?: () => void
}) {
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const plan = buildFinalMissionPlan(now, { completedMissionIds })
  const completed = new Set(completedMissionIds)
  const next = getNextMission(plan, completed, now)
  const reading = plan.find((mission) => mission.kind === "reading")
  const totalQuestions = plan.reduce(
    (total, mission) => total + mission.count,
    0
  )
  const actionablePlan = plan.filter((mission) => mission.kind !== "reading")
  const progress = actionablePlan.length
    ? Math.round(
        (actionablePlan.filter((mission) => completed.has(mission.id)).length /
          actionablePlan.length) *
          100
      )
    : 0

  if (!next) {
    return (
      <section
        className="rounded-3xl border border-primary/20 bg-card p-6 shadow-sm"
        aria-labelledby="final-mission-complete-title"
      >
        <h1
          id="final-mission-complete-title"
          className="text-3xl font-semibold tracking-tight"
        >
          RUTA DEL DÍA COMPLETADA
        </h1>
        <p className="mt-3 text-muted-foreground">
          Terminaste todos los bloques accionables de hoy. Descansa y vuelve
          para la siguiente ruta.
        </p>
        <Progress
          aria-label="Progreso de la ruta de hoy"
          className="mt-5"
          value={100}
        />
      </section>
    )
  }
  const handleContinue = async () => {
    if (starting) return
    setStarting(true)
    setStartError(null)
    try {
      await onContinue(next)
    } catch (error) {
      setStartError(
        error instanceof Error
          ? error.message
          : "No se pudo preparar la ronda. Inténtalo de nuevo."
      )
    } finally {
      setStarting(false)
    }
  }
  return (
    <section
      className="overflow-hidden rounded-3xl border border-primary/20 bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--card))_58%)] shadow-sm"
      aria-labelledby="final-mission-title"
    >
      <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[minmax(0,1.25fr)_minmax(17rem,0.75fr)] lg:p-10">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="gap-1">
              <Flag className="size-3.5" aria-hidden="true" /> Banco Maestro
              Único
            </Badge>
            <Badge variant="outline">
              {totalQuestions.toLocaleString("es-HN")} preguntas programadas
            </Badge>
          </div>
          <h1
            id="final-mission-title"
            className="mt-5 max-w-3xl text-3xl font-semibold tracking-tight text-balance sm:text-4xl"
          >
            RUTA DEL DÍA
          </h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">
            Sigue los bloques en orden. Las preguntas nuevas vencidas pasan al
            siguiente día, excepto el viernes, que nunca supera 500.
          </p>

          <div className="mt-7 rounded-2xl border border-border/70 bg-background/80 p-5 sm:p-6">
            <p className="text-xs font-semibold tracking-[0.14em] text-primary uppercase">
              Próximo bloque
            </p>
            <h2 className="mt-2 text-xl font-semibold">{next.label}</h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
              {next.description}
            </p>
            {reading?.reading ? (
              <div
                className="mt-4 flex flex-wrap gap-2"
                aria-label="Lectura de hoy"
              >
                {reading.reading.map((item) => (
                  <Badge key={item} variant="outline">
                    {item}
                  </Badge>
                ))}
              </div>
            ) : null}
            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm">
              <span className="inline-flex items-center gap-2">
                <Target className="size-4 text-primary" aria-hidden="true" />
                {next.kind === "reading"
                  ? "Bloque de lectura"
                  : `${next.count} preguntas${next.familiarity === "known" ? " conocidas" : ""}`}
              </span>
              <span className="inline-flex items-center gap-2">
                <Clock3 className="size-4 text-primary" aria-hidden="true" />~
                {next.durationMinutes} min
              </span>
              <span className="inline-flex items-center gap-2">
                <ShieldCheck
                  className="size-4 text-primary"
                  aria-hidden="true"
                />
                {next.optional
                  ? "Opcional"
                  : next.blindPool
                    ? `Ciega ${next.blindPool}`
                    : "Solo GOLD"}
              </span>
            </div>
          </div>

          <Button
            size="lg"
            className="mt-6 min-h-12 w-full sm:w-auto sm:min-w-64"
            disabled={starting}
            aria-busy={starting}
            onClick={() => void handleContinue()}
          >
            {starting ? (
              <>
                <LoaderCircle className="animate-spin" aria-hidden="true" />{" "}
                PREPARANDO RONDA…
              </>
            ) : (
              "CONTINUAR MI RUTA"
            )}
          </Button>
          {starting ? (
            <p
              className="mt-3 text-sm text-muted-foreground"
              role="status"
              aria-live="polite"
            >
              Preparando el bloque {next.label.toLocaleLowerCase("es-HN")} del
              banco maestro. Puede tardar unos segundos.
            </p>
          ) : null}
          {startError ? (
            <p className="mt-3 text-sm text-destructive" role="alert">
              {startError}
            </p>
          ) : null}
          {onManual ? (
            <button
              type="button"
              disabled={starting}
              className="mt-4 block text-sm text-muted-foreground underline-offset-4 hover:underline sm:ml-5 sm:inline"
              onClick={onManual}
            >
              Configurar manualmente
            </button>
          ) : null}
        </div>

        <aside
          className="rounded-2xl bg-secondary/55 p-5 sm:p-6"
          aria-label="Progreso de hoy"
        >
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-medium">Progreso de hoy</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {
                  actionablePlan.filter((mission) => completed.has(mission.id))
                    .length
                }{" "}
                de {actionablePlan.length} bloques
              </p>
            </div>
            <strong className="text-3xl tabular-nums">{progress}%</strong>
          </div>
          <Progress
            aria-label="Progreso de la ruta de hoy"
            className="mt-4"
            value={progress}
          />
          <div className="mt-7 border-t border-border/70 pt-5">
            <p className="text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase">
              Prioridad crítica
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {[
                "PR43",
                "PR44",
                "Daniel 7",
                "Daniel 8",
                "Daniel 9",
                "Daniel 11",
              ].map((label) => (
                <Badge
                  key={label}
                  variant="outline"
                  className="bg-background/70"
                >
                  {label}
                </Badge>
              ))}
            </div>
          </div>
          <p className="mt-7 text-xs leading-5 text-muted-foreground">
            Las repeticiones inmediatas reparan; solo las recuperaciones
            separadas aumentan dominio.
          </p>
        </aside>
      </div>
    </section>
  )
}
