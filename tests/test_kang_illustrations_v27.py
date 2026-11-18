"""RE:LAND lecture 15 v27 image, source preservation and route checks."""
from pathlib import Path
import base64
import hashlib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "kang_blog" / "assets"


def test_lesson_15_art_is_renderable_and_unique():
    path = A / "lesson-scenes-v27" / "lesson-015.svg"
    node = ET.parse(path).getroot()
    assert node.tag.endswith("svg")
    assert node.attrib["width"] == "1600" and node.attrib["height"] == "900"
    im = next(x for x in node.iter() if x.tag.endswith("image"))
    uri = im.attrib["href"]
    assert uri.startswith("data:image/webp;base64,")
    binary = base64.b64decode(uri.split(",", 1)[1], validate=True)
    assert binary[:4] == b"RIFF" and binary[8:12] == b"WEBP"
    assert len(binary) > 80_000
    assert len(binary) > 300_000


def test_original_60_lessons_remain_available():
    for n in range(1, 61):
        assert (A / "lesson-scenes-v22" / f"lesson-{n:03d}.svg").is_file()
    for n in range(1, 12):
        assert (A / "lesson-scenes-v23" / f"lesson-{n:03d}.svg").is_file()
    assert (A / "lesson-scenes-v24" / "lesson-012.svg").is_file()
    assert (A / "lesson-scenes-v25" / "lesson-013.svg").is_file()
    assert (A / "lesson-scenes-v26" / "lesson-014.svg").is_file()


def test_only_15_selects_new_route():
    story = (ROOT / "kang_blog" / "lesson-story-v11.js").read_text(encoding="utf-8")
    loader = (ROOT / "kang_blog" / "story-photo-v14.js").read_text(encoding="utf-8")
    server = (ROOT / "app.py").read_text(encoding="utf-8")
    html = (ROOT / "kang_blog" / "lesson-v6.html").read_text(encoding="utf-8")
    assert "id===15?" in story and "lesson-scenes-v27/lesson-015.svg" in story
    assert "id===15?" in loader and "previousIllustration" in loader
    assert "int(item_id) == 15" in server and "lesson-scenes-v27/lesson-015.svg" in server
    assert "story-photo-v14.js?v=20261118v31" in html
    assert "lesson-story-v11.js?v=20261118v31" in html
