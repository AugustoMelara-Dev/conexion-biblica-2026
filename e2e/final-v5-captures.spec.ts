import { expect, test, type Page } from "@playwright/test"
import { mkdir } from "node:fs/promises"
import { join } from "node:path"

const output = join(process.cwd(), "output", "playwright", "final-2026")

async function openPractice(page: Page) {
  const heading = page.getByRole("heading", { name: "Configura tu próxima ronda" })
  if (await heading.isVisible()) return
  const navigation = page.getByRole("navigation", { name: "Navegación principal" })
  await navigation.getByRole("button", { name: "Practicar", exact: true }).click()
  await expect(heading).toBeVisible()
}

async function startMode(page: Page, mode: string, family: string) {
  await openPractice(page)
  const reveal = page.getByRole("button", { name: "Ver plan y modos" })
  if (await reveal.isVisible()) await reveal.click()
  const hub = page.getByRole("region", { name: "Modos avanzados" })
  await hub.getByRole("combobox", { name: "Modo avanzado" }).selectOption(mode)
  await hub.getByRole("button", { name: "Iniciar modo avanzado" }).click()
  await expect(page.getByText(`· ${family}`, { exact: true })).toBeVisible({ timeout: 30_000 })
}

async function chooseWrong(page: Page) {
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
    if (!((await radios.nth(index).textContent()) ?? "").includes(correct ?? "")) {
      await radios.nth(index).click()
      return
    }
  }
}

async function chooseCorrect(page: Page) {
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
      const match = (rows as Array<{ question: string; correct_answer: string }>).find((row) => row.question === questionText)
      if (match) return match.correct_answer
    }
    return null
  }, normalized)
  const radios = page.getByRole("radio")
  for (let index = 0; index < (await radios.count()); index += 1) {
    if (((await radios.nth(index).textContent()) ?? "").includes(correct ?? "")) {
      await radios.nth(index).click()
      return
    }
  }
  throw new Error("No se encontró la respuesta correcta")
}

test("genera las capturas de aceptación del banco canónico", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Capturas canónicas de escritorio")
  await mkdir(output, { recursive: true })
  await page.goto("/")
  await expect(page.getByRole("heading", { name: "PLAN FINAL — GANAR EL 29" })).toBeVisible({ timeout: 30_000 })
  await page.screenshot({ path: join(output, "01-resumen-unico.png"), fullPage: true })

  const modes = [
    ["expert-multiple-choice", "Selección única", "02-seleccion-directa.png"],
    ["fill-text", "Completar con opciones", "03-completar-opciones.png"],
    ["expert-true-false", "Verdadero o falso", "04-verdadero-falso.png"],
    ["contextual-traps", "Selección única", "05-seleccion-contextual.png"],
  ] as const
  for (const [mode, family, filename] of modes) {
    await startMode(page, mode, family)
    await page.screenshot({ path: join(output, filename), fullPage: true })
    await page.getByRole("button", { name: "Salir" }).click()
  }

  await startMode(page, "fill-text", "Completar con opciones")
  await chooseWrong(page)
  await page.getByRole("button", { name: "Confirmar respuesta" }).click()
  await expect(page.getByText("Respuesta correcta:")).toBeVisible()
  await page.screenshot({ path: join(output, "06-feedback-fundamentado.png"), fullPage: true })
  await page.getByRole("button", { name: "Siguiente" }).click()
  for (let answered = 0; answered < 8; answered += 1) {
    await chooseCorrect(page)
    await page.getByRole("button", { name: "Confirmar respuesta" }).click()
    await page.getByRole("button", { name: "Siguiente" }).click()
  }
  await expect(page.getByText("Pregunta 10 de 101", { exact: true })).toBeVisible()
  await page.screenshot({ path: join(output, "07-recuperacion-otra-variante.png"), fullPage: true })
})
