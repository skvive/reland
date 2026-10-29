"""Build unique editorial WebP per column (120) and Kang lecture (60).

Blends licensed AI base assets with category-specific color grading and
angle-specific symbolic overlays so each card thumbnail is distinct.
Updates content/columns_120.json and content/kang/lectures_60.json paths.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "assets"
CURSOR_ASSETS = Path(r"C:\Users\user\.cursor\projects\e-currsor-C-blog\assets")
COLUMN_OUT = ASSETS / "columns"
KANG_OUT = ROOT / "kang_blog" / "assets" / "lessons"
COLUMNS_JSON = ROOT / "content" / "columns_120.json"
LECTURES_JSON = ROOT / "content" / "kang" / "lectures_60.json"

CATEGORY_TINT = {
    "조합설립 절차": (72, 118, 98),
    "총회와 의결": (58, 92, 118),
    "분양신청": (88, 108, 72),
    "관리처분계획": (64, 102, 108),
    "정보공개": (92, 118, 128),
    "이전고시·등기": (108, 92, 72),
    "주민 참여와 분쟁 예방": (82, 112, 88),
    "상담 준비 체크리스트": (96, 108, 118),
    "등기·서류 실무": (74, 98, 118),
    "행정 인허가·신청": (68, 108, 102),
    "전문가 광고·홍보": (118, 98, 72),
    "지역별 공개자료 검증": (88, 102, 118),
}

KANG_TINT = {
    "분담금·감정평가": (78, 108, 96),
    "조합 갈등·총회": (58, 92, 118),
    "행정절차·정보공개": (92, 118, 128),
    "행정심판·불복": (68, 98, 118),
    "행정소송·인가취소": (72, 88, 118),
    "민사소송·소장 읽기": (96, 108, 118),
    "형사고소·사실 확인": (88, 92, 108),
    "사업단계·도면 읽기": (82, 112, 88),
    "분양·관리처분": (64, 102, 108),
    "보상·이주·갈등관리": (88, 108, 72),
}


def _sources() -> list[Path]:
    paths: list[Path] = []
    for i in range(1, 13):
        p = ASSETS / f"legal-topic-{i:02d}.webp"
        if p.exists():
            paths.append(p)
    for name in (
        "legal-office-source.webp",
        "reland-hero-city.webp",
        "community-neighborhood.webp",
    ):
        p = ASSETS / name
        if p.exists():
            paths.append(p)
    for name in (
        "reland-base-union-docs.jpg",
        "reland-base-meeting-vote.jpg",
        "reland-base-sale-apply.jpg",
    ):
        p = CURSOR_ASSETS / name
        if p.exists():
            paths.append(p)
    ai_bases = ASSETS / "ai-bases"
    if ai_bases.is_dir():
        paths.extend(sorted(ai_bases.glob("*.jpg")))
    return paths


def _seed(*parts: str | int) -> random.Random:
    h = sum(ord(c) for p in parts for c in str(p))
    return random.Random(h * 9973 + 17)


def _load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def _tint(im: Image.Image, rgb: tuple[int, int, int], strength: float) -> Image.Image:
    overlay = Image.new("RGB", im.size, rgb)
    return Image.blend(im, overlay, strength)


def _unique_crop(im: Image.Image, rng: random.Random) -> Image.Image:
    w, h = im.size
    target = 1.55
    crop_w = min(w, int(h * target))
    crop_h = min(h, int(w / target))
    if crop_w < w:
        x0 = rng.randint(0, w - crop_w)
        im = im.crop((x0, 0, x0 + crop_w, h))
    elif crop_h < h:
        y0 = rng.randint(0, h - crop_h)
        im = im.crop((0, y0, w, y0 + crop_h))
    return im


def _draw_overlay(im: Image.Image, angle_index: int, label: str) -> None:
    draw = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    # bottom gradient for title legibility on cards
    for y in range(int(h * 0.55), h):
        a = int(180 * (y - h * 0.55) / (h * 0.45))
        draw.line([(0, y), (w, y)], fill=(18, 45, 38, min(200, a)))
    accent = (196, 168, 92, 210)
    x, y = int(w * 0.08), int(h * 0.12)
    shapes = angle_index % 10
    if shapes == 0:
        for i in range(3):
            draw.rounded_rectangle(
                (x + i * 18, y + i * 10, x + 140 + i * 18, y + 96 + i * 10),
                radius=8,
                outline=accent,
                width=3,
            )
    elif shapes == 1:
        draw.ellipse((x, y, x + 110, y + 110), outline=accent, width=4)
        draw.ellipse((x + 70, y + 40, x + 200, y + 170), outline=(140, 196, 168, 180), width=3)
    elif shapes == 2:
        draw.rectangle((x, y, x + 160, y + 110), outline=accent, width=3)
        draw.line([(x + 12, y + 36), (x + 148, y + 36)], fill=accent, width=2)
    elif shapes == 3:
        for i in range(5):
            draw.rectangle((x + i * 34, y + 40, x + 24 + i * 34, y + 120), outline=accent, width=2)
    elif shapes == 4:
        draw.polygon([(x, y + 80), (x + 60, y), (x + 120, y + 80)], outline=accent)
        draw.rectangle((x + 140, y + 20, x + 220, y + 120), outline=(140, 196, 168, 200), width=3)
    elif shapes == 5:
        draw.line([(x, y + 60), (x + 180, y + 60)], fill=accent, width=4)
        draw.line([(x, y + 90), (x + 140, y + 90)], fill=(140, 196, 168, 200), width=3)
    elif shapes == 6:
        draw.arc((x, y, x + 120, y + 120), 20, 300, fill=accent, width=4)
        draw.line([(x + 60, y + 60), (x + 110, y + 20)], fill=accent, width=4)
    elif shapes == 7:
        draw.ellipse((x + 40, y + 30, x + 110, y + 100), outline=accent, width=4)
        draw.rectangle((x + 130, y + 50, x + 210, y + 70), fill=(140, 196, 168, 160))
    elif shapes == 8:
        draw.polygon([(x + 60, y), (x + 120, y + 110), (x, y + 110)], outline=accent)
    else:
        for i in range(4):
            draw.rectangle((x, y + i * 28, x + 18, y + 18 + i * 28), fill=accent)
            draw.line([(x + 28, y + 10 + i * 28), (x + 170, y + 10 + i * 28)], fill=(140, 196, 168, 190), width=2)
    # subtle category tag strip (no readable text — abstract bar only)
    draw.rounded_rectangle((x, h - int(h * 0.18), x + min(220, w // 3), h - int(h * 0.12)), radius=6, fill=(24, 58, 48, 120))


def render_frame(
    *,
    item_id: int,
    category: str,
    angle: str,
    sources: list[Path],
    tint_map: dict[str, tuple[int, int, int]],
) -> Image.Image:
    rng = _seed(item_id, category, angle)
    src = sources[(item_id + len(angle)) % len(sources)]
    im = _load_rgb(src)
    im = _unique_crop(im, rng)
    im = ImageEnhance.Contrast(im).enhance(0.92 + (item_id % 7) * 0.03)
    im = ImageEnhance.Brightness(im).enhance(0.94 + (item_id % 5) * 0.02)
    tint = tint_map.get(category, (72, 108, 96))
    im = _tint(im, tint, 0.18 + (item_id % 4) * 0.04)
    if item_id % 3 == 0:
        im = im.filter(ImageFilter.GaussianBlur(radius=0.3))
    angle_index = abs(hash(angle)) % 10
    _draw_overlay(im, angle_index, angle)
    im = im.resize((1050, 680), Image.Resampling.LANCZOS)
    return im


def main() -> None:
    sources = _sources()
    if len(sources) < 3:
        raise SystemExit("Need at least 3 source assets under static/assets")

    COLUMN_OUT.mkdir(parents=True, exist_ok=True)
    KANG_OUT.mkdir(parents=True, exist_ok=True)

    columns = json.loads(COLUMNS_JSON.read_text(encoding="utf-8"))
    for row in columns:
        cid = int(row["id"])
        out = COLUMN_OUT / f"column-{cid:03d}.webp"
        frame = render_frame(
            item_id=cid,
            category=row["category"],
            angle=row["angle"],
            sources=sources,
            tint_map=CATEGORY_TINT,
        )
        frame.save(out, "WEBP", quality=82, method=6)
        row["image"] = f"/static/assets/columns/column-{cid:03d}.webp"
        row["image_alt"] = (
            f"{row['category']} · {row['angle']} — PIL 합성 콘셉트 (실제 사업장·확정 도면 아님)"
        )
    COLUMNS_JSON.write_text(json.dumps(columns, ensure_ascii=False, indent=2), encoding="utf-8")

    lectures = json.loads(LECTURES_JSON.read_text(encoding="utf-8"))
    for row in lectures:
        lid = int(row["id"])
        out = KANG_OUT / f"lesson-{lid:03d}.webp"
        frame = render_frame(
            item_id=lid + 1000,
            category=row["category"],
            angle=row["title"],
            sources=sources,
            tint_map=KANG_TINT,
        )
        frame.save(out, "WEBP", quality=82, method=6)
        row["cover"] = f"assets/lessons/lesson-{lid:03d}.webp"
        row["cover_alt"] = f"{row['title']} — AI 기반 강의 썸네일 (실제 사무소·현장 아님)"
    LECTURES_JSON.write_text(json.dumps(lectures, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"columns: {len(columns)} -> {COLUMN_OUT}")
    print(f"lectures: {len(lectures)} -> {KANG_OUT}")
    print(f"sources used: {len(sources)}")


if __name__ == "__main__":
    main()
