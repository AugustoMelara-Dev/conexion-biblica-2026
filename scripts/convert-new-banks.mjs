import fs from "node:fs"
import path from "node:path"

const ROOT = process.cwd()
const OUT_DIR = path.join(ROOT, "public", "banks")

const SOURCES = [
  { file: "conexion_biblica_2026_daniel_1_replica_campeonato_v2.json", out: "daniel_1_replica_campeonato_v2.json", chapterFallback: 1 },
  { file: "conexion_biblica_2026_daniel_4_replica_campeonato_v2.json", out: "daniel_4_replica_campeonato_v2.json", chapterFallback: 4 },
  { file: "daniel2f.json", out: "daniel2f.json", chapterFallback: 2 },
  { file: "daniel3fff.json", out: "daniel3fff.json", chapterFallback: 3 },
  { file: "daniel6f.json", out: "daniel6f.json", chapterFallback: 6 },
  { file: "daniel9.json", out: "daniel9.json", chapterFallback: 9 },
  { file: "daniel_10_conexion_biblica_2026_replca_conexion_60.json", out: "daniel_10_replica_conexion_60.json", chapterFallback: 10 },
  { file: "Daniel_11_Conexion_Biblica_2026_Prompt_v2_120_preguntas (1).json", out: "daniel_11_prompt_v2_120_preguntas.json", chapterFallback: 11 },
  { file: "daniel_12_replica_conexion_60.json", out: "daniel_12_replica_conexion_60.json", chapterFallback: 12 },
  { file: "daniel_2_conexion_biblica_2026_banco_v4_150.json", out: "daniel_2_banco_v4_150.json", chapterFallback: 2 },
  { file: "daniel_5_conexion_2026_banco_100.json", out: "daniel_5_banco_100.json", chapterFallback: 5 },
  { file: "daniel_7_conexion_biblica_2026_banco_100.json", out: "daniel_7_banco_100.json", chapterFallback: 7 },
  { file: "daniel_8_conexion_biblica_2026_banco_100.json", out: "daniel_8_banco_100.json", chapterFallback: 8 },
]

function chapterFromReference(reference) {
  const match = /(?:Daniel|Profetas\s*y\s*Reyes)\s+(\d+)/i.exec(String(reference ?? ""))
  return match ? Number(match[1]) : null
}

function asArray(value) {
  if (Array.isArray(value)) return value.map(String)
  if (value === undefined || value === null || value === "") return []
  return [String(value)]
}

const report = []

for (const source of SOURCES) {
  const raw = JSON.parse(fs.readFileSync(path.join(ROOT, source.file), "utf8"))
  const rawQuestions = Array.isArray(raw) ? raw : raw.questions ?? []
  const warnings = []

  const questions = rawQuestions.map((q, index) => {
    const reference = String(q.reference ?? q.supportingReferences?.[0] ?? "").trim()
    const chapter = chapterFromReference(reference) ?? source.chapterFallback
    const finalReference = reference || `Daniel ${chapter}`
    const options = (Array.isArray(q.options) ? q.options : []).map((o) => ({
      id: String(o.id ?? o.optionId ?? "").trim(),
      text: String(o.text ?? "").trim(),
    })).filter((o) => o.id && o.text)

    const rawAnswer = q.correctOptionId ?? q.correctAnswer
    const correctAnswer = asArray(rawAnswer).map(String).filter(Boolean)
    const optionIds = new Set(options.map((o) => o.id))
    if (correctAnswer.length === 0) warnings.push(`${q.id}: sin respuesta correcta`)
    else if (!correctAnswer.every((id) => optionIds.has(id))) warnings.push(`${q.id}: respuesta no apunta a opción existente`)

    const prompt = String(q.question ?? q.prompt ?? "").trim()
    if (!prompt) warnings.push(`${q.id}: sin texto de pregunta`)

    const questionClass = Array.isArray(q.questionClass) ? q.questionClass.map(String) : q.questionClass ? [String(q.questionClass)] : []
    const converted = {
      id: String(q.id),
      type: "single_choice",
      difficulty: Math.min(5, Math.max(1, Number(q.difficulty) || 1)),
      source: { work: "Daniel", version: "RVR95", chapter, reference: finalReference },
      tags: questionClass,
      factKey: String(q.id),
      question: prompt,
      options,
      correctAnswer,
    }
    if (q.explanation && String(q.explanation).trim()) converted.explanation = String(q.explanation).trim()
    if (typeof q.verified === "boolean") converted.verified = q.verified
    if (q.trapReason && String(q.trapReason).trim()) converted.trapReason = String(q.trapReason).trim()
    void index
    return converted
  })

  const chapters = [...new Set(questions.map((q) => q.source.chapter))]
  const bank = {
    schemaVersion: "1.0",
    bank: {
      sourceWork: "Daniel",
      sourceVersion: "RVR95",
      chapter: chapters.length === 1 ? chapters[0] : source.chapterFallback,
      chapters,
      originalFile: source.file,
    },
    questions,
  }

  const outPath = path.join(OUT_DIR, source.out)
  fs.writeFileSync(outPath, JSON.stringify(bank, null, 2) + "\n", "utf8")
  report.push({ out: source.out, count: questions.length, chapters, warnings })
}

for (const item of report) {
  console.log(`${item.out}: ${item.count} preguntas, capítulos ${item.chapters.join(",")}`)
  for (const warning of item.warnings.slice(0, 5)) console.log(`   ⚠ ${warning}`)
  if (item.warnings.length > 5) console.log(`   … y ${item.warnings.length - 5} más`)
}
