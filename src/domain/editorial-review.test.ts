import { describe, expect, it } from "vitest"

import {
  buildHumanReviewDecision,
  parseHumanReviewQuestionShard,
  parseHumanReviewIndex,
  reconcileHumanReview,
  selectNextHumanReview,
  type HumanReviewDecision,
  type HumanReviewEntry,
} from "@/domain/editorial-review"

const entry = (id: string, hash = `hash-${id}`): HumanReviewEntry => ({
  id,
  fact_id: `fact-${id}`,
  chapter: "DAN7",
  family: "single_choice_contextual",
  reference: "Daniel 7:1",
  content_sha256: hash,
  risk_score: 15,
  automatic_flags: [],
  automatic_status: "passed",
})

const decision = (id: string, hash = `hash-${id}`): HumanReviewDecision => ({
  id,
  content_sha256: hash,
  reviewer: "Revisor humano",
  reviewed_at: "2026-08-28T12:00:00.000Z",
  disposition: "approved",
  notes: "",
})

describe("auditoría editorial humana", () => {
  it("adapta el review-index 10 real a una cola segura", () => {
    expect(
      parseHumanReviewIndex({
        schema_version: "10.0",
        total_reviewed: 1,
        human_signatures: 0,
        entries: [
          {
            question_id: "Q-DAN1-0001",
            content_sha256: "hash-real",
            decision: "passed",
            reviewer_type: "ai_semantic_audit",
            reviewer: "reviewer-pilot",
          },
        ],
      })
    ).toEqual({
      bank_questions: 1,
      entries: [
        {
          id: "Q-DAN1-0001",
          fact_id: "",
          chapter: "DAN1",
          family: "",
          reference: "",
          content_sha256: "hash-real",
          risk_score: 0,
          automatic_flags: [],
          automatic_status: "passed",
          questions_file: "banks/final-2026/questions/DAN1.json",
        },
      ],
    })
  })

  it("deriva el shard de las unidades PR publicadas", () => {
    expect(
      parseHumanReviewIndex({
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [
          {
            question_id: "PR39-AUTH-0001",
            content_sha256: "hash-pr39",
            decision: "passed",
          },
        ],
      }).entries[0]
    ).toMatchObject({
      id: "PR39-AUTH-0001",
      chapter: "PR39",
      questions_file: "banks/final-2026/questions/PR39.json",
    })
  })

  it("acepta el prefijo de variantes competitivas publicado", () => {
    expect(
      parseHumanReviewIndex({
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [
          {
            question_id: "PV-DAN7-0001",
            content_sha256: "hash-variante",
            decision: "passed",
          },
        ],
      }).entries[0]
    ).toMatchObject({
      id: "PV-DAN7-0001",
      chapter: "DAN7",
      questions_file: "banks/final-2026/questions/DAN7.json",
    })
  })

  it("deriva el shard de variantes competitivas v13 con prefijos de release", () => {
    expect(
      parseHumanReviewIndex({
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [
          {
            question_id: "V13-R2-DAN11-C10-V002-F01",
            content_sha256: "hash-v13",
            decision: "passed",
          },
        ],
      }).entries[0]
    ).toMatchObject({
      id: "V13-R2-DAN11-C10-V002-F01",
      chapter: "DAN11",
      questions_file: "banks/final-2026/questions/DAN11.json",
    })
  })

  it("acepta los identificadores explícitos de variantes de presentación", () => {
    expect(
      parseHumanReviewIndex({
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [
          {
            question_id: "Q-DAN10-CENTRAL-0001::PRESENTATION-01",
            content_sha256: "hash-presentación",
            decision: "passed",
          },
        ],
      }).entries[0]
    ).toMatchObject({
      id: "Q-DAN10-CENTRAL-0001::PRESENTATION-01",
      chapter: "DAN10",
      questions_file: "banks/final-2026/questions/DAN10.json",
    })
  })

  it("rechaza entradas incompletas en vez de declararlas completadas", () => {
    expect(() =>
      parseHumanReviewIndex({
        schema_version: "10.0",
        total_reviewed: 2,
        entries: [
          { question_id: null, content_sha256: "hash-inválido" },
          { question_id: "sin-capitulo", content_sha256: "hash-inválido" },
        ],
      })
    ).toThrow("entrada 1")
  })

  it.each([
    [
      "esquema desconocido",
      { schema_version: "11.0", total_reviewed: 0, entries: [] },
      "esquema",
    ],
    [
      "total discrepante",
      { schema_version: "10.0", total_reviewed: 2, entries: [] },
      "total_reviewed",
    ],
    [
      "decisión inválida",
      {
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [
          {
            question_id: "DAN1-AUTH-0001",
            content_sha256: "hash-real",
            decision: "unknown",
          },
        ],
      },
      "decision",
    ],
  ])("rechaza %s", (_case, payload, message) => {
    expect(() => parseHumanReviewIndex(payload)).toThrow(message)
  })

  it.each([
    [
      "id sin question_id",
      {
        id: "DAN1-AUTH-0001",
        content_sha256: "hash-real",
        decision: "passed",
      },
      "question_id",
    ],
    [
      "id contradictorio",
      {
        id: "DAN1-AUTH-9999",
        question_id: "DAN1-AUTH-0001",
        content_sha256: "hash-real",
        decision: "passed",
      },
      "id no coincide",
    ],
    [
      "chapter contradictorio",
      {
        question_id: "DAN1-AUTH-0001",
        chapter: "DAN2",
        content_sha256: "hash-real",
        decision: "passed",
      },
      "chapter no coincide",
    ],
  ])("rechaza schema10 con %s", (_case, item, message) => {
    expect(() =>
      parseHumanReviewIndex({
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [item],
      })
    ).toThrow(message)
  })

  it("usa questions_file válido del índice y conserva sus metadatos", () => {
    expect(
      parseHumanReviewIndex({
        bank_questions: 1,
        entries: [
          {
            id: "custom-id",
            fact_id: "fact-1",
            chapter: "DAN12",
            family: "fill_choice",
            reference: "Daniel 12:1",
            content_sha256: "hash-custom",
            risk_score: 17,
            automatic_flags: ["manual-check"],
            automatic_status: "requires_attention",
            questions_file: "banks/final-2026/questions/DAN12.json",
          },
        ],
      }).entries[0]
    ).toMatchObject({
      id: "custom-id",
      fact_id: "fact-1",
      chapter: "DAN12",
      family: "fill_choice",
      reference: "Daniel 12:1",
      risk_score: 17,
      automatic_flags: ["manual-check"],
      automatic_status: "requires_attention",
      questions_file: "banks/final-2026/questions/DAN12.json",
    })
  })

  it("valida cada pregunta del shard antes de exponerla", () => {
    expect(() =>
      parseHumanReviewQuestionShard([
        {
          id: "DAN1-AUTH-0001",
          question: "Pregunta válida",
          options: ["A", "B"],
          correct_answer: "A",
          source_quote: "Texto fuente",
          why_distractors_fail: { B: "No corresponde." },
        },
        {
          id: "DAN1-AUTH-0002",
          question: "Pregunta corrupta",
          options: null,
          correct_answer: "A",
          source_quote: "Texto fuente",
        },
      ])
    ).toThrow("pregunta 2")
  })

  it.each([
    ["family", 42],
    ["chapter", null],
    ["reference", []],
  ])("rechaza el tipo inválido de %s en el shard", (field, value) => {
    expect(() =>
      parseHumanReviewQuestionShard(
        [
          {
            id: "DAN1-AUTH-0001",
            family: "single_choice_direct",
            chapter: "DAN1",
            reference: "Daniel 1:1",
            question: "Pregunta válida",
            options: ["A", "B"],
            correct_answer: "A",
            source_quote: "Texto fuente",
            why_distractors_fail: { B: "No corresponde." },
            [field]: value,
          },
        ],
        "DAN1"
      )
    ).toThrow(field)
  })

  it("rechaza chapter contradictorio con la unidad solicitada", () => {
    expect(() =>
      parseHumanReviewQuestionShard(
        [
          {
            id: "DAN1-AUTH-0001",
            chapter: "DAN2",
            question: "Pregunta válida",
            options: ["A", "B"],
            correct_answer: "A",
            source_quote: "Texto fuente",
          },
        ],
        "DAN1"
      )
    ).toThrow("no coincide")
  })

  it("rechaza why_distractors_fail cuando es un arreglo", () => {
    expect(() =>
      parseHumanReviewQuestionShard([
        {
          id: "DAN1-AUTH-0001",
          question: "Pregunta válida",
          options: ["A", "B"],
          correct_answer: "A",
          source_quote: "Texto fuente",
          why_distractors_fail: ["No corresponde."],
        },
      ])
    ).toThrow("distractores")
  })

  it("preserva el estado automático explícito del índice anterior", () => {
    expect(
      parseHumanReviewIndex({
        entries: [
          {
            ...entry("q1"),
            questions_file: "banks/final-2026/questions/DAN7.json",
          },
        ],
      }).entries[0]?.automatic_status
    ).toBe("passed")
  })

  it("sólo acredita decisiones cuya huella coincide con el contenido actual", () => {
    const result = reconcileHumanReview(
      [entry("q1"), entry("q2"), entry("q3")],
      [
        decision("q1"),
        { ...decision("q2"), disposition: "rejected" },
        decision("q3", "huella-obsoleta"),
      ]
    )

    expect(result.reviewed.map((item) => item.id)).toEqual(["q1", "q2"])
    expect(result.accepted.map((item) => item.id)).toEqual(["q1"])
    expect(result.rejected.map((item) => item.id)).toEqual(["q2"])
    expect(result.pending.map((item) => item.id)).toEqual(["q3"])
    expect(result.stale.map((item) => item.id)).toEqual(["q3"])
  })

  it("crea una decisión trazable y exige revisor", () => {
    expect(() =>
      buildHumanReviewDecision(entry("q1"), {
        reviewer: "   ",
        disposition: "approved",
        notes: "",
        reviewedAt: new Date("2026-08-28T12:00:00.000Z"),
      })
    ).toThrow("revisor")

    expect(
      buildHumanReviewDecision(entry("q1"), {
        reviewer: "  María  ",
        disposition: "rejected",
        notes: "  Distractor ambiguo.  ",
        reviewedAt: new Date("2026-08-28T12:00:00.000Z"),
      })
    ).toEqual({
      id: "q1",
      content_sha256: "hash-q1",
      reviewer: "María",
      reviewed_at: "2026-08-28T12:00:00.000Z",
      disposition: "rejected",
      notes: "Distractor ambiguo.",
    })
  })

  it("continúa por riesgo y permite acotar familia y capítulo", () => {
    const entries = [
      { ...entry("low"), risk_score: 2, chapter: "DAN8" },
      { ...entry("high"), risk_score: 20 },
      {
        ...entry("fill"),
        risk_score: 30,
        family: "fill_choice",
      },
    ]

    expect(selectNextHumanReview(entries, [], {})?.id).toBe("fill")
    expect(
      selectNextHumanReview(entries, [decision("fill")], {
        family: "single_choice_contextual",
        chapter: "DAN7",
      })?.id
    ).toBe("high")
  })
})
