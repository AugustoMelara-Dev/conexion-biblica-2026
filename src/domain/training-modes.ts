import type {
  DifficultyBand,
  QuestionStatus,
  QuestionType,
  SourceWork,
} from "@/domain/types"

export type MassiveTrainingModeId =
  | "national-final"
  | "extreme-championship"
  | "pr-complete"
  | "daniel-complete"
  | "daniel-7-12-intensive"
  | "daniel-7-9-11-intensive"
  | "pr43-44-intensive"
  | "unseen-only"
  | "contextual-traps"
  | "fill-text"
  | "expert-true-false"
  | "expert-multiple-choice"
  | "order-sequence"
  | "previous-errors"
  | "slow-correct"
  | "weak-chapters"
  | "cold-mode"
  | "speed-mode"
  | "spaced-review"
  | "blind-simulation"

export type MassiveTrainingMode = {
  id: MassiveTrainingModeId
  label: string
  description: string
  group: "competencia" | "cobertura" | "precisión" | "adaptativo"
  count: number
  sourceWorks: SourceWork[]
  chapters: number[]
  types: QuestionType[]
  difficultyBands: DifficultyBand[]
  statuses: QuestionStatus[]
  includeBlind: boolean
  perQuestionSeconds: number | null
  noveltyOnly?: boolean
  contextualOnly?: boolean
  slowOnly?: boolean
}

const ALL_DIFFICULTIES: DifficultyBand[] = ["BASIC", "MEDIUM", "HARD", "EXPERT"]
const ALL_WORKS: SourceWork[] = ["Daniel", "Profetas y Reyes"]

export const MASSIVE_TRAINING_MODES: MassiveTrainingMode[] = [
  { id: "national-final", label: "Final nacional", description: "100 preguntas con mezcla de final.", group: "competencia", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ["HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 12 },
  { id: "extreme-championship", label: "Campeonato extremo", description: "200 preguntas de máxima interferencia.", group: "competencia", count: 200, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ["HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 10 },
  { id: "pr-complete", label: "PR39–44 completo", description: "Cobertura integral de los seis capítulos.", group: "cobertura", count: 100, sourceWorks: ["Profetas y Reyes"], chapters: [39, 40, 41, 42, 43, 44], types: [], difficultyBands: ALL_DIFFICULTIES, statuses: ["all"], includeBlind: false, perQuestionSeconds: null },
  { id: "daniel-complete", label: "Daniel 1–12 completo", description: "Mezcla equilibrada de todo Daniel.", group: "cobertura", count: 100, sourceWorks: ["Daniel"], chapters: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], types: [], difficultyBands: ALL_DIFFICULTIES, statuses: ["all"], includeBlind: false, perQuestionSeconds: null },
  { id: "daniel-7-12-intensive", label: "Daniel 7–12 intensivo", description: "Profecías con alta precisión textual.", group: "cobertura", count: 100, sourceWorks: ["Daniel"], chapters: [7, 8, 9, 10, 11, 12], types: [], difficultyBands: ["MEDIUM", "HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 15 },
  { id: "daniel-7-9-11-intensive", label: "Daniel 7–9–11 intensivo", description: "Los tres capítulos de mayor interferencia.", group: "cobertura", count: 100, sourceWorks: ["Daniel"], chapters: [7, 9, 11], types: [], difficultyBands: ["HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 12 },
  { id: "pr43-44-intensive", label: "PR43–44 intensivo", description: "Caída de imperios, tiempo final y Daniel estadista.", group: "cobertura", count: 100, sourceWorks: ["Profetas y Reyes"], chapters: [43, 44], types: [], difficultyBands: ["HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 12 },
  { id: "unseen-only", label: "Solo nunca vistas", description: "Hechos y variantes sin exposición previa.", group: "adaptativo", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ALL_DIFFICULTIES, statuses: ["new"], includeBlind: false, perQuestionSeconds: null, noveltyOnly: true },
  { id: "contextual-traps", label: "Trampas contextuales", description: "Opciones verdaderas fuera del contexto exacto.", group: "precisión", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: ["single_choice"], difficultyBands: ["HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 15, contextualOnly: true },
  { id: "fill-text", label: "Completar texto", description: "Recuperación textual con anclaje suficiente.", group: "precisión", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: ["fill_blank"], difficultyBands: ALL_DIFFICULTIES, statuses: ["all"], includeBlind: false, perQuestionSeconds: 15 },
  { id: "expert-true-false", label: "Verdadero/Falso experto", description: "Un solo detalle alterado bajo presión.", group: "precisión", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: ["true_false"], difficultyBands: ["EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 8 },
  { id: "expert-multiple-choice", label: "Selección múltiple experta", description: "Distractores cercanos y contexto exacto.", group: "precisión", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: ["single_choice"], difficultyBands: ["EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 12 },
  { id: "order-sequence", label: "Orden y secuencia", description: "Cronología, listas y relaciones consecutivas.", group: "precisión", count: 50, sourceWorks: ALL_WORKS, chapters: [], types: ["single_choice"], difficultyBands: ["HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 20 },
  { id: "previous-errors", label: "Errores anteriores", description: "Reintento con otra variante y separación.", group: "adaptativo", count: 50, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ALL_DIFFICULTIES, statuses: ["failed"], includeBlind: false, perQuestionSeconds: null },
  { id: "slow-correct", label: "Correctas lentas", description: "Convierte aciertos dudosos en respuestas rápidas.", group: "adaptativo", count: 50, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ALL_DIFFICULTIES, statuses: ["all"], includeBlind: false, perQuestionSeconds: 12, slowOnly: true },
  { id: "weak-chapters", label: "Capítulos débiles", description: "Se adapta a precisión y tiempo por capítulo.", group: "adaptativo", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ALL_DIFFICULTIES, statuses: ["all"], includeBlind: false, perQuestionSeconds: null },
  { id: "cold-mode", label: "Modo frío", description: "Sin pistas ni retroalimentación hasta terminar.", group: "competencia", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ["HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 12 },
  { id: "speed-mode", label: "Modo velocidad", description: "Decisiones rápidas con cinco segundos.", group: "competencia", count: 50, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ["MEDIUM", "HARD", "EXPERT"], statuses: ["all"], includeBlind: false, perQuestionSeconds: 5 },
  { id: "spaced-review", label: "Repaso espaciado", description: "Prioriza hechos vencidos y mezcla variantes.", group: "adaptativo", count: 50, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ALL_DIFFICULTIES, statuses: ["all"], includeBlind: false, perQuestionSeconds: null },
  { id: "blind-simulation", label: "Simulación ciega", description: "Reserva inédita para medir conocimiento real.", group: "competencia", count: 100, sourceWorks: ALL_WORKS, chapters: [], types: [], difficultyBands: ["HARD", "EXPERT"], statuses: ["new"], includeBlind: true, perQuestionSeconds: 12 },
]

export function getMassiveTrainingMode(id: MassiveTrainingModeId) {
  const mode = MASSIVE_TRAINING_MODES.find((item) => item.id === id)
  if (!mode) throw new Error(`Modo masivo desconocido: ${id}`)
  return mode
}
