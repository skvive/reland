"""Opt-in Blogger DRAFT ONLY uploader for 60 lessons / 30 Q&A.
Requires a user-created Blogger blog & Google OAuth Installed App JSON.
Uses no network and no credentials in default dry-run mode.
"""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCOPES=['https://www.googleapis.com/auth/blogger']

def select_items(kind,start,count):
 root=ROOT/'kang_blog'/('lectures' if kind=='lecture' else 'qa')
 for i in range(start,start+count):
  fname=f'lesson-{i:03d}.html' if kind=='lecture' else f'qa-{i:03d}.html'
  p=root/fname
  if not p.is_file():raise ValueError(f'선택한 원고가 없습니다: {p.name}')
  body=p.read_text(encoding='utf-8').split('<article>',1)[-1].split('</article>',1)[0]
  # no local relative imgs or external fetching; only links to verified official sources
  manifest=json.loads((ROOT/'content'/'kang'/('lectures_60.json' if kind=='lecture' else 'qa_30.json')).read_text(encoding='utf-8'))
  item=next(a for a in manifest if a['id']==i)
  yield {'slug':f'{kind}-{i:03d}','title':item.get('title') or item['question'],
         'content':body,'category':item['category'],'type':kind}

def main(argv=None):
 p=argparse.ArgumentParser(description='개설된 Blogger 블로그에 비공개 초안 생성 (기본은 무전송 미리보기)')
 p.add_argument('--kind',choices=('lecture','qa'),default='lecture')
 p.add_argument('--start',type=int,default=1)
 p.add_argument('--count',type=int,default=3)
 p.add_argument('--blog-id')
 p.add_argument('--client-secret')
 p.add_argument('--confirm',action='store_true',help='Google 로그인 후 Blogger 비공개 초안을 실제로 생성')
 a=p.parse_args(argv)
 if a.start<1 or a.count<1 or a.count>10 or a.start+a.count-1>(60 if a.kind=='lecture' else 30):p.error('범위는 1~60강, Q&A 1~30이고 한 번에 최대 10편입니다.')
 items=list(select_items(a.kind,a.start,a.count))
 if not a.confirm:
  print(json.dumps({'mode':'dry_run','network_requests':0,'publish_public':False,'draft_count':len(items),'items':[x['title'] for x in items],'notice':'외부 Google 요청 전혀 없음. 블로그를 생성하거나 공개 게시하지 않음.'},ensure_ascii=False,indent=2));return
 if not a.blog_id or not re.fullmatch(r'[0-9]+',a.blog_id):p.error('실제 게시에는 숫자로 된 Blogger 블로그 ID가 필요합니다.')
 if not a.client_secret or not Path(a.client_secret).is_file():p.error('로컬 OAuth 클라이언트 JSON 경로가 필요합니다.')
 try:
  from google_auth_oauthlib.flow import InstalledAppFlow
  from google.auth.transport.requests import AuthorizedSession
 except ImportError:p.error('pip install -r scripts/requirements-blogger.txt')
 flow=InstalledAppFlow.from_client_secrets_file(a.client_secret,SCOPES)
 creds=flow.run_local_server(port=0,open_browser=True)
 session=AuthorizedSession(creds)
 receipts_path=ROOT/'data'/f'kang_blogger_draft_receipts_{a.blog_id}.json'
 receipts=json.loads(receipts_path.read_text(encoding='utf-8')) if receipts_path.exists() else {}
 for x in items:
  if x['slug'] in receipts:
   print('중복 제외:',x['slug']);continue
  data={'kind':'blogger#post','title':x['title'],'content':x['content'],'labels':['재개발','강실장',x['category'],'감수전']}
  response=session.post(f'https://www.googleapis.com/blogger/v3/blogs/{a.blog_id}/posts',params={'isDraft':'true'},json=data,timeout=35)
  response.raise_for_status()
  result=response.json()
  if str(result.get('status','')).upper()!='DRAFT':raise RuntimeError('응답이 DRAFT가 아니므로 다음 요청 중단')
  receipts[x['slug']]={'post_id':result['id'],'status':'DRAFT'}
  receipts_path.parent.mkdir(exist_ok=True)
  receipts_path.write_text(json.dumps(receipts,ensure_ascii=False,indent=2),encoding='utf-8')
  print('비공개 초안 생성',x['slug']);time.sleep(.2)
 print('완료: 외부에 공개되지 않은 Blogger 초안입니다. 법률 검수 후 관리자가 공개하세요.')

if __name__=='__main__':main()
