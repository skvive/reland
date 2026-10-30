"""Publish bundled editorial content (v3.0.2: 120 columns + 60 lectures + 30 Q&A) into community boards."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
SEED_VERSION = "v3.0.2-210-boards"

COMMUNITIES = [
    {
        "seed_key": "board-legal-journal",
        "name": "RE:LAND 법률지식",
        "region": "전국",
        "description": "재개발·도시정비 법률 저널 120편 요약과 전문 링크. 편집 초안이며 개별 법률 자문을 대신하지 않습니다.",
        "official": 1,
    },
    {
        "seed_key": "board-kang-class",
        "name": "재개발 강실장 클래스",
        "region": "전국",
        "description": "강실장 교육 모듈 60편 안내. 교육용 초안이며 소송·고소 대리를 제공하지 않습니다.",
        "official": 1,
    },
    {
        "seed_key": "board-kang-qa",
        "name": "강실장 Q&A TOP30",
        "region": "전국",
        "description": "재개발 실무에서 자주 묻는 질문 30선. 답변은 편집 초안이며 사건별 전문가 검토가 필요합니다.",
        "official": 1,
    },
]


def _load_json(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def _clip(text: str, n: int = 4800) -> str:
    t = (text or "").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def build_posts() -> list[dict]:
    posts: list[dict] = []
    for col in _load_json("columns_120.json"):
        posts.append(
            {
                "seed_key": f"column-{col['id']:03d}",
                "community_seed_key": "board-legal-journal",
                "kind": "discussion",
                "title": col["title"],
                "body": _clip(
                    f"{col.get('description', '')}\n\n"
                    f"카테고리: {col.get('category', '')}\n"
                    f"전문 보기: /column/{col['id']}\n\n"
                    f"{col.get('legal_review', '편집 초안')}"
                ),
                "author_label": "RE:LAND 법률 저널",
                "resolved": 0,
            }
        )
    for lec in _load_json("kang/lectures_60.json"):
        posts.append(
            {
                "seed_key": f"lesson-{lec['id']:03d}",
                "community_seed_key": "board-kang-class",
                "kind": "discussion",
                "title": lec["title"],
                "body": _clip(
                    f"{lec.get('summary', '')}\n\n"
                    f"카테고리: {lec.get('category', '')}\n"
                    f"강의 열기: /kang/lectures/{lec.get('slug', 'lesson-' + str(lec['id']).zfill(3))}.html\n\n"
                    f"{lec.get('review', '편집 초안')}"
                ),
                "author_label": "재개발 강실장",
                "resolved": 0,
            }
        )
    for qa in _load_json("kang/qa_30.json"):
        posts.append(
            {
                "seed_key": f"qa-{qa['id']:03d}",
                "community_seed_key": "board-kang-qa",
                "kind": "question",
                "title": qa["question"],
                "body": _clip(
                    f"{qa.get('answer', '')}\n\n"
                    f"카테고리: {qa.get('category', '')}\n"
                    f"강실장 Q&A 더 보기: /kang/\n\n"
                    f"{qa.get('status', '편집 초안')}"
                ),
                "author_label": "재개발 강실장",
                "resolved": 1,
            }
        )
    return posts


def ensure_seed_columns(c, table_has_column) -> None:
    if not table_has_column(c, "communities", "seed_key"):
        c.execute("ALTER TABLE communities ADD COLUMN seed_key TEXT NOT NULL DEFAULT ''")
    if not table_has_column(c, "posts", "seed_key"):
        c.execute("ALTER TABLE posts ADD COLUMN seed_key TEXT NOT NULL DEFAULT ''")


def apply_published_content(c, utcnow, table_has_column, *, force: bool = False) -> dict:
    """Idempotent board seed. Returns counts inserted/skipped."""
    ensure_seed_columns(c, table_has_column)
    row = c.execute("SELECT value FROM settings WHERE key='content_boards_seed'").fetchone()
    if row and row["value"] == SEED_VERSION and not force:
        return {"skipped": True, "version": SEED_VERSION}

    comm_ids: dict[str, int] = {}
    comm_inserted = 0
    for spec in COMMUNITIES:
        existing = c.execute(
            "SELECT id FROM communities WHERE seed_key=?", (spec["seed_key"],)
        ).fetchone()
        if existing:
            comm_ids[spec["seed_key"]] = existing["id"]
            continue
        cur = c.execute(
            """INSERT INTO communities(name,region,description,official,seed_key,created_at)
               VALUES(?,?,?,?,?,?)""",
            (
                spec["name"],
                spec["region"],
                spec["description"],
                spec["official"],
                spec["seed_key"],
                utcnow(),
            ),
        )
        comm_ids[spec["seed_key"]] = cur.lastrowid
        comm_inserted += 1

    posts = build_posts()
    post_inserted = 0
    for post in posts:
        if c.execute("SELECT 1 FROM posts WHERE seed_key=?", (post["seed_key"],)).fetchone():
            continue
        cid = comm_ids.get(post["community_seed_key"])
        if not cid:
            continue
        c.execute(
            """INSERT INTO posts(community_id,kind,title,body,demo,author_label,resolved,seed_key,created_at)
               VALUES(?,?,?,?,0,?,?,?,?)""",
            (
                cid,
                post["kind"],
                post["title"],
                post["body"],
                post["author_label"],
                post.get("resolved", 0),
                post["seed_key"],
                utcnow(),
            ),
        )
        post_inserted += 1

    c.execute(
        "INSERT INTO settings(key,value) VALUES('content_boards_seed',?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (SEED_VERSION,),
    )
    return {
        "skipped": False,
        "version": SEED_VERSION,
        "communities_inserted": comm_inserted,
        "posts_inserted": post_inserted,
        "posts_total": len(posts),
    }
