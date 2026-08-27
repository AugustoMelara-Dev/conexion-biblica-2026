import { describe, expect, it } from "vitest"
import { BANK_DEFINITIONS, filterQuestionsForSelection, filterReportsForSelection, filterSessionsForSelection, questionBelongsToSelection } from "@/domain/banks"
import type { Question, QuestionReport, Session } from "@/domain/types"

function question(bankProfileId: string) {
  return { bankProfileId } as Question
}

describe("selecciones de bancos", () => {
  it("declara el banco final V9 de doce mil preguntas sin cambiar el perfil histórico", () => {
    expect(BANK_DEFINITIONS["final-v7"]).toMatchObject({
      version: "9.0",
      expectedQuestionCount: 12000,
    })
  })

  it("V3 contiene sólo el banco curado de 500", () => {
    const master = question("master-v2")
    const supplement = question("prep-v3")
    const legacy = question("legacy-v1")

    expect(questionBelongsToSelection(master, "prep-v3")).toBe(false)
    expect(questionBelongsToSelection(supplement, "prep-v3")).toBe(true)
    expect(questionBelongsToSelection(legacy, "prep-v3")).toBe(false)
    expect(filterQuestionsForSelection([legacy, master, supplement], "prep-v3")).toEqual([supplement])
  })

  it("filtra sesiones y reportes históricos de V2 en mixto", () => {
    const legacy = question("legacy-v1")
    const master = question("master-v2")
    const curated = question("curated-v4")
    const questions = [
      { ...legacy, id: "legacy-v1", bankId: "legacy-v1" },
      { ...master, id: "master-v2", bankId: "master-v2" },
      { ...curated, id: "curated-v4", bankId: "curated-v4" },
    ] as Question[]
    const session = {
      id: "mixed-history",
      questionKeys: ["legacy-v1:legacy-v1", "master-v2:master-v2", "curated-v4:curated-v4"],
      answers: [
        { questionKey: "legacy-v1:legacy-v1" },
        { questionKey: "master-v2:master-v2" },
        { questionKey: "curated-v4:curated-v4" },
      ],
    } as unknown as Session
    const reports = [
      { id: "r1", questionKey: "master-v2:master-v2", question: questions[1] },
      { id: "r2", questionKey: "curated-v4:curated-v4", question: questions[2] },
    ] as unknown as QuestionReport[]

    const scopedSessions = filterSessionsForSelection([session], questions, "mixed")
    const scopedReports = filterReportsForSelection(reports, questions, "mixed")

    expect(scopedSessions[0].questionKeys).toEqual(["legacy-v1:legacy-v1", "curated-v4:curated-v4"])
    expect(scopedSessions[0].answers.map((answer) => answer.questionKey)).toEqual(["legacy-v1:legacy-v1", "curated-v4:curated-v4"])
    expect(scopedReports.map((report) => report.questionKey)).toEqual(["curated-v4:curated-v4"])
  })
})
