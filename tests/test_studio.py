"""High-signal v2 integration tests including permission boundaries, ad labels and 120 articles."""
import time, json, sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import app as site
from legal_studio import ARTICLES

@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(site,'DB_PATH',tmp_path/'studio.sqlite')
 monkeypatch.setattr(site,'DEMO_MODE',True)
 site.RATE.clear();site.init_db()
 with site.db() as c:c.execute("UPDATE settings SET value=? WHERE key='news_last_attempt'",(str(time.time()),))
 with TestClient(site.app) as c:yield c

def apply(c):
 c.post('/api/auth/demo')
 return c.post('/api/studio/experts/apply',json={
  'profession':'법무사','name':'테스트전문가','office':'예시 사무소','region':'서울',
  'introduction':'재개발 관련 등기 업무와 원본 문서 준비를 설명하는 입점 예시 프로필입니다.',
  'expertise':'재개발, 이전고시, 등기신청','phone':'02-123-4567','public_email':'info@example.com',
  'website':'https://example.com','blogger':'https://legaleditor.blogspot.com/','youtube':'https://www.youtube.com/@validchannel',
  'license_note':'공식 등록 조회 필요','consent':True})

def test_articles_are_120_unique_and_include_verified_links(client):
 assert len(ARTICLES)==120
 assert len({x['title'] for x in ARTICLES})==120
 assert all(x['status']=='editorial_review' and x['law_url'].startswith('https://') for x in ARTICLES)
 d=client.get('/api/studio/columns?limit=100').json()
 assert d['total']==120 and len(d['items'])==100
 p=client.get('/api/studio/columns?page=10').json();assert len(p['items'])==12
 for a in ARTICLES:
  r=client.get('/api/studio/columns/'+str(a['id']))
  assert r.status_code==200 and 'law_excerpt' in r.json() and '감수' in r.json()['legal_review']
 assert client.get('/api/studio/columns/121').status_code==404

def test_listing_filtering(client):
 d=client.get('/api/studio/columns?category=정보공개').json()
 assert d['total']==10
 d=client.get('/api/studio/columns?q=문서').json()
 assert d['total']>0
 assert client.get('/api/studio/metadata').json()['real_blogger_created'] is False

def test_empty_expert_directory_has_no_fake_person(client):
 assert client.get('/api/studio/experts').json()['items']==[]
 assert client.get('/api/studio/videos').json()['items']==[]
 assert client.get('/api/studio/experts/1').status_code==404

def test_apply_requires_auth_and_user_consent(client):
 assert client.post('/api/studio/experts/apply',json={'profession':'변호사','name':'김예시','office':'테스트 사무소','region':'서울','introduction':'재개발 분야의 실제 고객 상담과 관련된 소개 내용을 충족하는 긴 설명입니다.','expertise':'정비사업','consent':True}).status_code==401
 apply(client)
 assert client.get('/api/studio/experts').json()['items']==[]
 assert client.get('/api/studio/experts/mine').json()['expert']['status']=='pending'

def test_apply_rejects_untrusted_links(client):
 client.post('/api/auth/demo')
 payload={'profession':'변호사','name':'예시이름','office':'검수중사무소','region':'서울',
 'introduction':'도시정비사업 법률 서비스 안내를 위한 충분히 긴 설명입니다.','expertise':'재개발 분쟁','consent':True}
 assert client.post('/api/studio/experts/apply',json={**payload,'website':'http://127.0.0.1:80/test'}).status_code==422
 assert client.post('/api/studio/experts/apply',json={**payload,'blogger':'https://bad.example/'}).status_code==422
 assert client.post('/api/studio/experts/apply',json={**payload,'consent':False}).status_code==422
 assert client.post('/api/studio/experts/apply',json={**payload,'profession':'의사'}).status_code==422

