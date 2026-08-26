import { describe, expect, it, vi } from "vitest"

import {
  adaptGoldQuestion,
  loadConsolidationQuestionPool,
  type ConsolidationManifest,
  type GoldRawQuestion,
} from "@/storage/consolidation-bank"

const raw = (id: string, fact: string, blindPool: GoldRawQuestion["blind_pool"] = null): GoldRawQuestion => ({
  id,
  fact_id: fact,
  variant_id: `${fact}-V1`,
  template_id: "mc-contextual-v1",
  bank: "DANIEL1-12",
  chapter: "DAN7",
  verse_or_page: "Daniel 7:9",
  source_span: "el pelo de su cabeza, como lana limpia",
  type: "multiple_choice",
  difficulty: "hard",
  topic: "Anciano de días",
  context_anchor: "Daniel 7:9",
  question: "Según Daniel 7:9, ¿con qué se compara el pelo?",
  options: ["Lana limpia", "Nieve", "Fuego", "Bronce"],
  correct_option: 0,
  correct_answer: "Lana limpia",
  accepted_answers: ["Lana limpia"],
  answer_mode: "exact_text",
  explanation: "El pelo se compara con lana limpia.",
  why_distractors_fail: {},
  why_each_distractor_fails: {},
  source_quote: "el pelo de su cabeza, como lana limpia",
  trap_type: null,
  blind_final_pool: blindPool !== null,
  blind_pool: blindPool,
  validation_status: "gold_audited",
  editorial_status: "gold",
  quality_score: 95,
  semantic_skill: "contextual_precision",
})

const manifest: ConsolidationManifest = {
  schema_version: "5.1",
  profile_id: "consolidation-v5",
  version: "test",
  gold_questions: 3,
  gold_facts: 3,
  shards: [{ chapter: "DAN7", question_count: 3, questions_file: "banks/consolidation-v5/questions/DAN7.json" }],
}

describe("consolidation GOLD loader", () => {
  it("adapts only audited GOLD into the consolidation profile", () => {
    expect(adaptGoldQuestion(raw("G1", "F1"))).toMatchObject({
      bankId: "consolidation-v5",
      bankProfileId: "consolidation-v5",
      editorialStatus: "gold",
      qualityScore: 95,
      source: { reference: "Daniel 7:9" },
    })
  })

  it("excludes every blind pool from normal training", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => [raw("G1", "F1"), raw("G2", "F2", "A"), raw("G3", "F3", "B")] })
    const result = await loadConsolidationQuestionPool({ manifest, chapters: [7], count: 10, seed: 1, fetcher })
    expect(result.map((question) => question.id)).toEqual(["G1"])
  })

  it("loads only the requested blind pool", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => [raw("G1", "F1"), raw("G2", "F2", "A"), raw("G3", "F3", "B")] })
    const result = await loadConsolidationQuestionPool({ manifest, chapters: [7], count: 10, seed: 1, blindPool: "B", fetcher })
    expect(result.map((question) => question.factId)).toEqual(["F3"])
  })

  it("filters difficulty and type before applying the requested count", async () => {
    const easy = { ...raw("G1", "F1"), difficulty: "easy" as const }
    const hard = raw("G2", "F2")
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => [easy, hard] })
    const result = await loadConsolidationQuestionPool({
      manifest,
      chapters: [7],
      count: 1,
      seed: 1,
      difficultyBands: ["HARD"],
      types: ["single_choice"],
      fetcher,
    })
    expect(result.map((question) => question.id)).toEqual(["G2"])
  })
})
