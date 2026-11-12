"""Neighborhood builder regression tests: auth, proof, permissions, and safety."""
import time

import pytest
from fastapi.testclient import TestClient

import app as site
import community_builder


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(site, "DB_PATH", tmp_path / "community-builder-qa.sqlite")
    monkeypatch.setattr(site, "DEMO_MODE", True)
    site.RATE.clear()
    site.init_db()
    with site.db() as con:
        con.execute("UPDATE settings SET value=? WHERE key='news_last_attempt'", (str(time.time()),))
    with TestClient(site.app) as c:
        yield c


def login(c):
    response = c.post("/api/auth/demo")
    assert response.status_code == 200
    return response.json()["user"]


def make_community(c):
    result = c.post("/api/communities", json={
        "name": "시흥4동 주민사랑방",
        "region": "서울",
        "description": "우리 동네 소식과 서로의 질문을 나눕니다.",
    })
    assert result.status_code == 201, result.text
    return result.json()["id"]


def test_builder_page_and_auth_gate(client):
    page = client.get("/community/builder")
    assert page.status_code == 200
    assert "무료 템플릿" in page.text
    assert 'href="https://www.blogger.com/"' in page.text
    assert client.post("/api/communities/1/blog/claim", json={
        "blog_url": "https://localtown.blogspot.com/"
    }).status_code == 401
    assert client.put("/api/communities/1/band", json={"band_url": "https://band.us/band/123"}).status_code == 401


def test_owner_claim_verify_updates_blog(monkeypatch, client):
    login(client)
    cid = make_community(client)
    claim = client.post(f"/api/communities/{cid}/blog/claim", json={
        "blog_url": "https://localtown.blogspot.com/"
    })
    assert claim.status_code == 200, claim.text
    code = claim.json()["verification_code"]
    assert code.startswith("RELAND-")
    wrong = client.post(f"/api/communities/{cid}/blog/verify", json={
        "verification_code": "RELAND-THIS-IS-NOT-VALID"
    })
    assert wrong.status_code == 422
    class FakeFeed:
        status_code = 200
        content = b"{}"
        def json(self):
            return {"feed": {"entry": [{"title": {"$t": "확인 코드 " + code}}]}}
    def fake_get(url, **kwargs):
        assert url == "https://localtown.blogspot.com/feeds/posts/default?alt=json&max-results=25"
        assert kwargs.get("follow_redirects") is False
        return FakeFeed()
    monkeypatch.setattr(community_builder.httpx, "get", fake_get)
    verified = client.post(f"/api/communities/{cid}/blog/verify", json={
        "verification_code": code
    })
    assert verified.status_code == 200, verified.text
    assert verified.json()["verified_blog_owner"] is True
    detail = client.get(f"/api/communities/{cid}").json()["item"]
    assert detail["blog_verified"] == 1
    assert detail["blog_url"] == "https://localtown.blogspot.com/"
    with site.db() as con:
        assert not con.execute(
            "SELECT 1 FROM community_blog_claims WHERE community_id=?", (cid,)
        ).fetchone()
    second = client.post("/api/communities", json={
        "name":"또다른 사랑방","description":"여기에도 등록해 봅니다.","region":"서울",
    })
    sid = second.json()["id"]
    collision = client.post(f"/api/communities/{sid}/blog/claim", json={
        "blog_url": "https://localtown.blogspot.com/"
    })
    assert collision.status_code == 409


def test_proof_not_visible_cannot_verify(monkeypatch, client):
    login(client)
    cid = make_community(client)
    claim=client.post(f"/api/communities/{cid}/blog/claim",json={
        "blog_url":"https://no-proof.blogspot.com/"
    })
    code=claim.json()["verification_code"]
    monkeypatch.setattr(community_builder, "_proof_is_visible", lambda url, code: False)
    r=client.post(f"/api/communities/{cid}/blog/verify",json={"verification_code":code})
    assert r.status_code == 422
    assert client.get(f"/api/communities/{cid}").json()["item"]["blog_verified"] == 0


def test_band_allowed_and_malicious_rejected(client):
    login(client)
    cid=make_community(client)
    r=client.put(f"/api/communities/{cid}/band",json={"band_url":"https://band.us/band/123456"})
    assert r.status_code == 200
    assert r.json()["band_url"] == "https://band.us/band/123456"
    detail=client.get(f"/api/communities/{cid}").json()["item"]
    assert detail["band_url"] == "https://band.us/band/123456"
    for bad in ["http://band.us/band/123", "https://band.us.evil.example/band/123",
                "https://localhost/private", "https://band.us//evil"]:
        r=client.put(f"/api/communities/{cid}/band",json={"band_url":bad})
        assert r.status_code == 422, bad


def test_notice_only_operator_and_pins_to_top(client):
    me=login(client)
    cid=make_community(client)
    note=client.post("/api/posts",json={
        "community_id":cid,"kind":"notice","title":"이번 주 주민 소식 안내",
        "body":"동네 주민 여러분, 이번 주 새로운 소식을 전합니다.",
    })
    assert note.status_code == 201, note.text
    other=client.post("/api/posts",json={
        "community_id":cid,"kind":"discussion","title":"동네 주민 의견을 모읍니다",
        "body":"새로운 의견을 함께 나누고 싶습니다.",
    })
    assert other.status_code == 201, other.text
    feed=client.get(f"/api/posts?community_id={cid}").json()["items"]
    assert feed[0]["kind"] == "notice"
    with site.db() as con:
        other_user=con.execute("INSERT INTO users (google_sub,nickname,created_at) VALUES(?,?,?)",
                               ("other-local-owner","다른 운영자",site.utcnow())).lastrowid
        con.execute("UPDATE communities SET owner_id=? WHERE id=?", (other_user,cid))
    unauthorized=client.post("/api/posts",json={
        "community_id":cid,"kind":"notice","title":"허가되지 않은 운영자 공지",
        "body":"운영자가 아닌 사람이 올리는 글입니다.",
    })
    assert unauthorized.status_code == 403
    discussion=client.post("/api/posts",json={
        "community_id":cid,"kind":"discussion","title":"동네에서 함께 이야기 나누기",
        "body":"운영자가 아닌 주민도 동네 이야기를 적을 수 있습니다.",
    })
    assert discussion.status_code == 201
    answer=client.post(f"/api/posts/{note.json()['id']}/comments",json={
        "body":"소식 잘 봤습니다. 감사합니다."
    })
    assert answer.status_code == 201


def test_blog_change_revokes_prior_proof(client, monkeypatch):
    login(client)
    cid=make_community(client)
    with site.db() as con:
        con.execute("UPDATE communities SET blog_url=?,blog_verified=1 WHERE id=?",
                    ("https://town1.blogspot.com/",cid))
    changed=client.put(f"/api/communities/{cid}/blog",json={
        "blog_url":"https://town2.blogspot.com/"
    })
    assert changed.status_code == 200
    detail=client.get(f"/api/communities/{cid}").json()["item"]
    assert detail["blog_verified"] == 0


def test_repeated_database_migration_does_not_destroy_records(client):
    login(client)
    cid=make_community(client)
    site.init_db()
    assert client.get(f"/api/communities/{cid}").status_code == 200
