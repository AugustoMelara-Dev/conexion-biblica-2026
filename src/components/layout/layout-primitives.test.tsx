import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { MetricStrip } from "@/components/layout/metric-strip"
import { PageHeader } from "@/components/layout/page-header"

describe("primitivas de layout", () => {
  it("presenta una sola cabecera principal y conserva la acción", () => {
    render(
      <PageHeader
        eyebrow="Preparación"
        title="Practicar"
        description="Configura una ronda"
        action={<button>Comenzar</button>}
      />
    )

    expect(
      screen.getByRole("heading", { level: 1, name: "Practicar" })
    ).toBeVisible()
    expect(screen.getByRole("button", { name: "Comenzar" })).toBeVisible()
    expect(
      screen.getByRole("button", { name: "Comenzar" }).parentElement
    ).toHaveClass("w-full", "[&>*]:w-full", "lg:w-auto", "lg:[&>*]:w-auto")
  })

  it("expone las métricas como una lista accesible", () => {
    render(
      <MetricStrip
        items={[
          { label: "Precisión", value: "82%" },
          { label: "Tiempo", value: "8.4 s" },
        ]}
      />
    )

    expect(screen.getByRole("list")).toBeVisible()
    expect(screen.getAllByRole("listitem")).toHaveLength(2)
  })

  it("limita la cuadrícula de métricas a tres columnas en escritorio", () => {
    render(<MetricStrip items={[{ label: "Precisión", value: "82%" }]} />)

    expect(screen.getByRole("list")).toHaveClass("lg:grid-cols-3")
  })
})
