#!/usr/bin/env python3
"""RE:LAND Kang class: real Chromium screenshot/viewport QA against local FastAPI.
Generated screenshots are CI artifacts, not replacements for physical-device testing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa-screenshots"
BASE = os.environ.get("RELAND_QA_URL", "http://127.0.0.1:8765").rstrip("/")
WIDTHS = (320, 375, 390, 430, 768)
IDS = (1, 30, 60)


def ensure_server() -> None:
    with urlopen(BASE + "/kang/lesson-v6.html?id=1", timeout=12) as response:
        assert response.status == 200, "local FastAPI preview must be reachable"


def inspect(page, lesson_id: int, width: int, standalone: bool = False) -> dict:
    route = f"/kang/lectures/lesson-{lesson_id:03d}.html" if standalone else f"/kang/lesson-v6.html?id={lesson_id}"
    response = page.goto(BASE + route, wait_until="domcontentloaded", timeout=45_000)
    assert response and response.status == 200, (route, "HTTP", response.status if response else None)
    assert page.locator(".lecture-hero" if not standalone else ".rk-brand-banner").count() == 1
    elements = [
        (".rk-brand-banner > img", "top brand"),
        (".rk-story-scene-brand > img", "scene brand"),
    ] if standalone else [
        (".lecture-hero > img", "top brand"),
        ("#storySceneImage", "scene brand"),
    ]
    for selector, name in elements:
        img = page.locator(selector)
        img.wait_for(state="visible", timeout=20_000)
        img.evaluate("(img) => img.decode().catch(() => null)")
        obj = img.evaluate("(img) => ({ok: img.complete && img.naturalWidth > 0, width: img.naturalWidth, src: img.currentSrc})")
        assert obj["ok"], (route, width, name, obj)
        assert "/kang/assets/kang-class-hero-v5.webp" in obj["src"], (route, width, name, obj["src"])
    image_region = page.locator(".rk-story-scene-brand" if standalone else ".scene-image-wrap")
    image_region.scroll_into_view_if_needed()
    image_box = image_region.bounding_box()
    assert image_box and image_box["height"] >= 130, (route, width, "blank/zero image region")
    label = page.locator(".rk-kang-only" if standalone else ".scene-kang-label")
    assert "강실장" in label.inner_text(), (route, width, "missing Kang wordmark")
    label_box = label.bounding_box()
    assert label_box and label_box["x"] >= image_box["x"] - 3, (route, width, "off left")
    assert label_box["x"] + label_box["width"] <= image_box["x"] + image_box["width"] + 3, (route, width, "off right")
    assert label_box["y"] >= image_box["y"] - 3, (route, width, "above image")
    assert label_box["y"] + label_box["height"] <= image_box["y"] + image_box["height"] + 3, (route, width, "below image")
    assert "RE:LAND" not in image_region.inner_text(), (route, width, "brand-only visual contains RE:LAND text")
    page_width = page.evaluate("document.documentElement.scrollWidth")
    assert page_width <= width + 3, (route, width, "horizontal overflow", page_width)
    if not standalone:
        eyebrow = page.locator("#lectureEyebrow")
        assert "RE:LAND · " in eyebrow.inner_text(), (route, width, "unexpected long heading")
        eyebrow_box = eyebrow.bounding_box()
        if width <= 430:
            assert eyebrow_box and eyebrow_box["x"] + eyebrow_box["width"] < width * .53, (
                route, width, "eyebrow crosses the presenter's face", eyebrow_box)
        assert page.locator("#storySceneTitle").inner_text().strip(), (route, width, "missing lesson title")
        assert page.locator("#learning").count() == 1
        if width == 390:
            page.locator(".lecture-hero").screenshot(path=str(OUT / f"lesson-{lesson_id:02d}-header-390.png"), animations="disabled")
            image_region.screenshot(path=str(OUT / f"lesson-{lesson_id:02d}-kang-banner-390.png"), animations="disabled")
        if width == 320 and lesson_id == 1:
            image_region.screenshot(path=str(OUT / "lesson-01-kang-banner-320.png"), animations="disabled")
    elif width == 390:
        image_region.screenshot(path=str(OUT / f"lesson-{lesson_id:02d}-standalone-390.png"), animations="disabled")
    return {"lesson": lesson_id, "viewport": width, "standalone": standalone, "pageWidth": page_width,
            "sceneHeight": round(image_box["height"], 1), "labelWidth": round(label_box["width"], 1), "ok": True}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    ensure_server()
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        for width in WIDTHS:
            context = browser.new_context(viewport={"width": width, "height": 900},
                                          device_scale_factor=1, is_mobile=True, has_touch=True,
                                          locale="ko-KR")
            page = context.new_page()
            try:
                for n in IDS:
                    results.append(inspect(page, n, width))
                if width in (320, 390):
                    for n in (1, 60):
                        results.append(inspect(page, n, width, standalone=True))
            finally:
                context.close()
        browser.close()
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    assert len(results) == 19, f"expected 19 responsive cases; got {len(results)}"
    print(f"PASS: {len(results)} Chromium layout cases / 5 widths / 1,30,60 + standalone 1,60")
    print("MEDIA: Approved Kang source image decoded; Kang wordmark inside scene; no RE:LAND overlay in scene")
    print("VIEWPORT: No horizontal overflow; story title and content anchors retained")
    print(f"SCREENSHOTS: {len(list(OUT.glob('*.png')))} files in {OUT.name}/")


if __name__ == "__main__":
    main()
