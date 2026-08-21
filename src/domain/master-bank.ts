import type {
  Bank,
  DifficultyBand,
  Question,
  QuestionOption,
  QuestionType,
  SourceWork,
  ValidationError,
} from "@/domain/types"

export type MasterQuestionRaw = {
  QUESTION_ID: string
  origen: "HISTORICAL" | "GENERATED"
  material: "DANIEL" | "PR"
  capitulo: string | number
  tipo: string
  dificultad: "MEDIUM" | "HARD" | "EXPERT" | "HISTORICAL_UNRATED"
  pregunta: string
  A: string
  B: string
  C: string
  D: string
  respuesta_correcta: string
  fuente: string
  FULL_FACT_IDS: string[]
  PARTIAL_FACT_IDS: string[]
  INCIDENTAL_FACT_IDS: string[]
  habilidad: string
  riesgo_objetivo: string
  explicacion: string
  estado_QC: string
  variant_of: string
  generation_level: string
  duplicate_group: string
  HIST_IDS: string[]
  historical_status: string
  fact_support: string
  answer_span: string
  answer_category: string
  [key: string]: unknown
}

type MasterDocument = { metadata: Record<string, unknown>; questions: MasterQuestionRaw[] }

export type MasterBankCounts = {
  total: number
  daniel: number
  prophetsAndKings: number
  historical: number
  generated: number
  uniqueIds: number
  correctedHistorical: number
}

export type MasterValidationResult = {
  valid: boolean
  errors: ValidationError[]
  counts: MasterBankCounts
}

const expectedCounts: MasterBankCounts = {
  total: 3558,
  daniel: 2211,
  prophetsAndKings: 1347,
  historical: 888,
  generated: 2670,
  uniqueIds: 3558,
  correctedHistorical: 46,
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function asMasterDocument(value: unknown): MasterDocument | null {
  if (!isRecord(value) || !isRecord(value.metadata) || !Array.isArray(value.questions)) return null
  return value as unknown as MasterDocument
}

function countMasterQuestions(questions: MasterQuestionRaw[]): MasterBankCounts {
  return {
    total: questions.length,
    daniel: questions.filter((item) => item.material === "DANIEL").length,
    prophetsAndKings: questions.filter((item) => item.material === "PR").length,
    historical: questions.filter((item) => item.origen === "HISTORICAL").length,
    generated: questions.filter((item) => item.origen === "GENERATED").length,
    uniqueIds: new Set(questions.map((item) => item.QUESTION_ID)).size,
    correctedHistorical: questions.filter((item) => item.historical_status === "CORRECTED").length,
  }
}

export function validateMasterBank(value: unknown): MasterValidationResult {
  const document = asMasterDocument(value)
  if (!document) {
    return {
      valid: false,
      counts: { total: 0, daniel: 0, prophetsAndKings: 0, historical: 0, generated: 0, uniqueIds: 0, correctedHistorical: 0 },
      errors: [{ code: "INVALID_MASTER_DOCUMENT", path: "$", message: "El Banco Maestro requiere metadata y questions." }],
    }
  }

  const errors: ValidationError[] = []
  document.questions.forEach((item, index) => {
    const path = `$.questions[${index}]`
    if (!isRecord(item)) {
      errors.push({ code: "INVALID_MASTER_QUESTION", path, message: "La pregunta debe ser un objeto." })
      return
    }
    for (const field of ["QUESTION_ID", "material", "tipo", "dificultad", "pregunta", "respuesta_correcta", "fuente"] as const) {
      if (typeof item[field] !== "string" || !item[field].trim()) {
        errors.push({ code: "MISSING_MASTER_FIELD", path: `${path}.${field}`, message: `${field} es obligatorio.`, questionId: item.QUESTION_ID })
      }
    }
    for (const field of ["FULL_FACT_IDS", "PARTIAL_FACT_IDS", "INCIDENTAL_FACT_IDS", "HIST_IDS"] as const) {
      if (!Array.isArray(item[field])) errors.push({ code: "INVALID_MASTER_ARRAY", path: `${path}.${field}`, message: `${field} debe ser un arreglo.`, questionId: item.QUESTION_ID })
    }
  })

  const counts = countMasterQuestions(document.questions)
  for (const [field, expected] of Object.entries(expectedCounts) as [keyof MasterBankCounts, number][]) {
    if (counts[field] !== expected) errors.push({ code: "MASTER_COUNT_MISMATCH", path: `$.counts.${field}`, message: `Se esperaban ${expected}; se encontraron ${counts[field]}.` })
  }
  return { valid: errors.length === 0, errors, counts }
}

function fnv1a(value: string) {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0).toString(16)
}

