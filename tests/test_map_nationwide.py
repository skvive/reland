"""Nationwide map regression: URL filters, 17-region pins, responsive viewport."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
import app as site

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(site,'DB_PATH',tmp_path/'map-national.sqlite')
    monkeypatch.setattr(site,'DEMO_MODE',True)
    site.init_db()
    with TestClient(site.app) as web:yield web

def test_map_nationwide_data_not_replaced_by_seoul(client):
    # A clean test DB intentionally contains no operating-site rows. Seed three
    # example provinces and verify filtering without touching production data.
    fixtures=[
        ('서울특별시','강남구','서울 검사구역',37.5665,126.9780),
        ('부산광역시','부산진구','부산 검사구역',35.1796,129.0756),
        ('제주특별자치도','제주시','제주 검사구역',33.4996,126.5312),
    ]
    with site.db() as conn:
        for province,city,name,lat,lon in fixtures:
            conn.execute("""INSERT INTO districts
                (name,province,city,stage,kind,operator,households,
                 lat,lon,precision,source_url,source_date,demo)
                VALUES (?, ?, ?, '추진위원회','재개발','조합',100,
                    ?, ?, 'province_center',
                    'https://www.data.go.kr/data/15160169/fileData.do',
                    '2026-05-18',0)""",
                (name,province,city,lat,lon))
    all_areas=client.get('/api/districts?region=전국&limit=2000')
    assert all_areas.status_code==200
    body=all_areas.json()
    districts=[x for x in body['items'] if not x['demo']]
    assert body['verified_data_rows']==3
    assert len(districts)==3
    assert len({x['province'] for x in districts})==3
    seoul=client.get('/api/districts?region=서울특별시&limit=2000').json()['items']
    assert len(seoul)==1
    assert seoul[0]['province']=='서울특별시'
    coords={(round(float(d['lat']),3),round(float(d['lon']),3)) for d in districts}
    assert len(coords)==3
    assert min(x for x,y in coords)<34
    assert max(x for x,y in coords)>37
    assert min(y for x,y in coords)<127
    assert max(y for x,y in coords)>129
    assert site._molit_official_snapshot()['verified'] is True
    assert len(site._molit_official_snapshot()['regions'])==17


def test_clearing_filter_uses_full_query_string_not_pathname_only():
    js=(ROOT/'static'/'app.js').read_text(encoding='utf-8')
    assert "if(path===location.pathname+location.search)" in js
    assert "if(path===location.pathname){" not in js
    assert "normalizedMapRegion(params.get('region'))" in js
    assert "'서울특별시':'서울'" in js
    assert "'강원특별자치도':'강원'" in js
    assert 'href="/map" data-nav="map"' in js
    assert '↶ 전국 보기' in js

def test_both_map_providers_fit_all_visible_markers():
    js=(ROOT/'static'/'app.js').read_text(encoding='utf-8')
    assert 'function districtMarkerCoordinates(items)' in js
    assert 'fitGoogleDistrictViewport(map,items,zoom)' in js
    assert 'map.fitBounds(bounds,{top:42,bottom:42,left:36,right:36})' in js
    assert 'map.fitBounds(points,{padding:[32,32],maxZoom:zoom,animate:false})' in js
    assert "region==='전국'?7:10" in js
    assert "region==='서울'" in js
    assert "region==='서울특별시'" not in js

def test_map_assets_are_cache_busted_and_live_shell_loads(client):
    response=client.get('/map')
    assert response.status_code==200
    assert '/static/app.js?v=20261117map14' in response.text
    assert '/static/style.css?v=20261117map14' in response.text
    style=(ROOT/'static'/'style.css').read_text(encoding='utf-8')
    assert '.map-viewport-badge' in style
    sw=(ROOT/'static'/'sw.js').read_text(encoding='utf-8')
    assert 'reland-shell-v9-national-map-20261117' in sw
