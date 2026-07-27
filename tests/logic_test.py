from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import re

ROOT = Path('/mnt/data/conexion-biblica-2026')
DIST = ROOT / 'dist'
raw = (DIST / 'index.html').read_text(encoding='utf-8')
test_html = re.sub(r'\blocalStorage\b', 'TEST_STORAGE', raw)
test_html = test_html.replace("'use strict';", "'use strict';\nconst TEST_STORAGE=(()=>{let d=Object.create(null);return{getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>{d[k]=String(v)},removeItem:k=>{delete d[k]},clear:()=>{d=Object.create(null)}}})();", 1)
app = json.loads((DIST / 'app_data.json').read_text(encoding='utf-8'))

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.set_content(test_html, wait_until='load', timeout=60000)
    page.wait_for_selector('text=Ruta a la Final')

    # Deadline routing and classification flags.
    assert page.evaluate('nextDeadline().key') == 'church'
    assert page.evaluate('state.classifications.church=true;nextDeadline().key') == 'district'
    assert page.evaluate('state.classifications.district=true;nextDeadline().key') == 'association'
    page.evaluate("state.classifications={church:false,district:false}")
    print('DEADLINE_ROUTING_OK')

    # Mode sizing and exit check.
    d1_count = next(p['questions'] for p in app['profiles'] if p['chapter'] == 'Daniel 1')
    page.evaluate("startMode('learn',{chapter:'Daniel 1',count:10})")
    learned = page.evaluate("({initial:session().initialCount,total:session().queue.length,unique:new Set(session().queue).size})")
    assert learned == {'initial': 10, 'total': 13, 'unique': 10}, learned
    page.evaluate("discardSession();startMode('marathon',{chapter:'Daniel 1'})")
    marathon = page.evaluate("({initial:session().initialCount,total:session().queue.length,unique:new Set(session().queue).size})")
    assert marathon == {'initial': d1_count, 'total': d1_count, 'unique': d1_count}, marathon
    before = page.evaluate('session().queue.length')
    page.evaluate("scheduleReappearance({qid:session().queue[0],correct:false,confidence:'Seguro'})")
    assert page.evaluate('session().queue.length') == before
    page.evaluate('discardSession()')
    print('MODE_SIZING_MARATHON_OK')

    # Time calibration excludes invalid samples and uses P60/P50 gate behavior.
    result = page.evaluate("""()=>{
      const backup=structuredClone(state);state.answers=[];
      for(let i=0;i<20;i++)state.answers.push({correct:true,skipped:false,confidence:'Seguro',interrupted:false,activeMs:2000+i*100,chapter:'Daniel 1',type:'seleccionar',difficulty:'difícil'});
      state.answers.push({correct:false,skipped:false,confidence:'Seguro',interrupted:false,activeMs:3000,chapter:'Daniel 1',type:'seleccionar',difficulty:'difícil'});
      state.answers.push({correct:true,skipped:false,confidence:'Adiviné',interrupted:false,activeMs:3000,chapter:'Daniel 1',type:'seleccionar',difficulty:'difícil'});
      state.answers.push({correct:true,skipped:false,confidence:'Seguro',interrupted:true,activeMs:3000,chapter:'Daniel 1',type:'seleccionar',difficulty:'difícil'});
      state.answers.push({correct:true,skipped:false,confidence:'Seguro',interrupted:false,activeMs:500,chapter:'Daniel 1',type:'seleccionar',difficulty:'difícil'});
      state.answers.push({correct:true,skipped:false,confidence:'Seguro',interrupted:false,activeMs:999999,chapter:'Daniel 1',type:'seleccionar',difficulty:'difícil'});
      const g=timeGoal('Daniel 1'), sampleCount=timeSamples({chapter:'Daniel 1'}).length;state=backup;
      return {ready:g.ready,count:g.count,needed:g.needed,target:g.targetMs,sampleCount};
    }""")
    assert result['ready'] and result['count'] == 20 and result['sampleCount'] == 20 and result['needed'] == 20, result
    assert 3000 <= result['target'] <= 3300, result
    print('TIME_CALIBRATION_OK')

    # Mastery needs multi-day evidence; a subsequent miss creates relapse.
    mastery = page.evaluate("""()=>{
      const backup=structuredClone(state),q=getQuestions().find(x=>['difícil','trampa'].includes(x.difficulty));
      state.progress={};state.answers=[];
      const mk=(date,correct=true)=>({id:id(),qid:q.id,question:q.prompt,chapter:q.chapter,source:q.source,reference:q.reference,type:q.type,difficulty:q.difficulty,detail:q.detail,family:q.family,selected:correct?q.correctAnswer:'x',correctAnswer:q.correctAnswer,correct,skipped:false,activeMs:3000,date,at:new Date().toISOString(),confidence:'Seguro',mode:'adaptive',isFinal:false,interrupted:false});
      applyProgress(mk('2026-07-27',true));applyProgress(mk('2026-07-28',true));applyProgress(mk('2026-07-28',true));
      const mastered=progressFor(q.id).status;applyProgress(mk('2026-07-29',false));
      const relapse=progressFor(q.id).status,due=progressFor(q.id).nextDue;state=backup;return{mastered,relapse,due};
    }""")
    assert mastery['mastered'] == 'Dominada' and mastery['relapse'] == 'Recaída', mastery
    print('MASTERY_RELAPSE_OK')

    # Adaptive selection exact size, no duplicates, full-bank filters.
    adaptive = page.evaluate("()=>{state.progress={};const q=adaptivePick({chapter:'all'},75);return{n:q.length,u:new Set(q.map(x=>x.id)).size,chapters:new Set(q.map(x=>x.chapter)).size}}")
    assert adaptive['n'] == 75 and adaptive['u'] == 75 and adaptive['chapters'] >= 4, adaptive
    assert page.evaluate("filterQuestions({chapter:'Daniel 12'}).length") == next(p['questions'] for p in app['profiles'] if p['chapter']=='Daniel 12')
    print('ADAPTIVE_FILTERS_OK')

    # Imported bank is deduplicated and receives a dynamic profile.
    profile = page.evaluate("""()=>{
      const q=structuredClone(getQuestions()[0]);q.id='TEST-CH-1';q.chapter='Capítulo importado';q.source='Fuente importada';q.reference='Fuente importada, unidad 1';q.unitKey='import:1';q.prompt=q.prompt+' [importada]';q.context=q.evidence;
      state.importedBanks=[{id:'test',questions:[q],sources:[{id:'src-test',source:'Fuente importada',chapter:'Capítulo importado',title:'Capítulo importado',version:'Texto suministrado',units:[{reference:q.reference,unitKey:q.unitKey,text:q.context}]}],profiles:[]}];
      const p=getProfiles().find(x=>x.chapter==='Capítulo importado'),filtered=filterQuestions({chapter:'Capítulo importado'}).length;state.importedBanks=[];return{p,filtered};
    }""")
    assert profile['filtered'] == 1 and profile['p']['questions'] == 1 and profile['p']['competitiveGoal'] == 100, profile
    print('IMPORT_PROFILE_OK')

    assert not errors, errors
    browser.close()
    print('LOGIC_TESTS_OK')
