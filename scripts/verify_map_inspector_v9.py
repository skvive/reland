#!/usr/bin/env python3
"""RE:LAND map v9 real browser verification against local demo data.

This tests project-specific right-side dossier and official portal links, not external
government website availability or the legal currency of any individual project's data.
"""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

URL=os.getenv("RELAND_QA_URL","http://127.0.0.1:8765").rstrip("/")
OUT=Path(__file__).resolve().parents[1]/"qa-screenshots"
OUT.mkdir(exist_ok=True)
cases=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    for width in (390,768,1280):
        context=browser.new_context(viewport={"width":width,"height":920},device_scale_factor=1,
                                    is_mobile=width<920,has_touch=width<920,locale="ko-KR")
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda ex:errors.append(str(ex)))
        response=page.goto(URL+"/map",wait_until="domcontentloaded",timeout=60_000)
        assert response and response.status==200,("map HTTP",width)
        first=page.locator(".map-results .re-open-detail").first
        first.wait_for(state="visible",timeout=30_000)
        first.click()
        dossier=page.locator("#map-project-detail .map-dossier")
        dossier.wait_for(state="visible",timeout=25_000)
        assert "공공정보" in dossier.inner_text(),width
        assert page.locator(".map-official-link").count()>=5,width
        for item in page.locator(".map-official-link").all():
            assert item.get_attribute("target")=="_blank",width
            assert item.get_attribute("rel")=="noopener noreferrer",width
            assert item.get_attribute("href","").startswith("https://"),width
        assert page.locator("#map-project-detail .map-facts dd").count()==7,width
        assert page.locator("#map-project-detail .map-unknown-facts li").count()>=6,width
        assert page.locator("#map-project-detail .map-stage-track li").count()==8,width
        selected=page.locator(".map-results .re-open-detail[aria-pressed='true']")
        assert selected.count()==1,width
        assert "?id=" in page.url or "&id=" in page.url,(width,page.url)
        if page.locator(".map-results .re-open-detail").count()>1:
            second=page.locator(".map-results .re-open-detail").nth(1)
            second.click()
            assert page.locator(".map-results .re-open-detail[aria-pressed='true']").count()==1,width
        box=page.locator("#map-project-detail").bounding_box()
        assert box and box["x"]>=-3 and box["x"]+box["width"]<=width+3,(width,box)
        assert not errors,(width,errors[:3])
        page.screenshot(path=str(OUT/f"map-inspector-v9-{width}.png"),full_page=True,animations="disabled")
        cases.append(width)
        context.close()
    browser.close()
assert cases==[390,768,1280],cases
print("PASS: /map sidebar selected project renders at 390, 768 and 1280 px")
print("PASS: seven sourced facts; six missing-field warnings; eight stage guides; official links open new tab")
print("SCREENSHOTS: map-inspector-v9-{390,768,1280}.png")
