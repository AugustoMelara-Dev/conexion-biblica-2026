import { createHash } from "node:crypto"
import { readFile, readdir } from "node:fs/promises"
import { resolve, relative, sep } from "node:path"
import { fileURLToPath } from "node:url"

const SCHEMA_VERSION = "10.0"
const BANK_ID = "BANCO_UNICO_CONEXION_BIBLICA_2026"
const BANK_ROOT = "banks/final-2026"
const MANIFEST_PATH = `${BANK_ROOT}/manifest.json`
const REVIEW_INDEX_PATH = `${BANK_ROOT}/review-index.json`
const V18_PACKAGES_PATH = `${BANK_ROOT}/packages-v18.json`
const BLIND_CONTRACT = "private-blind-artifact-v1"
const BLIND_ARTIFACT_ID = "competitive-v11-blind"
const BUILD_DESCRIPTOR_CONTRACT = "competitive-v11-emitted-descriptors-v1"
const BLIND_POOLS = ["A", "B", "emergency"]
const BLIND_FAMILIES = ["selection", "fill_choice", "true_false"]
export const RELEASE_BLIND_REQUIREMENTS = {
  A: { fact_count: 100, families: { selection: 45, fill_choice: 30, true_false: 25 } },
  B: { fact_count: 100, families: { selection: 45, fill_choice: 30, true_false: 25 } },
  emergency: { fact_count: 50, families: { selection: 23, fill_choice: 15, true_false: 12 } },
}
const EXPECTED_UNITS = [
  ...Array.from({ length: 12 }, (_, index) => `DAN${index + 1}`),
  ...Array.from({ length: 6 }, (_, index) => `PR${index + 39}`),
]
const PUBLIC_INTEGER_FIELDS = [
  "unique_facts",
  "gold_questions",
  "central_question_count",
  "presentation_variant_count",
  "training_fact_count",
  "training_presentation_count",
  "blind_fact_count",
  "blind_presentation_count",
  "total_fact_count",
  "total_presentation_count",
  "total_central_question_count",
  "total_presentation_variant_count",
]
const HASH_PATTERN = /^[a-f0-9]{64}$/

const isRecord = (value) => value !== null && typeof value === "object" && !Array.isArray(value)
const isInteger = (value) => Number.isInteger(value) && value >= 0
const sha256 = (value) => createHash("sha256").update(value).digest("hex")
const sortedEntries = (record) => Object.entries(record).sort(([left], [right]) => left.localeCompare(right))
const normalizedCounts = (record) => ({ selection: 0, fill_choice: 0, true_false: 0, ...record })
const sameCounts = (actual, expected) => (
  isRecord(actual)
  && isRecord(expected)
  && JSON.stringify(sortedEntries(normalizedCounts(actual))) === JSON.stringify(sortedEntries(normalizedCounts(expected)))
)

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`
  if (isRecord(value)) {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`
  }
  return JSON.stringify(value)
}

function emittedRowHash(row) {
  return sha256(Buffer.from(canonicalJson(Object.fromEntries(
    Object.entries(row).filter(([key]) => key !== "row_content_sha256"),
  )), "utf8"))
}

function artifactBuildDescriptor(publicManifest, privateManifest) {
  const publicCountKeys = [
    "unique_facts",
    "gold_questions",
    "central_question_count",
    "presentation_variant_count",
    "training_fact_count",
    "training_presentation_count",
    "total_fact_count",
    "total_presentation_count",
    "total_central_question_count",
    "total_presentation_variant_count",
    "blind_fact_count",
    "blind_presentation_count",
  ]
  return {
    contract: BUILD_DESCRIPTOR_CONTRACT,
    schema_version: publicManifest.schema_version,
    bank_id: publicManifest.bank_id,
    artifact_revision: publicManifest.blind_delivery.artifact_revision,
    public: {
      counts: Object.fromEntries(publicCountKeys.map((key) => [key, publicManifest[key]])),
      families: publicManifest.families,
      total_families: publicManifest.total_families,
      blind_pools: publicManifest.blind_pools,
      review_index: publicManifest.review_index,
      shards: publicManifest.shards,
    },
    private: {
      contract: privateManifest.contract,
      artifact_id: privateManifest.artifact_id,
      artifact_revision: privateManifest.artifact_revision,
      schema_version: privateManifest.schema_version,
      bank_id: privateManifest.bank_id,
      counts: Object.fromEntries([
        "total_fact_count",
        "total_presentation_count",
        "central_question_count",
        "presentation_variant_count",
      ].map((key) => [key, privateManifest[key]])),
      families: privateManifest.families,
      review_index: privateManifest.review_index,
      pools: privateManifest.pools,
    },
  }
}

function validateEmittedRowHash(context, question, label) {
  if (typeof question.row_content_sha256 !== "string" || !HASH_PATTERN.test(question.row_content_sha256)) {
    fail(context, `${label}:invalid_row_content_sha256`)
    return
  }
  if (question.row_content_sha256 !== emittedRowHash(question)) fail(context, `${label}:row_content_sha256_mismatch`)
  if (typeof question.content_sha256 !== "string" || !HASH_PATTERN.test(question.content_sha256)) {
    fail(context, `${label}:invalid_content_sha256`)
  }
}

