import { act, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { FinalMissionDashboard } from "@/components/final-mission-dashboard"

describe("FinalMissionDashboard", () => {
  it("shows one primary action and starts the next mission", async () => {
    const onContinue = vi.fn()
    render(
      <FinalMissionDashboard
        now={new Date("2026-08-26T08:00:00-06:00")}
        onContinue={onContinue}
        onManual={vi.fn()}
      />
    )
    expect(
      screen.getByRole("heading", { name: /PLAN FINAL — GANAR EL 29/i })
    ).toBeInTheDocument()
    expect(
      screen.getByRole("progressbar", { name: "Progreso de la misión de hoy" })
    ).toBeInTheDocument()
    const button = screen.getByRole("button", { name: "CONTINUAR MI MISIÓN" })
    await userEvent.click(button)
    expect(onContinue).toHaveBeenCalledWith(
      expect.objectContaining({ id: "26-cold-tier-a", count: 150 })
    )
    expect(
      screen.getAllByRole("button", { name: "CONTINUAR MI MISIÓN" })
    ).toHaveLength(1)
  })

  it("muestra que está preparando la ronda y bloquea clics duplicados", async () => {
    let resolveStart!: () => void
    const onContinue = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveStart = resolve
        })
    )
    const user = userEvent.setup()
    render(
      <FinalMissionDashboard
        now={new Date("2026-08-26T08:00:00-06:00")}
        onContinue={onContinue}
        onManual={vi.fn()}
      />
    )

    const button = screen.getByRole("button", { name: /CONTINUAR MI MISIÓN/i })
    await user.click(button)

    expect(button).toBeDisabled()
    expect(screen.getByRole("button", { name: "Configurar manualmente" })).toBeDisabled()
    expect(button).toHaveAttribute("aria-busy", "true")
    expect(screen.getByRole("status")).toHaveTextContent(
      "Preparando 150 preguntas"
    )
    await user.click(button)
    expect(onContinue).toHaveBeenCalledTimes(1)

    await act(async () => resolveStart())
  })
})
