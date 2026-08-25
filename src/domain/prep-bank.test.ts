import { existsSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, it } from "vitest"
import { validateBank } from "@/domain/validation"
import { createBankFromRaw } from "@/storage/seed"

const files = ["v3_daniel.json", "v3_profetas_reyes.json"]

function readBank(file: string) {
  const path = join(process.cwd(), "public", "banks", file)
  if (!existsSync(path)) return null
  return JSON.parse(readFileSync(path, "utf8")) as {
    questions: Array<{
      id: string
      factKey: string
      question: string
      explanation: string
      trapReason: string
      memoryCue: string
      verified: boolean
      integrative?: boolean
      options: Array<{ id: string; text: string }>
      correctAnswer: string[]
      source: { work: string; chapter: number }
    }>
  }
}

describe("suplemento de preparación V3", () => {
  it("carga exactamente 500 preguntas con las cuotas aprobadas", () => {
    const banks = files.map(readBank)
    expect(banks.every(Boolean)).toBe(true)

    const questions = banks.flatMap((bank, index) => {
      if (!bank) return []
      expect(validateBank(bank, files[index]).valid).toBe(true)
      expect(bank.questions.every((question) =>
        question.factKey.length > 0 &&
        question.explanation.length > 0 &&
        question.trapReason.length > 0 &&
        question.memoryCue.length > 0 &&
        question.verified,
      )).toBe(true)
      return bank.questions
    })
    const scopedQuestions = questions.filter((question) => !question.integrative)
    const keys = scopedQuestions.map((question) => `${question.source.work}:${question.source.chapter}`)
    const counts = new Map<string, number>()
    keys.forEach((key) => counts.set(key, (counts.get(key) ?? 0) + 1))

    expect(questions).toHaveLength(500)
    expect(new Set(questions.map((question) => question.id)).size).toBe(500)
    expect(new Set(questions.map((question) => question.question.trim().toLocaleLowerCase("es"))).size).toBe(500)
    expect(questions.filter((question) => question.integrative)).toHaveLength(2)
    for (let chapter = 1; chapter <= 12; chapter += 1) {
      expect(counts.get(`Daniel:${chapter}`)).toBe(28)
    }
    for (let chapter = 39; chapter <= 44; chapter += 1) {
      expect(counts.get(`Profetas y Reyes:${chapter}`)).toBe(27)
    }

    const familySizes = new Map<string, number>()
    questions.forEach((question) => familySizes.set(question.factKey, (familySizes.get(question.factKey) ?? 0) + 1))
    expect([...familySizes.values()].filter((size) => size > 1).length).toBeGreaterThanOrEqual(100)
  })

  it("normaliza el suplemento como perfil V3 y conserva la pista de memoria", () => {
    const raw = readBank(files[0])
    expect(raw).not.toBeNull()
    const bank = createBankFromRaw(raw as Record<string, unknown>, files[0], 7)

    expect(bank.bankProfileId).toBe("prep-v3")
    expect(bank.questions[0].bankProfileId).toBe("prep-v3")
    expect(bank.questions[0].memoryCue).toBeTruthy()
  })
})
