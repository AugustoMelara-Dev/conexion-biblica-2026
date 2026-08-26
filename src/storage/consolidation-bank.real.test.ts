import { readFileSync } from "node:fs"
import { resolve } from "node:path"
import { describe, expect, it } from "vitest"

import {
  loadConsolidationQuestionPool,
  type ConsolidationManifest,
} from "@/storage/consolidation-bank"

const publicRoot = resolve(process.cwd(), "public")
const manifest = JSON.parse(
  readFileSync(resolve(publicRoot, "banks/consolidation-v5/manifest.json"), "utf8")
) as ConsolidationManifest
const fetcher = async (input: string | URL | Request) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.pathname : new URL(input.url).pathname
  return new Response(readFileSync(resolve(publicRoot, url.replace(/^\//, "")), "utf8"), {
    status: 200,
    headers: { "content-type": "application/json" },
  })
}

describe("real V6 blind simulations", () => {
  for (const pool of ["A", "B"] as const) {
    it(`builds blind pool ${pool} with the mandatory 100-question mix`, async () => {
      const questions = await loadConsolidationQuestionPool({
        manifest,
        chapters: manifest.shards.map((shard) => Number(shard.chapter.match(/\d+/)?.[0])),
        count: 100,
        seed: pool === "A" ? 101 : 202,
        blindPool: pool,
        fetcher: fetcher as typeof fetch,
      })

      expect(questions).toHaveLength(100)
      expect(new Set(questions.map((question) => question.factId)).size).toBe(100)
      expect(questions.filter((question) => question.type === "fill_blank")).toHaveLength(30)
      expect(questions.filter((question) => question.type === "true_false")).toHaveLength(25)
      expect(questions.filter((question) => question.type === "single_choice")).toHaveLength(45)
      expect(questions.filter((question) => question.trapType === "true_elsewhere").length).toBeGreaterThanOrEqual(18)
    })
  }
})