function validateArtifactBuildId(context, publicManifest, privateManifest) {
  const expected = sha256(Buffer.from(canonicalJson(artifactBuildDescriptor(publicManifest, privateManifest)), "utf8"))
  if (publicManifest.build_id !== expected || privateManifest.build_id !== expected) {
    fail(context, "manifest:build_id_descriptor_mismatch")
  }
}

function makeContext(options) {
  const blindBaseUrl = (options.blindBaseUrl ?? process.env.BLIND_BANK_BASE_URL ?? "").replace(/\/+$/, "")
  const blindRoot = options.blindRoot ?? process.env.BLIND_BANK_ROOT ?? ""
  return {
    baseUrl: (options.baseUrl ?? process.env.FINAL_BANK_BASE_URL ?? "https://conexion-biblica-2026.vercel.app").replace(/\/+$/, ""),
    publicRoot: resolve(options.publicRoot ?? "public"),
    timeoutMs: options.timeoutMs ?? 30_000,
    fetchImpl: options.fetchImpl ?? fetch,
    blindBaseUrl,
    blindRoot,
    blindRequirements: options.blindRequirements ?? null,
    privateAudit: "NOT_RUN",
    privateAuditMode: blindRoot && blindBaseUrl ? "LOCAL_AND_REMOTE" : blindRoot ? "LOCAL" : blindBaseUrl ? "REMOTE" : "NOT_RUN",
    failures: [],
  }
}

function fail(context, message) {
  if (!context.failures.includes(message)) context.failures.push(message)
}

function report(context, details = {}) {
  return {
    baseUrl: context.baseUrl,
    resources: details.resources ?? 1,
    shards: details.shards ?? 0,
    questions: details.questions ?? 0,
    uniqueFacts: details.uniqueFacts ?? 0,
    privateAudit: context.privateAudit,
    blindQuestions: context.privateAudit === "NOT_RUN" ? null : (details.blindQuestions ?? 0),
    totalBytes: details.totalBytes ?? 0,
    failures: context.failures,
  }
}

