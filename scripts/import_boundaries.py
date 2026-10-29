"""Operator-only import of WGS84 polygon geometries from separately verified government spatial data.

python scripts/import_boundaries.py zones.geojson --source-url https://example.go.kr/official-file \
    --source-date 2026-10-29 --confirm-reviewed [--dry-run]

Feature identifiers may be properties.district_id or exact (name,province,city).
This tool validates geometry structure and plausible Korean coordinates, NOT government authenticity.
Never use this to invent polygon geometry from province centroids.
"""
from __future__ import annotations
import argparse, json, math, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import db,init_db,utcnow

MAX_COORDS=30_000

def rings_of(geom):
    if not isinstance(geom,dict):raise ValueError('geometry must be an object')
    if geom.get('type')=='Polygon':polys=[geom.get('coordinates')]
    elif geom.get('type')=='MultiPolygon':polys=geom.get('coordinates')
    else:raise ValueError('Only Polygon and MultiPolygon are permitted')
    if not isinstance(polys,list) or not polys:raise ValueError('Missing polygon coordinates')
    flat=[]
    for poly in polys:
        if not isinstance(poly,list) or not poly:raise ValueError('Missing polygon rings')
        for ring in poly:
            if not isinstance(ring,list) or len(ring)<4:raise ValueError('A ring must contain 4+ coordinates')
            if ring[0]!=ring[-1]:raise ValueError('Polygon rings must be closed')
            for point in ring:
                if not isinstance(point,list) or len(point)!=2:raise ValueError('Coordinates must be [longitude,latitude]')
                lon,lat=point
                if not all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in (lon,lat)):
                    raise ValueError('Non-numeric or nonfinite coordinate')
                if not (123<=lon<=133 and 32<=lat<=40):raise ValueError('Coordinate out of South Korea vicinity')
                flat.append((lon,lat))
                if len(flat)>MAX_COORDS:raise ValueError('Polygon too detailed; simplify before import')
    return flat

def import_boundaries(file,source_url,source_date,confirm_reviewed=False,dry_run=True):
    if not confirm_reviewed:raise ValueError('Provide --confirm-reviewed after independently checking the spatial source and license')
    url=urlsplit(source_url)
    if url.scheme!='https' or not url.hostname or url.username:raise ValueError('An https source URL is required')
    date.fromisoformat(source_date)
    obj=json.loads(Path(file).read_text(encoding='utf-8-sig'))
    if not isinstance(obj,dict) or obj.get('type')!='FeatureCollection' or not isinstance(obj.get('features'),list):
        raise ValueError('Expected FeatureCollection')
    if not obj['features'] or len(obj['features'])>2500:raise ValueError('Unexpected feature count')
    parsed=[]
    with db() as c:
        for i,f in enumerate(obj['features'],1):
            if not isinstance(f,dict) or f.get('type')!='Feature':raise ValueError(f'Feature {i} malformed')
            p=f.get('properties') or {}
            if not isinstance(p,dict):raise ValueError('Feature properties must be an object')
            coords=rings_of(f.get('geometry'))
            if p.get('district_id') is not None:
                rows=c.execute('SELECT id,demo FROM districts WHERE id=?',(int(p['district_id']),)).fetchall()
            else:
                if not all(p.get(k) for k in ('name','province','city')):
                    raise ValueError('Require properties.district_id or exact name,province,city')
                rows=c.execute('SELECT id,demo FROM districts WHERE name=? AND province=? AND city=?',
                    (p['name'],p['province'],p['city'])).fetchall()
            if len(rows)!=1 or rows[0]['demo']:
                raise ValueError(f'Feature {i}: no unique real government district match')
            district_id=rows[0]['id']
            if district_id in [x[0] for x in parsed]:raise ValueError('Duplicate district geometry')
            centroid=(sum(x for x,y in coords)/len(coords),sum(y for x,y in coords)/len(coords))
            # Strip user-supplied properties to avoid unsafe/inaccurate annotations.
            feature={'type':'Feature','properties':{'district_id':district_id},'geometry':f['geometry']}
            parsed.append((district_id,json.dumps(feature,ensure_ascii=False,separators=(',',':')),centroid))
        if not dry_run:
            for did,geojson,(lon,lat) in parsed:
                c.execute('''INSERT INTO district_geometries(district_id,geojson,source_url,source_date,recorded_at)
                    VALUES(?,?,?,?,?) ON CONFLICT(district_id) DO UPDATE SET
                    geojson=excluded.geojson,source_url=excluded.source_url,
                    source_date=excluded.source_date,recorded_at=excluded.recorded_at''',
                    (did,geojson,source_url,source_date,utcnow()))
                c.execute('UPDATE districts SET lat=?,lon=?,precision=? WHERE id=?',(lat,lon,'boundary_polygon',did))
    return {'imported':len(parsed),'dry_run':dry_run,'source_url':source_url,'source_date':source_date,
        'notice':'Geometry plausibility checks passed; source authenticity must be independently reviewed by the operator.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('file',type=Path)
    ap.add_argument('--source-url',required=True)
    ap.add_argument('--source-date',required=True)
    ap.add_argument('--confirm-reviewed',action='store_true')
    ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args()
    init_db()
    try:print(json.dumps(import_boundaries(a.file,a.source_url,a.source_date,a.confirm_reviewed,a.dry_run),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError) as ex:print('ERROR:',ex,file=sys.stderr);sys.exit(1)
