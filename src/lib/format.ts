import { formatElapsedMs } from "@/domain/time"
import type { SessionMode, SourceWork } from "@/domain/types"

export { formatElapsedMs }

export function formatDate(timestamp: number) {
  return new Intl.DateTimeFormat("es-HN", { dateStyle: "medium", timeStyle: "short" }).format(timestamp)
}

export function sourceLabel(source: SourceWork) {
  return source === "Daniel" ? "Daniel" : "Profetas y Reyes"
}

export function modeLabel(mode: SessionMode) {
  const labels: Record<SessionMode, string> = {
    learn: "Aprender",
    "smart-review": "Repaso inteligente",
    simulation: "Simulacro",
    final: "Modo final",
    training: "Entrenamiento",
    errors: "Modo errores",
    difficult: "Modo difíciles",
    speed: "Velocidad",
    new: "Preguntas nuevas",
    mixed: "Mezcla total",
    chapter: "Por capítulo",
    championship: "Campeonato",
  }
  return labels[mode]
}

export function chapterLabel(work: SourceWork, chapter: number) {
  return work === "Daniel" ? `Daniel ${chapter}` : `PR ${chapter}`
}

export function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
