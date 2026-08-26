import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { useApp } from "@/app/app-state"
import { BankManagerPage } from "@/components/bank-manager-page"
import type { Bank, Question } from "@/domain/types"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

const bankFixtures: Bank[] = [
  {
    bankId: "curated-v4-daniel",
    bankProfileId: "curated-v4",
    name: "V4 — Banco Curado Daniel",
    sourceWork: "Daniel",
    sourceVersion: "RVR95",
    schemaVersion: "2.0",
    importedAt: 1,
    fingerprint: "v4-fingerprint",
    sourceFileName: "Curación Daniel.json",
    raw: {
      bank: {
        curationSummary: { approved: 2, repaired: 1, rejected: 0 },
        generatedAt: "2026-08-25T00:00:00.000Z",
        masterFingerprint: "a".repeat(64),
      },
    },
    questions: [],
  },
  {
    bankId: "legacy-daniel-2",
    bankProfileId: "legacy-v1",
    name: "Daniel 2",
    sourceWork: "Profetas y Reyes",
    sourceVersion: "RVR95",
    schemaVersion: "1.0",
    importedAt: 2,
    fingerprint: "legacy-fingerprint",
    sourceFileName: "Daniel 2.json",
    questions: [],
  },
]

const questions: Question[] = ["v4-1", "v4-2", "legacy-1"].map((id) => ({
  id,
  bankId: id.startsWith("v4") ? "curated-v4-daniel" : "legacy-daniel-2",
  bankProfileId: id.startsWith("v4") ? "curated-v4" : "legacy-v1",
  type: "single_choice",
  difficulty: 2,
  source: {
    work: "Daniel",
    version: "RVR95",
    chapter: 2,
    reference: "Daniel 2:1",
  },
  tags: [],
  factKey: id,
  question: `Pregunta ${id}`,
  options: [{ id: "A", text: "Opción" }],
  correctAnswer: ["A"],
}))

function renderBankManager({ banks = bankFixtures }: { banks?: Bank[] } = {}) {
  const removeBank = vi.fn(async () => undefined)
  vi.mocked(useApp).mockReturnValue({
    banks,
    allQuestions: questions,
    importBankFiles: vi.fn(async () => []),
    removeBank,
    exportBanks: vi.fn(async () => []),
    exportProgress: vi.fn(async () => []),
    exportBackup: vi.fn(async () => ({
      backupVersion: "2.0",
      exportedAt: 0,
      banks: [],
      progress: [],
      sessions: [],
      reports: [],
      preferences: {
        theme: "system",
        lastMode: "learn",
        reducedMotion: false,
        lastBankSelection: "legacy-v1",
      },
      coverageCycles: [],
      activeRound: null,
    })),
    importBackup: vi.fn(async () => ({ valid: true, errors: [] })),
    refresh: vi.fn(async () => undefined),
  } as never)

  return { ...render(<BankManagerPage />), removeBank }
}

describe("gestor de bancos", () => {
  it("filtra bancos por nombre normalizado sin ocultar la acción de importar", async () => {
    const user = userEvent.setup()
    renderBankManager()

    await user.type(
      screen.getByRole("searchbox", { name: "Buscar bancos" }),
      "curacion"
    )

    expect(screen.getByText("V4 — Banco Curado Daniel")).toBeVisible()
    expect(screen.queryByText("Daniel 2")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Importar banco" })).toBeVisible()
  })

  it("muestra cada banco como una fila con fuente y cantidad", () => {
    renderBankManager()

    expect(
      screen.getByRole("row", {
        name: /V4 — Banco Curado Daniel.*Daniel.*2 preguntas/,
      })
    ).toBeVisible()
  })

  it("filtra por fuente y muestra un estado vacío al no encontrar bancos", async () => {
    const user = userEvent.setup()
    renderBankManager()

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Fuente" }),
      "Profetas y Reyes"
    )
    expect(screen.getByText("Daniel 2")).toBeVisible()
    expect(
      screen.queryByText("V4 — Banco Curado Daniel")
    ).not.toBeInTheDocument()

    await user.type(
      screen.getByRole("searchbox", { name: "Buscar bancos" }),
      "sin coincidencias"
    )
    expect(
      screen.getByRole("heading", { name: "No hay bancos que coincidan" })
    ).toBeVisible()
    expect(screen.getByRole("button", { name: "Importar banco" })).toBeVisible()
  })

  it("mantiene V4 como fuente solo lectura con su resumen expandible", async () => {
    const user = userEvent.setup()
    renderBankManager()

    const row = screen.getByRole("row", { name: /V4 — Banco Curado Daniel/ })
    expect(
      within(row).queryByRole("button", { name: "Eliminar" })
    ).not.toBeInTheDocument()
    const summary = within(row).getByText(
      "Ver resumen de curación de V4 — Banco Curado Daniel"
    )
    const details = summary.closest("details")
    expect(details).not.toHaveAttribute("open")

    await user.click(summary)
    expect(details).toHaveAttribute("open")
    expect(
      within(row).getByLabelText("Resumen de curación V4")
    ).toHaveTextContent("2 aprobadas")
  })

  it("conserva la confirmación y el ID al eliminar un banco editable", async () => {
    const user = userEvent.setup()
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true)
    const { removeBank } = renderBankManager()

    const row = screen.getByRole("row", { name: /^Daniel 2/ })
    await user.click(within(row).getByRole("button", { name: "Eliminar" }))

    expect(confirm).toHaveBeenCalledWith(
      "¿Eliminar Daniel 2? El progreso se conserva separado."
    )
    expect(removeBank).toHaveBeenCalledWith("legacy-daniel-2")
    confirm.mockRestore()
  })
})
