import { describe, expect, it } from "vitest"

import {
  mapLegacyProgressFromSignatureIndex,
  mapLegacyProgressToFacts,
  migrationSignature,
} from "@/storage/history-migration"
import type { Question, QuestionProgress } from "@/domain/types"

const gold: Question = {
  id: "DAN7-G1",
  bankId: "consolidation-v5",
  bankProfileId: "consolidation-v5",
  type: "single_choice",
  difficulty: 4,
  source: { work: "Daniel", version: "RVR95", chapter: 7, reference: "Daniel 7:9" },
  tags: [],
  factKey: "DAN7-V09-F1",
  factId: "DAN7-V09-F1",
  question: "¿Con qué se compara el pelo?",
  options: [{ id: "A", text: "Lana limpia" }, { id: "B", text: "Nieve" }],
  correctAnswer: ["A"],
  correctAnswerText: "Lana limpia",
  sourceQuote: "el pelo de su cabeza, como lana limpia",
}

const progress: QuestionProgress = {
  questionKey: "curated-v4:old-1",
  timesSeen: 2,
  timesCorrect: 1,
  timesIncorrect: 1,
  timesUnanswered: 0,
  currentCorrectStreak: 1,
  averageResponseTimeMs: 4000,
  bestResponseTimeMs: 3000,
  lastResponseTimeMs: 5000,
  lastSeenAt: 10,
  masteryScore: 0.5,
  favorite: true,
  markedDifficult: true,
  reported: false,
  history: [],
}

describe("legacy history migration", () => {
  it("maps only an unambiguous reference and answer match", () => {
    const old = { ...gold, id: "old-1", bankId: "curated-v4", bankProfileId: "curated-v4" as const }
    const result = mapLegacyProgressToFacts([old], [progress], [gold])
    expect(result.mapped).toHaveLength(1)
    expect(result.mapped[0]).toMatchObject({ factId: "DAN7-V09-F1", sourceQuestionKey: progress.questionKey })
    expect(result.legacy).toHaveLength(0)
  })

  it("keeps ambiguous matches as legacy events without mastery", () => {
    const old = { ...gold, id: "old-1", bankId: "curated-v4", bankProfileId: "curated-v4" as const }
    const duplicate = { ...gold, id: "DAN7-G2", factId: "DAN7-V09-F2", factKey: "DAN7-V09-F2" }
    const result = mapLegacyProgressToFacts([old], [progress], [gold, duplicate])
    expect(result.mapped).toHaveLength(0)
    expect(result.legacy[0]).toMatchObject({ reason: "ambiguous_match" })
  })

  it("clasifica no_match como terminal contra el índice completo", () => {
    const old = { ...gold, id: "old-1", bankId: "curated-v4", bankProfileId: "curated-v4" as const }
    const result = mapLegacyProgressFromSignatureIndex(
      [old],
      [progress],
      new Map()
    )

    expect(result.mapped).toEqual([])
    expect(result.legacy).toEqual([
      expect.objectContaining({ reason: "no_match" }),
    ])
  })

  it("clasifica dos facts con la misma firma como ambiguous", () => {
    const old = { ...gold, id: "old-1", bankId: "curated-v4", bankProfileId: "curated-v4" as const }
    const result = mapLegacyProgressFromSignatureIndex(
      [old],
      [progress],
      new Map([
        [migrationSignature(old), new Set(["FACT-1", "FACT-2"])],
      ])
    )

    expect(result.mapped).toEqual([])
    expect(result.legacy).toEqual([
      expect.objectContaining({ reason: "ambiguous_match" }),
    ])
  })
})
