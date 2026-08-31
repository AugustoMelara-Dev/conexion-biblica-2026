export type FinalMissionKind =
  | "reading"
  | "new"
  | "hard-expert"
  | "review"
  | "simulation"
  | "adversarial"
  | "translation-noise"
  | "warm-up"

export type FinalMission = {
  id: string
  date: string
  label: string
  description: string
  count: number
  durationMinutes: number
  chapters: number[]
  exposureKind: "practice" | "cold" | "deferred" | "blind"
  blindPool: "A" | "B" | null
  mode: "smart-review" | "simulation"
  kind: FinalMissionKind
  reading?: string[]
  sourceMix?: { daniel: number; profetasReyes: number }
  optional?: boolean
  familiarity?: "known"
}

type PlanOptions = {
  carryMissedNew?: boolean
  completedMissionIds?: Iterable<string>
}

const mission = (
  date: string,
  slug: string,
  values: Omit<FinalMission, "id" | "date">
): FinalMission => ({ id: `${date}-${slug}`, date, ...values })

const common = {
  blindPool: null,
  mode: "smart-review",
} as const

const plans: Record<string, FinalMission[]> = {
  "2026-08-31": [
    mission("2026-08-31", "reading", {
      ...common,
      kind: "reading",
      label: "Lectura dirigida",
      description:
        "Lee Daniel 1–6 y Profetas y Reyes 39–41 antes de practicar.",
      count: 0,
      durationMinutes: 90,
      chapters: [1, 2, 3, 4, 5, 6, 39, 40, 41],
      exposureKind: "practice",
      reading: ["Daniel 1–6", "Profetas y Reyes 39–41"],
    }),
    mission("2026-08-31", "new", {
      ...common,
      kind: "new",
      label: "Preguntas nuevas",
      description:
        "850 preguntas nuevas de Daniel 1–6 y Profetas y Reyes 39–41.",
      count: 850,
      durationMinutes: 300,
      chapters: [1, 2, 3, 4, 5, 6, 39, 40, 41],
      exposureKind: "cold",
    }),
    mission("2026-08-31", "hard-expert", {
      ...common,
      kind: "hard-expert",
      label: "HARD / EXPERT",
      description: "300 preguntas HARD/EXPERT de la mitad estudiada hoy.",
      count: 300,
      durationMinutes: 120,
      chapters: [1, 2, 3, 4, 5, 6, 39, 40, 41],
      exposureKind: "deferred",
    }),
    mission("2026-08-31", "review", {
      ...common,
      kind: "review",
      label: "Falladas, dudadas y lentas",
      description: "150 falladas, dudadas o respondidas con lentitud.",
      count: 150,
      durationMinutes: 60,
      chapters: [],
      exposureKind: "practice",
    }),
    mission("2026-08-31", "simulation", {
      ...common,
      kind: "simulation",
      label: "Simulación 5 × 20",
      description: "100 preguntas en 5 × 20, con pausas breves entre tandas.",
      count: 100,
      durationMinutes: 50,
      chapters: [],
      exposureKind: "deferred",
      mode: "simulation",
    }),
  ],
  "2026-09-01": [
    mission("2026-09-01", "reading", {
      ...common,
      kind: "reading",
      label: "Lectura dirigida",
      description:
        "Lee Daniel 7–12 y Profetas y Reyes 42–44 antes de practicar.",
      count: 0,
      durationMinutes: 90,
      chapters: [7, 8, 9, 10, 11, 12, 42, 43, 44],
      exposureKind: "practice",
      reading: ["Daniel 7–12", "Profetas y Reyes 42–44"],
    }),
    mission("2026-09-01", "new", {
      ...common,
      kind: "new",
      label: "Preguntas nuevas",
      description:
        "850 preguntas nuevas de Daniel 7–12 y Profetas y Reyes 42–44.",
      count: 850,
      durationMinutes: 300,
      chapters: [7, 8, 9, 10, 11, 12, 42, 43, 44],
      exposureKind: "cold",
    }),
    mission("2026-09-01", "hard-expert", {
      ...common,
      kind: "hard-expert",
      label: "HARD / EXPERT",
      description: "300 preguntas HARD/EXPERT de la mitad estudiada hoy.",
      count: 300,
      durationMinutes: 120,
      chapters: [7, 8, 9, 10, 11, 12, 42, 43, 44],
      exposureKind: "deferred",
    }),
    mission("2026-09-01", "review", {
      ...common,
      kind: "review",
      label: "Repaso de errores",
      description: "150 falladas, dudadas o respondidas con lentitud.",
      count: 150,
      durationMinutes: 60,
      chapters: [],
      exposureKind: "practice",
    }),
    mission("2026-09-01", "simulation", {
      ...common,
      kind: "simulation",
      label: "Simulación 5 × 20",
      description: "100 preguntas en 5 × 20, con pausas breves entre tandas.",
      count: 100,
      durationMinutes: 50,
      chapters: [],
      exposureKind: "deferred",
      mode: "simulation",
    }),
  ],
  "2026-09-02": [
    mission("2026-09-02", "reading", {
      ...common,
      kind: "reading",
      label: "Lectura dirigida",
      description:
        "Lee Daniel 1–12 y Profetas y Reyes 39–44 antes de practicar.",
      count: 0,
      durationMinutes: 120,
      chapters: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 39, 40, 41, 42, 43, 44],
      exposureKind: "practice",
      reading: ["Daniel 1–12", "Profetas y Reyes 39–44"],
    }),
    mission("2026-09-02", "new", {
      ...common,
      kind: "new",
      label: "Nuevas no vistas",
      description:
        "Prioriza 800 preguntas nuevas todavía no vistas de todo el material.",
      count: 800,
      durationMinutes: 280,
      chapters: [],
      exposureKind: "cold",
    }),
    mission("2026-09-02", "hard-expert", {
      ...common,
      kind: "hard-expert",
      label: "Segunda exposición HARD / EXPERT",
      description:
        "300 HARD/EXPERT en segunda exposición, con recuperación real.",
      count: 300,
      durationMinutes: 120,
      chapters: [],
      exposureKind: "deferred",
    }),
    mission("2026-09-02", "review", {
      ...common,
      kind: "review",
      label: "Errores y lentas",
      description: "100 falladas, dudadas o lentas de ambos materiales.",
      count: 100,
      durationMinutes: 45,
      chapters: [],
      exposureKind: "practice",
    }),
    mission("2026-09-02", "simulation-a", {
      ...common,
      kind: "simulation",
      label: "Simulación A · 5 × 20",
      description: "Primera simulación de 100 preguntas en 5 × 20.",
      count: 100,
      durationMinutes: 50,
      chapters: [],
      exposureKind: "deferred",
      mode: "simulation",
    }),
    mission("2026-09-02", "simulation-b", {
      ...common,
      kind: "simulation",
      label: "Simulación B · 5 × 20",
      description: "Segunda simulación de 100 preguntas en 5 × 20.",
      count: 100,
      durationMinutes: 50,
      chapters: [],
      exposureKind: "deferred",
      mode: "simulation",
    }),
  ],
  "2026-09-03": [
    mission("2026-09-03", "reading", {
      ...common,
      kind: "reading",
      label: "Lectura dirigida",
      description:
        "Lee Daniel 1–12 y Profetas y Reyes 39–44 antes de practicar.",
      count: 0,
      durationMinutes: 120,
      chapters: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 39, 40, 41, 42, 43, 44],
      exposureKind: "practice",
      reading: ["Daniel 1–12", "Profetas y Reyes 39–44"],
    }),
    mission("2026-09-03", "adversarial", {
      ...common,
      kind: "adversarial",
      label: "Variantes adversariales",
      description: "700 variantes adversariales nuevas de todo el material.",
      count: 700,
      durationMinutes: 245,
      chapters: [],
      exposureKind: "cold",
    }),
    mission("2026-09-03", "translation-noise", {
      ...common,
      kind: "translation-noise",
      label: "Ruido de traducción",
      description:
        "200 casos translation_noise para separar redacción de conocimiento.",
      count: 200,
      durationMinutes: 80,
      chapters: [],
      exposureKind: "practice",
    }),
    mission("2026-09-03", "review", {
      ...common,
      kind: "review",
      label: "Errores y lentas",
      description: "200 falladas, dudadas o lentas de todo el material.",
      count: 200,
      durationMinutes: 80,
      chapters: [],
      exposureKind: "practice",
    }),
    ...(
      [
        ["60-40", 60, 40],
        ["50-50", 50, 50],
        ["40-60", 40, 60],
      ] as const
    ).map(([slug, daniel, profetasReyes]) =>
      mission("2026-09-03", `simulation-${slug}`, {
        ...common,
        kind: "simulation",
        label: `Simulación ${daniel}/${profetasReyes}`,
        description: `${daniel}% Daniel y ${profetasReyes}% Profetas y Reyes.`,
        count: 100,
        durationMinutes: 50,
        chapters: [],
        exposureKind: "deferred",
        mode: "simulation",
        sourceMix: { daniel, profetasReyes },
      })
    ),
  ],
  "2026-09-04": [
    mission("2026-09-04", "adversarial", {
      ...common,
      kind: "adversarial",
      label: "Adversariales nuevas",
      description:
        "200 adversariales nuevas solo del texto relacionado con fallos y dudas.",
      count: 200,
      durationMinutes: 70,
      chapters: [],
      exposureKind: "cold",
    }),
    mission("2026-09-04", "simulation", {
      ...common,
      kind: "simulation",
      label: "Simulación final",
      description: "100 preguntas de simulación, sin añadir volumen después.",
      count: 100,
      durationMinutes: 50,
      chapters: [],
      exposureKind: "deferred",
      mode: "simulation",
    }),
    mission("2026-09-04", "review", {
      ...common,
      kind: "review",
      label: "Errores, dudas y lentas",
      description: "200 fallos, dudas y lentas. Termina temprano.",
      count: 200,
      durationMinutes: 70,
      chapters: [],
      exposureKind: "practice",
    }),
  ],
  "2026-09-05": [
    mission("2026-09-05", "warm-up", {
      ...common,
      kind: "warm-up",
      label: "Calentamiento opcional",
      description: "15 preguntas conocidas. Nada nuevo y sin maratón.",
      count: 15,
      durationMinutes: 10,
      chapters: [],
      exposureKind: "deferred",
      optional: true,
      familiarity: "known",
    }),
  ],
}

