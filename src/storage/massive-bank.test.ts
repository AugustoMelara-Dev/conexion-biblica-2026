import { describe, expect, it, vi } from "vitest"
import {
  adaptMassiveQuestion,
  loadMassiveQuestionPool,
  type MassiveBankManifest,
  type MassiveRawQuestion,
} from "@/storage/massive-bank"

const rawQuestion: MassiveRawQuestion = {
  id: "DAN7-0001",
  fact_id: "DAN7-V01-S01-F01",
  variant_id: "DAN7-V01-S01-F01-MC-01",
  template_id: "mc-contextual-v1",
  bank: "DANIEL1-12",
  chapter: "DAN7",
  verse_or_page: "16, Daniel 7:1",
  source_span: "En el primer año de Belsasar tuvo Daniel un sueño.",
  type: "multiple_choice",
  difficulty: "hard",
  topic: "visión",
  context_anchor: "En el primer año de Belsasar",
  question: "Según Daniel 7:1, ¿qué ocurrió?",
  options: ["un sueño", "un decreto", "un banquete", "una guerra"],
  correct_option: 0,
  correct_answer: "un sueño",
  accepted_answers: ["un sueño"],
  answer_mode: "exact_text",
  explanation: "El versículo menciona un sueño.",
  why_distractors_fail: { "un decreto": "Otra escena" },
  source_quote: "tuvo Daniel un sueño",
  trap_type: "true_elsewhere",
  blind_final_pool: false,
  validation_status: "verified",
}

describe("banco masivo fragmentado", () => {
  it("adapta el esquema editorial sin perder factId, variantId ni respaldo", () => {
    const question = adaptMassiveQuestion(rawQuestion)
    expect(question).toMatchObject({
      id: "DAN7-0001",
      bankId: "massive-v5",
      bankProfileId: "massive-v5",
      type: "single_choice",
      difficulty: 4,
      difficultyBand: "HARD",
      factKey: "DAN7-V01-S01-F01",
      factId: "DAN7-V01-S01-F01",
      variantId: "DAN7-V01-S01-F01-MC-01",
      sourceQuote: "tuvo Daniel un sueño",
      blindFinalPool: false,
    })
    expect(question.correctAnswer).toEqual(["A"])
  })

  it("carga solo los shards solicitados y excluye la reserva ciega", async () => {
    const manifest: MassiveBankManifest = {
      schema_version: "5.0",
      profile_id: "massive-v5",
      totals: { questions: 3, facts: 2, templates: 1, distractors: 3 },
      shards: [
        { chapter: "DAN7", bank: "DANIEL1-12", question_count: 2, fact_count: 1, questions_file: "banks/massive-v5/questions/DAN7.json", facts_file: "", questions_sha256: "", facts_sha256: "", bytes: 1 },
        { chapter: "DAN8", bank: "DANIEL1-12", question_count: 1, fact_count: 1, questions_file: "banks/massive-v5/questions/DAN8.json", facts_file: "", questions_sha256: "", facts_sha256: "", bytes: 1 },
      ],
    }
    const fetcher = vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () => String(input).includes("DAN7")
        ? [rawQuestion, { ...rawQuestion, id: "DAN7-0002", variant_id: "blind", blind_final_pool: true }]
        : [{ ...rawQuestion, id: "DAN8-0001", chapter: "DAN8" }],
    }) as Response) as unknown as typeof fetch
    const result = await loadMassiveQuestionPool({
      manifest,
      chapters: [7],
      count: 20,
      includeBlind: false,
      fetcher,
      seed: 7,
    })
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(result.map((question) => question.id)).toEqual(["DAN7-0001"])
  })
})
