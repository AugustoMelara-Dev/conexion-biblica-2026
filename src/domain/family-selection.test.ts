import { describe, expect, it } from "vitest"
import {
  filterEligibleQuestions,
  selectNextFamilyVariant,
  selectSessionQuestions,
} from "@/domain/session-selector"
import { createEmptyProgress } from "@/domain/mastery"
import type {
  AttemptRecord,
  Question,
  QuestionProgress,
  SessionConfig,
} from "@/domain/types"

function question(id: string, factKey: string, chapter = 1): Question {
  return {
    id,
    bankId: "prep",
    bankProfileId: "prep-v3",
    type: "single_choice",
    difficulty: 3,
    source: {
      work: "Daniel",
      version: "RVR95",
      chapter,
      reference: `Daniel ${chapter}:1`,
    },
    tags: [],
    factKey,
    question: id,
    options: [
      { id: "A", text: "Sí" },
      { id: "B", text: "No" },
    ],
    correctAnswer: ["A"],
  }
}

const config: SessionConfig = {
  mode: "training",
  count: 4,
  sourceWorks: ["Daniel"],
  chapters: [],
  difficulties: [],
  types: [],
  statuses: ["all"],
  shuffleQuestions: true,
  shuffleOptions: false,
  perQuestionSeconds: null,
  totalSeconds: null,
}

function progress(
  id: string,
  latest: AttemptRecord,
  timesIncorrect = 0
): QuestionProgress {
  return {
    ...createEmptyProgress(`prep:${id}`),
    timesSeen: timesIncorrect + (latest.isCorrect ? 1 : 0),
    timesCorrect: latest.isCorrect ? 1 : 0,
    timesIncorrect,
    timesUnanswered: latest.wasAnswered ? 0 : 1,
    averageResponseTimeMs: latest.wasAnswered ? latest.responseTimeMs : 0,
    lastResponseTimeMs: latest.responseTimeMs,
    lastSeenAt: latest.timestamp,
    history: [latest],
  }
}

describe("selección por familias", () => {
  it("agota variantes no vistas antes de reciclar", () => {
    const family = [
      question("a", "fact"),
      question("b", "fact"),
      question("c", "fact"),
    ]
    expect(
      selectNextFamilyVariant(family, new Set(["prep:a", "prep:b"]), 4)?.id
    ).toBe("c")
    expect(family.map((item) => item.id)).toContain(
      selectNextFamilyVariant(
        family,
        new Set(["prep:a", "prep:b", "prep:c"]),
        4
      )?.id
    )
  })

  it("evita familias consecutivas cuando hay alternativa", () => {
    const selected = selectSessionQuestions(
      [
        question("a1", "fact-a", 1),
        question("a2", "fact-a", 2),
        question("b1", "fact-b", 3),
        question("c1", "fact-c", 4),
      ],
      new Map(),
      config,
      9
    )
    for (let index = 1; index < selected.length; index += 1) {
      expect(selected[index].factKey).not.toBe(selected[index - 1].factKey)
    }
  })

  it("no presenta dos redacciones idénticas de bancos distintos", () => {
    const master = {
      ...question("master", "fact-a"),
      bankId: "master-v2",
      bankProfileId: "master-v2" as const,
      question: "¿La misma pregunta?",
    }
    const prep = {
      ...question("prep", "fact-a"),
      bankId: "prep-v3",
      bankProfileId: "prep-v3" as const,
      question: "¿La misma pregunta?",
      memoryCue: "Pista",
    }
    const selected = selectSessionQuestions(
      [master, prep, question("different", "fact-b")],
      new Map(),
      { ...config, count: 3 },
      3
    )
    expect(selected).toHaveLength(2)
    expect(selected).toContain(prep)
    expect(selected).not.toContain(master)
  })

  it("deja los estados masivos al selector por factId", () => {
    const alternateVariant = question("alternate", "failed-fact")

    expect(
      filterEligibleQuestions([alternateVariant], new Map(), {
        ...config,
        statuses: ["failed"],
        massive: true,
        trainingPresetId: "previous-errors",
      })
    ).toEqual([alternateVariant])
  })

  it("en repaso ordena el último error o blanco antes que una correcta lenta o segura", () => {
    const secure = question("secure", "fact-secure", 1)
    const slow = question("slow", "fact-slow", 2)
    const incorrect = question("incorrect", "fact-incorrect", 3)
    const unanswered = question("unanswered", "fact-unanswered", 4)
    const selected = selectSessionQuestions(
      [secure, slow, incorrect, unanswered],
      new Map([
        [
          "prep:secure",
          progress(
            "secure",
            {
              timestamp: 4,
              isCorrect: true,
              wasAnswered: true,
              responseTimeMs: 2_000,
              reason: "correct",
            },
            20
          ),
        ],
        [
          "prep:slow",
          progress("slow", {
            timestamp: 4,
            isCorrect: true,
            wasAnswered: true,
            responseTimeMs: 6_001,
            reason: "correct",
          }),
        ],
        [
          "prep:incorrect",
          progress(
            "incorrect",
            {
              timestamp: 4,
              isCorrect: false,
              wasAnswered: true,
              responseTimeMs: 1_000,
              reason: "incorrect",
            },
            1
          ),
        ],
        [
          "prep:unanswered",
          progress(
            "unanswered",
            {
              timestamp: 4,
              isCorrect: false,
              wasAnswered: false,
              responseTimeMs: 0,
              reason: "unanswered",
            },
            1
          ),
        ],
      ]),
      { ...config, mode: "smart-review" },
      7
    )

    expect(new Set(selected.slice(0, 2).map((item) => item.id))).toEqual(
      new Set(["incorrect", "unanswered"])
    )
    expect(selected[2]?.id).toBe("slow")
    expect(selected[3]?.id).toBe("secure")
  })
})
