"""Produce 120 distinct editorial-review drafts. Not a substitute for licensed legal review.
Original text excerpts were checked against national law portal on 2026-10-29.
"""
from pathlib import Path
import json, html, re, csv
from PIL import Image, ImageEnhance
ROOT=Path(__file__).resolve().parents[1]
# Keep source link to exact law portal clause, not anonymous search landing page.
LAWS={
 'zone':{'name':'도시 및 주거환경정비법','article':'제35조제2항','heading':'조합설립인가 등','url':'https://law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1023452023','excerpt':'재개발사업의 추진위원회(제31조제7항에 따라 추진위원회를 구성하지 아니하는 경우에는 토지등소유자를 말한다)가 조합을 설립하려면 토지등소유자의 4분의 3 이상 및 토지면적의 2분의 1 이상의 토지소유자의 동의를 받아'},
 'vote':{'name':'도시 및 주거환경정비법','article':'제45조제1항','heading':'총회의 의결','url':'https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1028206431','excerpt':'다음 각 호의 사항은 총회의 의결을 거쳐야 한다.'},
 'apply':{'name':'도시 및 주거환경정비법','article':'제72조제2항','heading':'분양공고 및 분양신청','url':'https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1020045547','excerpt':'분양신청기간은 통지한 날부터 30일 이상 60일 이내로 하여야 한다.'},
 'plan':{'name':'도시 및 주거환경정비법','article':'제74조제1항','heading':'관리처분계획의 인가 등','url':'https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1032613459','excerpt':'사업시행자는 제72조에 따른 분양신청기간이 종료된 때에는 분양신청의 현황을 기초로 다음 각 호의 사항이 포함된 관리처분계획을 수립하여 시장ㆍ군수등의 인가를 받아야 하며'},
 'disclose':{'name':'도시 및 주거환경정비법','article':'제124조제1항','heading':'관련 자료의 공개 등','url':'https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1032070415','excerpt':'정비사업의 시행에 관한 다음 각 호의 서류 및 관련 자료가 작성되거나 변경된 후 15일 이내에 이를 조합원, 토지등소유자 또는 세입자가 알 수 있도록 인터넷과 그 밖의 방법을 병행하여 공개하여야 한다.'},
 'transfer':{'name':'도시 및 주거환경정비법','article':'제86조제2항','heading':'이전고시 등','url':'https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1029442681','excerpt':'이 경우 대지 또는 건축물을 분양받을 자는 고시가 있은 날의 다음 날에 그 대지 또는 건축물의 소유권을 취득한다.'},
 'lawyer':{'name':'변호사법','article':'제23조제1항','heading':'광고','url':'https://www.law.go.kr/LSW/lsInfoP.do?ancYnChk=0&chrClsCd=010202&efYd=20261002&lsiSeq=290789&urlMode=lsInfoP','excerpt':'변호사ㆍ법무법인ㆍ법무법인(유한) 또는 법무조합(이하 이 조에서 “변호사등”이라 한다)은 자기 또는 그 구성원의 학력, 경력, 주요 취급 업무, 업무 실적, 그 밖에 그 업무의 홍보에 필요한 사항을 신문ㆍ잡지ㆍ방송ㆍ컴퓨터통신 등의 매체를 이용하여 광고할 수 있다.'},
 'notary':{'name':'법무사법','article':'제2조제1항','heading':'업무','url':'https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1026297435','excerpt':'법무사의 업무는 다른 사람이 위임한 다음 각 호의 사무로 한다.'},
 'admin':{'name':'행정사법','article':'제2조제1항','heading':'업무','url':'https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1016817059','excerpt':'행정사는 다른 사람의 위임을 받아 다음 각 호의 업무를 수행한다. 다만, 다른 법률에 따라 제한된 업무는 할 수 없다.'},
}
# (topic, legal anchor, tailored intro, terms to explore)
TOPICS=[
 ('조합설립 절차','zone','재개발 조합설립은 사업단계 판단과 동의 요건 확인에서 출발합니다.', '동의서 원본, 토지등소유자 수, 토지면적의 산정기준'),
 ('총회와 의결','vote','조합의 중요한 결의는 총회가 어떤 사항을 의결했는지와 증빙이 핵심입니다.', '총회 소집공고, 의안, 참석 및 의결 기록'),
 ('분양신청','apply','분양신청 안내는 정해진 기간·대상·자료를 함께 확인해야 합니다.', '분양신청 통지일, 접수기간, 접수증 및 변경공고'),
 ('관리처분계획','plan','관리처분은 분양신청 결과와 비용·권리 배분이 결합되는 과정입니다.', '관리처분안, 감정평가 자료, 총회 의결서, 인가 고시'),
 ('정보공개','disclose','정비사업 정보공개에서 가장 먼저 살펴볼 것은 자료 유형과 작성일입니다.', '공개 대상 자료, 갱신일, 열람 요청 경로'),
 ('이전고시·등기','transfer','완료 단계에서는 공고일과 소유권 변경 시점의 관계를 정확히 확인해야 합니다.', '준공 공고, 이전고시문, 등기부 및 계약 문서'),
 ('주민 참여와 분쟁 예방','vote','주민이 협의하는 과정에서는 공식 결정과 개인의 의견을 엄격히 구별해야 합니다.', '회의 자료, 의사록, 질의회신 기록'),
 ('상담 준비 체크리스트','lawyer','전문가 상담은 질문을 구체화하고 본인의 서류를 최소한으로 정리하는 데서 시작됩니다.', '사건 경위표, 공식 고시 링크, 관련 서면'),
 ('등기·서류 실무','notary','등기·공탁 등은 법무사의 법정 업무범위를 확인하고 필요한 서류를 준비해야 합니다.', '등기사항증명서, 위임장, 권리관계 입증 문서'),
 ('행정 인허가·신청','admin','행정기관의 신청과 서류 처리에서는 업무 권한과 절차를 먼저 나누어야 합니다.', '행정기관 서식, 접수증, 처분통지서'),
 ('전문가 광고·홍보','lawyer','변호사 광고는 정보 제공과 사건 알선 사이의 법적 경계를 점검해야 합니다.', '광고 표시, 객관적 경력 증빙, 연락 경로'),
 ('지역별 공개자료 검증','disclose','같은 정비사업 정보라도 지역과 공고 시점에 따라 확인할 원본이 달라집니다.', '지자체 공보, 공식 정보공개 포털, 고시 번호'),
]
ANGLES=[
 ('처음 확인할 문서 5가지','서류 누락으로 진행단계를 오해하지 않도록 어떤 원본부터 확인할지','공식 문서의 생성기관·발행일·문서번호가 일치하는지'),
 ('조합원과 일반 주민의 관점 차이','권리관계·이해관계가 다를 때 설명 방법을 어떻게 나눌지','열람 가능한 자료와 이해관계인 자격이 구분되는지'),
 ('예고와 확정고시 구별법','계획안·안내문·인가고시를 서로 혼동하지 않는 방법','보도자료가 아니라 법정 효력의 근거가 되는 고시가 있는지'),
 ('날짜 계산 전에 살필 것','게시일과 법적 기산일이 다를 가능성에 어떻게 대비할지','통지일·공고일·수령일과 해당 절차의 법정 기간을 구분했는지'),
 ('전자문서 보관 요령','웹사이트 자료가 삭제·변경되어도 출처를 추적할 수 있는 기록 방법','원본 주소·보관시각·변경이력을 함께 저장했는지'),
 ('회의록과 공지의 핵심 비교','회의에서 논의한 내용과 실제로 결의된 결과를 비교하는 방법','안건번호와 의결 정족수, 후속 고시의 관련성을 확인했는지'),
 ('분쟁 상담 전 질문 정리','상담 시간을 낭비하지 않고 쟁점을 정리하는 실용적인 방법','사실·주장·추측을 분리한 경위표를 작성했는지'),
 ('공식 사이트에서 찾는 법','공고 원문을 지자체·국가법령정보센터에서 찾는 실제 절차','검색결과가 시행일이 다른 과거 자료가 아닌지'),
 ('자주 하는 오해와 확인 절차','온라인 게시글로 인해 발생할 수 있는 잘못된 판단을 줄이는 방법','개인 사례를 전체 구역에 일반화하지 않았는지'),
 ('다음 단계 준비 체크리스트','현재 절차가 끝났을 때 어떤 서류를 다음 단계로 넘길지','담당기관 확인·업데이트 날짜·문의 채널을 기록했는지'),
]

