import { expect, test, type Page } from "@playwright/test"

type BankSelection = "curated-v4" | "prep-v3" | "mixed"

async function waitForApp(page: Page) {
  await page.goto("/")
  await expect(page.getByText("Preparando tus bancos")).toBeHidden({ timeout: 30_000 })
}

async function selectBank(page: Page, selection: BankSelection) {
  const bankView = page.getByLabel("Vista de banco")
  await expect(bankView).toBeVisible()
  await bankView.selectOption(selection)
  await expect(bankView).toHaveValue(selection)
}

async function openPractice(page: Page, selection: BankSelection = "curated-v4") {
  await waitForApp(page)
  await selectBank(page, selection)
  await page.getByRole("button", { name: "Practicar", exact: true }).click()
  await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Comenzar ronda" })).toBeEnabled()
}

async function selectQuestionCount(page: Page, count: number) {
  const quantity = page.getByRole("combobox", { name: "Cantidad" })
  await quantity.click()
  await page.getByRole("option", { name: `${count} preguntas` }).click()
}

async function startLearnRound(page: Page, count = 10, selection: BankSelection = "curated-v4") {
  await openPractice(page, selection)
  await page.getByRole("button", { name: /Aprender/ }).click()
  if (count !== 10) await selectQuestionCount(page, count)
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(page.getByText(`Pregunta 1 de ${count}`)).toBeVisible()
}

async function answerCurrentQuestion(page: Page) {
  const textAnswer = page.getByPlaceholder("Respuesta canónica")
  if (await textAnswer.count() && await textAnswer.isVisible()) {
    await textAnswer.fill("respuesta de prueba")
  } else {
    const choice = page.locator('button[aria-pressed="false"]').filter({ has: page.locator("span.flex-1") })
    if (await choice.count()) {
      await choice.first().click()
    } else {
      const checkbox = page.getByRole("checkbox").first()
      if (await checkbox.count()) {
        await checkbox.click()
      } else {
        const match = page.getByRole("combobox", { name: /Relacionar/ }).first()
        if (await match.count()) {
          await match.click()
          await page.getByRole("option").nth(1).click()
        }
      }
    }
  }
  await expect(page.getByRole("button", { name: "Confirmar respuesta" })).toBeEnabled()
  await page.getByRole("button", { name: "Confirmar respuesta" }).click()
}

async function answerAndAdvance(page: Page, isLast = false) {
  await answerCurrentQuestion(page)
  if (!isLast) await page.getByRole("button", { name: "Siguiente" }).click()
}

async function expectCuratedMixedProfile(page: Page) {
  const profileBadge = page.locator("[data-bank-profile]")
  await expect(profileBadge).toHaveCount(1)
  await expect(profileBadge).toBeVisible()
  const profile = await profileBadge.getAttribute("data-bank-profile")
  expect(["legacy-v1", "prep-v3", "curated-v4"]).toContain(profile)
  expect(profile).not.toBe("master-v2")
}

test("V4 — Aprender muestra feedback, fuente y pista sin presión", async ({ page }) => {
  await startLearnRound(page)
  await expect(page.getByText("V4", { exact: true })).toBeVisible()

  await answerCurrentQuestion(page)
  await expect(page.getByText(/Respuesta (correcta|incorrecta)/).first()).toBeVisible()
  await expect(page.getByText("Fuente:")).toBeVisible()
  await expect(page.getByText("Pista para recordar")).toBeVisible()
})

test("V4 — Repaso inteligente activa la selección adaptativa", async ({ page }) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Repaso inteligente/ }).click()
  await expect(page.getByText("Adaptativa", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  await expect(page.getByText("Repaso inteligente", { exact: true }).last()).toBeVisible()
})

test("V4 — Simulacro aplica el piloto y oculta la solución inmediata", async ({ page }) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Simulacro/ }).click()
  await expect(page.getByText("12 segundos", { exact: true })).toBeVisible()
  await expect(page.getByText("10 minutos", { exact: true })).toBeVisible()
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  await answerCurrentQuestion(page)
  await expect(page.getByText("Respuesta registrada. La solución se revelará al finalizar la ronda.")).toBeVisible()
  await expect(page.getByText("Respuesta correcta:")).toBeHidden()
})

test("V4 — una recarga conserva la ronda, el banco y la pregunta actual", async ({ page }) => {
  await startLearnRound(page)
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  const question = page.locator('[data-slot="card-title"]').last()
  const prompt = await question.textContent()
  await page.reload()
  await expect(page.getByText("Preparando tus bancos")).toBeHidden({ timeout: 30_000 })
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  await expect(page.getByText("Pregunta 1 de 10")).toBeVisible()
  await expect(page.locator('[data-slot="card-title"]').last()).toHaveText(prompt ?? "")
})

test("Estadísticas V3 muestra las 252 familias y sus variantes pendientes", async ({ page }) => {
  await waitForApp(page)
  await selectBank(page, "prep-v3")
  await page.getByRole("button", { name: "Estadísticas", exact: true }).click()
  await expect(page.getByText("Dominio por familia de conocimiento")).toBeVisible()
  await expect(page.getByRole("button", { name: "Todas (252)" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Pendiente (252)" })).toBeVisible()
})

test("V4 es recomendado en una instalación nueva", async ({ page }) => {
  await waitForApp(page)
  await expect(page.getByRole("radio", { name: /V4 — Banco Curado/ })).toBeChecked()
  await page.getByRole("button", { name: "Banco de preguntas", exact: true }).click()
  await expect(page.getByRole("heading", { name: "Banco de preguntas" })).toBeVisible()
  await expect(page.getByText(/aprobadas/).first()).toBeVisible()
  await expect(page.getByText(/reparadas/).first()).toBeVisible()
  await expect(page.getByText(/rechazadas/).first()).toBeVisible()
})

test("Mixto curado nunca inicia una pregunta V2", async ({ page }) => {
  await startLearnRound(page, 25, "mixed")
  for (let index = 0; index < 25; index += 1) {
    await expectCuratedMixedProfile(page)
    await answerAndAdvance(page, index === 24)
  }
})
