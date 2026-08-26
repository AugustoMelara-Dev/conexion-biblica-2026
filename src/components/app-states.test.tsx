import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest"

import { App } from "@/App"
import { useApp } from "@/app/app-state"
import { ThemeProvider } from "@/components/theme-provider"
import { buildStatistics } from "@/lib/statistics"
import type { Question } from "@/domain/types"

vi.mock("@/app/app-state", () => ({ useApp: vi.fn() }))

type AppContext = ReturnType<typeof useApp>

function createAppContext(
  overrides: Partial<AppContext> = {}
): AppContext {
  const questions: Question[] = []
  const progress = new Map()

  return {
    loading: false,
    error: null,
    masterBankError: null,
    nav: "dashboard",
    setNav: vi.fn(),
    banks: [],
    questions,
    allQuestions: questions,
    progress,
    sessions: [],
    reports: [],
    preferences: {
      theme: "system",
      lastMode: "learn",
      reducedMotion: false,
      lastBankSelection: "curated-v4",
    },
    bankSelection: "curated-v4",
    setBankSelection: vi.fn(),
    bankCounts: { legacy: 0, master: 0, prep: 0, curated: 0 },
    coverageCycles: new Map(),
    activeRound: null,
    statistics: buildStatistics(questions, progress),
    refresh: async () => undefined,
    importBankFiles: async () => [],
    removeBank: async () => undefined,
    recordAnswer: async () => {
      throw new Error("No se usa en los estados de la aplicación")
    },
    recordReport: async () => undefined,
    saveSession: async () => undefined,
    saveCoverageCycle: async () => undefined,
    saveActiveRound: async () => undefined,
    clearActiveRound: async () => undefined,
    exportBanks: async () => [],
    exportProgress: async () => [],
    exportBackup: async () => ({
      backupVersion: "2.0" as const,
      exportedAt: 0,
      banks: [],
      progress: [],
      sessions: [],
      reports: [],
      preferences: {
        theme: "system" as const,
        lastMode: "learn" as const,
        reducedMotion: false,
        lastBankSelection: "curated-v4" as const,
      },
      coverageCycles: [],
      activeRound: null,
    }),
    importBackup: async () => ({ valid: true, errors: [] }),
    setPreferences: vi.fn(),
    repositories: null,
    ...overrides,
  }
}

function renderApp(overrides: Partial<AppContext> = {}) {
  vi.mocked(useApp).mockReturnValue(createAppContext(overrides))
  return render(
    <ThemeProvider disableTransitionOnChange={false}>
      <App />
    </ThemeProvider>
  )
}

afterEach(cleanup)

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: () => ({
      matches: false,
      media: "",
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    }),
  })
})

describe("estados transversales de App", () => {
  it("anuncia la carga ocupada con una estructura anticipada del resumen", () => {
    renderApp({ loading: true })

    expect(
      screen.getByRole("status", { name: "Preparando tus bancos" })
    ).toHaveAttribute("aria-busy", "true")
    expect(
      screen.getByText(
        "Cargando preguntas y progreso desde este dispositivo."
      )
    ).toHaveClass("sr-only")
    expect(screen.getAllByTestId("dashboard-skeleton")).toHaveLength(3)
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1)
  })

  it("mantiene el resumen usable cuando la carga de V2 falla", () => {
    renderApp({ masterBankError: "Sin conexión" })

    expect(
      screen.getByText("Sin conexión. V1 continúa disponible.")
    ).toBeVisible()
    expect(
      screen.getByRole("heading", { name: "Entrena con intención." })
    ).toBeVisible()
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1)
  })
})
