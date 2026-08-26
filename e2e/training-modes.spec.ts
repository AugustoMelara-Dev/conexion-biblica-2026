import { expect, test, type Page } from "@playwright/test"

type BankSelection = "curated-v4" | "prep-v3" | "mixed"

const bankNames: Record<BankSelection, string> = {
  "curated-v4": "V4 — Banco Curado",
  "prep-v3": "V3 — Preparación intensiva de 4 días",
  mixed: "Mixto curado",
}

async function waitForApp(page: Page) {
  await page.goto("/")
  await expect(
    page.getByRole("heading", { level: 1, name: "Entrena con intención." })
  ).toBeVisible({ timeout: 30_000 })
}

type Destination = "practice" | "stats" | "banks" | "review"

async function navigateTo(page: Page, destination: Destination) {
  if ((page.viewportSize()?.width ?? 0) >= 1024) {
    const desktopNames: Record<Destination, string> = {
      practice: "Practicar",
      stats: "Estadísticas",
      banks: "Banco de preguntas",
      review: "Revisar preguntas",
    }
    const navigation = page.getByRole("navigation", {
      name: "Navegación principal",
    })
    await expect(navigation).toBeVisible()
    await navigation
      .getByRole("button", { name: desktopNames[destination], exact: true })
      .click()
    return
  }

  const navigation = page.getByRole("navigation", {
    name: "Navegación móvil",
  })
  await expect(navigation).toBeVisible()
  if (destination === "practice" || destination === "stats") {
    await navigation
      .getByRole("button", {
        name: destination === "practice" ? "Practicar" : "Progreso",
        exact: true,
      })
      .click()
    return
  }

  await navigation.getByRole("button", { name: "Más", exact: true }).click()
  await page
    .getByRole("menuitem", {
      name: destination === "banks" ? "Bancos" : "Revisión",
      exact: true,
    })
    .click()
}

async function selectBank(page: Page, selection: BankSelection) {
  const detail = page.getByRole("region", {
    name: "Detalle del banco seleccionado",
  })

  if ((page.viewportSize()?.width ?? 0) >= 1024) {
    const group = page.getByRole("radiogroup", { name: "Versión del banco" })
    await expect(group).toBeVisible()
    const option = group.getByRole("radio", { name: bankNames[selection] })
    await option.check()
    await expect(option).toBeChecked()
  } else {
    const selector = page.getByRole("combobox", {
      name: "Seleccionar versión del banco",
    })
    await expect(selector).toBeVisible()
    await selector.selectOption(selection)
    await expect(selector).toHaveValue(selection)
  }

  await expect(detail).toContainText(bankNames[selection])
}

async function openPractice(
  page: Page,
  selection: BankSelection = "curated-v4"
) {
  await waitForApp(page)
  await selectBank(page, selection)
  await navigateTo(page, "practice")
  await expect(
    page.getByRole("heading", { name: "Configura tu próxima ronda" })
  ).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Comenzar ronda" })
  ).toBeEnabled()
}

async function selectQuestionCount(page: Page, count: number) {
  const quantity = page.getByRole("combobox", { name: "Cantidad" })
  await quantity.click()
  await page.getByRole("option", { name: `${count} preguntas` }).click()
}

async function openAdvancedSettings(page: Page) {
  const disclosure = page.getByRole("button", {
    name: "Configuración avanzada",
  })
  await expect(disclosure).toHaveAttribute("aria-expanded", "false")
  await disclosure.click()
  await expect(disclosure).toHaveAttribute("aria-expanded", "true")
  await expect(page.getByTestId("advanced-round-settings")).toBeVisible()
}

async function startLearnRound(
  page: Page,
  count = 10,
  selection: BankSelection = "curated-v4"
) {
  await openPractice(page, selection)
  await page.getByRole("button", { name: /Aprender/ }).click()
  if (count !== 10) await selectQuestionCount(page, count)
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(
    page.getByText(`Pregunta 1 de ${count}`, { exact: true })
  ).toBeVisible()
}

async function answerCurrentQuestion(page: Page) {
  const textAnswer = page.getByPlaceholder("Respuesta canónica")
  if ((await textAnswer.count()) && (await textAnswer.isVisible())) {
    await textAnswer.fill("respuesta de prueba")
  } else {
    const choice = page.getByRole("radio", { checked: false })
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
  await expect(
    page.getByRole("button", { name: "Confirmar respuesta" })
  ).toBeEnabled()
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

test("V4 — Aprender muestra feedback, fuente y pista sin presión", async ({
  page,
}) => {
  await startLearnRound(page)
  await expect(page.getByText("V4", { exact: true })).toBeVisible()

  await answerCurrentQuestion(page)
  await expect(
    page.getByText(/Respuesta (correcta|incorrecta)/).first()
  ).toBeVisible()
  await expect(page.getByText("Fuente:")).toBeVisible()
  await expect(page.getByText("Pista para recordar")).toBeVisible()
})

test("V4 — Repaso inteligente activa la selección adaptativa", async ({
  page,
}) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Repaso inteligente/ }).click()
  await openAdvancedSettings(page)
  await expect(
    page.getByRole("combobox", { name: "Estrategia de selección" })
  ).toHaveText("Adaptativa")
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  await expect(
    page.getByText("Repaso inteligente", { exact: true }).last()
  ).toBeVisible()
})

