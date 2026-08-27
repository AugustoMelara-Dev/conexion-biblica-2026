import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { MassiveTrainingHub } from "@/components/massive-training-hub"
import type { SessionConfig } from "@/domain/types"

describe("centro de entrenamiento masivo", () => {
  it("presenta veinte modos en un selector compacto e inicia el campeonato", async () => {
    const onStart = vi.fn<(config: SessionConfig) => void>()
    render(<MassiveTrainingHub onStart={onStart} />)
    const select = screen.getByRole("combobox", { name: "Modo avanzado" })
    expect(screen.getAllByRole("option")).toHaveLength(20)
    await userEvent.selectOptions(select, "extreme-championship")
    await userEvent.click(screen.getByRole("button", { name: "Iniciar modo avanzado" }))
    expect(onStart).toHaveBeenCalledWith(
      expect.objectContaining({
        count: 200,
        bankSelection: "final-v7",
        massive: true,
        shuffleOptions: false,
        trainingPresetId: "extreme-championship",
        includeBlind: false,
      })
    )
  })

  it("expone el plan de 48 horas e inicia la simulación ciega final", async () => {
    const onStart = vi.fn<(config: SessionConfig) => void>()
    render(<MassiveTrainingHub onStart={onStart} />)
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
})
