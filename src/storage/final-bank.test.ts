import { describe, expect, it, vi } from "vitest"

import {
  adaptFinalQuestion,
  finalManifestFingerprint,
  loadFinalQuestionPool,
  readFinalManifest,
  resolveFinalMigrationSignatures,
  type FinalBankManifest,
  type FinalRawQuestion,
} from "@/storage/final-bank"
import { createEmptyProgress } from "@/domain/mastery"
import {
  mapLegacyProgressFromSignatureIndex,
  migrationSignature,
} from "@/storage/history-migration"

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
  it("fingerprint distingue builds con el mismo schema y es estable", async () => {
    const base: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      build_id: "build-a",
      gold_questions: 1,
      unique_facts: 1,
      shards: [
        {
          chapter: "DAN7",
          question_count: 1,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ],
    }

    expect(await finalManifestFingerprint(base)).toBe(
      await finalManifestFingerprint(structuredClone(base))
    )
    expect(await finalManifestFingerprint(base)).not.toBe(
      await finalManifestFingerprint({ ...base, build_id: "build-b" })
    )
  })

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

  it("does not promote hard questions to competitive without explicit evidence", () => {
    const question = adaptFinalQuestion(raw({ difficulty: "hard" }))
    expect(question.tier).toBeUndefined()
    expect(question.metadata?.tier).toBeUndefined()
  })

  it("keeps fill-choice as four buttons rather than written text", () => {
    const question = adaptFinalQuestion(raw({ family: "fill_choice" }))
    expect(question.type).toBe("fill_blank")
    expect(question.answerMode).toBe("option_id")
    expect(question.options).toHaveLength(4)
  })

  it("adapts V10 authored questions preserving subtype, evidence excerpt and ai review", () => {
    const question = adaptFinalQuestion(
      raw({
        schema_version: "10.0",
        subtype: "speaker_addressee",
        evidence_excerpt: "declaró el rey a Daniel",
        ai_review: {
          status: "passed",
          reviewer_type: "ai_semantic_audit",
          reviewer: "reviewer-7",
        },
      })
    )
    expect(question.semanticSkill).toBe("speaker_addressee")
    expect(question.metadata?.evidenceExcerpt).toBe("declaró el rey a Daniel")
    expect(question.metadata?.aiReviewer).toBe("reviewer-7")
    expect(question.metadata?.aiReviewerType).toBe("ai_semantic_audit")
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

  it("loads exact audited question IDs without replacing them with another presentation", async () => {
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 2,
      unique_facts: 1,
      shards: [{
        chapter: "DAN7",
        question_count: 2,
        questions_file: "banks/final-2026/questions/DAN7.json",
      }],
    }
    const rows = [
      raw({ id: "DROP", fact_id: "DROP-FACT", variant_id: "DROP-VARIANT" }),
      raw({ id: "KEEP", variant_id: "KEEP-VARIANT" }),
    ]
    const fetcher = vi.fn(async () => ({ ok: true, json: async () => rows })) as unknown as typeof fetch

    const loaded = await loadFinalQuestionPool({
      manifest,
      chapters: [7],
      count: 2,
      seed: 7,
      questionIds: new Set(["KEEP"]),
      fetcher,
    })

    expect(loaded.map((question) => question.id)).toEqual(["KEEP"])
    expect(loaded[0].metadata?.retryVariants).toEqual([])
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
          totalResponseTimeMs: 6_001,
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

  it("rescata firmas legacy preferidas antes de aplicar factFilter", async () => {
    const manifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 2,
      unique_facts: 2,
      shards: [
        {
          chapter: "DAN7",
          question_count: 2,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ],
    }
    const known = raw({
      id: "KNOWN",
      fact_id: "F-KNOWN",
      variant_id: "V-KNOWN",
    })
    const legacy = raw({
      id: "LEGACY",
      fact_id: "F-LEGACY",
      variant_id: "V-LEGACY",
      reference: "Daniel 7:20",
    })
    const fetcher = vi.fn(async () => ({
      ok: true,
      json: async () => [known, legacy],
    })) as unknown as typeof fetch

    const selected = await loadFinalQuestionPool({
      manifest,
      chapters: [7],
      count: 2,
      seed: 1,
      factFilter: (factId) => factId === "F-KNOWN",
      preferredMigrationSignatures: new Set([
        migrationSignature(adaptFinalQuestion(legacy)),
      ]),
      fetcher,
    })

    expect(selected.map((question) => question.factId).sort()).toEqual([
      "F-KNOWN",
      "F-LEGACY",
    ])
  })

  it("indexa sólo firmas legacy contra todos los shards sin adaptar el universo", async () => {
    const target = raw({ id: "TARGET-1", fact_id: "FACT-1" })
    const duplicateFact = raw({ id: "TARGET-2", fact_id: "FACT-2" })
    const ignored = raw({
      id: "IGNORED",
      fact_id: "FACT-IGNORED",
      reference: "Daniel 7:99",
    })
    const multiShardManifest: FinalBankManifest = {
      schema_version: "9.0",
      bank_id: "BANCO_UNICO_CONEXION_BIBLICA_2026",
      display_name: "Banco Maestro Único — Final 2026",
      gold_questions: 3,
      unique_facts: 3,
      shards: [
        {
          chapter: "DAN7",
          question_count: 1,
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
        {
          chapter: "DAN8",
          question_count: 2,
          questions_file: "banks/final-2026/questions/DAN8.json",
        },
      ],
    }
    const fetcher = vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).endsWith("DAN8.json")
          ? [duplicateFact, ignored]
          : [target],
    })) as unknown as typeof fetch
    const signature = migrationSignature(adaptFinalQuestion(target))

    const index = await resolveFinalMigrationSignatures({
      manifest: multiShardManifest,
      signatures: new Set([signature]),
      fetcher,
    })

    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(index.size).toBe(1)
    expect([...index.get(signature)!].sort()).toEqual(["FACT-1", "FACT-2"])
    const filtered = await loadFinalQuestionPool({
      manifest: multiShardManifest,
      chapters: [7],
      count: 1,
      seed: 1,
      fetcher,
    })
    expect(filtered.map((question) => question.factId)).toEqual(["FACT-1"])
    const legacy = {
      ...adaptFinalQuestion(target),
      id: "legacy-target",
      bankId: "curated-v4",
      bankProfileId: "curated-v4" as const,
    }
    const migration = mapLegacyProgressFromSignatureIndex(
      [legacy],
      [
        {
          ...createEmptyProgress("curated-v4:legacy-target"),
          timesSeen: 1,
        },
      ],
      index
    )
    expect(migration.mapped).toEqual([])
    expect(migration.legacy).toEqual([
      expect.objectContaining({ reason: "ambiguous_match" }),
    ])
  })
})
