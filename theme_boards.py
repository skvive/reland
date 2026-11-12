"""RE:LAND branded theme boards: nine curated portals, using existing communities/posts.

One master grid asset carries nine distinct photographs. Each top-level board is
RE:LAND-managed, while local communities and linked Blogger sites remain owned
by their respective operators. Existing community rows are preserved.
"""
from __future__ import annotations
from fastapi import HTTPException
from fastapi.responses import FileResponse

THEMES = (
    ("neighborhood", "우리동네 소식판", "Neighborhood", "이웃이 직접 전하는 생활 소식·모임·동네 알림", "우리동네 Blogger 정보방"),
    ("operations", "동네모임 운영판", "Community Management", "운영자 공지, 모임 안내, 지역 커뮤니티 운영 노하우", "모임 관리자 테스트"),
    ("moving", "입주·이주 정보판", "Moving & Housing", "입주 준비, 이주 일정, 생활 편의시설 정보를 나눕니다", "수도권 입주·이주 정보방"),
    ("busan", "부산·영남 동네판", "Busan & Yeongnam", "부산과 영남권 이웃들의 생활 소식과 지역 변화", "부산 우리동네 변화모임"),
    ("seoul", "서울 정비사업판", "Seoul Redevelopment", "서울의 재개발·재건축 현황을 주민 눈높이로 살펴봅니다", "서울 정비사업 이웃모임"),
    ("qa", "재개발 질문·답변판", "Questions & Answers", "사업 단계부터 서류까지 주민들이 질문하고 답합니다", "강실장 Q&A TOP30"),
    ("academy", "재개발 강실장 클래스", "Learning & Class", "처음 시작하는 이웃을 위한 쉬운 재개발 교육", "재개발 강실장 클래스"),
    ("law", "RE:LAND 법률지식", "Law & Policy", "도시정비법·조합 운영·고시 원문을 함께 확인합니다", "RE:LAND 법률지식"),
    ("chungcheong", "청주·충청 동네판", "Chungcheong Neighbors", "청주와 충청권 주민이 모여 지역 이야기를 나눕니다", "청주 정보방"),
)
THEME_BY_SLUG = {entry[0]: entry for entry in THEMES}


def init_theme_board_schema(c, has_column, utcnow):
    if not has_column(c, "communities", "board_slug"):
        c.execute("ALTER TABLE communities ADD COLUMN board_slug TEXT NOT NULL DEFAULT ''")
    if not has_column(c, "communities", "is_theme_board"):
        c.execute("ALTER TABLE communities ADD COLUMN is_theme_board INTEGER NOT NULL DEFAULT 0")
    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_reland_theme_board_slug
                  ON communities(board_slug) WHERE is_theme_board=1""")
    # Assign legacy community rows to their matching portal, never rename them.
    # Preserve a previously assigned topic on re-running this additive migration.
    for slug, title, english, description, old_name in THEMES:
        c.execute(
            "UPDATE communities SET board_slug=? WHERE name=? AND is_theme_board=0 AND board_slug=''",
            (slug, old_name))
        exists = c.execute(
            "SELECT id FROM communities WHERE is_theme_board=1 AND board_slug=?",
            (slug,)).fetchone()
        if not exists:
            c.execute("""INSERT INTO communities
                         (name,region,description,owner_id,official,created_at,board_slug,is_theme_board)
                         VALUES (?,?,?,NULL,0,?,?,1)""",
                      ("RE:LAND " + title, "전국", description, utcnow(), slug))


def public_board(c, slug):
    if slug not in THEME_BY_SLUG:
        raise HTTPException(404, "존재하지 않는 테마판입니다.")
    row = c.execute(
        "SELECT id FROM communities WHERE is_theme_board=1 AND board_slug=?",
        (slug,)).fetchone()
    if not row:
        raise HTTPException(503, "테마판 초기화가 완료되지 않았습니다.")
    return row["id"]


def board_data(c, slug, index, include_local=False, search="", region=""):
    theme = THEME_BY_SLUG[slug]
    board_id = public_board(c, slug)
    local_count = c.execute(
        "SELECT COUNT(*) FROM communities WHERE is_theme_board=0 AND board_slug=?",
        (slug,)).fetchone()[0]
    post_count = c.execute(
        "SELECT COUNT(*) FROM posts WHERE community_id=? AND hidden=0",
        (board_id,)).fetchone()[0]
    result = {
        "slug": slug, "id": board_id, "title": theme[1], "eyebrow": theme[2],
        "description": theme[3], "image_index": index, "local_count": local_count,
        "post_count": post_count, "is_official_theme_board": True,
    }
    if include_local:
        query = """SELECT c.*, (SELECT COUNT(*) FROM follows WHERE community_id=c.id) AS followers,
           (SELECT COUNT(*) FROM posts WHERE community_id=c.id AND hidden=0) AS post_count
           FROM communities c WHERE c.is_theme_board=0 AND c.board_slug=?"""
        params = [slug]
        if search.strip():
            query += " AND (c.name LIKE ? OR c.description LIKE ?)"
            params.extend(["%" + search.strip()[:80] + "%"] * 2)
        if region.strip() and region != "전국":
            query += " AND c.region=?"
            params.append(region.strip()[:20])
        query += " ORDER BY followers DESC,c.id DESC LIMIT 60"
        result["communities"] = [dict(x) for x in c.execute(query, params).fetchall()]
    return result


def register_theme_board_routes(app, root, db):
    @app.get("/board/{slug}", include_in_schema=False)
    def theme_board_page(slug: str):
        if slug not in THEME_BY_SLUG:
            raise HTTPException(404, "존재하지 않는 테마판입니다.")
        return FileResponse(root / "static" / "theme-board.html", media_type="text/html")

    @app.get("/api/boards")
    def theme_boards_index():
        with db() as c:
            return {"items": [board_data(c, t[0], i) for i, t in enumerate(THEMES)]}

    @app.get("/api/boards/{slug}")
    def theme_board_detail(slug: str, q: str = "", region: str = ""):
        with db() as c:
            return {"item": board_data(c, slug, list(THEME_BY_SLUG).index(slug) if slug in THEME_BY_SLUG else -1,
                                        include_local=True, search=q, region=region)}
