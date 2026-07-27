from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import re

ROOT = Path('/mnt/data/conexion-biblica-2026')
DIST = ROOT / 'dist'
OUT = ROOT / 'test-output'
raw = (DIST / 'index.html').read_text(encoding='utf-8')
# Chromium in this managed environment blocks storage on set_content; use an equivalent in-memory adapter only for tests.
test_html = re.sub(r'\blocalStorage\b', 'TEST_STORAGE', raw)
test_html = test_html.replace("'use strict';", "'use strict';\nconst TEST_STORAGE=(()=>{let d=Object.create(null);return{getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>{d[k]=String(v)},removeItem:k=>{delete d[k]},clear:()=>{d=Object.create(null)}}})();", 1)
app = json.loads((DIST / 'app_data.json').read_text(encoding='utf-8'))

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    errors, console_errors, requests = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
    page.on('request', lambda r: requests.append(r.url))

    page.set_content(test_html, wait_until='load', timeout=60000)
    page.wait_for_selector('text=Ruta a la Final', timeout=30000)
    assert page.title().startswith('Conexión Bíblica 2026')
    assert page.locator('button.action-card').count() == 6
    assert page.locator('.lucide-icon').count() >= 6
    assert page.locator('.score-num').inner_text() == '0'
    assert page.evaluate('getQuestions().length') == app['audit']['valid']
    assert page.evaluate('getSources().length') == 18
    assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
    page.screenshot(path=str(OUT / 'mobile-home.png'))
    print('HOME_MOBILE_OK')

    # Practice: think-first, timer freeze, feedback, confidence, next question.
    page.locator('button.action-card', has_text='Rato libre · 5 min').click()
    page.wait_for_selector('.question-card')
    assert page.locator('.think-box').count() == 1
    page.get_by_role('button', name='Ya lo pensé').click()
    page.wait_for_selector('.option')
    qid = page.evaluate('currentQuestion().id')
    correct = page.evaluate('currentQuestion().correctAnswer')
    opts = page.evaluate('runtimeOptions(currentQuestion())')
    wrong_index = next((i for i, x in enumerate(opts) if x != correct), 0)
    page.locator('.option').nth(wrong_index).click()
    page.wait_for_timeout(1100)
    page.get_by_role('button', name='Confirmar').click()
    page.wait_for_selector('.feedback')
    frozen_1 = page.evaluate('activeElapsed()')
    page.wait_for_timeout(450)
    frozen_2 = page.evaluate('activeElapsed()')
    assert abs(frozen_2 - frozen_1) < 20, (frozen_1, frozen_2)
    assert page.get_by_text('¿Con qué confianza respondiste?').count() == 1
    assert page.get_by_text('Por qué no corresponde:').count() == 1
    page.screenshot(path=str(OUT / 'mobile-feedback.png'))
    page.get_by_role('button', name='Seguro').click()
    progress = page.evaluate('(qid)=>state.progress[qid]', qid)
    assert progress['errors'] == 1 and progress['safeErrors'] == 1
    page.get_by_role('button', name='Siguiente').click()
    page.wait_for_selector('.question-card')
    assert page.locator('.session-count').inner_text().startswith('2/')
    print('PRACTICE_TIMER_FEEDBACK_OK')

    # Save and resume.
    page.get_by_role('button', name='Salir').click()
    page.get_by_role('button', name='Guardar y salir').click()
    page.wait_for_selector('text=Sesión guardada')
    assert page.get_by_role('button', name='Reanudar').count() >= 1
    page.get_by_role('button', name='Reanudar').click()
    page.wait_for_selector('.question-card')
    print('SESSION_RESUME_OK')

    # Final mode: no think-first, no feedback/confidence, auto-advance, navigation locked.
    page.evaluate("discardSession();currentView='train';render()")
    page.wait_for_selector('text=Modo Final y simulacros')
    page.get_by_role('button', name='Final 25').click()
    page.wait_for_selector('.question-card')
    assert page.locator('.think-box').count() == 0
    assert page.evaluate("getComputedStyle(document.querySelector('#nav')).display") == 'none'
    page.evaluate("setView('text')")
    assert page.evaluate('currentView') == 'session'
    page.locator('.option').first.click()
    page.get_by_role('button', name='Confirmar').click()
    page.wait_for_timeout(600)
    assert page.locator('.session-count').inner_text().startswith('2/')
    assert page.locator('.feedback').count() == 0
    assert page.get_by_text('¿Con qué confianza respondiste?').count() == 0
    print('FINAL_MODE_OK')

    # Audit and full text navigation.
    page.evaluate("discardSession();currentView='audit';render()")
    page.wait_for_selector('text=Auditoría del banco')
    assert str(app['audit']['valid']) in page.locator('body').inner_text()
    page.evaluate("currentView='text';render()")
    page.wait_for_selector('text=Texto base')
    assert page.locator('.text-toolbar .segmented button').count() == 18
    page.get_by_role('button', name='Daniel 12').click()
    assert page.locator('.text-unit').count() == 13
    page.get_by_role('button', name='Profetas y Reyes 44').click()
    assert page.locator('.text-unit').count() == 22
    page.screenshot(path=str(OUT / 'mobile-text-pr44.png'))
    print('AUDIT_TEXT_18_CHAPTERS_OK')

    # Desktop layout.
    desktop = browser.new_page(viewport={'width': 1440, 'height': 1000})
    desktop_errors, desktop_requests = [], []
    desktop.on('pageerror', lambda e: desktop_errors.append(str(e)))
    desktop.on('request', lambda r: desktop_requests.append(r.url))
    desktop.set_content(test_html, wait_until='load', timeout=60000)
    desktop.wait_for_selector('text=Ruta a la Final')
    assert desktop.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
    desktop.screenshot(path=str(OUT / 'desktop-home.png'))
    assert not desktop_errors, desktop_errors
    assert not desktop_requests, desktop_requests
    desktop.close()

    assert not errors, errors
    assert not console_errors, console_errors
    assert not requests, requests
    browser.close()
    print('BROWSER_SMOKE_OK')
