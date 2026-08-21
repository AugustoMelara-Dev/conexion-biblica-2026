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

for (const file of NEW_FILES) {
  const data = JSON.parse(fs.readFileSync(path.join(ROOT, file), "utf8"))
  const questions = Array.isArray(data) ? data : data.questions ?? []
  const ids = new Set()
  let dupes = 0
  let missingRef = 0
  let badOptions = 0
  let badCorrect = 0
  let diffMin = 99, diffMax = 0
  const optionShapes = new Set()
  const answerShapes = new Set()
  const refSamples = []
  for (const q of questions) {
    if (ids.has(q.id)) dupes += 1
    ids.add(q.id)
    const ref = String(q.reference ?? q.source_reference ?? "").trim()
    if (!ref) missingRef += 1
    else if (refSamples.length < 3) refSamples.push(ref)
    const d = Number(q.difficulty)
    if (Number.isInteger(d)) { diffMin = Math.min(diffMin, d); diffMax = Math.max(diffMax, d) }
    const opts = q.options
    if (!Array.isArray(opts) || opts.length < 2) badOptions += 1
    else for (const o of opts) optionShapes.add(Object.keys(o).sort().join("+"))
    const ans = q.correctOptionId ?? q.correctAnswer
    if (ans === undefined || ans === null || (Array.isArray(ans) && ans.length === 0)) badCorrect += 1
    else answerShapes.add(JSON.stringify(typeof ans) + ":" + JSON.stringify(ans).slice(0, 60))
    if (opts && Array.isArray(opts)) {
      const found = Array.isArray(ans) ? opts.some((o) => ans.includes(o.id)) : opts.some((o) => o.id === ans)
      if (!found) badCorrect += 1
    }
  }
  console.log("=".repeat(80))
  console.log(file)
  console.log(`  ids únicos: ${ids.size}/${questions.length} (dupes: ${dupes})`)
  console.log(`  sin reference: ${missingRef} | ejemplos: ${refSamples.join(" | ")}`)
  console.log(`  difficulty rango: ${diffMin}-${diffMax}`)
  console.log(`  options mal: ${badOptions} | formas: ${[...optionShapes].join(" ; ")}`)
  console.log(`  correctAnswer mal/ausente: ${badCorrect} | formas: ${[...answerShapes].slice(0, 5).join(" ; ")}`)
}
