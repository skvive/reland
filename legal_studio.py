"""RE:LAND v2 Legal Studio: editorial library & compliance-first directory.
No referral fees, automated lawyer ranking, paid lead transfers or fake expert profiles.
"""
import json, re, hmac, urllib.parse
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
ROOT=Path(__file__).resolve().parent
ARTICLES=json.loads((ROOT/'content'/'columns_120.json').read_text(encoding='utf-8'))
ARTICLE_BY_ID={a['id']:a for a in ARTICLES}
ALLOWED_ROLES=['변호사','법무사','행정사']
ALLOWED_REGIONS=['전국','서울','경기','인천','부산','대구','대전','광주','울산','세종','강원','충북','충남','전북','전남','경북','경남','제주']

def verified_https(url:str,domains=None):
 if not url:return ''
 try:
  u=urllib.parse.urlsplit(url.strip())
  if u.scheme!='https' or not u.hostname or u.username or u.password or u.port:
   raise ValueError('HTTPS URL required')
  if domains and not any(u.hostname.lower()==d or u.hostname.lower().endswith('.'+d) for d in domains):raise ValueError('domain not allowed')
  return u.geturl()
 except Exception:raise HTTPException(422,'정상적인 HTTPS 링크를 입력하세요.')

def clip(s,n):return str(s or '').strip()[:n]

class ExpertApply(BaseModel):
 profession:str
 name:str=Field(min_length=2,max_length=65)
 office:str=Field(min_length=2,max_length=100)
 region:str
 introduction:str=Field(min_length=30,max_length=1800)
 expertise:str=Field(min_length=3,max_length=300)
 phone:str=Field(default='',max_length=30)
 public_email:str=Field(default='',max_length=140)
 website:str=Field(default='',max_length=250)
 blogger:str=Field(default='',max_length=250)
 youtube:str=Field(default='',max_length=250)
 license_note:str=Field(default='',max_length=300)
 consent:bool

class ExpertReview(BaseModel):
 approved:bool
 note:str=Field(min_length=4,max_length=500)

class ExpertStory(BaseModel):
 title:str=Field(min_length=8,max_length=120)
 summary:str=Field(min_length=30,max_length=500)
 body:str=Field(min_length=100,max_length=8000)
 law_url:str=Field(default='',max_length=500)

class ContentReview(BaseModel):
 approved:bool
 note:str=Field(min_length=4,max_length=500)

class VideoCreate(BaseModel):
 title:str=Field(min_length=5,max_length=150)
 youtube_url:str=Field(max_length=250)
 category:str=Field(min_length=2,max_length=80)
 creator:str=Field(min_length=2,max_length=120)
 source_disclaimer:str=Field(default='',max_length=200)

class CampaignCreate(BaseModel):
 expert_id:int
 label:str=Field(default='광고 · 유료 노출',max_length=50)
 starts_at:str=Field(min_length=10,max_length=30)
 ends_at:str=Field(min_length=10,max_length=30)
 placement:str=Field(default='experts',max_length=30)
 note:str=Field(default='',max_length=500)



def init_studio_db(db):
 with db() as c:
  c.executescript('''
    CREATE TABLE IF NOT EXISTS expert_profiles(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
      profession TEXT NOT NULL, name TEXT NOT NULL, office TEXT NOT NULL, region TEXT NOT NULL,
      introduction TEXT NOT NULL, expertise TEXT NOT NULL, phone TEXT NOT NULL, public_email TEXT NOT NULL,
      website TEXT NOT NULL, blogger TEXT NOT NULL, youtube TEXT NOT NULL, license_note TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'pending', reviewed_note TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS expert_stories(
      id INTEGER PRIMARY KEY AUTOINCREMENT, expert_id INTEGER NOT NULL REFERENCES expert_profiles(id) ON DELETE CASCADE,
      title TEXT NOT NULL, summary TEXT NOT NULL, body TEXT NOT NULL, law_url TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending', reviewed_note TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS studio_videos(
      id INTEGER PRIMARY KEY AUTOINCREMENT,video_id TEXT NOT NULL UNIQUE,title TEXT NOT NULL,
      category TEXT NOT NULL,creator TEXT NOT NULL,source_disclaimer TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS studio_campaigns(
      id INTEGER PRIMARY KEY AUTOINCREMENT,expert_id INTEGER NOT NULL REFERENCES expert_profiles(id) ON DELETE CASCADE,
      label TEXT NOT NULL,starts_at TEXT NOT NULL,ends_at TEXT NOT NULL,placement TEXT NOT NULL,
      note TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS studio_events(
      id INTEGER PRIMARY KEY AUTOINCREMENT,expert_id INTEGER NOT NULL REFERENCES expert_profiles(id) ON DELETE CASCADE,
      event_type TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS ix_studio_events_expert ON studio_events(expert_id,event_type);
  ''')

