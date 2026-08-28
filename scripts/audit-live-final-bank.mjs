import { createHash } from "node:crypto"
import { readFile } from "node:fs/promises"
import { resolve } from "node:path"

const baseUrl = process.env.FINAL_BANK_BASE_URL ?? "https://conexion-biblica-2026.vercel.app"
const publicRoot = resolve("public")
const resources = [
  "banks/final-2026/manifest.json",
  "banks/final-2026/source_inventory.json",
  "banks/final-2026/fact_inventory.json",
  "banks/final-2026/coverage_manifest.json",
  "banks/final-2026/editorial_audit.json",
  "banks/final-2026/review-index.json",
]

const manifest = JSON.parse(
  await readFile(resolve(publicRoot, resources[0]), "utf8"),
)
for (const shard of manifest.shards) resources.push(shard.questions_file)

const failures = []
let totalBytes = 0
for (const resource of resources) {
  const [local, response] = await Promise.all([
    readFile(resolve(publicRoot, resource)),
    fetch(`${baseUrl}/${resource}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(30_000),
    }),
  ])
  if (!response.ok) {
    failures.push(`${resource}:http_${response.status}`)
    continue
  }
  const remote = Buffer.from(await response.arrayBuffer())
  totalBytes += remote.byteLength
  const normalizeEol = (value) => value.toString("utf8").replaceAll("\r\n", "\n")
  const digest = (value) => createHash("sha256").update(value).digest("hex")
  if (digest(normalizeEol(local)) !== digest(normalizeEol(remote)))
    failures.push(`${resource}:content_mismatch`)
}

console.log(JSON.stringify({
  baseUrl,
  resources: resources.length,
  totalBytes,
  failures,
}, null, 2))

if (failures.length) process.exitCode = 1
