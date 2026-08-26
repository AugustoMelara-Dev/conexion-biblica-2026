import { ArrowRight } from "lucide-react"
import type { ReactNode } from "react"
import type { SessionConfig, SessionMode } from "@/domain/types"
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
import { getModeOption } from "@/components/practice/mode-picker"

export function RoundSummary({
  eligibleCount,
  count,
  mode,
  onStart,
  disabled,
  startLabel = "Comenzar ronda",
  details,
}: {
  eligibleCount: number
  count: SessionConfig["count"]
  mode: SessionMode
  onStart: () => void
  disabled: boolean
  startLabel?: string
  details?: ReactNode
}) {
  const currentMode = getModeOption(mode)
  const selectedCount = count === "all" ? eligibleCount : count
  const usedCount = Math.min(selectedCount, eligibleCount)

  return (
    <aside className="min-w-0 xl:sticky xl:top-24 xl:self-start">
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-2">
            Resumen <Badge variant="secondary">{currentMode.label}</Badge>
          </CardTitle>
          <CardDescription>{currentMode.description}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5">
          <div className="rounded-xl bg-muted/40 p-4">
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase">
                  Disponibles
                </p>
                <p className="mt-1 text-3xl font-semibold tabular-nums">
                  {eligibleCount}
                </p>
              </div>
              <p className="text-right text-xs text-muted-foreground">
                Se usarán
                <br />
                <span className="font-semibold text-foreground tabular-nums">
                  {usedCount}
                </span>
              </p>
            </div>
            <Progress
              className="mt-4"
              value={
                eligibleCount
                  ? Math.min(100, (selectedCount / eligibleCount) * 100)
                  : 0
              }
            />
            <p className="mt-3 text-xs text-muted-foreground">
              {eligibleCount} preguntas disponibles con los filtros actuales.
            </p>
            {details}
          </div>
          <Button
            className="min-h-11 w-full"
            disabled={disabled}
            onClick={onStart}
          >
            {startLabel} <ArrowRight data-icon="inline-end" />
          </Button>
          <p className="text-center text-xs leading-5 text-muted-foreground">
            El progreso se guarda localmente al terminar la ronda.
          </p>
        </CardContent>
      </Card>
    </aside>
  )
}
