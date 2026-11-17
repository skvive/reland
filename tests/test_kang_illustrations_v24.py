"""RE:LAND lesson 12 cinematic replacement v24 – preserve every prior asset."""
from __future__ import annotations
import base64
from pathlib import Path
from xml.etree import ElementTree
ROOT=Path(__file__).resolve().parents[1]
def test_cinematic_12_art_is_decodable():
    image=ROOT/"kang_blog/assets/lesson-scenes-v24/lesson-012.svg"
    root=ElementTree.parse(image).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["width"]=="1600" and root.attrib["height"]=="900"
    obj=next(x for x in root.iter() if x.tag.endswith("image"))
    uri=obj.attrib.get("href","")
    assert uri.startswith("data:image/webp;base64,")
    payload=base64.b64decode(uri.split(",",1)[1], validate=True)
    assert payload[:4]==b"RIFF" and payload[8:12]==b"WEBP"
    assert len(payload)>100_000
def test_previous_sixty_assets_retained():
    for i in range(1,61):
        assert (ROOT/f"kang_blog/assets/lesson-scenes-v22/lesson-{i:03d}.svg").is_file()
    for i in range(1,12):
        assert (ROOT/f"kang_blog/assets/lesson-scenes-v23/lesson-{i:03d}.svg").is_file()
def test_story_route_12_only_and_retains_13_on_v22():
    js=(ROOT/"kang_blog/lesson-story-v11.js").read_text(encoding="utf8")
    photo=(ROOT/"kang_blog/story-photo-v14.js").read_text(encoding="utf8")
    app=(ROOT/"app.py").read_text(encoding="utf8")
    assert "id===12?" in js and "lesson-scenes-v24/lesson-012.svg" in js
    assert "id===12?" in photo and "previousIllustration" in photo
    assert "int(item_id) == 12" in app
    assert "lesson-scenes-v22/lesson-" in app
