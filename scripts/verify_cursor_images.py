from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
rows = json.loads((root / "content/columns_120.json").read_text(encoding="utf-8"))
c = sum(1 for x in rows if "Cursor AI" in x.get("image_alt", ""))
missing = [
    x["id"]
    for x in rows
    if not (root / f"static/assets/columns/column-{x['id']:03d}.webp").exists()
]
print("columns cursor alt", c, "/", len(rows), "missing webp", len(missing))
lec = json.loads((root / "content/kang/lectures_60.json").read_text(encoding="utf-8"))
lc = sum(1 for x in lec if "Cursor AI" in x.get("cover_alt", ""))
lm = [
    x["id"]
    for x in lec
    if not (root / f"kang_blog/assets/lessons/lesson-{x['id']:03d}.webp").exists()
]
print("lectures cursor alt", lc, "/", len(lec), "missing webp", len(lm))
