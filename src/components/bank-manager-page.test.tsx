import { render, screen, waitFor, within } from "@testing-library/react"
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
  {
    bankId: "master-v2",
    bankProfileId: "master-v2",
    name: "V2 — Banco Maestro",
    sourceWork: "Daniel",
    sourceVersion: "CB2026",
    schemaVersion: "2.0",
    importedAt: 3,
    fingerprint: "master-fingerprint",
    sourceFileName: "Banco_Maestro_CB2026.json",
    questions: [],
  },
  {
    bankId: "prep-v3-daniel",
    bankProfileId: "prep-v3",
    name: "V3 — Preparación Daniel",
    sourceWork: "Daniel",
    sourceVersion: "RVR95",
    schemaVersion: "2.0",
    importedAt: 4,
    fingerprint: "prep-fingerprint",
    sourceFileName: "v3_daniel.json",
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
  const importBankFiles = vi.fn(async () => [])
  const importBackup = vi.fn(async () => ({ valid: true, errors: [] }))
  vi.mocked(useApp).mockReturnValue({
    banks,
    allQuestions: questions,
    importBankFiles,
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
    importBackup,
    refresh: vi.fn(async () => undefined),
  } as never)

  return {
    ...render(<BankManagerPage />),
    importBackup,
    importBankFiles,
    removeBank,
  }
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
    expect(summary).toHaveClass("min-h-11")
    const details = summary.closest("details")
    expect(details).not.toHaveAttribute("open")

    await user.click(summary)
    expect(details).toHaveAttribute("open")
    expect(
      within(row).getByLabelText("Resumen de curación V4")
    ).toHaveTextContent("2 aprobadas")
    expect(
      within(row).getByLabelText("Metadatos de generación V4")
    ).toHaveTextContent("Maestro SHA-256 aaaaaaaaaaaa…")
  })

  it("expone acciones editables con nombres únicos y conserva el ID de reemplazo", async () => {
    const user = userEvent.setup()
    const { importBankFiles } = renderBankManager()
    const replacement = new File(["{}"], "reemplazo.json", {
      type: "application/json",
    })

    expect(
      screen.getByRole("searchbox", { name: "Buscar bancos" })
    ).toHaveClass("min-h-11")
    expect(screen.getByRole("combobox", { name: "Fuente" })).toHaveClass(
      "min-h-11"
    )
    const replace = screen.getByRole("button", { name: "Reemplazar Daniel 2" })
    expect(replace).toHaveClass("min-h-11")
    expect(
      screen.getByRole("button", { name: "Eliminar Daniel 2" })
    ).toHaveClass("min-h-11")

    await user.click(replace)
    const bankInput = document.querySelector<HTMLInputElement>(
      'input[type="file"][multiple]'
    )
    if (!bankInput) throw new Error("No se encontró el selector de bancos")
    await user.upload(bankInput, replacement)

    expect(importBankFiles).toHaveBeenCalledWith(
      [replacement],
      "legacy-daniel-2"
    )
  })

  it("conserva la confirmación y el ID al eliminar un banco editable", async () => {
    const user = userEvent.setup()
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true)
    const { removeBank } = renderBankManager()

    await user.click(screen.getByRole("button", { name: "Eliminar Daniel 2" }))

    expect(confirm).toHaveBeenCalledWith(
      "¿Eliminar Daniel 2? El progreso se conserva separado."
    )
    expect(removeBank).toHaveBeenCalledWith("legacy-daniel-2")
    confirm.mockRestore()
  })

  it("mantiene V2 y V3 sin acciones destructivas", () => {
    renderBankManager()

    for (const name of ["V2 — Banco Maestro", "V3 — Preparación Daniel"]) {
      const row = screen.getByRole("row", { name: new RegExp(`^${name}`) })
      expect(within(row).getByText("Integrado · solo lectura")).toBeVisible()
      expect(
        screen.queryByRole("button", { name: `Reemplazar ${name}` })
      ).not.toBeInTheDocument()
      expect(
        screen.queryByRole("button", { name: `Eliminar ${name}` })
      ).not.toBeInTheDocument()
    }
  })

  it("restaura un respaldo mediante el callback y muestra el resultado", async () => {
    const user = userEvent.setup()
    const { importBackup } = renderBankManager()
    const backup = new File(["{}"], "respaldo.json", {
      type: "application/json",
    })

    const [bankInput, backupInput] =
      document.querySelectorAll<HTMLInputElement>('input[type="file"]')
    if (!bankInput || !backupInput)
      throw new Error("No se encontraron los selectores de archivos")
    await user.upload(backupInput, backup)

    await waitFor(() => expect(importBackup).toHaveBeenCalledWith(backup))
    expect(screen.getByText("Restauración completada")).toBeVisible()
  })
})
