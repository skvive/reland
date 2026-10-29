"""Opt-in Blogger v3 DRAFT publisher for an already-created blog.
Never creates a blog. Never publishes publicly: uses isDraft=true. Explicit per-batch --confirm.
Install: pip install -r scripts/requirements-blogger.txt
OAuth installed-app client JSON from Google Cloud Console (do not commit).
"""
import argparse, json, re, sys, html, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'content'/'columns_120.json'
SCOPES=['https://www.googleapis.com/auth/blogger']

def safe_html(article,img_base):
 from html import escape
 parts=['<section class="reland-editorial">',f'<h1>{escape(article["title"])}</h1>',
        '<p><strong>RE:LAND 편집 원고 · 전문가 감수 필요 · 공개 전 검토</strong></p>']
 if img_base:
  asset=article['image'].removeprefix('/static/')
  parts.append(f'<figure><img src="{escape(img_base.rstrip("/")+"/"+asset)}" alt="{escape(article["image_alt"])}"/><figcaption>AI 제작 설명용 이미지 · 실제 정비사업 현장 아님</figcaption></figure>')
 parts += [f'<p>{escape(part)}</p>' for part in article['body'].split('\n\n')]
 parts += [f'<h2>{escape(article["law_name"])} {escape(article["law_article"])} — 원문 발췌</h2>',
           f'<blockquote>{escape(article["law_excerpt"])}</blockquote>',
           f'<p><a href="{escape(article["law_url"])}">국가법령정보센터 조문 원문 및 시행일 확인</a></p>',
           '<p>※ 이 글은 개별 사안의 법률 자문이 아닙니다. 공개 전 전문가의 내용 감수와 최신 법령 확인이 필요합니다.</p>', '</section>']
 return '\n'.join(parts)

def build_request(article,img_base):return {'kind':'blogger#post','title':article['title'],'content':safe_html(article,img_base),'labels':['RELAND','재개발',article['category'],'감수전']}

def main():
 p=argparse.ArgumentParser(description='Blogger에 비공개 초안만 생성하는 옵트인 발행기')
 p.add_argument('--blog-id',help='관리자가 직접 개설한 Blogger blog ID')
 p.add_argument('--client-secret',help='구글 OAuth 데스크톱 클라이언트 JSON 경로')
 p.add_argument('--image-base-url',default='',help='이미지를 실제 공개 호스팅한 https:// 도메인 + /static 접두경로. 비워두면 이미지 없음')
 p.add_argument('--start',type=int,default=1)
 p.add_argument('--count',type=int,default=5)
 p.add_argument('--confirm',action='store_true',help='실제로 Blogger에 비공개 초안 생성')
 args=p.parse_args()
 if args.count<1 or args.count>10: p.error('--count 값은 1부터 10까지')
 if args.image_base_url and not re.match(r'^https://[a-zA-Z0-9][a-zA-Z0-9.-]+(?:/.*)?$',args.image_base_url):p.error('이미지 URL은 HTTPS로 시작해야 합니다')
 items=json.loads(CONTENT.read_text(encoding='utf-8'))
 selected=[x for x in items if args.start<=x['id']<args.start+args.count]
 if not selected:p.error('선택한 원고가 없습니다.')
 if not args.confirm:
  print(json.dumps({'mode':'dry_run','count':len(selected),'titles':[x['title'] for x in selected],'notice':'Blogger에 아무 요청도 보내지 않았습니다. 공개 발행도 하지 않습니다.'},ensure_ascii=False,indent=2));return
 if not args.blog_id or not args.client_secret:p.error('실제 발행에는 --blog-id 와 --client-secret 모두 필요합니다')
 try:
  import requests
  from google_auth_oauthlib.flow import InstalledAppFlow
  from google.auth.transport.requests import AuthorizedSession
 except ImportError:p.error('pip install -r scripts/requirements-blogger.txt 실행 필요')
 path=Path(args.client_secret)
 if not path.exists():p.error('OAuth 클라이언트 JSON 파일이 존재하지 않습니다.')
 flow=InstalledAppFlow.from_client_secrets_file(str(path),SCOPES)
 creds=flow.run_local_server(port=0,open_browser=True,authorization_prompt_message='Blogger에 비공개 초안을 올리려면 아래 주소에서 계정 권한을 승인하세요: {url}')
 session=AuthorizedSession(creds)
 state=ROOT/'data'/f'blogger_draft_receipts_{re.sub(r"[^0-9]","",args.blog_id)}.json'
 receipts=json.loads(state.read_text()) if state.exists() else {}
 for a in selected:
  if a['slug'] in receipts:
   print('SKIP duplicate',a['slug']);continue
  endpoint=f'https://www.googleapis.com/blogger/v3/blogs/{args.blog_id}/posts'
  resp=session.post(endpoint,params={'isDraft':'true'},json=build_request(a,args.image_base_url),timeout=30)
  if resp.status_code not in (200,201):
   print('ERROR',a['slug'],resp.status_code,resp.text[:300]);sys.exit(1)
  result=resp.json()
  if result.get('status','DRAFT') not in ('DRAFT','draft'):
   print('WARNING: API returned unexpected status',result.get('status'));sys.exit(2)
  receipts[a['slug']]={'blogger_post_id':result['id'],'status':result.get('status'),'original_id':a['id']}
  state.parent.mkdir(exist_ok=True);state.write_text(json.dumps(receipts,ensure_ascii=False,indent=2),encoding='utf-8')
  print('CREATED DRAFT',a['slug'],result['id'])
  time.sleep(0.3)
 print('완료: 비공개 초안만 생성했습니다. 공개 발행하려면 Blogger 관리자 화면에서 개별 검토 후 발행하세요.')

if __name__=='__main__':main()
