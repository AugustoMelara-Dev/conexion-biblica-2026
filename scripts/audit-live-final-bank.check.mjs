import assert from "node:assert/strict"
import { createHash } from "node:crypto"
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises"
import { createServer } from "node:http"
import { tmpdir } from "node:os"
import { dirname, join } from "node:path"
import test from "node:test"
import { auditLiveFinalBank } from "./audit-live-final-bank.mjs"

const units = [
  ...Array.from({ length: 12 }, (_, index) => `DAN${index + 1}`),
  ...Array.from({ length: 6 }, (_, index) => `PR${index + 39}`),
]

const sha256 = (value) => createHash("sha256").update(value).digest("hex")
const jsonBytes = (value) => Buffer.from(`${JSON.stringify(value, null, 2)}\n`)
const canonicalJson = (value) => {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`
  if (value !== null && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`
  }
  return JSON.stringify(value)
}
const emittedRowHash = (row) => sha256(canonicalJson(Object.fromEntries(
  Object.entries(row).filter(([key]) => key !== "row_content_sha256"),
)))
const buildDescriptor = (publicManifest, privateManifest) => ({
  contract: "competitive-v11-emitted-descriptors-v1",
  schema_version: publicManifest.schema_version,
  bank_id: publicManifest.bank_id,
  artifact_revision: publicManifest.blind_delivery.artifact_revision,
  public: {
    counts: Object.fromEntries([
      "unique_facts", "gold_questions", "central_question_count", "presentation_variant_count",
      "training_fact_count", "training_presentation_count", "total_fact_count", "total_presentation_count",
      "total_central_question_count", "total_presentation_variant_count", "blind_fact_count", "blind_presentation_count",
    ].map((key) => [key, publicManifest[key]])),
    families: publicManifest.families,
    total_families: publicManifest.total_families,
    blind_pools: publicManifest.blind_pools,
    review_index: publicManifest.review_index,
    shards: publicManifest.shards,
  },
  private: privateManifest ? {
    contract: privateManifest.contract,
    artifact_id: privateManifest.artifact_id,
    artifact_revision: privateManifest.artifact_revision,
    schema_version: privateManifest.schema_version,
    bank_id: privateManifest.bank_id,
    counts: Object.fromEntries([
      "total_fact_count", "total_presentation_count", "central_question_count", "presentation_variant_count",
    ].map((key) => [key, privateManifest[key]])),
    families: privateManifest.families,
    review_index: privateManifest.review_index,
    pools: privateManifest.pools,
  } : null,
})
const artifactBuildId = (publicManifest, privateManifest = null) => sha256(canonicalJson(buildDescriptor(publicManifest, privateManifest)))

