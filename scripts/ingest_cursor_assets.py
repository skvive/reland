"""Copy Cursor GenerateImage outputs into RE:LAND WebP paths.

Expects files in the Cursor project assets folder, named:
  column-001.jpg | column-001.png | column-001-gen.jpg
  lesson-001.jpg | lesson-001.png

Usage:
  python scripts/ingest_cursor_assets.py --columns 1-120
  python scripts/ingest_cursor_assets.py --lectures 1-60
  python scripts/ingest_cursor_assets.py --all
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CURSOR_ASSETS = Path(r"C:\Users\user\.cursor\projects\e-currsor-C-blog\assets")
COLUMN_OUT = ROOT / "static" / "assets" / "columns"
KANG_OUT = ROOT / "kang_blog" / "assets" / "lessons"
COLUMNS_JSON = ROOT / "content" / "columns_120.json"
LECTURES_JSON = ROOT / "content" / "kang" / "lectures_60.json"


def parse_range(spec: str) -> list[int]:
    if "-" in spec:
        a, b = spec.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in re.split(r"[\s,]+", spec.strip()) if x]


def find_source(stem: str) -> Path | None:
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        for suffix in ("", "-gen", "-cursor"):
            p = CURSOR_ASSETS / f"{stem}{suffix}{ext}"
            if p.is_file():
                return p
    return None


def to_webp(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    im = im.resize((1050, 680), Image.Resampling.LANCZOS)
    im.save(dest, "WEBP", quality=84, method=6)


def ingest_columns(ids: list[int]) -> int:
    rows = json.loads(COLUMNS_JSON.read_text(encoding="utf-8"))
    by_id = {int(r["id"]): r for r in rows}
    n = 0
    for cid in ids:
        src = find_source(f"column-{cid:03d}")
        if not src:
            print(f"  skip column-{cid:03d}: no Cursor asset")
            continue
        dest = COLUMN_OUT / f"column-{cid:03d}.webp"
        to_webp(src, dest)
        row = by_id[cid]
        row["image"] = f"/static/assets/columns/column-{cid:03d}.webp"
        row["image_alt"] = (
            f"{row['category']} · {row['angle']} — Cursor AI 생성 콘셉트 (실제 사업장·확정 도면 아님)"
        )
        print(f"  column-{cid:03d} <- {src.name}")
        n += 1
    COLUMNS_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def ingest_lectures(ids: list[int]) -> int:
    rows = json.loads(LECTURES_JSON.read_text(encoding="utf-8"))
    by_id = {int(r["id"]): r for r in rows}
    n = 0
    for lid in ids:
        src = find_source(f"lesson-{lid:03d}")
        if not src:
            print(f"  skip lesson-{lid:03d}: no Cursor asset")
            continue
        dest = KANG_OUT / f"lesson-{lid:03d}.webp"
        to_webp(src, dest)
        row = by_id[lid]
        row["cover"] = f"assets/lessons/lesson-{lid:03d}.webp"
        row["cover_alt"] = f"{row['title']} — Cursor AI 강의 썸네일 (실제 현장·사무소 아님)"
        print(f"  lesson-{lid:03d} <- {src.name}")
        n += 1
    LECTURES_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--columns", default="")
    ap.add_argument("--lectures", default="")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    total = 0
    if args.all or args.columns:
        spec = "1-120" if args.all else args.columns
        print(f"columns {spec}")
        total += ingest_columns(parse_range(spec))
    if args.all or args.lectures:
        spec = "1-60" if args.all else args.lectures
        print(f"lectures {spec}")
        total += ingest_lectures(parse_range(spec))
    print(f"ingested {total} files")


if __name__ == "__main__":
    main()
