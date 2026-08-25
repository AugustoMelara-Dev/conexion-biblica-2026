import { useRef, useState } from "react"
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

  return (
    <div className="flex flex-col gap-7">
      <section className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Datos locales
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            Banco de preguntas
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Importa, valida y audita tus bancos sin modificar los archivos
            originales. Se encontraron {banks.length} bancos y{" "}
            {allQuestions.length} preguntas.
          </p>
        </div>
        <Button variant="outline" onClick={() => void refresh()}>
          <RefreshCw data-icon="inline-start" />
          Actualizar
        </Button>
      </section>

      <Card className="border-dashed shadow-none">
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

      <section className="grid gap-4 sm:grid-cols-3">
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

      <section>
        <div className="mb-4 flex items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Bancos cargados</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Cada banco conserva su fuente, versión y archivo original.
            </p>
          </div>
          <Badge variant="secondary">{banks.length} bancos</Badge>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {banks.map((bank) => {
            const count = allQuestions.filter(
              (question) => question.bankId === bank.bankId
            ).length
            return (
              <Card key={bank.bankId} className="shadow-none">
                <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
                  <div className="flex min-w-0 gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-primary">
                      <FileJson />
                    </div>
                    <div className="min-w-0">
                      <CardTitle className="truncate text-base">
                        {bank.name}
                      </CardTitle>
                      <CardDescription className="mt-1 truncate">
                        {bank.sourceFileName ?? "Banco local"}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge variant="outline">{count} preguntas</Badge>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span>{bank.sourceWork}</span>
                    <span>{bank.sourceVersion}</span>
                    <span>Importado {formatDate(bank.importedAt)}</span>
                  </div>
                  <Separator className="my-4" />
                  <div className="flex flex-wrap gap-2">
                    {bank.bankId === "master-v2" || bank.bankProfileId === "prep-v3" ? (
                      <Badge variant="secondary">
                        Integrado · solo lectura
                      </Badge>
                    ) : (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => selectFiles(bank.bankId)}
                        >
                          Reemplazar
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-destructive hover:text-destructive"
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
                  </div>
                </CardContent>
              </Card>
            )
          })}
          {banks.length === 0 ? (
            <Card className="shadow-none lg:col-span-2">
              <CardContent className="p-8 text-center text-sm text-muted-foreground">
                No hay bancos cargados todavía.
              </CardContent>
            </Card>
          ) : null}
        </div>
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
