import fs from "node:fs"
import path from "node:path"

const ROOT = process.cwd()
const NEW_FILES = [
  "conexion_biblica_2026_daniel_1_replica_campeonato_v2.json",
  "conexion_biblica_2026_daniel_4_replica_campeonato_v2.json",
  "daniel2f.json",
  "daniel3fff.json",
  "daniel6f.json",
  "daniel9.json",
  "daniel_10_conexion_biblica_2026_replca_conexion_60.json",
  "Daniel_11_Conexion_Biblica_2026_Prompt_v2_120_preguntas (1).json",
  "daniel_12_replica_conexion_60.json",
  "daniel_2_conexion_biblica_2026_banco_v4_150.json",
  "daniel_5_conexion_2026_banco_100.json",
  "daniel_7_conexion_biblica_2026_banco_100.json",
  "daniel_8_conexion_biblica_2026_banco_100.json",
]

const summary = []
for (const file of NEW_FILES) {
  const full = path.join(ROOT, file)
  const text = fs.readFileSync(full, "utf8")
  const data = JSON.parse(text)
  const questions = Array.isArray(data) ? data : data.questions ?? []
  const byType = new Map()
  const fields = new Map()
  const refs = new Set()
  let mojibake = 0
  for (const q of questions) {
    byType.set(q.type, (byType.get(q.type) ?? 0) + 1)
    for (const key of Object.keys(q)) fields.set(key, (fields.get(key) ?? 0) + 1)
    if (q.reference) refs.add(String(q.reference))
    const sample = `${q.prompt ?? q.question ?? ""}`
    if (/[\u00c2\u00c3][\u0080-\u00bf]/.test(sample)) mojibake += 1
  }
  const chapters = [...refs].map((r) => {
    const m = /^([A-Za-zÁÉÍÓÚáéíóúÑñ\s.]+?)\s*(\d+)\s*:\s*\d+/.exec(r)
    return m ? `${m[1].trim()} ${m[2]}` : `?(${r})`
  })
  summary.push({
    file,
    count: questions.length,
    types: Object.fromEntries(byType),
    chapters: [...new Set(chapters)],
    mojibake,
    answerFields: {
      correctOptionId: fields.get("correctOptionId") ?? 0,
      correctAnswer: fields.get("correctAnswer") ?? 0,
      correctMatches: fields.get("correctMatches") ?? 0,
    },
    fields: Object.fromEntries(fields),
  })
}

for (const item of summary) {
  console.log("=".repeat(80))
  console.log(item.file)
  console.log(`  preguntas: ${item.count} | mojibake: ${item.mojibake}`)
  console.log(`  tipos: ${JSON.stringify(item.types)}`)
  console.log(`  capítulos: ${item.chapters.join(", ")}`)
  console.log(`  campos de respuesta: ${JSON.stringify(item.answerFields)}`)
  console.log(`  campos: ${Object.keys(item.fields).join(", ")}`)
}
