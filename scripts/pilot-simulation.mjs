import { mkdir, readFile, writeFile } from "node:fs/promises"
import { runPilot } from "./lib/pilot.mjs"

const readJson = async (path) => JSON.parse(await readFile(path, "utf8"))
const banks = await Promise.all([readJson("public/banks/v3_daniel.json"), readJson("public/banks/v3_profetas_reyes.json")])
const report = runPilot(banks.flatMap((bank) => bank.questions), { rounds: 100, count: 50, seed: 2026 })
await mkdir("reports", { recursive: true })
await writeFile("reports/simulation-pilot.json", `${JSON.stringify(report, null, 2)}\n`)
const mix = report.summary.averageDifficultyMix
const lines = [
  "# Simulacro piloto V3", "", `Generado: ${report.generatedAt}`, "",
  "## Resultado", "",
  `- Banco: ${report.summary.poolSize} preguntas`, `- Rondas simuladas: ${report.summary.rounds}`, `- Rondas completas: ${report.summary.completeRounds}`, `- Rondas con duplicados internos: ${report.summary.roundsWithDuplicates}`, `- Familias distintas por ronda (promedio): ${report.summary.averageFamilies}`, `- Palabras visibles por pregunta (promedio): ${report.summary.averageWords}`, `- Mezcla promedio: ${mix.EXPERT} EXPERT, ${mix.HARD} HARD, ${mix.MEDIUM} MEDIUM, ${mix.BASIC} BASIC/UNRATED`, "",
  "## Calibración aplicada", "",
  `- ${report.preset.count} preguntas`, `- ${report.preset.perQuestionSeconds} segundos por pregunta`, `- ${report.preset.totalSeconds / 60} minutos totales`, "- Puntuación: porcentaje de respuestas correctas, de 0 a 100", "- El tiempo se informa aparte y no añade ni resta puntos.", "",
  "> Esta es una calibración piloto local y configurable; no se presenta como reglamento oficial del concurso.", "",
]
await writeFile("reports/simulation-pilot.md", `${lines.join("\n")}\n`)
console.log(JSON.stringify(report.summary, null, 2))