async function makeBank(mutate = () => {}) {
  const root = await mkdtemp(join(tmpdir(), "live-bank-v11-"))
  const publicRoot = join(root, "public")
  const bankRoot = join(publicRoot, "banks", "final-2026")
  const files = new Map()
  const questions = []
  const families = {
    single_choice_direct: 0,
    fill_choice: 0,
    true_false: 0,
  }
  const familyNames = Object.keys(families)

  for (const [index, chapter] of units.entries()) {
    const family = familyNames[index % familyNames.length]
    families[family] += 1
    const question = {
      id: `${chapter}-V11-TEST-001`,
      schema_version: "10.0",
      chapter,
      fact_id: `${chapter}-F001`,
      family,
      role: "central",
      blind_pool: null,
      ai_review: {
        status: "passed",
        reviewer_type: "ai_semantic_audit",
        reviewer: "test-reviewer",
      },
      content_sha256: sha256(`${chapter}:content`),
    }
    question.row_content_sha256 = emittedRowHash(question)
    questions.push(question)
    files.set(`banks/final-2026/questions/${chapter}.json`, jsonBytes([question]))
  }

  const reviewIndex = {
    schema_version: "10.0",
    total_reviewed: questions.length,
    human_signatures: 0,
    entries: questions.map((question) => ({
      question_id: question.id,
      content_sha256: question.row_content_sha256,
      source_content_sha256: question.content_sha256,
      decision: "passed",
      reviewer_type: "ai_semantic_audit",
      reviewer: "test-reviewer",
    })),
  }
  files.set("banks/final-2026/review-index.json", jsonBytes(reviewIndex))

  const shards = units.map((chapter) => {
    const path = `banks/final-2026/questions/${chapter}.json`
    const bytes = files.get(path)
    return {
      chapter,
      question_count: 1,
      training_question_count: 1,
      questions_file: path,
      bytes: bytes.byteLength,
      sha256: sha256(bytes),
    }
  })
  const manifest = {
    schema_version: "10.0",
    bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
    build_id: "0".repeat(64),
    display_name: "Banco competitivo V11 de prueba",
    source: "MaterialConexionBiblica (1).pdf",
    gold_questions: questions.length,
    unique_facts: questions.length,
    central_question_count: questions.length,
    presentation_variant_count: 0,
    training_fact_count: questions.length,
    training_presentation_count: questions.length,
    blind_fact_count: 0,
    blind_presentation_count: 0,
    total_fact_count: questions.length,
    total_presentation_count: questions.length,
    total_central_question_count: questions.length,
    total_presentation_variant_count: 0,
    total_families: { ...families },
    blind_pools: Object.fromEntries(["A", "B", "emergency"].map((pool) => [pool, {
      fact_count: 0,
      presentation_count: 0,
      families: { selection: 0, fill_choice: 0, true_false: 0 },
    }])),
    blind_delivery: {
      contract: "private-blind-artifact-v1",
      artifact_id: "competitive-v11-blind",
      artifact_revision: "b".repeat(64),
    },
    families,
    shards,
    review_index: {
      file: "banks/final-2026/review-index.json",
      bytes: files.get("banks/final-2026/review-index.json").byteLength,
      sha256: sha256(files.get("banks/final-2026/review-index.json")),
    },
  }
  manifest.build_id = artifactBuildId(manifest)

  const fixture = { root, publicRoot, bankRoot, files, manifest, reviewIndex, questions }
  await mutate(fixture)
  files.set("banks/final-2026/manifest.json", jsonBytes(manifest))
  files.set("banks/final-2026/review-index.json", jsonBytes(reviewIndex))

  for (const [path, contents] of files) {
    const destination = join(publicRoot, ...path.split("/"))
    await mkdir(dirname(destination), { recursive: true })
    await writeFile(destination, contents)
  }
  return fixture
}

