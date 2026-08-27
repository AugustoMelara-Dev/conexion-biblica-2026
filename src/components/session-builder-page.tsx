import { useEffect, useId, useMemo, useState, type ReactNode } from "react"
import { CircleHelp, Shuffle, TimerReset } from "lucide-react"
import { useApp } from "@/app/app-state"
import { AdvancedSettings } from "@/components/practice/advanced-settings"
import { EssentialSettings } from "@/components/practice/essential-settings"
import { ModePicker } from "@/components/practice/mode-picker"
import { MassiveTrainingHub } from "@/components/massive-training-hub"
import { RoundSummary } from "@/components/practice/round-summary"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { filterEligibleQuestions } from "@/domain/session-selector"
import {
  buildPoolKey,
  getSequentialBlockCount,
} from "@/domain/session-selection"
import { SIMULATION_PRESET } from "@/domain/simulation-calibration"
import {
  getStudyDay,
  type StudyDay,
} from "@/domain/study-plan"
import {
  type DifficultyBand,
  type QuestionStatus,
  type QuestionType,
  type SelectionStrategy,
  type SessionConfig,
} from "@/domain/types"
import { typeLabel } from "@/lib/statistics"

const allChapters = [
  ...Array.from({ length: 12 }, (_, index) => ({
    source: "Daniel" as const,
    chapter: index + 1,
  })),
  ...Array.from({ length: 6 }, (_, index) => ({
    source: "Profetas y Reyes" as const,
    chapter: index + 39,
  })),
]

const FINAL_VISIBLE_TYPES: QuestionType[] = [
  "single_choice",
  "fill_blank",
  "true_false",
]

const initialConfig: SessionConfig = {
  mode: "learn",
  count: 10,
  sourceWorks: ["Daniel", "Profetas y Reyes"],
  chapters: [],
  difficulties: [1, 2, 3, 4, 5],
  types: [...FINAL_VISIBLE_TYPES],
  statuses: ["all"],
  shuffleQuestions: true,
  shuffleOptions: true,
  perQuestionSeconds: null,
  totalSeconds: null,
  bankSelection: "final-v7",
  strategy: "coverage-cycle",
}

