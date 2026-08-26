import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { AnswerLearningFeedback } from "@/components/answer-learning-feedback"
import type { Question } from "@/domain/types"

const question: Question = {
  id: "Q1", type: "single_choice", difficulty: 4,
  source: { work: "Daniel", version: "RVR1995", chapter: 7, reference: "Daniel 7:19" },
  tags: [], factKey: "F1", question: "¿Qué detalle se añade?",
  options: [{ id: "A", text: "Tres costillas" }, { id: "B", text: "Uñas de bronce" }],
  correctAnswer: ["B"], correctAnswerText: "Uñas de bronce",
  sourceQuote: "sus uñas eran de bronce",
  explanation: "Daniel 7:19 añade las uñas de bronce.",
  whyDistractorsFail: { "Tres costillas": "Corresponde a la segunda bestia de Daniel 7:5, no a la cuarta." },
}

describe("AnswerLearningFeedback", () => {
  it("explains only the selected contrast and offers understanding actions", async () => {
    const confused = vi.fn()
    render(<AnswerLearningFeedback question={question} selectedAnswer="A" isCorrect={false} onUnderstood={() => undefined} onConfused={confused} />)
    expect(screen.getByText(/Corresponde a la segunda bestia/)).toBeInTheDocument()
    expect(screen.getByText("Daniel 7:19")).toBeInTheDocument()
    expect(screen.queryByText(/Por qué no aplican las otras opciones/)).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole("button", { name: "Todavía lo confundo" }))
    expect(confused).toHaveBeenCalledOnce()
  })
})
