"""Strictly verified 2026-10-31 Incheon municipal data; never infer renamed districts."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
import app as site


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(site,'DB_PATH',tmp_path/'incheon-test.sqlite')
    monkeypatch.setattr(site,'DEMO_MODE',True)
    site.init_db()
    with TestClient(site.app) as t:yield t


def test_incheon_official_source_integrity():
    snapshot=site._incheon_public_snapshot()
    assert snapshot['verified'],snapshot['error']
    assert snapshot['source_rows']==168
    assert len(snapshot['records'])==168
    assert len(snapshot['by_key'])==165
    assert site.INCH_RAW_SHA256=='83ba7ddf9932cd429fba1278009a5a273ece0f7a32a9790e0834d2bb8615db17'


def test_exact_city_and_name_only_and_no_guessing():
    match=site._incheon_exact_records({'province':'인천광역시','city':'미추홀구','name':'도화1'})
    assert len(match)==1
    assert match[0]['area_square_meters']=='81788.80'
    assert match[0]['stage']=='관리처분계획인가'
    assert match[0]['source_asof']=='2026-10-31'
    assert match[0]['address'] and match[0]['source_url'].startswith('https://www.data.go.kr/')
    assert site._incheon_exact_records({'province':'인천광역시','city':'중구','name':'경동율목'})==[]
    assert len(site._incheon_exact_records({'province':'인천광역시','city':'미추홀구','name':'주안5동'}))==2
    assert site._incheon_exact_records({'province':'부산광역시','city':'미추홀구','name':'도화1'})==[]


def test_public_api_project_values_are_distinct_from_national(client):
    with site.db() as c:
        c.execute("""INSERT INTO districts
          (name,province,city,stage,kind,operator,households,precision,source_url,source_date,demo)
          VALUES ('도화1','인천광역시','미추홀구','5)관리처분인가','1)재개발(주택정비)','1)조합','0','province_center',
             'https://www.data.go.kr/data/15160169/fileData.do','2026-05-18',0)""")
        project_id=c.execute("SELECT id FROM districts WHERE name='도화1'").fetchone()[0]
    res=client.get(f'/api/districts/{project_id}/public')
    assert res.status_code==200
    payload=res.json()
    assert payload['source']['snapshot_date']=='2026-05-18'
    assert len(payload['incheon_official_records'])==1
    assert payload['incheon_official_records'][0]['area_square_meters']=='81788.80'
    assert payload['incheon_official_records'][0]['source_asof']=='2026-10-31'
    page=client.get('/district-info/'+str(project_id))
    assert page.status_code==200
    assert '인천시 2026-10-31 정비사업 추가 공공정보' in page.text
    assert '81788.80' in page.text
    assert '구역 면적(㎡)' in page.text


def test_incheon_full_official_catalog_is_public_and_sitemapped(client):
    index=client.get('/regions/incheon-official')
    assert index.status_code==200
    assert '<h1>' in index.text
    assert '168개 기록' in index.text
    assert '경동율목' in index.text
    assert '면적' in index.text
    assert '2026-10-31' in index.text
    assert 'data.go.kr/data/15055212' in index.text
    sitemap=client.get('/sitemap.xml')
    assert sitemap.status_code==200
    assert 'https://reland.lexid.site/regions/incheon-official' in sitemap.text
    regional=client.get('/regions/incheon')
    assert regional.status_code==200
    assert '/regions/incheon-official' in regional.text


def test_public_map_source_audit_proves_168_records(client):
    r=client.get('/api/map/public-status')
    assert r.status_code==200
    d=r.json()
    assert d['incheon_source_verified'] is True
    assert d['incheon_source_rows']==168
    assert d['incheon_source_asof']=='2026-10-31'
    sources=client.get('/api/map/secondary-sources').json()
    assert sources['incheon_20261031']['verified'] is True
    assert sources['incheon_20261031']['source_rows']==168


def test_gyesan_notice_draft_provenance_and_missing_households(client):
    official=site._verified_public_notice_record({
        'province':'인천광역시','city':'계양구','name':'계산극동아파트'
    })
    assert len(official['notices'])==2
    assert official['notices'][0]['notice_number']=='인천광역시 고시 제2026-33호'
    draft=official['historical_draft']
    assert draft['notice_number']=='인천광역시 계양구 공고 제2025-300호'
    assert draft['notice_date']=='2025-02-28'
    assert '확정' in draft['status']
    assert any(v['value']=='35,797.3㎡' for v in draft['values'])
    with site.db() as c:
        c.execute("""INSERT INTO districts
          (name,province,city,stage,kind,operator,households,precision,source_url,source_date,demo)
          VALUES ('계산극동아파트','인천광역시','계양구','3)추진위구성','3)재건축(공동주택)','1)조합','0','province_center',
             'https://www.data.go.kr/data/15160169/fileData.do','2026-05-18',0)""")
        district_id=c.execute("SELECT id FROM districts WHERE name='계산극동아파트'").fetchone()[0]
    response=client.get(f'/api/districts/{district_id}/public')
    assert response.status_code==200
    profile=response.json()
    assert profile['households_data_quality']=='unreported_zero'
    assert profile['historical_draft']['notice_date']=='2025-02-28'
    assert profile['official_parcel_address']=='인천광역시 계양구 계산동 899번지 일원'
    assert profile['location']['verified_boundary'] is False
    assert profile['official_notices'][0]['notice_date']=='2026-02-02'
    assert profile['official_portal_stage']['value']=='정비구역지정'
    for row in profile['incheon_official_records']:
        assert row['source_asof']=='2026-10-31'


def test_gyesan_map_client_does_not_misstate_zero_or_draft():
    source=(Path(__file__).resolve().parents[1]/'static'/'app.js').read_text(encoding='utf-8')
    assert '미확인 (원자료 0)' in source
    assert '2025년 정비계획 공람안' in source
    assert '확정 고시와 수치를 대조하기 전까지' in source
    assert 'map-source-record' in source
