"""Print GenerateImage prompts for columns / Kang lectures (for agent batch runs)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = (
    "RE:LAND Korean urban renewal law editorial concept art. "
    "Palette: sage green, deep teal, warm cream accent. "
    "Premium legal journal photography, soft cinematic light, shallow depth. "
    "Fictional concept only - not a real construction site, law firm, or official plan. "
    "No text, no logos, no Korean characters, no watermarks. 16:9 horizontal."
)

SCENE = {
    "조합설립 절차": "official consent forms and planning documents on a desk, abstract apartment silhouettes",
    "총회와 의결": "cooperative meeting room, agenda folders and voting papers",
    "분양신청": "housing application documents, floor plan blueprints, model units concept",
    "관리처분계획": "urban renewal master plan boards, cost allocation abstract charts",
    "정보공개": "public records archive, transparent filing and digital portal screens",
    "이전고시·등기": "property transfer documents, registry metaphor, keys on desk",
    "주민 참여와 분쟁 예방": "community workshop table, residents discussing plans calmly",
    "상담 준비 체크리스트": "organized checklist binder, calm consultation desk",
    "등기·서류 실무": "notary desk with sealed documents and property ledgers",
    "행정 인허가·신청": "government permit counter, application stacks and stamps",
    "전문가 광고·홍보": "ethical professional brochure layout without faces",
    "지역별 공개자료 검증": "city hall notice board, regional map pins, magnifying glass",
}


def column_prompt(row: dict) -> str:
    scene = SCENE.get(row["category"], "urban renewal law education desk scene")
    return (
        f"{STYLE} Topic: {row['category']}. Focus: {row['angle']}. "
        f"Scene: {scene}. Unique variation #{row['id']}."
    )


def lecture_prompt(row: dict) -> str:
    return (
        f"{STYLE} Korean redevelopment law classroom thumbnail. "
        f"Category: {row['category']}. Lesson: {row['title']}. "
        f"Context: {row['summary'][:100]}. Unique variation #{row['id']}."
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=("columns", "lectures"), required=True)
    ap.add_argument("--from-id", type=int, default=1)
    ap.add_argument("--to-id", type=int, default=120)
    args = ap.parse_args()
    if args.target == "columns":
        rows = json.loads((ROOT / "content" / "columns_120.json").read_text(encoding="utf-8"))
        default_to = 120
    else:
        rows = json.loads((ROOT / "content" / "kang" / "lectures_60.json").read_text(encoding="utf-8"))
        default_to = 60
    hi = args.to_id if args.to_id else default_to
    for row in rows:
        rid = int(row["id"])
        if rid < args.from_id or rid > hi:
            continue
        fn = f"column-{rid:03d}" if args.target == "columns" else f"lesson-{rid:03d}"
        prompt = column_prompt(row) if args.target == "columns" else lecture_prompt(row)
        print(f"FILE={fn}\nPROMPT={prompt}\n---")


if __name__ == "__main__":
    main()
