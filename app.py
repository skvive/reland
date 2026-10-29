"""RE:LAND - Korean redevelopment information & community prototype.
Run: python app.py  (or uvicorn app:app --host 127.0.0.1 --port 8000)
Public data imports are opt-in and are never confused with demo regional hubs.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from contextlib import contextmanager
from db_engine import open_db, table_has_column, USE_POSTGRES
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import httpx
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes
from fastapi import BackgroundTasks, Cookie, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from neon_auth_jwt import validate_neon_token

ROOT = Path(__file__).resolve().parent
# Support a local .env settings file without introducing a mandatory extra package.
# Existing environment variables always take precedence over file values.
def load_env_file():
    env_file = ROOT / '.env'
    if not env_file.is_file():return
    for raw in env_file.read_text(encoding='utf-8-sig').splitlines():
        line=raw.strip()
        if not line or line.startswith('#') or '=' not in line:continue
        key,val=line.split('=',1)
        key=key.strip()
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',key):continue
        val=val.strip()
        if len(val)>=2 and val[0]==val[-1] and val[0] in ('"',"'"):
            val=val[1:-1]
        os.environ.setdefault(key,val)
load_env_file()
DB_PATH = Path(os.getenv('RELAND_DB', str(ROOT / 'data' / 'reland.sqlite')))
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '').strip()
ENV = os.getenv('ENVIRONMENT', 'development').lower()
DEMO_MODE = os.getenv('RELAND_DEMO_MODE', '1') == '1' and ENV != 'production'
COOKIE_SECURE = ENV == 'production' or os.getenv('COOKIE_SECURE', '0') == '1'
ADMIN_KEY = os.getenv('RELAND_ADMIN_KEY', '')
NEON_AUTH_BASE_URL = os.getenv('NEON_AUTH_BASE_URL', '').strip()
NEON_AUTH_PROXY_PREFIX = '/api/neon-auth'
NEWS_TTL = 60 * 60 * 3
NEWS_LOCK = False
JWKS_CACHE = {'at': 0, 'keys': []}
RATE = defaultdict(deque)

app = FastAPI(title='RE:LAND', version='3.0.0', docs_url='/api/docs' if ENV != 'production' else None, redoc_url=None)
app.mount('/static', StaticFiles(directory=str(ROOT / 'static')), name='static')

REGIONS = [
    ('서울','서울특별시',37.5665,126.9780,'한강권역 및 도심 주요 생활권'),
    ('경기','경기도',37.4138,127.5183,'수도권 신도시·기존 도심'),
    ('인천','인천광역시',37.4563,126.7052,'원도심 정비와 항만 생활권'),
    ('부산','부산광역시',35.1796,129.0756,'해안 도시 주거지 정비'),
    ('대구','대구광역시',35.8714,128.6014,'도심 주거환경 개선'),
    ('대전','대전광역시',36.3504,127.3845,'역세권 및 원도심 변화'),
    ('광주','광주광역시',35.1595,126.8526,'지역 중심 생활권'),
    ('울산','울산광역시',35.5384,129.3114,'도심과 산업 주거권역'),
    ('세종','세종특별자치시',36.4800,127.2890,'행정중심 생활권'),
    ('충북','충청북도',36.6357,127.4914,'청주권 중심 지역'),
    ('충남','충청남도',36.6588,126.6728,'내포권 및 천안·아산권'),
    ('전북','전북특별자치도',35.8242,127.1480,'전주권 중심 지역'),
    ('전남','전라남도',34.8161,126.4630,'목포·순천권 생활권'),
    ('경북','경상북도',36.0190,129.3435,'포항·경주권 생활권'),
    ('경남','경상남도',35.2279,128.6811,'창원·진주권 생활권'),
    ('강원','강원특별자치도',37.8813,127.7298,'춘천·원주권 생활권'),
    ('제주','제주특별자치도',33.4996,126.5312,'제주시·서귀포 생활권'),
]
STAGES = ['정비구역 지정','추진위원회','조합설립인가','사업시행인가','관리처분인가','이주·철거','착공','준공·이전고시']

@contextmanager
def db():
    with open_db(str(DB_PATH)) as con:
        yield con

def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def init_db():
    with db() as c:
        c.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS districts (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, province TEXT NOT NULL,
          city TEXT NOT NULL, stage TEXT NOT NULL, kind TEXT NOT NULL,
          operator TEXT NOT NULL DEFAULT '', households TEXT NOT NULL DEFAULT '',
          lat REAL, lon REAL, precision TEXT NOT NULL DEFAULT 'region_center',
          source_url TEXT NOT NULL DEFAULT '', source_date TEXT NOT NULL DEFAULT '',
          demo INTEGER NOT NULL DEFAULT 0, UNIQUE(name,province,city));
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, google_sub TEXT NOT NULL UNIQUE,
          nickname TEXT NOT NULL, email TEXT NOT NULL DEFAULT '', avatar TEXT NOT NULL DEFAULT '',
          blog_url TEXT NOT NULL DEFAULT '', bio TEXT NOT NULL DEFAULT '',
          role TEXT NOT NULL DEFAULT 'member', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS communities (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, region TEXT NOT NULL,
          description TEXT NOT NULL, blog_url TEXT NOT NULL DEFAULT '', district_id INTEGER REFERENCES districts(id),
          owner_id INTEGER REFERENCES users(id), official INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS follows (
          user_id INTEGER REFERENCES users(id), community_id INTEGER REFERENCES communities(id),
          PRIMARY KEY(user_id,community_id));
        CREATE TABLE IF NOT EXISTS posts (
          id INTEGER PRIMARY KEY AUTOINCREMENT, community_id INTEGER NOT NULL REFERENCES communities(id),
          author_id INTEGER REFERENCES users(id), author_label TEXT NOT NULL DEFAULT '',
          kind TEXT NOT NULL DEFAULT 'discussion', title TEXT NOT NULL, body TEXT NOT NULL,
          demo INTEGER NOT NULL DEFAULT 0, hidden INTEGER NOT NULL DEFAULT 0, resolved INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS comments (
          id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL REFERENCES posts(id),
          author_id INTEGER NOT NULL REFERENCES users(id), body TEXT NOT NULL,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS likes (
          user_id INTEGER NOT NULL REFERENCES users(id), post_id INTEGER NOT NULL REFERENCES posts(id),
          PRIMARY KEY(user_id,post_id));
        CREATE TABLE IF NOT EXISTS bookmarks (
          user_id INTEGER NOT NULL REFERENCES users(id), post_id INTEGER NOT NULL REFERENCES posts(id),
          PRIMARY KEY(user_id,post_id));
        CREATE TABLE IF NOT EXISTS reports (
          id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL REFERENCES posts(id),
          user_id INTEGER NOT NULL REFERENCES users(id), reason TEXT NOT NULL,
          created_at TEXT NOT NULL, UNIQUE(post_id,user_id));
        CREATE TABLE IF NOT EXISTS verification_requests (
          id INTEGER PRIMARY KEY AUTOINCREMENT, community_id INTEGER NOT NULL REFERENCES communities(id),
          user_id INTEGER NOT NULL REFERENCES users(id), note TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL,
          UNIQUE(community_id,user_id));
        CREATE TABLE IF NOT EXISTS consultations (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
          category TEXT NOT NULL, region TEXT NOT NULL, subject TEXT NOT NULL,
          message TEXT NOT NULL, consent INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT '접수', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, target_id INTEGER NOT NULL,
          note TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS news (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
          source TEXT NOT NULL, published TEXT NOT NULL, topic TEXT NOT NULL,
          fetched_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS district_watches (
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          district_id INTEGER NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL, PRIMARY KEY(user_id,district_id));
        CREATE TABLE IF NOT EXISTS district_changes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          district_id INTEGER NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
          old_stage TEXT NOT NULL,new_stage TEXT NOT NULL,
          source_url TEXT NOT NULL,source_date TEXT NOT NULL,detected_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS district_geometries (
          district_id INTEGER PRIMARY KEY REFERENCES districts(id) ON DELETE CASCADE,
          geojson TEXT NOT NULL, source_url TEXT NOT NULL, source_date TEXT NOT NULL,
          recorded_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_changes_district_id ON district_changes(district_id,id);
        CREATE INDEX IF NOT EXISTS idx_watches_user_id ON district_watches(user_id);
        ''')
        # Schema upgrade for databases created before Q&A resolved-status support.
        if not table_has_column(c, 'posts', 'resolved'):
            c.execute('ALTER TABLE posts ADD COLUMN resolved INTEGER NOT NULL DEFAULT 0')
        if not table_has_column(c, 'communities', 'blog_url'):
            c.execute("ALTER TABLE communities ADD COLUMN blog_url TEXT NOT NULL DEFAULT ''")
        if c.execute('SELECT count(*) FROM districts').fetchone()[0] == 0:
            c.executemany('''INSERT INTO districts (name,province,city,stage,kind,lat,lon,precision,source_url,demo)
                VALUES (?,?,?,?,?,?,?,?,?,1)''', [
                (f'{short} 지역 정비사업 안내 허브',full,short,'자료 연결 전','지역 안내',lat,lon,'region_center',
                 'https://www.data.go.kr/data/15160169/fileData.do')
                for short,full,lat,lon,_ in REGIONS
            ])
        if c.execute('SELECT count(*) FROM communities').fetchone()[0] == 0:
            names=[('서울 정비사업 이웃모임','서울','지역별 정비사업 정보와 생활 이야기를 공유합니다.'),
            ('부산 우리동네 변화모임','부산','원도심의 변화와 정책을 함께 살펴봅니다.'),
            ('수도권 입주·이주 정보방','경기','이주 준비, 서류, 정책을 서로 질문합니다.'),
            ('전국 정비사업 열린광장','전국','모두가 참여하는 전국 공통 Q&A 광장입니다.')]
            for name,region,description in names:
                c.execute('INSERT INTO communities(name,region,description,created_at) VALUES(?,?,?,?)',
                          (name,region,description,utcnow()))
            examples=[(1,'discussion','동네의 변화, 어떤 정보부터 확인하면 좋을까요?',
                      '정비사업 진행 단계는 반드시 지자체 고시와 공공 포털의 최신 자료를 함께 확인하세요.'),
                     (3,'question','관리처분인가 이후 어떤 공고를 확인하나요?',
                      '공식 고시문과 조합 공개자료의 날짜·적용대상·이의절차를 확인하세요. 이 게시글은 기능 시연용 예시입니다.'),
                     (4,'discussion','리랜드 게시판 이용 가이드',
                      '주민등록번호, 조합원 명부 등 민감한 개인정보는 게시하지 마세요. 실명 조합 인증은 별도 검증 절차가 필요합니다.')]
            for community, kind,title,body in examples:
                c.execute('INSERT INTO posts(community_id,kind,title,body,demo,author_label,created_at) VALUES(?,?,?,?,1,?,?)',
                          (community,kind,title,body,'리랜드 데모 에디터',utcnow()))
        if not c.execute("SELECT 1 FROM settings WHERE key='news_last_attempt'").fetchone():
            c.execute("INSERT INTO settings(key,value) VALUES('news_last_attempt','0')")

    # Studio tables are also initialized on isolated test DBs and fresh deployments.
    from legal_studio import init_studio_db
    init_studio_db(db)

init_db()

class LoginToken(BaseModel):
    credential: str = Field(min_length=100,max_length=8000)

class NeonSyncBody(BaseModel):
    token: str = Field(default='', max_length=8192)

class UserUpdate(BaseModel):
    nickname: str = Field(min_length=2,max_length=32)
    bio: str = Field(default='',max_length=180)
    blog_url: str = Field(default='',max_length=250)

class CommunityCreate(BaseModel):
    name: str = Field(min_length=3,max_length=60)
    description: str = Field(min_length=8,max_length=450)
    region: str = Field(min_length=2,max_length=20)
    district_id: int | None = None

class CommunityBlogUpdate(BaseModel):
    blog_url: str = Field(default='',max_length=250)

class PostCreate(BaseModel):
    community_id: int
    kind: str = Field(pattern='^(question|discussion|notice)$')
    title: str = Field(min_length=5,max_length=120)
    body: str = Field(min_length=10,max_length=5000)

class CommentCreate(BaseModel):
    body: str = Field(min_length=2,max_length=1600)

class ConsultationCreate(BaseModel):
    category: str = Field(min_length=2,max_length=40)
    region: str = Field(min_length=2,max_length=40)
    subject: str = Field(min_length=5,max_length=100)
    message: str = Field(min_length=20,max_length=3000)
    consent: bool

class ConsultationStatusUpdate(BaseModel):
    status: str = Field(pattern='^(접수|검토중|연락완료|종료)$')
    note: str = Field(min_length=10,max_length=300)

class VerificationCreate(BaseModel):
    note: str = Field(min_length=10,max_length=400)

class ReportCreate(BaseModel):
    reason: str = Field(min_length=5,max_length=240)

class AdminReview(BaseModel):
    note: str = Field(min_length=10,max_length=400)
    approved: bool = False

class AccountDelete(BaseModel):
    confirmation: str = Field(pattern='^DELETE MY ACCOUNT$')


def output_user(row):
    if not row: return None
    return {key: row[key] for key in ('id','nickname','avatar','blog_url','bio','role')}

def get_user(request: Request):
    token=request.cookies.get('reland_session')
    if not token: return None
    hash_token=hashlib.sha256(token.encode()).hexdigest()
    with db() as c:
        row=c.execute('''SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id
            WHERE s.token_hash=? AND s.expires>?''',(hash_token,int(time.time()))).fetchone()
    return dict(row) if row else None

def require_user(request: Request):
    user=get_user(request)
    if not user:raise HTTPException(401,'로그인이 필요합니다.')
    return user

def get_json_row(row):
    return dict(row) if row else None

def create_session(response: Response, user_id: int):
    token=secrets.token_urlsafe(40)
    expiry=int(time.time())+14*86400
    with db() as c:
        c.execute('INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)',
                  (hashlib.sha256(token.encode()).hexdigest(),user_id,expiry))
    response.set_cookie('reland_session',token,max_age=14*86400,httponly=True,
                        secure=COOKIE_SECURE,samesite='lax',path='/')

def _bearer_token(request: Request) -> str:
    auth=request.headers.get('authorization','')
    if auth.lower().startswith('bearer '):
        return auth[7:].strip()
    return ''

def upsert_user_from_neon(claims: dict):
    sub=str(claims.get('sub') or claims.get('id') or '').strip()
    if not sub:raise HTTPException(401,'유효하지 않은 Neon Auth 토큰입니다.')
    nickname=(claims.get('name') or claims.get('email') or '회원')
    if isinstance(nickname,str):nickname=nickname.split('@')[0][:40]
    email=str(claims.get('email') or '')
    avatar=str(claims.get('image') or claims.get('picture') or '')
    with db() as c:
        c.execute('''INSERT INTO users(google_sub,nickname,email,avatar,created_at) VALUES(?,?,?,?,?)
          ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email,avatar=excluded.avatar''',
            ('neon:'+sub,str(nickname),email,avatar,utcnow()))
        row=c.execute('SELECT * FROM users WHERE google_sub=?',('neon:'+sub,)).fetchone()
    return dict(row)

def _rewrite_neon_set_cookie(value: str) -> str:
    v=re.sub(r';\s*Domain=[^;]+','',value,flags=re.I)
    v=re.sub(r';\s*Path=[^;]+','; Path='+NEON_AUTH_PROXY_PREFIX,v,flags=re.I)
    if 'Path=' not in v:
        v+=f'; Path={NEON_AUTH_PROXY_PREFIX}'
    if COOKIE_SECURE and 'Secure' not in v:
        v+='; Secure'
    if 'SameSite=' not in v:
        v+='; SameSite=Lax'
    return v

@app.api_route('/api/neon-auth/{path:path}',methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'])
async def neon_auth_proxy(request: Request,path:str):
    if not NEON_AUTH_BASE_URL:raise HTTPException(503,'Neon Auth가 설정되지 않았습니다.')
    if request.method=='OPTIONS':
        return Response(status_code=204)
    upstream=f"{NEON_AUTH_BASE_URL.rstrip('/')}/{path}"
    if request.url.query:
        upstream+='?'+request.url.query
    hop={'host','content-length','connection','transfer-encoding'}
    headers={k:v for k,v in request.headers.items() if k.lower() not in hop}
    body=await request.body()
    async with httpx.AsyncClient(follow_redirects=False,timeout=45) as client:
        upstream_resp=await client.request(request.method,upstream,headers=headers,content=body)
    response=Response(content=upstream_resp.content,status_code=upstream_resp.status_code)
    skip={'transfer-encoding','connection','content-encoding','content-length'}
    for key,value in upstream_resp.headers.multi_items():
        lower=key.lower()
        if lower in skip:continue
        if lower=='set-cookie':
            response.headers.append('set-cookie',_rewrite_neon_set_cookie(value))
        elif lower not in response.headers:
            response.headers[key]=value
    return response

def validate_blog(url):
    if not url:return ''
    try:
        u=urllib.parse.urlsplit(url)
        host=(u.hostname or '').lower()
        if u.scheme!='https' or not host.endswith('.blogspot.com') or host=='blogspot.com' or u.port is not None or u.username:
            raise ValueError()
        return 'https://'+host+'/'
    except Exception:
        raise HTTPException(422,'Blogger 주소는 https://블로그명.blogspot.com/ 형식만 가능합니다.')

@app.middleware('http')
async def security_headers(request: Request, call_next):
    if request.url.path.startswith('/api/') and request.method in ('POST','PUT','PATCH','DELETE'):
        origin=request.headers.get('origin')
        if origin:
            origin_parsed=urllib.parse.urlsplit(origin)
            host=request.headers.get('x-forwarded-host') or request.headers.get('host','')
            scheme=request.headers.get('x-forwarded-proto') or request.url.scheme
            target=f'{scheme}://{host.split(",")[0].strip()}'
            if origin_parsed.scheme+'://'+origin_parsed.netloc != target:
                return Response('다른 출처의 쓰기 요청은 차단됩니다.',status_code=403)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']=(
      "default-src 'self'; script-src 'self' https://accounts.google.com https://unpkg.com; "
      "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; "
      "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://lh3.googleusercontent.com https://*.googleusercontent.com; "
      "font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://accounts.google.com; "
      "frame-src https://accounts.google.com https://www.youtube.com https://www.youtube-nocookie.com; object-src 'none'; base-uri 'self'; form-action 'self'"
    )
    return response

@app.get('/')
def home(): return FileResponse(ROOT/'static'/'index.html')

def _health_payload():
    return {'status':'ok','service':'RE:LAND','mode':'demo' if DEMO_MODE else 'production'}

@app.get('/api/health')
@app.get('/api/health/', include_in_schema=False)
@app.get('/health', include_in_schema=False)
@app.head('/api/health', include_in_schema=False)
@app.head('/api/health/', include_in_schema=False)
@app.head('/health', include_in_schema=False)
def health():
    return _health_payload()
@app.get('/api/config')
def config():
    return {'google_client_id':GOOGLE_CLIENT_ID,'demo_enabled':DEMO_MODE,'source_count':1566,
            'source_asof':'2026-05-18',
            'neon_auth_enabled':bool(NEON_AUTH_BASE_URL),
            'neon_auth_url':NEON_AUTH_PROXY_PREFIX if NEON_AUTH_BASE_URL else '',
            'notice':'전국 공공데이터 원본 1,566행은 CSV 가져오기 전까지 지도에 표시되지 않습니다.'}
@app.get('/api/auth/me')
def me(request:Request):return {'user':output_user(get_user(request))}


def verify_google_credential(jwt_token: str):
    """Verify RS256 signature, Google issuer, audience, expiry, email verification via Google JWKS."""
    import base64
    def decode(value):return base64.urlsafe_b64decode(value+'='*((4-len(value)%4)%4))
    try:
        a,b,s=jwt_token.split('.')
        head=json.loads(decode(a)); claims=json.loads(decode(b))
        if head.get('alg')!='RS256' or not head.get('kid'):raise ValueError('algorithm')
        if not GOOGLE_CLIENT_ID or claims.get('aud')!=GOOGLE_CLIENT_ID:raise ValueError('audience')
        if claims.get('iss') not in ('accounts.google.com','https://accounts.google.com'):raise ValueError('issuer')
        now=int(time.time())
        if int(claims.get('exp',0))<=now or int(claims.get('iat',0))>now+90:raise ValueError('timing')
        if claims.get('email_verified') not in (True,'true'):raise ValueError('email')
        if not claims.get('sub'):raise ValueError('sub')
        if JWKS_CACHE['at'] < time.time()-3600:
            r=httpx.get('https://www.googleapis.com/oauth2/v3/certs',timeout=8,follow_redirects=False)
            r.raise_for_status(); keys=r.json().get('keys',[])
            JWKS_CACHE.update({'at':time.time(),'keys':keys})
        matching=next((k for k in JWKS_CACHE['keys'] if k.get('kid')==head['kid'] and k.get('kty')=='RSA' and k.get('use')=='sig'),None)
        if not matching:raise ValueError('kid')
        pk=rsa.RSAPublicNumbers(int.from_bytes(decode(matching['e']),'big'),int.from_bytes(decode(matching['n']),'big')).public_key()
        pk.verify(decode(s),(a+'.'+b).encode(),padding.PKCS1v15(),hashes.SHA256())
        return claims
    except Exception as ex:
        raise HTTPException(401,'Google 인증을 확인할 수 없습니다.') from ex

@app.post('/api/auth/google')
def google_login(data:LoginToken,response:Response):
    if not GOOGLE_CLIENT_ID:raise HTTPException(503,'Google OAuth 클라이언트 설정이 필요합니다.')
    info=verify_google_credential(data.credential)
    with db() as c:
        c.execute('''INSERT INTO users(google_sub,nickname,email,avatar,created_at) VALUES(?,?,?,?,?)
          ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email,avatar=excluded.avatar''',
            ('google:'+info['sub'],info.get('given_name') or info.get('name') or '회원',
             info.get('email',''),info.get('picture',''),utcnow()))
        user=c.execute('SELECT * FROM users WHERE google_sub=?',('google:'+info['sub'],)).fetchone()
    create_session(response,user['id'])
    return {'user':output_user(user)}

@app.post('/api/auth/neon/sync')
def neon_sync(request:Request,response:Response,body:NeonSyncBody|None=None):
    if not NEON_AUTH_BASE_URL:raise HTTPException(503,'Neon Auth가 설정되지 않았습니다.')
    token=_bearer_token(request) or (body.token if body else '')
    if not token:raise HTTPException(401,'Neon Auth JWT가 필요합니다.')
    claims=validate_neon_token(token,NEON_AUTH_BASE_URL)
    if not claims:raise HTTPException(401,'Neon Auth 토큰을 확인할 수 없습니다.')
    user=upsert_user_from_neon(claims)
    create_session(response,user['id'])
    return {'user':output_user(user)}

@app.post('/api/auth/demo')
def demo_login(request:Request,response:Response):
    if not DEMO_MODE or request.client is None or request.client.host not in ('127.0.0.1','::1','localhost','testclient','testserver'):
        raise HTTPException(403,'데모 계정은 로컬 개발 환경에서만 사용할 수 있습니다.')
    with db() as c:
        c.execute("INSERT OR IGNORE INTO users(google_sub,nickname,created_at) VALUES('demo:local','리랜드 체험회원',?)",(utcnow(),))
        user=c.execute("SELECT * FROM users WHERE google_sub='demo:local'").fetchone()
    create_session(response,user['id'])
    return {'user':output_user(user)}

@app.post('/api/auth/logout')
def logout(request:Request,response:Response):
    token=request.cookies.get('reland_session')
    if token:
        with db() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie('reland_session',path='/')
    return {'ok':True}

@app.put('/api/auth/profile')
def update_profile(data:UserUpdate,request:Request):
    u=require_user(request)
    blog=validate_blog(data.blog_url)
    with db() as c:
        c.execute('UPDATE users SET nickname=?,bio=?,blog_url=? WHERE id=?',
                  (data.nickname.strip(),data.bio.strip(),blog,u['id']))
    return {'ok':True}

@app.get('/api/districts')
def districts(q:str='',region:str='',kind:str='',stage:str='',limit:int=2000):
    limit=max(1,min(limit,3000))
    sql='SELECT * FROM districts WHERE 1=1'; args=[]
    if q:
        sql+=' AND (name LIKE ? OR city LIKE ? OR province LIKE ?)';args.extend(['%'+q[:80]+'%']*3)
    if region and region!='전국':
        sql+=' AND (province LIKE ? OR city LIKE ?)';args.extend(['%'+region+'%']*2)
        sql+=' AND demo=0'
    if kind and kind!='전체':
        kind_patterns={
            '재개발사업':'%재개발%',
            '재건축사업':'%재건축%',
            '주거환경개선사업':'%주거환경%',
            '지역 안내':'%지역%안내%',
        }
        pat=kind_patterns.get(kind,kind)
        sql+=' AND kind LIKE ?';args.append(pat)
    if stage and stage!='전체':
        sql+=' AND stage LIKE ?';args.append('%'+stage.replace('·','%')+'%')
    sql+=' ORDER BY demo ASC, id DESC LIMIT ?'; args.append(limit)
    with db() as c:
        items=[dict(r) for r in c.execute(sql,args).fetchall()]
        total=c.execute('SELECT COUNT(*) FROM districts WHERE demo=0').fetchone()[0]
    return {'items':items,'verified_data_rows':total,'shown':len(items),
            'message':'시연용 지역 허브는 실제 정비구역 또는 경계를 뜻하지 않습니다.'}

@app.get('/api/districts/{district_id}')
def district_detail(district_id:int):
    with db() as c:row=c.execute('SELECT * FROM districts WHERE id=?',(district_id,)).fetchone()
    if not row:raise HTTPException(404,'찾을 수 없는 정비사업입니다.')
    return get_json_row(row)

@app.get('/api/districts/{district_id}/geometry')
def district_geometry(district_id:int):
    """Serve only manually curated WGS84 polygons linked to a public source."""
    with db() as c:
        item=c.execute('SELECT geojson,source_url,source_date FROM district_geometries WHERE district_id=?',(district_id,)).fetchone()
    if not item:raise HTTPException(404,'검증된 구역 경계가 없습니다.')
    return {'feature':json.loads(item['geojson']),'source_url':item['source_url'],'source_date':item['source_date'],'precision':'boundary_polygon'}

@app.get('/api/map/boundaries')
def map_boundaries(limit:int=250):
    with db() as c:
        rows=c.execute('''SELECT g.district_id,g.geojson,g.source_url,g.source_date
             FROM district_geometries g JOIN districts d ON d.id=g.district_id
             WHERE d.demo=0 ORDER BY g.district_id LIMIT ?''',(max(1,min(limit,1000)),)).fetchall()
    return {'items':[{'district_id':r['district_id'],'feature':json.loads(r['geojson']),
        'source_url':r['source_url'],'source_date':r['source_date']} for r in rows],
        'notice':'공간정보 원본을 별도로 확인하고 등록한 구역만 반환합니다.'}

@app.post('/api/districts/{district_id}/watch')
def toggle_district_watch(district_id:int,request:Request):
    u=require_user(request)
    with db() as c:
        row=c.execute('SELECT id,demo FROM districts WHERE id=?',(district_id,)).fetchone()
        if not row:raise HTTPException(404,'구역을 찾을 수 없습니다.')
        if row['demo']:raise HTTPException(422,'시연 지역 허브는 실제 정비구역이 아니므로 추적할 수 없습니다.')
        watched=c.execute('SELECT 1 FROM district_watches WHERE user_id=? AND district_id=?',
                          (u['id'],district_id)).fetchone()
        if watched:c.execute('DELETE FROM district_watches WHERE user_id=? AND district_id=?',(u['id'],district_id))
        else:c.execute('INSERT INTO district_watches VALUES(?,?,?)',(u['id'],district_id,utcnow()))
    return {'watching':not bool(watched),'notice':'관심 구역의 변경 내역은 내 활동 페이지에서 확인할 수 있습니다. 푸시 알림은 아직 제공하지 않습니다.'}

@app.get('/api/my/dashboard')
def my_dashboard(request:Request):
    u=require_user(request)
    with db() as c:
        watches=[dict(r) for r in c.execute('''SELECT d.id,d.name,d.province,d.city,d.stage,d.source_date,w.created_at
             FROM district_watches w JOIN districts d ON d.id=w.district_id
             WHERE w.user_id=? ORDER BY w.created_at DESC LIMIT 100''',(u['id'],)).fetchall()]
        changes=[dict(r) for r in c.execute('''SELECT ch.id,d.id AS district_id,d.name,d.province,
             ch.old_stage,ch.new_stage,ch.source_date,ch.source_url,ch.detected_at
             FROM district_changes ch JOIN district_watches w ON w.district_id=ch.district_id
             JOIN districts d ON d.id=ch.district_id
             WHERE w.user_id=? AND ch.detected_at>=w.created_at
             ORDER BY ch.id DESC LIMIT 100''',(u['id'],)).fetchall()]
        consultations=[dict(r) for r in c.execute('''SELECT id,category,region,subject,status,created_at
             FROM consultations WHERE user_id=? ORDER BY id DESC LIMIT 50''',(u['id'],)).fetchall()]
        counts={}
        counts['posts']=c.execute('SELECT COUNT(*) FROM posts WHERE author_id=? AND hidden=0 AND demo=0',(u['id'],)).fetchone()[0]
        counts['comments']=c.execute('''SELECT COUNT(*) FROM comments c JOIN posts p ON p.id=c.post_id
             WHERE c.author_id=? AND p.hidden=0''',(u['id'],)).fetchone()[0]
        counts['follows']=c.execute('SELECT COUNT(*) FROM follows WHERE user_id=?',(u['id'],)).fetchone()[0]
    score=min(counts['posts'],20)*8+min(counts['comments'],30)*3+min(counts['follows'],15)*2+min(len(watches),15)*5
    badges=[]
    if watches:badges.append('우리동네 탐험가')
    if counts['posts']>=1:badges.append('첫 이야기')
    if counts['comments']>=3:badges.append('소통 이웃')
    if counts['follows']>=3:badges.append('모임 길잡이')
    return {'watches':watches,'changes':changes,'consultations':consultations,
      'engagement':{'score':score,'badges':badges,'counts':counts},
      'notice':'참여 포인트는 게임형 커뮤니티 지표일 뿐 조합원 자격·법률적 권리와 무관합니다.'}

@app.get('/api/stats')
def stats():
    with db() as c:
        real=c.execute('SELECT COUNT(*) FROM districts WHERE demo=0').fetchone()[0]
        community=c.execute('SELECT COUNT(*) FROM communities').fetchone()[0]
        post=c.execute('SELECT COUNT(*) FROM posts WHERE hidden=0 AND demo=0').fetchone()[0]
        news=c.execute('SELECT COUNT(*) FROM news').fetchone()[0]
    return {'districts':real,'communities':community,'posts':post,'news':news,'official_catalog_rows':1566}

@app.get('/api/communities')
def communities(q:str='',region:str=''):
    sql='''SELECT c.*, (SELECT COUNT(*) FROM follows WHERE community_id=c.id) AS followers,
       (SELECT COUNT(*) FROM posts WHERE community_id=c.id AND hidden=0) AS post_count
       FROM communities c WHERE 1=1'''; params=[]
    if q:sql+=' AND (c.name LIKE ? OR c.description LIKE ?)';params.extend(['%'+q[:80]+'%']*2)
    if region and region!='전국':sql+=' AND (c.region=? OR c.region=?)';params.extend([region,'전국'])
    sql+=' ORDER BY followers DESC,c.id DESC'
    with db() as c:items=[dict(r) for r in c.execute(sql,params).fetchall()]
    return {'items':items}

@app.post('/api/communities',status_code=201)
def create_community(data:CommunityCreate,request:Request):
    u=require_user(request)
    with db() as c:
        if data.district_id and not c.execute('SELECT 1 FROM districts WHERE id=?',(data.district_id,)).fetchone():raise HTTPException(404,'지역 정보가 없습니다.')
        cur=c.execute('INSERT INTO communities(name,region,description,district_id,owner_id,created_at) VALUES(?,?,?,?,?,?)',
                      (data.name.strip(),data.region.strip(),data.description.strip(),data.district_id,u['id'],utcnow()))
        c.execute('INSERT INTO follows(user_id,community_id) VALUES(?,?)',(u['id'],cur.lastrowid))
        return {'id':cur.lastrowid,'official':False}

@app.get('/api/communities/{community_id}')
def community_detail(community_id:int,request:Request):
    u=get_user(request)
    with db() as c:
        row=c.execute('SELECT * FROM communities WHERE id=?',(community_id,)).fetchone()
        if not row:raise HTTPException(404,'없는 커뮤니티입니다.')
        count=c.execute('SELECT COUNT(*) FROM follows WHERE community_id=?',(community_id,)).fetchone()[0]
        following=bool(u and c.execute('SELECT 1 FROM follows WHERE community_id=? AND user_id=?',(community_id,u['id'])).fetchone())
    with db() as c:
        verification=c.execute('SELECT status FROM verification_requests WHERE community_id=? AND user_id=?',(community_id,u['id'])).fetchone() if u else None
    return {'item':dict(row),'followers':count,'following':following,'verification_status':verification['status'] if verification else None}

@app.put('/api/communities/{community_id}/blog')
def set_community_blog(community_id:int,data:CommunityBlogUpdate,request:Request):
    u=require_user(request)
    blog=validate_blog(data.blog_url)
    with db() as c:
        row=c.execute('SELECT owner_id FROM communities WHERE id=?',(community_id,)).fetchone()
        if not row:raise HTTPException(404,'없는 커뮤니티입니다.')
        if row['owner_id'] != u['id']:raise HTTPException(403,'모임 운영자만 공개 블로그 링크를 등록할 수 있습니다.')
        c.execute('UPDATE communities SET blog_url=? WHERE id=?',(blog,community_id))
    return {'ok':True,'blog_url':blog,'verified_blog_owner':False}

@app.get('/api/communities/{community_id}/blog')
def community_blog(community_id:int):
    with db() as c:
        row=c.execute('SELECT blog_url FROM communities WHERE id=?',(community_id,)).fetchone()
    if not row:raise HTTPException(404,'없는 커뮤니티입니다.')
    if not row['blog_url']:return {'items':[],'notice':'공개 Blogger 피드가 연결되지 않았습니다.'}
    return blog_preview(row['blog_url'])

@app.post('/api/communities/{community_id}/follow')
def follow(community_id:int,request:Request):
    u=require_user(request)
    with db() as c:
        if not c.execute('SELECT 1 FROM communities WHERE id=?',(community_id,)).fetchone():raise HTTPException(404,'없는 커뮤니티입니다.')
        present=c.execute('SELECT 1 FROM follows WHERE user_id=? AND community_id=?',(u['id'],community_id)).fetchone()
        if present:c.execute('DELETE FROM follows WHERE user_id=? AND community_id=?',(u['id'],community_id))
        else:c.execute('INSERT INTO follows(user_id,community_id) VALUES(?,?)',(u['id'],community_id))
    return {'following':not bool(present),'notice':'팔로우는 법적 조합원 자격 인증과 무관합니다.'}

@app.post('/api/communities/{community_id}/verification')
def request_verification(community_id:int,data:VerificationCreate,request:Request):
    u=require_user(request)
    with db() as c:
        if not c.execute('SELECT 1 FROM communities WHERE id=?',(community_id,)).fetchone():raise HTTPException(404,'없는 커뮤니티입니다.')
        c.execute('''INSERT INTO verification_requests(community_id,user_id,note,status,created_at) VALUES(?,?,?,'pending',?)
             ON CONFLICT(community_id,user_id) DO UPDATE SET note=excluded.note,status='pending',created_at=excluded.created_at''',
                  (community_id,u['id'],data.note.strip(),utcnow()))
    return {'ok':True,'message':'인증 요청만 접수되었습니다. 조합원 자격은 확인되지 않았습니다.'}

@app.get('/api/posts')
def posts(request:Request,community_id:int|None=None,kind:str='',q:str='',limit:int=50):
    u=get_user(request)
    sql='''SELECT p.*,c.name AS community_name,c.region,u.nickname AS nickname,u.avatar AS avatar,
     (SELECT COUNT(*) FROM likes WHERE post_id=p.id) AS like_count,
     (SELECT COUNT(*) FROM comments WHERE post_id=p.id) AS comment_count'''
    sql+=', (SELECT COUNT(*) FROM likes WHERE post_id=p.id AND user_id=?) AS liked' if u else ', 0 AS liked'
    sql+=', (SELECT COUNT(*) FROM bookmarks WHERE post_id=p.id AND user_id=?) AS bookmarked' if u else ', 0 AS bookmarked'
    sql+=' FROM posts p JOIN communities c ON c.id=p.community_id LEFT JOIN users u ON u.id=p.author_id WHERE p.hidden=0'
    args=[u['id'],u['id']] if u else []
    if community_id:sql+=' AND p.community_id=?';args.append(community_id)
    if kind in ('question','discussion','notice'):sql+=' AND p.kind=?';args.append(kind)
    if q:sql+=' AND (p.title LIKE ? OR p.body LIKE ?)';args.extend(['%'+q[:90]+'%']*2)
    sql+=' ORDER BY p.id DESC LIMIT ?';args.append(max(1,min(limit,100)))
    with db() as c:items=[dict(row) for row in c.execute(sql,args).fetchall()]
    return {'items':items}


def throttle(request,key,limit=8,window=60):
    ip=request.client.host if request.client else 'unknown'; now=time.time()
    q=RATE[(ip,key)]
    while q and q[0]<now-window:q.popleft()
    if len(q)>=limit:raise HTTPException(429,'요청이 너무 많습니다. 잠시 후 다시 시도하세요.')
    q.append(now)

@app.post('/api/posts',status_code=201)
def create_post(data:PostCreate,request:Request):
    u=require_user(request);throttle(request,'post',6,60)
    with db() as c:
        if not c.execute('SELECT 1 FROM communities WHERE id=?',(data.community_id,)).fetchone():raise HTTPException(404,'커뮤니티가 없습니다.')
        cur=c.execute('INSERT INTO posts(community_id,author_id,kind,title,body,created_at) VALUES(?,?,?,?,?,?)',
                      (data.community_id,u['id'],data.kind,data.title.strip(),data.body.strip(),utcnow()))
    return {'id':cur.lastrowid}

@app.get('/api/posts/{post_id}')
def post_detail(post_id:int,request:Request):
    with db() as c:
        row=c.execute('''SELECT p.*,co.name community_name,u.nickname nickname FROM posts p
            JOIN communities co ON co.id=p.community_id LEFT JOIN users u ON p.author_id=u.id
            WHERE p.id=? AND p.hidden=0''',(post_id,)).fetchone()
        if not row:raise HTTPException(404,'게시글이 없습니다.')
        comments=[dict(r) for r in c.execute('''SELECT cm.*,u.nickname FROM comments cm JOIN users u ON u.id=cm.author_id
            WHERE cm.post_id=? ORDER BY cm.id''',(post_id,))]
    return {'item':dict(row),'comments':comments}

@app.post('/api/posts/{post_id}/comments',status_code=201)
def add_comment(post_id:int,data:CommentCreate,request:Request):
    u=require_user(request);throttle(request,'comment',12,60)
    with db() as c:
        if not c.execute('SELECT 1 FROM posts WHERE id=? AND hidden=0',(post_id,)).fetchone():raise HTTPException(404,'게시글이 없습니다.')
        cur=c.execute('INSERT INTO comments(post_id,author_id,body,created_at) VALUES(?,?,?,?)',
                      (post_id,u['id'],data.body.strip(),utcnow()))
    return {'id':cur.lastrowid}

@app.post('/api/posts/{post_id}/like')
@app.post('/api/posts/{post_id}/bookmark')
def toggle_post(post_id:int,request:Request):
    action=request.url.path.rsplit('/',1)[-1]
    if action not in ('like','bookmark'):raise HTTPException(404,'잘못된 기능입니다.')
    u=require_user(request)
    table='likes' if action=='like' else 'bookmarks'
    with db() as c:
        if not c.execute('SELECT 1 FROM posts WHERE id=? AND hidden=0',(post_id,)).fetchone():raise HTTPException(404,'게시글이 없습니다.')
        present=c.execute(f'SELECT 1 FROM {table} WHERE user_id=? AND post_id=?',(u['id'],post_id)).fetchone()
        if present:c.execute(f'DELETE FROM {table} WHERE user_id=? AND post_id=?',(u['id'],post_id))
        else:c.execute(f'INSERT INTO {table}(user_id,post_id) VALUES(?,?)',(u['id'],post_id))
    return {'active':not bool(present)}

@app.post('/api/posts/{post_id}/report')
def report_post(post_id:int,data:ReportCreate,request:Request):
    u=require_user(request);throttle(request,'report',5,3600)
    with db() as c:
        if not c.execute('SELECT 1 FROM posts WHERE id=?',(post_id,)).fetchone():raise HTTPException(404,'게시글이 없습니다.')
        c.execute('INSERT OR IGNORE INTO reports(post_id,user_id,reason,created_at) VALUES(?,?,?,?)',
                  (post_id,u['id'],data.reason.strip(),utcnow()))
    return {'ok':True,'message':'운영자 검토 대상으로 접수되었습니다.'}

@app.post('/api/consultations',status_code=201)
def consultation(data:ConsultationCreate,request:Request):
    u=require_user(request);throttle(request,'consultation',3,3600)
    if not data.consent:raise HTTPException(422,'상담 접수 및 연락을 위한 개인정보 처리에 동의해야 합니다.')
    with db() as c:
        cur=c.execute('''INSERT INTO consultations(user_id,category,region,subject,message,consent,created_at)
            VALUES(?,?,?,?,?,1,?)''',(u['id'],data.category,data.region,data.subject.strip(),data.message.strip(),utcnow()))
        cid=cur.lastrowid
    # SMTP is intentionally optional: no claim of professional match if not configured.
    if os.getenv('SMTP_HOST') and os.getenv('CONSULTATION_NOTIFY_EMAIL'):
        try:email_consultation(cid,data)
        except Exception:pass
    return {'id':cid,'status':'접수','notice':'상담 요청 접수이며 전문가 배정·법률자문 제공을 의미하지 않습니다.'}

def email_consultation(cid,data):
    msg=EmailMessage()
    msg['Subject']=f'[리랜드] 새 전문가 상담 요청 #{cid}'
    msg['From']=os.getenv('SMTP_FROM',os.getenv('SMTP_USER','noreply@example.com'))
    msg['To']=os.getenv('CONSULTATION_NOTIFY_EMAIL')
    msg.set_content(f'번호: {cid}\n유형: {data.category}\n지역: {data.region}\n제목: {data.subject}\n내용: {data.message}')
    host=os.environ['SMTP_HOST'];port=int(os.getenv('SMTP_PORT','587'))
    with smtplib.SMTP(host,port,timeout=8) as s:
        s.starttls();s.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD']);s.send_message(msg)

@app.post('/api/posts/{post_id}/resolve')
def resolve_question(post_id:int,request:Request):
    u=require_user(request)
    with db() as c:
        row=c.execute('SELECT author_id,kind,resolved FROM posts WHERE id=? AND hidden=0',(post_id,)).fetchone()
        if not row:raise HTTPException(404,'게시글이 없습니다.')
        if row['author_id']!=u['id'] or row['kind']!='question':raise HTTPException(403,'질문 작성자만 답변 완료 처리할 수 있습니다.')
        next_status=0 if row['resolved'] else 1
        c.execute('UPDATE posts SET resolved=? WHERE id=?',(next_status,post_id))
    return {'resolved':bool(next_status)}

@app.delete('/api/posts/{post_id}')
def delete_post(post_id:int,request:Request):
    u=require_user(request)
    with db() as c:
        row=c.execute('SELECT author_id FROM posts WHERE id=? AND hidden=0',(post_id,)).fetchone()
        if not row:raise HTTPException(404,'게시글이 없습니다.')
        if row['author_id']!=u['id']:raise HTTPException(403,'본인의 글만 삭제할 수 있습니다.')
        c.execute('UPDATE posts SET hidden=1 WHERE id=?',(post_id,))
    return {'ok':True}

@app.delete('/api/auth/account')
def delete_account(data:AccountDelete,request:Request,response:Response):
    u=require_user(request)
    with db() as c:
        c.execute('UPDATE posts SET author_id=NULL,author_label=? WHERE author_id=?',('탈퇴한 회원',u['id']))
        c.execute('UPDATE communities SET owner_id=NULL WHERE owner_id=?',(u['id'],))
        for table in ('comments','likes','bookmarks','follows','reports','verification_requests','consultations','sessions','district_watches'):
            c.execute(f'DELETE FROM {table} WHERE '+('author_id' if table=='comments' else 'user_id')+'=?',(u['id'],))
        c.execute('DELETE FROM users WHERE id=?',(u['id'],))
    response.delete_cookie('reland_session',path='/')
    return {'deleted':True,'notice':'계정과 연결된 활동 일부를 삭제하고 게시글은 탈퇴한 회원으로 익명화했습니다.'}

NEWS_QUERIES=[('재개발','재개발 정비사업'),('정책','도시정비법 재개발 정책'),('조합','재개발 조합 관리처분')]

def parse_rss(xml_text,topic):
    root=ET.fromstring(xml_text)
    out=[]
    for item in root.findall('.//item')[:20]:
        def t(tag):return (item.findtext(tag) or '').strip()
        title=t('title');url=t('link');source=t('source') or 'Google 뉴스 검색';published=t('pubDate')
        if title and url.startswith('https://') and len(title)<=400:
            out.append({'title':title,'url':url,'source':source[:120],'published':published[:100],'topic':topic})
    return out

def refresh_news():
    global NEWS_LOCK
    if NEWS_LOCK:return 0
    NEWS_LOCK=True
    count=0
    try:
        with httpx.Client(timeout=8,follow_redirects=False,headers={'User-Agent':'RELAND-InfoPortal/1.0'}) as client:
            for topic,query in NEWS_QUERIES:
                url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'ko','gl':'KR','ceid':'KR:ko'})
                try:
                    resp=client.get(url);resp.raise_for_status()
                    if len(resp.content)>1_000_000:continue
                    for item in parse_rss(resp.text,topic):
                        with db() as c:
                            c.execute('''INSERT OR IGNORE INTO news(title,url,source,published,topic,fetched_at)
                                VALUES(?,?,?,?,?,?)''',(*item.values(),utcnow()))
                        count+=1
                except (httpx.HTTPError,ET.ParseError):continue
        with db() as c:
            c.execute("INSERT INTO settings(key,value) VALUES('news_last_attempt',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(str(time.time()),))
            c.execute('DELETE FROM news WHERE id NOT IN (SELECT id FROM news ORDER BY id DESC LIMIT 250)')
    finally:NEWS_LOCK=False
    return count

@app.get('/api/news')
def news(background_tasks:BackgroundTasks,topic:str='',limit:int=35):
    with db() as c:
        last=float(c.execute("SELECT value FROM settings WHERE key='news_last_attempt'").fetchone()[0])
        sql='SELECT * FROM news';args=[]
        if topic and topic!='전체':sql+=' WHERE topic=?';args.append(topic)
        sql+=' ORDER BY id DESC LIMIT ?';args.append(max(1,min(limit,100)))
        rows=[dict(r) for r in c.execute(sql,args).fetchall()]
    if time.time()-last>NEWS_TTL and not NEWS_LOCK:background_tasks.add_task(refresh_news)
    return {'items':rows,'last_attempt':datetime.fromtimestamp(last,timezone.utc).isoformat() if last else None,
            'status':'live_cache' if rows else 'awaiting_feed',
            'notice':'뉴스 제목과 원문 링크만 제공하며, 기사 본문을 복제하지 않습니다.'}

@app.get('/api/blog/preview')
def blog_preview(url:str):
    parsed=validate_blog(url)
    feed_url=parsed+'feeds/posts/default?alt=rss&max-results=5'
    try:
        r=httpx.get(feed_url,timeout=6,follow_redirects=False,headers={'User-Agent':'RELAND/1.0'})
        r.raise_for_status()
        if len(r.content)>1_000_000:raise HTTPException(413,'Blogger 공개 피드가 지나치게 큽니다.')
        root=ET.fromstring(r.text)
        return {'items':parse_rss(ET.tostring(root,encoding='unicode'),'블로그'),'source':parsed,'verified_owner':False}
    except Exception:raise HTTPException(502,'블로그 공개 피드를 가져오지 못했습니다. 주소와 공개 설정을 확인하세요.')

@app.get('/api/admin/reports')
def admin_reports(request:Request):
    if not ADMIN_KEY or not hmac.compare_digest(request.headers.get('x-admin-key',''),ADMIN_KEY):raise HTTPException(403,'관리자 권한이 없습니다.')
    with db() as c:
        reports=[dict(r) for r in c.execute('''SELECT r.*,p.title,u.nickname FROM reports r JOIN posts p ON p.id=r.post_id
            JOIN users u ON u.id=r.user_id ORDER BY r.id DESC LIMIT 100''')]
        verifications=[dict(r) for r in c.execute('SELECT * FROM verification_requests WHERE status="pending" LIMIT 100')]
        consultations=[dict(r) for r in c.execute('SELECT id,category,region,subject,status,created_at FROM consultations ORDER BY id DESC LIMIT 100')]
    return {'reports':reports,'verification_requests':verifications,'consultations':consultations}

@app.post('/api/admin/posts/{post_id}/hide')
def admin_hide(post_id:int,request:Request):
    if not ADMIN_KEY or not hmac.compare_digest(request.headers.get('x-admin-key',''),ADMIN_KEY):raise HTTPException(403,'관리자 권한이 없습니다.')
    with db() as c:c.execute('UPDATE posts SET hidden=1 WHERE id=?',(post_id,))
    return {'ok':True}

@app.post('/api/admin/consultations/{consultation_id}/status')
def admin_consultation_status(consultation_id:int,data:ConsultationStatusUpdate,request:Request):
    if not ADMIN_KEY or not hmac.compare_digest(request.headers.get('x-admin-key',''),ADMIN_KEY):
        raise HTTPException(403,'관리자 권한이 없습니다.')
    with db() as c:
        cur=c.execute('UPDATE consultations SET status=? WHERE id=?',(data.status,consultation_id))
        if not cur.rowcount:raise HTTPException(404,'상담 내역을 찾을 수 없습니다.')
        c.execute('INSERT INTO audit_events(action,target_id,note,created_at) VALUES(?,?,?,?)',
             ('consultation_status_'+data.status,consultation_id,data.note,utcnow()))
    return {'ok':True,'status':data.status,'notice':'상태 변경이며 전문가 자격·배정 증빙을 의미하지 않습니다.'}

@app.post('/api/admin/verification/{request_id}/review')
def admin_verification_review(request_id:int,data:AdminReview,request:Request):
    if not ADMIN_KEY or not hmac.compare_digest(request.headers.get('x-admin-key',''),ADMIN_KEY):
        raise HTTPException(403,'관리자 권한이 없습니다.')
    with db() as c:
        row=c.execute('SELECT 1 FROM verification_requests WHERE id=?',(request_id,)).fetchone()
        if not row:raise HTTPException(404,'인증 요청이 없습니다.')
        status='approved' if data.approved else 'rejected'
        c.execute('UPDATE verification_requests SET status=? WHERE id=?',(status,request_id))
        c.execute('INSERT INTO audit_events(action,target_id,note,created_at) VALUES(?,?,?,?)',
                  ('member_review_'+status,request_id,data.note,utcnow()))
    return {'status':status,'note':'승인은 해당 사용자 확인 상태만 변경합니다. 법정 조합원 지위를 부여하지 않습니다.'}

@app.post('/api/admin/communities/{community_id}/official')
def admin_community_official(community_id:int,data:AdminReview,request:Request):
    if not ADMIN_KEY or not hmac.compare_digest(request.headers.get('x-admin-key',''),ADMIN_KEY):
        raise HTTPException(403,'관리자 권한이 없습니다.')
    with db() as c:
        if not c.execute('SELECT 1 FROM communities WHERE id=?',(community_id,)).fetchone():
            raise HTTPException(404,'커뮤니티가 없습니다.')
        c.execute('UPDATE communities SET official=? WHERE id=?',(int(data.approved),community_id))
        c.execute('INSERT INTO audit_events(action,target_id,note,created_at) VALUES(?,?,?,?)',
                 ('community_official_'+str(data.approved),community_id,data.note,utcnow()))
    return {'official':bool(data.approved),'notice':'외부 검증자료를 확인한 경우에만 공식 표시를 부여해야 합니다.'}

# Register separately reviewed legal-editorial and expert directory endpoints.
from legal_studio import install as install_legal_studio
install_legal_studio(app,db,get_user,require_user,ADMIN_KEY)

# Search-friendly initial response for each journal article. Draft legal content is noindexed
# until an actual licensed reviewer changes the per-item status and a public domain is set.
@app.get('/column/{article_id}',response_class=HTMLResponse,include_in_schema=False)
def editorial_html(article_id: int):
    from html import escape as esc
    from legal_studio import ARTICLE_BY_ID
    a=ARTICLE_BY_ID.get(article_id)
    if not a:raise HTTPException(404,'원고를 찾을 수 없습니다.')
    raw=(ROOT/'static'/'index.html').read_text(encoding='utf-8')
    title=esc(a['title']+' | RE:LAND 재개발 법률 저널',quote=True)
    description=esc(a['description'][:154],quote=True)
    raw=re.sub(r'<title>[^<]*</title>',f'<title>{title}</title>',raw,count=1)
    raw=re.sub(r'<meta name="description" content="[^"]*">',f'<meta name="description" content="{description}">',raw,count=1)
    # Prevent unreviewed legal material being indexed as authoritative advice.
    reviewed=a['status']=='legally_reviewed'
    robots='index,follow' if reviewed and os.getenv('RELAND_PUBLIC_URL') else 'noindex,follow'
    raw=raw.replace('</head>',f'<meta name="robots" content="{robots}"></head>',1)
    if reviewed and os.getenv('RELAND_PUBLIC_URL'):
        base=os.environ['RELAND_PUBLIC_URL'].rstrip('/')
        if base.startswith('https://'):
            canonical=esc(f'{base}/column/{article_id}',quote=True)
            raw=raw.replace('</head>',f'<link rel="canonical" href="{canonical}"></head>',1)
    excerpt=esc(a['law_excerpt'])
    source=esc(a['law_url'],quote=True)
    # HTML is server-rendered for accessibility and preview; SPA enhances it after JS loads.
    fallback='<article class="shell page-body"><h1>'+title+'</h1><p>'+description+'</p>'+''.join('<p>'+esc(part)+'</p>' for part in a['body'].split('\n\n'))+'<h2>법령 원문 발췌</h2><blockquote>'+excerpt+'</blockquote><a href="'+source+'">국가법령정보센터 원문 열기</a><p>전문가 감수 전 편집 초안입니다. 개별 법률 자문이 아닙니다.</p></article>'
    raw=raw.replace('<div class="loading-screen"><div class="loading-dot"></div>리랜드를 준비하고 있어요</div>',fallback,1)
    return HTMLResponse(raw)

# Separate editor brand. Public educational content only; no case intake or paid legal advice.
# Must be registered before SPA catch-all. Independent Blogger-compatible design mock.
app.mount('/kang', StaticFiles(directory=str(ROOT/'kang_blog'), html=True), name='kang-blog')

@app.get('/api/kang/metadata')
def kang_metadata():
    return {'brand':'재개발 강실장','lecture_count':60,'qa_count':30,'review':'editorial_draft','phone':None,
            'contact_email':'kangjunchul8@gmail.com','legal_representation':False,
            'blogger_blog_created':False,'public_blog_published':False}

@app.get('/api/kang/lectures')
def kang_lectures(category:str='',q:str='',limit:int=100):
    rows=json.loads((ROOT/'content'/'kang'/'lectures_60.json').read_text(encoding='utf-8'))
    rows=[x for x in rows if (not category or x['category']==category) and (not q or q in (x['title']+x['summary']))]
    return {'count':len(rows),'items':rows[:max(1,min(limit,100))]}

@app.get('/api/kang/lectures/{lesson_id}')
def kang_lecture(lesson_id:int):
    rows=json.loads((ROOT/'content'/'kang'/'lectures_60.json').read_text(encoding='utf-8'))
    obj=next((x for x in rows if x['id']==lesson_id),None)
    if not obj:raise HTTPException(404,'강의를 찾을 수 없습니다.')
    return obj

@app.get('/api/kang/qa')
def kang_qa(category:str=''):
    rows=json.loads((ROOT/'content'/'kang'/'qa_30.json').read_text(encoding='utf-8'))
    rows=[x for x in rows if not category or x['category']==category]
    return {'count':len(rows),'items':rows}

@app.get('/{full_path:path}',include_in_schema=False)
def spa_fallback(full_path:str):
    if full_path.startswith(('api/','static/')) or '.' in full_path:
        raise HTTPException(404,'Not found')
    return FileResponse(ROOT/'static'/'index.html')

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=int(os.getenv('PORT','8000')))