async function fetchBytes(context, path) {
  try {
    const response = await context.fetchImpl(`${context.baseUrl}/${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(context.timeoutMs),
    })
    if (!response.ok) {
      fail(context, `${path}:http_${response.status}`)
      return null
    }
    return Buffer.from(await response.arrayBuffer())
  } catch (error) {
    const timeout = error?.name === "AbortError" || error?.name === "TimeoutError" || error?.code === "ABORT_ERR"
    fail(context, `${path}:${timeout ? "timeout_or_abort" : "fetch_error"}`)
    return null
  }
}

async function readLocal(context, path) {
  try {
    return await readFile(resolve(context.publicRoot, ...path.split("/")))
  } catch {
    fail(context, `${path}:local_missing`)
    return null
  }
}

function parseJson(context, path, bytes) {
  if (!bytes) return null
  try {
    return JSON.parse(bytes.toString("utf8"))
  } catch {
    fail(context, `${path}:invalid_json`)
    return null
  }
}

function validateCountRecord(context, label, value) {
  if (!isRecord(value) || Object.values(value).some((count) => !isInteger(count))) {
    fail(context, `${label}:invalid_counts`)
    return false
  }
  return true
}

function validateReleaseRequirements(context, manifest) {
  const requirements = context.blindRequirements
  if (requirements === null) return
  if (!isRecord(requirements)
    || JSON.stringify(Object.keys(requirements).sort()) !== JSON.stringify([...BLIND_POOLS].sort())) {
    fail(context, "release:requirements_schema")
    return
  }
  for (const pool of BLIND_POOLS) {
    const expected = requirements[pool]
    const actual = manifest.blind_pools[pool]
    if (!isRecord(expected) || !isInteger(expected.fact_count) || !isRecord(expected.families)
      || JSON.stringify(Object.keys(expected.families).sort()) !== JSON.stringify([...BLIND_FAMILIES].sort())
      || Object.values(expected.families).some((count) => !isInteger(count))) {
      fail(context, `release:${pool}:requirements_schema`)
      continue
    }
    if (Object.values(expected.families).reduce((sum, count) => sum + count, 0) !== expected.fact_count) {
      fail(context, `release:${pool}:requirements_total`)
    }
    if (actual.fact_count !== expected.fact_count) {
      fail(context, `release:${pool}:fact_count:expected_${expected.fact_count}:actual_${actual.fact_count}`)
    }
    for (const family of BLIND_FAMILIES) {
      if (actual.families[family] !== expected.families[family]) {
        fail(context, `release:${pool}:family_${family}:expected_${expected.families[family]}:actual_${actual.families[family]}`)
      }
    }
  }
}

function validatePublicManifest(context, manifest) {
  const start = context.failures.length
  if (!isRecord(manifest)) {
    fail(context, "manifest:invalid_document")
    return null
  }
  if (manifest.schema_version !== SCHEMA_VERSION) fail(context, "manifest:schema_version")
  if (manifest.bank_id === undefined) fail(context, "manifest:missing_bank_id")
  else if (manifest.bank_id !== BANK_ID) fail(context, "manifest:bank_id")
  if (typeof manifest.build_id !== "string" || !HASH_PATTERN.test(manifest.build_id)) fail(context, "manifest:build_id")
  for (const field of ["display_name", "source"]) {
    if (typeof manifest[field] !== "string" || !manifest[field].trim()) fail(context, `manifest:missing_${field}`)
  }
  for (const field of PUBLIC_INTEGER_FIELDS) {
    if (manifest[field] === undefined) fail(context, `manifest:missing_${field}`)
    else if (!isInteger(manifest[field])) fail(context, `manifest:invalid_${field}`)
  }
  validateCountRecord(context, "manifest:families", manifest.families)
  validateCountRecord(context, "manifest:total_families", manifest.total_families)
  if (!isRecord(manifest.blind_pools)) fail(context, "manifest:blind_pools")
  else {
    if (JSON.stringify(Object.keys(manifest.blind_pools).sort()) !== JSON.stringify([...BLIND_POOLS].sort())) {
      fail(context, "manifest:blind_pools_schema")
    }
    for (const [pool, metadata] of Object.entries(manifest.blind_pools)) {
      if (isRecord(metadata) && isRecord(metadata.families)
        && JSON.stringify(Object.keys(metadata.families).sort()) !== JSON.stringify([...BLIND_FAMILIES].sort())) {
        fail(context, `manifest:blind_pool_${pool}_families_schema`)
      }
    }
  }
  if (
    !isRecord(manifest.blind_delivery)
    || manifest.blind_delivery.contract !== BLIND_CONTRACT
    || manifest.blind_delivery.artifact_id !== BLIND_ARTIFACT_ID
    || typeof manifest.blind_delivery.artifact_revision !== "string"
    || !HASH_PATTERN.test(manifest.blind_delivery.artifact_revision)
  ) fail(context, "manifest:blind_delivery")
  if (
    !isRecord(manifest.review_index)
    || manifest.review_index.file !== REVIEW_INDEX_PATH
    || !isInteger(manifest.review_index.bytes)
    || manifest.review_index.bytes === 0
    || typeof manifest.review_index.sha256 !== "string"
    || !HASH_PATTERN.test(manifest.review_index.sha256)
  ) fail(context, "manifest:review_index")
  if (!Array.isArray(manifest.shards)) fail(context, "manifest:invalid_shards")
  if (context.failures.length !== start) return null

  const chapters = manifest.shards.map((shard) => shard?.chapter)
  if (
    manifest.shards.length !== EXPECTED_UNITS.length
    || new Set(chapters).size !== EXPECTED_UNITS.length
    || JSON.stringify([...chapters].sort()) !== JSON.stringify([...EXPECTED_UNITS].sort())
  ) fail(context, "manifest:expected_units")

  const shards = []
  for (const unit of EXPECTED_UNITS) {
    const shard = manifest.shards.find((candidate) => candidate?.chapter === unit)
    if (!isRecord(shard)) continue
    const expectedPath = `${BANK_ROOT}/questions/${unit}.json`
    if (shard.questions_file !== expectedPath) fail(context, `${unit}:questions_file`)
    if (!isInteger(shard.question_count)) fail(context, `${unit}:question_count`)
    if (!isInteger(shard.training_question_count)) fail(context, `${unit}:training_question_count`)
    if (shard.training_question_count !== shard.question_count) fail(context, `${unit}:training_question_count_mismatch`)
    if (!isInteger(shard.bytes) || shard.bytes === 0) fail(context, `${unit}:bytes`)
    if (typeof shard.sha256 !== "string" || !HASH_PATTERN.test(shard.sha256)) fail(context, `${unit}:sha256`)
    shards.push(shard)
  }

  if (context.failures.length !== start) return null
  const shardCount = shards.reduce((sum, shard) => sum + shard.question_count, 0)
  if (manifest.gold_questions !== manifest.training_presentation_count) fail(context, "manifest:gold_questions_mismatch")
  if (manifest.unique_facts !== manifest.training_fact_count) fail(context, "manifest:unique_facts_mismatch")
  if (manifest.training_presentation_count !== shardCount) fail(context, "manifest:training_presentation_count_mismatch")
  if (manifest.central_question_count + manifest.presentation_variant_count !== manifest.training_presentation_count) {
    fail(context, "manifest:role_counts_mismatch")
  }
  if (Object.values(manifest.families).reduce((sum, count) => sum + count, 0) !== manifest.training_presentation_count) {
    fail(context, "manifest:families_mismatch")
  }
  let blindFacts = 0
  let blindPresentations = 0
  for (const [pool, metadata] of Object.entries(manifest.blind_pools)) {
    if (!BLIND_POOLS.includes(pool) || !isRecord(metadata)) {
      fail(context, `manifest:blind_pool_${pool}`)
      continue
    }
    if (!isInteger(metadata.fact_count) || !isInteger(metadata.presentation_count)) {
      fail(context, `manifest:blind_pool_${pool}_counts`)
      continue
    }
    if (!validateCountRecord(context, `manifest:blind_pool_${pool}_families`, metadata.families)) continue
    if (Object.values(metadata.families).reduce((sum, count) => sum + count, 0) !== metadata.presentation_count) {
      fail(context, `manifest:blind_pool_${pool}_families_mismatch`)
    }
    blindFacts += metadata.fact_count
    blindPresentations += metadata.presentation_count
  }
  if (manifest.blind_fact_count !== blindFacts) fail(context, "manifest:blind_fact_count_mismatch")
  if (manifest.blind_presentation_count !== blindPresentations) fail(context, "manifest:blind_presentation_count_mismatch")
  if (manifest.total_fact_count !== manifest.training_fact_count + manifest.blind_fact_count) {
    fail(context, "manifest:total_fact_count_mismatch")
  }
  if (manifest.total_presentation_count !== manifest.training_presentation_count + manifest.blind_presentation_count) {
    fail(context, "manifest:total_presentation_count_mismatch")
  }
  if (manifest.total_central_question_count < manifest.central_question_count) {
    fail(context, "manifest:total_central_question_count_mismatch")
  }
  if (manifest.total_presentation_variant_count < manifest.presentation_variant_count) {
    fail(context, "manifest:total_presentation_variant_count_mismatch")
  }
  if (manifest.total_central_question_count + manifest.total_presentation_variant_count !== manifest.total_presentation_count) {
    fail(context, "manifest:total_role_counts_mismatch")
  }
  if (Object.values(manifest.total_families).reduce((sum, count) => sum + count, 0) !== manifest.total_presentation_count) {
    fail(context, "manifest:total_families_mismatch")
  }
  validateReleaseRequirements(context, manifest)
  return context.failures.length === start ? shards : null
}

async function walk(root, current = root) {
  const output = []
  for (const entry of await readdir(current, { withFileTypes: true })) {
    const absolute = resolve(current, entry.name)
    const normalized = relative(root, absolute).split(sep).join("/")
    if (entry.isDirectory()) {
      output.push({ path: `${normalized}/`, directory: true })
      output.push(...await walk(root, absolute))
    } else {
      output.push({ path: normalized, directory: false })
    }
  }
  return output
}

async function validateLocalAllowlist(context, declaredPaths) {
  const bankRoot = resolve(context.publicRoot, BANK_ROOT)
  const allowedDirectories = new Set(["questions/"])
  try {
    for (const entry of await walk(bankRoot)) {
      const resource = `${BANK_ROOT}/${entry.path}`
      if (entry.directory) {
        if (!allowedDirectories.has(entry.path)) fail(context, `${resource}:undeclared_local_directory`)
      } else if (!declaredPaths.has(resource)) {
        fail(context, `${resource}:undeclared_local_resource`)
      }
    }
  } catch {
    fail(context, `${BANK_ROOT}:local_missing`)
  }
}

function validateQuestions(context, manifest, shards, documents) {
  const questions = []
  const ids = new Set()
  for (const shard of shards) {
    const rows = documents.get(shard.questions_file)
    if (!Array.isArray(rows)) {
      fail(context, `${shard.questions_file}:expected_array`)
      continue
    }
    if (rows.length !== shard.question_count) fail(context, `${shard.chapter}:question_count_mismatch`)
    for (const question of rows) {
      if (!isRecord(question)) {
        fail(context, `${shard.chapter}:invalid_question`)
        continue
      }
      const label = typeof question.id === "string" ? question.id : shard.chapter
      if (question.schema_version !== SCHEMA_VERSION) fail(context, `${label}:schema_version`)
      if (question.chapter !== shard.chapter) fail(context, `${label}:chapter_mismatch`)
      if (typeof question.id !== "string" || ids.has(question.id)) fail(context, `${label}:duplicate_or_missing_id`)
      else ids.add(question.id)
      if (typeof question.fact_id !== "string" || !question.fact_id) fail(context, `${label}:fact_id`)
      if (typeof question.family !== "string" || !question.family) fail(context, `${label}:family`)
      if (!isRecord(question.ai_review)) fail(context, `${label}:ai_review`)
      if (question.blind_pool !== null) fail(context, `${label}:public_blind_pool`)
      validateEmittedRowHash(context, question, label)
      questions.push(question)
    }
  }
  const families = {}
  for (const row of questions) families[row.family] = (families[row.family] ?? 0) + 1
  const factCount = new Set(questions.map((row) => row.fact_id)).size
  if (questions.length !== manifest.training_presentation_count) fail(context, "manifest:training_presentation_count_mismatch")
  if (factCount !== manifest.training_fact_count) fail(context, "manifest:training_fact_count_mismatch")
  if (!sameCounts(families, manifest.families)) fail(context, "manifest:families_mismatch")
  const central = questions.filter((row) => row.role === "central").length
  const variants = questions.filter((row) => row.role === "variant").length
  if (central !== manifest.central_question_count) fail(context, "manifest:central_question_count_mismatch")
  if (variants !== manifest.presentation_variant_count) fail(context, "manifest:presentation_variant_count_mismatch")
  return { questions, factCount }
}

function validateReviewIndex(context, reviewIndex, questions) {
  if (!isRecord(reviewIndex)) {
    fail(context, "review-index:invalid_document")
    return
  }
  if (reviewIndex.schema_version !== SCHEMA_VERSION) fail(context, "review-index:schema_version")
  if (reviewIndex.human_signatures !== 0) fail(context, "review-index:human_signatures")
  if (!isInteger(reviewIndex.total_reviewed) || !Array.isArray(reviewIndex.entries)) {
    fail(context, "review-index:invalid_entries")
    return
  }
  if (reviewIndex.total_reviewed !== reviewIndex.entries.length || reviewIndex.total_reviewed !== questions.length) {
    fail(context, "review-index:total_reviewed_mismatch")
  }
  const byId = new Map(questions.map((question) => [question.id, question]))
  const seen = new Set()
  for (const entry of reviewIndex.entries) {
    if (!isRecord(entry) || typeof entry.question_id !== "string" || seen.has(entry.question_id)) {
      fail(context, "review-index:duplicate_or_missing_question_id")
      continue
    }
    seen.add(entry.question_id)
    const question = byId.get(entry.question_id)
    if (!question) {
      fail(context, `${entry.question_id}:review_without_question`)
      continue
    }
    if (typeof entry.content_sha256 !== "string" || !HASH_PATTERN.test(entry.content_sha256)) {
      fail(context, `${entry.question_id}:invalid_review_hash`)
    } else if (entry.content_sha256 !== question.row_content_sha256) fail(context, `${entry.question_id}:review_hash_mismatch`)
    if (typeof entry.source_content_sha256 !== "string" || !HASH_PATTERN.test(entry.source_content_sha256)) {
      fail(context, `${entry.question_id}:invalid_source_review_hash`)
    } else if (entry.source_content_sha256 !== question.content_sha256) {
      fail(context, `${entry.question_id}:source_review_hash_mismatch`)
    }
    if (entry.decision !== "passed") fail(context, `${entry.question_id}:review_not_passed`)
    if (typeof entry.reviewer !== "string" || !entry.reviewer.trim()) fail(context, `${entry.question_id}:invalid_reviewer`)
    if (typeof entry.reviewer_type !== "string" || !entry.reviewer_type.trim()) fail(context, `${entry.question_id}:invalid_reviewer_type`)
    const aiReview = question.ai_review
    if (
      !isRecord(aiReview)
      || aiReview.status !== "passed"
      || aiReview.reviewer !== entry.reviewer
      || aiReview.reviewer_type !== entry.reviewer_type
    ) fail(context, `${entry.question_id}:ai_review_mismatch`)
  }
  for (const question of questions) if (!seen.has(question.id)) fail(context, `${question.id}:missing_review`)
}

async function fetchPrivate(context, path) {
  try {
    const response = await context.fetchImpl(`${context.blindBaseUrl}/${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(context.timeoutMs),
    })
    if (!response.ok) {
      fail(context, `${path}:http_${response.status}`)
      return null
    }
    return Buffer.from(await response.arrayBuffer())
  } catch (error) {
    const timeout = error?.name === "AbortError" || error?.name === "TimeoutError" || error?.code === "ABORT_ERR"
    fail(context, `${path}:${timeout ? "timeout_or_abort" : "fetch_error"}`)
    return null
  }
}

