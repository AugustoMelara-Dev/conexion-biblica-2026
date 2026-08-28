import { describe, expect, it } from "vitest"

import * as competitiveAudit from "./competitive-audit.mjs"

import {
  buildExhaustiveReviewQueue,
  buildPublicReviewIndex,
  buildCompetitiveAuditReport,
  exhaustiveRiskFlags,
  selectStratifiedSample,
  semanticAuditFlags,
} from "./competitive-audit.mjs"

describe("competitive audit sampling", () => {
  it("mantiene los rechazos humanos como defectos abiertos", () => {
    expect(
      competitiveAudit.summarizeHumanReviewQueue?.([
        { review_status: "pending_human", disposition: null },
        { review_status: "reviewed", disposition: "approved" },
        { review_status: "reviewed", disposition: "corrected" },
        { review_status: "reviewed", disposition: "rejected" },
      ]) ?? null,
    ).toEqual({
      reviewed: 3,
      accepted: 2,
      rejected: 1,
      pending_human: 1,
    })
  })

  it("bloquea el cierre editorial mientras exista un rechazo humano", () => {
    expect(
      competitiveAudit.hasBlockingHumanReviewFindings?.({
        rejected: 1,
        pending_human: 0,
      }) ?? null,
    ).toBe(true)
    expect(
      competitiveAudit.hasBlockingHumanReviewFindings?.({
        rejected: 0,
        pending_human: 12000,
      }) ?? null,
    ).toBe(false)
  })

  it("builds a reproducible report for identical audited input", () => {
    const input = {
      bank: "BANK-1",
      bankQuestions: 12000,
      chapters: ["DAN7"],
      families: ["fill_choice"],
      perStratum: 3,
      automaticFlags: [],
      sample: [{ id: "DAN7-FILL-1" }],
    }

    expect(buildCompetitiveAuditReport(input)).toEqual(
      buildCompetitiveAuditReport(input)
    )
    expect(buildCompetitiveAuditReport(input)).toEqual({
      bank: "BANK-1",
      bank_questions: 12000,
      sample_size: 1,
      design: {
        chapters: ["DAN7"],
        families: ["fill_choice"],
        per_stratum: 3,
        strata: 1,
      },
      automatic_flags: [],
      sample: [{ id: "DAN7-FILL-1" }],
    })
  })

  it("selects the requested number from every chapter and high-risk family", () => {
    const chapters = ["DAN7", "PR39"]
    const families = ["fill_choice", "true_false_false"]
    const rows = chapters.flatMap((chapter) =>
      families.flatMap((family) =>
        Array.from({ length: 5 }, (_, index) => ({
          id: `${chapter}-${family}-${index}`,
          chapter,
          family: family === "true_false_false" ? "true_false" : family,
          correct_answer:
            family === "true_false_false" ? "Falso" : `respuesta-${index}`,
        }))
      )
    )

    const sample = selectStratifiedSample(rows, {
      chapters,
      families,
      perStratum: 3,
    })

    expect(sample).toHaveLength(12)
    for (const chapter of chapters) {
      for (const family of families) {
        expect(
          sample.filter(
            (row) =>
              row.chapter === chapter &&
              (family === "true_false_false"
                ? row.family === "true_false" && row.correct_answer === "Falso"
                : row.family === family)
          )
        ).toHaveLength(3)
      }
    }
  })

  it("fails loudly when a requested stratum is too small", () => {
    expect(() =>
      selectStratifiedSample(
        [
          {
            id: "DAN7-FILL-1",
            chapter: "DAN7",
            family: "fill_choice",
            correct_answer: "respuesta",
          },
        ],
        {
          chapters: ["DAN7"],
          families: ["fill_choice"],
          perStratum: 2,
        }
      )
    ).toThrow("DAN7/fill_choice")
  })

  it("accepts a false statement whose precise correction is grounded in the quote", () => {
    expect(
      semanticAuditFlags({
        family: "true_false",
        question: "Verdadero o falso: Según Daniel 7:19, tenía uñas de plata.",
        options: ["Verdadero", "Falso"],
        correct_option: 1,
        correct_answer: "Falso",
        source_quote: "tenía uñas de bronce",
        incorrect_detail: "plata",
        correction: "bronce",
        corrected_statement: "Según Daniel 7:19, tenía uñas de bronce.",
      })
    ).toEqual([])
  })

  it("enumerates every question once and prioritizes structural findings", () => {
    const queue = buildExhaustiveReviewQueue([
      {
        id: "SAFE",
        chapter: "DAN7",
        family: "fill_choice",
        reference: "Daniel 7:1",
        question: "Completa: ____.",
        options: ["sueño", "visión"],
        correct_option: 0,
        correct_answer: "sueño",
        source_quote: "sueño",
      },
      {
        id: "BROKEN",
        chapter: "PR39",
        family: "true_false",
        reference: "PR 39, p. 1",
        question: "Verdadero o falso",
        options: ["Verdadero", "Falso"],
        correct_option: 0,
        correct_answer: "Falso",
        source_quote: "la respuesta real",
      },
    ])

    expect(queue).toHaveLength(2)
    expect(new Set(queue.map((row) => row.id)).size).toBe(2)
    expect(queue[0].id).toBe("BROKEN")
    expect(queue[0].review_status).toBe("pending_human")
    expect(queue[0].automatic_flags).toContain("answer_index_mismatch")
    expect(queue[1].risk_score).toBeLessThan(queue[0].risk_score)
  })

  it("publica un índice completo con la ruta del capítulo sin decisiones humanas", () => {
    const queue = buildExhaustiveReviewQueue([
      {
        id: "DAN7-Q1",
        chapter: "DAN7",
        family: "fill_choice",
        reference: "Daniel 7:1",
        question: "Completa: ____.",
        options: ["sueño", "visión"],
        correct_option: 0,
        correct_answer: "sueño",
        source_quote: "sueño",
      },
    ])

    expect(
      buildPublicReviewIndex(queue, [
        {
          chapter: "DAN7",
          questions_file: "banks/final-2026/questions/DAN7.json",
        },
      ]),
    ).toEqual([
      expect.objectContaining({
        id: "DAN7-Q1",
        questions_file: "banks/final-2026/questions/DAN7.json",
      }),
    ])
  })

  it("flags contextual distractors without auditable source references", () => {
    expect(
      exhaustiveRiskFlags({
        id: "CTX",
        family: "single_choice_contextual",
        question: "¿Quién aparece aquí?",
        options: ["Daniel", "Gabriel", "Miguel", "Darío"],
        correct_option: 0,
        correct_answer: "Daniel",
        source_quote: "Daniel respondió",
        trap_type: "true_in_other_context",
        why_distractors_fail: {
          Gabriel: "No corresponde aquí.",
          Miguel: "No corresponde aquí.",
          Darío: "No corresponde aquí.",
        },
      })
    ).toContain("contextual_distractor_without_source_reference")
  })

  it("flags the deprecated generic wording in false statements", () => {
    expect(
      exhaustiveRiskFlags({
        id: "TF",
        family: "true_false",
        question: "Verdadero o falso",
        statement: "Según Daniel 7:1 aparece la expresión visión.",
        options: ["Verdadero", "Falso"],
        correct_option: 1,
        correct_answer: "Falso",
        source_quote: "sueño",
        incorrect_detail: "visión",
        correction: "sueño",
        corrected_statement: "Según Daniel 7:1 aparece la expresión sueño.",
      })
    ).toContain("deprecated_generic_false_wording")
  })
})