function stripOptionPrefix(value: string) {
  return value.trim().replace(/^[A-D]\)\s*/i, "")
}

function comparable(value: string) {
  return stripOptionPrefix(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLocaleLowerCase("es")
}

function mapType(value: string): QuestionType {
  const normalized = value.replace(/\s+/g, " ").trim().toLocaleUpperCase("es")
  if (normalized.startsWith("VERDADERO")) return "true_false"
  if (normalized.startsWith("COMPLET") || normalized === "RESPUESTA CORTA") return "fill_blank"
  return "single_choice"
}

function mapDifficulty(value: MasterQuestionRaw["dificultad"]): { numeric: Question["difficulty"]; band: DifficultyBand } {
  if (value === "EXPERT") return { numeric: 5, band: "EXPERT" }
  if (value === "HARD") return { numeric: 4, band: "HARD" }
  if (value === "HISTORICAL_UNRATED") return { numeric: 3, band: "UNRATED" }
  return { numeric: 3, band: "MEDIUM" }
}

function createOptions(item: MasterQuestionRaw, type: QuestionType): QuestionOption[] {
  const values = ["A", "B", "C", "D"] as const
  const options = values
    .map((id) => ({ id, text: stripOptionPrefix(String(item[id] ?? "")) }))
    .filter((option) => option.text.length > 0)
  if (type === "true_false" && options.length === 0) {
    return [{ id: "TRUE", text: "Verdadero" }, { id: "FALSE", text: "Falso" }]
  }
  return options
}

function correctOptionId(item: MasterQuestionRaw, options: QuestionOption[]) {
  const answer = comparable(item.respuesta_correcta)
  return options.find((option) => comparable(option.text) === answer)?.id
    ?? (answer === "verdadero" ? "TRUE" : answer === "falso" ? "FALSE" : undefined)
}

function adaptQuestion(item: MasterQuestionRaw): Question {
  const type = mapType(item.tipo)
  const difficulty = mapDifficulty(item.dificultad)
  const options = createOptions(item, type)
  const optionId = correctOptionId(item, options)
  const requiresCanonicalText = item.historical_status === "CORRECTED" || type === "fill_blank" || !optionId
  const factKeys = [...item.FULL_FACT_IDS]
  const work: SourceWork = item.material === "DANIEL" ? "Daniel" : "Profetas y Reyes"
  return {
    id: item.QUESTION_ID,
    bankId: "master-v2",
    bankProfileId: "master-v2",
    type,
    difficulty: difficulty.numeric,
    originalDifficulty: item.dificultad,
    difficultyBand: difficulty.band,
    answerMode: requiresCanonicalText ? "canonical_text" : "option_id",
    source: { work, version: "CB2026 Master", chapter: Number(item.capitulo), reference: item.fuente },
    tags: [item.origen, item.habilidad, item.riesgo_objetivo].filter(Boolean),
    factKey: factKeys[0] ?? item.duplicate_group ?? item.QUESTION_ID,
    factKeys,
    question: item.pregunta,
    options,
    correctAnswer: requiresCanonicalText ? [] : [optionId],
    correctAnswerText: item.respuesta_correcta,
    explanation: item.explicacion,
    verified: item.estado_QC.length > 0,
    metadata: structuredClone(item),
  }
}

export function adaptMasterBank(value: unknown, importedAt = Date.now()): Bank {
  const validation = validateMasterBank(value)
  if (!validation.valid) throw new Error(validation.errors.map((error) => `${error.path}: ${error.message}`).join("\n"))
  const document = asMasterDocument(value)!
  return {
    bankId: "master-v2",
    bankProfileId: "master-v2",
    name: "V2 — Banco Maestro",
    sourceWork: "Daniel",
    sourceVersion: "CB2026-FASE4-CIERRE",
    schemaVersion: "2.0",
    importedAt,
    fingerprint: fnv1a(JSON.stringify(value)),
    sourceFileName: "Banco_Maestro_CB2026.json",
    raw: { metadata: structuredClone(document.metadata) },
    questions: document.questions.map(adaptQuestion),
  }
}
