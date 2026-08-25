import { expect, test, type Page } from "@playwright/test"

async function openPractice(page: Page) {
  await page.goto("/")
  await expect(page.getByText("Preparando tus bancos")).toBeHidden({ timeout: 30_000 })
  await page.getByRole("button", { name: "Practicar", exact: true }).click()
  await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()
  await expect(page.getByText("500", { exact: true }).last()).toBeVisible()
}

async function answerCurrentQuestion(page: Page) {
  const textAnswer = page.getByPlaceholder("Respuesta canónica")
  if (await textAnswer.isVisible()) await textAnswer.fill("respuesta de prueba")
  else await page.locator('button[aria-pressed="false"]').filter({ has: page.locator("span.flex-1") }).first().click()
  await page.getByRole("button", { name: "Confirmar respuesta" }).click()
}

test("Aprender muestra feedback, fuente y pista sin presión", async ({ page }) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Aprender/ }).click()
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await answerCurrentQuestion(page)
  await expect(page.getByText(/Respuesta (correcta|incorrecta)/).first()).toBeVisible()
  await expect(page.getByText("Fuente:")).toBeVisible()
  await expect(page.getByText("Pista para recordar")).toBeVisible()
})

test("Repaso inteligente activa la selección adaptativa", async ({ page }) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Repaso inteligente/ }).click()
  await expect(page.getByText("Adaptativa", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(page.getByText("Repaso inteligente", { exact: true }).last()).toBeVisible()
})

test("Simulacro aplica el piloto y oculta la solución inmediata", async ({ page }) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Simulacro/ }).click()
  await expect(page.getByText("12 segundos", { exact: true })).toBeVisible()
  await expect(page.getByText("10 minutos", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await answerCurrentQuestion(page)
  await expect(page.getByText("Respuesta registrada. La solución se revelará al finalizar la ronda.")).toBeVisible()
  await expect(page.getByText("Respuesta correcta:")).toBeHidden()
})

test("una recarga conserva la ronda y la pregunta actual", async ({ page }) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Aprender/ }).click()
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(page.getByText("Pregunta 1 de 10")).toBeVisible()
  const question = page.locator('[data-slot="card-title"]').last()
  const prompt = await question.textContent()
  await page.reload()
  await expect(page.getByText("Preparando tus bancos")).toBeHidden({ timeout: 30_000 })
  await expect(page.getByText("Pregunta 1 de 10")).toBeVisible()
  await expect(page.locator('[data-slot="card-title"]').last()).toHaveText(prompt ?? "")
})

test("Estadísticas muestra las 252 familias y sus variantes pendientes", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByText("Preparando tus bancos")).toBeHidden({ timeout: 30_000 })
  await page.getByRole("button", { name: "Estadísticas", exact: true }).click()
  await expect(page.getByText("Dominio por familia de conocimiento")).toBeVisible()
  await expect(page.getByRole("button", { name: "Todas (252)" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Pendiente (252)" })).toBeVisible()
})
