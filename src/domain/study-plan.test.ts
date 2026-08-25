import { describe, expect, it } from "vitest"
import { getStudyDay, studyDayMatchesQuestion } from "@/domain/study-plan"
import type { Question } from "@/domain/types"

function question(work: Question["source"]["work"], chapter: number) {
  return { source: { work, chapter } } as Question
}

describe("plan de estudio de cuatro días", () => {
  it("distribuye exactamente el material en cuatro días", () => {
    expect(getStudyDay(1).chapters).toEqual([
      { work: "Daniel", chapters: [1, 2, 3] },
      { work: "Profetas y Reyes", chapters: [39] },
    ])
    expect(getStudyDay(4).chapters).toEqual([
      { work: "Daniel", chapters: [10, 11, 12] },
      { work: "Profetas y Reyes", chapters: [44] },
    ])
  })

  it("no mezcla un capítulo de otro día", () => {
    expect(studyDayMatchesQuestion(question("Daniel", 4), 1)).toBe(false)
    expect(studyDayMatchesQuestion(question("Daniel", 4), 2)).toBe(true)
    expect(studyDayMatchesQuestion(question("Profetas y Reyes", 43), 3)).toBe(true)
    expect(studyDayMatchesQuestion(question("Profetas y Reyes", 43), 4)).toBe(false)
  })
})
