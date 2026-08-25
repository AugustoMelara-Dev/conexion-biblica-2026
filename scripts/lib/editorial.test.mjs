import { describe, expect, it } from "vitest"
import { naturalizePrompt } from "./editorial.mjs"

describe("edición de variantes V3", () => {
  it("elimina el lenguaje interno de generación sin tocar el hecho evaluado", () => {
    const original = "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «Al cabo de diez días, los jóvenes __________»."
    expect(naturalizePrompt(original)).toBe("Completa la afirmación: Al cabo de diez días, los jóvenes __________.")
  })

  it("conserva una cita interna sin duplicar las comillas exteriores", () => {
    const original = "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «El rey reiteró: «Decidme, pues, el sueño __________»»."
    expect(naturalizePrompt(original)).toBe("Completa la afirmación: El rey reiteró: «Decidme, pues, el sueño __________».")
  })

  it("descarta una comilla de cierre heredada que no tiene apertura", () => {
    const original = "¿Qué dato completa correctamente esta segunda formulación de alto riesgo? «Darío llamó __________»»."
    expect(naturalizePrompt(original)).toBe("Completa la afirmación: Darío llamó __________.")
  })

  it("no modifica preguntas que ya tienen una redacción natural", () => {
    expect(naturalizePrompt("¿Quién interpretó el sueño del rey?")).toBe("¿Quién interpretó el sueño del rey?")
  })
})
