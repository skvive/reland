"""Run with RELAND_ADMIN_KEY set before importing app. Isolated temp DB; doesn't modify included files."""
import os,sys,tempfile,json
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['RELAND_ADMIN_KEY']='not-a-real-production-secret-12345'
os.environ['RELAND_DB']=str(Path(tempfile.mkdtemp())/'test_admin.sqlite')
os.environ['RELAND_DEMO_MODE']='1'
from app import app
key={'x-admin-key':'not-a-real-production-secret-12345'}
with TestClient(app) as c:
 assert c.post('/api/auth/demo').status_code==200
 payload={'profession':'변호사','name':'검증용가상인물','office':'테스트법률사무소','region':'서울',
  'introduction':'이 예시는 실제 사람이 아니며 관리자의 검수 승인 흐름을 확인하기 위한 자동 테스트입니다.',
  'expertise':'조합설립과 분양신청','consent':True}
 r=c.post('/api/studio/experts/apply',json=payload);assert r.status_code==201,r.text
 eid=r.json()['id'];assert c.get('/api/studio/experts').json()['items']==[]
 assert c.get('/api/studio/admin/expert-applications',headers=key).status_code==200
 r=c.post(f'/api/studio/admin/experts/{eid}/review',headers=key,json={'approved':True,'note':'테스트 데이터 수동 승인'});assert r.status_code==200,r.text
 assert len(c.get('/api/studio/experts').json()['items'])==1
 r=c.post('/api/studio/admin/campaigns',headers=key,json={'expert_id':eid,'starts_at':'2026-10-01','ends_at':'2026-12-01','label':'광고 · 유료 노출'})
 assert r.status_code==201,r.text
 listing=c.get('/api/studio/experts').json()['items'][0]
 assert listing['sponsored'] and listing['ad_disclosure'].startswith('광고')
 r=c.post('/api/studio/admin/videos',headers=key,json={'youtube_url':'https://www.youtube.com/shorts/abcdefghijk','title':'가상 테스트 영상 식별자','category':'정비사업','creator':'테스트용 가상 제작자'})
 assert r.status_code==201,r.text
 assert c.get('/api/studio/videos').json()['items'][0]['video_id']=='abcdefghijk'
 assert c.post(f'/api/studio/experts/{eid}/event?event=phone_click').status_code==200
 assert c.get('/api/studio/experts/analytics').json()['events'].get('phone_click')==1
 assert len(c.get('/api/studio/admin/events',headers=key).json()['items'])>=1
 assert c.get('/api/studio/admin/events').status_code==403
 print('ADMIN INTEGRATION PASS — application → approval → advertising label → Shorts → own analytics → authorization')
