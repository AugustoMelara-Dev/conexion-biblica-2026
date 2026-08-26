import { ChevronDown, ClipboardCheck, Copy, SearchCheck } from "lucide-react"
import { useMemo, useState } from "react"
import { useApp } from "@/app/app-state"
import { EmptyState } from "@/components/layout/empty-state"
import { PageHeader } from "@/components/layout/page-header"
import { SectionHeader } from "@/components/layout/section-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { QuestionProgress, QuestionReport } from "@/domain/types"
import { formatDate } from "@/lib/format"

export function ReviewPage() {
  const { reports, progress, setNav } = useApp()
  const [reason, setReason] = useState("all")
  const [chapter, setChapter] = useState("all")
  const [family, setFamily] = useState("all")
  const [copied, setCopied] = useState<string | null>(null)
  const [copyError, setCopyError] = useState<string | null>(null)
  const reasons = useMemo(
    () => [...new Set(reports.map((report) => report.reason))],
    [reports]
  )
  const chapters = useMemo(
    () => [
      ...new Set(
        reports.map(
          (report) =>
            `${report.question.source.work}:${report.question.source.chapter}`
        )
      ),
    ],
    [reports]
  )
  const families = useMemo(
    () => [...new Set(reports.map(reportFamily))],
    [reports]
  )
  const visibleReports = reports
    .filter(
      (report) =>
        (reason === "all" || report.reason === reason) &&
        (chapter === "all" ||
          `${report.question.source.work}:${report.question.source.chapter}` ===
            chapter) &&
        (family === "all" || reportFamily(report) === family)
    )
    .sort(
      (left, right) =>
        reportPriority(right, progress) - reportPriority(left, progress) ||
        right.reportedAt - left.reportedAt
    )
  const copyJson = async (id: string, question: unknown) => {
    if (
      await copyToClipboard(JSON.stringify(question, null, 2), setCopyError)
    ) {
      setCopied(id)
      window.setTimeout(() => setCopied(null), 1800)
    }
  }
  const copyReference = async (reference: string) => {
    await copyToClipboard(reference, setCopyError)
  }

  return (
    <div className="flex min-w-0 flex-col gap-8">
      <PageHeader
        eyebrow="Auditoría de bancos generados"
        title="Revisión"
        description="Empieza por la cola recomendada; abre el contexto completo sólo cuando lo necesites."
        action={
          reports.length > 0 ? (
            <Button className="min-h-11" onClick={() => setNav("practice")}>
              Empezar una ronda
            </Button>
          ) : undefined
        }
      />
      <section aria-label="Cola de revisión">
        <SectionHeader
          title="Cola recomendada"
          description={
            reports.length > 0
              ? `${reports.length} reportes pendientes de revisar.`
              : "Los reportes de tus rondas aparecerán aquí."
          }
        />
        {reports.length > 0 ? (
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <ReviewFilter
              id="review-reason"
              label="Motivo"
              value={reason}
              onChange={setReason}
            >
              <option value="all">Todos los motivos</option>
              {reasons.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </ReviewFilter>
            <ReviewFilter
              id="review-chapter"
              label="Capítulo"
              value={chapter}
              onChange={setChapter}
            >
              <option value="all">Todos los capítulos</option>
              {chapters.map((item) => (
                <option key={item} value={item}>
                  {chapterLabel(item)}
                </option>
              ))}
            </ReviewFilter>
            <ReviewFilter
              id="review-family"
              label="Familia"
              value={family}
              onChange={setFamily}
            >
              <option value="all">Todas las familias</option>
              {families.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </ReviewFilter>
          </div>
        ) : null}
        {reports.length === 0 ? (
          <div className="mt-5">
            <EmptyState
              icon={SearchCheck}
              title="No hay preguntas pendientes"
              description="Durante una ronda puedes reportar una pregunta ambigua o incorrecta para traerla a esta cola."
              action={
                <Button className="min-h-11" onClick={() => setNav("practice")}>
                  Empezar una ronda
                </Button>
              }
            />
          </div>
        ) : visibleReports.length === 0 ? (
          <div className="mt-5">
            <EmptyState
              icon={SearchCheck}
              title="No hay reportes con estos filtros"
              description="Prueba otro motivo, capítulo o familia para recuperar la cola."
            />
          </div>
        ) : (
          <div
            role="list"
            aria-label="Preguntas pendientes de revisión"
            className="mt-5 divide-y rounded-xl border border-border/70"
          >
            {visibleReports.map((report) => (
              <ReviewRow
                key={report.id}
                report={report}
                progress={
                  progress.get(report.questionKey) ??
                  progress.get(
                    `${report.question.bankId ?? "local"}:${report.question.id}`
                  )
                }
                copied={copied === report.id}
                onCopyJson={() => void copyJson(report.id, report.question)}
                onCopyReference={() =>
                  void copyReference(report.question.source.reference)
                }
              />
            ))}
          </div>
        )}
      </section>
      {copyError ? (
        <p
          role="status"
          aria-live="polite"
          className="text-sm text-destructive"
        >
          {copyError}
        </p>
      ) : null}
      <p className="flex items-center gap-2 text-xs text-muted-foreground">
        <ClipboardCheck className="size-4" aria-hidden="true" />
        Los reportes se exportan dentro del respaldo completo.
      </p>
    </div>
  )
}

function ReviewFilter({
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
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-11 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
      >
        {children}
      </select>
    </div>
  )
}

function ReviewRow({
  report,
  progress,
  copied,
  onCopyJson,
  onCopyReference,
}: {
  report: QuestionReport
  progress?: QuestionProgress
  copied: boolean
  onCopyJson: () => void
  onCopyReference: () => void
}) {
  const taxonomy = reportTaxonomy(report, progress)
  const visibleStatus = taxonomy.difficult
    ? "Difícil"
    : taxonomy.failed
      ? "Fallada"
      : taxonomy.favorite
        ? "Favorita"
        : null
  const explanation = [
    report.question.explanation,
    report.question.trapReason,
    report.question.memoryCue,
  ].filter(Boolean)
  return (
    <article role="listitem">
      <details className="group">
        <summary
          aria-label={`Abrir detalle de ${report.question.question}`}
          className="grid min-h-11 cursor-pointer list-none gap-3 px-4 py-4 outline-none marker:hidden focus-visible:ring-[3px] focus-visible:ring-ring/50 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center [&::-webkit-details-marker]:hidden"
        >
          <div className="min-w-0">
            <p className="font-medium text-balance">
              {report.question.question}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {report.question.source.reference} · {reportFamily(report)} ·{" "}
              {profileLabel(report.question.bankProfileId)} · reportada{" "}
              {formatDate(report.reportedAt)}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="destructive">Reportada</Badge>
            {visibleStatus ? (
              <Badge variant="secondary">{visibleStatus}</Badge>
            ) : null}
          </div>
          <ChevronDown
            aria-hidden="true"
            className="size-4 text-muted-foreground transition-transform group-open:rotate-180 motion-reduce:transition-none"
          />
        </summary>
        <div className="border-t bg-muted/20 px-4 py-5">
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
            <div className="min-w-0">
              <p className="text-sm font-medium">Motivo reportado</p>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                {report.reason}
              </p>
              {explanation.length > 0 ? (
                <div className="mt-4 rounded-lg border bg-background p-4">
                  <p className="text-sm font-medium">Explicación completa</p>
                  {explanation.map((item, index) => (
                    <p
                      key={index}
                      className="mt-2 text-sm leading-6 text-muted-foreground"
                    >
                      {item}
                    </p>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-muted-foreground">
                  Esta pregunta no incluye explicación adicional.
                </p>
              )}
              <p className="mt-4 text-xs text-muted-foreground">
                Estado:{" "}
                <strong className="text-foreground">
                  {taxonomy.difficult ? "Difícil" : "Sin dificultad marcada"}
                  {taxonomy.failed ? " · Fallada" : ""}
                  {taxonomy.favorite ? " · Favorita" : ""} · Reportada
                </strong>
              </p>
              <p className="mt-2 text-xs text-muted-foreground">
                Respuesta registrada:{" "}
                <strong className="text-foreground">
                  {formatAnswer(report.answer)}
                </strong>
                {report.response
                  ? ` · ${report.response.isCorrect ? "correcta" : report.response.reason === "unanswered" ? "sin responder" : report.response.reason === "timeout" ? "vencida" : "incorrecta"}`
                  : ""}
              </p>
            </div>
            <div className="flex flex-wrap gap-2 lg:justify-end">
              <Button
                size="sm"
                variant="outline"
                className="min-h-11"
                onClick={onCopyJson}
              >
                <Copy data-icon="inline-start" />
                {copied ? "Copiado" : "Copiar JSON"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="min-h-11"
                onClick={onCopyReference}
              >
                <Copy data-icon="inline-start" />
                Copiar referencia
              </Button>
            </div>
          </div>
        </div>
      </details>
    </article>
  )
}

function reportPriority(
  report: QuestionReport,
  progress: ReadonlyMap<string, QuestionProgress>
) {
  const questionProgress =
    progress.get(report.questionKey) ??
    progress.get(`${report.question.bankId ?? "local"}:${report.question.id}`)
  const taxonomy = reportTaxonomy(report, questionProgress)
  return (
    (taxonomy.difficult ? 1_000 : 0) +
    (taxonomy.failed ? 100 : 0) +
    (taxonomy.reported ? 10 : 0) +
    (taxonomy.favorite ? 1 : 0)
  )
}

function reportTaxonomy(report: QuestionReport, progress?: QuestionProgress) {
  return {
    difficult:
      report.question.difficulty >= 4 || Boolean(progress?.markedDifficult),
    failed: (progress?.timesIncorrect ?? 0) > 0,
    favorite: Boolean(progress?.favorite),
    reported: true,
  }
}

async function copyToClipboard(
  value: string,
  setError: (message: string | null) => void
) {
  setError(null)
  if (!navigator.clipboard?.writeText) {
    setError("No se pudo copiar: el portapapeles no está disponible.")
    return false
  }
  try {
    await navigator.clipboard.writeText(value)
    return true
  } catch {
    setError("No se pudo copiar. Intenta de nuevo.")
    return false
  }
}

function reportFamily(report: QuestionReport) {
  return report.question.factKeys?.[0] ?? report.question.factKey
}

function chapterLabel(value: string) {
  const [work, chapter] = value.split(":")
  return `${work === "Daniel" ? "Daniel" : "PR"} ${chapter}`
}

function profileLabel(profile: QuestionReport["question"]["bankProfileId"]) {
  return profile === "curated-v4"
    ? "V4"
    : profile === "prep-v3"
      ? "V3"
      : profile === "master-v2"
        ? "V2"
        : "V1"
}

function formatAnswer(answer: unknown) {
  if (answer === undefined || answer === null) return "Sin respuesta"
  if (Array.isArray(answer)) return answer.join(", ")
  if (typeof answer === "object")
    return Object.entries(answer as Record<string, string>)
      .map(([left, right]) => `${left}→${right}`)
      .join(" · ")
  return String(answer)
}
