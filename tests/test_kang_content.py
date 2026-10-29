"""Integrity/security regression checks for Kang editor's educational blog."""
import json, re, subprocess, sys
from pathlib import Path
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
from app import app
client=TestClient(app)

def load(name):return json.loads((ROOT/'content'/'kang'/name).read_text(encoding='utf-8'))

def test_counts_and_unique_content():
 lessons=load('lectures_60.json');qa=load('qa_30.json')
 assert len(lessons)==60 and len(qa)==30
 assert len({x['title'] for x in lessons})==60 and len({x['question'] for x in qa})==30
 assert len({x['summary'] for x in lessons})==60
 assert len({x['answer'] for x in qa})==30
 assert len({x['category'] for x in lessons})==10
 assert all(len(x['pages'])>=7 for x in lessons)
 assert all(len(' '.join(p['body'] for p in x['pages']))>400 for x in lessons)

def test_all_lectures_sources_and_diagrams_exist():
 l=load('lectures_60.json');source=load('sources.json');law=source['law'];cases=source['precedents']
 for x in l:
  assert (ROOT/'kang_blog'/x['diagram']).is_file()
  assert (ROOT/'kang_blog'/'lectures'/f'{x["slug"]}.html').is_file()
  assert (ROOT/'kang_blog'/'slides'/f'{x["slug"]}.html').is_file()
  assert all(y in law for y in x['refs'])
  assert all(y in cases for y in x['cases'])
  assert '감수 전' in x['review']
 for x in load('qa_30.json'):
  assert (ROOT/'kang_blog'/'qa'/f"qa-{x['id']:03d}.html").is_file()
  assert all(y in law for y in x['refs'])
 for entry in list(law.values())+list(cases.values()):
  assert entry[1].startswith(('https://www.law.go.kr/','https://law.go.kr/'))

def test_no_real_private_photo_or_credentials_bundled():
 assert not list((ROOT/'kang_blog').rglob('28953*'))
 assert not list(ROOT.rglob('client_secret*.json'))
 assert not list(ROOT.rglob('token.json'))
 assert not list(ROOT.rglob('.env'))

def test_public_metadata_does_not_claim_legal_license():
 r=client.get('/api/kang/metadata');assert r.status_code==200
 d=r.json();assert d['lecture_count']==60 and d['qa_count']==30
 assert d['legal_representation'] is False
 assert d['public_blog_published'] is False
 assert d['blogger_blog_created'] is False

def test_lectures_and_qa_rest_api():
 d=client.get('/api/kang/lectures').json()
 assert d['count']==60 and len(d['items'])==60
 assert client.get('/api/kang/lectures/61').status_code==404
 assert client.get('/api/kang/lectures/1').json()['id']==1
 assert client.get('/api/kang/lectures?category=형사고소·사실 확인').json()['count']==6
 assert client.get('/api/kang/lectures?q=행정').status_code==200
 assert client.get('/api/kang/qa').json()['count']==30
 assert client.get('/api/kang/qa?category=분양·관리처분').json()['count']==3

def test_kang_blog_pages_real_http_response():
 for url in ('/kang/','/kang/index.html','/kang/blog.css','/kang/blog.js','/kang/data.js','/kang/assets/kang-avatar.webp','/kang/assets/lecture-001.svg','/kang/slides/lesson-001.html','/kang/lectures/lesson-001.html','/kang/qa/qa-001.html'):
  r=client.get(url)
  assert r.status_code==200,(url,r.status_code)
  assert r.content

def test_blogger_publisher_default_no_network():
 p=subprocess.run([sys.executable,str(ROOT/'scripts'/'publish_kang_blogger.py'),'--kind','lecture','--start','1','--count','3'],capture_output=True,text=True,timeout=10)
 assert p.returncode==0,p.stderr
 d=json.loads(p.stdout)
 assert d['mode']=='dry_run' and d['network_requests']==0 and not d['publish_public']

def test_blog_visible_disclaimer_and_no_fake_lawyer_claim():
 x=(ROOT/'kang_blog'/'index.html').read_text()
 assert '로펌 대표 변호사' not in x
 assert '개별 감수 전' in x and '교육 콘텐츠' in x
 assert 'mailto:kangjunchul8@gmail.com' in x
 assert '로스쿨 졸업' not in x and '변호사·법무사·행정사 사무소가 아니며' in x

def test_qa_case_only_validated():
 cases=load('sources.json')['precedents']
 for x in load('qa_30.json'):
  assert all(c in cases for c in x['cases'])
