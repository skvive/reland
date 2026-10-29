"""Generate one unique AI editorial image per column (120) and Kang lecture (60).

Uses OpenAI Images API (OPENAI_API_KEY). Skips existing files unless --force.
Updates content/columns_120.json image paths and content/kang/lectures_60.json cover fields.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLUMNS_JSON = ROOT / "content" / "columns_120.json"
LECTURES_JSON = ROOT / "content" / "kang" / "lectures_60.json"
COLUMN_OUT = ROOT / "static" / "assets" / "columns"
KANG_OUT = ROOT / "kang_blog" / "assets" / "lessons"

NEGATIVE = (
    "text, letters, numbers, watermark, logo, brand name, Korean hangul, "
    "real identifiable building, construction site photo, news screenshot, "
    "lawyer face, celebrity, gore, violence"
)

CATEGORY_SCENE = {
    "조합설립 절차": "official documents and consent forms on a planning desk, abstract apartment blocks",
    "총회와 의결": "cooperative meeting room, ballots and agenda folders, community decision",
    "분양신청": "housing allocation models, floor plan blueprints, application forms concept",
    "관리처분계획": "urban renewal master plan boards, cost breakdown charts as abstract shapes",
    "정보공개": "transparent filing cabinets and digital archive screens, public records",
    "이전고시·등기": "registry office metaphor, keys and property transfer documents",
    "주민 참여와 분쟁 예방": "neighbors in discussion circle, community workshop not protest",
    "상담 준비 체크리스트": "organized checklist binder, calm consultation desk",
    "등기·서류 실무": "notary desk with sealed documents and property ledger books",
    "행정 인허가·신청": "government counter window, permit stamps and application stack",
    "전문가 광고·홍보": "ethical professional brochure layout without faces, compliance theme",
    "지역별 공개자료 검증": "city hall notice board and regional map pins, verification magnifier",
}

KANG_CATEGORY_SCENE = {
    "분담금·감정평가": "cost tables and appraisal documents, calculator and ledger",
    "조합 갈등·총회": "general assembly room, voting slips, transparent governance",
    "행정절차·정보공개": "administrative files and disclosure portal on laptop",
    "행정심판·불복": "appeal timeline calendar and official decision letters",
    "행정소송·인가취소": "courtroom sketch abstract, administrative lawsuit documents",
    "민사소송·소장 읽기": "civil complaint structure diagram on desk, contract papers",
    "형사고소·사실 확인": "evidence timeline board, factual record keeping",
    "사업단계·도면 읽기": "zoning map layers, blueprint rolls, planning phases",
    "분양·관리처분": "housing supply plan and member allocation sheets",
    "보상·이주·갈등관리": "relocation support documents, moving boxes and compensation folder",
}


def _client():
    try:
        from openai import OpenAI
    except ImportError:
        print("Install openai: pip install openai", file=sys.stderr)
        raise SystemExit(1)
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY is not set", file=sys.stderr)
        raise SystemExit(1)
    return OpenAI(api_key=key)


def prompt_column(category: str, angle: str, title: str) -> str:
    scene = CATEGORY_SCENE.get(category, "urban renewal law education desk scene")
    return (
        f"Editorial concept illustration for Korean urban redevelopment law education. "
        f"Topic: {category}. Focus: {angle}. "
        f"Visual scene: {scene}. "
        f"Palette: sage green, deep teal, warm cream highlights. "
        f"Style: premium legal journal cover, soft cinematic light, shallow depth of field. "
        f"Must be fictional concept art, not a real project site or law firm photo. "
        f"No text or readable characters anywhere."
    )


def prompt_lecture(category: str, title: str, summary: str) -> str:
    scene = KANG_CATEGORY_SCENE.get(category, "legal education studio desk")
    short = summary[:120].replace("\n", " ")
    return (
        f"Editorial concept illustration for Korean redevelopment law classroom content. "
        f"Category: {category}. Lesson theme: {title}. "
        f"Context: {short}. Scene: {scene}. "
        f"Palette: deep forest green, gold accent, dark teal background gradient. "
        f"Educational magazine style, no text, no logos, not a real person or office."
    )


def generate_png(client, prompt: str, size: str = "1536x1024") -> bytes:
    # gpt-image-1 supports landscape editorial sizes
    for attempt in range(3):
        try:
            resp = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
                quality="medium",
                n=1,
            )
            import base64

            return base64.b64decode(resp.data[0].b64_json)
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                raise
            print(f"  retry ({attempt + 1}): {exc}", flush=True)
            time.sleep(2 + attempt * 2)


def save_webp(png_bytes: bytes, dest: Path) -> None:
    from PIL import Image
    import io

    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    im = im.resize((1050, 700), Image.Resampling.LANCZOS)
    im.save(dest, "WEBP", quality=82, method=6)


def slug_alt_column(category: str, angle: str) -> str:
    return f"{category} · {angle} — AI 생성 교육용 콘셉트 이미지 (실제 사업장·확정 도면 아님)"


def run_columns(client, force: bool, limit: int | None, start_id: int) -> None:
    rows = json.loads(COLUMNS_JSON.read_text(encoding="utf-8"))
    done = 0
    for row in rows:
        cid = int(row["id"])
        if cid < start_id:
            continue
        if limit is not None and done >= limit:
            break
        rel = f"/static/assets/columns/column-{cid:03d}.webp"
        out = COLUMN_OUT / f"column-{cid:03d}.webp"
        if out.exists() and not force:
            row["image"] = rel
            row["image_alt"] = slug_alt_column(row["category"], row["angle"])
            continue
        print(f"[column {cid:03d}] {row['angle'][:40]}…", flush=True)
        png = generate_png(client, prompt_column(row["category"], row["angle"], row["title"]))
        save_webp(png, out)
        row["image"] = rel
        row["image_alt"] = slug_alt_column(row["category"], row["angle"])
        done += 1
        time.sleep(0.4)
    COLUMNS_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"columns updated ({done} generated this run)")


def run_lectures(client, force: bool, limit: int | None, start_id: int) -> None:
    rows = json.loads(LECTURES_JSON.read_text(encoding="utf-8"))
    done = 0
    for row in rows:
        lid = int(row["id"])
        if lid < start_id:
            continue
        if limit is not None and done >= limit:
            break
        rel = f"assets/lessons/lesson-{lid:03d}.webp"
        out = KANG_OUT / f"lesson-{lid:03d}.webp"
        if out.exists() and not force:
            row["cover"] = rel
            row["cover_alt"] = f"{row['title']} — AI 생성 강의 썸네일 (실제 사무소·현장 아님)"
            continue
        print(f"[lesson {lid:03d}] {row['title'][:36]}…", flush=True)
        png = generate_png(client, prompt_lecture(row["category"], row["title"], row["summary"]))
        save_webp(png, out)
        row["cover"] = rel
        row["cover_alt"] = f"{row['title']} — AI 생성 강의 썸네일 (실제 사무소·현장 아님)"
        done += 1
        time.sleep(0.4)
    LECTURES_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"lectures updated ({done} generated this run)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=("columns", "lectures", "all"), default="all")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--start-id", type=int, default=1)
    args = ap.parse_args()
    client = _client()
    if args.target in ("columns", "all"):
        run_columns(client, args.force, args.limit, args.start_id)
    if args.target in ("lectures", "all"):
        run_lectures(client, args.force, args.limit, args.start_id)


if __name__ == "__main__":
    main()
