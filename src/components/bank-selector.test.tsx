import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { useApp } from "@/app/app-state"
import { BankSelector } from "@/components/bank-selector"
import { DashboardPage } from "@/components/dashboard-page"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

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

describe("inicio", () => {
  it("conserva el resumen de puntos débiles con acceso a práctica enfocada", async () => {
    const setNav = vi.fn()
    vi.mocked(useApp).mockReturnValue({
      statistics: {
        general: {
          total: 12,
          seen: 12,
          correct: 8,
          incorrect: 4,
          unanswered: 0,
          accuracy: 67,
          averageResponseTimeMs: 4000,
          medianResponseTimeMs: 4000,
          bestResponseTimeMs: 2500,
          slowestResponseTimeMs: 6000,
          unseen: 3,
          mastered: 2,
          difficult: 4,
          favorite: 0,
        },
        sources: [
          { key: "Daniel", label: "Daniel", total: 6, seen: 6, correct: 4, incorrect: 2, unanswered: 0, accuracy: 67, averageResponseTimeMs: 4000, mastery: 2 },
          { key: "Profetas y Reyes", label: "Profetas y Reyes", total: 6, seen: 6, correct: 4, incorrect: 2, unanswered: 0, accuracy: 67, averageResponseTimeMs: 4000, mastery: 2 },
        ],
        chapters: [],
        difficulties: [],
        types: [],
        weakChapters: [{ key: "Daniel:2", label: "Daniel 2", total: 4, seen: 4, correct: 2, incorrect: 2, unanswered: 0, accuracy: 50, averageResponseTimeMs: 4500, mastery: 1, chapter: 2, source: "Daniel" }],
        weakTypes: [{ key: "single_choice", label: "Selección única", total: 4, seen: 4, correct: 2, incorrect: 2, unanswered: 0, accuracy: 50, averageResponseTimeMs: 4500, mastery: 1, type: "single_choice" }],
        mostFailed: [{ id: "q-1" }, { id: "q-2" }],
        slowest: [],
      },
      banks: [],
      questions: [{ id: "q-1" }, { id: "q-2" }, { id: "q-3" }],
      sessions: [],
      progress: new Map(),
      setNav,
      bankSelection: "curated-v4",
      setBankSelection: vi.fn(),
      bankCounts: { legacy: 2360, master: 3558, prep: 500, curated: 3220 },
    } as never)

    render(<DashboardPage />)

    expect(screen.getByRole("heading", { name: "Mis puntos débiles" })).toBeVisible()
    expect(screen.getByText("Daniel 2")).toBeVisible()
    expect(screen.getByText("Selección única")).toBeVisible()
    expect(screen.getByText("2 preguntas detectadas")).toBeVisible()
    const weaknessSummary = screen.getByRole("region", { name: "Mis puntos débiles" }).querySelector(":scope > div")
    expect(weaknessSummary).toHaveClass("lg:grid-cols-3")
    expect(weaknessSummary).not.toHaveClass("sm:grid-cols-3")

    await userEvent.click(screen.getByRole("button", { name: "Abrir práctica enfocada" }))
    expect(setNav).toHaveBeenCalledWith("practice")
  })
})