async function readPrivate(context, path) {
  try {
    return await readFile(resolve(context.blindRoot, ...path.split("/")))
  } catch {
    fail(context, `${path}:local_missing`)
    return null
  }
}

async function loadPrivateResource(context, path) {
  const [local, remote] = await Promise.all([
    context.blindRoot ? readPrivate(context, path) : null,
    context.blindBaseUrl ? fetchPrivate(context, path) : null,
  ])
  if (local && remote && !local.equals(remote)) fail(context, `${path}:content_mismatch`)
  return remote ?? local
}

function validatePrivateManifest(context, manifest, publicManifest) {
  const start = context.failures.length
  if (!isRecord(manifest)) {
    fail(context, "blind-manifest:invalid_document")
    return null
  }
  if (manifest.contract !== BLIND_CONTRACT) fail(context, "blind-manifest:contract")
  if (manifest.artifact_id !== BLIND_ARTIFACT_ID) fail(context, "blind-manifest:artifact_id")
  if (typeof manifest.build_id !== "string" || !HASH_PATTERN.test(manifest.build_id)
    || manifest.build_id !== publicManifest.build_id) fail(context, "blind-manifest:build_id")
  if (typeof manifest.artifact_revision !== "string" || !HASH_PATTERN.test(manifest.artifact_revision)
    || manifest.artifact_revision !== publicManifest.blind_delivery.artifact_revision) {
    fail(context, "blind-manifest:artifact_revision")
  }
  if (manifest.schema_version !== SCHEMA_VERSION) fail(context, "blind-manifest:schema_version")
  if (manifest.bank_id !== BANK_ID) fail(context, "blind-manifest:bank_id")
  for (const field of [
    "total_fact_count",
    "total_presentation_count",
    "central_question_count",
    "presentation_variant_count",
  ]) {
    if (!isInteger(manifest[field])) fail(context, `blind-manifest:${field}`)
  }
  if (!isRecord(manifest.families)
    || JSON.stringify(Object.keys(manifest.families).sort()) !== JSON.stringify([...BLIND_FAMILIES].sort())) {
    fail(context, "blind-manifest:families_schema")
  } else validateCountRecord(context, "blind-manifest:families", manifest.families)
  if (
    !isRecord(manifest.review_index)
    || manifest.review_index.file !== "review-index.json"
    || !isInteger(manifest.review_index.bytes)
    || manifest.review_index.bytes === 0
    || typeof manifest.review_index.sha256 !== "string"
    || !HASH_PATTERN.test(manifest.review_index.sha256)
  ) fail(context, "blind-manifest:review_index")
  if (!isRecord(manifest.pools)) fail(context, "blind-manifest:pools")
  else {
    if (JSON.stringify(Object.keys(manifest.pools).sort()) !== JSON.stringify([...BLIND_POOLS].sort())) {
      fail(context, "blind-manifest:pools_schema")
    }
    for (const [pool, metadata] of Object.entries(manifest.pools)) {
      if (isRecord(metadata) && isRecord(metadata.families)
        && JSON.stringify(Object.keys(metadata.families).sort()) !== JSON.stringify([...BLIND_FAMILIES].sort())) {
        fail(context, `blind-manifest:pool_${pool}_families_schema`)
      }
    }
  }
  if (context.failures.length !== start) return null

  if (JSON.stringify(Object.keys(manifest.pools).sort()) !== JSON.stringify(Object.keys(publicManifest.blind_pools).sort())) {
    fail(context, "blind-manifest:pools_mismatch")
  }
  const shards = []
  const paths = new Set()
  for (const [pool, metadata] of Object.entries(manifest.pools)) {
    if (!BLIND_POOLS.includes(pool) || !isRecord(metadata) || !Array.isArray(metadata.shards)) {
      fail(context, `blind-manifest:pool_${pool}`)
      continue
    }
    if (!isInteger(metadata.fact_count) || !isInteger(metadata.presentation_count)) {
      fail(context, `blind-manifest:pool_${pool}_counts`)
    }
    validateCountRecord(context, `blind-manifest:pool_${pool}_families`, metadata.families)
    const publicMetadata = publicManifest.blind_pools[pool]
    if (!publicMetadata || !sameCounts(metadata.families, publicMetadata.families)
      || metadata.fact_count !== publicMetadata.fact_count
      || metadata.presentation_count !== publicMetadata.presentation_count) {
      fail(context, `blind-manifest:pool_${pool}_metadata_mismatch`)
    }
    for (const shard of metadata.shards) {
      if (!isRecord(shard) || !EXPECTED_UNITS.includes(shard.chapter)) {
        fail(context, `blind-manifest:pool_${pool}_shard`)
        continue
      }
      const expectedPath = `questions/${pool}/${shard.chapter}.json`
      if (shard.questions_file !== expectedPath) fail(context, `${pool}:${shard.chapter}:questions_file`)
      if (paths.has(shard.questions_file)) fail(context, `${shard.questions_file}:duplicate_shard`)
      paths.add(shard.questions_file)
      if (!isInteger(shard.question_count)) fail(context, `${pool}:${shard.chapter}:question_count`)
      if (!isInteger(shard.bytes) || shard.bytes === 0) fail(context, `${pool}:${shard.chapter}:bytes`)
      if (typeof shard.sha256 !== "string" || !HASH_PATTERN.test(shard.sha256)) fail(context, `${pool}:${shard.chapter}:sha256`)
      shards.push({ ...shard, pool })
    }
    if (metadata.shards.reduce((sum, shard) => sum + (isInteger(shard?.question_count) ? shard.question_count : 0), 0) !== metadata.presentation_count) {
      fail(context, `blind-manifest:pool_${pool}_presentation_count_mismatch`)
    }
  }
  if (Object.values(manifest.pools).reduce((sum, pool) => sum + (pool?.fact_count ?? 0), 0) !== manifest.total_fact_count) {
    fail(context, "blind-manifest:total_fact_count_mismatch")
  }
  if (Object.values(manifest.pools).reduce((sum, pool) => sum + (pool?.presentation_count ?? 0), 0) !== manifest.total_presentation_count) {
    fail(context, "blind-manifest:total_presentation_count_mismatch")
  }
  if (manifest.central_question_count !== manifest.total_presentation_count) {
    fail(context, "blind-manifest:central_question_count_mismatch")
  }
  if (manifest.presentation_variant_count !== 0) fail(context, "blind-manifest:presentation_variant_count_mismatch")
  if (isRecord(manifest.families)) {
    const aggregateFamilies = Object.fromEntries(BLIND_FAMILIES.map((family) => [
      family,
      Object.values(manifest.pools).reduce((sum, pool) => sum + (pool?.families?.[family] ?? 0), 0),
    ]))
    if (!sameCounts(manifest.families, aggregateFamilies)) fail(context, "blind-manifest:families_mismatch")
  }
  return context.failures.length === start ? shards : null
}

