import type { QuestionExposure } from "@/domain/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function summarizeFactCoverage(exposures: QuestionExposure[]) {
  const facts = new Map<
    string,
    { correct: number; incorrect: number; responseMs: number; exposures: number }
  >()
  for (const exposure of exposures) {
    const current = facts.get(exposure.factId) ?? {
      correct: 0,
      incorrect: 0,
      responseMs: 0,
      exposures: 0,
    }
    current.correct += exposure.correct
    current.incorrect += exposure.incorrect
    current.responseMs += exposure.totalResponseTimeMs
    current.exposures += exposure.exposures
    facts.set(exposure.factId, current)
  }
  const values = [...facts.values()]
  return {
    seen: facts.size,
    weak: values.filter((fact) => fact.incorrect >= fact.correct && fact.incorrect > 0).length,
    slow: values.filter(
      (fact) => fact.exposures > 0 && fact.responseMs / fact.exposures >= 8000
    ).length,
  }
}

export function FactCoveragePanel({
  totalFacts,
  exposures,
}: {
  totalFacts: number
  exposures: QuestionExposure[]
}) {
  const summary = summarizeFactCoverage(exposures)
  const ratio = totalFacts ? Math.round((summary.seen / totalFacts) * 100) : 0
  return (
    <Card className="border-primary/20 bg-primary/[0.03] shadow-none">
      <CardHeader>
        <CardTitle>Cobertura V5 por hechos</CardTitle>
        <CardDescription>
          Agrupa todas las redacciones del mismo contenido; repetir una variante no infla la cobertura.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-3">
        <div>
          <p className="text-2xl font-semibold tabular-nums">
            {summary.seen.toLocaleString("en-US")} / {totalFacts.toLocaleString("en-US")} hechos
          </p>
          <p className="text-sm text-muted-foreground">{ratio}% de cobertura real</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums">{summary.weak} débil</p>
          <p className="text-sm text-muted-foreground">Más fallos que aciertos</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tabular-nums">{summary.slow} lento</p>
          <p className="text-sm text-muted-foreground">Promedio de 8 s o más</p>
        </div>
      </CardContent>
    </Card>
  )
}
