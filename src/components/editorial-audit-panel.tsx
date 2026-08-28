import { Download, ShieldCheck, Upload } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  buildHumanReviewDecision,
  reconcileHumanReview,
  selectNextHumanReview,
  type HumanReviewDecision,
  type HumanReviewDisposition,
  type HumanReviewEntry,
} from "@/domain/editorial-review"
import { downloadJson } from "@/lib/format"

type IndexedReviewEntry = HumanReviewEntry & { questions_file: string }
type ReviewIndex = {
  bank_questions: number
  entries: IndexedReviewEntry[]
}
type ReviewQuestion = {
  id: string
  question: string
  options: string[]
  correct_answer: string
  source_quote: string
  why_distractors_fail: Record<string, string>
}

const DECISIONS_KEY = "conexion-biblica-human-review-v1"
const REVIEWER_KEY = "conexion-biblica-human-reviewer-v1"

function readDecisions(): HumanReviewDecision[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(DECISIONS_KEY) ?? "[]")
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function EditorialAuditPanel() {
  const [index, setIndex] = useState<ReviewIndex | null>(null)
  const [decisions, setDecisions] = useState<HumanReviewDecision[]>(readDecisions)
  const [reviewer, setReviewer] = useState(
    () => localStorage.getItem(REVIEWER_KEY) ?? "",
  )
  const [family, setFamily] = useState("")
  const [chapter, setChapter] = useState("")
  const [notes, setNotes] = useState("")
  const [question, setQuestion] = useState<ReviewQuestion | null>(null)
  const [error, setError] = useState<string | null>(null)
  const shardCache = useRef(new Map<string, Promise<ReviewQuestion[]>>())

  useEffect(() => {
    let active = true
    void fetch("/banks/final-2026/review-index.json")
      .then((response) => {
        if (!response.ok) throw new Error("No se pudo cargar el índice editorial.")
        return response.json() as Promise<ReviewIndex>
      })
      .then((payload) => {
        if (active) setIndex(payload)
      })
      .catch((loadError: unknown) => {
        if (active)
          setError(
            loadError instanceof Error
              ? loadError.message
              : "No se pudo cargar la auditoría editorial.",
          )
      })
    return () => {
      active = false
    }
  }, [])

  const reconciliation = useMemo(
    () => reconcileHumanReview(index?.entries ?? [], decisions),
    [decisions, index?.entries],
  )
  const current = useMemo(
    () =>
      selectNextHumanReview(index?.entries ?? [], decisions, {
        family: family || undefined,
        chapter: chapter || undefined,
      }) as IndexedReviewEntry | undefined,
    [chapter, decisions, family, index?.entries],
  )
  const families = useMemo(
    () => [...new Set((index?.entries ?? []).map((entry) => entry.family))].sort(),
    [index?.entries],
  )
  const chapters = useMemo(
    () => [...new Set((index?.entries ?? []).map((entry) => entry.chapter))].sort(),
    [index?.entries],
  )

  useEffect(() => {
    if (!current) {
      setQuestion(null)
      return
    }
    let active = true
    let shard = shardCache.current.get(current.questions_file)
    if (!shard) {
      shard = fetch(`/${current.questions_file}`).then((response) => {
        if (!response.ok) throw new Error("No se pudo cargar el capítulo.")
        return response.json() as Promise<ReviewQuestion[]>
      })
      shardCache.current.set(current.questions_file, shard)
    }
    setQuestion(null)
    void shard
      .then((rows) => {
        const match = rows.find((row) => row.id === current.id)
        if (!match) throw new Error(`No se encontró ${current.id}.`)
        if (active) setQuestion(match)
      })
      .catch((loadError: unknown) => {
        if (active)
          setError(
            loadError instanceof Error
              ? loadError.message
              : "No se pudo cargar la pregunta.",
          )
      })
    return () => {
      active = false
    }
  }, [current])

  const decide = (disposition: HumanReviewDisposition) => {
    if (!current) return
    if (disposition === "rejected" && !notes.trim()) {
      setError("Explica el motivo antes de rechazar la pregunta.")
      return
    }
    try {
      const next = buildHumanReviewDecision(current, {
        reviewer,
        disposition,
        notes,
      })
      const updated = [
        ...decisions.filter((decision) => decision.id !== current.id),
        next,
      ]
      setDecisions(updated)
      localStorage.setItem(DECISIONS_KEY, JSON.stringify(updated))
      localStorage.setItem(REVIEWER_KEY, next.reviewer)
      setReviewer(next.reviewer)
      setNotes("")
      setError(null)
    } catch (decisionError) {
      setError(
        decisionError instanceof Error
          ? decisionError.message
          : "No se pudo guardar la decisión.",
      )
    }
  }

  const importDecisions = async (file: File) => {
    try {
      const text = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(String(reader.result ?? ""))
        reader.onerror = () => reject(reader.error)
        reader.readAsText(file)
      })
      const parsed = JSON.parse(text) as unknown
      if (
        !Array.isArray(parsed) ||
        parsed.some(
          (item) =>
            !item ||
            typeof item !== "object" ||
            typeof item.id !== "string" ||
            typeof item.content_sha256 !== "string" ||
            typeof item.reviewer !== "string" ||
            typeof item.reviewed_at !== "string" ||
            !["approved", "corrected", "rejected"].includes(item.disposition),
        )
      )
        throw new Error("El archivo no contiene decisiones editoriales válidas.")
      const merged = new Map(decisions.map((item) => [item.id, item]))
      for (const item of parsed as HumanReviewDecision[]) merged.set(item.id, item)
      const updated = [...merged.values()]
      setDecisions(updated)
      localStorage.setItem(DECISIONS_KEY, JSON.stringify(updated))
      setError(null)
    } catch (importError) {
      setError(
        importError instanceof Error
          ? importError.message
          : "No se pudieron importar las decisiones.",
      )
    }
  }

  return (
    <section aria-labelledby="human-audit-title" className="space-y-5">
      <Card className="border-primary/20 shadow-none">
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2
                id="human-audit-title"
                className="flex items-center gap-2 text-2xl font-semibold leading-none tracking-tight"
              >
                <ShieldCheck className="size-5" aria-hidden="true" />
                Auditoría humana final
              </h2>
              <CardDescription className="mt-2 max-w-3xl">
                Contrasta el enunciado, la respuesta, cada distractor y el texto
                fuente. La aprobación queda ligada a la huella exacta de la
                pregunta.
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline">
                <label>
                  <Upload data-icon="inline-start" />
                  Importar decisiones
                  <input
                    className="sr-only"
                    type="file"
                    accept="application/json,.json"
                    aria-label="Importar decisiones"
                    onChange={async (event) => {
                      const input = event.currentTarget
                      const file = input.files?.[0]
                      if (file) await importDecisions(file)
                      input.value = ""
                    }}
                  />
                </label>
              </Button>
              <Button
                variant="outline"
                disabled={decisions.length === 0}
                onClick={() =>
                  downloadJson("final-human-review-decisions.json", decisions)
                }
              >
                <Download data-icon="inline-start" />
                Exportar decisiones
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">
              {reconciliation.reviewed.length} de {index?.bank_questions ?? "…"} revisadas
            </Badge>
            <Badge variant="outline">
              {reconciliation.pending.length} pendientes
            </Badge>
          </div>
          {reconciliation.stale.length > 0 ? (
            <Alert variant="destructive">
              <AlertTitle>Decisiones obsoletas</AlertTitle>
              <AlertDescription>
                {reconciliation.stale.length} decisión corresponde a contenido
                anterior y debe revisarse otra vez.
              </AlertDescription>
            </Alert>
          ) : null}
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>No se guardó la decisión</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <div className="grid gap-4 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-medium">
              Nombre del revisor
              <Input
                value={reviewer}
                onChange={(event) => setReviewer(event.target.value)}
                autoComplete="name"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              Familia
              <select
                className="h-10 rounded-md border border-input bg-background px-3"
                value={family}
                onChange={(event) => setFamily(event.target.value)}
              >
                <option value="">Todas</option>
                {families.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 text-sm font-medium">
              Capítulo
              <select
                className="h-10 rounded-md border border-input bg-background px-3"
                value={chapter}
                onChange={(event) => setChapter(event.target.value)}
              >
                <option value="">Todos</option>
                {chapters.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
          </div>
        </CardContent>
      </Card>

      {current && question ? (
        <Card className="shadow-none">
          <CardHeader>
            <div className="flex flex-wrap gap-2">
              <Badge>{current.family}</Badge>
              <Badge variant="outline">{current.chapter}</Badge>
              <Badge variant="outline">Riesgo {current.risk_score}</Badge>
            </div>
            <CardTitle className="text-xl leading-relaxed">
              {question.question}
            </CardTitle>
            <CardDescription>
              {current.reference} · {current.id}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="rounded-xl border bg-muted/30 p-4">
              <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                Texto fuente
              </p>
              <p className="mt-2 text-sm leading-6">{question.source_quote}</p>
            </div>
            <ol className="grid gap-2" aria-label="Opciones auditadas">
              {question.options.map((option) => (
                <li
                  key={option}
                  className={`rounded-lg border px-4 py-3 text-sm ${option === question.correct_answer ? "border-emerald-500/40 bg-emerald-500/5" : ""}`}
                >
                  <span className="font-medium">{option}</span>
                  {option === question.correct_answer ? (
                    <Badge className="ml-2">Respuesta</Badge>
                  ) : (
                    <p className="mt-1 text-muted-foreground">
                      {question.why_distractors_fail?.[option] ??
                        "Sin explicación registrada."}
                    </p>
                  )}
                </li>
              ))}
            </ol>
            <label className="grid gap-2 text-sm font-medium">
              Nota editorial
              <textarea
                className="min-h-24 rounded-md border border-input bg-background p-3 font-normal"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Obligatoria al rechazar; opcional al aprobar."
              />
            </label>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => decide("approved")}>Aprobar pregunta</Button>
              <Button variant="destructive" onClick={() => decide("rejected")}>Rechazar pregunta</Button>
            </div>
          </CardContent>
        </Card>
      ) : index && !current ? (
        <Alert>
          <AlertTitle>Cola completada</AlertTitle>
          <AlertDescription>
            No quedan preguntas pendientes con estos filtros.
          </AlertDescription>
        </Alert>
      ) : !error ? (
        <p role="status" className="text-sm text-muted-foreground">
          Cargando cola editorial…
        </p>
      ) : null}
    </section>
  )
}
