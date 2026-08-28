import { ChevronDown, ClipboardCheck, Copy, SearchCheck } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { useApp } from "@/app/app-state"
import { EmptyState } from "@/components/layout/empty-state"
import { EditorialAuditPanel } from "@/components/editorial-audit-panel"
import { PageHeader } from "@/components/layout/page-header"
import { SectionHeader } from "@/components/layout/section-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { Question, QuestionProgress, QuestionReport } from "@/domain/types"
import { formatDate } from "@/lib/format"

type ReviewItem = {
  questionKey: string
  question: Question
  progress?: QuestionProgress
  reports: QuestionReport[]
}

export function ReviewPage({
  onPracticeQueue,
}: {
  onPracticeQueue: (questions: Question[]) => Promise<void>
}) {
  const { reports, progress, questions, setNav } = useApp()
  const [reason, setReason] = useState("all")
  const [chapter, setChapter] = useState("all")
  const [family, setFamily] = useState("all")
  const [copied, setCopied] = useState<string | null>(null)
  const [copyError, setCopyError] = useState<string | null>(null)
  const [practicePending, setPracticePending] = useState(false)
  const [practiceError, setPracticeError] = useState<string | null>(null)
  const copiedTimer = useRef<number | null>(null)
  const mounted = useRef(false)
  const copySequence = useRef(0)
  const practicePendingRef = useRef(false)
  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
      copySequence.current += 1
      if (copiedTimer.current !== null) {
        window.clearTimeout(copiedTimer.current)
        copiedTimer.current = null
      }
    }
  }, [])
  const queue = useMemo(() => {
    const items = new Map<string, ReviewItem>()
    for (const question of questions) {
      const key = questionKey(question)
      items.set(key, {
        questionKey: key,
        question,
        progress: progress.get(key) ?? progress.get(question.id),
        reports: [],
      })
    }
    for (const report of reports) {
      const key = report.questionKey || questionKey(report.question)
      const item = items.get(key) ?? {
        questionKey: key,
        question: report.question,
        progress: progress.get(key) ?? progress.get(report.question.id),
        reports: [],
      }
      item.reports.push(report)
      item.reports.sort((left, right) => right.reportedAt - left.reportedAt)
      items.set(key, item)
    }
    return [...items.values()]
      .filter((item) => {
        const taxonomy = reviewTaxonomy(item)
        return (
          taxonomy.reported ||
          taxonomy.difficult ||
          taxonomy.failed ||
          taxonomy.favorite
        )
      })
      .sort(
        (left, right) =>
          reviewPriority(right) - reviewPriority(left) ||
          (right.reports[0]?.reportedAt ?? 0) -
            (left.reports[0]?.reportedAt ?? 0)
      )
  }, [progress, questions, reports])
  const reasons = useMemo(
    () => [
      ...new Set(
        queue.flatMap((item) => item.reports.map((report) => report.reason))
      ),
    ],
    [queue]
  )
  const chapters = useMemo(
    () => [
      ...new Set(
        queue.map(
          (item) =>
            `${item.question.source.work}:${item.question.source.chapter}`
        )
      ),
    ],
    [queue]
  )
  const families = useMemo(
    () => [...new Set(queue.map((item) => questionFamily(item.question)))],
    [queue]
  )
  const visibleItems = queue.filter(
    (item) =>
      (reason === "all" ||
        item.reports.some((report) => report.reason === reason)) &&
      (chapter === "all" ||
        `${item.question.source.work}:${item.question.source.chapter}` ===
          chapter) &&
      (family === "all" || questionFamily(item.question) === family)
  )
  const copyJson = async (id: string, question: unknown) => {
    await copyText(JSON.stringify(question, null, 2), (token) => {
      setCopied(id)
      copiedTimer.current = window.setTimeout(() => {
        if (!mounted.current || copySequence.current !== token) return
        setCopied(null)
        copiedTimer.current = null
      }, 1800)
    })
  }
  const copyReference = async (reference: string) => {
    await copyText(reference)
  }
  const practiceQueue = async () => {
    if (practicePendingRef.current) return
    practicePendingRef.current = true
    setPracticePending(true)
    setPracticeError(null)
    try {
      await onPracticeQueue(queue.map((item) => item.question))
    } catch {
      if (mounted.current)
        setPracticeError(
          "No se pudo iniciar la cola. Revisa el almacenamiento e inténtalo de nuevo."
        )
    } finally {
      practicePendingRef.current = false
      if (mounted.current) setPracticePending(false)
    }
  }
  const copyText = async (
    value: string,
    onSuccess?: (token: number) => void
  ) => {
    const token = copySequence.current + 1
    copySequence.current = token
    if (copiedTimer.current !== null) {
      window.clearTimeout(copiedTimer.current)
      copiedTimer.current = null
    }
    if (!mounted.current) return
    setCopied(null)
    setCopyError(null)

    let error: string | null = null
    if (!navigator.clipboard?.writeText) {
      error = "No se pudo copiar: el portapapeles no está disponible."
    } else {
      try {
        await navigator.clipboard.writeText(value)
      } catch {
        error = "No se pudo copiar. Intenta de nuevo."
      }
    }

    if (!mounted.current || copySequence.current !== token) return
    if (error) {
      setCopyError(error)
      return
    }
    onSuccess?.(token)
  }

  return (
    <div className="flex min-w-0 flex-col gap-8">
      <PageHeader
        eyebrow="Auditoría del Banco Maestro Único"
        title="Revisión"
        description="Empieza por la cola recomendada; abre el contexto completo sólo cuando lo necesites."
        action={
          queue.length > 0 ? (
            <Button
              className="min-h-11"
              disabled={practicePending}
              onClick={practiceQueue}
            >
              {practicePending ? "Iniciando cola…" : "Practicar esta cola"}
            </Button>
          ) : undefined
        }
      />
      {practiceError ? (
        <p
          role="alert"
          className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {practiceError}
        </p>
      ) : null}
      <EditorialAuditPanel />
      <section aria-label="Cola de revisión">
        <SectionHeader
          title="Cola recomendada"
          description={
            queue.length > 0
              ? `${queue.length} preguntas pendientes de revisar.`
              : "Las preguntas difíciles, falladas, favoritas o reportadas aparecerán aquí."
          }
        />
        {queue.length > 0 ? (
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
        {queue.length === 0 ? (
          <div className="mt-5">
            <EmptyState
              icon={SearchCheck}
              title="No hay preguntas pendientes"
              description="Marca una pregunta como difícil o favorita, falla una respuesta o repórtala para traerla a esta cola."
              action={
                <Button className="min-h-11" onClick={() => setNav("practice")}>
                  Empezar una ronda
                </Button>
              }
            />
          </div>
        ) : visibleItems.length === 0 ? (
          <div className="mt-5">
            <EmptyState
              icon={SearchCheck}
              title="No hay preguntas con estos filtros"
              description="Prueba otro motivo, capítulo o familia para recuperar la cola."
            />
          </div>
        ) : (
          <div
            role="list"
            aria-label="Preguntas pendientes de revisión"
            className="mt-5 divide-y rounded-xl border border-border/70"
          >
            {visibleItems.map((item) => (
              <ReviewRow
                key={item.questionKey}
                item={item}
                copied={copied === item.questionKey}
                onCopyJson={() =>
                  void copyJson(item.questionKey, item.question)
                }
                onCopyReference={() =>
                  void copyReference(item.question.source.reference)
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
  item,
  copied,
  onCopyJson,
  onCopyReference,
}: {
  item: ReviewItem
  copied: boolean
  onCopyJson: () => void
  onCopyReference: () => void
}) {
  const taxonomy = reviewTaxonomy(item)
  const latestReport = item.reports[0]
  const visibleStatus = taxonomy.difficult
    ? "Difícil"
    : taxonomy.failed
      ? "Fallada"
      : taxonomy.favorite
        ? "Favorita"
        : taxonomy.reported
          ? "Reportada"
          : null
  const explanation = [
    item.question.explanation,
    item.question.trapReason,
    item.question.memoryCue,
  ].filter(Boolean)
  const status = [
    taxonomy.difficult ? "Difícil" : null,
    taxonomy.failed ? "Fallada" : null,
    taxonomy.favorite ? "Favorita" : null,
    taxonomy.reported ? "Reportada" : null,
  ].filter(Boolean)
  return (
    <article role="listitem">
      <details className="group">
        <summary
          aria-label={`Abrir detalle de ${item.question.question}`}
          className="grid min-h-11 cursor-pointer list-none gap-3 px-4 py-4 outline-none marker:hidden focus-visible:ring-[3px] focus-visible:ring-ring/50 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center [&::-webkit-details-marker]:hidden"
        >
          <div className="min-w-0">
            <p className="font-medium text-balance">{item.question.question}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {item.question.source.reference} · {questionFamily(item.question)}{" "}
              · {profileLabel(item.question.bankProfileId)}
              {latestReport
                ? ` · reportada ${formatDate(latestReport.reportedAt)}`
                : ""}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {visibleStatus ? (
              <Badge
                variant={
                  visibleStatus === "Reportada" ? "destructive" : "secondary"
                }
              >
                {visibleStatus}
              </Badge>
            ) : null}
            {taxonomy.reported && visibleStatus !== "Reportada" ? (
              <Badge variant="destructive">Reportada</Badge>
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
              {item.reports.length > 0 ? (
                <div>
                  <p className="text-sm font-medium">Motivo reportado</p>
                  {item.reports.map((report) => (
                    <p
                      key={report.id}
                      className="mt-1 text-sm leading-6 text-muted-foreground"
                    >
                      {report.reason} · {formatDate(report.reportedAt)}
                    </p>
                  ))}
                </div>
              ) : null}
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
              {status.length > 1 || !taxonomy.reported ? (
                <p className="mt-4 text-xs text-muted-foreground">
                  Estado:{" "}
                  <strong className="text-foreground">
                    {status.join(" · ")}
                  </strong>
                </p>
              ) : null}
              {latestReport ? (
                <p className="mt-2 text-xs text-muted-foreground">
                  Respuesta registrada:{" "}
                  <strong className="text-foreground">
                    {formatAnswer(latestReport.answer)}
                  </strong>
                  {latestReport.response
                    ? ` · ${latestReport.response.isCorrect ? "correcta" : latestReport.response.reason === "unanswered" ? "sin responder" : latestReport.response.reason === "timeout" ? "vencida" : "incorrecta"}`
                    : ""}
                </p>
              ) : null}
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

function reviewPriority(item: ReviewItem) {
  const taxonomy = reviewTaxonomy(item)
  return (
    (taxonomy.difficult ? 1_000 : 0) +
    (taxonomy.failed ? 100 : 0) +
    (taxonomy.reported ? 10 : 0) +
    (taxonomy.favorite ? 1 : 0)
  )
}

function reviewTaxonomy(item: ReviewItem) {
  return {
    difficult:
      item.question.difficulty >= 4 || Boolean(item.progress?.markedDifficult),
    failed: (item.progress?.timesIncorrect ?? 0) > 0,
    favorite: Boolean(item.progress?.favorite),
    reported: item.reports.length > 0 || Boolean(item.progress?.reported),
  }
}

function questionKey(question: Question) {
  return `${question.bankId ?? "local"}:${question.id}`
}

function questionFamily(question: Question) {
  return question.factKeys?.[0] ?? question.factKey
}

function chapterLabel(value: string) {
  const [work, chapter] = value.split(":")
  return `${work === "Daniel" ? "Daniel" : "PR"} ${chapter}`
}

function profileLabel(profile: Question["bankProfileId"]) {
  return profile === "final-v7" ? "Banco Maestro Único" : "Historial migrado"
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
