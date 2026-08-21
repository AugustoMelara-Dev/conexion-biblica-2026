import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, it } from "vitest"
import { adaptMasterBank, validateMasterBank } from "@/domain/master-bank"
import { isCorrectAnswer } from "@/domain/evaluation"

const master = JSON.parse(
  readFileSync(join(process.cwd(), "Banco_Maestro_CB2026.json"), "utf8"),
) as unknown

describe("Banco Maestro V2", () => {
  it("valida los conteos canónicos y todos los identificadores", () => {
    const result = validateMasterBank(master)

    expect(result.errors).toEqual([])
    expect(result.counts).toEqual({
      total: 3558,
      daniel: 2211,
      prophetsAndKings: 1347,
      historical: 888,
      generated: 2670,
      uniqueIds: 3558,
      correctedHistorical: 46,
    })
  })

  it("normaliza las 3558 preguntas sin perder identidad, fuente ni metadata", () => {
    const bank = adaptMasterBank(master, 123)

    expect(bank.bankId).toBe("master-v2")
    expect(bank.schemaVersion).toBe("2.0")
    expect(bank.questions).toHaveLength(3558)
    expect(new Set(bank.questions.map((question) => question.id)).size).toBe(3558)
    expect(bank.questions.every((question) => question.bankId === "master-v2")).toBe(true)
    expect(bank.questions.every((question) => question.source.reference.length > 0)).toBe(true)
    expect(bank.questions.every((question) => question.correctAnswerText?.length)).toBe(true)
    expect(bank.questions.every((question) => Array.isArray(question.factKeys))).toBe(true)
    expect(bank.questions.every((question) => question.metadata?.QUESTION_ID === question.id)).toBe(true)
  })

  it("conserva respuestas corregidas como texto canónico sin señalar una opción falsa", () => {
    const bank = adaptMasterBank(master)
    const corrected = bank.questions.filter(
      (question) => question.metadata?.historical_status === "CORRECTED",
    )
    const sample = corrected.find((question) => question.id === "HIST-0017")

    expect(corrected).toHaveLength(46)
    expect(sample).toMatchObject({
      answerMode: "canonical_text",
      correctAnswer: [],
      correctAnswerText: "Casi una hora",
      originalDifficulty: "HISTORICAL_UNRATED",
      difficultyBand: "UNRATED",
    })
    expect(sample?.options.map((option) => option.text)).toContain("Una hora y media")
  })

  it("mapea tipos y dificultad sin destruir los valores originales", () => {
    const bank = adaptMasterBank(master)
    const types = new Set(bank.questions.map((question) => question.type))
    const bands = new Set(bank.questions.map((question) => question.difficultyBand))

    expect(types).toEqual(new Set(["single_choice", "true_false", "fill_blank"]))
    expect(bands).toEqual(new Set(["MEDIUM", "HARD", "EXPERT", "UNRATED"]))
    expect(bank.questions.find((question) => question.metadata?.tipo === "RESPUESTA CORTA"))
      .toMatchObject({ type: "fill_blank", answerMode: "canonical_text" })
  })

  it("evalúa la respuesta textual canónica sin forzar una opción histórica falsa", () => {
    const question = adaptMasterBank(master).questions.find((item) => item.id === "HIST-0017")!

    expect(isCorrectAnswer(question, "  CASI una hora ")).toBe(true)
    expect(isCorrectAnswer(question, "Una hora y media")).toBe(false)
  })
})
