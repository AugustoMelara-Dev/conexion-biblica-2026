import { expect, test, type Page } from "@playwright/test"

async function waitForHome(page: Page) {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "RUTA DEL DÍA" })
  ).toBeVisible({ timeout: 30_000 })
}

async function expectNoHorizontalOverflow(page: Page) {
  const sizes = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }))
  expect(sizes.scroll).toBe(sizes.client)
}

test("escritorio presenta jerarquía clara y navegación canónica", async ({
  page,
}, testInfo) => {
  test.skip(
    !testInfo.project.name.startsWith("desktop-"),
    "Geometría de escritorio"
  )
  await page.setViewportSize({ width: 1024, height: 900 })
  await waitForHome(page)

  const navigation = page.getByRole("navigation", {
    name: "Navegación principal",
  })
  await expect(navigation).toBeVisible()
  await expect(
    navigation.getByRole("button", { name: "Banco de preguntas" })
  ).toHaveCount(0)
  await expect(page.getByText("Banco Maestro Único — Final 2026")).toBeVisible()
  await expect(
    page.getByRole("button", { name: "CONTINUAR MI RUTA" })
  ).toBeVisible()
  await expectNoHorizontalOverflow(page)
})

test("móvil a 390 px navega sin solapamiento ni desbordamiento", async ({
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("mobile-"), "Viewport móvil")
  await waitForHome(page)
  await expectNoHorizontalOverflow(page)

  const navigation = page.getByRole("navigation", { name: "Navegación móvil" })
  await expect(navigation).toBeVisible()
  const practice = navigation.getByRole("button", {
    name: "Practicar",
    exact: true,
  })
  await expect(practice).toBeVisible()
  await practice.click()
  await expect(
    page.getByRole("heading", { name: "Configura tu próxima ronda" })
  ).toBeVisible()
  await expectNoHorizontalOverflow(page)
})

test("teclado abre práctica desde ambas navegaciones", async ({ page }) => {
  await waitForHome(page)
  const navigation = page.getByRole("navigation", {
    name:
      (page.viewportSize()?.width ?? 0) >= 1024
        ? "Navegación principal"
        : "Navegación móvil",
  })
  const practice = navigation.getByRole("button", {
    name: "Practicar",
    exact: true,
  })
  await practice.focus()
  await expect(practice).toBeFocused()
  await page.keyboard.press("Enter")
  await expect(
    page.getByRole("heading", { name: "Configura tu próxima ronda" })
  ).toBeVisible()
})
