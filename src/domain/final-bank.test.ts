import { describe, expect, it } from "vitest"

describe("contrato del Banco Maestro Único", () => {
  it("expone una sola identidad y exactamente cuatro familias", async () => {
    const modulePath = "./final-bank"
    const contract = await import(/* @vite-ignore */ modulePath).catch(() => null)

    expect(contract, "falta src/domain/final-bank.ts").not.toBeNull()
    expect(contract?.FINAL_BANK_ID).toBe("BANCO_UNICO_CONEXION_BIBLICA_2026")
    expect(contract?.FINAL_BANK_DISPLAY_NAME).toBe(
      "Banco Maestro Único — Final 2026"
    )
    expect(contract?.FINAL_QUESTION_FAMILIES).toEqual([
      "single_choice_direct",
      "fill_choice",
      "true_false",
      "single_choice_contextual",
    ])
  })

  it("rechaza familias antiguas y cardinalidades incompatibles", async () => {
    const modulePath = "./final-bank"
    const contract = await import(/* @vite-ignore */ modulePath).catch(() => null)
    expect(contract, "falta src/domain/final-bank.ts").not.toBeNull()
    if (!contract) return

    expect(
      contract.validateFinalQuestion({
        family: "free_text",
        options: [],
        correctAnswer: [],
        finalEditorialStatus: "GOLD",
      })
    ).toEqual(expect.arrayContaining(["invalid_family", "invalid_option_count"]))
    expect(
      contract.validateFinalQuestion({
        family: "true_false",
        options: [
          { id: "A", text: "Verdadero" },
          { id: "B", text: "Falso" },
        ],
        correctAnswer: ["A"],
        finalEditorialStatus: "GOLD",
      })
    ).toEqual([])
  })
})
