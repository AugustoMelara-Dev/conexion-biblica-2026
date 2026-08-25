import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { MemoryCue } from "@/components/quiz-page"

describe("pista de memoria", () => {
  it("muestra la pista únicamente cuando existe", () => {
    const { rerender } = render(<MemoryCue cue="D1: 10 días y 10 veces." />)
    expect(screen.getByText("Pista para recordar")).toBeInTheDocument()
    expect(screen.getByText("D1: 10 días y 10 veces.")).toBeInTheDocument()

    rerender(<MemoryCue />)
    expect(screen.queryByText("Pista para recordar")).not.toBeInTheDocument()
  })
})
