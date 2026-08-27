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
}

const missions: FinalMission[] = [
  { id: "26-cold-tier-a", date: "2026-08-26", label: "Diagnóstico frío prioritario", description: "150 preguntas de PR43, PR44 y Daniel 7, 8, 9 y 11; sin pistas ni hechos repetidos.", count: 150, durationMinutes: 90, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "cold", blindPool: null, mode: "simulation" },
  { id: "26-guided-repair", date: "2026-08-26", label: "Reparación de errores y lentas", description: "Contrasta cada error y recupéralo después con otra familia.", count: 60, durationMinutes: 45, chapters: [], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-weak-1", date: "2026-08-26", label: "Capítulo débil · bloque 1", description: "50 preguntas del capítulo con menor precisión tras el diagnóstico.", count: 50, durationMinutes: 35, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-weak-2", date: "2026-08-26", label: "Capítulo débil · bloque 2", description: "50 preguntas del segundo capítulo con menor precisión.", count: 50, durationMinutes: 35, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-weak-3", date: "2026-08-26", label: "Capítulo débil · bloque 3", description: "50 preguntas del tercer capítulo con menor precisión.", count: 50, durationMinutes: 35, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-mixed", date: "2026-08-26", label: "Mezcla completa", description: "Daniel 1–12 y PR39–44, ponderados por debilidad.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-night", date: "2026-08-26", label: "Recuperación diferida nocturna", description: "70 hechos estudiados varias horas antes.", count: 70, durationMinutes: 45, chapters: [], exposureKind: "deferred", blindPool: null, mode: "simulation" },
  { id: "27-morning", date: "2026-08-27", label: "Prueba fría matutina", description: "Vencidas, sin leer antes ni repetir enunciados.", count: 100, durationMinutes: 60, chapters: [], exposureKind: "cold", blindPool: null, mode: "simulation" },
  { id: "27-context", date: "2026-08-27", label: "Trampas contextuales", description: "Distingue detalles verdaderos que pertenecen a otra escena.", count: 100, durationMinutes: 70, chapters: [], exposureKind: "cold", blindPool: null, mode: "simulation" },
  { id: "27-fill", date: "2026-08-27", label: "Completar con opciones", description: "100 expresiones significativas, siempre seleccionando entre A–D.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "deferred", blindPool: null, mode: "simulation" },
  { id: "27-true-false", date: "2026-08-27", label: "Verdadero/Falso de detalle fino", description: "100 afirmaciones naturales con un solo dato decisivo.", count: 100, durationMinutes: 50, chapters: [], exposureKind: "deferred", blindPool: null, mode: "simulation" },
  { id: "27-blind-a", date: "2026-08-27", label: "Simulación ciega A", description: "100 hechos GOLD nunca expuestos; feedback al finalizar.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "blind", blindPool: "A", mode: "simulation" },
  { id: "27-repair", date: "2026-08-27", label: "Reparación de la simulación", description: "Solo errores de la simulación, con otra variante y contraste exacto.", count: 80, durationMinutes: 55, chapters: [], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "27-blind-b", date: "2026-08-27", label: "Simulación ciega B", description: "Pool independiente, sin hechos de la simulación A.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "blind", blindPool: "B", mode: "simulation" },
  { id: "27-red-sheet", date: "2026-08-27", label: "Hoja roja final", description: "Máximo 50 hechos recurrentes que aún requieren recuperación.", count: 50, durationMinutes: 30, chapters: [], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "29-activation", date: "2026-08-29", label: "Activación de competencia", description: "20 preguntas medias conocidas, 20 hechos rojos y 10 de confianza; termina 60–90 minutos antes.", count: 50, durationMinutes: 30, chapters: [], exposureKind: "deferred", blindPool: null, mode: "smart-review" },
]

function localDate(now: Date) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Tegucigalpa", year: "numeric", month: "2-digit", day: "2-digit" }).format(now)
}

export function buildFinalMissionPlan(now = new Date()) {
  const today = localDate(now)
  if (today >= "2026-08-29") return missions.filter((mission) => mission.date === "2026-08-29")
  if (today <= "2026-08-26") return missions.filter((mission) => mission.date === "2026-08-26")
  return missions.filter((mission) => mission.date === "2026-08-27")
}

export function getNextMission(plan: FinalMission[], completed: Set<string>, _now = new Date()) {
  void _now
  return plan.find((mission) => !completed.has(mission.id)) ?? plan.at(-1) ?? null
}