async function addBlindBank(fixture) {
  const blindRoot = join(fixture.root, "private-blind")
  const files = new Map()
  const definitions = [
    ["A", "DAN1", "single_choice_contextual", "selection"],
    ["B", "DAN7", "fill_choice", "fill_choice"],
    ["emergency", "PR44", "true_false", "true_false"],
  ]
  const questions = definitions.map(([pool, chapter, family], index) => {
    const question = {
      id: `${chapter}-V11-BLIND-${pool}`,
      schema_version: "10.0",
      chapter,
      fact_id: `${chapter}-BLIND-F${index + 1}`,
      family,
      role: "central",
      blind_pool: pool,
      ai_review: {
        status: "passed",
        reviewer_type: "ai_semantic_audit",
        reviewer: "blind-reviewer",
      },
      content_sha256: sha256(`${chapter}:${pool}:content`),
    }
    question.row_content_sha256 = emittedRowHash(question)
    return question
  })
  const pools = {}
  for (const [index, [pool, chapter, , aggregateFamily]] of definitions.entries()) {
    const path = `questions/${pool}/${chapter}.json`
    const bytes = jsonBytes([questions[index]])
    files.set(path, bytes)
    pools[pool] = {
      fact_count: 1,
      presentation_count: 1,
      families: {
        selection: aggregateFamily === "selection" ? 1 : 0,
        fill_choice: aggregateFamily === "fill_choice" ? 1 : 0,
        true_false: aggregateFamily === "true_false" ? 1 : 0,
      },
      shards: [{
        chapter,
        question_count: 1,
        questions_file: path,
        bytes: bytes.byteLength,
        sha256: sha256(bytes),
      }],
    }
  }
  const reviewIndex = {
    schema_version: "10.0",
    total_reviewed: questions.length,
    human_signatures: 0,
    entries: questions.map((question) => ({
      question_id: question.id,
      content_sha256: question.row_content_sha256,
      source_content_sha256: question.content_sha256,
      decision: "passed",
      reviewer_type: "ai_semantic_audit",
      reviewer: "blind-reviewer",
    })),
  }
  files.set("review-index.json", jsonBytes(reviewIndex))
  const manifest = {
    contract: "private-blind-artifact-v1",
    artifact_id: "competitive-v11-blind",
    artifact_revision: fixture.manifest.blind_delivery.artifact_revision,
    build_id: "0".repeat(64),
    schema_version: "10.0",
    bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
    total_fact_count: questions.length,
    total_presentation_count: questions.length,
    central_question_count: questions.length,
    presentation_variant_count: 0,
    families: { selection: 1, fill_choice: 1, true_false: 1 },
    pools,
    review_index: {
      file: "review-index.json",
      bytes: files.get("review-index.json").byteLength,
      sha256: sha256(files.get("review-index.json")),
    },
  }
  files.set("manifest.json", jsonBytes(manifest))
  for (const [path, contents] of files) {
    const destination = join(blindRoot, ...path.split("/"))
    await mkdir(dirname(destination), { recursive: true })
    await writeFile(destination, contents)
  }

  fixture.manifest.blind_fact_count = 3
  fixture.manifest.blind_presentation_count = 3
  fixture.manifest.total_fact_count += 3
  fixture.manifest.total_presentation_count += 3
  fixture.manifest.total_central_question_count += 3
  fixture.manifest.total_families.single_choice_contextual = 1
  fixture.manifest.total_families.fill_choice += 1
  fixture.manifest.total_families.true_false += 1
  fixture.manifest.blind_pools = Object.fromEntries(Object.entries(pools).map(([pool, metadata]) => [pool, {
    fact_count: metadata.fact_count,
    presentation_count: metadata.presentation_count,
    families: metadata.families,
  }]))
  const buildId = artifactBuildId(fixture.manifest, manifest)
  fixture.manifest.build_id = buildId
  manifest.build_id = buildId
  files.set("manifest.json", jsonBytes(manifest))
  fixture.files.set("banks/final-2026/manifest.json", jsonBytes(fixture.manifest))
  await writeFile(join(blindRoot, "manifest.json"), files.get("manifest.json"))
  await writeFile(join(fixture.bankRoot, "manifest.json"), fixture.files.get("banks/final-2026/manifest.json"))
  return { blindRoot, files, manifest, reviewIndex, questions }
}