async function validatePrivateAllowlist(context, declaredPaths) {
  if (!context.blindRoot) return
  const allowedDirectories = new Set()
  for (const path of declaredPaths) {
    const parts = path.split("/").slice(0, -1)
    for (let index = 1; index <= parts.length; index += 1) allowedDirectories.add(`${parts.slice(0, index).join("/")}/`)
  }
  try {
    for (const entry of await walk(resolve(context.blindRoot))) {
      if (entry.directory) {
        if (!allowedDirectories.has(entry.path)) fail(context, `${entry.path}:undeclared_local_directory`)
      } else if (!declaredPaths.has(entry.path)) fail(context, `${entry.path}:undeclared_local_resource`)
    }
  } catch {
    fail(context, "blind-root:local_missing")
  }
}

function validateBlindQuestions(context, manifest, shards, documents) {
  const questions = []
  const ids = new Set()
  for (const shard of shards) {
    const rows = documents.get(shard.questions_file)
    if (!Array.isArray(rows)) {
      fail(context, `${shard.questions_file}:expected_array`)
      continue
    }
    if (rows.length !== shard.question_count) fail(context, `${shard.pool}:${shard.chapter}:question_count_mismatch`)
    for (const question of rows) {
      if (!isRecord(question)) continue
      const label = question.id ?? shard.chapter
      if (question.schema_version !== SCHEMA_VERSION) fail(context, `${label}:schema_version`)
      if (question.chapter !== shard.chapter) fail(context, `${label}:chapter_mismatch`)
      if (question.blind_pool !== shard.pool) fail(context, `${label}:blind_pool_mismatch`)
      if (question.role !== "central") fail(context, `${label}:blind_role`)
      if (typeof question.id !== "string" || ids.has(question.id)) fail(context, `${label}:duplicate_or_missing_id`)
      else ids.add(question.id)
      if (typeof question.fact_id !== "string" || !question.fact_id) fail(context, `${label}:fact_id`)
      if (!isRecord(question.ai_review)) fail(context, `${label}:ai_review`)
      validateEmittedRowHash(context, question, label)
      questions.push(question)
    }
  }
  const facts = new Set(questions.map((row) => row.fact_id))
  if (questions.length !== manifest.total_presentation_count) fail(context, "blind-manifest:total_presentation_count_mismatch")
  if (facts.size !== manifest.total_fact_count) fail(context, "blind-manifest:total_fact_count_mismatch")
  for (const [pool, metadata] of Object.entries(manifest.pools)) {
    const rows = questions.filter((row) => row.blind_pool === pool)
    const families = {}
    for (const row of rows) {
      const family = row.family?.startsWith("single_choice") ? "selection" : row.family
      families[family] = (families[family] ?? 0) + 1
    }
    if (rows.length !== metadata.presentation_count) fail(context, `blind-manifest:pool_${pool}_presentation_count_mismatch`)
    if (new Set(rows.map((row) => row.fact_id)).size !== metadata.fact_count) fail(context, `blind-manifest:pool_${pool}_fact_count_mismatch`)
    if (!sameCounts(families, metadata.families)) fail(context, `blind-manifest:pool_${pool}_families_mismatch`)
  }
  return { questions, facts }
}

