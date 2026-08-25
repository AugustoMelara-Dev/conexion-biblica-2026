import { describe, expect, it } from "vitest"
import { sessionContextForMode, showsImmediateFeedback } from "@/domain/session-context"

describe("contexto de sesión", () => {
  it("separa práctica de simulacro", () => {
    expect(sessionContextForMode("learn")).toBe("practice")
    expect(sessionContextForMode("smart-review")).toBe("practice")
    expect(sessionContextForMode("simulation")).toBe("simulation")
    expect(sessionContextForMode("training")).toBe("practice")
  })

  it("sólo revela feedback inmediato en modos de aprendizaje", () => {
    expect(showsImmediateFeedback("learn")).toBe(true)
    expect(showsImmediateFeedback("smart-review")).toBe(true)
    expect(showsImmediateFeedback("simulation")).toBe(false)
  })
})
