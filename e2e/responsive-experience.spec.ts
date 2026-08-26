import { expect, test, type Page } from "@playwright/test"

async function waitForHome(page: Page) {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "Entrena con intención." })
  ).toBeVisible({ timeout: 30_000 })
}

test("escritorio evita la fila de cinco tarjetas", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop-chromium",
    "La geometría del selector maestro-detalle pertenece a escritorio"
  )
  await waitForHome(page)

  const selector = page.getByRole("radiogroup", {
    name: "Versión del banco",
  })
  await expect(selector).toBeVisible()
  await expect(selector.getByRole("radio")).toHaveCount(5)

  const box = await selector.boundingBox()
  expect(
    box,
    "el selector de escritorio debe tener geometría visible"
  ).not.toBeNull()
  expect(box!.width).toBeLessThan(520)
  await expect(
    page.getByRole("region", { name: "Detalle del banco seleccionado" })
  ).toBeVisible()
})

test("móvil navega sin scroll horizontal", async ({ page }, testInfo) => {
  test.skip(
    testInfo.project.name !== "mobile-chromium",
    "La navegación inferior pertenece al viewport móvil"
  )
  await waitForHome(page)

  const sizes = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }))
  expect(sizes.scroll).toBe(sizes.client)

  const navigation = page.getByRole("navigation", {
    name: "Navegación móvil",
  })
  await expect(navigation).toHaveCount(1)
  await expect(navigation).toBeVisible()
})