async function runAudit(fixture, {
  remoteOverrides = new Map(),
  rogueResources = new Map(),
  timeoutMs = 30_000,
  blindFixture = null,
  blindTransport = "both",
  blindRequirements,
} = {}) {
  const requests = []
  const server = createServer((request, response) => {
    const path = decodeURIComponent(new URL(request.url, "http://fixture.test").pathname).replace(/^\//, "")
    requests.push(path)
    const blindPath = path.startsWith("private/") ? path.slice("private/".length) : null
    const override = remoteOverrides.get(path)
    if (override?.hang) return
    if (override?.status) {
      response.writeHead(override.status).end(override.body)
      return
    }
    const body = rogueResources.get(path) ?? override ?? (blindPath ? blindFixture?.files.get(blindPath) : fixture.files.get(path))
    if (body === undefined) {
      response.writeHead(404).end()
      return
    }
    response.writeHead(200, { "content-type": "application/json" }).end(body)
  })
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve))
  server.unref()
  const { port } = server.address()
  try {
    const report = await auditLiveFinalBank({
      baseUrl: `http://127.0.0.1:${port}`,
      publicRoot: fixture.publicRoot,
      timeoutMs,
      ...(blindRequirements ? { blindRequirements } : {}),
      ...(blindFixture && blindTransport !== "root" ? { blindBaseUrl: `http://127.0.0.1:${port}/private` } : {}),
      ...(blindFixture && blindTransport !== "url" ? { blindRoot: blindFixture.blindRoot } : {}),
    })
    return { exitCode: report.failures.length ? 1 : 0, report, requests }
  } finally {
    server.close()
    server.closeAllConnections()
  }
}

async function withFixture(mutate, action) {
  const fixture = await makeBank(mutate)
  try {
    await action(fixture)
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
}

test("acepta un banco live V11 íntegro con las 18 unidades y recursos declarados", async () => {
  await withFixture(() => {}, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 0, JSON.stringify(result.report, null, 2))
    assert.deepEqual(result.report.failures, [])
    assert.equal(result.report.shards, 18)
    assert.equal(result.report.questions, 18)
    assert.equal(result.report.uniqueFacts, 18)
    assert.equal(result.report.resources, 20)
    assert.match(result.report.baseUrl, /^http:\/\/127\.0\.0\.1:/)
  })
})

test("rechaza unidades faltantes o adicionales aunque los conteos internos coincidan", async () => {
  await withFixture(async ({ manifest }) => {
    manifest.shards.pop()
    manifest.shards.push({ ...manifest.shards[0], chapter: "PR45", questions_file: "banks/final-2026/questions/PR45.json" })
  }, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("manifest:expected_units"))
  })
})

test("rechaza divergencias de conteos y familias antes de leer recursos dependientes", async () => {
  await withFixture(async ({ manifest }) => {
    manifest.gold_questions += 1
    manifest.unique_facts -= 1
    manifest.families.fill_choice += 1
  }, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("manifest:gold_questions_mismatch"))
    assert.ok(result.report.failures.includes("manifest:unique_facts_mismatch"))
    assert.ok(result.report.failures.includes("manifest:families_mismatch"))
    assert.deepEqual(result.requests, ["banks/final-2026/manifest.json"])
  })
})

test("rechaza bytes o SHA declarados incorrectos y archivos legacy locales no declarados", async () => {
  await withFixture(async ({ manifest }) => {
    manifest.shards[0].bytes += 1
    manifest.shards[0].sha256 = "f".repeat(64)
  }, async (fixture) => {
    const roguePath = "banks/final-2026/source_inventory.json"
    await writeFile(join(fixture.publicRoot, ...roguePath.split("/")), "{}")
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes(`${fixture.manifest.shards[0].questions_file}:bytes_mismatch`))
    assert.ok(result.report.failures.includes(`${fixture.manifest.shards[0].questions_file}:sha256_mismatch`))
    assert.ok(result.report.failures.includes(`${roguePath}:undeclared_local_resource`))
  })
})

test("rechaza schema distinto de 10 y contenido live diferente del artefacto local", async () => {
  await withFixture(async ({ reviewIndex }) => {
    reviewIndex.schema_version = "11.0"
  }, async (fixture) => {
    const shardPath = fixture.manifest.shards[1].questions_file
    const result = await runAudit(fixture, {
      remoteOverrides: new Map([[shardPath, Buffer.from("[]\n")]]),
    })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("review-index:schema_version"))
    assert.ok(result.report.failures.includes(`${shardPath}:content_mismatch`))
  })
})

test("devuelve un reporte de gate en vez de caerse ante un shard malformado", async () => {
  await withFixture(async ({ manifest }) => {
    manifest.shards[0] = null
  }, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("manifest:expected_units"))
  })
})

