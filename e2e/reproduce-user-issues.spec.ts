import { expect, test } from "@playwright/test"

test.describe("Verificación Casos de Consola Competitiva V17", () => {
  test.beforeEach(async ({ page }) => {
    // Clear indexedDB and localStorage before each test
    await page.goto("/")
    await page.evaluate(() => {
      localStorage.clear()
    })
  })

  test("Caso 1: Seleccionar únicamente Profetas y Reyes (25 preguntas)", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Uncheck Daniel, ensure Profetas y Reyes is checked
    const danCheckbox = page.getByRole("checkbox", { name: "Daniel" })
    if (await danCheckbox.isChecked()) {
      await danCheckbox.click()
    }
    const prCheckbox = page.getByRole("checkbox", { name: "Profetas y Reyes" })
    if (!(await prCheckbox.isChecked())) {
      await prCheckbox.click()
    }

    // Select 25 questions
    await page.getByRole("combobox", { name: "Cantidad" }).click()
    await page.getByRole("option", { name: "25 preguntas" }).click()

    // Click manual start button
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    // Wait for quiz screen contract summary
    const contractSummary = page.locator('[data-testid="round-contract-summary"]')
    await expect(contractSummary).toBeVisible({ timeout: 30_000 })
    await expect(contractSummary).toHaveAttribute("data-pr-count", "25")
    await expect(contractSummary).toHaveAttribute("data-dan-count", "0")
  })

  test("Caso 2: Seleccionar únicamente Daniel (25 preguntas)", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Uncheck PR, ensure Daniel is checked
    const prCheckbox = page.getByRole("checkbox", { name: "Profetas y Reyes" })
    if (await prCheckbox.isChecked()) {
      await prCheckbox.click()
    }
    const danCheckbox = page.getByRole("checkbox", { name: "Daniel" })
    if (!(await danCheckbox.isChecked())) {
      await danCheckbox.click()
    }

    // Select 25 questions
    await page.getByRole("combobox", { name: "Cantidad" }).click()
    await page.getByRole("option", { name: "25 preguntas" }).click()

    // Click manual start button
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    // Wait for quiz screen contract summary
    const contractSummary = page.locator('[data-testid="round-contract-summary"]')
    await expect(contractSummary).toBeVisible({ timeout: 30_000 })
    await expect(contractSummary).toHaveAttribute("data-pr-count", "0")
    await expect(contractSummary).toHaveAttribute("data-dan-count", "25")
  })

  test("Caso 3: Seleccionar únicamente PR 43", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Uncheck Daniel
    const danCheckbox = page.getByRole("checkbox", { name: "Daniel" })
    if (await danCheckbox.isChecked()) {
      await danCheckbox.click()
    }

    // Reveal advanced settings
    await page.getByRole("button", { name: "Configuración avanzada" }).click()

    // Click PR 43
    await page.getByRole("button", { name: /^PR 43/ }).click()

    // Start round
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    const contractSummary = page.locator('[data-testid="round-contract-summary"]')
    await expect(contractSummary).toBeVisible({ timeout: 30_000 })
    await expect(contractSummary).toContainText("PR")
    await expect(contractSummary).toContainText("Cap. 43")
    await expect(contractSummary).toHaveAttribute("data-dan-count", "0")
  })

  test("Caso 4: Seleccionar Daniel 9 y Daniel 11", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Uncheck PR
    const prCheckbox = page.getByRole("checkbox", { name: "Profetas y Reyes" })
    if (await prCheckbox.isChecked()) {
      await prCheckbox.click()
    }

    // Reveal advanced settings
    await page.getByRole("button", { name: "Configuración avanzada" }).click()

    // Select D9 and D11
    await page.getByRole("button", { name: /^D9/ }).click()
    await page.getByRole("button", { name: /^D11/ }).click()

    // Start round
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    const contractSummary = page.locator('[data-testid="round-contract-summary"]')
    await expect(contractSummary).toBeVisible({ timeout: 30_000 })
    await expect(contractSummary).toContainText("Daniel")
    await expect(contractSummary).toContainText("Cap. 9, 11")
    await expect(contractSummary).toHaveAttribute("data-pr-count", "0")
  })

  test("Caso 5: Solo verdadero/falso", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Reveal advanced settings
    await page.getByRole("button", { name: "Configuración avanzada" }).click()

    // Toggle types: uncheck single choice and fill, keep true_false
    const singleChoiceCb = page.getByRole("checkbox", { name: /Selección única/ })
    if (await singleChoiceCb.isChecked()) {
      await singleChoiceCb.click()
    }
    const fillCb = page.getByRole("checkbox", { name: /^Completar/ })
    if (await fillCb.isChecked()) {
      await fillCb.click()
    }
    const tfCb = page.getByRole("checkbox", { name: /^Verdadero/ })
    if (!(await tfCb.isChecked())) {
      await tfCb.click()
    }

    // Start round
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    await expect(page.locator("span", { hasText: /^Pregunta 1 de/ })).toBeVisible({ timeout: 15_000 })
    // Verify true/false options exist on the question card (rendered as radio options)
    await expect(page.getByRole("radio", { name: /Verdadero/ })).toBeVisible()
    await expect(page.getByRole("radio", { name: /Falso/ })).toBeVisible()
  })

  test("Caso 6: Solo Competitivas (HARD y EXPERT)", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Reveal advanced settings
    await page.getByRole("button", { name: "Configuración avanzada" }).click()

    // Deselect BASIC, MEDIUM, UNRATED so only HARD and EXPERT remain
    await page.getByRole("button", { name: "BASIC", exact: true }).click()
    await page.getByRole("button", { name: "MEDIUM", exact: true }).click()
    await page.getByRole("button", { name: "Histórica / sin clasificar", exact: true }).click()

    // Start round
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    const contractSummary = page.locator('[data-testid="round-contract-summary"]')
    await expect(contractSummary).toBeVisible({ timeout: 30_000 })
    const totalCount = await contractSummary.getAttribute("data-questions-count")
    await expect(contractSummary).toHaveAttribute("data-competitive-count", totalCount ?? "10")
  })

  test("Caso 7: Estado Falladas", async ({ page }) => {
    await page.goto("/")
    // Seed a failed question progress in IndexedDB
    await page.evaluate(() => {
      return new Promise<boolean>((resolve, reject) => {
        const req = window.indexedDB.open("conexion-biblica-2026", 4)
        req.onerror = () => reject(new Error("Error abriendo indexedDB"))
        req.onsuccess = () => {
          const db = req.result
          const tx = db.transaction("progress", "readwrite")
          const store = tx.objectStore("progress")
          store.put({
            questionKey: "BANCO_UNICO_CONEXION_BIBLICA_2026:Q-DAN1-0001",
            timesSeen: 2,
            timesCorrect: 0,
            timesIncorrect: 2,
            timesUnanswered: 0,
            currentCorrectStreak: 0,
            averageResponseTimeMs: 3000,
            bestResponseTimeMs: null,
            lastResponseTimeMs: 3000,
            lastSeenAt: Date.now(),
            masteryScore: 0,
            favorite: false,
            markedDifficult: false,
            reported: false,
            history: [],
          })
          tx.oncomplete = () => {
            db.close()
            resolve(true)
          }
          tx.onerror = () => reject(new Error("Error escribiendo en progress"))
        }
      })
    })

    // Reload page so app loads seeded progress
    await page.reload()
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Reveal advanced settings
    await page.getByRole("button", { name: "Configuración avanzada" }).click()

    // Select status "Falladas"
    await page.getByRole("combobox", { name: "Estado" }).click()
    await page.getByRole("option", { name: /^Falladas/ }).click()

    // Start round
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    const contractSummary = page.locator('[data-testid="round-contract-summary"]')
    await expect(contractSummary).toBeVisible({ timeout: 30_000 })
  })

  test("Caso 8: Estado Nuevas", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Reveal advanced settings
    await page.getByRole("button", { name: "Configuración avanzada" }).click()

    // Select status "Nuevas"
    await page.getByRole("combobox", { name: "Estado" }).click()
    await page.getByRole("option", { name: /^Nuevas/ }).click()

    // Start round
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await startBtn.click()

    const contractSummary = page.locator('[data-testid="round-contract-summary"]')
    await expect(contractSummary).toBeVisible({ timeout: 30_000 })
  })

  test("Caso 9: Combinación sin inventario", async ({ page }) => {
    await page.goto("/")
    await page.getByLabel("Navegación principal").getByRole("button", { name: "Practicar" }).click()
    await expect(page.getByRole("heading", { name: "Configura tu próxima ronda" })).toBeVisible()

    // Uncheck both works
    const danCheckbox = page.getByRole("checkbox", { name: "Daniel" })
    if (await danCheckbox.isChecked()) {
      await danCheckbox.click()
    }
    const prCheckbox = page.getByRole("checkbox", { name: "Profetas y Reyes" })
    if (await prCheckbox.isChecked()) {
      await prCheckbox.click()
    }

    // Start button must be disabled
    const startBtn = page.getByRole("button", { name: /Comenzar ronda/ })
    await expect(startBtn).toBeDisabled()
    await expect(page.getByText(/0 preguntas disponibles/)).toBeVisible()
  })
})
