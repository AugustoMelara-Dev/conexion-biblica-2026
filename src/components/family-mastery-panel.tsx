import { useMemo, useState } from "react"
import {
  buildFamilyInsights,
  type FamilyStatus,
} from "@/domain/family-insights"
import type { Question, QuestionProgress } from "@/domain/types"
import { SectionHeader } from "@/components/layout/section-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const labels: Record<FamilyStatus, string> = {
  weak: "Débil",
  pending: "Pendiente",
  learning: "En progreso",
  mastered: "Dominado",
}

export function FamilyMasteryPanel({
  questions,
  progress,
}: {
  questions: Question[]
  progress: ReadonlyMap<string, QuestionProgress>
}) {
  const [filter, setFilter] = useState<FamilyStatus | "all">("all")
  const rows = useMemo(
    () => buildFamilyInsights(questions, progress),
    [progress, questions]
  )
  const visible =
    filter === "all" ? rows : rows.filter((row) => row.status === filter)
  const count = (status: FamilyStatus) =>
    rows.filter((row) => row.status === status).length

  return (
    <section aria-label="Dominio por familia de conocimiento">
      <SectionHeader
        title="Dominio por familia de conocimiento"
        description="Cada fila agrupa las variantes del mismo hecho. Dominar una frase no basta si quedan variantes pendientes."
      />
      <div aria-label="Filtrar familias" className="mt-5 flex flex-wrap gap-2">
        <FilterButton
          active={filter === "all"}
          onClick={() => setFilter("all")}
        >
          Todas ({rows.length})
        </FilterButton>
        {(["weak", "pending", "learning", "mastered"] as FamilyStatus[]).map(
          (status) => (
            <FilterButton
              key={status}
              active={filter === status}
              onClick={() => setFilter(status)}
            >
              {labels[status]} ({count(status)})
            </FilterButton>
          )
        )}
      </div>
      <div
        role="list"
        aria-label="Familias de conocimiento"
        className="mt-4 divide-y rounded-xl border border-border/70"
      >
        {visible.map((row) => (
          <article
            key={row.factKey}
            role="listitem"
            className="grid gap-3 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center"
          >
            <div className="min-w-0">
              <p className="font-medium text-balance">{row.label}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {row.work} · cap. {row.chapter} · {row.factKey}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge
                variant={
                  row.status === "weak"
                    ? "destructive"
                    : row.status === "mastered"
                      ? "default"
                      : "secondary"
                }
              >
                {labels[row.status]}
              </Badge>
              <span className="text-sm text-muted-foreground tabular-nums">
                {row.mastery}/5 dominio
              </span>
            </div>
            <dl className="grid grid-cols-3 gap-3 text-sm tabular-nums sm:min-w-52">
              <div>
                <dt className="text-xs text-muted-foreground">Variantes</dt>
                <dd>
                  {row.seenVariants}/{row.variants}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Pendientes</dt>
                <dd>{row.pendingVariants}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Fallos</dt>
                <dd>{row.incorrect}</dd>
              </div>
            </dl>
          </article>
        ))}
        {visible.length === 0 ? (
          <div
            role="listitem"
            className="px-4 py-10 text-center text-sm text-muted-foreground"
          >
            No hay familias en este estado.
          </div>
        ) : null}
      </div>
    </section>
  )
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <Button
      type="button"
      size="sm"
      className="min-h-11"
      variant={active ? "default" : "outline"}
      aria-pressed={active}
      onClick={onClick}
    >
      {children}
    </Button>
  )
}
