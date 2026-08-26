import { expect, test } from "@playwright/test"
import { mkdir } from "node:fs/promises"
import { join } from "node:path"

const output = join(process.cwd(), "output", "consolidacion_final", "screenshots")

test("capturas finales V5: plan, feedback, progreso y simulación ciega", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Las capturas canónicas se generan en escritorio")
  await mkdir(output, { recursive: true })
  await page.goto("/")
  await expect(page.getByRole("heading", { level: 1, name: "PLAN FINAL — GANAR EL 29" })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: join(output, "04-plan-final-produccion.png"), fullPage: true })

  await page.getByRole("button", { name: "Configurar manualmente" }).click()
  await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()
  const guidedReview = page.getByRole("region", { name: "Modos avanzados" })
  await guidedReview.getByRole("combobox", { name: "Modo avanzado" }).selectOption("spaced-review")
  await guidedReview.getByRole("button", { name: "Iniciar modo avanzado" }).click()
  await expect(page.getByText("Pregunta 1 de 50", { exact: true })).toBeVisible({ timeout: 30_000 })

  const textAnswer = page.getByPlaceholder("Respuesta canónica")
  if ((await textAnswer.count()) && (await textAnswer.isVisible())) {
    await textAnswer.fill("respuesta deliberadamente incorrecta")
  } else {
    await page.getByRole("radio").last().click()
  }
  await page.getByRole("button", { name: "Confirmar respuesta" }).click()
  await expect(page.getByText(/Respuesta correcta:/)).toBeVisible()
  await page.screenshot({ path: join(output, "05-feedback-aprendizaje.png"), fullPage: true })

  await page.getByRole("button", { name: "Salir" }).click()
  await page.getByRole("navigation", { name: "Navegación principal" })
    .getByRole("button", { name: "Estadísticas", exact: true }).click()
  await expect(page.getByRole("heading", { level: 1, name: "Progreso" })).toBeVisible()
  await page.screenshot({ path: join(output, "06-progreso-por-hechos.png"), fullPage: true })

  await page.getByRole("navigation", { name: "Navegación principal" })
    .getByRole("button", { name: "Practicar", exact: true }).click()
  const advanced = page.getByRole("region", { name: "Modos avanzados" })
  await advanced.getByRole("combobox", { name: "Modo avanzado" }).selectOption("blind-simulation")
  await advanced.getByRole("button", { name: "Iniciar modo avanzado" }).click()
  await expect(page.getByText("Pregunta 1 de 100", { exact: true })).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText("V5 GOLD", { exact: true })).toBeVisible()
  await page.screenshot({ path: join(output, "07-simulacion-ciega-a.png"), fullPage: true })
})