async function auditPrivateArtifact(context, publicManifest, trainingQuestions) {
  if (!context.blindBaseUrl && !context.blindRoot) return null
  context.privateAudit = context.privateAuditMode
  const manifestBytes = await loadPrivateResource(context, "manifest.json")
  if (!manifestBytes) return { questions: [], facts: new Set(), totalBytes: 0, resources: 1, shards: 0 }
  const manifest = parseJson(context, "manifest.json", manifestBytes)
  if (!manifest) return { questions: [], facts: new Set(), totalBytes: manifestBytes.byteLength, resources: 1, shards: 0 }
  const shards = validatePrivateManifest(context, manifest, publicManifest)
  if (!shards) return { questions: [], facts: new Set(), totalBytes: manifestBytes.byteLength, resources: 1, shards: 0 }
  validateArtifactBuildId(context, publicManifest, manifest)
  const paths = ["review-index.json", ...shards.map((shard) => shard.questions_file)]
  await validatePrivateAllowlist(context, new Set(["manifest.json", ...paths]))
  const bytesByPath = new Map()
  let totalBytes = manifestBytes.byteLength
  await Promise.all(paths.map(async (path) => {
    const bytes = await loadPrivateResource(context, path)
    if (!bytes) return
    bytesByPath.set(path, bytes)
    totalBytes += bytes.byteLength
    const descriptor = path === "review-index.json" ? manifest.review_index : shards.find((shard) => shard.questions_file === path)
    if (bytes.byteLength !== descriptor.bytes) fail(context, `${path}:bytes_mismatch`)
    if (sha256(bytes) !== descriptor.sha256) fail(context, `${path}:sha256_mismatch`)
  }))
  const documents = new Map(shards.map((shard) => [shard.questions_file, parseJson(context, shard.questions_file, bytesByPath.get(shard.questions_file))]))
  const result = validateBlindQuestions(context, manifest, shards, documents)
  validateReviewIndex(context, parseJson(context, "review-index.json", bytesByPath.get("review-index.json")), result.questions)
  const trainingIds = new Set(trainingQuestions.map((row) => row.id))
  const trainingFacts = new Set(trainingQuestions.map((row) => row.fact_id))
  for (const row of result.questions) {
    if (trainingIds.has(row.id)) fail(context, `${row.id}:training_blind_id_collision`)
    if (trainingFacts.has(row.fact_id)) fail(context, `${row.fact_id}:training_blind_fact_collision`)
  }
  return { ...result, totalBytes, resources: paths.length + 1, shards: shards.length }
}

