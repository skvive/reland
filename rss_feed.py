"""RE:LAND RSS 2.0 feed for publicly readable Kang educational lessons.

This feed intentionally excludes unreviewed legal-journal columns, private posts,
and administrative data. Source titles and summaries come from the same JSON
that serves the live lectures; no synthetic publication dates are assigned.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = "https://reland.lexid.site"
ATOM_NS = "http://www.w3.org/2005/Atom"
CONTENT_FILE = Path(__file__).resolve().parent / "content" / "kang" / "lectures_60.json"


def build_rss() -> bytes:
    lessons = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))
    root = ET.Element("rss", {"version": "2.0", "xmlns:atom": ATOM_NS})
    channel = ET.SubElement(root, "channel")

    def tag(parent, name: str, value: str):
        ET.SubElement(parent, name).text = str(value)

    tag(channel, "title", "RE:LAND 리랜드 | 재개발 강실장 클래스")
    tag(channel, "link", f"{BASE}/kang/")
    tag(channel, "description", "재개발·재건축 절차와 법률상식을 배우는 강실장 교육 강의. 개별 법률자문이 아닌 전문가 감수 전 교육자료입니다.")
    tag(channel, "language", "ko-KR")
    tag(channel, "lastBuildDate", format_datetime(datetime.now(timezone.utc), usegmt=True))
    tag(channel, "generator", "RE:LAND RSS")
    ET.SubElement(channel, f"{{{ATOM_NS}}}link", {
        "href": f"{BASE}/feed.xml",
        "rel": "self",
        "type": "application/rss+xml",
    })

    seen: set[str] = set()
    for lesson in sorted(lessons, key=lambda row: int(row["id"]), reverse=True):
        slug = str(lesson.get("slug", ""))
        if not re.fullmatch(r"lesson-[0-9]{3}", slug) or slug in seen:
            continue
        if not (CONTENT_FILE.parent.parent.parent / "kang_blog" / "lectures" / f"{slug}.html").is_file():
            continue
        seen.add(slug)
        link = f"{BASE}/kang/lectures/{slug}.html"
        item = ET.SubElement(channel, "item")
        tag(item, "title", lesson["title"])
        tag(item, "link", link)
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = link
        tag(item, "description", f"{lesson.get('summary', '')} (교육용 편집 초안 · 법률전문가 개별 감수 전)")
        if lesson.get("category"):
            tag(item, "category", lesson["category"])

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
