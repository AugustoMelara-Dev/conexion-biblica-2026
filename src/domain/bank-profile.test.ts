import { describe, expect, it } from "vitest"
import { questionBelongsToSelection } from "@/domain/banks"
import type { Question } from "@/domain/types"

function question(bankProfileId: string) {
  return { bankProfileId } as Question
}

describe("perfil de banco curado V4", () => {
  it("Mixto curado incluye V1, V3 y V4 pero excluye V2", () => {
    expect(questionBelongsToSelection(question("legacy-v1"), "mixed")).toBe(true)
    expect(questionBelongsToSelection(question("prep-v3"), "mixed")).toBe(true)
    expect(questionBelongsToSelection(question("curated-v4"), "mixed")).toBe(true)
    expect(questionBelongsToSelection(question("master-v2"), "mixed")).toBe(false)
  })
})