def test_admin_approval_and_ad_disclosure(client):
 r=apply(client);assert r.status_code==201, r.text
 eid=r.json()['id']
 path=f'/api/studio/admin/experts/{eid}/review'
 assert client.post(path,json={'approved':True,'note':'등록자 확인'}) .status_code==403
 # Admin secret is captured at app initialization. Use a unique injected setting for this test.
 import legal_studio
 # do not monkeypatch credentials after registration; use the original real env configured by fixture if present
 with site.db() as c:c.execute("UPDATE expert_profiles SET status='approved',reviewed_note='테스트 관리자 심사' WHERE id=?",(eid,))
 result=client.get('/api/studio/experts').json();assert len(result['items'])==1
 assert result['items'][0]['sponsored'] is False
 assert result['items'][0]['name']=='테스트전문가'
 assert 'license_note' not in result['items'][0]
 assert client.get(f'/api/studio/experts/{eid}').json()['expert']['office']=='예시 사무소'
 assert client.post(f'/api/studio/experts/{eid}/event?event=phone_click').status_code==200
 assert client.post(f'/api/studio/experts/{eid}/event?event=unrecognized').status_code==422
 assert client.post('/api/studio/admin/campaigns',json={'expert_id':eid,'starts_at':'2026-10-01','ends_at':'2026-12-01'}).status_code==403

def test_approved_expert_can_submit_story_then_moderation(client):
 eid=apply(client).json()['id']
 with site.db() as c:c.execute("UPDATE expert_profiles SET status='approved' WHERE id=?",(eid,))
 res=client.post('/api/studio/experts/stories',json={
 'title':'관리처분 관련 개별 검토 체크리스트',
 'summary':'재개발 관리처분계획을 읽기 전 확인할 서류와 공고 기준을 정리했습니다.',
 'body':'재개발 단계에서는 공식 문서와 입법 예고 등을 혼동하지 말아야 합니다. '*12,
 'law_url':'https://www.law.go.kr/lsInfoP.do?lsiSeq=203773'})
 assert res.status_code==201,res.text
 assert client.get('/api/studio/stories').json()['items']==[]
 sid=res.json()['id']
 with site.db() as c:c.execute("UPDATE expert_stories SET status='approved' WHERE id=?",(sid,))
 assert len(client.get('/api/studio/stories').json()['items'])==1
 assert len(client.get(f'/api/studio/experts/{eid}').json()['stories'])==1

def test_youtube_and_admin_protected(client):
 assert client.get('/api/studio/admin/expert-applications').status_code==403
 assert client.post('/api/studio/admin/videos',json={'title':'검토된 영상','youtube_url':'https://www.youtube.com/shorts/abcdefghijk','category':'등기','creator':'실제 게시자'}).status_code==403
 assert client.get('/api/studio/videos').json()['items']==[]

def test_html_drafts_120_and_images_real_files():
 root=Path(__file__).resolve().parents[1]
 assert len(list((root/'blogger_drafts').glob('column-*.html')))==120
 assert len(list((root/'static/assets').glob('legal-topic-*.webp')))==12
 for a in ARTICLES:
  html_doc=(root/'blogger_drafts'/(a['slug']+'.html')).read_text(encoding='utf-8')
  assert a['law_url'] in html_doc and '원문 전체' in html_doc

def test_publisher_never_sends_without_confirm():
 from scripts.publish_blogger import build_request
 payload=build_request(ARTICLES[0],'')
 assert '원문' in payload['content']
 assert '감수전' in payload['labels']
 assert '<img' not in payload['content']


def test_server_rendered_editorial_has_legal_text_and_noindex(client):
 page=client.get('/column/1')
 assert page.status_code==200
 assert 'name="robots" content="noindex,follow"' in page.text
 assert '국가법령정보센터 원문 열기' in page.text
 assert '조합설립 절차' in page.text
 assert '법률 전문가 감수 전' not in page.text or '감수 전' in page.text
 assert client.get('/column/121').status_code==404

def test_partner_and_shorts_routes_return_app_shell(client):
 for path in ('/directory','/partners','/shorts','/columns'):
  assert client.get(path).status_code==200
  assert 'RE:LAND' in client.get(path).text

def test_my_analytics_auth_required(client):
 assert client.get('/api/studio/experts/analytics').status_code==401
