import { useMemo, useRef, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileJson,
  RefreshCw,
  ShieldCheck,
  Trash2,
  UploadCloud,
} from "lucide-react"
import { useApp, type ImportOutcome } from "@/app/app-state"
import { downloadJson, formatDate } from "@/lib/format"
import { EmptyState } from "@/components/layout/empty-state"
import { PageHeader } from "@/components/layout/page-header"
import { SectionHeader } from "@/components/layout/section-header"
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
import type { SourceWork } from "@/domain/types"

type CurationSummary = {
  approved: number
  repaired: number
  rejected: number
}

type CurationMetadata = {
  generatedAt: string | null
  masterFingerprint: string | null
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function getCurationSummary(
  raw: Record<string, unknown> | undefined
): CurationSummary | null {
  if (!raw || !isRecord(raw.bank) || !isRecord(raw.bank.curationSummary))
    return null
  const summary = raw.bank.curationSummary
  const { approved, repaired, rejected } = summary
  if (
    typeof approved !== "number" ||
    typeof repaired !== "number" ||
    typeof rejected !== "number"
  )
    return null
  return { approved, repaired, rejected }
}

function getCurationMetadata(
  raw: Record<string, unknown> | undefined
): CurationMetadata | null {
  if (!raw || !isRecord(raw.bank)) return null
  const generatedAt =
    typeof raw.bank.generatedAt === "string" &&
    Number.isFinite(Date.parse(raw.bank.generatedAt))
      ? raw.bank.generatedAt
      : null
  const masterFingerprint =
    typeof raw.bank.masterFingerprint === "string" &&
    raw.bank.masterFingerprint.length > 0
      ? raw.bank.masterFingerprint
      : null
  return generatedAt || masterFingerprint
    ? { generatedAt, masterFingerprint }
    : null
}

function normalize(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
}

export function BankManagerPage() {
  const {
    banks,
    allQuestions,
    importBankFiles,
    removeBank,
    exportBanks,
    exportProgress,
    exportBackup,
    importBackup,
    refresh,
  } = useApp()
  const inputRef = useRef<HTMLInputElement>(null)
  const backupInputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [replaceBankId, setReplaceBankId] = useState<string | undefined>()
  const [outcomes, setOutcomes] = useState<ImportOutcome[]>([])
  const [backupMessage, setBackupMessage] = useState<string | null>(null)
  const [query, setQuery] = useState("")
  const [source, setSource] = useState<"all" | SourceWork>("all")

  const selectFiles = (nextReplaceBankId?: string) => {
    setReplaceBankId(nextReplaceBankId)
    inputRef.current?.click()
  }

  const handleFiles = async (files: FileList | File[]) => {
    const jsonFiles = [...files].filter((file) =>
      file.name.toLowerCase().endsWith(".json")
    )
    if (jsonFiles.length === 0) {
      setOutcomes([
        {
          sourceName: "selección",
          valid: false,
          questionCount: 0,
          errors: [
            {
              code: "NO_JSON",
              path: "$",
              message: "Selecciona al menos un archivo .json.",
            },
          ],
        },
      ])
      return
    }
    setOutcomes(await importBankFiles(jsonFiles, replaceBankId))
    setReplaceBankId(undefined)
  }

  const handleBackup = async (file: File) => {
    const result = await importBackup(file)
    setBackupMessage(
      result.valid
        ? "Respaldo restaurado. Se reemplazaron los datos locales después de validar el archivo."
        : result.errors
            .map((error) => `${error.path}: ${error.message}`)
            .join("\n")
    )
  }

  const visibleBanks = banks.filter((bank) => {
    const matchesQuery = normalize(
      `${bank.name} ${bank.sourceFileName ?? ""}`
    ).includes(normalize(query))
    const matchesSource = source === "all" || bank.sourceWork === source
    return matchesQuery && matchesSource
  })
  const questionCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const question of allQuestions) {
      if (!question.bankId) continue
      counts.set(question.bankId, (counts.get(question.bankId) ?? 0) + 1)
    }
    return counts
  }, [allQuestions])

  return (
    <div className="flex min-w-0 flex-col gap-8">
      <PageHeader
        eyebrow="Datos locales"
        title="Banco de preguntas"
        description="Administra fuentes y respaldos sin mezclar el progreso de cada banco."
        action={
          <Button onClick={() => selectFiles()}>
            Importar banco <UploadCloud data-icon="inline-end" />
          </Button>
        }
      />

      <Card className="border-dashed shadow-none">
        <CardHeader className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <CardTitle>Importar archivos JSON</CardTitle>
            <CardDescription>
              Se validan antes de guardarlos y no se modifica el archivo
              original.
            </CardDescription>
          </div>
          <Button variant="outline" onClick={() => void refresh()}>
            <RefreshCw data-icon="inline-start" />
            Actualizar
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <button
            type="button"
            className={`flex w-full flex-col items-center justify-center gap-3 rounded-[inherit] px-6 py-12 text-center transition-colors ${dragging ? "bg-secondary" : "hover:bg-muted/50"}`}
            onClick={() => selectFiles()}
            onDragEnter={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault()
              setDragging(false)
              void handleFiles(event.dataTransfer.files)
            }}
          >
            <span className="flex size-12 items-center justify-center rounded-2xl bg-secondary text-primary">
              <UploadCloud />
            </span>
            <span className="text-base font-semibold">
              Arrastra uno o varios JSON aquí
            </span>
            <span className="max-w-md text-sm leading-5 text-muted-foreground">
              También puedes seleccionarlos. Se validarán los IDs, opciones,
              tipos y respuestas antes de guardarlos.
            </span>
            <span className="text-xs font-medium text-primary">
              Schema aceptado: 1.0
            </span>
          </button>
          <input
            ref={inputRef}
            className="sr-only"
            type="file"
            accept="application/json,.json"
            multiple
            onChange={(event) => {
              if (event.target.files) void handleFiles(event.target.files)
              event.currentTarget.value = ""
            }}
          />
        </CardContent>
      </Card>

      {outcomes.length > 0 ? (
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="text-chart-2" />
              Resultado de la importación
            </CardTitle>
            <CardDescription>
              Los inválidos se rechazaron completos; no se descartó información
              en silencio.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {outcomes.map((outcome) => (
              <div key={outcome.sourceName} className="rounded-xl border p-4">
                <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                  <div className="flex items-start gap-3">
                    <span
                      className={`mt-0.5 ${outcome.valid ? "text-chart-2" : "text-destructive"}`}
                    >
                      {outcome.valid ? <CheckCircle2 /> : <AlertTriangle />}
                    </span>
                    <div>
                      <p className="font-medium">{outcome.sourceName}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {outcome.valid
                          ? `${outcome.questionCount} preguntas cargadas`
                          : `${outcome.errors.length} errores encontrados`}
                      </p>
                    </div>
                  </div>
                  {outcome.valid ? (
                    <Badge>Válido</Badge>
                  ) : (
                    <Badge variant="destructive">Rechazado</Badge>
                  )}
                </div>
                {!outcome.valid ? (
                  <div className="mt-3 flex flex-col gap-2 rounded-lg bg-destructive/5 p-3 text-xs text-destructive">
                    {outcome.errors.map((error, index) => (
                      <p key={`${error.path}-${index}`}>
                        <strong>{error.path}</strong> · {error.code}:{" "}
                        {error.message}
                        {error.questionId ? ` (${error.questionId})` : ""}
                      </p>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ActionCard
          icon={Download}
          title="Exportar bancos"
          detail="Incluye el raw original de cada banco."
          onClick={async () =>
            downloadJson("conexion-biblica-bancos.json", await exportBanks())
          }
        />
        <ActionCard
          icon={Download}
          title="Exportar progreso"
          detail="Solo métricas y evolución de preguntas."
          onClick={async () =>
            downloadJson(
              "conexion-biblica-progreso.json",
              await exportProgress()
            )
          }
        />
        <ActionCard
          icon={ShieldCheck}
          title="Exportar todo"
          detail="Respaldo versionado para restaurar después."
          onClick={async () =>
            downloadJson("conexion-biblica-respaldo.json", await exportBackup())
          }
        />
      </section>

      {backupMessage ? (
        <Alert
          variant={
            backupMessage.startsWith("Respaldo") ? "default" : "destructive"
          }
        >
          <AlertTitle>
            {backupMessage.startsWith("Respaldo")
              ? "Restauración completada"
              : "No se restauró el respaldo"}
          </AlertTitle>
          <AlertDescription className="whitespace-pre-wrap">
            {backupMessage}
          </AlertDescription>
        </Alert>
      ) : null}
      <Card className="shadow-none">
        <CardHeader className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <CardTitle>Importar respaldo</CardTitle>
            <CardDescription>
              Valida el archivo completo antes de reemplazar tus datos locales.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            onClick={() => backupInputRef.current?.click()}
          >
            <UploadCloud data-icon="inline-start" />
            Importar respaldo
          </Button>
          <input
            ref={backupInputRef}
            className="sr-only"
            type="file"
            accept="application/json,.json"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) void handleBackup(file)
              event.currentTarget.value = ""
            }}
          />
        </CardHeader>
      </Card>

      <section className="min-w-0" aria-label="Gestión de bancos">
        <SectionHeader
          title="Bancos cargados"
          description={`Cada banco conserva su fuente, versión y archivo original. ${banks.length} bancos y ${allQuestions.length} preguntas.`}
          action={
            <Badge variant="secondary">{visibleBanks.length} visibles</Badge>
          }
        />
        <div className="mt-5 grid gap-3 sm:grid-cols-[minmax(0,1fr)_14rem]">
          <div>
            <label
              htmlFor="bank-search"
              className="mb-1.5 block text-sm font-medium"
            >
              Buscar bancos
            </label>
            <Input
              id="bank-search"
              type="search"
              className="min-h-11 py-2"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Nombre o archivo"
            />
          </div>
          <div>
            <label
              htmlFor="bank-source"
              className="mb-1.5 block text-sm font-medium"
            >
              Fuente
            </label>
            <select
              id="bank-source"
              className="h-11 min-h-11 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
              value={source}
              onChange={(event) =>
                setSource(event.target.value as "all" | SourceWork)
              }
            >
              <option value="all">Todas las fuentes</option>
              <option value="Daniel">Daniel</option>
              <option value="Profetas y Reyes">Profetas y Reyes</option>
            </select>
          </div>
        </div>

        {visibleBanks.length > 0 ? (
          <div
            role="table"
            aria-label="Bancos disponibles"
            className="mt-5 divide-y rounded-xl border border-border/70"
          >
            <div role="rowgroup" className="sr-only">
              <div role="row">
                <span role="columnheader">Banco</span>
                <span role="columnheader">Fuente</span>
                <span role="columnheader">Preguntas</span>
                <span role="columnheader">Acciones</span>
              </div>
            </div>
            <div role="rowgroup" className="divide-y">
              {visibleBanks.map((bank) => {
                const curationSummary =
                  bank.bankProfileId === "curated-v4"
                    ? getCurationSummary(bank.raw)
                    : null
                const curationMetadata =
                  bank.bankProfileId === "curated-v4"
                    ? getCurationMetadata(bank.raw)
                    : null
                const isTechnicalBank =
                  bank.bankId === "master-v2" ||
                  bank.bankProfileId === "master-v2"
                const readOnly =
                  isTechnicalBank ||
                  bank.bankProfileId === "prep-v3" ||
                  bank.bankProfileId === "curated-v4"
                const count = questionCounts.get(bank.bankId) ?? 0

                return (
                  <div
                    role="row"
                    key={bank.bankId}
                    className="grid min-w-0 gap-2 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_10rem_8rem_auto] sm:items-center"
                  >
                    <div role="cell" className="min-w-0">
                      <p className="truncate font-medium">{bank.name}</p>
                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        {bank.sourceFileName ?? "Banco local"} ·{" "}
                        {bank.sourceVersion} · Importado{" "}
                        {formatDate(bank.importedAt)}
                      </p>
                    </div>
                    <span role="cell" className="text-sm text-muted-foreground">
                      {bank.sourceWork}
                    </span>
                    <span role="cell" className="text-sm tabular-nums">
                      {count} preguntas
                    </span>
                    <div
                      role="cell"
                      className="flex min-w-0 flex-wrap items-center gap-2 sm:justify-end"
                    >
                      {readOnly ? (
                        <Badge variant="secondary">
                          Integrado · solo lectura
                        </Badge>
                      ) : (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            className="min-h-11 px-4"
                            aria-label={`Reemplazar ${bank.name}`}
                            onClick={() => selectFiles(bank.bankId)}
                          >
                            Reemplazar
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="min-h-11 px-4 text-destructive hover:text-destructive"
                            aria-label={`Eliminar ${bank.name}`}
                            onClick={() => {
                              if (
                                window.confirm(
                                  `¿Eliminar ${bank.name}? El progreso se conserva separado.`
                                )
                              )
                                void removeBank(bank.bankId)
                            }}
                          >
                            <Trash2 data-icon="inline-start" />
                            Eliminar
                          </Button>
                        </>
                      )}
                      {isTechnicalBank ? (
                        <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
                          Fuente técnica conservada sin modificaciones
                        </span>
                      ) : null}
                      {curationSummary || curationMetadata ? (
                        <details className="w-full text-xs text-muted-foreground">
                          <summary className="flex min-h-11 w-full cursor-pointer items-center rounded-md px-2 font-medium focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none">
                            Ver resumen de curación de {bank.name}
                          </summary>
                          {curationSummary ? (
                            <div
                              aria-label="Resumen de curación V4"
                              className="mt-2 flex flex-wrap gap-x-3 gap-y-1"
                            >
                              <span>{curationSummary.approved} aprobadas</span>
                              <span>{curationSummary.repaired} reparadas</span>
                              <span>{curationSummary.rejected} rechazadas</span>
                            </div>
                          ) : null}
                          {curationMetadata ? (
                            <div
                              aria-label="Metadatos de generación V4"
                              className="mt-2 flex flex-wrap gap-x-3 gap-y-1"
                            >
                              {curationMetadata.generatedAt ? (
                                <span>
                                  Generado{" "}
                                  {formatDate(
                                    Date.parse(curationMetadata.generatedAt)
                                  )}
                                </span>
                              ) : null}
                              {curationMetadata.masterFingerprint ? (
                                <span
                                  title={curationMetadata.masterFingerprint}
                                >
                                  Maestro SHA-256{" "}
                                  {curationMetadata.masterFingerprint.slice(
                                    0,
                                    12
                                  )}
                                  …
                                </span>
                              ) : null}
                            </div>
                          ) : null}
                        </details>
                      ) : null}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="mt-5">
            <EmptyState
              icon={FileJson}
              title="No hay bancos que coincidan"
              description="Prueba otra búsqueda o fuente, o importa un banco nuevo."
            />
          </div>
        )}
      </section>
    </div>
  )
}

function ActionCard({
  icon: Icon,
  title,
  detail,
  onClick,
}: {
  icon: typeof Download
  title: string
  detail: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      className="rounded-xl border bg-card p-5 text-left transition-colors hover:bg-muted/40"
      onClick={onClick}
    >
      <div className="flex size-9 items-center justify-center rounded-lg bg-secondary text-primary">
        <Icon />
      </div>
      <p className="mt-4 font-medium">{title}</p>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</p>
    </button>
  )
}
