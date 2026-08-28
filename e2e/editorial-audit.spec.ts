import { expect, test } from "@playwright/test"

test("la auditoría humana firma por huella y avanza sobre las doce mil", async ({
  page,
}, testInfo) => {
  test.skip(
    !testInfo.project.name.endsWith("chromium"),
    "El contrato editorial se valida en escritorio y móvil Chromium",
  )
  test.setTimeout(120_000)
  const errors: string[] = []
  page.on("pageerror", (error) => errors.push(error.message))
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "PLAN FINAL — GANAR EL 29" }),
  ).toBeVisible({ timeout: 30_000 })
  const isDesktop = (page.viewportSize()?.width ?? 0) >= 1024
  const navigation = page.getByRole("navigation", {
    name: isDesktop ? "Navegación principal" : "Navegación móvil",
  })
  if (isDesktop) {
    await navigation.getByRole("button", { name: "Revisar preguntas" }).click()
  } else {
    await navigation.getByRole("button", { name: "Más" }).click()
    await page.getByRole("menuitem", { name: "Revisión" }).click()
  }

  await expect(
    page.getByRole("heading", { name: "Auditoría humana final" }),
  ).toBeVisible()
  await expect(page.getByText("0 de 12000 revisadas")).toBeVisible({
    timeout: 60_000,
  })
  await expect(
    page.getByText(
      /Según Daniel 1:1, ¿qué lugar funciona como origen/,
    ),
  ).toBeVisible({ timeout: 30_000 })
  await page.getByLabel("Nombre del revisor").fill("Auditor E2E")
  await page.getByRole("button", { name: "Aprobar pregunta" }).click()

  await expect(page.getByText("1 de 12000 revisadas")).toBeVisible()
  const stored = await page.evaluate(() =>
    JSON.parse(
      localStorage.getItem("conexion-biblica-human-review-v1") ?? "[]",
    ),
  )
  expect(stored).toHaveLength(1)
  expect(stored[0]).toMatchObject({
    id: "DAN1-GOLD-0001-SINGLE_CHOICE_CONTEXTUAL",
    reviewer: "Auditor E2E",
    disposition: "approved",
  })
  expect(stored[0].content_sha256).toMatch(/^[a-f0-9]{64}$/)

  await page.getByRole("button", { name: "Deshacer última decisión" }).click()
  await expect(page.getByText("0 de 12000 revisadas")).toBeVisible()
  await expect(
    page.getByText(
      /Según Daniel 1:1, ¿qué lugar funciona como origen/,
    ),
  ).toBeVisible()
  expect(
    await page.evaluate(() =>
      JSON.parse(
        localStorage.getItem("conexion-biblica-human-review-v1") ?? "[]",
      ),
    ),
  ).toEqual([])
  expect(errors).toEqual([])
})
