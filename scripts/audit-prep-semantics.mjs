import { mkdir, readFile, writeFile } from "node:fs/promises"
import { auditQuestions } from "./lib/semantic-audit.mjs"

const readJson = async (path) => JSON.parse(await readFile(path, "utf8"))
const banks = await Promise.all([readJson("public/banks/v3_daniel.json"), readJson("public/banks/v3_profetas_reyes.json")])
const master = await readJson("Banco_Maestro_CB2026.json")
const report = auditQuestions(banks.flatMap((bank) => bank.questions), master.questions)
await mkdir("reports", { recursive: true })
await writeFile("reports/semantic-audit-500.json", `${JSON.stringify(report, null, 2)}\n`)
const grouped = Object.groupBy(report.findings, (finding) => finding.severity)
const lines = [
  "# Auditoría semántica de las 500 preguntas V3", "",
  `Generado: ${report.generatedAt}`, "",
  `- Preguntas: ${report.summary.questions}`, `- Trazadas al Banco Maestro: ${report.summary.traced}`, `- Integradoras revisadas por reglas propias: ${report.summary.integrative}`, `- Preguntas con al menos un hallazgo: ${report.summary.suspiciousQuestions}`, `- Bloqueadores: ${report.summary.blockers}`, `- Revisiones humanas: ${report.summary.reviews}`, "",
  "> Un hallazgo de revisión es una señal para inspección; no afirma por sí solo que el contenido bíblico sea incorrecto.", "",
]
for (const severity of ["blocker", "review", "warning"]) {
  const items = grouped[severity] ?? []
  lines.push(`## ${severity === "blocker" ? "Bloqueadores" : severity === "review" ? "Revisión recomendada" : "Advertencias"}`, "")
  if (!items.length) lines.push("Ninguno.", "")
  else items.forEach((item) => lines.push(`- **${item.questionId} · ${item.code}** — ${item.message} (${item.source ?? "sin referencia"})`))
  lines.push("")
}
await writeFile("reports/semantic-audit-500.md", `${lines.join("\n")}\n`)
console.log(JSON.stringify(report.summary, null, 2))
if (report.summary.blockers > 0) process.exitCode = 1

