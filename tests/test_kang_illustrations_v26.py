"""QA: dedicated lesson 14 narrative watercolor without replacing originals."""
from pathlib import Path
import base64
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "kang_blog" / "assets"


def test_lesson_14_scene_is_a_valid_webp_image():
    target = ASSETS / "lesson-scenes-v26" / "lesson-014.svg"
    svg = ElementTree.parse(target).getroot()
    assert svg.attrib["viewBox"] == "0 0 1600 900"
    assert svg.attrib["width"] == "1600"
    assert svg.attrib["height"] == "900"
    image = next(node for node in svg.iter() if node.tag.endswith("image"))
    href = image.attrib.get("href", "")
    assert href.startswith("data:image/webp;base64,")
    raw = base64.b64decode(href.split(",", 1)[1], validate=True)
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
    assert len(raw) > 200_000


def test_each_legacy_lecture_image_remains_available():
    for n in range(1, 61):
        assert (ASSETS / f"lesson-scenes-v22/lesson-{n:03d}.svg").is_file(), n
    for n in range(1, 12):
        assert (ASSETS / f"lesson-scenes-v23/lesson-{n:03d}.svg").is_file(), n
    assert (ASSETS / "lesson-scenes-v24/lesson-012.svg").is_file()
    assert (ASSETS / "lesson-scenes-v25/lesson-013.svg").is_file()


def test_14_uses_new_scene_on_main_and_standalone_pages():
    story = (ROOT / "kang_blog/lesson-story-v11.js").read_text(encoding="utf-8")
    loader = (ROOT / "kang_blog/story-photo-v14.js").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "id===14?" in story and "lesson-scenes-v26/lesson-014.svg" in story
    assert "id===14?" in loader and "previousIllustration" in loader
    assert "const preferred=id===14?illustrations(id):originals[id];" in loader
    assert "get:id=>id===14?illustrations(id)" in loader
    assert "int(item_id) == 14" in app
    assert "lesson-scenes-v22/lesson-" in app
