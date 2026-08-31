import { readFileSync } from "node:fs"
import { resolve } from "node:path"
import { describe, expect, it } from "vitest"

import {
  selectMandatoryHundred,
  selectMissionQuestions,
} from "@/domain/final-mission-selection"
import { materializeDynamicQuestion } from "@/domain/dynamic-question"
import { parseHumanReviewIndex } from "@/domain/editorial-review"
import {
  adaptFinalQuestion,
  type FinalBankManifest,
  type FinalRawQuestion,
} from "@/storage/final-bank"

const root = resolve(import.meta.dirname, "../..")
const bankRoot = resolve(root, "public/banks/final-2026")
const manifest = JSON.parse(
  readFileSync(resolve(bankRoot, "manifest.json"), "utf8")
) as FinalBankManifest
const reviewIndex = JSON.parse(
  readFileSync(resolve(bankRoot, "review-index.json"), "utf8")
) as unknown
const questions = manifest.shards.flatMap((shard) => {
  const rows = JSON.parse(
    readFileSync(resolve(root, "public", shard.questions_file), "utf8")
  ) as FinalRawQuestion[]
  return rows.filter((row) => row.blind_pool === null).map(adaptFinalQuestion)
})

describe("real V10 competitive bank rounds", () => {
  it("loads every emitted entry into the human review queue", () => {
    expect(parseHumanReviewIndex(reviewIndex).bank_questions).toBe(2468)
  })

  it("loads the exact public training artifact without leaking blind pools", () => {
    expect(manifest.gold_questions).toBe(2468)
    expect(manifest.unique_facts).toBe(2217)
    expect(manifest.shards).toHaveLength(18)
    expect(
      manifest.shards.reduce((sum, shard) => sum + shard.question_count, 0)
    ).toBe(2468)
    expect(questions.every((question) => !question.blindPool)).toBe(true)
  })

  it("sustains the national-final contract across 1,000 hard/expert seeds", () => {
    const nationalFinal = questions.filter(
      (question) =>
        question.difficultyBand === "HARD" ||
        question.difficultyBand === "EXPERT"
    )
    const signatures = new Set<string>()

    for (let seed = 0; seed < 1000; seed += 1) {
      const selected = selectMandatoryHundred(nationalFinal, seed)
      const facts = selected.map((question) => question.factId)
      expect(selected).toHaveLength(100)
      expect(new Set(facts).size).toBe(100)
      expect(
        selected.filter((question) => question.type === "single_choice")
      ).toHaveLength(45)
      expect(
        selected.filter((question) => question.type === "fill_blank")
      ).toHaveLength(30)
      expect(
        selected.filter((question) => question.type === "true_false")
      ).toHaveLength(25)
      expect(
        selected.every(
          (question) =>
            !question.blindPool &&
            (question.difficultyBand === "HARD" ||
              question.difficultyBand === "EXPERT")
        )
      ).toBe(true)
      signatures.add(facts.slice().sort().join("|"))
    }

    expect(signatures.size).toBeGreaterThan(900)
  })

  it("selects 100 distinct facts with the required competitive mix", () => {
    const selected = selectMandatoryHundred(questions, 20260829)
    const byType = {
      fill_blank: selected.filter((question) => question.type === "fill_blank"),
      true_false: selected.filter((question) => question.type === "true_false"),
      single_choice: selected.filter(
        (question) => question.type === "single_choice"
      ),
    }
    const contextual = selected.filter(
      (question) => question.family === "single_choice_contextual"
    )
    const relational = selected.filter(
      (question) =>
        question.semanticSkill === "cause_consequence" ||
        /purpose|speaker|recipient|sequence|order|comparison|difference/.test(
          String(question.metadata?.relationType ?? "")
        )
    )

    expect(new Set(selected.map((question) => question.factId)).size).toBe(100)
    expect(byType.fill_blank).toHaveLength(30)
    expect(byType.true_false).toHaveLength(25)
    expect(byType.single_choice).toHaveLength(45)
    expect(contextual).toHaveLength(18)
    expect(relational.length).toBeGreaterThanOrEqual(10)
    const trueCount = byType.true_false.filter(
      (question) => question.correctAnswerText === "Verdadero"
    ).length
    expect([trueCount, 25 - trueCount].sort()).toEqual([12, 13])
  })

  it.each([50, 100, 200] as const)(
    "builds a %i-question session without repeating a fact",
    (count) => {
      const selected = selectMissionQuestions({
        questions,
        count,
        seed: 20260829 + count,
      })
      expect(selected).toHaveLength(count)
      expect(new Set(selected.map((question) => question.factId)).size).toBe(
        count
      )
    }
  )

  it("keeps the contract across consecutive rounds and changes answer positions", () => {
    for (let offset = 0; offset < 24; offset += 1) {
      const selected = selectMandatoryHundred(questions, 20260829 + offset)
      expect(
        selected.filter((question) => question.type === "fill_blank")
      ).toHaveLength(30)
      expect(
        selected.filter((question) => question.type === "true_false")
      ).toHaveLength(25)
      expect(
        selected.filter((question) => question.type === "single_choice")
      ).toHaveLength(45)
      expect(
        selected.filter((question) => question.trapType === "true_elsewhere")
      ).toHaveLength(18)
      expect(new Set(selected.map((question) => question.factId)).size).toBe(
        100
      )
      expect(selected.every((question) => !question.blindPool)).toBe(true)
    }

    const anchor = questions.find((question) => question.options.length === 4)!
    const positions = new Set(
      Array.from(
        { length: 16 },
        (_, exposure) =>
          materializeDynamicQuestion(anchor, {
            seed: 20260829,
            exposure,
          }).correctAnswer[0]
      )
    )
    expect(positions).toEqual(new Set(["A", "B", "C", "D"]))
  })

  it("keeps authored variants genuinely different when a fact has more than one", () => {
    const byFact = new Map<string, typeof questions>()
    for (const question of questions) {
      const fact = question.factId!
      byFact.set(fact, [...(byFact.get(fact) ?? []), question])
    }
    const variants = [...byFact.values()].find((rows) => rows.length >= 2)!

    expect(new Set(variants.map((question) => question.question)).size).toBe(
      variants.length
    )
    expect(
      new Set(
        variants.map((question) =>
          question.options
            .map((option) => option.text)
            .sort()
            .join("|")
        )
      ).size
    ).toBeGreaterThanOrEqual(2)
  })
})
