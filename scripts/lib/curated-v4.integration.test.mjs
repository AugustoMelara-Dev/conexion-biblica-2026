import { readFile } from "node:fs/promises"
import { mkdtemp, readdir, readFile as readTempFile, rm, writeFile } from "node:fs/promises"
import { join } from "node:path"
import { tmpdir } from "node:os"
import { describe, expect, it } from "vitest"
import { buildCuratedV4, writePayloadsAtomically } from "../build-curated-v4.mjs"

const master = JSON.parse(await readFile("Banco_Maestro_CB2026.json", "utf8"))
const result = buildCuratedV4(master)

describe("integración del Banco Curado V4", () => {
  it("clasifica cada pregunta maestra exactamente una vez", () => {
    expect(result.audit.summary.total).toBe(3558)
    expect(result.audit.summary.approved).toBe(2011)
    expect(result.audit.summary.repaired).toBe(1502)
    expect(result.audit.summary.rejected).toBe(45)
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
      expect((question.question.match(/«/g) ?? []).length).toBe((question.question.match(/»/g) ?? []).length)
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
})
