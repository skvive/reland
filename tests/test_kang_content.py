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


def test_kang_education_inquiry_is_visible_on_all_pages():
    email = 'kangjunchul8@gmail.com'
    for url in ('/', '/kang/', '/kang/lesson-v6.html?id=1', '/kang/qa/'):
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        assert email in response.text, url
        assert 'mailto:' + email in response.text, url

    for number in range(1, 61):
        n = f'{number:03d}'
        for url in (f'/kang/lectures/lesson-{n}.html', f'/kang/slides/lesson-{n}.html'):
            response = client.get(url)
            assert response.status_code == 200, (url, response.status_code)
            assert email in response.text, url
            assert '재개발 교육·강의 문의' in response.text, url

    for number in range(1, 31):
        url = f'/kang/qa/qa-{number:03d}.html'
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        assert email in response.text, url
        assert '재개발 교육·강의 문의' in response.text, url

    assert client.get('/kang/lectures/lesson-999.html').status_code == 404
    assert client.get('/kang/qa/qa-999.html').status_code == 404
    assert client.get('/kang/qa/qa-v7.css').status_code == 200


def test_all_sixty_lecture_covers_are_local_and_http_decodable():
    """Prevents CDN expiry or missing media turning Android cards/heroes dark green."""
    asset_root = ROOT / 'kang_blog' / 'assets'
    loader = (ROOT / 'kang_blog' / 'story-photo-v14.js').read_text(encoding='utf-8')
    assert 'cloudfront.net' not in loader
    assert "const originals=Object.freeze" in loader
    assert "document.addEventListener('error'" in loader
    checksums = set()
    for n in range(1, 61):
        number = f'{n:03d}'
        webp = asset_root / 'lessons' / f'lesson-{number}.webp'
        svg = asset_root / 'lesson-stories' / f'story-{number}.svg'
        assert webp.is_file() and svg.is_file(), number
        image_response = client.get(f'/kang/assets/lessons/lesson-{number}.webp')
        assert image_response.status_code == 200, number
        assert image_response.headers['content-type'].startswith('image/webp')
        assert image_response.content[:4] == b'RIFF'
        assert image_response.content[8:12] == b'WEBP'
        checksums.add(__import__('hashlib').sha256(image_response.content).hexdigest())
        svg_response = client.get(f'/kang/assets/lesson-stories/story-{number}.svg')
        assert svg_response.status_code == 200, number
        assert b'<svg' in svg_response.content[:1000]
    assert len(checksums) == 60
    for n in (1, 10, 11, 20, 30, 60):
        html = client.get(f'/kang/lectures/lesson-{n:03d}.html')
        assert html.status_code == 200
        assert '/kang/assets/kang-class-hero-v5.webp' in html.text
        assert '기존 7단계 교육 원고와 공식 법령 출처 보기' in html.text
    for url in ('/kang/', '/kang/lesson-v6.html?id=1', '/kang/lesson-v6.html?id=60'):
        page = client.get(url)
        assert page.status_code == 200
        assert 'story-photo-v14.js?v=20261113v16' in page.text

def test_approved_brand_hero_and_individual_scene_visuals_on_all_60():
    """Instructor portrait stays approved; scene image changes with every course."""
    brand = client.get('/kang/assets/kang-class-hero-v5.webp')
    assert brand.status_code == 200
    assert brand.headers['content-type'].startswith('image/webp')
    assert brand.content[:4] == b'RIFF'

    detail = client.get('/kang/lesson-v6.html?id=1')
    assert detail.status_code == 200
    assert 'id="lectureImage" data-brand-hero="1"' in detail.text
    assert 'src="/kang/assets/kang-class-hero-v5.webp"' in detail.text
    assert 'id="storySceneImage"' in detail.text
    assert '/kang/lesson-brand-v17.css?v=20261113v17' in detail.text
    assert client.get('/kang/lesson-brand-v17.css').status_code == 200

    controller = (ROOT/'kang_blog'/'lesson-v6.js').read_text(encoding='utf-8')
    assert "brandImage.src = '/kang/assets/kang-class-hero-v5.webp'" in controller
    assert "sceneImage.src = '/kang/assets/kang-class-hero-v5.webp'" in controller
    assert "storySceneTitle" in controller

    for number in range(1, 61):
        n = f'{number:03d}'
        response = client.get(f'/kang/lectures/lesson-{n}.html')
        assert response.status_code == 200, number
        assert '<div class="rk-brand-banner"' in response.text, number
        assert '/kang/assets/kang-class-hero-v5.webp' in response.text, number
        assert '/kang/lesson-brand-v17.css?v=20261113v17' in response.text, number
        assert '/kang/assets/kang-class-hero-v5.webp' in response.text, number
        assert '기존 7단계 교육 원고와 공식 법령 출처 보기' in response.text, number


def test_kang_v19_restores_top_brand_and_replaces_meeting_picture():
    """All 60 chapters use approved instructor visual without RE:LAND text in scene."""
    logo = client.get('/static/assets/logo-reland.svg')
    assert logo.status_code == 200
    brand = client.get('/kang/assets/kang-class-hero-v5.webp')
    assert brand.status_code == 200 and brand.content[:4] == b'RIFF'
    assert client.get('/kang/lesson-brand-v19.css').status_code == 200
    detail = client.get('/kang/lesson-v6.html?id=1')
    assert detail.status_code == 200
    assert '<div class="hero-copy">' in detail.text
    assert 'class="hero-logo-panel"' not in detail.text
    assert 'id="storySceneImage" data-brand-hero="1"' in detail.text
    assert '/kang/lesson-brand-v18.css' not in detail.text
    assert '/kang/lesson-brand-v19.css' in detail.text
    js = (ROOT / 'kang_blog' / 'lesson-v6.js').read_text(encoding='utf-8')
    assert "sceneImage.src = '/kang/assets/kang-class-hero-v5.webp'" in js
    assert "sceneImage.dataset.brandHero = '1'" in js
    assert 'sceneImage.src = scenePath' not in js
    for i in range(1, 61):
        html = client.get(f'/kang/lectures/lesson-{i:03d}.html')
        assert html.status_code == 200
        assert 'class="rk-brand-banner"' in html.text
        assert 'class="rk-story-scene-brand"' in html.text
        assert 'class="rk-kang-only"' in html.text
        assert 'data-brand-hero="1"' in html.text
        assert '/kang/lesson-brand-v18.css' not in html.text
        assert '/kang/assets/kang-class-hero-v5.webp' in html.text
        assert '기존 7단계 교육 원고와 공식 법령 출처 보기' in html.text
