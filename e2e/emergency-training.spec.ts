import { expect, test } from '@playwright/test'

test.describe('Modo Emergencia Final 2026 E2E', () => {
  test('loads Emergency Console, launches Simulación AAH, verifies toolbar controls and survives reload', async ({
    page,
  }) => {
    // Mobile viewport to guarantee responsive verification
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    // 1. Verify Emergency Console is prominent
    const badge = page.getByText('Modo Emergencia Final 2026')
    await expect(badge).toBeVisible({ timeout: 30_000 })

    const title = page.getByRole('heading', { name: 'Entrenamiento de Alta Utilidad' })
    await expect(title).toBeVisible()

    // 2. Verify all 6 emergency modules are visible
    await expect(page.getByText('1. PR39–44 Intensivo')).toBeVisible()
    await expect(page.getByText('2. Daniel 7–12 Contrastes')).toBeVisible()
    await expect(page.getByText('3. Daniel 1–6 Mantenimiento')).toBeVisible()
    await expect(page.getByText('4. Reparar Errores y Dudas')).toBeVisible()
    await expect(page.getByText('5. Simulación AAH (Oficial)')).toBeVisible()
    await expect(page.getByText('6. Escudo Central')).toBeVisible()

    // 3. Launch Simulación AAH
    const startSimBtn = page.getByRole('button', { name: 'Iniciar Simulación AAH' })
    await expect(startSimBtn).toBeVisible()
    await startSimBtn.click()

    // 4. Verify Quiz page is active with 100 questions
    const counter = page.getByText('Pregunta 1 de 100', { exact: true })
    await expect(counter).toBeVisible({ timeout: 30_000 })

    // 5. Verify 'Dudé entre dos' toolbar button is present and clickable
    const doubtBtn = page.getByRole('button', { name: 'Dudé entre dos' })
    await expect(doubtBtn).toBeVisible()
    await doubtBtn.click()
    await expect(doubtBtn).toHaveAttribute('aria-pressed', 'true')

    // 6. Capture mobile screenshot of emergency quiz console
    await page.screenshot({ path: '.work/emergency-mobile-quiz.png', fullPage: false })

    // 7. Verify persistence across page reload
    await page.reload()
    await expect(counter).toBeVisible({ timeout: 30_000 })
  })
})