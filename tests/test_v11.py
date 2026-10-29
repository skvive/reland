"""v1.1 real DB integration tests for watches, change detection, geometry and case status."""
import json
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import app as site
from scripts.import_districts import import_file
from scripts.import_boundaries import import_boundaries

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(site,'DB_PATH',tmp_path/'v11.sqlite')
    monkeypatch.setattr(site,'DEMO_MODE',True)
    site.RATE.clear()
    site.init_db()
    with site.db() as c:
        c.execute("UPDATE settings SET value=? WHERE key='news_last_attempt'",(str(time.time()),))
    with TestClient(site.app) as cli:yield cli

def official(client,tmp_path,stage='조합설립인가'):
    fn=tmp_path/'official.csv'
    fn.write_text('시도,시군구,구역명칭,현 사업추진단계,사업유형,사업시행자,공급 예정 세대수\n'
        f'서울특별시,종로구,검증테스트구역,{stage},재개발사업,임의단체,430\n',encoding='utf-8-sig')
    result=import_file(fn)
    items=[x for x in client.get('/api/districts').json()['items'] if not x['demo']]
    return fn,items[0]['id'],result

def login(client):
    assert client.post('/api/auth/demo').status_code==200

def geomfile(tmp_path,district_id):
    p=tmp_path/'geometry.geojson'
    p.write_text(json.dumps({'type':'FeatureCollection','features':[
        {'type':'Feature','properties':{'district_id':district_id},
         'geometry':{'type':'Polygon','coordinates':[[
            [126.975,37.575],[126.977,37.575],[126.977,37.577],[126.975,37.575]]]} }]}))
    return p

def test_dashboard_auth_required(client):
    assert client.get('/api/my/dashboard').status_code==401

def test_demo_cannot_watch(client):
    login(client)
    res=client.post('/api/districts/1/watch')
    assert res.status_code==422

def test_official_district_watch_toggle_and_dashboard(client,tmp_path):
    _,did,_=official(client,tmp_path)
    login(client)
    assert client.post(f'/api/districts/{did}/watch').json()['watching'] is True
    dash=client.get('/api/my/dashboard').json()
    assert len(dash['watches'])==1 and dash['watches'][0]['id']==did
    assert '우리동네 탐험가' in dash['engagement']['badges']
    assert dash['engagement']['score']==5
    assert client.post(f'/api/districts/{did}/watch').json()['watching'] is False
    assert client.get('/api/my/dashboard').json()['watches']==[]

def test_change_detection_after_watch(client,tmp_path):
    _,did,_=official(client,tmp_path)
    login(client)
    client.post(f'/api/districts/{did}/watch')
    official(client,tmp_path,stage='사업시행인가')
    dashboard=client.get('/api/my/dashboard').json()
    assert len(dashboard['changes'])==1
    assert dashboard['changes'][0]['old_stage']=='조합설립인가'
    assert dashboard['changes'][0]['new_stage']=='사업시행인가'
    official(client,tmp_path,stage='사업시행인가')
    assert len(client.get('/api/my/dashboard').json()['changes'])==1

def test_geometry_requires_manual_acknowledgment(client,tmp_path):
    _,did,_=official(client,tmp_path)
    geo=geomfile(tmp_path,did)
    with pytest.raises(ValueError,match='confirm-reviewed'):
        import_boundaries(geo,'https://data.go.kr/official','2026-10-29')
    assert client.get(f'/api/districts/{did}/geometry').status_code==404

def test_polygon_import_and_reimport_does_not_lose_precise_geometry(client,tmp_path):
    fn,did,_=official(client,tmp_path)
    geo=geomfile(tmp_path,did)
    assert import_boundaries(geo,'https://data.go.kr/example.geojson','2026-10-29',True,True)['imported']==1
    assert client.get(f'/api/districts/{did}/geometry').status_code==404
    assert import_boundaries(geo,'https://data.go.kr/example.geojson','2026-10-29',True,False)['imported']==1
    exact=client.get(f'/api/districts/{did}/geometry')
    assert exact.status_code==200
    assert exact.json()['feature']['geometry']['type']=='Polygon'
    assert len(client.get('/api/map/boundaries').json()['items'])==1
    district=client.get(f'/api/districts/{did}').json()
    assert district['precision']=='boundary_polygon'
    assert 126.97<district['lon']<126.98
    import_file(fn)
    assert client.get(f'/api/districts/{did}').json()['precision']=='boundary_polygon'
    assert client.get(f'/api/districts/{did}/geometry').status_code==200