test("falla cerrado si falta un campo obligatorio del manifiesto", async () => {
  await withFixture(async ({ manifest }) => {
    delete manifest.bank_id
    delete manifest.training_fact_count
  }, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("manifest:missing_bank_id"))
    assert.ok(result.report.failures.includes("manifest:missing_training_fact_count"))
  })
})

test("exige A/B/emergency y las tres familias blind aunque sus conteos sean cero", async () => {
  await withFixture(async ({ manifest }) => {
    delete manifest.blind_pools.emergency
    delete manifest.blind_pools.A.families.true_false
  }, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("manifest:blind_pools_schema"))
    assert.ok(result.report.failures.includes("manifest:blind_pool_A_families_schema"))
  })
})

test("compara bytes crudos: CRLF remoto no equivale a LF local", async () => {
  await withFixture(() => {}, async (fixture) => {
    const shardPath = fixture.manifest.shards[0].questions_file
    const crlf = Buffer.from(fixture.files.get(shardPath).toString("utf8").replaceAll("\n", "\r\n"))
    const result = await runAudit(fixture, { remoteOverrides: new Map([[shardPath, crlf]]) })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes(`${shardPath}:content_mismatch`))
    assert.ok(result.report.failures.includes(`${shardPath}:bytes_mismatch`))
    assert.ok(result.report.failures.includes(`${shardPath}:sha256_mismatch`))
  })
})

test("rechaza review-index incompleto o incoherente con ai_review", async () => {
  await withFixture(async ({ reviewIndex, questions }) => {
    reviewIndex.human_signatures = 1
    reviewIndex.entries[0].reviewer = ""
    reviewIndex.entries[1].reviewer_type = "human"
    questions[1].ai_review.reviewer_type = "ai_semantic_audit"
  }, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("review-index:human_signatures"))
    assert.ok(result.report.failures.includes(`${fixture.questions[0].id}:invalid_reviewer`))
    assert.ok(result.report.failures.includes(`${fixture.questions[1].id}:ai_review_mismatch`))
  })
})

test("aborta después de un manifiesto 404 o JSON malformado", async (t) => {
  await t.test("404", async () => {
    await withFixture(() => {}, async (fixture) => {
      const result = await runAudit(fixture, {
        remoteOverrides: new Map([["banks/final-2026/manifest.json", { status: 404 }]]),
      })
      assert.equal(result.exitCode, 1)
      assert.deepEqual(result.requests, ["banks/final-2026/manifest.json"])
      assert.ok(result.report.failures.includes("banks/final-2026/manifest.json:http_404"))
    })
  })
  await t.test("JSON malformado", async () => {
    await withFixture(() => {}, async (fixture) => {
      const result = await runAudit(fixture, {
        remoteOverrides: new Map([["banks/final-2026/manifest.json", Buffer.from("{")]]),
      })
      assert.equal(result.exitCode, 1)
      assert.deepEqual(result.requests, ["banks/final-2026/manifest.json"])
      assert.ok(result.report.failures.includes("banks/final-2026/manifest.json:invalid_json"))
    })
  })
})

test("reporta timeout/abort sin continuar con recursos dependientes", async () => {
  await withFixture(() => {}, async (fixture) => {
    const result = await runAudit(fixture, {
      timeoutMs: 20,
      remoteOverrides: new Map([["banks/final-2026/manifest.json", { hang: true }]]),
    })
    assert.equal(result.exitCode, 1)
    assert.deepEqual(result.requests, ["banks/final-2026/manifest.json"])
    assert.ok(result.report.failures.includes("banks/final-2026/manifest.json:timeout_or_abort"))
  })
})

