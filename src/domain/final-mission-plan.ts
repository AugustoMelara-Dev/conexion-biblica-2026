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
  { id: "26-cold-tier-a", date: "2026-08-26", label: "Diagnóstico frío prioritario", description: "PR43, PR44 y Daniel 7, 8, 9 y 11; sin pistas ni hechos repetidos.", count: 120, durationMinutes: 70, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "cold", blindPool: null, mode: "simulation" },
  { id: "26-guided-repair", date: "2026-08-26", label: "Reparación guiada", description: "Contrasta cada error y recupéralo tras preguntas intermedias.", count: 60, durationMinutes: 45, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-weak-blocks", date: "2026-08-26", label: "Dos capítulos más débiles", description: "Dos bloques de 60 adaptados al diagnóstico.", count: 120, durationMinutes: 80, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-mixed", date: "2026-08-26", label: "Mezcla completa", description: "Daniel 1–12 y PR39–44, ponderados por debilidad.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "26-night", date: "2026-08-26", label: "Recuperación diferida nocturna", description: "Hechos estudiados varias horas antes.", count: 60, durationMinutes: 40, chapters: [], exposureKind: "deferred", blindPool: null, mode: "simulation" },
  { id: "27-morning", date: "2026-08-27", label: "Prueba fría matutina", description: "Vencidas, sin leer antes ni repetir enunciados.", count: 100, durationMinutes: 60, chapters: [], exposureKind: "cold", blindPool: null, mode: "simulation" },
  { id: "27-weak-three", date: "2026-08-27", label: "Tres capítulos más débiles", description: "Bloques focalizados de 50–60 preguntas.", count: 165, durationMinutes: 105, chapters: [43, 44, 7, 8, 9, 11], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "27-context", date: "2026-08-27", label: "Trampas contextuales", description: "Distingue detalles verdaderos que pertenecen a otra escena.", count: 100, durationMinutes: 70, chapters: [], exposureKind: "cold", blindPool: null, mode: "simulation" },
  { id: "27-deferred", date: "2026-08-27", label: "Recuperación diferida", description: "Solo hechos cuyo intervalo ya aporta evidencia.", count: 60, durationMinutes: 40, chapters: [], exposureKind: "deferred", blindPool: null, mode: "simulation" },
  { id: "28-blind-a", date: "2026-08-28", label: "Simulación ciega A", description: "100 hechos GOLD nunca expuestos; feedback al finalizar.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "blind", blindPool: "A", mode: "simulation" },
  { id: "28-repair", date: "2026-08-28", label: "Reparación de la simulación", description: "Máximo 80 hechos, con contraste exacto.", count: 80, durationMinutes: 55, chapters: [], exposureKind: "practice", blindPool: null, mode: "smart-review" },
  { id: "28-weak-two", date: "2026-08-28", label: "Dos resultados más débiles", description: "Dos bloques de 50 antes de la segunda simulación.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "deferred", blindPool: null, mode: "simulation" },
  { id: "28-blind-b", date: "2026-08-28", label: "Simulación ciega B", description: "Pool independiente, sin hechos de la simulación A.", count: 100, durationMinutes: 65, chapters: [], exposureKind: "blind", blindPool: "B", mode: "simulation" },
  { id: "29-activation", date: "2026-08-29", label: "Activación de competencia", description: "Preguntas conocidas y hechos rojos; termina 60–90 minutos antes.", count: 50, durationMinutes: 30, chapters: [], exposureKind: "deferred", blindPool: null, mode: "smart-review" },
]

function localDate(now: Date) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Tegucigalpa", year: "numeric", month: "2-digit", day: "2-digit" }).format(now)
}

export function buildFinalMissionPlan(now = new Date()) {
  const today = localDate(now)
  if (today >= "2026-08-29") return missions.filter((mission) => mission.date === "2026-08-29")
  if (today <= "2026-08-26") return missions.filter((mission) => mission.date === "2026-08-26")
  return missions.filter((mission) => mission.date === today)
}

export function getNextMission(plan: FinalMission[], completed: Set<string>, _now = new Date()) {
  void _now
  return plan.find((mission) => !completed.has(mission.id)) ?? plan.at(-1) ?? null
}
