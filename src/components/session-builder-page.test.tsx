import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import { describe, expect, it, vi } from "vitest"
import { useApp } from "@/app/app-state"
import {
  SequentialBlockPicker,
  SessionBuilderPage,
  StudyDayQuickStart,
} from "@/components/session-builder-page"
import type { Question } from "@/domain/types"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

const question: Question = {
  id: "session-builder-question",
  bankId: "legacy-v1",
  bankProfileId: "legacy-v1",
  type: "single_choice",
  difficulty: 3,
  source: {
    work: "Daniel",
    version: "RVR95",
    chapter: 1,
    reference: "Daniel 1:1",
  },
  tags: [],
  factKey: "DAN-1-1",
  question: "¿Pregunta de prueba?",
  options: [{ id: "A", text: "Respuesta" }],
  correctAnswer: ["A"],
}

function renderSessionBuilder() {
  vi.mocked(useApp).mockReturnValue({
    questions: [question],
    progress: new Map(),
    bankSelection: "legacy-v1",
    coverageCycles: new Map(),
  } as ReturnType<typeof useApp>)

  return render(<SessionBuilderPage onStart={vi.fn()} />)
}

describe("controles de preparación V3", () => {
  it("conserva el bloque 2 como índice interno 1", async () => {
    const onChange = vi.fn()
    function ControlledPicker() {
      const [value, setValue] = useState(0)
      return (
        <SequentialBlockPicker
          blockCount={4}
          value={value}
          onChange={(next) => {
            onChange(next)
            setValue(next)
          }}
        />
      )
    }
    render(<ControlledPicker />)

    const picker = screen.getByRole("combobox", {
      name: "Bloque de preguntas",
    })
    await userEvent.selectOptions(picker, "2")

    expect(picker).toHaveValue("2")
    expect(onChange).toHaveBeenCalledWith(1)
  })

  it("emite el día elegido para iniciar una ruta V3", async () => {
    const onSelect = vi.fn()
    render(<StudyDayQuickStart onSelect={onSelect} />)

    await userEvent.click(screen.getByRole("button", { name: /Día 2/i }))

    expect(onSelect).toHaveBeenCalledWith(2)
  })
})

describe("configuración progresiva de práctica", () => {
  it("oculta filtros secundarios hasta abrir configuración avanzada", async () => {
    const user = userEvent.setup()
    renderSessionBuilder()

    expect(screen.queryByText("Dificultad")).not.toBeInTheDocument()

    await user.click(
      screen.getByRole("button", { name: "Configuración avanzada" })
    )

    expect(screen.getByText("Dificultad")).toBeVisible()
    expect(screen.getByText("Tipos de pregunta")).toBeVisible()
  })

  it("mantiene visibles banco, cantidad y resumen", () => {
    renderSessionBuilder()

    expect(screen.getByText("Banco de preguntas")).toBeVisible()
    expect(screen.getByRole("combobox", { name: "Cantidad" })).toBeVisible()
    expect(screen.getByText(/preguntas disponibles/)).toBeVisible()
    expect(screen.getByRole("button", { name: "Comenzar ronda" })).toBeEnabled()
  })
})
