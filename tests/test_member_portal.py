import contextlib
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from member_portal import init_member_schema, register_member_portal

@pytest.fixture
def client(tmp_path):
    path=tmp_path/'member.sqlite'
    @contextlib.contextmanager
    def db():
        conn=sqlite3.connect(path)
        conn.row_factory=sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            yield conn
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:conn.close()
    with db() as c:
        c.executescript('''
        CREATE TABLE users(id INTEGER PRIMARY KEY, nickname TEXT NOT NULL, email TEXT NOT NULL,
          avatar TEXT NOT NULL DEFAULT '',bio TEXT NOT NULL DEFAULT '',blog_url TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL);
        CREATE TABLE posts(id INTEGER PRIMARY KEY, author_id INTEGER, title TEXT, created_at TEXT,
          hidden INTEGER DEFAULT 0,demo INTEGER DEFAULT 0);
        CREATE TABLE bookmarks(user_id INTEGER NOT NULL,post_id INTEGER NOT NULL);
        INSERT INTO users(id,nickname,email,created_at) VALUES(1,'테스트1','one@example.org','2026-11-22'),(2,'테스트2','two@example.org','2026-11-22');
        INSERT INTO posts(id,author_id,title,created_at) VALUES(1,1,'첫 번째 글','2026-11-22'),(2,2,'두 번째 글','2026-11-22');
        INSERT INTO bookmarks(user_id,post_id) VALUES(1,1),(2,2);
        ''')
    init_member_schema(db)
    init_member_schema(db)  # idempotent
    app=FastAPI()
    def require_user(req:Request):
        id=req.headers.get('x-test-user')
        if id not in ('1','2'):raise HTTPException(401,detail='로그인이 필요합니다.')
        with db() as con:u=con.execute('SELECT * FROM users WHERE id=?',(int(id),)).fetchone()
        if not u:raise HTTPException(401)
        return dict(u)
    register_member_portal(app,db,require_user,lambda:'2026-11-22T12:00:00+00:00',tmp_path)
    return TestClient(app),db

def headers(user=1,origin='http://testserver',safe=True):
    h={'x-test-user':str(user)}
    if safe:h.update({'X-Requested-With':'XMLHttpRequest','Origin':origin})
    return h

def test_auth_and_no_cache(client):
    api,_=client
    r=api.get('/api/member/learning')
    assert r.status_code==401
    r=api.get('/api/member/learning',headers=headers())
    assert r.status_code==200
    assert r.json()['member']['email']=='one@example.org'
    assert [x['title'] for x in r.json()['saved_posts']]==['첫 번째 글']

def test_progress_and_isolation(client):
    api,db=client
    r=api.put('/api/member/lessons/3',headers=headers(1),json={'status':'in_progress','saved':True})
    assert r.status_code==200,r.text
    assert r.json()['lesson']['saved']==1
    assert api.get('/api/member/learning',headers=headers(2)).json()['lessons']==[]
    r=api.put('/api/member/lessons/3',headers=headers(1),json={'status':'completed'})
    assert r.status_code==200
    assert r.json()['lesson']['saved']==1
    assert api.get('/api/member/learning',headers=headers(1)).json()['summary']=={'completed':1,'in_progress':0,'saved_lessons':1}
    with db() as con:con.execute('DELETE FROM users WHERE id=1')
    with db() as con:assert con.execute('SELECT COUNT(*) FROM member_course_progress').fetchone()[0]==0

def test_invalid_and_csrf(client):
    api,_=client
    assert api.put('/api/member/lessons/4',headers=headers(1,safe=False),json={'saved':True}).status_code==403
    assert api.put('/api/member/lessons/4',headers=headers(1,origin='https://evil.example'),json={'saved':True}).status_code==403
    assert api.put('/api/member/lessons/25',headers=headers(),json={'saved':True}).status_code==404
    assert api.put('/api/member/lessons/5',headers=headers(),json={}).status_code==422
    assert api.put('/api/member/lessons/5',headers=headers(),json={'status':'failed'}).status_code==422
