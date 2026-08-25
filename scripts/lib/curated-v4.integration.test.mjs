import { readFile } from "node:fs/promises"
import { mkdtemp, readdir, readFile as readTempFile, rename as renameFile, rm, unlink as unlinkFile, writeFile } from "node:fs/promises"
import { join } from "node:path"
import { tmpdir } from "node:os"
import { describe, expect, it } from "vitest"
import { auditCuratedV4, buildCuratedV4, writePayloadsAtomically } from "../build-curated-v4.mjs"

const master = JSON.parse(await readFile("Banco_Maestro_CB2026.json", "utf8"))
const result = buildCuratedV4(master)

describe("integración del Banco Curado V4", () => {
  it("clasifica cada pregunta maestra exactamente una vez", () => {
    expect(result.audit.summary.total).toBe(3558)
    expect(result.audit.summary.approved).toBe(1803)
    expect(result.audit.summary.repaired).toBe(1417)
    expect(result.audit.summary.rejected).toBe(338)
    expect(result.audit.countsByIssue.VISIBLE_TEXT_QUOTES).toBe(22)
    expect(result.audit.summary.approved + result.audit.summary.repaired + result.audit.summary.rejected).toBe(3558)
    expect(result.audit.summary.blockers).toBe(0)
    expect(result.banks.daniel.questions.every((q) => q.source.work === "Daniel")).toBe(true)
    expect(result.banks.prophets.questions.every((q) => q.source.work === "Profetas y Reyes")).toBe(true)
  })

  it("emite bancos V4 trazables y sin estados rechazados", () => {
    expect(result.banks.daniel.schemaVersion).toBe("1.0")
    expect(result.banks.prophets.schemaVersion).toBe("1.0")
    expect(result.banks.daniel.bank.profileId).toBe("curated-v4")
    expect(result.banks.prophets.bank.profileId).toBe("curated-v4")
    const questions = [...result.banks.daniel.questions, ...result.banks.prophets.questions]
    expect(questions).toHaveLength(3220)
    expect(new Set(questions.map((q) => q.id)).size).toBe(questions.length)
    expect(questions.every((q) => ["APPROVED", "REPAIRED"].includes(q.metadata.curationStatus))).toBe(true)
    expect(questions.every((q) => q.metadata.masterQuestionId && q.source.reference && Number.isInteger(q.source.chapter))).toBe(true)
  })

  it("aplica el ruling a prompts exactos y conserva una decisión por entrada", () => {
    const questions = [...result.banks.daniel.questions, ...result.banks.prophets.questions]
    const normalizePrompt = (value) => String(value ?? "").normalize("NFKC").replace(/\s+/gu, " ").trim()
    const prompts = questions.map((question) => normalizePrompt(question.question))

    expect(new Set(prompts).size).toBe(prompts.length)
    expect(result.audit.decisions).toHaveLength(3558)
    expect(result.audit.decisions.some((decision) => decision.issues.includes("DUPLICATE_PROMPT_NON_CANONICAL"))).toBe(true)
    expect(result.audit.decisions.some((decision) => decision.issues.includes("DUPLICATE_PROMPT_CONFLICT"))).toBe(true)
  })

  it("rechaza todo un grupo cuando los prompts exactos tienen respuestas distintas", () => {
    const conflictQuestions = master.questions.filter((question) => question.pregunta === "¿Cómo se puso el rey?").slice(0, 2)
    const conflictResult = buildCuratedV4({ questions: structuredClone(conflictQuestions) })

    expect(conflictResult.audit.summary.rejected).toBe(2)
    expect(conflictResult.audit.decisions.every((decision) => decision.status === "REJECTED")).toBe(true)
    expect(conflictResult.audit.decisions.every((decision) => decision.issues.includes("DUPLICATE_PROMPT_CONFLICT"))).toBe(true)
  })

  it("conserva opciones y modo de respuesta original y curado", () => {
    const repaired = result.audit.decisions.find((decision) => decision.status === "REPAIRED")

    expect(repaired).toMatchObject({
      originalOptions: expect.any(Object),
      curatedOptions: expect.any(Array),
      originalAnswerMode: expect.any(String),
      curatedAnswerMode: expect.any(String),
      curatedAnswerText: expect.any(String),
    })
  })

  it("conserva la explicación original de una pregunta APPROVED", () => {
    const raw = master.questions.find((question) => question.QUESTION_ID === "GEN-000001")
    const decision = result.audit.decisions.find((item) => item.masterQuestionId === raw?.QUESTION_ID)

    expect(decision?.status).toBe("APPROVED")
    expect(decision?.curatedExplanation).toBe(raw?.explicacion)
  })

  it("audita duplicados exactos introducidos en un banco", () => {
    const banks = structuredClone(result.banks)
    banks.daniel.questions[1] = { ...banks.daniel.questions[1], question: banks.daniel.questions[0].question }

    const audit = auditCuratedV4(banks, master, result.banks)

    expect(audit.summary.blockers).toBeGreaterThan(0)
    expect(audit.findings.some((finding) => finding.code === "DUPLICATE_EXACT_PROMPT")).toBe(true)
  })

  it("audita que el resumen de curación de cada banco coincida con sus decisiones", () => {
    const banks = structuredClone(result.banks)
    banks.daniel.bank.curationSummary.approved += 1

    const audit = auditCuratedV4(banks, master, result.banks)

    expect(audit.findings.some((finding) => finding.code === "CURATION_SUMMARY_MISMATCH")).toBe(true)
  })

  it("no deja lenguaje técnico ni correcciones pendientes", () => {
    const questions = [...result.banks.daniel.questions, ...result.banks.prophets.questions]
    expect(questions.some((q) => /segunda formulación|fase\s*[1-4]|cobertura auditada|requiere corrección/i.test(`${q.question} ${q.explanation} ${q.correctAnswerText ?? ""}`))).toBe(false)
  })

  it("conserva respuestas resolubles, referencias y capítulos del maestro", () => {
    const masterById = new Map(master.questions.map((q) => [q.QUESTION_ID, q]))
    const questions = [...result.banks.daniel.questions, ...result.banks.prophets.questions]
    for (const question of questions) {
      const source = masterById.get(question.metadata.masterQuestionId)
      expect(source).toBeDefined()
      expect(question.source.reference).toBe(source.fuente)
      expect(question.source.chapter).toBe(Number(source.capitulo))
      expect(question.correctAnswer.length).toBeGreaterThan(0)
      expect(question.options.some((option) => question.correctAnswer.includes(option.id))).toBe(true)
    }
  })

  it("balancea todos los textos visibles y la composición pregunta-respuesta", () => {
    const questions = [...result.banks.daniel.questions, ...result.banks.prophets.questions]
    const quoteDifference = (text) => (String(text ?? "").match(/«/g) ?? []).length - (String(text ?? "").match(/»/g) ?? []).length
    for (const question of questions) {
      const answerText = question.correctAnswerText ?? question.correctAnswer.map((id) => question.options.find((option) => option.id === id)?.text ?? "").join(" | ")
      const visibleTexts = [question.question, question.explanation, question.memoryCue, question.correctAnswerText, ...question.options.map((option) => option.text)]
      expect(visibleTexts.every((text) => quoteDifference(text) === 0), question.id).toBe(true)
      expect(quoteDifference(`${question.question} ${answerText}`), question.id).toBe(0)
    }
  })

  it("repite la sustitución segura sin dejar temporales", async () => {
    const directory = await mkdtemp(join(tmpdir(), "curated-v4-"))
    const target = join(directory, "bank.json")
    try {
      await writeFile(target, JSON.stringify({ version: 0 }), "utf8")
      await writePayloadsAtomically([{ target, value: { version: 1 } }])
      await writePayloadsAtomically([{ target, value: { version: 2 } }])
      expect(JSON.parse(await readTempFile(target, "utf8"))).toEqual({ version: 2 })
      expect(await readdir(directory)).toEqual(["bank.json"])
    } finally {
      await rm(directory, { recursive: true, force: true })
    }
  })

  it("revierte todos los destinos si falla un rename de instalación", async () => {
    const directory = await mkdtemp(join(tmpdir(), "curated-v4-rollback-"))
    const first = join(directory, "first.json")
    const second = join(directory, "second.json")
    try {
      await writeFile(first, "old-first", "utf8")
      await writeFile(second, "old-second", "utf8")
      let renameCalls = 0
      const failingRename = async (source, target) => {
        renameCalls += 1
        if (renameCalls === 4) throw new Error("simulated rename failure")
        return renameFile(source, target)
      }
      await expect(writePayloadsAtomically([
        { target: first, value: "new-first" },
        { target: second, value: "new-second" },
      ], { fsOps: { rename: failingRename } })).rejects.toThrow("simulated rename failure")
      expect(await readTempFile(first, "utf8")).toBe("old-first")
      expect(await readTempFile(second, "utf8")).toBe("old-second")
      expect(await readdir(directory)).toEqual(["first.json", "second.json"])
    } finally {
      await rm(directory, { recursive: true, force: true })
    }
  })

  it("tolera un fallo transitorio de unlink y no deja respaldos", async () => {
    const directory = await mkdtemp(join(tmpdir(), "curated-v4-cleanup-"))
    const first = join(directory, "first.json")
    const second = join(directory, "second.json")
    try {
      await writeFile(first, "old-first", "utf8")
      await writeFile(second, "old-second", "utf8")
      let unlinkCalls = 0
      const flakyUnlink = async (path) => {
        unlinkCalls += 1
        if (unlinkCalls === 1) {
          const error = new Error("simulated unlink failure")
          error.code = "EPERM"
          throw error
        }
        return unlinkFile(path)
      }
      await writePayloadsAtomically([
        { target: first, value: "new-first" },
        { target: second, value: "new-second" },
      ], { fsOps: { unlink: flakyUnlink } })
      expect(unlinkCalls).toBeGreaterThan(0)
      expect(await readTempFile(first, "utf8")).toBe("new-first")
      expect(await readTempFile(second, "utf8")).toBe("new-second")
      expect(await readdir(directory)).toEqual(["first.json", "second.json"])
    } finally {
      await rm(directory, { recursive: true, force: true })
    }
  })

  it("expone un commit válido si unlink y rm fallan permanentemente", async () => {
    const directory = await mkdtemp(join(tmpdir(), "curated-v4-permanent-cleanup-"))
    const first = join(directory, "first.json")
    const second = join(directory, "second.json")
    try {
      await writeFile(first, "old-first", "utf8")
      await writeFile(second, "old-second", "utf8")
      const permanentFailure = async () => {
        const error = new Error("simulated permanent cleanup failure")
        error.code = "EPERM"
        throw error
      }
      const failure = await writePayloadsAtomically([
        { target: first, value: "new-first" },
        { target: second, value: "new-second" },
      ], { fsOps: { unlink: permanentFailure, rm: permanentFailure } }).catch((error) => error)

      expect(failure).toMatchObject({ name: "AtomicCommitCleanupError", committed: true })
      expect(failure.remainingBackups).toHaveLength(2)
      expect(failure.cleanupErrors).toHaveLength(2)
      expect(failure.cleanupErrors.every(({ code }) => code === "EPERM")).toBe(true)
      expect(await readTempFile(first, "utf8")).toBe("new-first")
      expect(await readTempFile(second, "utf8")).toBe("new-second")
      const files = await readdir(directory)
      expect(files.filter((file) => file.includes(".bak-")).length).toBe(2)
      expect(files.some((file) => file.endsWith(".tmp"))).toBe(false)
    } finally {
      await rm(directory, { recursive: true, force: true })
    }
  })
})
