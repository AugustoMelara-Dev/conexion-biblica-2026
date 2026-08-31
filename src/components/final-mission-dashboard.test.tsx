import { act, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { FinalMissionDashboard } from "@/components/final-mission-dashboard"

describe("FinalMissionDashboard", () => {
  it("presenta la Ruta del Día vigente sin el copy obsoleto del 29", async () => {
    const onContinue = vi.fn()
    render(
      <FinalMissionDashboard
        now={new Date("2026-08-31T08:00:00-06:00")}
        onContinue={onContinue}
      />
    )

    expect(
      screen.getByRole("heading", { name: "RUTA DEL DÍA" })
    ).toBeInTheDocument()
    expect(screen.queryByText(/GANAR EL 29/i)).not.toBeInTheDocument()
    expect(screen.getByText("Daniel 1–6")).toBeInTheDocument()
    expect(screen.getByText("Profetas y Reyes 39–41")).toBeInTheDocument()
    expect(screen.getByText("1,400 preguntas programadas")).toBeInTheDocument()

    await userEvent.click(
      screen.getByRole("button", { name: "CONTINUAR MI RUTA" })
    )
    expect(onContinue).toHaveBeenCalledWith(
      expect.objectContaining({ id: "2026-08-31-new", kind: "new", count: 850 })
    )
  })

  it("identifica el calentamiento opcional del sábado", () => {
    render(
      <FinalMissionDashboard
        now={new Date("2026-09-05T08:00:00-06:00")}
        onContinue={vi.fn()}
      />
    )

    expect(screen.getByText("Calentamiento opcional")).toBeInTheDocument()
    expect(screen.getByText("15 preguntas conocidas")).toBeInTheDocument()
    expect(screen.getByText(/Nada nuevo/)).toBeInTheDocument()
  })

  it("calcula el progreso solo con bloques accionables y excluye la lectura", () => {
    render(
      <FinalMissionDashboard
        now={new Date("2026-08-31T08:00:00-06:00")}
        completedMissionIds={["2026-08-31-new"]}
        onContinue={vi.fn()}
      />
    )

    expect(screen.getByText("25%")).toBeInTheDocument()
    expect(screen.getByText("1 de 4 bloques")).toBeInTheDocument()
  })

  it("cierra la ruta sin repetir el último bloque al completar todo", () => {
    render(
      <FinalMissionDashboard
        now={new Date("2026-08-31T08:00:00-06:00")}
        completedMissionIds={[
          "2026-08-31-new",
          "2026-08-31-hard-expert",
          "2026-08-31-review",
          "2026-08-31-simulation",
        ]}
        onContinue={vi.fn()}
      />
    )

    expect(
      screen.getByRole("heading", { name: "RUTA DEL DÍA COMPLETADA" })
    ).toBeInTheDocument()
    expect(
      screen.queryByRole("button", { name: "CONTINUAR MI RUTA" })
    ).not.toBeInTheDocument()
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
        now={new Date("2026-09-01T08:00:00-06:00")}
        onContinue={onContinue}
        onManual={vi.fn()}
      />
    )

    const button = screen.getByRole("button", { name: "CONTINUAR MI RUTA" })
    await user.click(button)

    expect(button).toBeDisabled()
    expect(
      screen.getByRole("button", { name: "Configurar manualmente" })
    ).toBeDisabled()
    expect(button).toHaveAttribute("aria-busy", "true")
    expect(screen.getByRole("status")).toHaveTextContent("Preparando el bloque")
    await user.click(button)
    expect(onContinue).toHaveBeenCalledTimes(1)

    await act(async () => resolveStart())
  })
})
