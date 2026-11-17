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
