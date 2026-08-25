import { readFileSync } from "node:fs"
import { join } from "node:path"

const files = ["v3_daniel.json", "v3_profetas_reyes.json"]
const questions = files.flatMap((file) => JSON.parse(readFileSync(join(process.cwd(), "public", "banks", file), "utf8")).questions)
const errors = []
const ids = new Set()
const prompts = new Set()
const counts = new Map()

for (const question of questions) {
  if (ids.has(question.id)) errors.push(`ID duplicado: ${question.id}`)
  ids.add(question.id)
  const prompt = question.question.trim().toLocaleLowerCase("es")
  if (prompts.has(prompt)) errors.push(`Pregunta duplicada: ${question.id}`)
  prompts.add(prompt)
  for (const field of ["factKey", "question", "explanation", "trapReason", "memoryCue"]) {
    if (!String(question[field] ?? "").trim()) errors.push(`${question.id}: falta ${field}`)
  }
  const optionIds = new Set(question.options?.map((option) => option.id))
  if (optionIds.size !== question.options?.length) errors.push(`${question.id}: opciones duplicadas`)
  if (!question.correctAnswer?.length || question.correctAnswer.some((answer) => !optionIds.has(answer))) errors.push(`${question.id}: respuesta inválida`)
  if (!question.integrative) {
    const key = `${question.source.work}:${question.source.chapter}`
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
}

if (questions.length !== 500) errors.push(`Total esperado 500; recibido ${questions.length}`)
if (questions.filter((question) => question.integrative).length !== 2) errors.push("Se requieren 2 integradoras")
for (let chapter = 1; chapter <= 12; chapter += 1) if (counts.get(`Daniel:${chapter}`) !== 28) errors.push(`Daniel ${chapter}: ${counts.get(`Daniel:${chapter}`) ?? 0}/28`)
for (let chapter = 39; chapter <= 44; chapter += 1) if (counts.get(`Profetas y Reyes:${chapter}`) !== 27) errors.push(`PR ${chapter}: ${counts.get(`Profetas y Reyes:${chapter}`) ?? 0}/27`)
const familyCounts = new Map()
questions.forEach((question) => familyCounts.set(question.factKey, (familyCounts.get(question.factKey) ?? 0) + 1))
if ([...familyCounts.values()].filter((count) => count > 1).length < 100) errors.push("Menos de 100 familias tienen variantes")

if (errors.length) {
  console.error(errors.join("\n"))
  process.exitCode = 1
} else {
  console.log(`Banco V3 válido: ${questions.length} preguntas, ${familyCounts.size} familias, ${[...familyCounts.values()].filter((count) => count > 1).length} con variantes.`)
}