export async function auditLiveFinalBank(options = {}) {
  const context = makeContext(options)
  const [localManifestBytes, remoteManifestBytes] = await Promise.all([
    readLocal(context, MANIFEST_PATH),
    fetchBytes(context, MANIFEST_PATH),
  ])
  let totalBytes = remoteManifestBytes?.byteLength ?? 0
  if (!remoteManifestBytes) return report(context, { totalBytes })
  if (localManifestBytes && !localManifestBytes.equals(remoteManifestBytes)) fail(context, `${MANIFEST_PATH}:content_mismatch`)
  const manifest = parseJson(context, MANIFEST_PATH, remoteManifestBytes)
  if (!manifest) return report(context, { totalBytes })
  const shards = validatePublicManifest(context, manifest)
  if (!shards) return report(context, { totalBytes })

  const resourcePaths = [REVIEW_INDEX_PATH, ...shards.map((shard) => shard.questions_file)]
  const declaredPaths = new Set([MANIFEST_PATH, V18_PACKAGES_PATH, ...resourcePaths])
  await validateLocalAllowlist(context, declaredPaths)
  const remote = new Map()
  await Promise.all(resourcePaths.map(async (path) => {
    const [localBytes, remoteBytes] = await Promise.all([readLocal(context, path), fetchBytes(context, path)])
    if (!remoteBytes) return
    remote.set(path, remoteBytes)
    totalBytes += remoteBytes.byteLength
    if (localBytes && !localBytes.equals(remoteBytes)) fail(context, `${path}:content_mismatch`)
    const shard = shards.find((candidate) => candidate.questions_file === path)
    if (shard) {
      if (remoteBytes.byteLength !== shard.bytes) fail(context, `${path}:bytes_mismatch`)
      if (sha256(remoteBytes) !== shard.sha256) fail(context, `${path}:sha256_mismatch`)
    } else if (path === REVIEW_INDEX_PATH) {
      if (remoteBytes.byteLength !== manifest.review_index.bytes) fail(context, `${path}:bytes_mismatch`)
      if (sha256(remoteBytes) !== manifest.review_index.sha256) fail(context, `${path}:sha256_mismatch`)
    }
  }))
  const documents = new Map(shards.map((shard) => [
    shard.questions_file,
    parseJson(context, shard.questions_file, remote.get(shard.questions_file)),
  ]))
  const { questions, factCount } = validateQuestions(context, manifest, shards, documents)
  const reviewIndex = parseJson(context, REVIEW_INDEX_PATH, remote.get(REVIEW_INDEX_PATH))
  validateReviewIndex(context, reviewIndex, questions)
  const blind = await auditPrivateArtifact(context, manifest, questions)
  if (blind) {
    const combined = [...questions, ...blind.questions]
    const combinedFacts = new Set(combined.map((row) => row.fact_id))
    const combinedFamilies = {}
    for (const row of combined) combinedFamilies[row.family] = (combinedFamilies[row.family] ?? 0) + 1
    if (combined.length !== manifest.total_presentation_count) fail(context, "manifest:total_presentation_count_mismatch")
    if (combinedFacts.size !== manifest.total_fact_count) fail(context, "manifest:total_fact_count_mismatch")
    if (!sameCounts(combinedFamilies, manifest.total_families)) fail(context, "manifest:total_families_mismatch")
    if (combined.filter((row) => row.role === "central").length !== manifest.total_central_question_count) {
      fail(context, "manifest:total_central_question_count_mismatch")
    }
    if (combined.filter((row) => row.role === "variant").length !== manifest.total_presentation_variant_count) {
      fail(context, "manifest:total_presentation_variant_count_mismatch")
    }
    totalBytes += blind.totalBytes
    return report(context, {
      resources: declaredPaths.size + blind.resources,
      shards: shards.length + blind.shards,
      questions: combined.length,
      uniqueFacts: combinedFacts.size,
      blindQuestions: blind.questions.length,
      totalBytes,
    })
  }
  return report(context, {
    resources: declaredPaths.size,
    shards: shards.length,
    questions: questions.length,
    uniqueFacts: factCount,
    totalBytes,
  })
}

const isDirectRun = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))
if (isDirectRun) {
  const privateAuditRequested = Boolean(process.env.BLIND_BANK_BASE_URL || process.env.BLIND_BANK_ROOT)
  const result = await auditLiveFinalBank({
    blindRequirements: privateAuditRequested ? RELEASE_BLIND_REQUIREMENTS : null,
  })
  console.log(JSON.stringify(result, null, 2))
  if (result.failures.length) process.exitCode = 1
}
