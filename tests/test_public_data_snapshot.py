"""Regression checks for the exact 2026-05-18 public-data source file.
The 1,566 source records must not be mistaken for 1,547 identical projects.
"""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as site


def test_official_snapshot_sha256_and_source_count():
    data=site._molit_official_snapshot()
    assert data['verified'],data.get('error')
    assert data['source_rows']==1566
    assert data['unique_keys']==1547
    assert data['shared_name_groups']==17
    assert data['additional_same_name_records']==19
    assert len(data['regions'])==17


def test_same_name_rows_have_distinct_original_attributes():
    record={'province':'부산광역시','city':'남구','name':'대연3'}
    matches=site._molit_snapshot_variants(record)
    assert len(matches)==3
    assert len({r['사업유형'] for r in matches})==3
    assert len({r['_official_csv_line'] for r in matches})==3


def test_snapshot_does_not_invent_zone_geometry():
    data=site._molit_official_snapshot()
    sample=data['by_key'][site._clean_field('부산광역시'),site._clean_field('남구'),site._clean_field('대연3')]
    for row in sample:
        assert 'latitude' not in row and 'longitude' not in row
        assert '사업비' not in row


def test_public_details_preserve_source_variants_and_real_notice_only(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    monkeypatch.setattr(site, 'DB_PATH', tmp_path / 'district_info.sqlite')
    monkeypatch.setattr(site, 'DEMO_MODE', True)
    site.init_db()
    with site.db() as db:
        db.execute("""INSERT INTO districts
          (name, province, city, stage, kind, operator, households, precision,
           source_url, source_date, demo)
          VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
          ('대연3', '부산광역시', '남구', '7)착공', '1)재개발(주택정비)',
           '1)조합', '4488', 'province_center',
           'https://www.data.go.kr/data/15160169/fileData.do', '2026-05-18'))
        pk=db.execute("SELECT id FROM districts WHERE name=? AND city=?",
                      ('대연3','남구')).fetchone()[0]
    with TestClient(site.app) as client:
        result=client.get(f'/api/districts/{pk}/public')
        assert result.status_code == 200
        item=result.json()
        assert item['source']['snapshot_verified']
        assert len(item['official_source_variants']) == 3
        assert {rec['kind'] for rec in item['official_source_variants']} == {
            '3)재건축(공동주택)', '5)주거환경개선', '1)재개발(주택정비)'}
        assert item['official_notices'] == []
        assert item['official_parcel_address'] == ''
        page=client.get(f'/district-info/{pk}')
        assert page.status_code == 200
        for marker in ('id="projectRecordStatus"', 'id="projectNotices"',
                       'id="projectMissing"', '20261117v10'):
            assert marker in page.text
