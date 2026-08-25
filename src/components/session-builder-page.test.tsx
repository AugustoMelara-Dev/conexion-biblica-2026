import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import { describe, expect, it, vi } from "vitest"
import {
  SequentialBlockPicker,
  StudyDayQuickStart,
} from "@/components/session-builder-page"

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
