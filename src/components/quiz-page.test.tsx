import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { MemoryCue, QuizPage } from "@/components/quiz-page"
import type { Question, SessionConfig } from "@/domain/types"

vi.mock("@/app/app-state", () => ({
  useApp: () => ({
    progress: new Map(),
    recordAnswer: vi.fn(),
    recordReport: vi.fn(),
  }),
}))

describe("pista de memoria", () => {
  it("muestra la pista únicamente cuando existe", () => {
    const { rerender } = render(<MemoryCue cue="D1: 10 días y 10 veces." />)
    expect(screen.getByText("Pista para recordar")).toBeInTheDocument()
    expect(screen.getByText("D1: 10 días y 10 veces.")).toBeInTheDocument()

    rerender(<MemoryCue />)
    expect(screen.queryByText("Pista para recordar")).not.toBeInTheDocument()
  })
})

describe("badge de perfil del banco", () => {
  it("expone el ID estable del perfil curado", () => {
    const question: Question = {
      id: "curated-question",
      bankId: "curated-v4",
      bankProfileId: "curated-v4",
      type: "single_choice",
      difficulty: 3,
      source: { work: "Daniel", version: "RVR95", chapter: 1, reference: "Daniel 1:1" },
      tags: [],
      factKey: "FACT-D01-001",
      question: "¿Pregunta de prueba?",
      options: [{ id: "A", text: "Respuesta" }],
      correctAnswer: ["A"],
      answerMode: "option_id",
    }
    const config: SessionConfig = {
      mode: "learn",
      count: 1,
      sourceWorks: ["Daniel"],
      chapters: [1],
      difficulties: [3],
      types: ["single_choice"],
      statuses: ["all"],
      shuffleQuestions: false,
      shuffleOptions: false,
      perQuestionSeconds: null,
      totalSeconds: null,
      bankSelection: "curated-v4",
      strategy: "coverage-cycle",
    }

    render(<QuizPage questions={[question]} config={config} onFinish={vi.fn()} onExit={vi.fn()} />)

    expect(screen.getByText("V4", { exact: true })).toHaveAttribute("data-bank-profile", "curated-v4")
  })
})
