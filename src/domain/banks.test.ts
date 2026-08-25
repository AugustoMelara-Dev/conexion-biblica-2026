import { describe, expect, it } from "vitest"
import { filterQuestionsForSelection, questionBelongsToSelection } from "@/domain/banks"
import type { Question } from "@/domain/types"

function question(bankProfileId: string) {
  return { bankProfileId } as Question
}

describe("selecciones de bancos", () => {
  it("V3 contiene sólo el banco curado de 500", () => {
    const master = question("master-v2")
    const supplement = question("prep-v3")
    const legacy = question("legacy-v1")

    expect(questionBelongsToSelection(master, "prep-v3")).toBe(false)
    expect(questionBelongsToSelection(supplement, "prep-v3")).toBe(true)
    expect(questionBelongsToSelection(legacy, "prep-v3")).toBe(false)
    expect(filterQuestionsForSelection([legacy, master, supplement], "prep-v3")).toEqual([supplement])
  })
})