test("V4 — Simulacro aplica el piloto y oculta la solución inmediata", async ({
  page,
}) => {
  await openPractice(page)
  await page.getByRole("button", { name: /Simulacro/ }).click()
  await openAdvancedSettings(page)
  await expect(
    page.getByRole("combobox", { name: "Tiempo por pregunta" })
  ).toHaveText("12 segundos")
  await expect(page.getByRole("combobox", { name: "Tiempo total" })).toHaveText(
    "10 minutos"
  )
  await page.getByRole("button", { name: "Comenzar ronda" }).click()
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  await answerCurrentQuestion(page)
  await expect(
    page.getByText(
      "Respuesta registrada. La solución se revelará al finalizar la ronda."
    )
  ).toBeVisible()
  await expect(page.getByText("Respuesta correcta:")).toHaveCount(0)
})

test("V4 — una recarga conserva la ronda, el banco y la pregunta actual", async ({
  page,
}) => {
  await startLearnRound(page)
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  const question = page.getByRole("heading", { level: 1 })
  const prompt = await question.textContent()
  await page.reload()
  await expect(page.getByText("Preparando tus bancos")).toHaveCount(0, {
    timeout: 30_000,
  })
  await expect(page.getByText("V4", { exact: true })).toBeVisible()
  await expect(
    page.getByText("Pregunta 1 de 10", { exact: true })
  ).toBeVisible()
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(prompt ?? "")
})

test("Estadísticas V3 muestra las 252 familias y sus variantes pendientes", async ({
  page,
}) => {
  await waitForApp(page)
  await selectBank(page, "prep-v3")
  await navigateTo(page, "stats")
  await page.getByRole("tab", { name: "Familias", exact: true }).click()
  await expect(
    page.getByText("Dominio por familia de conocimiento")
  ).toBeVisible()
  await expect(page.getByRole("button", { name: "Todas (252)" })).toBeVisible()
  await expect(
    page.getByRole("button", { name: "Pendiente (252)" })
  ).toBeVisible()
})

test("V4 es recomendado en una instalación nueva", async ({ page }) => {
  await waitForApp(page)
  if ((page.viewportSize()?.width ?? 0) >= 1024) {
    await expect(
      page
        .getByRole("radiogroup", { name: "Versión del banco" })
        .getByRole("radio", {
          name: bankNames["curated-v4"],
        })
    ).toBeChecked()
  } else {
    await expect(
      page.getByRole("combobox", { name: "Seleccionar versión del banco" })
    ).toHaveValue("curated-v4")
  }
  await navigateTo(page, "banks")
  await expect(
    page.getByRole("heading", { name: "Banco de preguntas" })
  ).toBeVisible()
  const disclosures = page.getByText(/Ver resumen de curación de/)
  await expect(disclosures).toHaveCount(2)
  for (let index = 0; index < 2; index += 1) {
    await disclosures.nth(index).click()
  }
  const summaries = page.getByLabel("Resumen de curación V4")
  await expect(summaries).toHaveCount(2)
  for (let index = 0; index < 2; index += 1) {
    const summary = summaries.nth(index)
    await expect(summary).toBeVisible()
    await expect(summary.getByText(/aprobadas/)).toBeVisible()
    await expect(summary.getByText(/reparadas/)).toBeVisible()
    await expect(summary.getByText(/rechazadas/)).toBeVisible()
  }
})

test("Mixto curado nunca inicia una pregunta V2", async ({ page }) => {
  await startLearnRound(page, 25, "mixed")
  for (let index = 0; index < 25; index += 1) {
    await expectCuratedMixedProfile(page)
    await answerAndAdvance(page, index === 24)
  }
})

test("Revisar preguntas conserva la etiqueta V4 de un reporte", async ({
  page,
}) => {
  await startLearnRound(page)
  const question = await page.getByRole("heading", { level: 1 }).textContent()
  await page.getByRole("button", { name: "Reportar" }).click()
  await page
    .getByRole("textbox", { name: "Motivo del reporte" })
    .fill("Verificación E2E")
  await page.getByRole("button", { name: "Guardar reporte" }).click()
  await page.getByRole("button", { name: "Salir" }).click()
  await navigateTo(page, "review")
  await expect(
    page.getByRole("heading", { level: 1, name: "Revisión" })
  ).toBeVisible()
  const reportedQuestion = page
    .getByRole("listitem")
    .filter({ hasText: question ?? "" })
  await expect(reportedQuestion).toHaveCount(1)
  await expect(reportedQuestion).toContainText("V4")
})

test("V5 carga PR43–44 por fragmentos y conserva la variante dinámica al recargar", async ({
  page,
}) => {
  await waitForApp(page)
  await navigateTo(page, "practice")
  const massiveHub = page.getByRole("region", { name: "Entrenamiento masivo" })
  await expect(massiveHub).toBeVisible()

  const mode = massiveHub.getByRole("combobox", { name: "Modo avanzado" })
  await mode.selectOption("pr43-44-intensive")
  await massiveHub.getByRole("button", { name: "Iniciar modo avanzado" }).click()

  await expect(page.getByText("Pregunta 1 de 100", { exact: true })).toBeVisible({
    timeout: 30_000,
  })
  await expect(page.getByText("V5", { exact: true })).toBeVisible()
  const prompt = await page.getByRole("heading", { level: 1 }).textContent()
  const options = await page.getByRole("radio").allTextContents()

  await page.reload()

  await expect(page.getByText("Pregunta 1 de 100", { exact: true })).toBeVisible({
    timeout: 30_000,
  })
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(prompt ?? "")
  await expect(page.getByRole("radio")).toHaveText(options)
})
