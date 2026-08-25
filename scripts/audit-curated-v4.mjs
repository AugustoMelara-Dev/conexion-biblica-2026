import { readFile } from "node:fs/promises"
import { resolve } from "node:path"
import { fileURLToPath } from "node:url"
import {
  auditCuratedV4,
  buildCuratedV4,
  fingerprintText,
  renderAuditMarkdown,
  writePayloadsAtomically,
} from "./build-curated-v4.mjs"

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)))

const readJson = async (path) => JSON.parse(await readFile(path, "utf8"))

export async function auditCuratedV4Files({ root = ROOT } = {}) {
  const rawMaster = await readFile(resolve(root, "Banco_Maestro_CB2026.json"), "utf8")
  const master = JSON.parse(rawMaster)
  const banks = {
    daniel: await readJson(resolve(root, "public/banks/v4_daniel.json")),
    prophets: await readJson(resolve(root, "public/banks/v4_profetas_reyes.json")),
  }
  const expected = buildCuratedV4(master, { masterFingerprint: fingerprintText(rawMaster) })
  const crossAudit = auditCuratedV4(banks, master, expected.banks)
  const audit = {
    ...expected.audit,
    generatedAt: new Date().toISOString(),
    masterFingerprint: fingerprintText(rawMaster),
    summary: { ...expected.audit.summary, blockers: crossAudit.summary.blockers },
    findings: crossAudit.findings,
  }
  if (audit.summary.blockers > 0) {
    const details = crossAudit.findings.map((finding) => `${finding.code}: ${finding.message}`).join(" | ")
    throw new Error(`La auditoría V4 encontró ${audit.summary.blockers} bloqueadores: ${details}`)
  }
  const reportPayloads = [
    { target: resolve(root, "reports/curated-v4-audit.json"), value: audit },
    { target: resolve(root, "reports/curated-v4-audit.md"), value: renderAuditMarkdown(audit) },
  ]
  await writePayloadsAtomically(reportPayloads)
  return audit
}

async function main() {
  const audit = await auditCuratedV4Files()
  console.log(JSON.stringify(audit.summary, null, 2))
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error.stack ?? error.message)
    process.exitCode = 1
  })
}