def install(app,db,get_user,require_user,admin_key):
 router=APIRouter(prefix='/api/studio',tags=['legal-studio'])
 init_studio_db(db)
 def admin(request):
  if not admin_key or not hmac.compare_digest(request.headers.get('x-admin-key',''),admin_key):
   raise HTTPException(403,'관리자 권한이 없습니다.')
 def existing_expert(c,uid):return c.execute('SELECT * FROM expert_profiles WHERE user_id=?',(uid,)).fetchone()
 def output_expert(row,sponsored=False):
  out=dict(row)
  out.pop('license_note',None);out.pop('reviewed_note',None);out.pop('user_id',None)
  out['sponsored']=bool(sponsored)
  out['ad_disclosure']='광고 · 유료 노출' if sponsored else ''
  out['credential_notice']='전문자격과 업무 분야는 전문가 주장 및 운영자의 서류 확인을 바탕으로 표시되며, 최신 등록상태는 별도 확인이 필요합니다.'
  return out
 def video_id(url):
  u=urllib.parse.urlsplit(verified_https(url,['youtube.com','youtu.be']))
  if u.hostname and u.hostname.lower().endswith('youtu.be'):
   code=u.path.strip('/')
  else:
   s=u.path.strip('/').split('/')
   code=s[-1] if s[0] in ('shorts','embed','live') and len(s)>=2 else urllib.parse.parse_qs(u.query).get('v',[''])[0]
  if not re.fullmatch(r'[A-Za-z0-9_-]{11}',code):raise HTTPException(422,'YouTube 영상 ID 형식이 아닙니다.')
  return code

 @router.get('/metadata')
 def metadata():return {'column_count':len(ARTICLES),'status':'editorial_review','licensed_legal_review':False,'real_blogger_created':False,'experts_are_real':True,'advertising_policy':'No paid lead brokerage or per-case commissions'}

 @router.get('/columns')
 def columns(q:str='',category:str='',page:int=1,limit:int=12):
  page=max(1,min(page,9999));limit=max(1,min(limit,100))
  items=[a for a in ARTICLES if (not q or q.casefold() in (a['title']+a['body']).casefold()) and (not category or a['category']==category)]
  skip=(page-1)*limit
  short=[{k:a[k] for k in ('id','slug','title','category','angle','description','law_name','law_article','law_url','image','image_alt','date','status','legal_review')} for a in items[skip:skip+limit]]
  return {'total':len(items),'items':short,'page':page,'categories':sorted({a['category'] for a in ARTICLES})}

 @router.get('/columns/{article_id}')
 def column(article_id:int):
  row=ARTICLE_BY_ID.get(article_id)
  if not row:raise HTTPException(404,'글을 찾을 수 없습니다.')
  return row

 @router.post('/experts/apply',status_code=201)
 def apply(data:ExpertApply,request:Request):
  user=require_user(request)
  if data.profession not in ALLOWED_ROLES or data.region not in ALLOWED_REGIONS:raise HTTPException(422,'분야 또는 지역값을 확인하세요.')
  if not data.consent:raise HTTPException(422,'공개 프로필·심사에 동의해야 합니다.')
  if data.phone and not re.fullmatch(r'[0-9 +()\-]{8,30}',data.phone):raise HTTPException(422,'전화번호 형식을 확인하세요.')
  if data.public_email and (not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',data.public_email)):raise HTTPException(422,'공개 이메일 형식을 확인하세요.')
  links=[verified_https(data.website),verified_https(data.blogger,['blogspot.com']),verified_https(data.youtube,['youtube.com','youtu.be'])]
  with db() as c:
   prior=existing_expert(c,user['id'])
   args=(data.profession,data.name.strip(),data.office.strip(),data.region,data.introduction.strip(),data.expertise.strip(),data.phone,data.public_email,*links,data.license_note)
   if prior:
    if prior['status']=='approved':raise HTTPException(409,'승인된 프로필 변경은 운영자 재심사가 필요합니다.')
    c.execute('''UPDATE expert_profiles SET profession=?,name=?,office=?,region=?,introduction=?,expertise=?,phone=?,public_email=?,website=?,blogger=?,youtube=?,license_note=?,status='pending',updated_at=CURRENT_TIMESTAMP WHERE user_id=?''',args+(user['id'],))
    eid=prior['id']
   else:
    eid=c.execute('''INSERT INTO expert_profiles(user_id,profession,name,office,region,introduction,expertise,phone,public_email,website,blogger,youtube,license_note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(user['id'],)+args).lastrowid
  return {'id':eid,'status':'pending','notice':'증빙을 확인하고 관리자가 승인하기 전까지 공개하지 않습니다.'}

 @router.get('/experts/mine')
 def mine(request:Request):
  user=require_user(request)
  with db() as c:r=existing_expert(c,user['id'])
  return {'expert':dict(r) if r else None}

 @router.get('/experts')
 def experts(q:str='',region:str='',profession:str='',limit:int=30):
  with db() as c:
   rows=c.execute('''SELECT * FROM expert_profiles WHERE status='approved' AND (?='' OR region=?) AND (?='' OR profession=?) AND (?='' OR name LIKE ? OR office LIKE ? OR expertise LIKE ?) ORDER BY updated_at DESC,id DESC LIMIT ?''',(region,region,profession,profession,q,f'%{q}%',f'%{q}%',f'%{q}%',max(1,min(limit,100)))).fetchall()
   ads={r['expert_id'] for r in c.execute("SELECT DISTINCT expert_id FROM studio_campaigns WHERE starts_at<=DATE('now') AND ends_at>=DATE('now') AND placement='experts'").fetchall()}
  # Paid campaigns are not used to change organic order; displayed ad attribution only.
  return {'items':[output_expert(r,r['id'] in ads) for r in rows],'notice':'공개된 실제 전문가의 등록·검토된 프로필만 표시합니다. 유료 광고는 광고로 표시하며 검색순위 우대는 하지 않습니다.'}

 @router.get('/experts/analytics')
 def my_analytics(request:Request):
  user=require_user(request)
  with db() as c:
   expert=existing_expert(c,user['id'])
   if not expert:raise HTTPException(404,'전문가 등록 신청 정보가 없습니다.')
   events=c.execute('SELECT event_type,COUNT(*) AS n FROM studio_events WHERE expert_id=? GROUP BY event_type',(expert['id'],)).fetchall()
   articles=c.execute("SELECT status,COUNT(*) AS n FROM expert_stories WHERE expert_id=? GROUP BY status",(expert['id'],)).fetchall()
  return {'expert_id':expert['id'],'status':expert['status'],
          'events':{x['event_type']:x['n'] for x in events},'article_status':{x['status']:x['n'] for x in articles},
          'disclaimer':'서비스 내 비식별 클릭 집계이며 외부 유입·실제 수임 성과 또는 과금 근거가 아닙니다.'}

 @router.get('/experts/{expert_id}')
 def expert_detail(expert_id:int):
  with db() as c:
   r=c.execute("SELECT * FROM expert_profiles WHERE id=? AND status='approved'",(expert_id,)).fetchone()
   stories=c.execute("SELECT id,title,summary,law_url,created_at FROM expert_stories WHERE expert_id=? AND status='approved' ORDER BY id DESC",(expert_id,)).fetchall()
  if not r:raise HTTPException(404,'공개 프로필을 찾을 수 없습니다.')
  return {'expert':output_expert(r),'stories':[dict(x) for x in stories]}

 @router.post('/experts/{expert_id}/event')
 def expert_event(expert_id:int,request:Request,event:str='profile_view'):
  if event not in ('profile_view','official_website_click','phone_click','email_click','blog_click','youtube_click'):raise HTTPException(422,'이벤트 형식이 잘못되었습니다.')
  # Event counts are indicative only and are NEVER used for invoices/referral commissions.
  with db() as c:
   if not c.execute("SELECT 1 FROM expert_profiles WHERE id=? AND status='approved'",(expert_id,)).fetchone():raise HTTPException(404,'전문가를 찾을 수 없습니다.')
   c.execute('INSERT INTO studio_events(expert_id,event_type) VALUES(?,?)',(expert_id,event))
  return {'tracked':True,'billing_metric':False}

 @router.post('/experts/stories',status_code=201)
 def submit_story(data:ExpertStory,request:Request):
  user=require_user(request)
  link=verified_https(data.law_url,['law.go.kr'])
  with db() as c:
   expert=existing_expert(c,user['id'])
   if not expert or expert['status']!='approved':raise HTTPException(403,'승인된 전문가만 원고를 제출할 수 있습니다.')
   sid=c.execute('INSERT INTO expert_stories(expert_id,title,summary,body,law_url) VALUES(?,?,?,?,?)',(expert['id'],data.title,data.summary,data.body,link)).lastrowid
  return {'id':sid,'status':'pending'}

 @router.get('/stories')
 def stories(limit:int=30):
  with db() as c: rows=c.execute("SELECT s.id,s.title,s.summary,s.law_url,s.created_at,e.name AS expert_name,e.profession FROM expert_stories s JOIN expert_profiles e ON s.expert_id=e.id WHERE s.status='approved' AND e.status='approved' ORDER BY s.id DESC LIMIT ?",(max(1,min(limit,100)),)).fetchall()
  return {'items':[dict(x) for x in rows]}

 @router.get('/videos')
 def videos(category:str=''):
  with db() as c: rows=c.execute('SELECT * FROM studio_videos WHERE (?="" OR category=?) ORDER BY id DESC LIMIT 100',(category,category)).fetchall()
  return {'items':[dict(x) for x in rows], 'note':'운영자가 실제 YouTube URL을 검수·등록한 영상만 표시합니다.'}

 @router.get('/admin/expert-applications')
 def admin_applications(request:Request):
  admin(request)
  with db() as c:rows=c.execute('SELECT * FROM expert_profiles ORDER BY id DESC').fetchall()
  return {'items':[dict(x) for x in rows]}

 @router.post('/admin/experts/{expert_id}/review')
 def approve_expert(expert_id:int,data:ExpertReview,request:Request):
  admin(request)
  with db() as c:
   if not c.execute('SELECT 1 FROM expert_profiles WHERE id=?',(expert_id,)).fetchone():raise HTTPException(404,'신청 정보가 없습니다.')
   c.execute('UPDATE expert_profiles SET status=?,reviewed_note=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',('approved' if data.approved else 'rejected',data.note,expert_id))
   c.execute('INSERT INTO audit_events(action,target_id,note,created_at) VALUES(?,?,?,CURRENT_TIMESTAMP)',('expert_review',expert_id,data.note))
  return {'approved':data.approved,'notice':'자격증·등록 상태·광고 내용 확인은 운영자의 책임이며 자동 검증되지 않습니다.'}

 @router.get('/admin/stories')
 def admin_stories(request:Request):
  admin(request)
  with db() as c:rows=c.execute("SELECT * FROM expert_stories ORDER BY id DESC").fetchall()
  return {'items':[dict(x) for x in rows]}

 @router.post('/admin/stories/{story_id}/review')
 def review_story(story_id:int,data:ContentReview,request:Request):
  admin(request)
  with db() as c:
   if not c.execute('SELECT 1 FROM expert_stories WHERE id=?',(story_id,)).fetchone():raise HTTPException(404,'원고가 없습니다.')
   c.execute('UPDATE expert_stories SET status=?,reviewed_note=? WHERE id=?',('approved' if data.approved else 'rejected',data.note,story_id))
  return {'approved':data.approved}

 @router.post('/admin/videos',status_code=201)
 def add_video(data:VideoCreate,request:Request):
  admin(request);code=video_id(data.youtube_url)
  with db() as c:
   try:vid=c.execute('INSERT INTO studio_videos(video_id,title,category,creator,source_disclaimer) VALUES(?,?,?,?,?)',(code,data.title,data.category,data.creator,data.source_disclaimer)).lastrowid
   except Exception:raise HTTPException(409,'이미 등록된 영상입니다.')
  return {'id':vid,'youtube_id':code,'notice':'YouTube 게시자 허락 및 플랫폼 정책 확인은 별도입니다.'}

 @router.post('/admin/campaigns',status_code=201)
 def campaign(data:CampaignCreate,request:Request):
  admin(request)
  if data.starts_at>data.ends_at or data.placement!='experts' or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',data.starts_at) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',data.ends_at):raise HTTPException(422,'광고 기간 및 지면을 확인하세요.')
  if '광고' not in data.label:raise HTTPException(422,'광고 표시가 필요합니다.')
  with db() as c:
   if not c.execute("SELECT 1 FROM expert_profiles WHERE id=? AND status='approved'",(data.expert_id,)).fetchone():raise HTTPException(422,'승인된 전문가에만 광고를 연결할 수 있습니다.')
   cid=c.execute('INSERT INTO studio_campaigns(expert_id,label,starts_at,ends_at,placement,note) VALUES(?,?,?,?,?,?)',(data.expert_id,data.label,data.starts_at,data.ends_at,data.placement,data.note)).lastrowid
  return {'id':cid,'payment_link':None,'notice':'법률 광고 심사 전 광고비 자동 결제 비활성화. 사건 알선 수수료 없음.'}

 @router.get('/admin/events')
 def events(request:Request):
  admin(request)
  with db() as c:rows=c.execute('SELECT expert_id,event_type,COUNT(*) AS count FROM studio_events GROUP BY expert_id,event_type ORDER BY expert_id,event_type').fetchall()
  return {'items':[dict(x) for x in rows],'notice':'표본집계·봇으로 왜곡될 수 있으며 과금에 쓰지 않습니다.'}

 app.include_router(router)
