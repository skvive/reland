"""RE:LAND member learning routes; extend the existing login/session/database."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit
from typing import Literal

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel


class LessonUpdate(BaseModel):
    status: Literal['not_started', 'in_progress', 'completed'] | None = None
    saved: bool | None = None


def init_member_schema(db):
    """Idempotent schema; user FK ensures private learning data follows account deletion."""
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS member_course_progress (
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          lesson_no INTEGER NOT NULL CHECK(lesson_no BETWEEN 1 AND 24),
          status TEXT NOT NULL DEFAULT 'not_started'
            CHECK(status IN ('not_started', 'in_progress', 'completed')),
          saved INTEGER NOT NULL DEFAULT 0 CHECK(saved IN (0,1)),
          updated_at TEXT NOT NULL,
          PRIMARY KEY(user_id, lesson_no)
        );
        ''')


def require_same_site_write(request: Request):
    """Extra anti-CSRF guard for member changes in addition to existing SameSite cookie."""
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        raise HTTPException(status_code=403, detail='정상적인 사이트 요청만 허용됩니다.')
    origin = request.headers.get('origin')
    if origin:
        src = urlsplit(origin)
        scheme = (request.headers.get('x-forwarded-proto') or request.url.scheme).split(',')[0].strip()
        host = (request.headers.get('x-forwarded-host') or request.headers.get('host') or request.url.netloc).split(',')[0].strip()
        if src.scheme != scheme or src.netloc.lower() != host.lower() or src.path not in ('', '/'):  # exact origin
            raise HTTPException(status_code=403, detail='허용되지 않는 출처입니다.')
    elif request.headers.get('sec-fetch-site') != 'same-origin':
        raise HTTPException(status_code=403, detail='요청 출처를 확인할 수 없습니다.')


def register_member_portal(app: FastAPI, db, require_user, utcnow, root: Path):
    """Register routes before the site's catch-all SPA route."""

    @app.get('/mypage', include_in_schema=False)
    @app.get('/mypage/', include_in_schema=False)
    def member_page():
        return FileResponse(root/'static'/'mypage.html', media_type='text/html; charset=utf-8',
                            headers={'Cache-Control':'private, no-store', 'X-Robots-Tag':'noindex, noarchive'})

    @app.get('/api/member/learning')
    def member_learning(request: Request):
        user = require_user(request)
        uid = user['id']
        with db() as con:
            rows = [dict(row) for row in con.execute('''
                SELECT lesson_no,status,saved,updated_at FROM member_course_progress
                WHERE user_id=? ORDER BY lesson_no
            ''', (uid,)).fetchall()]
            saved_posts = [dict(row) for row in con.execute('''
                SELECT p.id,p.title,p.created_at FROM bookmarks b
                JOIN posts p ON p.id=b.post_id
                WHERE b.user_id=? AND p.hidden=0 AND p.demo=0
                ORDER BY p.id DESC LIMIT 16
            ''', (uid,)).fetchall()]
            my_posts = [dict(row) for row in con.execute('''
                SELECT id,title,created_at FROM posts
                WHERE author_id=? AND hidden=0 AND demo=0
                ORDER BY id DESC LIMIT 12
            ''', (uid,)).fetchall()]
        return {
            'member': {'nickname':user['nickname'], 'email':user['email'], 'avatar':user['avatar'],
                       'bio':user['bio'], 'blog_url':user['blog_url'], 'created_at':user['created_at']},
            'lessons':rows,
            'saved_posts':saved_posts,
            'my_posts':my_posts,
            'summary':{'completed':sum(x['status']=='completed' for x in rows),
                       'in_progress':sum(x['status']=='in_progress' for x in rows),
                       'saved_lessons':sum(bool(x['saved']) for x in rows)}
        }

    @app.put('/api/member/lessons/{lesson_no}')
    def update_member_lesson(lesson_no:int, data:LessonUpdate, request: Request):
        require_same_site_write(request)
        user = require_user(request)
        if not (1 <= lesson_no <= 24):
            raise HTTPException(status_code=404, detail='강의를 찾을 수 없습니다.')
        if data.status is None and data.saved is None:
            raise HTTPException(status_code=422, detail='수정할 항목이 없습니다.')
        with db() as con:
            current = con.execute('''SELECT status,saved FROM member_course_progress
                                     WHERE user_id=? AND lesson_no=?''',
                                  (user['id'],lesson_no)).fetchone()
            new_status = data.status if data.status is not None else (current['status'] if current else 'not_started')
            saved = int(data.saved) if data.saved is not None else int(current['saved'] if current else 0)
            row = con.execute('''
                INSERT INTO member_course_progress(user_id,lesson_no,status,saved,updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(user_id,lesson_no) DO UPDATE SET
                   status=excluded.status,saved=excluded.saved,updated_at=excluded.updated_at
                RETURNING lesson_no,status,saved,updated_at
            ''',(user['id'],lesson_no,new_status,saved,utcnow())).fetchone()
        return {'lesson': dict(row)}
