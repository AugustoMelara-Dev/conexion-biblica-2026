import { mkdir, readFile, writeFile } from "node:fs/promises"
import { resolve } from "node:path"

import {
  buildExhaustiveReviewQueue,
  buildPublicReviewIndex,
} from "./lib/competitive-audit.mjs"

const root = resolve(import.meta.dirname, "..")
const bankRoot = resolve(root, "public/banks/final-2026")
const reportRoot = resolve(root, "reports")
const decisionsPath = resolve(reportRoot, "final-human-review-decisions.json")
const ledgerPath = resolve(reportRoot, "final-exhaustive-audit-ledger.json")
const packetPath = resolve(reportRoot, "final-exhaustive-review-packet.json")
const summaryPath = resolve(reportRoot, "final-exhaustive-audit.md")
const publicIndexPath = resolve(bankRoot, "review-index.json")

async function readJson(path, fallback) {
  try {
    return JSON.parse(await readFile(path, "utf8"))
  } catch (error) {
    if (error?.code === "ENOENT") return fallback
    throw error
  }
}

const manifest = await readJson(resolve(bankRoot, "manifest.json"))
const questions = []
for (const shard of manifest.shards) {
  questions.push(
    ...(await readJson(resolve(root, "public", shard.questions_file)))
  )
}
if (questions.length !== manifest.gold_questions)
  throw new Error(
    `El manifiesto declara ${manifest.gold_questions}, pero se cargaron ${questions.length}.`
  )

const decisions = await readJson(decisionsPath, [])
if (!Array.isArray(decisions))
  throw new Error("final-human-review-decisions.json debe ser un arreglo.")
const decisionsById = new Map()
for (const decision of decisions) {
  if (!decision?.id || decisionsById.has(decision.id))
    throw new Error(`Decisión inválida o duplicada: ${decision?.id}`)
  if (!['approved', 'corrected', 'rejected'].includes(decision.disposition))
    throw new Error(`Disposición inválida para ${decision.id}.`)
  if (!decision.reviewer || !decision.reviewed_at || !decision.content_sha256)
    throw new Error(`Falta trazabilidad editorial en ${decision.id}.`)
  decisionsById.set(decision.id, decision)
}

const queue = buildExhaustiveReviewQueue(questions).map((row) => {
  const decision = decisionsById.get(row.id)
  if (!decision) return row
  if (decision.content_sha256 !== row.content_sha256)
    throw new Error(
      `La pregunta ${row.id} cambió después de la revisión; debe revisarse de nuevo.`
    )
  return {
    ...row,
    review_status: "reviewed",
    reviewer: decision.reviewer,
    reviewed_at: decision.reviewed_at,
    disposition: decision.disposition,
    notes: decision.notes ?? null,
  }
})

const questionById = new Map(questions.map((row) => [row.id, row]))
const attention = queue.filter(
  (row) => row.automatic_status === "requires_attention"
)
const pending = queue.filter((row) => row.review_status === "pending_human")
const highRiskPending = pending
  .filter((row) => row.risk_score > 0)
  .slice(0, 600)
  .map((row) => ({ ...row, question_record: questionById.get(row.id) }))
const familyCounts = Object.fromEntries(
  [...new Set(queue.map((row) => row.family))]
    .sort()
    .map((family) => [family, queue.filter((row) => row.family === family).length])
)
const flagCounts = {}
for (const row of queue)
  for (const flag of row.automatic_flags)
    flagCounts[flag] = (flagCounts[flag] ?? 0) + 1

const ledger = {
  schema_version: "1.0",
  bank_id: manifest.bank_id,
  bank_questions: questions.length,
  source_sha256: manifest.source_sha256,
  generated_at: new Date().toISOString(),
  counts: {
    reviewed: queue.length - pending.length,
    pending_human: pending.length,
    automatic_attention: attention.length,
    automatic_passed: queue.length - attention.length,
  },
  family_counts: familyCounts,
  automatic_flag_counts: flagCounts,
  entries: queue,
}

await mkdir(reportRoot, { recursive: true })
await writeFile(ledgerPath, `${JSON.stringify(ledger, null, 2)}\n`, "utf8")
await writeFile(
  packetPath,
  `${JSON.stringify(
    {
      bank_id: manifest.bank_id,
      purpose:
        "Paquete editorial priorizado. Aprobar requiere contrastar pregunta, respuesta, distractores y cita fuente.",
      total_pending: pending.length,
      included: highRiskPending.length,
      entries: highRiskPending,
    },
    null,
    2
  )}\n`,
  "utf8"
)
await writeFile(
  publicIndexPath,
  `${JSON.stringify({
    schema_version: "1.0",
    bank_id: manifest.bank_id,
    bank_questions: questions.length,
    source_sha256: manifest.source_sha256,
    entries: buildPublicReviewIndex(queue, manifest.shards),
  })}\n`,
  "utf8"
)

const summary = [
  "# Registro exhaustivo de auditoría editorial",
  "",
  `- Banco: ${manifest.bank_id}`,
  `- Variantes enumeradas: ${queue.length} de ${manifest.gold_questions}`,
  `- Revisión editorial trazable completada: ${queue.length - pending.length}`,
  `- Pendientes de revisión editorial: ${pending.length}`,
  `- Pasaron controles automáticos: ${queue.length - attention.length}`,
  `- Requieren atención automática: ${attention.length}`,
  "",
  "## Familias",
  "",
  ...Object.entries(familyCounts).map(([family, count]) => `- ${family}: ${count}`),
  "",
  "## Alertas automáticas",
  "",
  ...(Object.keys(flagCounts).length
    ? Object.entries(flagCounts)
        .sort((left, right) => right[1] - left[1])
        .map(([flag, count]) => `- ${flag}: ${count}`)
    : ["- Ninguna."]),
  "",
  "El estado `passed` solo significa que una regla automática no encontró un defecto. No equivale a revisión humana.",
  "Las decisiones editoriales se registran por ID y huella SHA-256 en `reports/final-human-review-decisions.json`; si cambia el contenido, la auditoría falla y exige revisar de nuevo.",
  "",
]
await writeFile(summaryPath, summary.join("\n"), "utf8")

console.log(
  JSON.stringify(
    {
      bank_questions: questions.length,
      reviewed: queue.length - pending.length,
      pending_human: pending.length,
      automatic_attention: attention.length,
      automatic_flag_counts: flagCounts,
      review_packet: highRiskPending.length,
    },
    null,
    2
  )
)
if (attention.length) process.exitCode = 1
