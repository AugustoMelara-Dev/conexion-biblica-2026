import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { MassiveTrainingHub } from "@/components/massive-training-hub"
import type { SessionConfig } from "@/domain/types"

describe("centro de entrenamiento masivo", () => {
  it("muestra una sola acción recomendada y oculta los veinte modos hasta pedirlos", async () => {
    const onStart = vi.fn<(config: SessionConfig) => void>()
    render(<MassiveTrainingHub onStart={onStart} />)
    expect(screen.getByText("12,000 preguntas GOLD")).toBeVisible()
    expect(screen.getByText("3,000 hechos")).toBeVisible()
    expect(screen.getByText("Ronda recomendada")).toBeVisible()
    expect(screen.queryByRole("combobox", { name: "Modo avanzado" })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole("button", { name: "Ver plan y modos" }))
    const select = screen.getByRole("combobox", { name: "Modo avanzado" })
    expect(screen.getAllByRole("option")).toHaveLength(20)
    await userEvent.selectOptions(select, "extreme-championship")
    await userEvent.click(screen.getByRole("button", { name: "Iniciar modo avanzado" }))
    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        count: 200,
        bankSelection: "final-v7",
        massive: true,
        shuffleOptions: true,
        trainingPresetId: "extreme-championship",
        includeBlind: false,
      })
    )
  })

  it("expone el plan de 48 horas e inicia la simulación ciega final", async () => {
    const onStart = vi.fn<(config: SessionConfig) => void>()
    render(<MassiveTrainingHub onStart={onStart} />)
    await userEvent.click(screen.getByRole("button", { name: "Ver plan y modos" }))
    expect(screen.getByText("PLAN FINAL — 48 HORAS")).toBeVisible()
    await userEvent.click(
      screen.getByRole("button", { name: /Simulación ciega final.*100/i })
    )
    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        count: 100,
        trainingPresetId: "blind-simulation",
        includeBlind: true,
      })
    )
  })

  it("inicia la final nacional desde la acción principal sin configurar nada", async () => {
    const onStart = vi.fn<(config: SessionConfig) => void>()
    render(<MassiveTrainingHub onStart={onStart} />)
    await userEvent.click(
      screen.getByRole("button", { name: /Empezar final nacional.*100/i }),
    )
    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        count: 100,
        trainingPresetId: "national-final",
        massive: true,
      }),
    )
  })
})