export function SessionBuilderPage({
  onStart,
}: {
  onStart: (config: SessionConfig, resetCycle?: boolean) => void
}) {
  const {
    questions,
    progress,
    bankSelection,
    coverageCycles,
    finalManifest,
  } = useApp()
  const [config, setConfig] = useState<SessionConfig>(() => ({
    ...initialConfig,
    bankSelection,
    difficultyBands:
      bankSelection === "legacy-v1"
        ? undefined
        : ["BASIC", "MEDIUM", "HARD", "EXPERT", "UNRATED"],
  }))
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [totalEnabled, setTotalEnabled] = useState(false)
  const finalChapterCounts = useMemo(() => {
    const counts = new Map<string, number>()
    if (bankSelection !== "final-v7" || !finalManifest) return counts
    for (const shard of finalManifest.shards) {
      const chapter = Number(shard.chapter.match(/\d+/)?.[0])
      const work = shard.chapter.startsWith("DAN")
        ? "Daniel"
        : "Profetas y Reyes"
      counts.set(
        `${work}:${chapter}`,
        shard.training_question_count ?? shard.question_count
      )
    }
    return counts
  }, [bankSelection, finalManifest])
  const availableChapters = useMemo(() => {
    if (finalChapterCounts.size) return new Set(finalChapterCounts.keys())
    return new Set(
      questions.map(
        (question) => `${question.source.work}:${question.source.chapter}`
      )
    )
  }, [finalChapterCounts, questions])

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
    [config, progress, questions]
  )
  const manifestEstimate = useMemo(() => {
    if (bankSelection !== "final-v7" || !finalChapterCounts.size) return null
    if (!config.sourceWorks.length || !config.types.length) return 0
    if (
      config.difficultyBands?.length &&
      !config.difficultyBands.some((band) => band !== "UNRATED")
    )
      return 0
    const works = new Set(config.sourceWorks)
    const chapters = new Set(config.chapters)
    let total = 0
    for (const [key, count] of finalChapterCounts) {
      const [work, rawChapter] = key.split(":")
      const chapter = Number(rawChapter)
      if (!works.has(work as (typeof config.sourceWorks)[number])) continue
      if (chapters.size && !chapters.has(chapter)) continue
      total += count
    }
    return total
  }, [bankSelection, config, finalChapterCounts])
  const estimated = manifestEstimate ?? eligibleQuestions.length
  const update = (partial: Partial<SessionConfig>) =>
    setConfig((current) => ({ ...current, ...partial }))
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
  const currentCycle =
    config.strategy === "coverage-cycle"
      ? coverageCycles.get(buildPoolKey(config))
      : undefined
  const sequentialBlockCount = Math.max(
    1,
    getSequentialBlockCount(estimated, config.count)
  )
  const selectedSequentialBlock = Math.min(
    Math.max(0, config.sequentialBlock ?? 0),
    sequentialBlockCount - 1
  )

  useEffect(() => {
    if (config.strategy !== "sequential-blocks") return
    if (selectedSequentialBlock === (config.sequentialBlock ?? 0)) return
    setConfig((current) => ({
      ...current,
      sequentialBlock: selectedSequentialBlock,
    }))
  }, [config.sequentialBlock, config.strategy, selectedSequentialBlock])

  const selectMode = (mode: SessionConfig["mode"]) => {
    setConfig((current) =>
      mode === "simulation"
        ? { ...current, mode, ...SIMULATION_PRESET }
        : {
            ...current,
            mode,
            perQuestionSeconds: null,
            totalSeconds: null,
            strategy: mode === "smart-review" ? "adaptive" : "coverage-cycle",
          }
    )
    setTotalEnabled(mode === "simulation")
  }
  const resetCycle = Boolean(
    currentCycle && currentCycle.remainingQuestionKeys.length === 0
  )

  return (
    <div className="flex flex-col gap-7">
      <PageHeader
        eyebrow="Entrenamiento"
        title="Configura tu próxima ronda"
        description="Elige cómo quieres estudiar; ajusta los detalles solo si los necesitas."
      />
      <MassiveTrainingHub onStart={(massiveConfig) => onStart(massiveConfig)} />
      <ModePicker value={config.mode} onChange={selectMode} />
      <section className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="grid gap-6">
          <EssentialSettings
            count={config.count}
            sourceWorks={config.sourceWorks}
            onCountChange={(value) => update({ count: value })}
            onSourceWorksChange={(value) => update({ sourceWorks: value })}
          />
          <AdvancedSettings open={advancedOpen} onOpenChange={setAdvancedOpen}>
            <div data-testid="advanced-round-settings" className="grid gap-6">
              <section
                aria-labelledby="difficulty-heading"
                className="grid gap-4"
              >
                <div>
                  <h2 id="difficulty-heading" className="font-semibold">
                    Dificultad
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    El modo elegido puede aplicar sus propios filtros
                    prioritarios.
                  </p>
                </div>
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
                        {band === "UNRATED"
                          ? "Histórica / sin clasificar"
                          : band}
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
              </section>
              <section
                aria-labelledby="chapters-heading"
                className="grid gap-4"
              >
                <div>
                  <h2 id="chapters-heading" className="font-semibold">
                    Capítulos
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Los capítulos sin banco se muestran deshabilitados.
                  </p>
                </div>
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
                            {finalChapterCounts.get(`${source}:${chapter}`) ??
                              questions.filter(
                                (q) =>
                                  q.source.work === source &&
                                  q.source.chapter === chapter
                              ).length}
                          </span>
                        ) : null}
                      </Button>
                    )
                  })}
                </div>
              </section>
              <section aria-labelledby="types-heading" className="grid gap-4">
                <div>
                  <h2 id="types-heading" className="font-semibold">
                    Tipos de pregunta
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Activa o desactiva las familias de pregunta del banco maestro.
                  </p>
                </div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {FINAL_VISIBLE_TYPES.map((type) => (
                    <label
                      key={type}
                      className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-colors hover:bg-muted/40"
                    >
                      <Checkbox
                        checked={config.types.includes(type)}
                        onCheckedChange={() => toggleType(type)}
                      />
                      <span>{typeLabel(type)}</span>
                    </label>
                  ))}
                </div>
              </section>
              <section
                aria-labelledby="round-rules-heading"
                className="grid gap-4"
              >
                <h2 id="round-rules-heading" className="font-semibold">
                  Estado, orden y tiempo
                </h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="grid gap-2 text-sm font-medium">
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
                  <label className="grid gap-2 text-sm font-medium">
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
                </div>
                {config.strategy === "sequential-blocks" ? (
                  <SequentialBlockPicker
                    blockCount={sequentialBlockCount}
                    value={selectedSequentialBlock}
                    onChange={(sequentialBlock) => update({ sequentialBlock })}
                  />
                ) : null}
                <div className="grid gap-3 sm:grid-cols-2">
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
                </div>
                <ToggleSetting
                  icon={
                    <TimerReset className="text-primary" aria-hidden="true" />
                  }
                  title="Temporizador total"
                  description="Límite para toda la ronda"
                  checked={totalEnabled}
                  onCheckedChange={(checked) => {
                    setTotalEnabled(checked)
                    update({ totalSeconds: checked ? 600 : null })
                  }}
                />
                <ToggleSetting
                  icon={<Shuffle className="text-primary" aria-hidden="true" />}
                  title="Usar selección no secuencial"
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
                <ToggleSetting
                  icon={
                    <CircleHelp className="text-primary" aria-hidden="true" />
                  }
                  title="Aleatorizar opciones"
                  checked={config.shuffleOptions}
                  onCheckedChange={(checked) =>
                    update({ shuffleOptions: checked })
                  }
                />
              </section>
            </div>
          </AdvancedSettings>
        </div>
        <aside className="min-w-0 xl:sticky xl:top-24 xl:self-start">
          <RoundSummary
            eligibleCount={estimated}
            count={config.count}
            mode={config.mode}
            disabled={
              !estimated || !config.types.length || !config.sourceWorks.length
            }
            onStart={() =>
              onStart(
                {
                  ...config,
                  massive:
                    config.massive || config.bankSelection === "final-v7",
                },
                resetCycle
              )
            }
          />
          {currentCycle ? (
            <p className="mt-3 text-xs text-muted-foreground">
              {currentCycle.seenQuestionKeys.length} /{" "}
              {currentCycle.totalPoolSize} recorridas ·{" "}
              {currentCycle.remainingQuestionKeys.length} pendientes
            </p>
          ) : null}
        </aside>
      </section>
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
    <label className="grid gap-2 text-sm font-medium">
      Bloque de preguntas
      <select
        aria-label="Bloque de preguntas"
        className="h-10 rounded-md border bg-background px-3 text-sm font-medium text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
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
          Cada día mezcla Daniel con Profetas y Reyes para ayudarte a recordar
          por recuperación activa.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 md:grid-cols-2">
        {days.map((day) => {
          const plan = getStudyDay(day)
          return (
            <Button
              key={day}
              type="button"
              variant="outline"
              className="h-auto min-h-11 items-start justify-start p-3 text-left whitespace-normal"
              onClick={() => onSelect(day)}
            >
              <span>
                <span className="block font-semibold">
                  Día {day}: {plan.title}
                </span>
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

function ToggleSetting({
  icon,
  title,
  description,
  checked,
  onCheckedChange,
}: {
  icon: ReactNode
  title: string
  description?: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}) {
  const labelId = useId()

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border px-3 py-3">
      <div className="flex items-center gap-3">
        {icon}
        <div>
          <p id={labelId} className="text-sm font-medium">
            {title}
          </p>
          {description ? (
            <p className="text-xs text-muted-foreground">{description}</p>
          ) : null}
        </div>
      </div>
      <Switch
        aria-labelledby={labelId}
        checked={checked}
        onCheckedChange={onCheckedChange}
      />
    </div>
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
    <label className="grid gap-2 text-sm font-medium">
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
