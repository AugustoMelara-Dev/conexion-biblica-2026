import { expect, test, type Page } from "@playwright/test"

async function waitForHome(page: Page) {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "PLAN FINAL — GANAR EL 29" }),
  ).toBeVisible({ timeout: 30_000 })
}

async function openBackup(page: Page) {
  if ((page.viewportSize()?.width ?? 0) >= 1024) {
    await page
      .getByRole("navigation", { name: "Navegación principal" })
      .getByRole("button", { name: "Respaldo", exact: true })
      .click()
  } else {
    await page.getByRole("button", { name: "Más" }).click()
    await page.getByRole("menuitem", { name: "Respaldo" }).click()
  }
  await expect(
    page.getByRole("heading", { level: 1, name: "Banco de preguntas" }),
  ).toBeVisible()
}

test("el respaldo completo se descarga como JSON versionado", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Una descarga integral basta para validar el contrato")
  await waitForHome(page)
  await openBackup(page)

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: /Exportar todo/ }).click(),
  ])
  expect(download.suggestedFilename()).toBe("conexion-biblica-respaldo.json")
  const stream = await download.createReadStream()
  const chunks: Buffer[] = []
  for await (const chunk of stream) chunks.push(Buffer.from(chunk))
  const payload = JSON.parse(Buffer.concat(chunks).toString("utf8")) as {
    backupVersion: string
    banks: unknown[]
    progress: unknown[]
    sessions: unknown[]
    reports: unknown[]
    coverageCycles: unknown[]
    activeRound: unknown
    preferences: unknown
  }
  expect(payload.backupVersion).toBe("2.0")
  expect(Array.isArray(payload.banks)).toBe(true)
  expect(Array.isArray(payload.progress)).toBe(true)
  expect(Array.isArray(payload.sessions)).toBe(true)
  expect(Array.isArray(payload.reports)).toBe(true)
  expect(Array.isArray(payload.coverageCycles)).toBe(true)
  expect(payload.activeRound).toBeNull()
  expect(payload.preferences).toBeTruthy()
})

test("el shell vuelve a abrir sin red después de quedar bajo control del service worker", async ({
  context,
  page,
}, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop-"), "Una validación por motor es suficiente")
  await waitForHome(page)
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready
  })
  await page.reload()
  await expect(
    page.getByRole("heading", { level: 1, name: "PLAN FINAL — GANAR EL 29" }),
  ).toBeVisible({ timeout: 30_000 })
  expect(await page.evaluate(() => Boolean(navigator.serviceWorker.controller))).toBe(true)

  await context.setOffline(true)
  try {
    await page.evaluate(() => window.location.reload())
    await expect(
      page.getByRole("heading", { level: 1, name: "PLAN FINAL — GANAR EL 29" }),
    ).toBeVisible({ timeout: 30_000 })
  } finally {
    await context.setOffline(false)
  }
})

test("una red lenta al cargar el banco no rompe la pantalla inicial", async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop-"), "Una validación por motor es suficiente")
  await page.route("**/banks/**", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 250))
    await route.continue()
  })
  await waitForHome(page)
  await expect(page.getByText("Banco Maestro Único — Final 2026")).toBeVisible()
})

test("una cuota agotada al guardar una preferencia no derriba la navegación", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "La ruta de almacenamiento es común a los motores")
  await page.addInitScript(() => {
    const original = Storage.prototype.setItem
    Storage.prototype.setItem = function (key: string, value: string) {
      if (key === "conexion-biblica-navigation-collapsed") {
        throw new DOMException("Quota exceeded", "QuotaExceededError")
      }
      return original.call(this, key, value)
    }
  })
  const pageErrors: string[] = []
  page.on("pageerror", (error) => pageErrors.push(error.message))
  await waitForHome(page)
  await page.getByRole("button", { name: "Contraer navegación" }).click()
  await expect(
    page
      .getByRole("navigation", { name: "Navegación principal" })
      .getByRole("button", { name: "Practicar" }),
  ).toBeVisible()
  expect(pageErrors).toEqual([])
})
