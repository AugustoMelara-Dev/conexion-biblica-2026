import type { SourceWork } from "@/domain/types"
import type { MassiveTrainingModeId } from "@/domain/training-modes"

export type ChapterSignal = {
  work: SourceWork
  chapter: number
  incorrect: number
  slow: number
}

export type Final48HourBlock = {
  id: string
  day: 1 | 2
  label: string
  count: number
  modeId: MassiveTrainingModeId
  focus: Array<{ work: SourceWork; chapter: number }>
}

function weakest(signals: ChapterSignal[], count: number) {
  return signals
    .slice()
    .sort(
      (left, right) =>
        right.incorrect * 3 + right.slow - (left.incorrect * 3 + left.slow)
    )
    .slice(0, count)
    .map(({ work, chapter }) => ({ work, chapter }))
}

export function buildFinal48HourPlan(
  signals: ChapterSignal[]
): Final48HourBlock[] {
  const adaptive = weakest(signals, 4)
  return [
    { id: "d1-diagnostic-pr", day: 1, label: "Diagnóstico PR39–44", count: 150, modeId: "pr-complete", focus: [39, 40, 41, 42, 43, 44].map((chapter) => ({ work: "Profetas y Reyes" as const, chapter })) },
    { id: "d1-diagnostic-daniel", day: 1, label: "Diagnóstico Daniel 7–12", count: 150, modeId: "daniel-7-12-intensive", focus: [7, 8, 9, 10, 11, 12].map((chapter) => ({ work: "Daniel" as const, chapter })) },
    { id: "d1-pr43-44", day: 1, label: "Bloque PR43–44", count: 100, modeId: "pr43-44-intensive", focus: [43, 44].map((chapter) => ({ work: "Profetas y Reyes" as const, chapter })) },
    { id: "d1-daniel-7-9-11", day: 1, label: "Bloque Daniel 7–9–11", count: 100, modeId: "daniel-7-9-11-intensive", focus: [7, 9, 11].map((chapter) => ({ work: "Daniel" as const, chapter })) },
    { id: "d1-errors-slow", day: 1, label: "Errores y lentas", count: 50, modeId: "previous-errors", focus: adaptive },
    { id: "d2-unseen", day: 2, label: "Preguntas nunca vistas", count: 150, modeId: "unseen-only", focus: adaptive },
    { id: "d2-traps", day: 2, label: "Trampas contextuales", count: 100, modeId: "contextual-traps", focus: adaptive },
    { id: "d2-pr-mixed", day: 2, label: "PR39–44 mezclado", count: 100, modeId: "pr-complete", focus: adaptive.filter((item) => item.work === "Profetas y Reyes") },
    { id: "d2-daniel-mixed", day: 2, label: "Daniel 1–12 mezclado", count: 100, modeId: "daniel-complete", focus: adaptive.filter((item) => item.work === "Daniel") },
    { id: "d2-blind-final", day: 2, label: "Simulación ciega final", count: 100, modeId: "blind-simulation", focus: [] },
  ]
}