assets=ROOT/'static'/'assets'
sources=[assets/'reland-city.webp',assets/'legal-office-source.webp']
for i in range(12):
 src=sources[i%2]
 if not src.exists():continue
 im=Image.open(src).convert('RGB');w,h=im.size
 # avoid creating apparently official evidence: these are illustrative crops of original AI images
 target=1.55;cropw=int(h*target)
 if cropw<=w:
  start=int(max(0,w-cropw)*(i%6)/5);im=im.crop((start,0,start+cropw,h))
 else:
  croph=int(w/target);start=int(max(0,h-croph)*(i%6)/5);im=im.crop((0,start,w,start+croph))
 im.thumbnail((1050,680));im=ImageEnhance.Contrast(im).enhance(1.0+(i%4)*.045)
 im.save(assets/f'legal-topic-{i+1:02d}.webp','WEBP',quality=78)

articles=[]
for i,(topic,key,opening,docs) in enumerate(TOPICS):
 law=LAWS[key]
 for j,(angle,problem,question) in enumerate(ANGLES):
  num=i*10+j+1
  title=f'{topic}: {angle} — 재개발 실무 가이드'
  lead=f'{topic}에서 자주 생기는 질문은 “{problem}”입니다. {opening} 당사자의 지위와 실제 고시의 효력 여부를 먼저 정리해야 합니다.'
  para1=f'먼저 {docs}을(를) 확인하세요. 서류를 한 장씩 모으는 것보다 날짜·발행기관·사업 구역명을 같은 기준으로 맞추는 것이 중요합니다. 단순한 커뮤니티 의견이나 광고 문구를 인가·고시로 착각하지 않도록 자료의 성격을 표시하세요.'
  para2=f'실무 점검 포인트는 “{question}”입니다. 해당 사실관계에 따라 정관, 조례, 시행령, 부칙, 재건축·재개발 사업구분이 영향을 줄 수 있습니다. 모든 구역에 같은 결론이 적용되는 것은 아니므로 해당 구청의 최신 공고와 구체적 처분 내용을 비교해야 합니다.'
  para3=f'질문을 정리할 때는 ① 내 지위와 구역명 ② 확인된 공식 자료의 제목과 날짜 ③ 지금 필요한 판단 ④ 기관에 문의한 이력 순서로 정리하세요. 개인정보가 포함된 계약서·명부·신분증은 공개 게시판에 올리지 말고 전문가에게 필요한 범위에서만 전달해야 합니다.'
  para4=f'다음 행동: {docs}을(를) 준비하고, 표시된 법령 원문 링크에서 시행일과 실제 조문을 다시 확인하세요. 법적 기한, 금전 부담, 소송 가능성이 문제라면 변호사 등 자격 있는 전문가에게 개별 검토를 의뢰하는 편이 안전합니다.'
  article=dict(id=num,slug=f'column-{num:03d}',title=title,category=topic,angle=angle,description=lead,
   body='\n\n'.join([lead,para1,para2,para3,para4]),
   law_name=law['name'],law_article=law['article'],law_heading=law['heading'],law_excerpt=law['excerpt'],law_url=law['url'],
   image=f'/static/assets/legal-topic-{i+1:02d}.webp',image_alt=f'{topic} 주제 AI 생성 콘셉트 이미지 — 실제 사업장 사진 아님',
   status='editorial_review',author='RE:LAND 법률 저널 편집부 (편집 초안)',date='2026-10-29',
   legal_review='미완료 — 실제 전문자격자 감수 전',source_review='확인 조문 발췌·링크 2026-10-29, 개별 사례는 미검토',
   keywords=[topic,angle,'재개발','도시정비법'])
  articles.append(article)

