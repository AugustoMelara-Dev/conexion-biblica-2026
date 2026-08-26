import {
  CalendarClock,
  Clock3,
  ListChecks,
  Percent,
  Trophy,
} from "lucide-react"
import { useMemo, useState } from "react"
import { useApp } from "@/app/app-state"
import { EmptyState } from "@/components/layout/empty-state"
import { PageHeader } from "@/components/layout/page-header"
import { SectionHeader } from "@/components/layout/section-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { buildSessionMetrics } from "@/domain/session-metrics"
import type { BankSelection, Session, SessionMode } from "@/domain/types"
import { formatDate, formatElapsedMs, modeLabel } from "@/lib/format"

export function HistoryPage() {
  const { sessions, questions, setNav } = useApp()
  const [mode, setMode] = useState<SessionMode | "all">("all")
  const [bank, setBank] = useState<BankSelection | "all">("all")
  const modes = useMemo(
    () => [...new Set(sessions.map((session) => session.mode))],
    [sessions]
  )
  const banks = useMemo(
    () => [
      ...new Set(
        sessions.map((session) => session.config.bankSelection ?? "legacy-v1")
      ),
    ],
    [sessions]
  )
  const questionMap = useMemo(
    () =>
      new Map(
        questions.map((question) => [
          `${question.bankId ?? "local"}:${question.id}`,
          question,
        ])
      ),
    [questions]
  )
  const visibleSessions = sessions.filter(
    (session) =>
      (mode === "all" || session.mode === mode) &&
      (bank === "all" || (session.config.bankSelection ?? "legacy-v1") === bank)
  )

  return (
    <div className="flex min-w-0 flex-col gap-8">
      <PageHeader
        eyebrow="Rondas guardadas localmente"
        title="Historial"
        description="Revisa tus sesiones, filtra lo que buscas y abre el detalle sin perder el contexto de la lista."
      />
      <section aria-label="Historial de sesiones">
        <SectionHeader
          title="Sesiones realizadas"
          description={`${sessions.length} rondas guardadas.`}
        />
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:max-w-xl">
          <FilterSelect
            id="history-mode"
            label="Modo"
            value={mode}
            onChange={(value) => setMode(value as SessionMode | "all")}
          >
            <option value="all">Todos los modos</option>
            {modes.map((item) => (
              <option key={item} value={item}>
                {modeLabel(item)}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect
            id="history-bank"
            label="Banco"
            value={bank}
            onChange={(value) => setBank(value as BankSelection | "all")}
          >
            <option value="all">Todos los bancos</option>
            {banks.map((item) => (
              <option key={item} value={item}>
                {bankLabel(item)}
              </option>
            ))}
          </FilterSelect>
        </div>
        {visibleSessions.length > 0 ? (
          <div
            role="list"
            aria-label="Sesiones guardadas"
            className="mt-5 divide-y rounded-xl border border-border/70"
          >
            {visibleSessions.map((session) => (
              <SessionRow
                key={session.id}
                session={session}
                questionMap={questionMap}
              />
            ))}
          </div>
        ) : (
          <div className="mt-5">
            <EmptyState
              icon={CalendarClock}
              title={
                sessions.length === 0
                  ? "Aún no hay sesiones"
                  : "No hay sesiones con estos filtros"
              }
              description={
                sessions.length === 0
                  ? "Completa una primera ronda para ver su resumen y sus respuestas aquí."
                  : "Cambia el modo o banco para recuperar sesiones guardadas."
              }
              action={
                sessions.length === 0 ? (
                  <Button
                    className="min-h-11"
                    onClick={() => setNav("practice")}
                  >
                    Empezar una ronda
                  </Button>
                ) : undefined
              }
            />
          </div>
        )}
      </section>
      <p className="flex items-center gap-2 text-xs text-muted-foreground">
        <CalendarClock className="size-4" aria-hidden="true" />
        El historial se guarda en IndexedDB y forma parte del respaldo.
      </p>
    </div>
  )
}

function FilterSelect({
  id,
  label,
  value,
  onChange,
  children,
}: {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  children: React.ReactNode
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium">
        {label}
      </label>
      <select
        id={id}
        className="h-11 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {children}
      </select>
    </div>
  )
}

function SessionRow({
  session,
  questionMap,
}: {
  session: Session
  questionMap: Map<string, { question: string; source: { reference: string } }>
}) {
  const metrics = buildSessionMetrics(session)
  const bank = session.config.bankSelection ?? "legacy-v1"
  return (
    <article role="listitem">
      <details>
        <summary className="grid min-h-11 cursor-pointer list-none gap-x-4 gap-y-2 px-4 py-4 outline-none marker:hidden focus-visible:ring-[3px] focus-visible:ring-ring/50 sm:grid-cols-[minmax(0,1fr)_auto_auto_auto_auto] sm:items-center [&::-webkit-details-marker]:hidden">
          <div className="min-w-0">
            <p className="font-medium">{modeLabel(session.mode)}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {formatDate(session.startedAt)}
            </p>
          </div>
          <SessionFact
            label="Precisión"
            value={`${metrics.accuracy}%`}
            icon={Percent}
          />
          <SessionFact
            label="Duración"
            value={formatElapsedMs(session.durationMs)}
            icon={Clock3}
          />
          <span className="text-sm text-muted-foreground">
            {bankLabel(bank)}
          </span>
          <Badge variant={metrics.accuracy >= 80 ? "default" : "secondary"}>
            {session.answers.length} preguntas
          </Badge>
        </summary>
        <div className="border-t bg-muted/20 px-4 py-5">
          <div className="grid gap-3 sm:grid-cols-3">
            <MiniMetric
              icon={Trophy}
              label="Puntuación"
              value={metrics.scoreLabel}
            />
            <MiniMetric
              icon={Percent}
              label="Precisión"
              value={`${metrics.accuracy}%`}
            />
            <MiniMetric
              icon={Clock3}
              label="Duración"
              value={formatElapsedMs(session.durationMs)}
            />
          </div>
          <div
            className="mt-5 divide-y rounded-lg border bg-background"
            aria-label={`Respuestas de ${modeLabel(session.mode)}`}
          >
            {session.answers.map((answer, index) => (
              <div
                key={`${answer.questionKey}-${index}`}
                className="flex items-start gap-3 px-3 py-3"
              >
                <ListChecks
                  aria-hidden="true"
                  className={`mt-0.5 size-4 shrink-0 ${answer.result.isCorrect ? "text-chart-2" : "text-destructive"}`}
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium">
                    {questionMap.get(answer.questionKey)?.question ??
                      answer.questionKey}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {questionMap.get(answer.questionKey)?.source.reference ??
                      "Sin referencia"}{" "}
                    ·{" "}
                    {answer.result.isCorrect
                      ? "Correcta"
                      : answer.result.reason === "timeout"
                        ? "Vencida"
                        : answer.result.reason === "unanswered"
                          ? "Sin responder"
                          : "Incorrecta"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </details>
    </article>
  )
}

function SessionFact({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string
  icon: typeof Clock3
}) {
  return (
    <span className="flex items-center gap-1.5 text-sm tabular-nums">
      <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
      <span className="sm:sr-only">{label}: </span>
      {value}
    </span>
  )
}

function MiniMetric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Trophy
  label: string
  value: string
}) {
  return (
    <div className="rounded-xl border bg-background p-3">
      <Icon className="size-4 text-primary" aria-hidden="true" />
      <p className="mt-3 text-xs tracking-[0.1em] text-muted-foreground uppercase">
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold tabular-nums">{value}</p>
    </div>
  )
}

function bankLabel(bank: BankSelection) {
  const labels: Record<BankSelection, string> = {
    "legacy-v1": "Banco V1",
    "master-v2": "Banco V2",
    "prep-v3": "Banco V3",
    "curated-v4": "Banco V4",
    mixed: "Bancos mezclados",
  }
  return labels[bank]
}
