import { describe, expect, it, vi } from "vitest"

import {
  adaptFinalQuestion,
  loadFinalQuestionPool,
  readFinalManifest,
  type FinalBankManifest,
  type FinalRawQuestion,
} from "@/storage/final-bank"

const raw = (overrides: Partial<FinalRawQuestion> = {}): FinalRawQuestion => ({
  id: "DAN7-GOLD-0001-SINGLE_CHOICE_CONTEXTUAL",
  bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
  bank_name: "Banco Maestro Único — Final 2026",
  schema_version: "9.0",
  source_unit_id: "DAN7-V019",
  fact_id: "DAN7-V019-F01",
  variant_id: "DAN7-V019-F01-SINGLE_CHOICE_CONTEXTUAL",
  template_id: "single_choice_contextual-editorial-v1",
  family: "single_choice_contextual",
  chapter: "DAN7",
  reference: "Daniel 7:19",
  source_ref: "Daniel 7:19",
  verse_or_page: "Daniel 7:19",
  source_span: "tenía uñas de bronce",
  source_quote: "tenía uñas de bronce",
  context_anchor: "tenía uñas de bronce",
  topic: "comparison",
  importance: "critical",
  relation_type: "comparison",
  option_category: "phrase",
  blind_pool: null,
  question: "Según Daniel 7:19, ¿qué detalle se añade?",
  options: [
    "Uñas de bronce",
    "Dientes de hierro",
    "Diez cuernos",
    "Gran fuerza",
  ],
  correct_option: 0,
  correct_answer: "Uñas de bronce",
  accepted_answers: ["Uñas de bronce"],
  answer_mode: "option_id",
  explanation: "Daniel 7:19 añade las uñas de bronce.",
  why_distractors_fail: {
    "Dientes de hierro": "Pertenece a otra descripción.",
  },
  trap_type: "true_in_other_context",
  final_editorial_status: "GOLD",
  difficulty: "hard",
  validation_adversarial: {
    reviewer: "source-blind-v1",
    status: "passed",
    selected_option: 0,
    rationale: "Única opción sustentada.",
    second_defensible_option: false,
  },
  ...overrides,
})

