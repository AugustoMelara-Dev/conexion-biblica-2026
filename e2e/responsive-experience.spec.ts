import { expect, test, type Page } from "@playwright/test"

async function waitForHome(page: Page) {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "Entrena con intención." })
  ).toBeVisible({ timeout: 30_000 })
}

async function expectNoHorizontalOverflow(page: Page) {
  const sizes = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }))
  expect(sizes.scroll).toBe(sizes.client)
}

test("escritorio a 1024 px muestra cinco radios verticales y detalle legible", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop-chromium",
    "La geometría del selector maestro-detalle pertenece a escritorio"
  )
  await page.setViewportSize({ width: 1024, height: 900 })
  await waitForHome(page)

  const selector = page.getByRole("radiogroup", {
    name: "Versión del banco",
  })
  await expect(selector).toBeVisible()
  const radios = selector.getByRole("radio")
  await expect(radios).toHaveCount(5)
  for (let index = 0; index < 5; index += 1) {
    await expect(radios.nth(index)).toBeVisible()
  }

  const radioBoxes = await radios.evaluateAll((elements) =>
    elements.map((element) => {
      const box = element.getBoundingClientRect()
      return { top: box.top, bottom: box.bottom }
    })
  )
  for (let index = 1; index < radioBoxes.length; index += 1) {
    expect(
      radioBoxes[index].top,
      `la posición Y del radio ${index + 1} debe ser mayor que la anterior`
    ).toBeGreaterThan(radioBoxes[index - 1].top)
    expect(
      radioBoxes[index].top,
      `el radio ${index + 1} debe estar debajo del radio ${index}`
    ).toBeGreaterThanOrEqual(radioBoxes[index - 1].bottom)
  }

  const box = await selector.boundingBox()
  expect(
    box,
    "el selector de escritorio debe tener geometría visible"
  ).not.toBeNull()
  expect(box!.width).toBeLessThan(520)
  const detail = page.getByRole("region", {
    name: "Detalle del banco seleccionado",
  })
  await expect(detail).toBeVisible()
  await expect(
    detail.getByRole("heading", { name: "V4 — Banco Curado" })
  ).toBeVisible()
  await expectNoHorizontalOverflow(page)
})

test("móvil navega sin scroll horizontal", async ({ page }, testInfo) => {
  test.skip(
    testInfo.project.name !== "mobile-chromium",
    "La navegación inferior pertenece al viewport móvil"
  )
  await waitForHome(page)

  await expectNoHorizontalOverflow(page)

  const navigation = page.getByRole("navigation", {
    name: "Navegación móvil",
  })
  await expect(navigation).toHaveCount(1)
  await expect(navigation).toBeVisible()
})

test("escritorio activa Practicar con Enter desde la navegación principal", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop-chromium",
    "La prueba de teclado usa la navegación principal de escritorio"
  )
  await waitForHome(page)

  const navigation = page.getByRole("navigation", {
    name: "Navegación principal",
  })
  const practice = navigation.getByRole("button", {
    name: "Practicar",
    exact: true,
  })
  await practice.focus()
  await expect(practice).toBeFocused()
  await page.keyboard.press("Enter")
  await expect(
    page.getByRole("heading", { level: 1, name: "Configura tu próxima ronda" })
  ).toBeVisible()
})

test("móvil activa Practicar con Enter desde la navegación inferior", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "mobile-chromium",
    "La prueba de teclado usa la navegación inferior móvil"
  )
  await waitForHome(page)

  const navigation = page.getByRole("navigation", {
    name: "Navegación móvil",
  })
  const practice = navigation.getByRole("button", {
    name: "Practicar",
    exact: true,
  })
  await practice.focus()
  await expect(practice).toBeFocused()
  await page.keyboard.press("Enter")
  await expect(
    page.getByRole("heading", { level: 1, name: "Configura tu próxima ronda" })
  ).toBeVisible()
})
