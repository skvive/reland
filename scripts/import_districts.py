"""Import the official MOLIT nationwide urban-renewal CSV without inventing geometry.
Usage: python scripts/import_districts.py path/to/official.csv [--dry-run]
Official source: https://www.data.go.kr/data/15160169/fileData.do
The 2026-05-18 source has 7 text fields and NO exact geocoordinates/boundaries.
"""
from __future__ import annotations
import argparse
import csv
import io
import os
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import REGIONS,db,init_db

COLS={
 'province':['시도','시도명','광역시도'],
 'city':['시군구','시군구명','구군'],
 'name':['구역명칭','정비구역명칭','정비구역명','구역명'],
 'stage':['현사업추진단계','현사업진행단계','사업추진단계','추진단계'],
 'kind':['사업유형','정비사업유형','사업종류'],
 'operator':['사업시행자','시행자'],
 'households':['공급예정세대수','공급예정세대','세대수']
}
def normalize(s):return ''.join(str(s).strip().replace('\ufeff','').split()).lower()

def decode_csv(path:Path):
    raw=path.read_bytes()
    for enc in ('utf-8-sig','cp949','euc-kr'):
        try:
            text=raw.decode(enc)
            if '구역' in text[:5000] and '시도' in text[:5000]:return text,enc
        except UnicodeDecodeError:pass
    raise ValueError('공식 CSV를 UTF-8/CP949/EUC-KR로 해독하지 못했습니다.')

def parse_rows(text):
    head=text[:2000]
    dialect=csv.Sniffer().sniff(head,delimiters=',\t;')
    reader=csv.DictReader(io.StringIO(text),dialect=dialect)
    names={normalize(k):k for k in reader.fieldnames or []}
    mapping={}
    for key,possibilities in COLS.items():
        actual=next((names.get(normalize(x)) for x in possibilities if names.get(normalize(x))),None)
        if not actual and key not in ('operator','households'):
            raise ValueError(f'필수 공식 컬럼 누락: {key}, 발견된 헤더: {list(names.values())}')
        mapping[key]=actual
    rows=[];skipped=0;seen=set()
    for i,row in enumerate(reader,2):
        def get(k):return str(row.get(mapping[k],'') or '').strip() if mapping[k] else ''
        name,province,city=get('name'),get('province'),get('city')
        if not name or not province or not city:
            skipped+=1;continue
        identity=(name,province,city)
        if identity in seen:skipped+=1;continue
        seen.add(identity)
        if len(name)>200 or len(province)>80 or len(city)>80:
            skipped+=1;continue
        place=next((r for r in REGIONS if r[0] in province or r[1] in province),None)
        if not place:
            # Never geolocate a zone without a verified region centroid.
            lat=lon=None;precision='unlocated'
        else:lat,lon,precision=place[2],place[3],'province_center'
        rows.append(dict(name=name,province=province,city=city,stage=get('stage') or '미기재',kind=get('kind') or '미기재',
            operator=get('operator'),households=get('households'),lat=lat,lon=lon,precision=precision,
            source_date='2026-05-18',source_url='https://www.data.go.kr/data/15160169/fileData.do'))
    return rows,skipped

def import_file(file,dry_run=False):
    text,encoding=decode_csv(Path(file));rows,skipped=parse_rows(text)
    if not rows:raise ValueError('삽입할 공식 데이터 행이 없습니다.')
    if not dry_run:
        init_db()
        with db() as c:
            for x in rows:
                prev=c.execute('SELECT id,stage FROM districts WHERE name=? AND province=? AND city=? AND demo=0',
                               (x['name'],x['province'],x['city'])).fetchone()
                c.execute('''INSERT INTO districts (name,province,city,stage,kind,operator,households,lat,lon,precision,source_url,source_date,demo)
                 VALUES (:name,:province,:city,:stage,:kind,:operator,:households,:lat,:lon,:precision,:source_url,:source_date,0)
                 ON CONFLICT(name,province,city) DO UPDATE SET stage=excluded.stage,kind=excluded.kind,
                 operator=excluded.operator,households=excluded.households,
                 lat=CASE WHEN EXISTS(SELECT 1 FROM district_geometries g WHERE g.district_id=districts.id)
                      THEN districts.lat ELSE excluded.lat END,
                 lon=CASE WHEN EXISTS(SELECT 1 FROM district_geometries g WHERE g.district_id=districts.id)
                      THEN districts.lon ELSE excluded.lon END,
                 precision=CASE WHEN EXISTS(SELECT 1 FROM district_geometries g WHERE g.district_id=districts.id)
                      THEN districts.precision ELSE excluded.precision END,
                 source_url=excluded.source_url,source_date=excluded.source_date,demo=0''',x)
                if prev and prev['stage']!=x['stage']:
                    c.execute('''INSERT INTO district_changes(district_id,old_stage,new_stage,source_url,source_date,detected_at)
                        VALUES(?,?,?,?,?,?)''',(prev['id'],prev['stage'],x['stage'],x['source_url'],x['source_date'],
                          __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(timespec='seconds')))
    return {'parsed':len(rows),'skipped':skipped,'encoding':encoding,'dry_run':dry_run,
            'geocoded_to_precise_boundary':0,'geometry_policy':'행정구역/시도 대표점: 정확 구역경계 아님'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='공공데이터포털 정비사업 CSV 가져오기')
    parser.add_argument('file',help='공공데이터포털에서 직접 내려받은 CSV')
    parser.add_argument('--dry-run',action='store_true',help='검증만 하고 DB는 수정하지 않음')
    args=parser.parse_args()
    try:print(import_file(args.file,args.dry_run))
    except Exception as ex:print(f'ERROR: {ex}',file=sys.stderr);sys.exit(1)
