"""RE:LAND 2026-11-15: source-preserving v23 narrative illustrations for lessons 01-11."""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "kang_blog" / "assets"


def test_v23_assets_are_unique_and_decode_as_webp() -> None:
    hashes: set[str] = set()
    for n in range(1, 12):
        asset = ASSET / "lesson-scenes-v23" / f"lesson-{n:03d}.svg"
        assert asset.is_file(), n
        root = ElementTree.parse(asset).getroot()
        assert root.tag.endswith("svg")
        assert (root.attrib["width"], root.attrib["height"]) == ("1600", "900")
        img = next(elem for elem in root.iter() if elem.tag.endswith("image"))
        href = img.attrib.get("href", "")
        assert href.startswith("data:image/webp;base64,"), n
        data = base64.b64decode(href.split(",", 1)[1], validate=True)
        assert data[:4] == b"RIFF" and data[8:12] == b"WEBP", n
        assert len(data) > 80_000, n
        hashes.add(hashlib.sha256(data).hexdigest())
    assert len(hashes) == 11, "duplicate realistic scenes detected"


def test_all_legacy_scenes_remain_unmodified_in_place() -> None:
    for n in range(1, 61):
        assert (ASSET / "lesson-scenes-v22" / f"lesson-{n:03d}.svg").is_file(), n
        assert (ASSET / "lesson-stories" / f"story-{n:03d}.svg").is_file(), n


def test_lecture_path_selection_and_fallbacks() -> None:
    story = (ROOT / "kang_blog" / "lesson-story-v11.js").read_text(encoding="utf-8")
    photo = (ROOT / "kang_blog" / "story-photo-v14.js").read_text(encoding="utf-8")
    server = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "id<=11?" in story
    assert "lesson-scenes-v23/lesson-" in story
    assert "id<=11?" in photo and "previousIllustration" in photo
    assert "int(item_id) <= 11" in server
    assert "lesson-scenes-v22/lesson-" in server