describe("canonical final bank storage", () => {
  it("adapts V8 without exposing a versioned bank name", () => {
    const question = adaptFinalQuestion(raw())
    expect(question.bankId).toBe("BANCO_UNICO_CONEXION_BIBLICA_2026")
    expect(question.bankProfileId).toBe("final-v7")
    expect(question.family).toBe("single_choice_contextual")
    expect(question.type).toBe("single_choice")
    expect(question.trapType).toBe("true_elsewhere")
    expect(question.answerMode).toBe("option_id")
    expect(question.correctAnswer).toEqual(["A"])
  })

  it("keeps fill-choice as four buttons rather than written text", () => {
    const question = adaptFinalQuestion(raw({ family: "fill_choice" }))
    expect(question.type).toBe("fill_blank")
    expect(question.answerMode).toBe("option_id")
    expect(question.options).toHaveLength(4)
  })

  it("reads the canonical manifest and loads chapter shards lazily", async () => {
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 4,
      unique_facts: 4,
      shards: [
        {
          chapter: "DAN7",
          question_count: 4,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ],
    }
    const rows = [
      raw(),
      raw({ id: "Q2", fact_id: "F2", variant_id: "V2", family: "fill_choice" }),
    ]
    const fetcher = vi.fn(async (url: string) => ({
      ok: true,
      json: async () => (url.endsWith("manifest.json") ? manifest : rows),
    })) as unknown as typeof fetch
    expect(await readFinalManifest(fetcher)).toEqual(manifest)
    const loaded = await loadFinalQuestionPool({
      manifest,
      chapters: [7],
      count: 2,
      seed: 7,
      fetcher,
    })
    expect(loaded).toHaveLength(2)
    expect(new Set(loaded.map((question) => question.factId)).size).toBe(2)
    expect(fetcher).toHaveBeenCalledWith(
      "/banks/final-2026/questions/DAN7.json"
    )
  })

  it("attaches alternate families for delayed repair without repeating the prompt", async () => {
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 4,
      unique_facts: 1,
      shards: [
        {
          chapter: "DAN7",
          question_count: 4,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ],
    }
    const rows = [
      raw({ family: "single_choice_direct", id: "DIRECT", variant_id: "VD" }),
      raw({ family: "fill_choice", id: "FILL", variant_id: "VF" }),
      raw({
        family: "true_false",
        id: "TF",
        variant_id: "VT",
        options: ["Verdadero", "Falso"],
      }),
      raw({
        family: "single_choice_contextual",
        id: "CONTEXT",
        variant_id: "VC",
      }),
    ]
    const fetcher = vi.fn(async () => ({
      ok: true,
      json: async () => rows,
    })) as unknown as typeof fetch

    const [loaded] = await loadFinalQuestionPool({
      manifest,
      chapters: [7],
      count: 1,
      seed: 5,
      fetcher,
    })
    const alternatives = loaded.metadata?.retryVariants as Array<{
      family?: string
    }>
    expect(alternatives).toHaveLength(3)
    expect(alternatives.every((item) => item.family !== loaded.family)).toBe(
      true
    )
  })

  it("prefers unseen facts across rounds and falls back only after novelty is exhausted", async () => {
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 8,
      unique_facts: 8,
      shards: [
        {
          chapter: "DAN7",
          question_count: 8,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ],
    }
    const rows = [
      ...Array.from({ length: 6 }, (_, index) =>
        raw({
          id: `SEEN-${index}`,
          fact_id: `F-SEEN-${index}`,
          variant_id: `V-SEEN-${index}`,
        })
      ),
      raw({ id: "NEW-1", fact_id: "F-NEW-1", variant_id: "V-NEW-1" }),
      raw({ id: "NEW-2", fact_id: "F-NEW-2", variant_id: "V-NEW-2" }),
    ]
    const fetcher = vi.fn(async () => ({
      ok: true,
      json: async () => rows,
    })) as unknown as typeof fetch

    for (const seed of [1, 2, 3, 4, 5, 9, 17, 29]) {
      const fresh = await loadFinalQuestionPool({
        manifest,
        chapters: [7],
        count: 2,
        seed,
        seenFactIds: new Set(
          Array.from({ length: 6 }, (_, index) => `F-SEEN-${index}`)
        ),
        fetcher,
      })
      expect(fresh.map((question) => question.factId).sort()).toEqual([
        "F-NEW-1",
        "F-NEW-2",
      ])
    }

    const fallback = await loadFinalQuestionPool({
      manifest,
      chapters: [7],
      count: 2,
      seed: 9,
      seenFactIds: new Set(rows.map((row) => row.fact_id)),
      fetcher,
    })
    expect(fallback).toHaveLength(2)
  })

  it("lets failed and slow seen facts displace novel facts in a later round", async () => {
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 6,
      unique_facts: 6,
      shards: [
        {
          chapter: "DAN7",
          question_count: 6,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ],
    }
    const rows = [
      raw({ id: "FAILED", fact_id: "F-FAILED", variant_id: "V-FAILED" }),
      raw({ id: "SLOW", fact_id: "F-SLOW", variant_id: "V-SLOW" }),
      ...Array.from({ length: 4 }, (_, index) =>
        raw({
          id: `NEW-${index}`,
          fact_id: `F-NEW-${index}`,
          variant_id: `V-NEW-${index}`,
        })
      ),
    ]
    const fetcher = vi.fn(async () => ({
      ok: true,
      json: async () => rows,
    })) as unknown as typeof fetch

    const selected = await loadFinalQuestionPool({
      manifest,
      chapters: [7],
      count: 2,
      seed: 17,
      seenFactIds: new Set(["F-FAILED", "F-SLOW"]),
      exposures: [
        {
          exposureKey: "F-FAILED:V-FAILED",
          factId: "F-FAILED",
          variantId: "V-FAILED",
          questionKey: "final-v7:FAILED",
          exposures: 2,
          correct: 0,
          incorrect: 2,
          totalResponseTimeMs: 8_000,
          averageResponseTimeMs: 4_000,
          lastSeenAt: 2,
          lastSelectedAnswer: "B",
          lastErrorType: "incorrect",
        },
        {
          exposureKey: "F-SLOW:V-SLOW",
          factId: "F-SLOW",
          variantId: "V-SLOW",
          questionKey: "final-v7:SLOW",
          exposures: 1,
          correct: 1,
          incorrect: 0,
          totalResponseTimeMs: 12_000,
          averageResponseTimeMs: 12_000,
          lastSeenAt: 3,
          lastSelectedAnswer: "A",
          lastErrorType: null,
        },
      ],
      fetcher,
    })

    expect(selected.map((question) => question.factId).sort()).toEqual([
      "F-FAILED",
      "F-SLOW",
    ])
  })
})