const routeDates = Object.keys(plans).sort()

function localDate(now: Date) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Tegucigalpa",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now)
}

function scheduledDate(now: Date) {
  const today = localDate(now)
  if (today <= routeDates[0]) return routeDates[0]
  if (today >= routeDates.at(-1)!) return routeDates.at(-1)!
  return today
}

function isNewWork(mission: FinalMission) {
  return mission.kind === "new" || mission.kind === "adversarial"
}

export function buildFinalMissionPlan(
  now = new Date(),
  { carryMissedNew = true, completedMissionIds = [] }: PlanOptions = {}
) {
  const date = scheduledDate(now)
  const plan = plans[date].map((item) => ({ ...item }))
  if (!carryMissedNew || date >= "2026-09-04" || date === routeDates[0]) {
    return plan
  }

  const completed = new Set(completedMissionIds)
  const carried = routeDates
    .filter((routeDate) => routeDate < date)
    .flatMap((routeDate) => plans[routeDate])
    .filter(isNewWork)
    .filter((item) => !completed.has(item.id))
    .reduce((total, item) => total + item.count, 0)
  const target = plan.find(isNewWork)
  if (target && carried > 0) {
    target.count += carried
    target.description = `${target.description} Incluye ${carried.toLocaleString("es-HN")} nuevas trasladadas de fechas pasadas.`
  }
  return plan
}

export function getNextMission(
  plan: FinalMission[],
  completed: Set<string>,
  _now = new Date()
) {
  void _now
  const eligible = plan.filter((item) => item.kind !== "reading")
  return eligible.find((item) => !completed.has(item.id)) ?? null
}
