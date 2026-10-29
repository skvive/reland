import os
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
import app as site

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(site,'DB_PATH',tmp_path/'sample.sqlite')
    monkeypatch.setattr(site,'DEMO_MODE',True)
    site.RATE.clear()
    site.init_db()
    with site.db() as c:c.execute("UPDATE settings SET value=? WHERE key='news_last_attempt'",(str(time.time()),))
    with TestClient(site.app) as c:yield c

def login(c):
    r=c.post('/api/auth/demo');assert r.status_code==200
    return r.json()['user']

def test_health_and_config(client):
    assert client.get('/api/health').json()['status']=='ok'
    j=client.get('/api/config').json();assert j['source_count']==1566

def test_sample_cannot_be_presented_as_public_data(client):
    data=client.get('/api/districts').json()
    assert data['verified_data_rows']==0
    assert len(data['items'])==17
    assert all(r['demo']==1 and r['precision']=='region_center' for r in data['items'])

def test_no_unauthenticated_write(client):
    assert client.post('/api/posts',json={'community_id':1,'kind':'question','title':'안녕하세요 질문','body':'재개발 질문을 남겨 봅니다.'}).status_code==401
    assert client.post('/api/communities',json={'name':'우리 지역 모임','region':'서울','description':'지역 주민이 모이는 사랑방'}).status_code==401

def test_google_credential_forgery_denied(client,monkeypatch):
    monkeypatch.setattr(site,'GOOGLE_CLIENT_ID','example.apps.googleusercontent.com')
    response=client.post('/api/auth/google',json={'credential':'x'*150})
    assert response.status_code==401

def test_demo_local_login_and_session(client):
    user=login(client);assert user['nickname']=='리랜드 체험회원'
    assert client.get('/api/auth/me').json()['user']['id']==user['id']
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/auth/me').json()['user'] is None

def test_demo_login_off_in_prod(client,monkeypatch):
    monkeypatch.setattr(site,'DEMO_MODE',False)
    assert client.post('/api/auth/demo').status_code==403

def test_community_and_follows(client):
    login(client)
    res=client.post('/api/communities',json={'name':'청주 정보방','region':'충북','description':'청주 우리지역 정비사업 소식'});assert res.status_code==201
    cid=res.json()['id'];detail=client.get(f'/api/communities/{cid}').json()
    assert detail['following'] is True and detail['item']['official']==0
    assert client.post(f'/api/communities/{cid}/follow').json()['following'] is False
    ver=client.post(f'/api/communities/{cid}/verification',json={'note':'지역 정보방 운영자 확인을 받고 싶습니다'})
    assert ver.status_code==200 and '확인되지' in ver.json()['message']

def test_post_comment_likes_report(client):
    login(client)
    new=client.post('/api/posts',json={'community_id':1,'kind':'question','title':'정비사업 사업단계 질문','body':'구역별 사업진행의 공식자료는 어디서 읽나요?'})
    assert new.status_code==201
    pid=new.json()['id']
    assert client.post(f'/api/posts/{pid}/comments',json={'body':'관할 지자체의 고시를 먼저 확인하세요.'}).status_code==201
    assert client.post(f'/api/posts/{pid}/like').json()['active'] is True
    assert client.post(f'/api/posts/{pid}/like').json()['active'] is False
    assert client.post(f'/api/posts/{pid}/bookmark').json()['active'] is True
    assert client.post(f'/api/posts/{pid}/report',json={'reason':'게시글 개인정보 포함 여부 검토 요청'}).status_code==200
    detail=client.get(f'/api/posts/{pid}').json();assert len(detail['comments'])==1
    posts=client.get('/api/posts').json()['items'];assert any(x['id']==pid for x in posts)

def test_consultation_consent_required(client):
    login(client)
    example={'category':'조합원 자격','region':'서울','subject':'자격 관련 상담이 필요합니다','message':'관리처분 시기와 자격의 관계가 궁금합니다. 문의드립니다.','consent':False}
    assert client.post('/api/consultations',json=example).status_code==422
    example['consent']=True
    r=client.post('/api/consultations',json=example);assert r.status_code==201
    assert '배정' in r.json()['notice']

def test_profile_blogger_validation(client):
    login(client)
    base={'nickname':'동네이웃','bio':'테스트','blog_url':'http://127.0.0.1/private'}
    assert client.put('/api/auth/profile',json=base).status_code==422
    base['blog_url']='https://example.blogspot.com/'
    assert client.put('/api/auth/profile',json=base).status_code==200
    assert client.get('/api/auth/me').json()['user']['blog_url']=='https://example.blogspot.com/'

