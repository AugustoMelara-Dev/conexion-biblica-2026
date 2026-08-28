import { expect, test, type Page } from "@playwright/test"

type CanonicalAnswer = {
  answer: string
  blindPool: "A" | "B" | "emergency" | null
}

async function waitForHome(page: Page) {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "PLAN FINAL — GANAR EL 29" }),
  ).toBeVisible({ timeout: 30_000 })
}

async function startNationalFinal(page: Page) {
  const navigation = page.getByRole("navigation", {
    name: "Navegación principal",
  })
  await navigation
    .getByRole("button", { name: "Practicar", exact: true })
    .click()
  const reveal = page.getByRole("button", { name: "Ver plan y modos" })
  if (await reveal.isVisible()) await reveal.click()
  const hub = page.getByRole("region", { name: "Modos avanzados" })
  await hub
    .getByRole("combobox", { name: "Modo avanzado" })
    .selectOption("national-final")
  await hub.getByRole("button", { name: "Iniciar modo avanzado" }).click()
  await expect(page.getByText("Pregunta 1 de 100", { exact: true })).toBeVisible({
    timeout: 30_000,
  })
}

async function loadCanonicalAnswers(page: Page) {
  return page.evaluate(async () => {
    const manifest = (await fetch("/banks/final-2026/manifest.json").then(
      (response) => response.json(),
    )) as { shards: Array<{ questions_file: string }> }
    const entries: Array<[string, CanonicalAnswer]> = []
    for (const shard of manifest.shards) {
      const rows = (await fetch(`/${shard.questions_file}`).then((response) =>
        response.json(),
      )) as Array<{
        question: string
        correct_answer: string
        blind_pool: CanonicalAnswer["blindPool"]
      }>
      for (const row of rows)
        entries.push([
          row.question,
          { answer: row.correct_answer, blindPool: row.blind_pool },
        ])
    }
    return entries
  })
}

function normalizePrompt(prompt: string) {
  const canonical = prompt.replace(
    /^(Atendiendo al contexto exacto, |Sin trasladar datos de otra escena, |Para distinguir este pasaje de los cercanos, )/,
    "",
  )
  return canonical.charAt(0).toUpperCase() + canonical.slice(1)
}

test("tres finales nacionales completas conservan mezcla, variación e historial", async ({
  page,
}, testInfo) => {
  test.skip(
    !process.env.PLAYWRIGHT_BASE_URL || testInfo.project.name !== "desktop-chromium",
    "Auditoría prolongada reservada para producción explícita",
  )
  test.setTimeout(1_200_000)
  const pageErrors: string[] = []
  page.on("pageerror", (error) => pageErrors.push(error.message))
  await waitForHome(page)
  const answerMap = new Map(await loadCanonicalAnswers(page))
  const correctPositions = new Set<number>()
  const prompts = new Set<string>()

  await startNationalFinal(page)
  for (let round = 0; round < 3; round += 1) {
    const mix = { fill: 0, trueFalse: 0, choice: 0 }
    for (let questionNumber = 1; questionNumber <= 100; questionNumber += 1) {
      await expect(
        page.getByText(`Pregunta ${questionNumber} de 100`, { exact: true }),
      ).toBeVisible({ timeout: 20_000 })
      const prompt =
        (await page.getByRole("heading", { level: 1 }).textContent()) ?? ""
      prompts.add(prompt)
      const canonical = answerMap.get(normalizePrompt(prompt))
      expect(canonical, `No se halló respuesta para: ${prompt}`).toBeTruthy()
      expect(canonical?.blindPool).toBeNull()

      const family =
        (await page
          .locator("section[aria-labelledby='question-title']")
          .locator(".text-muted-foreground")
          .first()
          .textContent()) ?? ""
      if (family.includes("Completar con opciones")) mix.fill += 1
      else if (family.includes("Verdadero o falso")) mix.trueFalse += 1
      else if (family.includes("Selección única")) mix.choice += 1
      else throw new Error(`Familia inesperada: ${family}`)

      const radios = page.getByRole("radio")
      let selected = false
      for (let index = 0; index < (await radios.count()); index += 1) {
        const optionText =
          (await radios.nth(index).locator("span").nth(1).textContent()) ?? ""
        if (optionText.trim() !== canonical?.answer.trim()) continue
        correctPositions.add(index)
        await radios.nth(index).click()
        selected = true
        break
      }
      expect(selected, `No se halló opción correcta para: ${prompt}`).toBe(true)
      await page.getByRole("button", { name: "Confirmar respuesta" }).click()
      const advance = page.getByRole("button", {
        name: questionNumber === 100 ? "Ver resultados" : "Siguiente",
      })
      await expect(advance).toBeVisible({ timeout: 20_000 })
      await advance.click()
    }

    expect(mix).toEqual({ fill: 30, trueFalse: 25, choice: 45 })
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "Ronda completada.",
      { timeout: 30_000 },
    )
    await expect(page.getByText("100 / 100", { exact: true })).toBeVisible()
    if (round < 2) {
      await page.getByRole("button", { name: "Otra tanda aleatoria" }).click()
      await expect(
        page.getByText("Pregunta 1 de 100", { exact: true }),
      ).toBeVisible({ timeout: 30_000 })
    }
  }

  expect(correctPositions).toEqual(new Set([0, 1, 2, 3]))
  expect(prompts.size).toBeGreaterThanOrEqual(250)
  const persistedSessions = await page.evaluate(
    () =>
      new Promise<number>((resolve, reject) => {
        const request = indexedDB.open("conexion-biblica-2026")
        request.onerror = () => reject(request.error)
        request.onsuccess = () => {
          const db = request.result
          const count = db
            .transaction("sessions", "readonly")
            .objectStore("sessions")
            .count()
          count.onerror = () => reject(count.error)
          count.onsuccess = () => resolve(count.result)
        }
      }),
  )
  expect(persistedSessions).toBe(3)
  expect(pageErrors).toEqual([])
})
