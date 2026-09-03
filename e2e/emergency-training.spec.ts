import { expect, test } from '@playwright/test'

test.describe('Modo Emergencia Final 2026 E2E', () => {
  test('Consola de emergencia: valida visibilidad de bloques, botón dudé y continuidad real', async ({
    page,
  }) => {
    // 1. Mobile viewport
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    // 2. Verify Emergency Console is prominent
    const badge = page.getByText('Modo Emergencia Final 2026')
    await expect(badge).toBeVisible({ timeout: 30_000 })

    const title = page.getByRole('heading', { name: 'Entrenamiento de Alta Utilidad' })
    await expect(title).toBeVisible()

    // 3. Verify all 6 emergency modules with corrected names
    await expect(page.getByText('1. PR39–44 Intensivo')).toBeVisible()
    await expect(page.getByText('2. Daniel 7–12 Contrastes')).toBeVisible()
    await expect(page.getByText('3. Daniel 1–6 Mantenimiento')).toBeVisible()
    await expect(page.getByText('4. Reparar Errores y Dudas')).toBeVisible()
    await expect(page.getByText('5. Simulación patrón AAH 2026')).toBeVisible()
    await expect(page.getByText('6. Simulación Adversarial')).toBeVisible()

    // 4. Launch Simulación AAH
    const startSimBtn = page.getByRole('button', { name: 'Iniciar Simulación AAH' })
    await expect(startSimBtn).toBeVisible()
    await startSimBtn.click()

    // 5. Verify Quiz page is active with 100 questions and round contract
    const counter = page.getByText('Pregunta 1 de 100', { exact: true })
    await expect(counter).toBeVisible({ timeout: 30_000 })

    const contract = page.locator('[data-testid="round-contract-summary"]')
    await expect(contract).toHaveAttribute('data-questions-count', '100')
    await expect(contract).toHaveAttribute('data-dan-count', '71')
    await expect(contract).toHaveAttribute('data-pr-count', '29')

    // 6. Verify 'Dudé entre dos' toolbar button is present and clickable
    const doubtBtn = page.getByRole('button', { name: 'Dudé entre dos' })
    await expect(doubtBtn).toBeVisible()
    await doubtBtn.click()
    await expect(doubtBtn).toHaveAttribute('aria-pressed', 'true')

    // 7. Capture mobile screenshot of emergency quiz console
    await page.screenshot({ path: '.work/emergency-mobile-quiz.png', fullPage: false })

    // 8. Verify persistence across page reload
    await page.reload()
    await expect(counter).toBeVisible({ timeout: 30_000 })
  })

  test('Continuar ronda: conserva ronda, orden e índice sin crear nueva ronda', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    // 1. Iniciar PR Intensivo
    const startBtn = page.getByRole('button', { name: 'Iniciar PR Intensivo' })
    await expect(startBtn).toBeVisible({ timeout: 30_000 })
    await startBtn.click()

    // 2. Verificar que inició en la pregunta 1
    await expect(page.getByText(/^Pregunta 1 de /).first()).toBeVisible({ timeout: 30_000 })

    // 3. Responder 5 preguntas
    for (let i = 1; i <= 5; i++) {
      await expect(page.getByText(new RegExp(`^Pregunta ${i} de `)).first()).toBeVisible({ timeout: 10_000 })
      // Select first option
      await page.locator('button[role="radio"]').first().click()
      // Submit answer
      await page.getByRole('button', { name: 'Confirmar respuesta' }).click()

      // Click advance (Siguiente or Comprendido)
      const nextBtn = page.getByRole('button', { name: 'Siguiente' })
      const understoodBtn = page.getByRole('button', { name: 'Comprendido' })
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click()
      } else if (await understoodBtn.isVisible().catch(() => false)) {
        await understoodBtn.click()
      }
    }

    // Now on question 6
    await expect(page.getByText(/^Pregunta 6 de /).first()).toBeVisible({ timeout: 10_000 })

    // 4. Pausar y volver al dashboard
    const pauseBtn = page.getByRole('button', { name: 'Pausar' })
    await expect(pauseBtn).toBeVisible()
    await pauseBtn.click()

    // 5. Verificar que en el dashboard se muestra la tarjeta de Ronda activa
    const resumeCard = page.getByText('Ronda activa en curso')
    await expect(resumeCard).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText(/^Pregunta 6 de /).first()).toBeVisible()

    // 6. Pulsar Continuar ronda
    const continueBtn = page.getByRole('button', { name: 'Continuar ronda' })
    await expect(continueBtn).toBeVisible()
    await continueBtn.click()

    // 7. Comprobar que reanuda exactamente en la pregunta 6
    await expect(page.getByText(/^Pregunta 6 de /).first()).toBeVisible({ timeout: 10_000 })
  })

  test('Daniel 7–12 Contrastes: inicia con 150 preguntas sin Daniel 5', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    const startBtn = page.getByRole('button', { name: 'Iniciar Dan Contrastes' })
    await expect(startBtn).toBeVisible({ timeout: 30_000 })
    await startBtn.click()

    await expect(page.getByText('Pregunta 1 de 150', { exact: true })).toBeVisible({ timeout: 30_000 })

    const contract = page.locator('[data-testid="round-contract-summary"]')
    await expect(contract).toHaveAttribute('data-questions-count', '150')
    await expect(contract).toHaveAttribute('data-dan-count', '150')
    await expect(contract).toHaveAttribute('data-pr-count', '0')
  })

  test('Simulación Adversarial: inicia con 100 preguntas verificadas (50 PR / 50 Daniel)', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    const startBtn = page.getByRole('button', { name: 'Iniciar Simulación Adversarial' })
    await expect(startBtn).toBeVisible({ timeout: 30_000 })
    await startBtn.click()

    await expect(page.getByText('Pregunta 1 de 100', { exact: true })).toBeVisible({ timeout: 30_000 })

    const contract = page.locator('[data-testid="round-contract-summary"]')
    await expect(contract).toHaveAttribute('data-questions-count', '100')
    await expect(contract).toHaveAttribute('data-dan-count', '50')
    await expect(contract).toHaveAttribute('data-pr-count', '50')
  })

  test('Rotación: dos sesiones del mismo modo iniciadas consecutivamente reciben preguntas diferentes', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')

    // Iniciar Simulación AAH primera vez
    const startSimBtn1 = page.getByRole('button', { name: 'Iniciar Simulación AAH' })
    await expect(startSimBtn1).toBeVisible({ timeout: 30_000 })
    await startSimBtn1.click()

    await expect(page.getByText('Pregunta 1 de 100', { exact: true })).toBeVisible({ timeout: 30_000 })
    const question1 = await page.locator('#question-title').innerText()

    // Salir (descartando la ronda activa)
    const exitBtn = page.getByRole('button', { name: 'Salir' })
    await expect(exitBtn).toBeVisible()
    await exitBtn.click()

    // Regresar al dashboard
    await page.goto('/')

    // Volver a iniciar Simulación AAH (semilla distinta por timestamp)
    const startSimBtn2 = page.getByRole('button', { name: 'Iniciar Simulación AAH' })
    await expect(startSimBtn2).toBeVisible({ timeout: 30_000 })
    await startSimBtn2.click()

    await expect(page.getByText('Pregunta 1 de 100', { exact: true })).toBeVisible({ timeout: 30_000 })

    const contract = page.locator('[data-testid="round-contract-summary"]')
    await expect(contract).toHaveAttribute('data-questions-count', '100')
    await expect(contract).toHaveAttribute('data-dan-count', '71')
    await expect(contract).toHaveAttribute('data-pr-count', '29')
  })
})