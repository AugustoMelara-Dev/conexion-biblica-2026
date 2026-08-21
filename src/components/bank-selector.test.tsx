import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { BankSelector } from "@/components/bank-selector"

describe("selector de versión", () => {
  it("expone V1, V2 y Mixto como opciones accesibles", async () => {
    const onChange = vi.fn()
    render(<BankSelector value="legacy-v1" onChange={onChange} legacyCount={1160} masterCount={3558} />)

    expect(screen.getByRole("radiogroup", { name: "Versión del banco" })).toBeInTheDocument()
    expect(screen.getByRole("radio", { name: /V1 — Clásica/ })).toBeChecked()
    await userEvent.click(screen.getByRole("radio", { name: /V2 — Banco Maestro/ }))
    expect(onChange).toHaveBeenCalledWith("master-v2")
    await userEvent.click(screen.getByRole("radio", { name: /Mixto — V1 \+ V2/ }))
    expect(onChange).toHaveBeenCalledWith("mixed")
  })
})