test("no lee ni solicita una ruta traversal declarada por un manifiesto hostil", async () => {
  await withFixture(async ({ manifest }) => {
    manifest.shards[0] = {
      ...manifest.shards[0],
      chapter: "../../outside",
      questions_file: "banks/final-2026/questions/../../outside.json",
    }
  }, async (fixture) => {
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.deepEqual(result.requests, ["banks/final-2026/manifest.json"])
    assert.ok(result.report.failures.includes("manifest:expected_units"))
  })
})

test("la allowlist local recursiva rechaza archivos y subdirectorios extra", async () => {
  await withFixture(() => {}, async (fixture) => {
    const extra = join(fixture.bankRoot, "unexpected", "nested.bin")
    await mkdir(dirname(extra), { recursive: true })
    await writeFile(extra, "extra")
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("banks/final-2026/unexpected/nested.bin:undeclared_local_resource"))
  })
})

test("dos auditorías concurrentes mantienen aislados URL, raíz y fallos", async () => {
  const first = await makeBank()
  const second = await makeBank()
  try {
    const [left, right] = await Promise.all([runAudit(first), runAudit(second)])
    assert.equal(left.exitCode, 0, JSON.stringify(left.report))
    assert.equal(right.exitCode, 0, JSON.stringify(right.report))
    assert.notEqual(left.report.baseUrl, right.report.baseUrl)
  } finally {
    await Promise.all([
      rm(first.root, { recursive: true, force: true }),
      rm(second.root, { recursive: true, force: true }),
    ])
  }
})

