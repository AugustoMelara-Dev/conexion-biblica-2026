import { ClipboardCheck, Copy, Flag, SearchCheck } from "lucide-react"
import { useState } from "react"
import { useApp } from "@/app/app-state"
import { formatDate } from "@/lib/format"
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
import { Separator } from "@/components/ui/separator"

export function ReviewPage() {
  const { reports } = useApp()
  const [copied, setCopied] = useState<string | null>(null)
  const copyJson = async (id: string, question: unknown) => {
    await navigator.clipboard?.writeText(JSON.stringify(question, null, 2))
    setCopied(id)
    window.setTimeout(() => setCopied(null), 1800)
  }
  const copyReference = async (reference: string) => {
    await navigator.clipboard?.writeText(reference)
  }
  return (
    <div className="flex flex-col gap-7">
      <section>
        <p className="text-sm font-medium text-muted-foreground">
          Auditoría de bancos generados
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          Revisar preguntas
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Aquí aparecen las preguntas reportadas durante el entrenamiento. Copia
          el JSON original para revisarlo manualmente.
        </p>
      </section>
      {reports.length === 0 ? (
        <Card className="shadow-none">
          <CardContent className="flex flex-col items-center gap-3 p-12 text-center">
            <span className="flex size-12 items-center justify-center rounded-2xl bg-secondary text-primary">
              <SearchCheck />
            </span>
            <p className="font-medium">No hay preguntas reportadas</p>
            <p className="max-w-md text-sm leading-5 text-muted-foreground">
              Si una pregunta parece ambigua o incorrecta, usa Reportar durante
              una ronda.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {reports.map((report) => (
            <Card key={report.id} className="shadow-none">
              <CardHeader className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                <div className="flex items-start gap-3">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
                    <Flag />
                  </div>
                  <div>
                    <CardTitle className="text-base">
                      {report.question.question}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {report.question.source.reference} · reportada{" "}
                      {formatDate(report.reportedAt)}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Badge variant="outline">{report.question.bankProfileId === "prep-v3" ? "V3" : report.question.bankProfileId === "master-v2" ? "V2" : "V1"}</Badge>
                  <Badge variant="destructive">Pendiente</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertTitle>Motivo</AlertTitle>
                  <AlertDescription>{report.reason}</AlertDescription>
                </Alert>
                <Separator className="my-4" />
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground">
                    Respuesta registrada:{" "}
                    <strong className="text-foreground">
                      {formatAnswer(report.answer)}
                    </strong>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => void copyJson(report.id, report.question)}
                    >
                      <Copy data-icon="inline-start" />
                      {copied === report.id ? "Copiado" : "Copiar JSON"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        void copyReference(report.question.source.reference)
                      }
                    >
                      <Copy data-icon="inline-start" />
                      Copiar referencia
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <ClipboardCheck className="size-4" /> Los reportes se exportan dentro
        del respaldo completo.
      </div>
    </div>
  )
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
