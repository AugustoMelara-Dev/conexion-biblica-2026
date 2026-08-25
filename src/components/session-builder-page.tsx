import { useEffect, useMemo, useState, type ComponentType } from "react"
import {
  ArrowRight,
  BookOpen,
  Brain,
  Check,
  CircleHelp,
  Shuffle,
  TimerReset,
} from "lucide-react"
import { useApp } from "@/app/app-state"
import { filterEligibleQuestions } from "@/domain/session-selector"
import { getSequentialBlockCount } from "@/domain/session-selection"
import { SIMULATION_PRESET } from "@/domain/simulation-calibration"
import { chaptersForStudyDay, getStudyDay, type StudyDay } from "@/domain/study-plan"
import {
  SUPPORTED_QUESTION_TYPES,
  type DifficultyBand,
  type QuestionStatus,
  type QuestionType,
  type SelectionStrategy,
  type SessionConfig,
  type SessionMode,
  type SourceWork,
} from "@/domain/types"
import { typeLabel } from "@/lib/statistics"
import { buildPoolKey } from "@/domain/session-selection"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"

const modes: {
  mode: SessionMode
  label: string
  description: string
  icon: ComponentType<{ className?: string }>
}[] = [
  {
    mode: "learn",
    label: "Aprender",
    description: "Feedback, explicación, referencia y pista. No afecta tu simulacro.",
    icon: BookOpen,
  },
  {
    mode: "smart-review",
    label: "Repaso inteligente",
    description: "Prioriza familias débiles y cambia la redacción.",
    icon: Brain,
  },
  {
    mode: "simulation",
    label: "Simulacro",
    description: "Tiempo y puntuación competitiva, separados de la práctica.",
    icon: TimerReset,
  },
]

const allChapters = [
  ...Array.from({ length: 12 }, (_, index) => ({
    source: "Daniel" as SourceWork,
    chapter: index + 1,
  })),
  ...Array.from({ length: 6 }, (_, index) => ({
    source: "Profetas y Reyes" as SourceWork,
    chapter: index + 39,
  })),
]

const initialConfig: SessionConfig = {
  mode: "learn",
  count: 10,
  sourceWorks: ["Daniel", "Profetas y Reyes"],
  chapters: [],
  difficulties: [1, 2, 3, 4, 5],
  types: [...SUPPORTED_QUESTION_TYPES],
  statuses: ["all"],
  shuffleQuestions: true,
  shuffleOptions: true,
  perQuestionSeconds: null,
  totalSeconds: null,
  bankSelection: "legacy-v1",
  strategy: "coverage-cycle",
}

