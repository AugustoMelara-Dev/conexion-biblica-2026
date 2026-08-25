import { describe, expect, it } from "vitest"
import { resumeQuestionIndex } from "@/domain/session-resume"

describe("reanudación de ronda", () => {
  it("avanza sobre una pregunta ya registrada antes de recargar", () => {
    expect(resumeQuestionIndex(6, 7, 50)).toBe(7)
  })

  it("conserva el cursor cuando todavía no existe respuesta", () => {
    expect(resumeQuestionIndex(6, 6, 50)).toBe(6)
  })
})
