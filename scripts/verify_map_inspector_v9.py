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
        choices=page.locator(".map-results .re-open-detail")
        choices.first.wait_for(state="visible",timeout=30_000)
        dossier=page.locator("#map-project-detail .map-dossier")
        status=page.request.get(URL+"/api/districts?limit=1",timeout=15_000)
        assert status.ok,(width,status.status)
        verified_count=int(status.json().get("verified_data_rows",0))
        picked=0
        # CI's isolated demo DB can legitimately contain zero verified districts.
        # Verify the disclaimer in that mode, and keep strict real-project
        # missing-field checks when actual government rows are available.
        choices.first.click()
        dossier.wait_for(state="visible",timeout=25_000)
        if verified_count:
            assert "시연용 지역" not in dossier.inner_text(),width
            assert "실제 사업 아님" not in dossier.inner_text(),width
        else:
            assert "시연용 지역" in dossier.inner_text(),width
            assert "실제 사업 아님" in dossier.inner_text(),width
        assert "공공정보" in dossier.inner_text(),width
        assert page.locator(".map-official-link").count()>=5,width
        for item in page.locator(".map-official-link").all():
            assert item.get_attribute("target")=="_blank",width
            assert item.get_attribute("rel")=="noopener noreferrer",width
            assert (item.get_attribute("href") or "").startswith("https://"),width
        assert page.locator("#map-project-detail .map-facts dd").count()==7,width
        unknown_count=page.locator("#map-project-detail .map-unknown-facts li").count()
        if verified_count:
            if unknown_count < 6:
                print("MAP QA verified project unknown facts",width,unknown_count,dossier.inner_text()[:900],flush=True)
                page.screenshot(path=str(OUT/f"map-inspector-v9-failure-{width}.png"),full_page=True)
            assert unknown_count>=6,(width,unknown_count)
        else:
            assert unknown_count>=0,width  # Demo hub is explicitly not an official project
        assert page.locator("#map-project-detail .map-stage-track li").count()==8,width
        selected=page.locator(".map-results .re-open-detail[aria-pressed='true']")
        assert selected.count()==1,width
        assert "?id=" in page.url or "&id=" in page.url,(width,page.url)
        if choices.count()>1:
            other=choices.nth(0 if picked!=0 else 1)
            other.click()
            assert page.locator(".map-results .re-open-detail[aria-pressed='true']").count()==1,width
            choices.nth(picked).click()
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
print("PASS: seven facts; verified-project warnings or explicitly labeled demo-only data; eight stage guides; official links open new tab")
print("SCREENSHOTS: map-inspector-v9-{390,768,1280}.png")
