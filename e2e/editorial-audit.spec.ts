import { expect, test } from "@playwright/test"

test("la auditoría humana firma por huella y avanza sobre el artefacto V10", async ({
  page,
}, testInfo) => {
  test.skip(
    !testInfo.project.name.endsWith("chromium"),
    "El contrato editorial se valida en escritorio y móvil Chromium"
  )
  test.setTimeout(120_000)
  const errors: string[] = []
  page.on("pageerror", (error) => errors.push(error.message))
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "RUTA DEL DÍA" })
  ).toBeVisible({ timeout: 30_000 })
  await expect(
    page.getByRole("button", { name: "CONTINUAR MI RUTA" })
  ).toBeVisible()
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
    page.getByRole("heading", { name: "Auditoría humana final" })
  ).toBeVisible()
  await expect(page.getByText("0 de 2852 revisadas")).toBeVisible({
    timeout: 60_000,
  })
  const approveButton = page.getByRole("button", { name: "Aprobar pregunta" })
  await expect(approveButton).toBeVisible({ timeout: 30_000 })
  const reviewCard = approveButton.locator(
    "xpath=ancestor::div[@data-slot='card']"
  )
  const questionText = (
    await reviewCard.locator('[data-slot="card-title"]').textContent()
  )?.trim()
  const descriptor = (
    await reviewCard.locator('[data-slot="card-description"]').textContent()
  )?.trim()
  const reviewedId = descriptor?.split(" · ").at(-1)?.trim()
  expect(questionText).toBeTruthy()
  expect(reviewedId).toBeTruthy()
  await page.getByLabel("Nombre del revisor").fill("Auditor E2E")
  await approveButton.click()

  await expect(page.getByText("1 de 2852 revisadas")).toBeVisible()
  const stored = await page.evaluate(() =>
    JSON.parse(localStorage.getItem("conexion-biblica-human-review-v1") ?? "[]")
  )
  expect(stored).toHaveLength(1)
  expect(stored[0]).toMatchObject({
    id: reviewedId,
    reviewer: "Auditor E2E",
    disposition: "approved",
  })
  expect(stored[0].content_sha256).toMatch(/^[a-f0-9]{64}$/)

  await page.getByRole("button", { name: "Deshacer última decisión" }).click()
  await expect(page.getByText("0 de 2852 revisadas")).toBeVisible()
  await expect(page.getByText(questionText!, { exact: true })).toBeVisible()
  expect(
    await page.evaluate(() =>
      JSON.parse(
        localStorage.getItem("conexion-biblica-human-review-v1") ?? "[]"
      )
    )
  ).toEqual([])
  expect(errors).toEqual([])
})
