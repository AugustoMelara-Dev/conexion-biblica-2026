import { describe, expect, it } from "vitest"

import {
  buildHumanReviewDecision,
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

const decision = (
  id: string,
  hash = `hash-${id}`,
): HumanReviewDecision => ({
  id,
  content_sha256: hash,
  reviewer: "Revisor humano",
  reviewed_at: "2026-08-28T12:00:00.000Z",
  disposition: "approved",
  notes: "",
})

describe("auditoría editorial humana", () => {
  it("sólo acredita decisiones cuya huella coincide con el contenido actual", () => {
    const result = reconcileHumanReview(
      [entry("q1"), entry("q2")],
      [decision("q1"), decision("q2", "huella-obsoleta")],
    )

    expect(result.reviewed.map((item) => item.id)).toEqual(["q1"])
    expect(result.pending.map((item) => item.id)).toEqual(["q2"])
    expect(result.stale.map((item) => item.id)).toEqual(["q2"])
  })

  it("crea una decisión trazable y exige revisor", () => {
    expect(() =>
      buildHumanReviewDecision(entry("q1"), {
        reviewer: "   ",
        disposition: "approved",
        notes: "",
        reviewedAt: new Date("2026-08-28T12:00:00.000Z"),
      }),
    ).toThrow("revisor")

    expect(
      buildHumanReviewDecision(entry("q1"), {
        reviewer: "  María  ",
        disposition: "rejected",
        notes: "  Distractor ambiguo.  ",
        reviewedAt: new Date("2026-08-28T12:00:00.000Z"),
      }),
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

    expect(selectNextHumanReview(entries, [], {} )?.id).toBe("fill")
    expect(
      selectNextHumanReview(entries, [decision("fill")], {
        family: "single_choice_contextual",
        chapter: "DAN7",
      })?.id,
    ).toBe("high")
  })
})
