"""Naver-friendly public HTML and public-data-source regression tests."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
import app as site

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(site,'DB_PATH',tmp_path/'seo.sqlite')
    monkeypatch.setattr(site,'DEMO_MODE',True)
    site.init_db()
    with TestClient(site.app) as browser:
        yield browser

def insert_project():
    with site.db() as c:
        c.execute("""INSERT INTO districts
            (name,province,city,stage,kind,operator,households,precision,source_url,source_date,demo)
            VALUES ('가야4','부산광역시','부산진구','4)조합설립인가',
                '1)재개발(주택정비)','1)조합','1020','province_center',
                'https://www.data.go.kr/data/15160169/fileData.do','2026-05-18',0)""")
        return c.execute("SELECT id FROM districts WHERE name='가야4'").fetchone()[0]

def test_naver_metadata_pages_are_server_rendered(client):
    for slug in site.SEO_TOPICS:
        res=client.get('/insights/'+slug)
        assert res.status_code==200
        assert 'index,follow' in res.text
        assert 'rel="canonical"' in res.text
        assert '<h1>' in res.text
        assert '공공데이터' in res.text or '재개발' in res.text
        assert 'application/ld+json' in res.text
    assert client.get('/insights/unknown').status_code==404

def test_regions_are_actual_source_count_not_invented(client):
    res=client.get('/regions/busan')
    assert res.status_code==200
    assert '부산광역시' in res.text
    assert '227' in res.text  # official MOLIT source rows for Busan on 2026-05-18
    assert '정비사업' in res.text
    assert client.get('/regions/no-such-region').status_code==404

def test_sitemap_excludes_demo_and_includes_official_pages(client):
    district=insert_project()
    response=client.get('/sitemap.xml')
    assert response.status_code==200
    doc=ET.fromstring(response.content)
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls=[el.text for el in doc.findall('.//s:loc',ns)]
    assert 'https://reland.lexid.site/district-info/'+str(district) in urls
    assert 'https://reland.lexid.site/insights/contribution' in urls
    assert 'https://reland.lexid.site/regions/busan' in urls
    assert len(urls)==len(set(urls))
    assert client.get('/robots.txt').status_code==200
    assert 'Sitemap: https://reland.lexid.site/sitemap.xml' in client.get('/robots.txt').text

def test_district_ssr_has_unique_text_and_canonical(client):
    pk=insert_project()
    result=client.get('/district-info/'+str(pk))
    assert result.status_code==200
    html=result.text
    assert 'rel="canonical" href="https://reland.lexid.site/district-info/'+str(pk)+'"' in html
    assert '<meta name="robots" content="index,follow' in html
    assert '부산광역시' in html
    assert '가야4' in html
    assert '공급 예정 세대' in html
    assert '부산시 정비사업 포털 추가자료' in html
    assert '2025-08-27' in html
    assert '부산시 사업장 공식 포털 원문' in html
    assert '<div id="record">' in html

def test_municipal_catalog_provenance_and_exact_match(client):
    pk=insert_project()
    profile=client.get('/api/districts/'+str(pk)+'/public').json()
    ref=profile['municipal_reference']
    assert ref['portal_stage']=='조합설립인가'
    assert ref['milestone']['date']=='2025-08-27'
    assert ref['representative_parcel']==''
    assert 'dynamice.busan.go.kr' in ref['source_url']
    refs=client.get('/api/map/secondary-sources').json()
    assert refs['matched_example_records']==7
    assert len(refs['sources'])==3
    assert refs['verified_on']=='2026-11-17'

def test_crawlable_spa_map_has_unique_title_links(client):
    res=client.get('/map')
    assert res.status_code==200
    assert '전국 재개발·재건축 지도' in res.text
    assert 'https://reland.lexid.site/map' in res.text
    assert '/insights/contribution' in res.text
