import { readFileSync } from "node:fs"
import { resolve } from "node:path"
import { describe, expect, it } from "vitest"

import { selectMandatoryHundred } from "@/domain/final-mission-selection"
import {
  adaptFinalQuestion,
  type FinalBankManifest,
  type FinalRawQuestion,
} from "@/storage/final-bank"

const root = resolve(import.meta.dirname, "../..")
const bankRoot = resolve(root, "public/banks/final-2026")
const manifest = JSON.parse(
  readFileSync(resolve(bankRoot, "manifest.json"), "utf8"),
) as FinalBankManifest
const questions = manifest.shards.flatMap((shard) => {
  const rows = JSON.parse(
    readFileSync(resolve(root, "public", shard.questions_file), "utf8"),
  ) as FinalRawQuestion[]
  return rows.filter((row) => row.blind_pool === null).map(adaptFinalQuestion)
})

describe("real V8 final bank rounds", () => {
  it("selects 100 distinct facts with the required competitive mix", () => {
    const selected = selectMandatoryHundred(questions, 20260829)
    const byType = {
      fill_blank: selected.filter((question) => question.type === "fill_blank"),
      true_false: selected.filter((question) => question.type === "true_false"),
      single_choice: selected.filter((question) => question.type === "single_choice"),
    }
    const contextual = selected.filter(
      (question) => question.family === "single_choice_contextual",
    )
    const relational = selected.filter(
      (question) =>
        question.semanticSkill === "cause_consequence" ||
        /purpose|speaker|recipient|sequence|order|comparison|difference/.test(
          String(question.metadata?.relationType ?? ""),
        ),
    )

    expect(new Set(selected.map((question) => question.factId)).size).toBe(100)
    expect(byType.fill_blank).toHaveLength(30)
    expect(byType.true_false).toHaveLength(25)
    expect(byType.single_choice).toHaveLength(45)
    expect(contextual).toHaveLength(18)
    expect(relational.length).toBeGreaterThanOrEqual(10)
    const trueCount = byType.true_false.filter(
      (question) => question.correctAnswerText === "Verdadero",
    ).length
    expect([trueCount, 25 - trueCount].sort()).toEqual([12, 13])
  })
})
