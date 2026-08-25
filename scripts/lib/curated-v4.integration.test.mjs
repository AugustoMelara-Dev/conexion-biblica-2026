import { readFile } from "node:fs/promises"
import { mkdtemp, readdir, readFile as readTempFile, rename as renameFile, rm, unlink as unlinkFile, writeFile } from "node:fs/promises"
import { join } from "node:path"
import { tmpdir } from "node:os"
import { describe, expect, it } from "vitest"
import { buildCuratedV4, writePayloadsAtomically } from "../build-curated-v4.mjs"

const master = JSON.parse(await readFile("Banco_Maestro_CB2026.json", "utf8"))
const result = buildCuratedV4(master)

describe("integración del Banco Curado V4", () => {
  it("clasifica cada pregunta maestra exactamente una vez", () => {
    expect(result.audit.summary.total).toBe(3558)
    expect(result.audit.summary.approved).toBe(2002)
    expect(result.audit.summary.repaired).toBe(1511)
    expect(result.audit.summary.rejected).toBe(45)
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
    expect(questions).toHaveLength(3513)
    expect(new Set(questions.map((q) => q.id)).size).toBe(questions.length)
    expect(questions.every((q) => ["APPROVED", "REPAIRED"].includes(q.metadata.curationStatus))).toBe(true)
    expect(questions.every((q) => q.metadata.masterQuestionId && q.source.reference && Number.isInteger(q.source.chapter))).toBe(true)
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
})
