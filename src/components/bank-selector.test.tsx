import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { BankSelector } from "@/components/bank-selector"

describe("selector de versión", () => {
  it("expone V1, V2 y Mixto como opciones accesibles", async () => {
    const onChange = vi.fn()
    render(<BankSelector value="legacy-v1" onChange={onChange} legacyCount={1160} masterCount={3558} prepCount={500} />)

    expect(screen.getByRole("radiogroup", { name: "Versión del banco" })).toBeInTheDocument()
    expect(screen.getByRole("radio", { name: /V1 — Clásica/ })).toBeChecked()
    await userEvent.click(screen.getByRole("radio", { name: /V2 — Banco Maestro/ }))
    expect(onChange).toHaveBeenCalledWith("master-v2")
    await userEvent.click(screen.getByRole("radio", { name: /Mixto — V1 \+ V2 \+ V3/ }))
    expect(onChange).toHaveBeenCalledWith("mixed")
    await userEvent.click(screen.getByRole("radio", { name: /V3 — Preparación 4 días/ }))
    expect(onChange).toHaveBeenCalledWith("prep-v3")
  })

  it("muestra el total agregado de V3 y lo recomienda", () => {
    render(<BankSelector value="prep-v3" onChange={vi.fn()} legacyCount={1160} masterCount={3558} prepCount={500} />)

    expect(screen.getByRole("radio", { name: /V3 — Preparación 4 días/ })).toBeChecked()
    expect(screen.getByText("500 preguntas")).toBeInTheDocument()
    expect(screen.getByText("5,218 preguntas")).toBeInTheDocument()
    expect(screen.getByText("Recomendado")).toBeInTheDocument()
  })
})
