import { afterEach, describe, expect, it, vi } from "vitest"
import { downloadJson } from "@/lib/format"

describe("exportación JSON local", () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it("crea un enlace descargable y libera el object URL", () => {
    const createObjectURL = vi.fn(() => "blob:conexion-biblica")
    const revokeObjectURL = vi.fn()
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL })
    const anchor = document.createElement("a")
    const click = vi.spyOn(anchor, "click").mockImplementation(() => undefined)
    vi.spyOn(document, "createElement").mockReturnValue(anchor)

    downloadJson("respaldo.json", { backupVersion: "1.0" })

    expect(createObjectURL).toHaveBeenCalledOnce()
    expect(anchor.download).toBe("respaldo.json")
    expect(anchor.href).toBe("blob:conexion-biblica")
    expect(click).toHaveBeenCalledOnce()
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:conexion-biblica")
  })
})
