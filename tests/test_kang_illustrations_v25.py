"""RE:LAND v25 art QA: single-scene chapter 13, no changes to 1-12/14-60."""
from pathlib import Path
import base64
from xml.etree import ElementTree
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"kang_blog/assets"

def test_13_new_scene_renders_and_is_embedded():
    file=ASSETS/"lesson-scenes-v25/lesson-013.svg"
    root=ElementTree.parse(file).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["width"]=="1600" and root.attrib["height"]=="900"
    graphic=next(x for x in root.iter() if x.tag.endswith("image"))
    uri=graphic.attrib["href"]
    assert uri.startswith("data:image/webp;base64,")
    b=base64.b64decode(uri.split(",",1)[1],validate=True)
    assert b[:4]==b"RIFF" and b[8:12]==b"WEBP"
    assert len(b)>100_000

def test_originals_not_replaced():
    for i in range(1,61):
        assert (ASSETS/f"lesson-scenes-v22/lesson-{i:03d}.svg").is_file()
        assert (ASSETS/f"lesson-stories/story-{i:03d}.svg").is_file()
    for i in range(1,12):
        assert (ASSETS/f"lesson-scenes-v23/lesson-{i:03d}.svg").is_file()
    assert (ASSETS/"lesson-scenes-v24/lesson-012.svg").is_file()

def test_13_only_and_fallback_routing():
    js=(ROOT/"kang_blog/lesson-story-v11.js").read_text(encoding="utf8")
    loader=(ROOT/"kang_blog/story-photo-v14.js").read_text(encoding="utf8")
    server=(ROOT/"app.py").read_text(encoding="utf8")
    assert "id===13?" in js and "lesson-scenes-v25/lesson-013.svg" in js
    assert "id===13?" in loader and "previousIllustration" in loader
    assert "int(item_id) == 13" in server
    assert "lesson-scenes-v22/lesson-" in server
    assert "lesson-scenes-v24/lesson-" in server
