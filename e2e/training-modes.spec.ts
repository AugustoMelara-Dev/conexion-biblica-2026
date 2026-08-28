import { expect, test, type Page } from "@playwright/test"

async function waitForHome(page: Page) {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "PLAN FINAL — GANAR EL 29" }),
  ).toBeVisible({ timeout: 30_000 })
}

async function openPractice(page: Page) {
  const heading = page.getByRole("heading", {
    level: 1,
    name: "Configura tu próxima ronda",
  })
  if (await heading.isVisible()) return
  const desktop = page.getByRole("navigation", { name: "Navegación principal" })
  const mobile = page.getByRole("navigation", { name: "Navegación móvil" })
  if ((page.viewportSize()?.width ?? 0) >= 1024)
    await desktop.getByRole("button", { name: "Practicar", exact: true }).click()
  else
    await mobile.getByRole("button", { name: "Practicar", exact: true }).click()
  await expect(heading).toBeVisible()
}

async function startAdvanced(page: Page, id: string, count: number) {
  await openPractice(page)
  const reveal = page.getByRole("button", { name: "Ver plan y modos" })
  if (await reveal.isVisible()) await reveal.click()
  const hub = page.getByRole("region", { name: "Modos avanzados" })
  await hub.getByRole("combobox", { name: "Modo avanzado" }).selectOption(id)
  await hub.getByRole("button", { name: "Iniciar modo avanzado" }).click()
  await expect(page.getByText(`Pregunta 1 de ${count}`, { exact: true })).toBeVisible({
    timeout: 30_000,
  })
}

async function answerAndAdvance(page: Page) {
  await chooseKnownAnswer(page, true)
  await page.getByRole("button", { name: "Confirmar respuesta" }).click()
  const next = page.getByRole("button", { name: "Siguiente" })
  if (await next.isVisible()) await next.click()
}

async function chooseKnownAnswer(page: Page, correctAnswer: boolean) {
  const prompt = (await page.getByRole("heading", { level: 1 }).textContent()) ?? ""
  const canonical = prompt.replace(
    /^(Atendiendo al contexto exacto, |Sin trasladar datos de otra escena, |Para distinguir este pasaje de los cercanos, )/,
    "",
  )
  const normalized = canonical.charAt(0).toUpperCase() + canonical.slice(1)
  const correct = await page.evaluate(async (questionText) => {
    const manifest = await fetch("/banks/final-2026/manifest.json").then((response) => response.json())
    for (const shard of manifest.shards as Array<{ questions_file: string }>) {
      const rows = await fetch(`/${shard.questions_file}`).then((response) => response.json())
      const match = (rows as Array<{ question: string; correct_answer: string }>).find(
        (row) => row.question === questionText,
      )
      if (match) return match.correct_answer
    }
    return null
  }, normalized)
  expect(correct).toBeTruthy()
  const radios = page.getByRole("radio")
  for (let index = 0; index < (await radios.count()); index += 1) {
    const isCorrect = ((await radios.nth(index).textContent()) ?? "").includes(
      correct ?? "",
    )
    if (isCorrect === correctAnswer) {
      await radios.nth(index).click()
      return
    }
  }
  throw new Error("No se encontró la opción solicitada")
}

test("una instalación nueva expone un solo banco y una sola misión primaria", async ({ page }) => {
  await waitForHome(page)
  await expect(page.getByText("Banco Maestro Único — Final 2026")).toBeVisible()
  await expect(page.getByRole("button", { name: "CONTINUAR MI MISIÓN" })).toHaveCount(1)
  await expect(page.getByRole("combobox", { name: /banco/i })).toHaveCount(0)
  await expect(page.getByText(/\bV[1-6]\b/)).toHaveCount(0)
})

test("la carga canónica y una pregunta no producen errores de consola", async ({ page }) => {
  const errors: string[] = []
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text())
  })
  page.on("pageerror", (error) => errors.push(error.message))
  await waitForHome(page)
  await startAdvanced(page, "contextual-traps", 100)
  await expect(page.getByRole("radio")).toHaveCount(4)
  expect(errors).toEqual([])
})

test("las cuatro familias canónicas usan solamente botones de selección", async ({ page }) => {
  const families = [
    ["expert-multiple-choice", "Selección única", 4],
    ["fill-text", "Completar con opciones", 4],
    ["expert-true-false", "Verdadero o falso", 2],
    ["contextual-traps", "Selección única", 4],
  ] as const

  await waitForHome(page)
  for (const [mode, label, optionCount] of families) {
    await startAdvanced(page, mode, 100)
    await expect(page.getByText(`· ${label}`, { exact: true })).toBeVisible()
    await expect(page.getByRole("radio")).toHaveCount(optionCount)
    await expect(page.locator("textarea")).toHaveCount(0)
    await expect(page.locator('input[type="text"]')).toHaveCount(0)
    await page.getByRole("button", { name: "Salir" }).click()
  }
})

test("una recarga conserva pregunta, opciones y posición", async ({ page }) => {
  await waitForHome(page)
  await startAdvanced(page, "fill-text", 100)
  const prompt = await page.getByRole("heading", { level: 1 }).textContent()
  const options = await page.getByRole("radio").allTextContents()
  await page.getByRole("radio").nth(2).click()

  await page.reload()

  await expect(page.getByText("Pregunta 1 de 100", { exact: true })).toBeVisible({
    timeout: 30_000,
  })
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(prompt ?? "")
  await expect(page.getByRole("radio")).toHaveText(options)
})

test("el aprendizaje muestra fuente y repara un fallo después de separación", async ({ page }) => {
  await waitForHome(page)
  await startAdvanced(page, "fill-text", 100)
  const firstPrompt = await page.getByRole("heading", { level: 1 }).textContent()
  const firstReference = await page
    .locator("section[aria-labelledby='question-title']")
    .locator(".text-muted-foreground")
    .first()
    .textContent()

  await chooseKnownAnswer(page, false)
  await page.getByRole("button", { name: "Confirmar respuesta" }).click()
  await expect(page.getByText("Respuesta correcta:")).toBeVisible()
  await expect(page.getByText("Referencia")).toBeVisible()
  await page.getByRole("button", { name: "Siguiente" }).click()

  for (let answered = 0; answered < 8; answered += 1) await answerAndAdvance(page)

  await expect(page.getByText("Pregunta 10 de 101", { exact: true })).toBeVisible()
  await expect(page.getByRole("heading", { level: 1 })).not.toHaveText(firstPrompt ?? "")
  await expect(page.getByText("Completar con opciones", { exact: true })).toHaveCount(0)
  expect(firstReference).toBeTruthy()
})

test("resumen, estadísticas e historial conservan la identidad canónica", async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("desktop-"), "La navegación móvil se valida por separado")
  await waitForHome(page)
  const desktop = page.getByRole("navigation", { name: "Navegación principal" })
  for (const [destination, heading] of [
    ["Estadísticas", "Progreso"],
    ["Historial", "Historial"],
    ["Resumen", "PLAN FINAL — GANAR EL 29"],
  ] as const) {
    await desktop.getByRole("button", { name: destination, exact: true }).click()
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible()
    await expect(page.getByText(/\bV[1-6]\b/)).toHaveCount(0)
  }
})
