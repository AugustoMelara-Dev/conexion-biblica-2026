from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import re

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
raw = (DIST / 'index.html').read_text(encoding='utf-8')
test_html = re.sub(r'\blocalStorage\b', 'TEST_STORAGE', raw)
test_html = test_html.replace("'use strict';", "'use strict';\nconst TEST_STORAGE=(()=>{let d=Object.create(null);return{getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>{d[k]=String(v)},removeItem:k=>{delete d[k]},clear:()=>{d=Object.create(null)},dump:()=>({...d})}})();", 1)
expected_q = json.loads((DIST / 'app_data.json').read_text(encoding='utf-8'))['audit']['valid']

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':390,'height':844}, accept_downloads=True)
    errors, console_errors, requests = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
    page.on('request', lambda r: requests.append(r.url))
    page.set_content(test_html, wait_until='load', timeout=60000)
    page.wait_for_selector('text=Ruta a la Final')
    assert page.evaluate('memoryOnly') is False

    # Intentionally fail safely, persist progress, and verify delayed reappearance.
    page.locator('button.action-card', has_text='Rato libre · 5 min').click()
    page.get_by_role('button', name='Ya lo pensé').click()
    qid = page.evaluate('currentQuestion().id')
    correct = page.evaluate('currentQuestion().correctAnswer')
    opts = page.evaluate('runtimeOptions(currentQuestion())')
    wrong_i = next(i for i, o in enumerate(opts) if o != correct)
    page.locator('.option').nth(wrong_i).click()
    page.wait_for_timeout(1050)
    page.get_by_role('button', name='Confirmar').click()
    page.wait_for_selector('.feedback')
    page.get_by_role('button', name='Seguro').click()
    progress = page.evaluate('(qid)=>state.progress[qid]', qid)
    assert progress['attempts'] == 1 and progress['errors'] == 1 and progress['safeErrors'] == 1
    queue = page.evaluate('session().queue')
    positions = [i for i, value in enumerate(queue) if value == qid]
    assert len(positions) >= 2 and max(positions) - min(positions) >= 4, positions
    page.get_by_role('button', name='Siguiente').click()
    count_before = page.locator('.session-count').inner_text()
    page.get_by_role('button', name='Salir').click()
    page.get_by_role('button', name='Guardar y salir').click()
    page.evaluate("state=defaultState();currentView='home';loadState();resumeSession()")
    page.wait_for_selector('.question-card')
    assert page.locator('.session-count').inner_text() == count_before
    t1 = page.evaluate('activeElapsed()'); page.wait_for_timeout(250); t2 = page.evaluate('activeElapsed()')
    assert t2 > t1
    page.evaluate("window.dispatchEvent(new Event('orientationchange'))")
    t3 = page.evaluate('activeElapsed()'); page.wait_for_timeout(150); t4 = page.evaluate('activeElapsed()')
    assert t4 >= t3
    print('PERSISTENCE_REAPPEAR_ORIENTATION_OK')

    # Skip is processed once.
    if page.locator('.think-box').count():
        page.get_by_role('button', name='Ya lo pensé').click()
    skip_qid = page.evaluate('currentQuestion().id')
    page.get_by_role('button', name='Saltar').click()
    page.wait_for_selector('.feedback')
    skip_progress = page.evaluate('(qid)=>state.progress[qid]', skip_qid)
    assert skip_progress['attempts'] == 1 and skip_progress['errors'] == 1
    assert page.evaluate('state.answers[state.answers.length-1].processed') is True
    print('SKIP_PROCESSED_ONCE_OK')

    # Final reload keeps timer and count; partial abandonment records omissions honestly.
    page.evaluate("discardSession();currentView='train';render()")
    page.get_by_role('button', name='Final 25').click()
    page.wait_for_selector('.question-card')
    page.locator('.option').first.click(); page.get_by_role('button', name='Confirmar').click(); page.wait_for_timeout(500)
    final_count = page.locator('.session-count').inner_text()
    f1 = page.evaluate('activeElapsed()')
    page.evaluate("state=defaultState();currentView='home';loadState();resumeSession()")
    page.wait_for_selector('.question-card')
    assert page.locator('.session-count').inner_text() == final_count
    f2 = page.evaluate('activeElapsed()')
    assert f2 >= f1
    page.get_by_role('button', name='Salir').click()
    page.get_by_role('button', name='Finalizar intento').click()
    page.wait_for_selector('text=Resultado de la sesión')
    assert page.evaluate('state.lastResult.abandoned') is True
    assert page.evaluate('state.lastResult.total') == 25
    assert page.evaluate('state.lastResult.skipped') >= 23
    assert page.locator('.result-score').inner_text() != '100%'
    print('FINAL_RECOVERY_ABANDONMENT_OK')

    # Theme persists.
    page.evaluate("state.settings.theme='dark';saveState();applyTheme()")
    assert page.get_attribute('html','data-theme') == 'dark'
    page.evaluate("state=defaultState();loadState();applyTheme();currentView='home';render()")
    assert page.get_attribute('html','data-theme') == 'dark'
    print('THEME_PERSISTENCE_OK')

    # Duplicate import rejected; invalid JSON does not replace data.
    before = page.evaluate('getQuestions().length')
    payload = page.evaluate("""()=>{const q=structuredClone(getQuestions()[0]);q.id='DIFFERENT-ID-SAME-CONTENT';return JSON.stringify({kind:'cb2026-bank',version:'test',questions:[q],sources:[]})}""")
    page.evaluate("payload=>{fileIntent='bank';importFile(new File([payload],'dup.json',{type:'application/json'}))}", payload)
    page.wait_for_timeout(350)
    assert page.evaluate('getQuestions().length') == before
    assert page.get_by_text('Banco importado: 0 preguntas nuevas.').count() == 1
    answers_before = page.evaluate('state.answers.length')
    page.evaluate("()=>{fileIntent='progress';importFile(new File(['{bad json'],'bad.json',{type:'application/json'}))}")
    page.wait_for_timeout(300)
    assert page.evaluate('state.answers.length') == answers_before
    print('IMPORT_SAFETY_OK')

    # Exports contain the complete bank/progress.
    exports = page.evaluate("""async()=>{window.__exports=[];URL.createObjectURL=blob=>{window.__exports.push({blob,name:''});return 'blob:test'};URL.revokeObjectURL=()=>{};HTMLAnchorElement.prototype.click=function(){window.__exports[window.__exports.length-1].name=this.download};exportProgress();exportBank();return await Promise.all(window.__exports.map(async x=>({name:x.name,text:await x.blob.text()})))}""")
    assert len(exports) == 2
    p0, p1 = json.loads(exports[0]['text']), json.loads(exports[1]['text'])
    assert p0['kind'] == 'cb2026-progress' and p1['kind'] == 'cb2026-bank'
    assert len(p1['questions']) == expected_q
    print('EXPORTS_COMPLETE_OK')

    assert not errors, errors
    assert not console_errors, console_errors
    assert not requests, requests
    browser.close()
    print('PERSISTENCE_TESTS_OK')
