"""Chromium E2E-like browser checks with FastAPI TestClient response bridge.
Local socket networking may be blocked in this environment; no external OAuth/Google publish is tested.
"""
from __future__ import annotations
import sys
from pathlib import Path
from urllib.parse import urlsplit
import base64, re
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app import app
ROOT=Path(__file__).resolve().parents[1]
client=TestClient(app)
def preview_html():
 # Local network navigation blocked by Chromium policy. Inject all code and binary assets
 # using data URLs; this measures layout & UI logic without claiming hosted-domain E2E.
 root=ROOT/'kang_blog'
 page=(root/'index.html').read_text(encoding='utf-8')
 css=(root/'blog.css').read_text(encoding='utf-8')
 scripts=(root/'data.js').read_text(encoding='utf-8')+'\n'+(root/'blog.js').read_text(encoding='utf-8')
 def data_uri(path):
  suffix=path.suffix.lower()
  media='image/svg+xml' if suffix=='.svg' else 'image/webp' if suffix=='.webp' else 'image/png'
  return 'data:'+media+';base64,'+base64.b64encode(path.read_bytes()).decode()
 def replace_url(match):
  local=root/match.group(1)
  return data_uri(local) if local.is_file() else match.group(0)
 css=css.replace("url('/kang/assets/city.webp')","url('"+data_uri(root/'assets'/'city.webp')+"')")
 page=page.replace('<link rel="stylesheet" href="/kang/blog.css">','<style>'+css+'</style>')
 page=page.replace('<script defer src="/kang/data.js"></script><script defer src="/kang/blog.js"></script>','')
 page=re.sub(r'/kang/(assets/[A-Za-z0-9_.-]+\.(?:webp|svg))',lambda m:data_uri(root/m.group(1)) if (root/m.group(1)).is_file() else m.group(0),page)
 page=page.replace('</body>','<script>'+scripts+'</script></body>')
 # dynamically added images in cards point at a test page with no host; replace their src later.
 return page

errors=[]
thumbs=['data:image/webp;base64,'+base64.b64encode((ROOT/'kang_blog'/'assets'/f'topic-{i:02d}.webp').read_bytes()).decode() for i in range(1,13)]
def hydrate_thumbnails(page):
 page.evaluate(r"""sources => {document.querySelectorAll('.card-visual img').forEach((node,idx) => {const matched=node.src.match(/topic-(\d+)\.webp/); if (matched) node.src=sources[Number(matched[1])-1]})}""",thumbs)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 ctx=browser.new_context(viewport={'width':1440,'height':920}, device_scale_factor=1)
 page=ctx.new_page()
 def bridge(route):
  address=urlsplit(route.request.url)
  url=address.path+('?' +address.query if address.query else '')
  try:
   resp=client.get(url)
   hdr={'content-type':resp.headers.get('content-type','text/plain')}
   route.fulfill(status=resp.status_code,body=resp.content,headers=hdr)
  except Exception as e:
   errors.append(str(e));route.abort()
 page.route('**/*',bridge)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(preview_html(),wait_until='load')
 page.wait_for_timeout(500)
 assert page.locator('.lesson-card').count()==9,page.locator('.lesson-card').count()
 assert page.locator('.qa-item').count()==30
 assert '재개발 법률' in page.locator('.hero h1').inner_text()
 hydrate_thumbnails(page)
 page.screenshot(path=str(ROOT/'docs'/'kang'/'desktop.png'),full_page=True)
 page.locator('[data-lesson="1"]').click()
 assert page.locator('#modal').is_visible()
 assert page.locator('.lesson-parts .lesson-part').count()>=7
 assert page.locator('.diagram').is_visible()
 page.locator('#modalClose').click()
 page.locator('#search').fill('총회')
 assert page.locator('.lesson-card').count()>0
 page.locator('#search').fill('')
 page.locator('.qa-button').first.click()
 assert page.locator('.qa-item.open').count()==1
 page.locator('#faqFilter').select_option('행정소송·인가취소')
 assert page.locator('.qa-item').count()==3
 ctx.close()
 mobile=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
 m=mobile.new_page();m.route('**/*',bridge)
 m.on('pageerror',lambda e:errors.append(str(e)))
 m.set_content(preview_html(),wait_until='load');m.wait_for_timeout(500)
 hydrate_thumbnails(m)
 sizes=m.evaluate('({document:document.documentElement.scrollWidth, viewport:window.innerWidth})')
 assert sizes['document']<=sizes['viewport']+1,sizes
 m.screenshot(path=str(ROOT/'docs'/'kang'/'mobile.png'),full_page=True)
 m.locator('#menuBtn').click();assert m.locator('.head-row nav').is_visible()
 m.locator('[data-lesson="1"]').click();assert m.locator('#modal').is_visible()
 m.locator('#modalClose').click()
 assert not errors,errors
 browser.close()
 print('BROWSER CHECK OK: desktop + mobile, query, lesson modal, FAQ, menu, overflow; screenshots saved.')