assert len(articles)==120 and len({x['title'] for x in articles})==120
content=ROOT/'content';content.mkdir(exist_ok=True)
(content/'law_references.json').write_text(json.dumps(LAWS,ensure_ascii=False,indent=2),encoding='utf-8')
(content/'columns_120.json').write_text(json.dumps(articles,ensure_ascii=False,indent=2),encoding='utf-8')
blogs=ROOT/'blogger_drafts';blogs.mkdir(exist_ok=True)
for a in articles:
 def p(s):return '<p>'+html.escape(s)+'</p>'
 html_body=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(a['title'])}</title></head><body><article><h1>{html.escape(a['title'])}</h1><p><strong>RE:LAND 편집 초안 · 전문가 법률 감수 전 · 2026-10-29 기준</strong></p><img alt="{html.escape(a['image_alt'])}" src="{{PUBLISH_IMAGE_URL}}"/><p>※ AI 생성 이미지로 실제 현장·확정 계획을 나타내지 않습니다.</p>{''.join(p(x) for x in a['body'].split(chr(10)*2))}<h2>관련 법령 원문(발췌)</h2><blockquote>{html.escape(a['law_excerpt'])}</blockquote><p>근거: {html.escape(a['law_name'])} {html.escape(a['law_article'])} · <a href="{a['law_url']}">국가법령정보센터 원문 전체 열기</a></p><p>※ 일반적인 교육정보입니다. 개별 사안에 대한 법률 자문이 아닙니다. 법령·조례·고시의 최신 기준을 재확인하세요.</p></article></body></html>'''
 (blogs/(a['slug']+'.html')).write_text(html_body,encoding='utf-8')
with (content/'columns_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=['id','slug','title','category','law_name','law_article','law_url','status','legal_review']);wr.writeheader();wr.writerows({k:a[k] for k in wr.fieldnames} for a in articles)
print(f'Generated {len(articles)} distinct legal/editorial drafts, {len(LAWS)} checked law excerpts, {len(list(blogs.glob("*.html")))} Blogger HTML files')