export function SessionBuilderPage({
  onStart,
}: {
  onStart: (config: SessionConfig, resetCycle?: boolean) => void
}) {
  const { questions, progress, bankSelection, coverageCycles } = useApp()
  const [config, setConfig] = useState<SessionConfig>(() => ({
    ...initialConfig,
    bankSelection,
    difficultyBands:
      bankSelection === "legacy-v1"
        ? undefined
        : ["BASIC", "MEDIUM", "HARD", "EXPERT", "UNRATED"],
  }))
  const [customCount, setCustomCount] = useState(30)
  const [totalEnabled, setTotalEnabled] = useState(false)
  const availableChapters = useMemo(
    () =>
      new Set(
        questions.map(
          (question) => `${question.source.work}:${question.source.chapter}`
        )
      ),
    [questions]
  )
  useEffect(() => {
    setConfig((current) => ({
      ...current,
      bankSelection,
      difficultyBands:
        bankSelection === "legacy-v1"
          ? undefined
          : (current.difficultyBands ?? [
              "BASIC",
              "MEDIUM",
              "HARD",
              "EXPERT",
              "UNRATED",
            ]),
    }))
  }, [bankSelection])
  const eligibleQuestions = useMemo(
    () => filterEligibleQuestions(questions, progress, config),
    [config, progress, questions],
  )
  const estimated = eligibleQuestions.length

  const update = (partial: Partial<SessionConfig>) =>
    setConfig((current) => ({ ...current, ...partial }))
  const toggleSource = (source: SourceWork) =>
    update({
      sourceWorks: config.sourceWorks.includes(source)
        ? config.sourceWorks.filter((item) => item !== source)
        : [...config.sourceWorks, source],
    })
  const toggleDifficulty = (difficulty: number) =>
    update({
      difficulties: config.difficulties.includes(difficulty)
        ? config.difficulties.filter((item) => item !== difficulty)
        : [...config.difficulties, difficulty],
    })
  const toggleDifficultyBand = (band: DifficultyBand) =>
    update({
      difficultyBands: config.difficultyBands?.includes(band)
        ? config.difficultyBands.filter((item) => item !== band)
        : [...(config.difficultyBands ?? []), band],
    })
  const toggleType = (type: QuestionType) =>
    update({
      types: config.types.includes(type)
        ? config.types.filter((item) => item !== type)
        : [...config.types, type],
    })
  const toggleChapter = (chapter: number) =>
    update({
      chapters: config.chapters.includes(chapter)
        ? config.chapters.filter((item) => item !== chapter)
        : [...config.chapters, chapter],
    })
  const selectedCount = config.count === "all" ? estimated : config.count
  const currentMode =
    modes.find((item) => item.mode === config.mode) ?? modes[0]
  const currentCycle =
    config.strategy === "coverage-cycle"
      ? coverageCycles.get(buildPoolKey(config))
      : undefined
  const sequentialBlockCount = Math.max(
    1,
    getSequentialBlockCount(
      eligibleQuestions.length,
      config.count,
    ),
  )
  const selectedSequentialBlock = Math.min(
    Math.max(0, config.sequentialBlock ?? 0),
    sequentialBlockCount - 1,
  )
  useEffect(() => {
    if (config.strategy !== "sequential-blocks") return
    if (selectedSequentialBlock === (config.sequentialBlock ?? 0)) return
    setConfig((current) => ({ ...current, sequentialBlock: selectedSequentialBlock }))
  }, [config.sequentialBlock, config.strategy, selectedSequentialBlock])
  const startStudyDay = (day: StudyDay) => {
    const plan = getStudyDay(day)
    onStart(
      {
        ...initialConfig,
        mode: "learn",
        count: 50,
        sourceWorks: plan.chapters.map((group) => group.work),
        chapters: chaptersForStudyDay(day),
        bankSelection: "prep-v3",
        strategy: "coverage-cycle",
        difficultyBands: ["BASIC", "MEDIUM", "HARD", "EXPERT", "UNRATED"],
      },
      false,
    )
  }
  return (
    <div className="flex flex-col gap-7">
      <section>
        <p className="text-sm font-medium text-muted-foreground">
          Generador de sesiones
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          Configura tu próxima ronda
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Ajusta el foco y la presión. El selector distribuye capítulos, fuentes
          y factKeys para evitar una secuencia predecible.
        </p>
      </section>

      <StudyDayQuickStart onSelect={startStudyDay} />

      <section className="grid grid-cols-2 gap-3 xl:grid-cols-3">
        {modes.map(({ mode, label, description, icon: Icon }) => (
          <button
            key={mode}
            type="button"
            className={`min-w-0 rounded-xl border p-3 text-left transition-colors sm:p-4 ${config.mode === mode ? "border-primary bg-primary/5" : "bg-card hover:bg-muted/40"}`}
            onClick={() => {
              update({ mode })
              if (mode === "simulation")
                {
                  update({ ...SIMULATION_PRESET })
                  setTotalEnabled(true)
                }
              if (mode === "learn" || mode === "smart-review")
                {
                  update({ perQuestionSeconds: null, totalSeconds: null, strategy: mode === "smart-review" ? "adaptive" : "coverage-cycle" })
                  setTotalEnabled(false)
                }
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <span
                className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${config.mode === mode ? "bg-primary text-primary-foreground" : "bg-secondary text-primary"}`}
              >
                <Icon />
              </span>
              {config.mode === mode ? (
                <Check className="text-primary" aria-label="Seleccionado" />
              ) : null}
            </div>
            <p className="mt-3 text-sm font-medium sm:mt-4">{label}</p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              {description}
            </p>
          </button>
        ))}
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="flex flex-col gap-5">
          <Card className="shadow-none">
            <CardHeader>
              <CardTitle>Fuente y capítulos</CardTitle>
              <CardDescription>
                Selecciona uno o varios. Los capítulos sin banco se muestran
                deshabilitados.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">
              <div className="grid gap-3 sm:grid-cols-2">
                <SourceToggle
                  label="Daniel"
                  count={
                    questions.filter((q) => q.source.work === "Daniel").length
                  }
                  checked={config.sourceWorks.includes("Daniel")}
                  onChange={() => toggleSource("Daniel")}
                />
                <SourceToggle
                  label="Profetas y Reyes"
                  count={
                    questions.filter(
                      (q) => q.source.work === "Profetas y Reyes"
                    ).length
                  }
                  checked={config.sourceWorks.includes("Profetas y Reyes")}
                  onChange={() => toggleSource("Profetas y Reyes")}
                />
              </div>
              <Separator />
              <div className="flex flex-wrap gap-2">
                {allChapters.map(({ source, chapter }) => {
                  const available = availableChapters.has(
                    `${source}:${chapter}`
                  )
                  const selected = config.chapters.includes(chapter)
                  return (
                    <Button
                      key={`${source}-${chapter}`}
                      disabled={!available}
                      size="sm"
                      variant={selected ? "default" : "outline"}
                      onClick={() => toggleChapter(chapter)}
                    >
                      {source === "Daniel" ? `D${chapter}` : `PR ${chapter}`}
                      {available ? (
                        <span className="ml-1 text-[10px] opacity-70">
                          {
                            questions.filter(
                              (q) =>
                                q.source.work === source &&
                                q.source.chapter === chapter
                            ).length
                          }
                        </span>
                      ) : null}
                    </Button>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-none">
            <CardHeader>
              <CardTitle>Dificultad y estado</CardTitle>
              <CardDescription>
                El modo elegido puede aplicar sus propios filtros prioritarios.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">
              {bankSelection === "legacy-v1" ? (
                <div className="flex flex-wrap gap-2">
                  {[1, 2, 3, 4, 5].map((difficulty) => (
                    <Button
                      key={difficulty}
                      size="sm"
                      variant={
                        config.difficulties.includes(difficulty)
                          ? "default"
                          : "outline"
                      }
                      onClick={() => toggleDifficulty(difficulty)}
                    >
                      Nivel {difficulty}
                    </Button>
                  ))}
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {(
                    [
                      "BASIC",
                      "MEDIUM",
                      "HARD",
                      "EXPERT",
                      "UNRATED",
                    ] as DifficultyBand[]
                  ).map((band) => (
                    <Button
                      key={band}
                      size="sm"
                      variant={
                        config.difficultyBands?.includes(band)
                          ? "default"
                          : "outline"
                      }
                      onClick={() => toggleDifficultyBand(band)}
                    >
                      {band === "UNRATED" ? "Histórica / sin clasificar" : band}
                    </Button>
                  ))}
                </div>
              )}
              {config.mode === "difficult" ? (
                <Button
                  size="sm"
                  variant="outline"
                  className="w-fit"
                  onClick={() =>
                    update(
                      bankSelection === "legacy-v1"
                        ? { difficulties: [5] }
                        : { difficultyBands: ["EXPERT"] }
                    )
                  }
                >
                  Solo máxima dificultad
                </Button>
              ) : null}
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Estado
                  <Select
                    value={config.statuses[0]}
                    onValueChange={(value) =>
                      update({ statuses: [value as QuestionStatus] })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="all">Todas</SelectItem>
                        <SelectItem value="new">Nuevas</SelectItem>
                        <SelectItem value="failed">Falladas</SelectItem>
                        <SelectItem value="difficult">Difíciles</SelectItem>
                        <SelectItem value="mastered">Dominadas</SelectItem>
                        <SelectItem value="favorite">Favoritas</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </label>
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Cantidad
                  <Select
                    value={String(config.count)}
                    onValueChange={(value) =>
                      update({
                        count:
                          value === "all"
                            ? "all"
                            : value === "custom"
                              ? customCount
                              : Number(value),
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="10">10 preguntas</SelectItem>
                        <SelectItem value="25">25 preguntas</SelectItem>
                        <SelectItem value="50">50 preguntas</SelectItem>
                        <SelectItem value="100">100 preguntas</SelectItem>
                        <SelectItem value="custom">Personalizada</SelectItem>
                        <SelectItem value="all">Todas ({estimated})</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </label>
              </div>
              {typeof config.count === "number" &&
              ![10, 25, 50, 100].includes(config.count) ? (
                <label className="flex max-w-xs flex-col gap-2 text-sm font-medium">
                  Cantidad personalizada
                  <Input
                    type="number"
                    min={1}
                    max={estimated || 1}
                    value={customCount}
                    onChange={(event) => {
                      const value = Math.max(1, Number(event.target.value))
                      setCustomCount(value)
                      update({ count: value })
                    }}
                  />
                </label>
              ) : null}
            </CardContent>
          </Card>

          <Card className="shadow-none">
            <CardHeader>
              <CardTitle>Tipos de pregunta</CardTitle>
              <CardDescription>
                Activa o desactiva cualquier tipo soportado por tus bancos.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {SUPPORTED_QUESTION_TYPES.map((type) => (
                <label
                  key={type}
                  className="flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-colors hover:bg-muted/40"
                >
                  <Checkbox
                    checked={config.types.includes(type)}
                    onCheckedChange={() => toggleType(type)}
                  />
                  <span>{typeLabel(type)}</span>
                </label>
              ))}
            </CardContent>
          </Card>
        </div>

        <aside className="order-first flex flex-col gap-5 xl:order-none">
          <Card className="shadow-none xl:sticky xl:top-24">
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-2">
                Resumen <Badge variant="secondary">{currentMode.label}</Badge>
              </CardTitle>
              <CardDescription>{currentMode.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">
              <div className="rounded-xl bg-muted/40 p-4">
                <div className="flex items-end justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase">
                      Disponibles
                    </p>
                    <p className="mt-1 text-3xl font-semibold">{estimated}</p>
                  </div>
                  <p className="text-right text-xs text-muted-foreground">
                    Se usarán
                    <br />
                    <span className="font-semibold text-foreground">
                      {Math.min(selectedCount, estimated)}
                    </span>
                  </p>
                </div>
                <Progress
                  className="mt-4"
                  value={
                    estimated
                      ? Math.min(100, (selectedCount / estimated) * 100)
                      : 0
                  }
                />
                {currentCycle ? (
                  <p className="mt-3 text-xs text-muted-foreground">
                    {currentCycle.seenQuestionKeys.length} /{" "}
                    {currentCycle.totalPoolSize} recorridas ·{" "}
                    {currentCycle.remainingQuestionKeys.length} pendientes
                  </p>
                ) : null}
              </div>
              <div className="grid gap-3">
                <label className="flex flex-col gap-2 text-sm font-medium">
                  Estrategia de selección
                  <Select
                    value={config.strategy ?? "coverage-cycle"}
                    onValueChange={(value) =>
                      update({
                        strategy: value as SelectionStrategy,
                        shuffleQuestions: value !== "sequential-blocks",
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="coverage-cycle">
                          Cobertura sin repetir
                        </SelectItem>
                        <SelectItem value="random-balanced">
                          Aleatoria equilibrada
                        </SelectItem>
                        <SelectItem value="sequential-blocks">
                          Bloques secuenciales
                        </SelectItem>
                        <SelectItem value="adaptive">Adaptativa</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </label>
                {config.strategy === "sequential-blocks" ? (
                  <SequentialBlockPicker
                    blockCount={sequentialBlockCount}
                    value={selectedSequentialBlock}
                    onChange={(sequentialBlock) => update({ sequentialBlock })}
                  />
                ) : null}
                <TimerField
                  label="Tiempo por pregunta"
                  value={
                    config.perQuestionSeconds === null
                      ? "none"
                      : String(config.perQuestionSeconds)
                  }
                  onChange={(value) =>
                    update({
                      perQuestionSeconds:
                        value === "none" ? null : Number(value),
                    })
                  }
                />
                <div className="flex items-center justify-between gap-3 rounded-lg border px-3 py-3">
                  <div className="flex items-center gap-3">
                    <TimerReset className="text-primary" />
                    <div>
                      <p className="text-sm font-medium">Temporizador total</p>
                      <p className="text-xs text-muted-foreground">
                        Límite para toda la ronda
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={totalEnabled}
                    onCheckedChange={(checked) => {
                      setTotalEnabled(checked)
                      update({ totalSeconds: checked ? 600 : null })
                    }}
                  />
                </div>
                {totalEnabled ? (
                  <TimerField
                    label="Tiempo total"
                    value={String(config.totalSeconds ?? 600)}
                    onChange={(value) =>
                      update({ totalSeconds: Number(value) })
                    }
                    total
                  />
                ) : null}
                <div className="flex items-center justify-between gap-3 rounded-lg border px-3 py-3">
                  <div className="flex items-center gap-3">
                    <Shuffle className="text-primary" />
                    <p className="text-sm font-medium">
                      Usar selección no secuencial
                    </p>
                  </div>
                  <Switch
                    checked={config.shuffleQuestions}
                    onCheckedChange={(checked) =>
                      update({
                        shuffleQuestions: checked,
                        strategy: checked
                          ? "coverage-cycle"
                          : "sequential-blocks",
                      })
                    }
                  />
                </div>
                <div className="flex items-center justify-between gap-3 rounded-lg border px-3 py-3">
                  <div className="flex items-center gap-3">
                    <CircleHelp className="text-primary" />
                    <p className="text-sm font-medium">Aleatorizar opciones</p>
                  </div>
                  <Switch
                    checked={config.shuffleOptions}
                    onCheckedChange={(checked) =>
                      update({ shuffleOptions: checked })
                    }
                  />
                </div>
              </div>
              <Button
                className="w-full"
                disabled={
                  !estimated ||
                  !config.types.length ||
                  !config.sourceWorks.length
                }
                onClick={() =>
                  onStart(
                    config,
                    Boolean(
                      currentCycle &&
                      currentCycle.remainingQuestionKeys.length === 0
                    )
                  )
                }
              >
                {currentCycle && currentCycle.remainingQuestionKeys.length === 0
                  ? "Iniciar nuevo ciclo"
                  : "Comenzar ronda"}{" "}
                <ArrowRight data-icon="inline-end" />
              </Button>
              <p className="text-center text-xs leading-5 text-muted-foreground">
                El progreso se guarda localmente al terminar la ronda.
              </p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  )
}

export function SequentialBlockPicker({
  blockCount,
  value,
  onChange,
}: {
  blockCount: number
  value: number
  onChange: (blockIndex: number) => void
}) {
  const safeBlockCount = Math.max(1, blockCount)
  return (
    <label className="flex flex-col gap-2 text-sm font-medium">
      Bloque de preguntas
      <select
        aria-label="Bloque de preguntas"
        className="h-10 rounded-md border bg-background px-3 text-sm font-medium text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        value={String(Math.min(Math.max(0, value), safeBlockCount - 1) + 1)}
        onChange={(event) => onChange(Number(event.target.value) - 1)}
      >
        {Array.from({ length: safeBlockCount }, (_, index) => (
          <option key={index} value={index + 1}>
            Bloque {index + 1} de {safeBlockCount}
          </option>
        ))}
      </select>
      <span className="text-xs font-normal text-muted-foreground">
        Se muestran {safeBlockCount} bloques según las preguntas elegibles.
      </span>
    </label>
  )
}

export function StudyDayQuickStart({
  onSelect,
}: {
  onSelect: (day: StudyDay) => void
}) {
  const days: StudyDay[] = [1, 2, 3, 4]
  return (
    <Card className="border-primary/20 bg-primary/[0.03] shadow-none">
      <CardHeader>
        <CardTitle>Ruta rápida de 4 días</CardTitle>
        <CardDescription>
          Cada día mezcla Daniel con Profetas y Reyes para ayudarte a recordar por recuperación activa.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {days.map((day) => {
          const plan = getStudyDay(day)
          return (
            <Button
              key={day}
              type="button"
              variant="outline"
              className="h-auto items-start justify-start whitespace-normal p-3 text-left"
              onClick={() => onSelect(day)}
            >
              <span>
                <span className="block font-semibold">Día {day}: {plan.title}</span>
                <span className="mt-1 block text-xs font-normal text-muted-foreground">
                  {plan.method}
                </span>
              </span>
            </Button>
          )
        })}
      </CardContent>
    </Card>
  )
}

function SourceToggle({
  label,
  count,
  checked,
  onChange,
}: {
  label: string
  count: number
  checked: boolean
  onChange: () => void
}) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border px-3 py-3 transition-colors hover:bg-muted/40">
      <span className="flex items-center gap-3">
        <Checkbox checked={checked} onCheckedChange={onChange} />
        <span className="text-sm font-medium">{label}</span>
      </span>
      <Badge variant="secondary">{count}</Badge>
    </label>
  )
}

function TimerField({
  label,
  value,
  onChange,
  total = false,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  total?: boolean
}) {
  return (
    <label className="flex flex-col gap-2 text-sm font-medium">
      {label}
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            {total ? (
              <>
                <SelectItem value="300">5 minutos</SelectItem>
                <SelectItem value="600">10 minutos</SelectItem>
                <SelectItem value="1200">20 minutos</SelectItem>
                <SelectItem value="1800">30 minutos</SelectItem>
              </>
            ) : (
              <>
                <SelectItem value="none">Sin límite</SelectItem>
                <SelectItem value="5">5 segundos</SelectItem>
                <SelectItem value="8">8 segundos</SelectItem>
                <SelectItem value="10">10 segundos</SelectItem>
                <SelectItem value="12">12 segundos</SelectItem>
                <SelectItem value="15">15 segundos</SelectItem>
                <SelectItem value="20">20 segundos</SelectItem>
              </>
            )}
          </SelectGroup>
        </SelectContent>
      </Select>
    </label>
  )
}
