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

async function downloadBackup(page: Page) {
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: /Exportar todo/ }).click(),
  ])
  const stream = await download.createReadStream()
  const chunks: Buffer[] = []
  for await (const chunk of stream) chunks.push(Buffer.from(chunk))
  return {
    filename: download.suggestedFilename(),
    payload: JSON.parse(Buffer.concat(chunks).toString("utf8")) as Record<
      string,
      unknown
    >,
  }
}

test("el respaldo completo se descarga como JSON versionado", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Una descarga integral basta para validar el contrato")
  await waitForHome(page)
  await openBackup(page)

  const { filename, payload: rawPayload } = await downloadBackup(page)
  expect(filename).toBe("conexion-biblica-respaldo.json")
  const payload = rawPayload as {
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
  expect(Array.isArray(payload.exposures)).toBe(true)
  expect(Array.isArray(payload.blindUsage)).toBe(true)
  expect(payload.activeRound).toBeNull()
  expect(payload.preferences).toBeTruthy()
})

test("restaura de verdad un respaldo con mil sesiones y lo conserva al recargar", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop-chromium",
    "La persistencia IndexedDB es común a los motores",
  )
  test.setTimeout(360_000)
  const pageErrors: string[] = []
  page.on("pageerror", (error) => pageErrors.push(error.message))
  await waitForHome(page)
  await openBackup(page)
  const { payload } = await downloadBackup(page)
  const now = Date.now()
  payload.sessions = Array.from({ length: 1_000 }, (_, index) => ({
    id: `large-history-${index}`,
    startedAt: now - index * 60_000,
    completedAt: now - index * 60_000 + 5_000,
    mode: "training",
    context: "practice",
    config: {
      mode: "training",
      count: 0,
      sourceWorks: ["Daniel", "Profetas y Reyes"],
      chapters: [],
      difficulties: [],
      types: [],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      bankSelection: "final-v7",
      strategy: "adaptive",
      includeBlind: false,
    },
    questionKeys: [],
    answers: [],
    score: index % 101,
    durationMs: 5_000,
  }))
  const preferences = payload.preferences as Record<string, unknown>
  preferences.reducedMotion = !preferences.reducedMotion
  await page
    .locator('input[type="file"][accept="application/json,.json"]')
    .last()
    .setInputFiles({
      name: "respaldo-grande.json",
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(payload)),
    })
  await expect(
    page.getByText("Restaurando respaldo… No cierres esta pestaña."),
  ).toBeVisible()
  await expect(page.getByText("Respaldo restaurado.", { exact: false })).toBeVisible({
    timeout: 240_000,
  })

  await page
    .getByRole("navigation", { name: "Navegación principal" })
    .getByRole("button", { name: "Historial", exact: true })
    .click()
  await expect(page.getByText("1000 rondas guardadas.")).toBeVisible({
    timeout: 30_000,
  })
  await expect(page.getByRole("list", { name: "Sesiones guardadas" })).toBeVisible()

  await page.reload()
  await page
    .getByRole("navigation", { name: "Navegación principal" })
    .getByRole("button", { name: "Historial", exact: true })
    .click()
  await expect(page.getByText("1000 rondas guardadas.")).toBeVisible({
    timeout: 30_000,
  })
  expect(pageErrors).toEqual([])
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

test("una reinstalación del service worker elimina cachés de versiones anteriores", async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop-chromium",
    "El contrato del service worker es idéntico en los motores",
  )
  await waitForHome(page)
  await page.evaluate(async () => {
    const registration = await navigator.serviceWorker.ready
    await registration.unregister()
    await caches.open("conexion-biblica-shell-v0-obsoleta")
  })
  await page.reload()
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready
  })
  await expect
    .poll(() =>
      page.evaluate(async () =>
        (await caches.keys()).includes("conexion-biblica-shell-v0-obsoleta"),
      ),
    )
    .toBe(false)
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
