"""Optional Chromium screen QA: python tests/ui_smoke.py.

Requires: pip install playwright, then install Chromium or set CHROMIUM_PATH.
The sandbox may block browser network navigation. This harness loads the real
HTML/CSS/JS and bridges API calls through FastAPI TestClient rather than
claiming external Google/HTTPS/browser E2E verification.
"""
import json,os,re,sys,tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import app as site


def main():
    with tempfile.TemporaryDirectory() as tmp:
        site.DB_PATH=Path(tmp)/'ui-qa.sqlite'
        site.DEMO_MODE=True
        site.init_db()
        client=TestClient(site.app)
        html=(ROOT/'static/index.html').read_text(encoding='utf-8')
        html=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>','',html)
        html=re.sub(r'<script[^>]*></script>','',html)
        html=html.replace('</head>','<style>'+(ROOT/'static/style.css').read_text(encoding='utf-8')+'</style></head>')
        js=(ROOT/'static/app.js').read_text(encoding='utf-8')
        js=js.replace('location.pathname',"(window.__TEST_PATH__||'/')")
        js=js.replace('location.search',"(window.__TEST_SEARCH__||'')")
        js=js.replace("history.pushState({},'',path)",'window.__TEST_PATH__=path')
        js=js.replace('location.origin',"'https://reland.local'")
        def call_api(method,url,body):
            if not url.startswith('/api/'):
                return {'status':404,'data':{'detail':'not an API path'}}
            res=client.request(method,url,json=body)
            try:data=res.json()
            except ValueError:data={'detail':res.text}
            return {'status':res.status_code,'data':data}
        with sync_playwright() as pw:
            options={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
            chromium=os.getenv('CHROMIUM_PATH')
            if chromium:options['executable_path']=chromium
            browser=pw.chromium.launch(**options)
            page=browser.new_page(viewport={'width':1440,'height':900},locale='ko-KR')
            errors=[]
            page.on('pageerror',lambda ex:errors.append(str(ex)))
            page.expose_function('bridgeRequest',call_api)
            page.set_content(html,wait_until='domcontentloaded')
            page.evaluate('''window.__TEST_PATH__='/';window.fetch=(url,opts={})=>window.bridgeRequest(opts.method||'GET',String(url),opts.body?JSON.parse(opts.body):null).then(r=>new Response(JSON.stringify(r.data),{status:r.status,headers:{'Content-Type':'application/json'}}));''')
            page.add_script_tag(content=js)
            page.wait_for_timeout(400)
            assert page.locator('h1').count()==1
            page.screenshot(path=str(ROOT/'docs/v11-home-browser.png'),full_page=True)
            page.locator('a[data-nav="map"]').first.click()
            page.wait_for_timeout(300)
            assert page.locator('.result-row').count()==17
            page.screenshot(path=str(ROOT/'docs/v11-map-browser.png'),full_page=True)
            page.locator('.login-button').click()
            assert page.locator('[data-action="demo-login"]').count()==1
            page.locator('[data-action="demo-login"]').click()
            page.wait_for_timeout(300)
            page.locator('.login-button').click()
            page.wait_for_timeout(300)
            assert page.locator('.member-dashboard').count()==1
            page.screenshot(path=str(ROOT/'docs/v11-profile-browser.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_timeout(300)
            assert not page.evaluate('document.documentElement.scrollWidth>window.innerWidth')
            page.screenshot(path=str(ROOT/'docs/v11-mobile-browser.png'),full_page=True)
            assert not errors,errors
            browser.close()
            print('PASS: Home / Map / demo login / Personal dashboard / 390px mobile / no JS exceptions')

if __name__=='__main__':main()
