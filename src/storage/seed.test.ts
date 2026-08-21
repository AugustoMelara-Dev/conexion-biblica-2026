import { describe, expect, it } from "vitest"
import { createBankFromRaw } from "@/storage/seed"

describe("normalización de bancos importados", () => {
  it("conserva el raw y asigna una clave estable a cada pregunta", () => {
    const raw = {
      schemaVersion: "1.0",
      bank: { sourceWork: "Daniel", sourceVersion: "RVR95", chapter: "3" },
      audit: { generated: true },
      questions: [{
        id: "D03-0001",
        type: "single_choice",
        difficulty: 1,
        source: { work: "Daniel", version: "RVR95", chapter: 3, reference: "Daniel 3:1" },
        tags: ["detalle"],
        factKey: "fact-1",
        question: "¿Pregunta?",
        options: [{ id: "A", text: "A" }, { id: "B", text: "B" }],
        correctAnswer: ["A"],
      }],
    }
    const bank = createBankFromRaw(raw, "Daniel3.json", 7)
    expect(bank.bankId).toBe("bank-daniel3-json")
    expect(bank.questions[0].bankId).toBe(bank.bankId)
    expect(bank.questions[0].id).toBe("D03-0001")
    expect(bank.raw).toEqual(raw)
  })
})