def test_no_access_to_admin_without_key(client,monkeypatch):
    monkeypatch.setattr(site,'ADMIN_KEY','super-secret-unknown')
    assert client.get('/api/admin/reports').status_code==403
    assert client.post('/api/admin/posts/1/hide').status_code==403

def test_origin_cross_site_write_blocked(client):
    r=client.post('/api/auth/demo',headers={'origin':'https://evil.example'})
    assert r.status_code==403

def test_news_parse_and_title_only():
    xml='<rss><channel><item><title>정비사업 정책 발표</title><link>https://news.example/story</link><source>example news</source><pubDate>Thu, 29 Oct 2026 05:00:00 GMT</pubDate><description>copyrighted article full text</description></item></channel></rss>'
    items=site.parse_rss(xml,'정책');assert len(items)==1
    assert 'description' not in items[0] and items[0]['title']=='정비사업 정책 발표'

def test_csv_import_dryrun_and_actual(client,tmp_path):
    from scripts.import_districts import import_file
    sample=tmp_path/'official.csv'
    sample.write_text('시도,시군구,구역명칭,현 사업추진단계,사업유형,사업시행자,공급 예정 세대수\n서울특별시,중구,테스트정비구역,조합설립인가,재개발사업,샘플사업시행자,450\n',encoding='utf-8-sig')
    assert import_file(sample,True)['parsed']==1
    assert client.get('/api/districts').json()['verified_data_rows']==0
    assert import_file(sample)['parsed']==1
    real=[x for x in client.get('/api/districts').json()['items'] if not x['demo']]
    assert len(real)==1 and real[0]['precision']=='province_center'
    assert real[0]['city']=='중구' and real[0]['lat']!=None

def test_spa_deep_links(client):
    assert client.get('/map').status_code==200
    assert '<title>리랜드' in client.get('/community/1').text
    assert client.get('/unknown.css').status_code==404
    assert client.get('/api/does-not-exist').status_code==404

def test_question_resolved_and_owner_only_delete(client):
    login(client)
    post=client.post('/api/posts',json={'community_id':1,'kind':'question','title':'관할 구청 공고 확인법 질문','body':'조합총회와 인가 고시는 어디서 확인할 수 있나요?'})
    pid=post.json()['id']
    assert client.post(f'/api/posts/{pid}/resolve').json()['resolved'] is True
    assert client.get(f'/api/posts/{pid}').json()['item']['resolved']==1
    assert client.request('DELETE',f'/api/posts/{pid}').status_code==200
    assert client.get(f'/api/posts/{pid}').status_code==404

def test_account_deletion_anonymizes_posts(client):
    login(client)
    post=client.post('/api/posts',json={'community_id':1,'kind':'discussion','title':'지역 동향을 확인해주세요','body':'여기서는 공개자료를 서로 공유할 수 있습니다.'})
    assert post.status_code==201
    assert client.request('DELETE','/api/auth/account',json={'confirmation':'WRONG'}).status_code==422
    assert client.request('DELETE','/api/auth/account',json={'confirmation':'DELETE MY ACCOUNT'}).status_code==200
    assert client.get('/api/auth/me').json()['user'] is None
    d=client.get(f"/api/posts/{post.json()['id']}").json()['item']
    assert d['author_label']=='탈퇴한 회원' and d['author_id'] is None

def test_official_status_requires_admin_secret(client,monkeypatch):
    login(client)
    cid=client.post('/api/communities',json={'name':'모임 관리자 테스트','region':'서울','description':'정비사업 관련 내용을 함께 나눕니다'}).json()['id']
    monkeypatch.setattr(site,'ADMIN_KEY','another-secret')
    endpoint=f'/api/admin/communities/{cid}/official'
    assert client.post(endpoint,json={'note':'대표자 확인을 아직 하지 않았습니다','approved':True}).status_code==403
    result=client.post(endpoint,headers={'X-Admin-Key':'another-secret'},json={'note':'공개된 법정 조합 자료를 운영자가 독립 확인한 기록','approved':True})
    assert result.status_code==200
    assert client.get(f'/api/communities/{cid}').json()['item']['official']==1

def test_community_blogger_owner_permissions(client):
    login(client)
    own=client.post('/api/communities',json={'name':'우리동네 Blogger 정보방','region':'서울','description':'공개 Blogger 게시글을 함께 살펴봅니다'})
    cid=own.json()['id']
    bad=client.put(f'/api/communities/{cid}/blog',json={'blog_url':'http://localhost/private'})
    assert bad.status_code==422
    ok=client.put(f'/api/communities/{cid}/blog',json={'blog_url':'https://town.blogspot.com/'})
    assert ok.status_code==200 and ok.json()['verified_blog_owner'] is False
    assert client.get(f'/api/communities/{cid}').json()['item']['blog_url']=='https://town.blogspot.com/'
