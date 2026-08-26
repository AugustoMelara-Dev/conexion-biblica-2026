import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest"
import type { ReactNode } from "react"

import { AppShell } from "@/components/app-shell"
import { FocusShell } from "@/components/layout/focus-shell"
import { ThemeProvider } from "@/components/theme-provider"

const setNav = vi.fn()

vi.mock("@/app/app-state", () => ({
  useApp: () => ({
    nav: "dashboard",
    setNav,
    statistics: { general: { difficult: 0 } },
    bankSelection: "prep-v3",
    setBankSelection: vi.fn(),
  }),
}))

function renderWithApp(ui: ReactNode) {
  return render(<ThemeProvider>{ui}</ThemeProvider>)
}

describe("AppShell", () => {
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

  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it("ofrece un enlace para saltar al contenido", () => {
    renderWithApp(
      <AppShell>
        <p>Contenido</p>
      </AppShell>
    )

    expect(
      screen.getByRole("link", { name: "Saltar al contenido" })
    ).toHaveAttribute("href", "#main-content")
    expect(document.querySelector("#main-content")).not.toBeNull()
  })

  it("colapsa el riel sin perder nombres accesibles", async () => {
    const user = userEvent.setup()
    renderWithApp(
      <AppShell>
        <p>Contenido</p>
      </AppShell>
    )

    await user.click(
      screen.getByRole("button", { name: "Contraer navegación" })
    )

    expect(
      within(screen.getByRole("complementary")).getByRole("button", {
        name: "Practicar",
      })
    ).toBeVisible()
    expect(localStorage.getItem("conexion-biblica-navigation-collapsed")).toBe(
      "true"
    )
  })

  it("ofrece las áreas secundarias desde Más en móvil", async () => {
    const user = userEvent.setup()
    renderWithApp(
      <AppShell>
        <p>Contenido</p>
      </AppShell>
    )

    const mobileNavigation = screen.getByRole("navigation", {
      name: "Navegación móvil",
    })
    await user.click(
      within(mobileNavigation).getByRole("button", { name: "Más" })
    )

    expect(screen.getByRole("menuitem", { name: "Bancos" })).toBeVisible()
    expect(screen.getByRole("menuitem", { name: "Historial" })).toBeVisible()
    expect(screen.getByRole("menuitem", { name: "Revisión" })).toBeVisible()
  })

  it("mantiene la ronda en una superficie sin navegación global", () => {
    render(
      <FocusShell>
        <p>Ronda activa</p>
      </FocusShell>
    )

    expect(screen.getByText("Ronda activa")).toBeVisible()
    expect(
      screen.queryByRole("navigation", { name: "Navegación principal" })
    ).not.toBeInTheDocument()
  })
})
