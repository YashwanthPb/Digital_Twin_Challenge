"""Real Chromium acceptance checks; start the application on port 8000 first."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000')
    page.wait_for_function("document.getElementById('current').textContent !== '—'")
    assert 125 < float(page.locator('#current').inner_text()) < 145
    page.screenshot(path=str(ROOT/'artifacts/dashboard.png'),full_page=True)
    page.locator('#steps').fill('12000')
    page.locator('#simulate').click()
    page.wait_for_function("!document.getElementById('simulate').disabled")
    changed=page.locator('#projected').inner_text()
    page.locator('#horizon').select_option('56')
    page.wait_for_function("document.getElementById('metric-day').textContent === '56'")
    page.screenshot(path=str(ROOT/'artifacts/scenario.png'),full_page=True)
    page.locator('#profile').select_option('dev')
    page.wait_for_function("document.getElementById('avatar').textContent === 'D'")
    page.wait_for_function("!document.getElementById('simulate').disabled")
    assert float(page.locator('#current').inner_text())>140
    page.locator('#upload').set_input_files(str(ROOT/'data/mira.csv'))
    page.wait_for_function("document.getElementById('data-chip').textContent === 'IMPORTED DATA'")
    page.wait_for_function("!document.getElementById('simulate').disabled")
    assert float(page.locator('#current').inner_text())<135
    page.locator('#profile').select_option('asha')
    page.wait_for_function("document.getElementById('avatar').textContent === 'A'")
    page.locator('#profile').select_option('imported')
    page.wait_for_function("document.getElementById('avatar').textContent === 'I'")
    page.wait_for_function("!document.getElementById('simulate').disabled")
    with page.expect_download() as d:page.locator('#export').click()
    exported=json.loads(Path(d.value.path()).read_text())
    assert len(exported['observations'])==90
    assert exported['source']=='IMPORTED DATA'
    page.locator('#upload').set_input_files({'name':'bad.csv','mimeType':'text/csv','buffer':b'bad,data\n1,2'})
    page.wait_for_selector('#error:visible')
    assert 'header' in page.locator('#error').inner_text()
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#profile').select_option('asha')
    page.wait_for_function("!document.getElementById('simulate').disabled")
    page.screenshot(path=str(ROOT/'artifacts/mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert not errors,errors
    browser.close()
print('PASS: initial render, scenario, horizon, profile, CSV import/reselection, JSON export, invalid CSV, mobile layout, no JavaScript errors.')
