"""RE:LAND lecture 16 (v28): registered-letter narrative illustration QA."""
from __future__ import annotations

import base64
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "kang_blog" / "assets"
WEBP_SHA = "4d7f4ae002fc90c7ad5f19c845a23cb186f1632b64ce41641027ebcdf00b5764"


def test_lesson_016_dedicated_scene_decodes_and_matches_source() -> None:
    path = ASSETS / "lesson-scenes-v28" / "lesson-016.svg"
    svg = ET.parse(path).getroot()
    assert svg.tag.endswith("svg")
    assert (svg.attrib["width"], svg.attrib["height"]) == ("1600", "900")
    item = next(x for x in svg.iter() if x.tag.endswith("image"))
    uri = item.attrib.get("href", "")
    assert uri.startswith("data:image/webp;base64,")
    image_bytes = base64.b64decode(uri.split(",", 1)[1], validate=True)
    assert image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP"
    assert hashlib.sha256(image_bytes).hexdigest() == WEBP_SHA
    assert len(image_bytes) > 200_000


def test_legacy_artworks_stay_accessible() -> None:
    for n in range(1, 61):
        assert (ASSETS / "lesson-scenes-v22" / f"lesson-{n:03d}.svg").is_file()
        assert (ASSETS / "lesson-stories" / f"story-{n:03d}.svg").is_file()
    for n in range(1, 12):
        assert (ASSETS / "lesson-scenes-v23" / f"lesson-{n:03d}.svg").is_file()
    for version, n in [(24,12), (25,13), (26,14), (27,15)]:
        assert (ASSETS / f"lesson-scenes-v{version}" / f"lesson-{n:03d}.svg").is_file()


def test_lesson16_only_selects_the_new_artwork() -> None:
    story = (ROOT / "kang_blog" / "lesson-story-v11.js").read_text(encoding="utf-8")
    photo = (ROOT / "kang_blog" / "story-photo-v14.js").read_text(encoding="utf-8")
    server = (ROOT / "app.py").read_text(encoding="utf-8")
    html = (ROOT / "kang_blog" / "lesson-v6.html").read_text(encoding="utf-8")
    assert "id===16?" in story and "lesson-scenes-v28/lesson-016.svg" in story
    assert "id===16?" in photo and "previousIllustration" in photo
    assert "int(item_id) == 16" in server and "lesson-scenes-v28/lesson-016.svg" in server
    assert "story-photo-v14.js?v=20261118v31" in html
    assert "lesson-story-v11.js?v=20261118v31" in html
