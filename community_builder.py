"""RE:LAND neighborhood Blogger onboarding.

Blogger API v3 cannot create a blog; this module verifies an existing public
Blogspot blog using a one-time proof posted by its operator. No OAuth tokens
or Blogger passwords are collected.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field


class BlogClaimRequest(BaseModel):
    blog_url: str = Field(min_length=24, max_length=250)


class BlogVerifyRequest(BaseModel):
    verification_code: str = Field(min_length=12, max_length=80)


class CommunityBandRequest(BaseModel):
    band_url: str = Field(default="", max_length=250)


def init_community_builder_schema(c, has_column):
    """Additive, re-runnable SQLite/Neon migration; never deletes existing data."""
    if not has_column(c, "communities", "blog_verified"):
        c.execute("ALTER TABLE communities ADD COLUMN blog_verified INTEGER NOT NULL DEFAULT 0")
    if not has_column(c, "communities", "band_url"):
        c.execute("ALTER TABLE communities ADD COLUMN band_url TEXT NOT NULL DEFAULT ''")
    c.execute("""CREATE TABLE IF NOT EXISTS community_blog_claims (
        community_id INTEGER PRIMARY KEY REFERENCES communities(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        blog_url TEXT NOT NULL,
        token_hash TEXT NOT NULL,
        expires_at BIGINT NOT NULL,
        created_at TEXT NOT NULL
    )""")


def normalize_band_url(value):
    if not value.strip():
        return ""
    raw = urlsplit(value.strip())
    if (raw.scheme != "https" or raw.hostname not in ("band.us", "www.band.us")
            or raw.port is not None or raw.username or raw.password
            or not re.fullmatch(r"/[A-Za-z0-9@/_-]{1,140}", raw.path)
            or "//" in raw.path):
        raise HTTPException(422, "band.us의 HTTPS 밴드 초대/커뮤니티 주소만 등록할 수 있습니다.")
    return "https://band.us" + raw.path.rstrip("/")


def _validate_public_blog(value, validate_blog):
    normalized = validate_blog(value)
    host = urlsplit(normalized).hostname or ""
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.blogspot\.com", host):
        raise HTTPException(422, "정상적인 blogspot.com 공개 블로그 주소를 입력하세요.")
    return normalized


def _proof_is_visible(blog_url, verification_code):
    """Only read the Google-owned Blogspot host; do not follow redirects."""
    url = blog_url + "feeds/posts/default?alt=json&max-results=25"
    try:
        response = httpx.get(url, timeout=9, follow_redirects=False,
                             headers={"Accept": "application/json"})
        if response.status_code != 200:
            return False
        if len(response.content) > 750_000:
            return False
        data = response.json()
        entries = data.get("feed", {}).get("entry", [])
        for entry in entries:
            title = entry.get("title", {}).get("$t", "")
            body = entry.get("content", entry.get("summary", {})).get("$t", "")
            if verification_code in title or verification_code in body:
                return True
    except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError):
        return False
    return False


def register_community_builder(app, root, db, require_user, validate_blog, throttle, utcnow):
    @app.get("/community/builder", include_in_schema=False)
    def community_builder_page():
        return FileResponse(root / "static" / "community-builder.html", media_type="text/html")

    def get_owner(c, community_id, user):
        row = c.execute("SELECT id,owner_id,blog_url,blog_verified FROM communities WHERE id=?",
                        (community_id,)).fetchone()
        if not row:
            raise HTTPException(404, "존재하지 않는 동네사랑방입니다.")
        if row["owner_id"] != user["id"] and user.get("role") != "admin":
            raise HTTPException(403, "이 사랑방 운영자만 설정할 수 있습니다.")
        return row

    @app.post("/api/communities/{community_id}/blog/claim")
    def begin_blog_claim(community_id: int, data: BlogClaimRequest, request: Request):
        user = require_user(request)
        throttle(request, "blog-claim", 6, 3600)
        url = _validate_public_blog(data.blog_url, validate_blog)
        secret = "RELAND-" + secrets.token_hex(12).upper()
        with db() as c:
            get_owner(c, community_id, user)
            prior = c.execute(
                "SELECT id FROM communities WHERE blog_url=? AND blog_verified=1 AND id<>?",
                (url, community_id)).fetchone()
            if prior:
                raise HTTPException(409, "이미 다른 사랑방에서 소유 확인된 블로그입니다.")
            c.execute("""INSERT INTO community_blog_claims
                (community_id,user_id,blog_url,token_hash,expires_at,created_at)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(community_id) DO UPDATE SET
                user_id=excluded.user_id, blog_url=excluded.blog_url,
                token_hash=excluded.token_hash, expires_at=excluded.expires_at,
                created_at=excluded.created_at""",
                (community_id, user["id"], url, hashlib.sha256(secret.encode()).hexdigest(),
                 int(time.time()) + 86400, utcnow()))
        return {
            "verification_code": secret, "blog_url": url,
            "instruction": "Blogger에 공개 게시글을 만들고 제목에 확인 코드를 붙여 게시하세요. 공개 피드에 표시되어야 합니다.",
            "expires_in_seconds": 86400,
        }

    @app.post("/api/communities/{community_id}/blog/verify")
    def verify_blog_claim(community_id: int, data: BlogVerifyRequest, request: Request):
        user = require_user(request)
        throttle(request, "blog-verify", 8, 3600)
        code = data.verification_code.strip()
        with db() as c:
            get_owner(c, community_id, user)
            claim = c.execute("SELECT * FROM community_blog_claims WHERE community_id=?",
                              (community_id,)).fetchone()
            if not claim or claim["user_id"] != user["id"]:
                raise HTTPException(404, "먼저 블로그 연결 확인 코드를 발급받으세요.")
            if claim["expires_at"] < int(time.time()):
                raise HTTPException(410, "확인 코드가 만료되었습니다. 다시 발급받으세요.")
            if not hmac.compare_digest(claim["token_hash"], hashlib.sha256(code.encode()).hexdigest()):
                raise HTTPException(422, "확인 코드가 일치하지 않습니다.")
            target = claim["blog_url"]
        if not _proof_is_visible(target, code):
            raise HTTPException(422, "공개 Blogger 피드에서 확인 코드를 찾지 못했습니다. 게시물 공개와 피드 설정을 확인하세요.")
        with db() as c:
            get_owner(c, community_id, user)
            current = c.execute("SELECT token_hash,blog_url FROM community_blog_claims WHERE community_id=?",
                                (community_id,)).fetchone()
            if not current or current["blog_url"] != target or not hmac.compare_digest(current["token_hash"], hashlib.sha256(code.encode()).hexdigest()):
                raise HTTPException(409, "확인 정보가 바뀌었습니다. 다시 시도하세요.")
            collision = c.execute(
                "SELECT id FROM communities WHERE blog_url=? AND blog_verified=1 AND id<>?",
                (target, community_id)).fetchone()
            if collision:
                raise HTTPException(409, "이미 다른 사랑방에서 등록한 블로그입니다.")
            c.execute("UPDATE communities SET blog_url=?,blog_verified=1 WHERE id=?",
                      (target, community_id))
            c.execute("DELETE FROM community_blog_claims WHERE community_id=?", (community_id,))
        return {"ok": True, "blog_url": target, "verified_blog_owner": True}

    @app.put("/api/communities/{community_id}/band")
    def save_community_band(community_id: int, data: CommunityBandRequest, request: Request):
        user = require_user(request)
        band_url = normalize_band_url(data.band_url)
        with db() as c:
            get_owner(c, community_id, user)
            c.execute("UPDATE communities SET band_url=? WHERE id=?", (band_url, community_id))
        return {"ok": True, "band_url": band_url}
