"""Run from administrator's local machine with administrator key in env. Never bundle the key in the ZIP."""
import argparse,json,os,sys
import httpx
p=argparse.ArgumentParser(description='RE:LAND 전문가 및 Shorts 관리자 명령')
p.add_argument('command',choices=['applications','approve','reject','stories','approve-story','reject-story','add-short','events'])
p.add_argument('--base',default='http://127.0.0.1:8000')
p.add_argument('--id',type=int)
p.add_argument('--note',default='공식 등록 확인 및 광고 심사 완료 여부 별도 기록')
p.add_argument('--title');p.add_argument('--url');p.add_argument('--category',default='재개발');p.add_argument('--creator',default='권리자 제공')
a=p.parse_args();key=os.environ.get('RELAND_ADMIN_KEY','')
if not key:sys.exit('오류: RELAND_ADMIN_KEY 환경변수 설정 필요')
headers={'X-Admin-Key':key};s=httpx.Client(headers=headers,timeout=25,base_url=a.base)
if a.command=='applications':response=s.get('/api/studio/admin/expert-applications')
elif a.command in ('approve','reject'):
 if not a.id:sys.exit('--id 값 필요')
 response=s.post(f'/api/studio/admin/experts/{a.id}/review',json={'approved':a.command=='approve','note':a.note})
elif a.command=='stories':response=s.get('/api/studio/admin/stories')
elif a.command in ('approve-story','reject-story'):
 if not a.id:sys.exit('--id 값 필요')
 response=s.post(f'/api/studio/admin/stories/{a.id}/review',json={'approved':a.command=='approve-story','note':a.note})
elif a.command=='add-short':
 if not a.url or not a.title:sys.exit('--url, --title 필요')
 response=s.post('/api/studio/admin/videos',json={'title':a.title,'youtube_url':a.url,'category':a.category,'creator':a.creator})
else:response=s.get('/api/studio/admin/events')
print('HTTP',response.status_code)
print(json.dumps(response.json(),ensure_ascii=False,indent=2))
response.raise_for_status()
