import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { BankSelector } from "@/components/bank-selector"

describe("selector de versión", () => {
  it("expone V4 recomendado, V2 técnico y Mixto curado como opciones accesibles", async () => {
    const onChange = vi.fn()
    render(
      <BankSelector
        value="curated-v4"
        onChange={onChange}
        legacyCount={10}
        masterCount={3558}
        prepCount={500}
        curatedCount={3200}
      />,
    )

    expect(screen.getByRole("radiogroup", { name: "Versión del banco" })).toBeInTheDocument()
    expect(screen.getByRole("radio", { name: /V4 — Banco Curado/ })).toBeChecked()
    expect(screen.getByText("Recomendado")).toBeInTheDocument()
    expect(screen.getByText(/Fuente técnica/)).toBeInTheDocument()
    expect(screen.getByText("3,200 preguntas")).toBeInTheDocument()
    expect(screen.getByText("3,710 preguntas")).toBeInTheDocument()
    await userEvent.click(screen.getByRole("radio", { name: /V2 — Fuente técnica/ }))
    expect(onChange).toHaveBeenCalledWith("master-v2")
    await userEvent.click(screen.getByRole("radio", { name: /Mixto curado/ }))
    expect(onChange).toHaveBeenCalledWith("mixed")
    await userEvent.click(screen.getByRole("radio", { name: /V3 — Preparación intensiva de 4 días/ }))
    expect(onChange).toHaveBeenCalledWith("prep-v3")
  })

  it("muestra las cinco opciones en el orden de curación", () => {
    render(
      <BankSelector
        value="curated-v4"
        onChange={vi.fn()}
        legacyCount={10}
        masterCount={3558}
        prepCount={500}
        curatedCount={3200}
      />,
    )

    expect(screen.getAllByRole("radio").map((radio) => radio.getAttribute("value"))).toEqual([
      "curated-v4",
      "prep-v3",
      "legacy-v1",
      "mixed",
      "master-v2",
    ])
    expect(screen.getByText(/puede contener redacción de auditoría/)).toBeInTheDocument()
  })
})
