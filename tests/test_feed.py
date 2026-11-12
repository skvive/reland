"""RE:LAND RSS endpoint and content integrity checks."""
from xml.etree import ElementTree as ET

from fastapi.testclient import TestClient
from app import app


def test_feed_returns_valid_rss2_with_published_lessons():
    response = TestClient(app).get("/feed.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/rss+xml")
    document = ET.fromstring(response.content)
    assert document.tag == "rss"
    assert document.get("version") == "2.0"
    channel = document.find("channel")
    assert channel is not None
    assert channel.findtext("title") == "RE:LAND 리랜드 | 재개발 강실장 클래스"
    self_link = channel.find("{http://www.w3.org/2005/Atom}link")
    assert self_link is not None
    assert self_link.attrib["href"] == "https://reland.lexid.site/feed.xml"
    items = channel.findall("item")
    assert len(items) == 60
    links = [item.findtext("link") for item in items]
    assert len(links) == len(set(links))
    assert all(link.startswith("https://reland.lexid.site/kang/lectures/lesson-") and link.endswith(".html") for link in links)
    assert all(item.findtext("title") and item.findtext("description") for item in items)
    assert all("감수 전" in item.findtext("description", "") for item in items)
    assert not any("/column/" in link or "/api/" in link for link in links)


def test_feed_is_discoverable_on_public_home_pages():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for path in ("static/index.html", "kang_blog/index.html"):
        content = (root / path).read_text(encoding="utf-8")
        assert 'type="application/rss+xml"' in content
        assert 'href="https://reland.lexid.site/feed.xml"' in content
