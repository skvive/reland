"""Theme portal regression tests: editorial hierarchy and backward compatibility."""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as site


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(site, "DB_PATH", tmp_path / "boards.sqlite")
    monkeypatch.setattr(site, "DEMO_MODE", True)
    site.RATE.clear()
    site.init_db()
    with site.db() as c:
        c.execute("UPDATE settings SET value=? WHERE key='news_last_attempt'", (str(time.time()),))
    with TestClient(site.app) as browser:
        yield browser


def test_nine_public_theme_boards(client):
    r = client.get("/api/boards")
    assert r.status_code == 200, r.text
    boards = r.json()["items"]
    assert len(boards) == 9
    assert len({b["slug"] for b in boards}) == 9
    assert len({b["image_index"] for b in boards}) == 9
    assert all(b["is_official_theme_board"] for b in boards)
    assert "우리동네 소식판" in [b["title"] for b in boards]
    assert "RE:LAND 법률지식" in [b["title"] for b in boards]
    assert client.get("/board/seoul").status_code == 200
    assert client.get("/board/does-not-exist").status_code == 404
    assert client.get("/api/boards/does-not-exist").status_code == 404


def test_theme_boards_are_not_in_local_community_list(client):
    themes = client.get("/api/boards").json()["items"]
    locals_ = client.get("/api/communities").json()["items"]
    assert not any(c["id"] in {b["id"] for b in themes} for c in locals_)
    assert all(not c["is_theme_board"] for c in locals_)
    assert any(x["name"] == "서울 정비사업 이웃모임" for x in locals_)
    seoul = client.get("/api/boards/seoul").json()["item"]
    assert any(c["name"] == "서울 정비사업 이웃모임" for c in seoul["communities"])


def test_create_local_community_under_selected_board(client):
    assert client.post("/api/auth/demo").status_code == 200
    data = {"name": "역삼동 우리 이웃 모임", "description": "역삼동의 매일매일 소식을 공유합니다",
            "region": "서울", "theme_slug": "neighborhood"}
    created = client.post("/api/communities", json=data)
    assert created.status_code == 201
    cid = created.json()["id"]
    detail = client.get(f"/api/communities/{cid}").json()["item"]
    assert detail["board_slug"] == "neighborhood"
    local = client.get("/api/boards/neighborhood").json()["item"]["communities"]
    assert any(x["id"] == cid for x in local)
    other = client.get("/api/boards/operations").json()["item"]["communities"]
    assert not any(x["id"] == cid for x in other)
    bad = client.post("/api/communities", json={**data, "theme_slug": "invalid-theme"})
    assert bad.status_code == 422


def test_parent_board_post_comment_and_notice_permissions(client):
    assert client.post("/api/auth/demo").status_code == 200
    b = client.get("/api/boards/seoul").json()["item"]
    normal = client.post("/api/posts",json={"community_id":b["id"],"kind":"discussion",
        "title":"동네 주민들이 궁금한 내용", "body":"이번 주 주민들이 알고 싶은 내용을 정리합니다."})
    assert normal.status_code == 201
    post_id = normal.json()["id"]
    reply = client.post(f"/api/posts/{post_id}/comments",json={"body":"함께 나누겠습니다."})
    assert reply.status_code == 201
    assert client.get(f"/api/posts/{post_id}").json()["comments"][0]["body"] == "함께 나누겠습니다."
    notice = client.post("/api/posts",json={"community_id":b["id"],"kind":"notice",
        "title":"운영자를 사칭하는 공지", "body":"일반 회원이 공지를 쓰려고 시도합니다."})
    assert notice.status_code == 403


def test_board_filtered_local_group_and_migration_idempotency(client):
    a = client.get("/api/boards/seoul?q=서울&region=서울").json()["item"]["communities"]
    assert any("서울" in x["name"] for x in a)
    assert client.get("/api/boards/seoul?region=부산").json()["item"]["communities"] == []
    with site.db() as c:
        before = c.execute("SELECT count(*) FROM communities WHERE is_theme_board=1").fetchone()[0]
    site.init_db()
    with site.db() as c:
        after = c.execute("SELECT count(*) FROM communities WHERE is_theme_board=1").fetchone()[0]
    assert before == after == 9