def test_geometry_rejects_invalid_and_remote_coordinates(client,tmp_path):
    _,did,_=official(client,tmp_path)
    geo=geomfile(tmp_path,did)
    for bad in [
        {'type':'Point','coordinates':[126,37]},
        {'type':'Polygon','coordinates':[[[0,0],[0,1],[1,1],[0,0]]]},
        {'type':'Polygon','coordinates':[[[126,37],[127,37],[127,38],[126,38]]]},
    ]:
        obj=json.loads(geo.read_text());obj['features'][0]['geometry']=bad
        geo.write_text(json.dumps(obj))
        with pytest.raises(ValueError):import_boundaries(geo,'https://data.go.kr/test','2026-10-29',True,False)
    assert client.get('/api/map/boundaries').json()['items']==[]

def test_cannot_map_demo_or_unmatched_district(client,tmp_path):
    geo=geomfile(tmp_path,1)
    with pytest.raises(ValueError,match='no unique real government district'):
        import_boundaries(geo,'https://data.go.kr/test','2026-10-29',True,False)

def test_badge_participation_and_consultations(client,tmp_path):
    login(client)
    for cid in (1,2,3):client.post(f'/api/communities/{cid}/follow')
    p=client.post('/api/posts',json={'community_id':1,'kind':'question','title':'구역 정보를 공유해주세요','body':'사업시행인가 고시 날짜를 어디서 확인할까요?'})
    assert p.status_code==201
    for _ in range(3):client.post(f'/api/posts/{p.json()["id"]}/comments',json={'body':'해당 자치단체 고시 게시판을 확인하세요.'})
    c=client.post('/api/consultations',json={'category':'조합 운영','region':'서울','subject':'조합문서 공개 여부 문의','message':'조합원 명부가 아닌 공개 문서의 범위를 상담하고 싶습니다.','consent':True})
    assert c.status_code==201
    dash=client.get('/api/my/dashboard').json()
    assert '첫 이야기' in dash['engagement']['badges']
    assert '소통 이웃' in dash['engagement']['badges']
    assert '모임 길잡이' in dash['engagement']['badges']
    assert dash['consultations'][0]['status']=='접수'

def test_consultation_status_admin_only_and_audit(client,tmp_path,monkeypatch):
    login(client)
    cons=client.post('/api/consultations',json={'category':'조합 운영','region':'서울','subject':'상담상태 알림 테스트 문의','message':'운영자 승인 절차를 확인하고 싶어서 문의드립니다.','consent':True})
    cid=cons.json()['id']
    monkeypatch.setattr(site,'ADMIN_KEY','test-only-strong-secret')
    end=f'/api/admin/consultations/{cid}/status'
    inp={'status':'검토중','note':'실제 운영자의 케이스 검토 시작 기록'}
    assert client.post(end,json=inp).status_code==403
    assert client.post(end,headers={'x-admin-key':'test-only-strong-secret'},json=inp).status_code==200
    assert client.get('/api/my/dashboard').json()['consultations'][0]['status']=='검토중'
    with site.db() as c:
        assert c.execute('SELECT COUNT(*) FROM audit_events WHERE target_id=?',(cid,)).fetchone()[0]==1

def test_account_deletion_removes_watches(client,tmp_path):
    _,did,_=official(client,tmp_path)
    login(client);client.post(f'/api/districts/{did}/watch')
    assert client.request('DELETE','/api/auth/account',json={'confirmation':'DELETE MY ACCOUNT'}).status_code==200
    with site.db() as c:assert c.execute('SELECT count(*) FROM district_watches').fetchone()[0]==0
