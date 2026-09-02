import { expect, test } from "@playwright/test"

test.describe("Sprint Nacional 3X E2E", () => {
  test("loads Dashboard, shows Sprint 3X daily card, launches 100-question round with exact 70/30 distribution", async ({
    page,
  }) => {
    await page.goto("/")

    // Verify Sprint 3X card
    const sprintCard = page.getByText("Sprint Nacional 3X — 70% PR / 30% Daniel")
    await expect(sprintCard).toBeVisible({ timeout: 30_000 })

    // Click primary button to start directed sprint
    const startBtn = page.getByRole("button", {
      name: /Iniciar Sprint Dirigido \(100 preguntas · 70\/30\)/,
    })
    await expect(startBtn).toBeVisible()
    await startBtn.click()

    // Wait for quiz screen
    await expect(page.getByText("Pregunta 1 de 100")).toBeVisible({
      timeout: 30_000,
    })

    // Inspect persisted ActiveRound in localStorage or IndexedDB
    const activeRoundSummary = await page.evaluate(async () => {
      // Access IndexedDB active round
      return new Promise<any>((resolve) => {
        const req = indexedDB.open("cb2026-v7", 1)
        req.onsuccess = () => {
          const db = req.result
          const tx = db.transaction("activeRounds", "readonly")
          const getReq = tx.objectStore("activeRounds").get("active")
          getReq.onsuccess = () => resolve(getReq.result)
          getReq.onerror = () => resolve(null)
        }
        req.onerror = () => resolve(null)
      })
    })

    expect(activeRoundSummary).toBeTruthy()
    expect(activeRoundSummary.config.strategy).toBe("sprint-3x")
    expect(activeRoundSummary.selectionSummary.strategy).toBe("sprint-3x")
    expect(activeRoundSummary.selectionSummary.prCount).toBe(70)
    expect(activeRoundSummary.selectionSummary.danielCount).toBe(30)
    expect(activeRoundSummary.selectionSummary.familyCounts.single_choice).toBe(45)
    expect(activeRoundSummary.selectionSummary.familyCounts.fill_blank).toBe(30)
    expect(activeRoundSummary.selectionSummary.familyCounts.true_false).toBe(25)
    expect(activeRoundSummary.selectionSummary.distinctFacts).toBe(100)
  })
})
