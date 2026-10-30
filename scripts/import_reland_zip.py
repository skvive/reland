#!/usr/bin/env python3
"""Extract RELAND v3.0.2 / Premium v4.1 ZIP packages into reland-deploy and refresh boards."""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPORT_ROOT = ROOT.parent / "_import" / "reland_packages"


def extract_zip(zip_path: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    # single top-level folder
    kids = [p for p in dest.iterdir() if p.name != "__MACOSX"]
    if len(kids) == 1 and kids[0].is_dir():
        return kids[0]
    return dest


def copy_tree(src: Path, dst: Path, pattern: str = "**/*") -> int:
    n = 0
    if not src.is_dir():
        return 0
    for f in src.glob(pattern):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        n += 1
    return n


def find_first(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        hit = next(root.rglob(name), None)
        if hit:
            return hit.parent if hit.is_file() else hit
    return None


def import_content_package(extracted: Path) -> dict:
    stats = {"json": 0, "images": 0}
    content_src = find_first(extracted, ("columns_120.json", "lectures_60.json", "qa_30.json"))
    if content_src:
        for rel in (
            "columns_120.json",
            "columns_manifest.csv",
            "law_references.json",
            "kang/lectures_60.json",
            "kang/qa_30.json",
            "kang/sources.json",
            "kang/manifest.csv",
        ):
            src = content_src / rel if (content_src / rel).exists() else extracted / "content" / rel
            if src.is_file():
                dst = ROOT / "content" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                stats["json"] += 1
    for folder_name, dest_rel in (
        ("columns", "static/assets/columns"),
        ("lessons", "kang_blog/assets/lessons"),
        ("ai_images", "static/assets/imported"),
    ):
        for candidate in (extracted / folder_name, extracted / "static" / folder_name, extracted / "assets" / folder_name):
            if candidate.is_dir():
                stats["images"] += copy_tree(candidate, ROOT / dest_rel)
    boards = next(extracted.rglob("boards_seed.json"), None) or next(extracted.rglob("boards/*.json"), None)
    if boards and boards.is_file():
        shutil.copy2(boards, ROOT / "content" / "boards_seed.json")
        stats["json"] += 1
    return stats


def import_design_package(extracted: Path) -> dict:
    stats = {"assets": 0}
    for sub in ("static", "design", "pages", "assets"):
        src = extracted / sub
        if src.is_dir():
            stats["assets"] += copy_tree(src, ROOT / "static" / "premium_v41")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description="Import RELAND ZIP content into reland-deploy")
    ap.add_argument("--v302", type=Path, help="RELAND_v3.0.2_...zip path")
    ap.add_argument("--design", type=Path, help="RELAND_Premium_Design_v4.1_...zip path")
    ap.add_argument("--apply-boards", action="store_true", help="Run board seed after import")
    args = ap.parse_args()
    if not args.v302 and not args.design:
        ap.error("Provide --v302 and/or --design")

    if args.v302:
        if not args.v302.is_file():
            raise SystemExit(f"ZIP not found: {args.v302}")
        out = extract_zip(args.v302, IMPORT_ROOT / "v302")
        print("v3.0.2 extracted to", out)
        print("content import:", import_content_package(out))

    if args.design:
        if not args.design.is_file():
            raise SystemExit(f"ZIP not found: {args.design}")
        out = extract_zip(args.design, IMPORT_ROOT / "v41")
        print("v4.1 extracted to", out)
        print("design import:", import_design_package(out))

    if args.apply_boards:
        import os
        import sys

        sys.path.insert(0, str(ROOT))
        os.chdir(ROOT)
        from app import db, init_db, utcnow  # noqa: WPS433
        from content_publisher import apply_published_content
        from db_engine import table_has_column

        init_db()
        with db() as c:
            result = apply_published_content(c, utcnow, table_has_column, force=True)
        print("boards:", result)


if __name__ == "__main__":
    main()
