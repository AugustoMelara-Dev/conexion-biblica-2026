import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { BankSelector } from "@/components/bank-selector"

describe("selector de versión", () => {
  it("muestra detalle solo para el perfil seleccionado", async () => {
    const onChange = vi.fn()
    render(
      <BankSelector
        value="curated-v4"
        onChange={onChange}
        legacyCount={2360}
        masterCount={3558}
        prepCount={500}
        curatedCount={3220}
      />,
    )

    expect(screen.getByRole("radiogroup", { name: "Versión del banco" })).toBeInTheDocument()
    expect(screen.getAllByRole("radio")).toHaveLength(5)
    expect(screen.getByRole("region", { name: "Detalle del banco seleccionado" })).toHaveTextContent("3,220 preguntas")

    await userEvent.click(screen.getByRole("radio", { name: /V3 — Preparación/ }))
    expect(onChange).toHaveBeenCalledWith("prep-v3")
  })

  it("no repite advertencias técnicas en opciones no seleccionadas", () => {
    render(
      <BankSelector
        value="curated-v4"
        onChange={vi.fn()}
        legacyCount={2360}
        masterCount={3558}
        prepCount={500}
        curatedCount={3220}
      />,
    )

    expect(screen.queryByText("Advertencia técnica: conserva el texto original.")).not.toBeInTheDocument()
  })

  it("ofrece el selector nativo etiquetado y conserva los IDs de callback", async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(
      <BankSelector
        value="curated-v4"
        onChange={onChange}
        legacyCount={2360}
        masterCount={3558}
        prepCount={500}
        curatedCount={3220}
      />,
    )

    await user.selectOptions(screen.getByRole("combobox", { name: "Seleccionar versión del banco" }), "master-v2")
    expect(onChange).toHaveBeenCalledWith("master-v2")
  })
})
