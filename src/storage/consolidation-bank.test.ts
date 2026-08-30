import { describe, expect, it, vi } from "vitest"
import { createEmptyProgress } from "@/domain/mastery"

import {
  adaptGoldQuestion,
  loadConsolidationQuestionPool,
  resolveConsolidationMigrationSignatures,
  type ConsolidationManifest,
  type GoldRawQuestion,
} from "@/storage/consolidation-bank"
import {
  mapLegacyProgressFromSignatureIndex,
  migrationSignature,
} from "@/storage/history-migration"

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

  it("rescata una firma legacy preferida antes de factFilter", async () => {
    const known = raw("KNOWN", "F-KNOWN")
    const legacy = {
      ...raw("LEGACY", "F-LEGACY"),
      verse_or_page: "Daniel 7:20",
    }
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [known, legacy],
    })

    const result = await loadConsolidationQuestionPool({
      manifest,
      chapters: [7],
      count: 2,
      seed: 1,
      difficultyBands: ["HARD"],
      types: ["single_choice"],
      factFilter: (factId) => factId === "F-KNOWN",
      preferredMigrationSignatures: new Set([
        migrationSignature(adaptGoldQuestion(legacy)),
      ]),
      fetcher,
    })

    expect(result.map((question) => question.factId).sort()).toEqual([
      "F-KNOWN",
      "F-LEGACY",
    ])
  })

  it("reduce firmas legacy pendientes por lotes y filtros distintos", async () => {
    const known = raw("KNOWN", "F-KNOWN")
    const legacyRows = [
      raw("LEGACY-1", "F-LEGACY-1"),
      raw("LEGACY-2", "F-LEGACY-2"),
      raw("LEGACY-3", "F-LEGACY-3"),
      { ...raw("LEGACY-EASY", "F-LEGACY-EASY"), difficulty: "easy" as const },
      {
        ...raw("LEGACY-TF", "F-LEGACY-TF"),
        type: "true_false" as const,
        options: ["Verdadero", "Falso"],
        correct_option: 0,
        correct_answer: "Verdadero",
      },
    ].map((question, index) => ({
      ...question,
      verse_or_page: `Daniel 7:${20 + index}`,
      source_quote: `fuente legacy ${index}`,
    }))
    const allPreferred = new Set(
      legacyRows.map((question) =>
        migrationSignature(adaptGoldQuestion(question))
      )
    )
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [known, ...legacyRows],
    })
    const resolved = new Set<string>()
    const unresolved: number[] = []

    for (const filters of [
      { difficultyBands: ["HARD"] as const, types: ["single_choice"] as const },
      { difficultyBands: ["HARD"] as const, types: ["single_choice"] as const },
      { difficultyBands: ["BASIC"] as const, types: ["single_choice"] as const },
      { difficultyBands: ["HARD"] as const, types: ["true_false"] as const },
    ]) {
      const pending = new Set(
        [...allPreferred].filter((signature) => !resolved.has(signature))
      )
      const result = await loadConsolidationQuestionPool({
        manifest,
        chapters: [7],
        count: 2,
        seed: 2,
        difficultyBands: [...filters.difficultyBands],
        types: [...filters.types],
        factFilter: (factId) => factId === "F-KNOWN",
        preferredMigrationSignatures: pending,
        fetcher,
      })
      for (const question of result) {
        const signature = migrationSignature(question)
        if (allPreferred.has(signature)) resolved.add(signature)
      }
      unresolved.push(allPreferred.size - resolved.size)
    }

    expect(unresolved).toEqual([3, 2, 1, 0])
  })

  it("resuelve firmas legacy contra todo V5 sin materializar preguntas", async () => {
    const target = raw("TARGET-1", "FACT-1")
    const duplicateFact = { ...target, id: "TARGET-2", fact_id: "FACT-2" }
    const multiShardManifest: ConsolidationManifest = {
      ...manifest,
      gold_questions: 2,
      gold_facts: 2,
      shards: [
        manifest.shards[0],
        {
          chapter: "DAN8",
          question_count: 1,
          questions_file: "banks/consolidation-v5/questions/DAN8.json",
        },
      ],
    }
    const fetcher = vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).endsWith("DAN8.json") ? [duplicateFact] : [target],
    })) as unknown as typeof fetch
    const signature = migrationSignature(adaptGoldQuestion(target))

    const index = await resolveConsolidationMigrationSignatures({
      manifest: multiShardManifest,
      signatures: new Set([signature]),
      fetcher,
    })

    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(index.size).toBe(1)
    expect([...index.get(signature)!].sort()).toEqual(["FACT-1", "FACT-2"])
    const filtered = await loadConsolidationQuestionPool({
      manifest: multiShardManifest,
      chapters: [7],
      count: 1,
      seed: 1,
      fetcher,
    })
    expect(filtered.map((question) => question.factId)).toEqual(["FACT-1"])
    const legacy = {
      ...adaptGoldQuestion(target),
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

  it("no resuelve una firma desde un raw V5 con correct_option inválido", async () => {
    const valid = raw("VALID", "FACT-VALID")
    const invalid = { ...valid, id: "INVALID", correct_option: 99 }
    const signature = migrationSignature(adaptGoldQuestion(valid))
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [invalid],
    })

    const index = await resolveConsolidationMigrationSignatures({
      manifest,
      signatures: new Set([signature]),
      fetcher,
    })

    expect(index.get(signature)).toBeUndefined()
    expect(() => adaptGoldQuestion(invalid)).toThrow("Respuesta fuera de rango")
  })
})
