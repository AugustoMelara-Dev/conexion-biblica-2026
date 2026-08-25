import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, it } from "vitest"

type HeaderRule = {
  source: string
  headers: Array<{ key: string; value: string }>
}

describe("política HTTP de actualización", () => {
  it("obliga a revalidar el service worker y los bancos", () => {
    const config = JSON.parse(
      readFileSync(join(process.cwd(), "vercel.json"), "utf8"),
    ) as { headers?: HeaderRule[] }
    const rules = config.headers ?? []

    for (const source of ["/sw.js", "/banks/(.*)"]) {
      const rule = rules.find((candidate) => candidate.source === source)
      expect(rule, `Falta la regla ${source}`).toBeDefined()
      expect(rule?.headers).toContainEqual({
        key: "Cache-Control",
        value: "public, max-age=0, must-revalidate",
      })
    }
  })
})
