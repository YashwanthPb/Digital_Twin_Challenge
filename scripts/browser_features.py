"""Acceptance coverage for the ten research workbench features."""
import json
import os
from pathlib import Path
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def ready():page.wait_for_function("result && !document.getElementById('simulate').disabled")
    page.goto('http://127.0.0.1:8000');ready()
    assert '90 consecutive' in page.locator('#quality-summary').inner_text()
    assert page.locator('#trend-chart svg').count()==1
    assert page.locator('#residual-table tr').count()==14
    page.locator('#confidence').select_option('80');ready()
    assert page.locator('#interval-label').inner_text()=='80%'
    narrow=page.evaluate('result.forecast.at(-1).upper-result.forecast.at(-1).lower')
    mean=page.evaluate('result.forecast.at(-1).scenario')
    page.locator('#confidence').select_option('99');ready()
    assert page.evaluate('result.forecast.at(-1).upper-result.forecast.at(-1).lower')>narrow
    assert page.evaluate('result.forecast.at(-1).scenario')==mean
    page.locator('#pin-scenario').click()
    page.wait_for_function('comparisonResult !== null')
    page.locator('#steps').fill('12000');assert page.locator('#save-scenario').is_disabled()
    page.locator('#simulate').click();ready();page.wait_for_function('comparisonResult !== null')
    assert page.evaluate('result.forecast.at(-1).scenario !== comparisonResult.forecast.at(-1).scenario')
    assert page.locator('#comparison svg').count()==1
    page.locator('#scenario-name').fill('Movement experiment')
    page.locator('#save-scenario').click()
    stored=json.loads(page.evaluate("localStorage.getItem('pulsetwin-scenarios-v1')"))
    assert set(stored[0]['settings'])=={'scenario','horizon','confidence'}
    assert 'observations' not in json.dumps(stored)
    page.reload();ready()
    assert page.locator('#saved-scenarios option').inner_text()=='Movement experiment'
    page.locator('#load-scenario').click();ready()
    assert page.locator('#steps').input_value()=='12000'
    assert page.locator('#confidence').input_value()=='99'
    page.locator('#share-scenario').click()
    page.wait_for_function("document.getElementById('share-link').value.length>0")
    link=page.locator('#share-link').input_value()
    shared=json.loads(unquote(link.split('#scenario=')[1]))
    assert set(shared)=={'v','scenario','horizon','confidence'}
    second=context.new_page();second.goto(link)
    second.wait_for_function('result && !document.getElementById("simulate").disabled')
    assert second.locator('#steps').input_value()=='12000'
    assert second.locator('#confidence').input_value()=='99'
    second.close()
    page.locator('#sensitivity-feature').select_option('sodium')
    assert 'per mg' in page.locator('#sensitivity-summary').inner_text()
    assert page.locator('#sensitivity-chart svg').count()==1
    page.locator('#obs-sbp').fill('134.2');page.locator('#append-observation').click()
    page.wait_for_function("result && result.observations===91 && !document.getElementById('simulate').disabled")
    assert page.locator('#data-chip').inner_text()=='SESSION DATA'
    assert page.locator('#obs-date').input_value()=='2026-04-02'
    assert '90' not in page.locator('#quality-summary').inner_text().split('consecutive')[0]
    page.locator('#profile').select_option('dev');ready()
    page.locator('#profile').select_option('imported');ready()
    assert page.locator('#data-chip').inner_text()=='SESSION DATA'
    assert '91' in page.locator('#days-label').inner_text()
    page.evaluate('window.print=()=>{window.printRequested=true}')
    page.locator('#print-report-button').click()
    assert page.evaluate('window.printRequested')
    assert 'Team Gimites' in page.locator('#print-report').text_content()
    page.pdf(path=str(ROOT/'artifacts/sample-research-report.pdf'),format='A4',print_background=True)
    page.locator('#research-tools').scroll_into_view_if_needed()
    page.screenshot(path=str(ROOT/'artifacts/research-workbench.png'),full_page=True)
    page.locator('#delete-scenario').click();assert page.locator('#load-scenario').is_disabled()
    assert json.loads(page.evaluate("localStorage.getItem('pulsetwin-scenarios-v1')"))==[]
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.goto('http://127.0.0.1:8000/#scenario=bad-json');ready()
    page.wait_for_selector('#error:visible');assert 'Shared settings rejected' in page.locator('#error').inner_text()
    assert not errors,errors
    browser.close()
print('PASS: all ten feature workflows, saved settings persistence/deletion, sharing without observations, invalid links, session provenance and mobile overflow.')
