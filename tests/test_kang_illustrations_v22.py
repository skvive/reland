"""RE:LAND Kang Class v22: 60 story-specific illustrations, add-only assets."""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW = ROOT / "kang_blog" / "assets" / "lesson-scenes-v22"
OLD = ROOT / "kang_blog" / "assets" / "lesson-stories"


def test_sixty_story_images_are_complete_and_unique() -> None:
    paths = sorted(NEW.glob("lesson-*.svg"))
    assert [path.name for path in paths] == [
        f"lesson-{lesson:03d}.svg" for lesson in range(1, 61)
    ]
    digests = []
    for path in paths:
        raw = path.read_bytes()
        root = ET.fromstring(raw)
        assert root.attrib["viewBox"] == "0 0 1600 900"
        assert root.attrib["width"] == "1600"
        assert root.attrib["height"] == "900"
        assert b"<script" not in raw.lower()
        assert b"xlink:href=" not in raw
        assert len(raw) > 3_000
        digests.append(hashlib.sha256(raw).digest())
    assert len(set(digests)) == 60


def test_legacy_60_scenes_are_preserved() -> None:
    for lesson in range(1, 61):
        assert (OLD / f"story-{lesson:03d}.svg").is_file()


def test_standalone_and_modern_lessons_use_new_scenes() -> None:
    story = (ROOT / "kang_blog" / "lesson-story-v11.js").read_text(encoding="utf-8")
    photo = (ROOT / "kang_blog" / "story-photo-v14.js").read_text(encoding="utf-8")
    server = (ROOT / "app.py").read_text(encoding="utf-8")
    html = (ROOT / "kang_blog" / "lesson-v6.html").read_text(encoding="utf-8")
    assert "lesson-scenes-v22/lesson-" in story
    assert "lesson-scenes-v22/lesson-" in photo
    assert "originalIllustration" in photo
    assert "lesson-scenes-v22/lesson-" in server
    assert "story-photo-v14.js?v=20261118v31" in html
    assert "lesson-story-v11.js?v=20261118v31" in html
