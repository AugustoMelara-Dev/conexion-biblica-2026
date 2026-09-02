import { expect, test } from "@playwright/test"

test.describe("Sprint Nacional 3X E2E", () => {
  test("loads Dashboard, shows Sprint 3X daily card, launches 100-question round, and survives reload", async ({
    page,
  }) => {
    await page.goto("/")

    // 1. Verify Sprint 3X card is prominently visible on Dashboard
    const sprintCard = page.getByText("Sprint Nacional 3X — 70% PR / 30% Daniel")
    await expect(sprintCard).toBeVisible({ timeout: 30_000 })

    // 2. Click primary button to start directed sprint
    const startBtn = page.getByRole("button", {
      name: /Iniciar Sprint Dirigido \(100 preguntas · 70\/30\)/,
    })
    await expect(startBtn).toBeVisible()
    await startBtn.click()

    // 3. Verify 100-question round is created and active
    const counter = page.getByText("Pregunta 1 de 100", { exact: true })
    await expect(counter).toBeVisible({ timeout: 30_000 })

    // 4. Test reload persistence: reloading the page restores the exact 100-question round
    await page.reload()
    await expect(counter).toBeVisible({ timeout: 30_000 })
  })
})
