import { describe, expect, it } from "vitest"

import {
  selectStratifiedSample,
  semanticAuditFlags,
} from "./competitive-audit.mjs"

describe("competitive audit sampling", () => {
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
})