test("el gate público valida metadatos blind sin solicitar el artefacto privado", async () => {
  const fixture = await makeBank()
  try {
    await addBlindBank(fixture)
    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 0, JSON.stringify(result.report, null, 2))
    assert.equal(result.report.questions, 18)
    assert.equal(result.report.privateAudit, "NOT_RUN")
    assert.equal(result.report.blindQuestions, null)
    assert.ok(result.requests.every((path) => !path.startsWith("private/")))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("con raíz y URL blind explícitas audita entrenamiento y reserva como corpus conjunto", async () => {
  const fixture = await makeBank()
  try {
    const blindFixture = await addBlindBank(fixture)
    const result = await runAudit(fixture, { blindFixture })
    assert.equal(result.exitCode, 0, JSON.stringify(result.report, null, 2))
    assert.equal(result.report.questions, 21)
    assert.equal(result.report.uniqueFacts, 21)
    assert.equal(result.report.blindQuestions, 3)
    assert.equal(result.report.privateAudit, "LOCAL_AND_REMOTE")
    assert.notEqual(fixture.manifest.build_id, fixture.manifest.blind_delivery.artifact_revision)
    assert.ok(result.requests.includes("private/manifest.json"))
    assert.ok(result.requests.includes("private/review-index.json"))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("rechaza una fila emitida alterada aunque shard y ledger conserven hashes internamente coherentes", async () => {
  const fixture = await makeBank()
  try {
    const shard = fixture.manifest.shards[0]
    const path = shard.questions_file
    const rows = JSON.parse(fixture.files.get(path).toString("utf8"))
    rows[0].tampered_after_emit = true
    const bytes = jsonBytes(rows)
    fixture.files.set(path, bytes)
    shard.bytes = bytes.byteLength
    shard.sha256 = sha256(bytes)
    fixture.manifest.build_id = artifactBuildId(fixture.manifest)
    fixture.files.set("banks/final-2026/manifest.json", jsonBytes(fixture.manifest))
    await writeFile(join(fixture.publicRoot, ...path.split("/")), bytes)
    await writeFile(join(fixture.bankRoot, "manifest.json"), fixture.files.get("banks/final-2026/manifest.json"))

    const result = await runAudit(fixture)
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes(`${rows[0].id}:row_content_sha256_mismatch`))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("recomputa el build_id conjunto cuando existe artefacto privado", async () => {
  const fixture = await makeBank()
  try {
    const blindFixture = await addBlindBank(fixture)
    fixture.manifest.shards.reverse()
    fixture.files.set("banks/final-2026/manifest.json", jsonBytes(fixture.manifest))
    await writeFile(join(fixture.bankRoot, "manifest.json"), fixture.files.get("banks/final-2026/manifest.json"))

    const result = await runAudit(fixture, { blindFixture })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("manifest:build_id_descriptor_mismatch"))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("el artefacto privado falla por integridad, review incompleto o colisión con training", async () => {
  const fixture = await makeBank()
  try {
    const blindFixture = await addBlindBank(fixture)
    const firstShard = blindFixture.manifest.pools.A.shards[0]
    firstShard.sha256 = "f".repeat(64)
    blindFixture.questions[0].fact_id = fixture.questions[0].fact_id
    blindFixture.reviewIndex.entries[0].reviewer = ""
    blindFixture.files.set(firstShard.questions_file, jsonBytes([blindFixture.questions[0]]))
    blindFixture.files.set("manifest.json", jsonBytes(blindFixture.manifest))
    blindFixture.files.set("review-index.json", jsonBytes(blindFixture.reviewIndex))
    await writeFile(join(blindFixture.blindRoot, "manifest.json"), blindFixture.files.get("manifest.json"))
    await writeFile(join(blindFixture.blindRoot, "review-index.json"), blindFixture.files.get("review-index.json"))
    await writeFile(join(blindFixture.blindRoot, ...firstShard.questions_file.split("/")), blindFixture.files.get(firstShard.questions_file))
    const result = await runAudit(fixture, { blindFixture })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes(`${firstShard.questions_file}:sha256_mismatch`))
    assert.ok(result.report.failures.includes(`${blindFixture.questions[0].id}:invalid_reviewer`))
    assert.ok(result.report.failures.includes(`${fixture.questions[0].fact_id}:training_blind_fact_collision`))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("un manifiesto privado malformado falla cerrado sin lanzar TypeError", async () => {
  const fixture = await makeBank()
  try {
    const blindFixture = await addBlindBank(fixture)
    blindFixture.manifest.pools.A.families = null
    blindFixture.files.set("manifest.json", jsonBytes(blindFixture.manifest))
    await writeFile(join(blindFixture.blindRoot, "manifest.json"), blindFixture.files.get("manifest.json"))
    const result = await runAudit(fixture, { blindFixture })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("blind-manifest:pool_A_families:invalid_counts"))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("el manifiesto privado exige roles centrales y las tres familias agregadas", async () => {
  const fixture = await makeBank()
  try {
    const blindFixture = await addBlindBank(fixture)
    delete blindFixture.manifest.central_question_count
    delete blindFixture.manifest.families.selection
    blindFixture.files.set("manifest.json", jsonBytes(blindFixture.manifest))
    await writeFile(join(blindFixture.blindRoot, "manifest.json"), blindFixture.files.get("manifest.json"))
    const result = await runAudit(fixture, { blindFixture })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("blind-manifest:central_question_count"))
    assert.ok(result.report.failures.includes("blind-manifest:families_schema"))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("reporta 404 y JSON malformado en review-index y shards requeridos", async (t) => {
  for (const [label, path] of [
    ["review 404", "banks/final-2026/review-index.json"],
    ["shard 404", "banks/final-2026/questions/DAN1.json"],
  ]) {
    await t.test(label, async () => {
      await withFixture(() => {}, async (fixture) => {
        const result = await runAudit(fixture, { remoteOverrides: new Map([[path, { status: 404 }]]) })
        assert.equal(result.exitCode, 1)
        assert.ok(result.report.failures.includes(`${path}:http_404`))
      })
    })
  }
  for (const [label, path] of [
    ["review JSON", "banks/final-2026/review-index.json"],
    ["shard JSON", "banks/final-2026/questions/DAN1.json"],
  ]) {
    await t.test(label, async () => {
      await withFixture(() => {}, async (fixture) => {
        const result = await runAudit(fixture, { remoteOverrides: new Map([[path, Buffer.from("{")]]) })
        assert.equal(result.exitCode, 1)
        assert.ok(result.report.failures.includes(`${path}:invalid_json`))
      })
    })
  }
})

test("el artefacto blind puede auditarse sólo desde raíz privada o sólo desde URL explícita", async () => {
  for (const blindTransport of ["root", "url"]) {
    const fixture = await makeBank()
    try {
      const blindFixture = await addBlindBank(fixture)
      const result = await runAudit(fixture, { blindFixture, blindTransport })
      assert.equal(result.exitCode, 0, `${blindTransport}: ${JSON.stringify(result.report)}`)
      assert.equal(result.report.blindQuestions, 3)
      assert.equal(result.report.privateAudit, blindTransport === "root" ? "LOCAL" : "REMOTE")
    } finally {
      await rm(fixture.root, { recursive: true, force: true })
    }
  }
})

test("el gate release oficial rechaza metadata pública coherente pero inferior a 100/100/50", async () => {
  const fixture = await makeBank()
  try {
    await addBlindBank(fixture)
    const release = {
      A: { fact_count: 100, families: { selection: 45, fill_choice: 30, true_false: 25 } },
      B: { fact_count: 100, families: { selection: 45, fill_choice: 30, true_false: 25 } },
      emergency: { fact_count: 50, families: { selection: 23, fill_choice: 15, true_false: 12 } },
    }
    const result = await runAudit(fixture, { blindRequirements: release })
    assert.equal(result.exitCode, 1)
    assert.equal(result.report.privateAudit, "NOT_RUN")
    assert.equal(result.report.blindQuestions, null)
    assert.ok(result.report.failures.includes("release:A:fact_count:expected_100:actual_1"))
    assert.ok(result.report.failures.includes("release:B:family_selection:expected_45:actual_0"))
    assert.ok(result.requests.every((path) => !path.startsWith("private/")))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("la API acepta requisitos blind custom que coinciden con la metadata pública", async () => {
  const fixture = await makeBank()
  try {
    await addBlindBank(fixture)
    const custom = Object.fromEntries(Object.entries(fixture.manifest.blind_pools).map(([pool, metadata]) => [pool, {
      fact_count: metadata.fact_count,
      families: metadata.families,
    }]))
    const result = await runAudit(fixture, { blindRequirements: custom })
    assert.equal(result.exitCode, 0, JSON.stringify(result.report, null, 2))
    assert.equal(result.report.privateAudit, "NOT_RUN")
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("un path traversal privado aborta antes de leer o solicitar shards", async () => {
  const fixture = await makeBank()
  try {
    const blindFixture = await addBlindBank(fixture)
    blindFixture.manifest.pools.A.shards[0].questions_file = "questions/A/../../secret.json"
    blindFixture.files.set("manifest.json", jsonBytes(blindFixture.manifest))
    await writeFile(join(blindFixture.blindRoot, "manifest.json"), blindFixture.files.get("manifest.json"))
    const result = await runAudit(fixture, { blindFixture })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("A:DAN1:questions_file"))
    assert.equal(result.requests.filter((path) => path.startsWith("private/")).join(","), "private/manifest.json")
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})

test("la allowlist privada recursiva rechaza cualquier recurso extra", async () => {
  const fixture = await makeBank()
  try {
    const blindFixture = await addBlindBank(fixture)
    const extra = join(blindFixture.blindRoot, "questions", "A", "nested", "secret.bin")
    await mkdir(dirname(extra), { recursive: true })
    await writeFile(extra, "secret")
    const result = await runAudit(fixture, { blindFixture })
    assert.equal(result.exitCode, 1)
    assert.ok(result.report.failures.includes("questions/A/nested/secret.bin:undeclared_local_resource"))
  } finally {
    await rm(fixture.root, { recursive: true, force: true })
  }
})
