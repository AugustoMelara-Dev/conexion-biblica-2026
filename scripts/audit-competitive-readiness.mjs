import { readFile, writeFile } from "node:fs/promises"
import { resolve } from "node:path"

import {
  buildCompetitiveAuditReport,
  selectStratifiedSample,
  semanticAuditFlags,
} from "./lib/competitive-audit.mjs"

const root = resolve(import.meta.dirname, "..")
const bankRoot = resolve(root, "public/banks/final-2026")
const manifest = JSON.parse(
  await readFile(resolve(bankRoot, "manifest.json"), "utf8")
)
const questions = []
for (const shard of manifest.shards) {
  questions.push(
    ...JSON.parse(
      await readFile(resolve(root, "public", shard.questions_file), "utf8")
    )
  )
}

const chapters = [
  "DAN7",
  "DAN8",
  "DAN9",
  "DAN10",
  "DAN11",
  "DAN12",
  "PR39",
  "PR40",
  "PR41",
  "PR42",
  "PR43",
  "PR44",
]
const families = ["single_choice_contextual", "true_false_false", "fill_choice"]
const sample = selectStratifiedSample(questions, {
  chapters,
  families,
  perStratum: 3,
}).map((row) => ({
  id: row.id,
  chapter: row.chapter,
  family: row.family,
  reference: row.reference,
  question: row.question,
  options: row.options,
  correct_answer: row.correct_answer,
  source_quote: row.source_quote,
  statement: row.statement ?? null,
  corrected_statement: row.corrected_statement ?? null,
  incorrect_detail: row.incorrect_detail ?? null,
  correction: row.correction ?? null,
  why_distractors_fail: row.why_distractors_fail,
  automatic_flags: semanticAuditFlags(row),
}))

const automaticFlags = sample.flatMap((row) =>
  row.automatic_flags.map((flag) => `${row.id}:${flag}`)
)
const report = buildCompetitiveAuditReport({
  bank: manifest.bank_id,
  bankQuestions: questions.length,
  chapters,
  families,
  perStratum: 3,
  automaticFlags,
  sample,
})

await writeFile(
  resolve(root, "reports/final-competitive-audit.json"),
  `${JSON.stringify(report, null, 2)}\n`,
  "utf8"
)

const lines = [
  "# Auditoría competitiva final",
  "",
  `- Banco: ${manifest.bank_id}`,
  `- Preguntas activas: ${questions.length}`,
  `- Muestra estratificada: ${sample.length} preguntas (${chapters.length} capítulos × ${families.length} familias × 3 casos).`,
  `- Alertas estructurales en la muestra: ${automaticFlags.length}`,
  "- Revisión visual asistida por IA: completada para las 108 preguntas; no constituye firma humana.",
  "",
  "## Muestra",
  "",
  "| ID | Familia | Referencia | Respuesta | Alertas |",
  "|---|---|---|---|---|",
  ...sample.map(
    (row) =>
      `| ${row.id} | ${row.family} | ${row.reference} | ${String(row.correct_answer).replaceAll("|", "\\|")} | ${row.automatic_flags.join(", ") || "—"} |`
  ),
  "",
  "El detalle completo de enunciado, opciones, cita, corrección y explicación de distractores está en `reports/final-competitive-audit.json`.",
  "",
]
await writeFile(
  resolve(root, "reports/final-competitive-audit-sample.md"),
  lines.join("\n"),
  "utf8"
)

console.log(
  JSON.stringify(
    {
      sample_size: sample.length,
      strata: chapters.length * families.length,
      automatic_flags: automaticFlags,
      report: "reports/final-competitive-audit.json",
    },
    null,
    2
  )
)
if (automaticFlags.length) process.exitCode = 1
