"""RE:LAND public search pages. Human-readable, source-linked, no invented figures."""
from __future__ import annotations

import json
from collections import Counter
from html import escape
from urllib.parse import quote

BASE = "https://reland.lexid.site"
SOURCE = "https://www.data.go.kr/data/15160169/fileData.do"
OG_IMAGE = BASE + "/static/assets/og-reland-20261111-v5.jpg"
REGIONS = {
 "seoul":"서울특별시","gyeonggi":"경기도","busan":"부산광역시",
 "daegu":"대구광역시","daejeon":"대전광역시","incheon":"인천광역시",
 "gwangju":"광주광역시","ulsan":"울산광역시","sejong":"세종특별자치시",
 "gangwon":"강원특별자치도","chungbuk":"충청북도","chungnam":"충청남도",
 "jeonbuk":"전북특별자치도","jeonnam":"전라남도","gyeongbuk":"경상북도",
 "gyeongnam":"경상남도","jeju":"제주특별자치도"
}
TOPICS = {
 "nationwide-redevelopment": {
  "title":"전국 재개발 현황과 지도 | 리랜드",
  "description":"전국 재개발·재건축 정비사업 현황을 국토교통부 원본 기준으로 조회합니다. 사업별 추진단계와 출처·자료 기준일을 확인하세요.",
  "heading":"전국 재개발 정보, 어디서 확인할까?",
  "intro":"전국 재개발 현황은 사업 이름뿐 아니라 행정구역, 사업유형, 추진단계, 시행주체를 함께 확인해야 합니다. RE:LAND는 국토교통부 2026년 5월 18일 기준 전국 도시정비사업 통합 원본을 출처와 함께 제공하는 민간 정보 서비스입니다.",
  "sections":[
   ("전국 정비사업 지도 읽기","공식 공개 원본은 1,566행이며, 시·도·시·군·구·구역명으로 분류한 지도 항목은 1,547개입니다. 이름이 같은 17개 그룹에는 서로 다른 사업유형 또는 시행주체의 기록이 포함돼 단순히 하나의 사업으로 합칠 수 없습니다. 대표점 표시는 실제 정비구역 위치나 법정 경계와 다릅니다."),
   ("지역별 현황 확인","서울·경기·인천·부산 등 17개 시도의 정비사업을 지역별로 구분합니다. 관심 구역 상세페이지에서 사업시행자, 사업유형, 공급 예정 세대 수와 원본 CSV 행 번호를 확인할 수 있습니다."),
   ("실제 사업 단계 확인","자료 기준일 이후의 변경은 반영되지 않을 수 있습니다. 정비구역 지정, 추진위원회 구성, 조합설립인가, 사업시행인가, 관리처분인가 등 개별 인허가와 고시 사항은 지자체 공고에서 별도로 대조해야 합니다.")
  ]},
 "redevelopment-info":{
  "title":"재개발정보 확인법과 공공데이터 | 리랜드",
  "description":"재개발정보는 정비구역명, 추진단계, 사업시행자, 고시번호, 사업비를 출처별로 구분해야 합니다. 공식 공공데이터 확인 방법 안내.",
  "heading":"재개발정보를 확인할 때 먼저 볼 5가지",
  "intro":"인터넷에 게시된 재개발 정보는 기관별 기준일과 법적 성격이 다를 수 있습니다. 사업명을 확인한 뒤 공공데이터 기본 현황, 관할 지자체 고시, 조합의 정보공개 문서를 차례로 대조하는 것이 안전합니다.",
  "sections":[
   ("사업명·행정구역·유형을 함께 보기","같은 구역명이 여러 지방자치단체에 존재할 수 있고, 한 지역에서 사업유형이 다른 동명이구역이 공개되기도 합니다. 이름만으로 한 사업으로 단정하지 마세요."),
   ("수치와 고시를 분리해 확인","국토부 통합 CSV에 있는 것은 기본 7개 필드입니다. 총사업비, 조합원 수, 필지 경계, 인가 고시번호, 분담금은 별도 공식 문서가 있어야 확인할 수 있습니다. RE:LAND 상세 화면은 검증된 항목과 미확인 항목을 나눕니다."),
   ("기준일·출처 링크 확인","오래된 자료의 추진단계를 오늘의 단계로 읽지 않습니다. 사업별 카드의 자료 작성일과 국토부 원문, 해당 지자체 포털의 최신 공고를 비교하세요.")
  ]},
 "redevelopment-process":{
  "title":"재개발사업 절차와 추진단계 | 리랜드",
  "description":"재개발사업의 정비구역 지정·추진위원회·조합설립·사업시행인가·관리처분·이주·착공 절차를 공식자료와 함께 설명합니다.",
  "heading":"재개발사업 추진 절차와 확인할 서류",
  "intro":"재개발사업은 각 단계에서 법적 요건과 이해관계자가 달라집니다. 지역마다 절차와 진행 속도가 다를 수 있으므로 아래 단계는 교육용 개요이며 특정 사업의 확정 일정이 아닙니다.",
  "sections":[
   ("정비구역 지정과 추진위원회","정비계획 수립과 정비구역 지정 고시를 확인한 뒤 추진위원회 승인 등 해당 사업의 실제 인허가 내용을 살핍니다. ‘추진위원회’ 표시만으로 곧바로 조합 설립이 승인됐다고 볼 수 없습니다."),
   ("조합설립인가와 사업시행인가","조합설립 인가 여부, 정관과 총회 의결사항, 사업시행계획 인가 고시를 각각 확인합니다. 사업유형이나 시행주체에 따라 절차가 달라질 수 있습니다."),
   ("관리처분·이주·착공·준공","관리처분계획인가와 분양·이주·착공은 서로 다른 사건입니다. 사업비와 분담금은 개별 사업의 공시 자료와 권리관계에 따라 달라집니다. 추정 일정이나 비용을 확정 사실처럼 제시하지 않습니다.")
  ]},
 "reconstruction":{
  "title":"재건축 정보와 추진단계 조회 | 리랜드",
  "description":"전국 재건축 정비사업의 추진단계와 공급 예정 세대 수를 공식 공공데이터 기준으로 확인하고, 안전한 고시 원문 확인법을 알아보세요.",
  "heading":"재건축 현황을 확인하는 기준",
  "intro":"재건축은 재개발과 같은 도시정비 범주에 속하지만 사업대상과 법적 요건이 다를 수 있습니다. 리랜드 지도에서 사업유형을 확인하고 해당 사업의 인허가 문서를 별도로 읽어야 합니다.",
  "sections":[
   ("재건축과 재개발 구분","기존 건축물과 기반시설 정비 방식에 따라 법 적용과 이해관계가 달라집니다. 공공데이터 원본의 ‘재건축(공동주택)’ 등 실제 사업유형을 기준으로 먼저 구분하세요."),
   ("세대 수와 추진단계","공급 예정 세대 수는 공개자료 기준의 계획치일 수 있습니다. 사업시행인가·관리처분인가·시공 과정에서 계획이 달라질 수 있으므로 최종 분양 세대 수로 단정하지 않습니다."),
   ("권리관계와 부담금","추정분담금은 종전자산평가액, 조합원 분양가, 사업비와 수입, 권리관계에 따라 달라집니다. 단일 지도 데이터만으로 개인별 분담금을 계산할 수 없습니다.")
  ]},
 "contribution":{
  "title":"재개발 분담금 계산 전 확인사항 | 리랜드",
  "description":"재개발·재건축 분담금과 추가분담금의 개념, 종전자산평가·비례율·조합원분양가 확인법을 살펴보세요. 개별 금액은 공식 문서로 확인.",
  "heading":"재개발 분담금, 어떤 자료가 필요한가?",
  "intro":"분담금은 공사비 하나만으로 정해지지 않습니다. 개별 권리와 조합원 분양 조건, 사업비·수입 구조 및 관리처분계획을 함께 확인해야 합니다. 인터넷의 일률적인 수치는 개별 사건에 적용하기 어렵습니다.",
  "sections":[
   ("분담금과 추가분담금의 차이","분담금은 조합원 분양과 권리가액의 차액 등을 기준으로 논의되며, 추가분담금은 사업비 변경과 분양 조건 변화 등으로 조정될 수 있습니다. 사업별 정관·관리처분계획·총회 자료의 정의를 확인하세요."),
   ("종전자산평가와 비례율","종전자산 감정평가와 비례율, 권리가액, 조합원 분양가 등은 서로 연결됩니다. 예시 계산만 보고 확정 납부액을 판단하면 안 됩니다. 공식 문서가 없는 사업은 리랜드에서 미확인으로 표시합니다."),
   ("확정액 확인 순서","해당 구역의 관리처분계획 인가 고시, 조합원별 분양계약, 총회 의결 및 예산 변동을 확인하세요. 필요하다면 관련 분야 전문가에게 개별 권리관계에 대한 설명을 요청해야 합니다.")
  ]},
 "reland":{
  "title":"리랜드 RE:LAND | 전국 재개발정보 플랫폼",
  "description":"리랜드(RE:LAND)는 전국 재개발·재건축 정비사업 공공정보, 사업별 추진단계, 강실장 교육과 동네 커뮤니티를 연결합니다.",
  "heading":"리랜드(RE:LAND), 재개발정보를 읽는 방법",
  "intro":"리랜드는 전국 재개발·재건축 사업의 기본 공공정보를 시민이 이해하기 쉽게 정리하는 민간 정보 플랫폼입니다. 행정기관이나 법정 조합의 공식 서비스가 아니며, 최신 인허가·권리관계의 효력은 공식 원문으로 확인해야 합니다.",
  "sections":[
   ("공공데이터를 구역별로 보기","지도와 사업별 상세정보에서 국토교통부 공식 원본의 사업명·추진단계·사업유형·시행주체·공급 예정 세대 수를 구분해 표시합니다."),
   ("학습과 확인을 함께","강실장 재개발 교육에서는 절차와 법률·경제 개념을 설명하며, 자료를 찾을 때에는 관할 지자체 고시와 법령 원문을 기준으로 다시 대조합니다."),
   ("정보의 한계를 표시","정확한 구역경계, 분담금, 사업비, 인가번호 등의 공식 원문을 확보하지 못한 경우 추측으로 채우지 않습니다. 공공정보 업데이트 기준일과 미확인 항목을 분리합니다.")
  ]}
}

def e(value):
    return escape(str(value if value is not None else ""), quote=True)

def links():
    items=[
      ("/insights/nationwide-redevelopment","전국 재개발"),
      ("/insights/redevelopment-info","재개발정보"),
      ("/insights/redevelopment-process","재개발사업 절차"),
      ("/insights/reconstruction","재건축"),
      ("/insights/contribution","분담금"),
      ("/insights/reland","리랜드 안내"),
      ("/map","정비사업 지도"),
      ("/sources","공공데이터 출처"),
    ]
    return '<nav class="seo-links" aria-label="재개발 주제별 정보">'+''.join(
      '<a href="'+e(url)+'">'+e(label)+'</a>' for url,label in items)+'</nav>'

def shell(title, description, url, heading, body, *, kind="WebPage", extra_schema=None):
    data={"@context":"https://schema.org","@type":kind,"name":title,
          "url":BASE+url,"description":description,"inLanguage":"ko-KR",
          "isPartOf":{"@type":"WebSite","name":"RE:LAND 리랜드","url":BASE+"/"}}
    if extra_schema:
        data.update(extra_schema)
    schema=json.dumps(data,ensure_ascii=False).replace("<","\\u003c")
    return ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
      '<meta name="viewport" content="width=device-width, initial-scale=1">'
      '<title>'+e(title)+'</title><meta name="description" content="'+e(description)+'">'
      '<meta name="robots" content="index,follow,max-image-preview:large">'
      '<link rel="canonical" href="'+e(BASE+url)+'">'
      '<link rel="alternate" type="application/rss+xml" href="'+BASE+'/feed.xml" title="리랜드 콘텐츠 RSS">'
      '<meta name="naver-site-verification" content="c4a5b3e6aaf0cea8aac1aa31fb7da9c9feb0c8e6">'
      '<meta property="og:type" content="article"><meta property="og:site_name" content="RE:LAND 리랜드">'
      '<meta property="og:title" content="'+e(title)+'"><meta property="og:description" content="'+e(description)+'">'
      '<meta property="og:url" content="'+e(BASE+url)+'"><meta property="og:image" content="'+OG_IMAGE+'">'
      '<meta name="twitter:card" content="summary_large_image">'
      '<script type="application/ld+json">'+schema+'</script>'
      '<link rel="icon" href="/favicon.ico">'
      '<style>body{margin:0;background:#f7f9f6;color:#1d3930;font-family:system-ui,"Noto Sans KR",sans-serif;line-height:1.85}'
      '.seo-wrap{width:min(940px,calc(100% - 32px));margin:auto}.seo-head{border-bottom:1px solid #dbe7df;background:white}'
      '.seo-head .seo-wrap{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 0}'
      '.brand{font-size:21px;font-weight:900;letter-spacing:-.04em;color:#173d33;text-decoration:none}'
      '.seo-main{padding:44px 0 64px}.seo-main h1{font-size:clamp(26px,4vw,38px);line-height:1.3;letter-spacing:-.04em}'
      '.seo-lead{font-size:17px;color:#486657;max-width:790px}.seo-panel{background:#fff;padding:23px 28px;border:1px solid #d9e6db;border-radius:16px;margin:24px 0}'
      '.seo-panel h2{font-size:21px;color:#1d543f;margin:0 0 10px}.seo-panel p{margin:0 0 10px}.seo-panel p:last-child{margin-bottom:0}'
      '.seo-links{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0}.seo-links a{display:inline-block;text-decoration:none;background:#e7f2e9;color:#1d5c42;border-radius:30px;padding:7px 14px;font-weight:700;font-size:13px}'
      '.seo-links a:hover,.seo-links a:focus-visible{background:#d3e8d7;outline:2px solid #3f9172}'
      '.seo-pill{display:inline-block;color:#206547;background:#e6f3e9;border-radius:20px;padding:4px 12px;font-size:12px;font-weight:800}'
      '.seo-table{border-collapse:collapse;width:100%;font-size:14px}.seo-table th,.seo-table td{padding:9px 12px;text-align:left;border-bottom:1px solid #e3ece5}.seo-table a{color:#165c40}'
      '.source{font-size:13px;color:#61796b}.source a{color:#13684b}.seo-foot{background:#16392c;color:#d6e5d9;padding:25px 0;font-size:12px}'
      '@media(max-width:600px){.seo-main{padding-top:22px}.seo-panel{padding:18px}.seo-table{font-size:12px}.seo-table th,.seo-table td{padding:7px}}'
      '</style></head><body><header class="seo-head"><div class="seo-wrap"><a class="brand" href="/">RE:LAND <small>리랜드</small></a><a href="/map">전국 정비사업 지도</a></div></header>'
      '<main class="seo-wrap seo-main"><span class="seo-pill">RE:LAND · 공식자료 읽기</span>'
      '<h1>'+e(heading)+'</h1>'+body+links()+'</main>'
      '<footer class="seo-foot"><div class="seo-wrap">리랜드는 정부기관이 아닌 민간 정보·교육 서비스입니다. 자료 기준일과 원문을 별도로 확인하세요.</div></footer></body></html>')

def topic_html(slug):
    topic=TOPICS.get(slug)
    if not topic:return None
    body='<p class="seo-lead">'+e(topic['intro'])+'</p>'
    body+=''.join('<section class="seo-panel"><h2>'+e(title)+'</h2><p>'+e(paragraph)+'</p></section>' for title,paragraph in topic['sections'])
    body+='<section class="seo-panel"><h2>17개 시·도 정비사업 현황</h2><p>아래 지역별 안내는 2026년 5월 18일 국토교통부 공식 원본을 기준으로 합니다.</p>'+links_regions()+'</section>'
    body+='<p class="source">공식 출처: <a target="_blank" rel="noopener noreferrer" href="'+SOURCE+'">국토교통부 전국 도시정비사업 통합 데이터</a> · 원본 자료 기준일: 2026-05-18</p>'
    return shell(topic['title'],topic['description'],'/insights/'+slug,topic['heading'],body,kind="Article")

def links_regions():
    return '<nav class="seo-links" aria-label="지역별 정비사업 현황">'+''.join(
       '<a href="/regions/'+e(slug)+'">'+e(name)+'</a>' for slug,name in REGIONS.items())+'</nav>'

def region_html(slug,snapshot,items):
    region=REGIONS.get(slug)
    if not region or not snapshot.get('verified'):return None
    raw_count=int(snapshot['regions'].get(region,0))
    rows=[row for row in items if row['province']==region and not row['demo']]
    rows.sort(key=lambda x:(x['city'],x['name'],x['id']))
    stage_counts=Counter(row['stage'].split(')',1)[-1].strip() for row in rows)
    stage_info=', '.join(e(k)+' '+str(v)+'개' for k,v in stage_counts.most_common(5))
    description=region+' 재개발·재건축 정비사업 구역별 추진단계와 사업유형, 공급 예정 세대 수를 국토부 2026년 5월 기준 출처와 함께 확인하세요.'
    heading=region+' 재개발·재건축 정비사업 현황'
    body=('<p class="seo-lead">국토교통부 2026년 5월 18일 기준 원본에서 '+e(region)+' 자료 '
          '<strong>'+str(raw_count)+'행</strong>을 확인했습니다. 지역·구역명을 묶은 지도 항목은 '
          '<strong>'+str(len(rows))+'개</strong>입니다. 동명이구역의 서로 다른 기록은 구역별 상세에서 구분합니다.</p>')
    body+='<section class="seo-panel"><h2>추진단계별 분포</h2><p>'+stage_info+'</p><p>개별 사업의 오늘 날짜 기준 단계가 아니라 공식 원본 기준일의 현황입니다.</p></section>'
    body+='<section class="seo-panel"><h2>'+e(region)+' 사업별 공공정보</h2><table class="seo-table"><thead><tr><th>시·군·구 · 구역명</th><th>사업유형</th><th>추진단계</th></tr></thead><tbody>'
    body+=''.join('<tr><td><a href="/district-info/'+str(row['id'])+'">'+e(row['city'])+' '+e(row['name'])+'</a></td><td>'+e(row['kind'])+'</td><td>'+e(row['stage'])+'</td></tr>' for row in rows)
    body+='</tbody></table><p><a href="/map?region='+quote(region)+'">'+e(region)+' 전체 구역 지도에서 검색하기</a></p></section>'
    body+='<p class="source">원본: <a href="'+SOURCE+'" target="_blank" rel="noopener noreferrer">국토교통부 전국 도시정비사업 통합 데이터</a> · 기준일 2026-05-18. 공간 좌표는 정확한 필지 경계를 의미하지 않습니다.</p>'
    return shell(heading+' | 리랜드',description,'/regions/'+slug,heading,body,kind="CollectionPage")

def district_html(template, data):
    """Pre-render actual project data inside the existing progressive-enhancement page."""
    if data.get('demo'):
        return template
    values={v['key']:str(v.get('value') or '').strip() for v in data.get('values',[])}
    published_kind=values.get('kind','')
    specific_kind=('재건축사업' if '재건축' in published_kind else
                   '재개발사업' if '재개발' in published_kind else
                   '주거환경개선사업' if '주거환경' in published_kind else '정비사업')
    title=data['name']+' '+specific_kind+' 추진단계 ('+values.get('province','')+' '+values.get('city','')+') | 리랜드'
    desc=(values.get('province','')+' '+values.get('city','')+' '+data['name']+
          ' 정비사업 '+values.get('stage','')+'·'+values.get('kind','')+
          '·공급 예정 '+(values.get('households') or '미제공')+'세대. 국토부 원본 기준일 2026-05-18.')
    desc=desc[:155]
    url='/district-info/'+str(data['id'])
    import re
    template=re.sub(r'<title>[^<]*</title>','<title>'+e(title)+'</title>',template,count=1)
    template=re.sub(r'<meta name="description" content="[^"]*">','<meta name="description" content="'+e(desc)+'">',template,count=1)
    template=template.replace('content="noindex,follow"','content="index,follow,max-image-preview:large"',1)
    canonical='<link rel="canonical" href="'+BASE+url+'">'
    schema={"@context":"https://schema.org","@type":"WebPage","name":title,"url":BASE+url,
            "description":desc,"inLanguage":"ko-KR",
            "isBasedOn":SOURCE,"about":{"@type":"Place","name":data['name'],"address":values.get('province','')+' '+values.get('city','')}}
    structured=json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')
    template=template.replace('</head>',canonical+'<meta property="og:type" content="article"><meta property="og:title" content="'+e(title)+'">'
        '<meta property="og:description" content="'+e(desc)+'"><meta property="og:url" content="'+BASE+url+'">'
        '<meta property="og:image" content="'+OG_IMAGE+'"><script type="application/ld+json">'+structured+'</script></head>',1)
    facts=''.join('<div><dt>'+e(field['label'])+'</dt><dd>'+e(field.get('value') or '자료 미제공')+'</dd></div>' for field in data.get('values',[]))
    source_rows=data.get('official_source_variants') or []
    record_list=''.join('<article class="project-official-record"><h3>국토부 원본 CSV '+str(int(r.get('csv_line',0)))+'행</h3><dl>'+
       ''.join('<div><dt>'+e(label)+'</dt><dd>'+e(r.get(key) or '미기재')+'</dd></div>' for label,key in (
        ('사업유형','kind'),('추진단계','stage'),('시행자','operator'),('공급 예정 세대수','households')))+'</dl></article>' for r in source_rows)
    notices=data.get('official_notices') or []
    links=''.join('<a class="district-site-link" href="'+e(n.get('source_url',''))+'" target="_blank" rel="noopener noreferrer">'
      '<span><strong>'+e(n.get('title','고시'))+'</strong><small>'+e(n.get('notice_number',''))+' · '+e(n.get('notice_date',''))+'</small></span></a>' for n in notices)
    if not notices:links='<p>이 사업과 정확히 매칭된 개별 고시번호·날짜는 아직 확인되지 않았습니다. 관할 지자체 원문에서 확인하세요.</p>'
    municipal=data.get('municipal_reference') or {}
    if municipal.get('source_url'):
        links+='<section class="project-official-record"><h3>부산시 정비사업 포털 추가자료</h3>'
        links+='<p>포털 표시 단계: '+e(municipal.get('portal_stage','미기재'))+'</p>'
        if municipal.get('representative_parcel'):
            links+='<p>대표지번: '+e(municipal['representative_parcel'])+' (정비구역 경계 아님)</p>'
        if municipal.get('milestone',{}).get('date'):
            links+='<p>포털 추진경과 '+e(municipal['milestone'].get('name'))+': '+e(municipal['milestone']['date'])+' (고시번호 별도 확인)</p>'
        links+='<a href="'+e(municipal['source_url'])+'" rel="noopener noreferrer" target="_blank">부산시 사업장 공식 포털 원문 ↗</a></section>'
    missing='<li>총사업비 · 원본 미제공</li><li>조합원 수 · 원본 미제공</li><li>확정 구역경계와 면적 · 검증 자료 없음</li><li>개별 추가분담금 · 원본 미제공</li>'
    replacements={
       '<div class="placeholder" id="loading">':'<div class="placeholder" id="loading" hidden>',
       '<div id="record" hidden>':'<div id="record">',
       '<h1 id="projectName"></h1>':'<h1 id="projectName">'+e(data['name'])+'</h1>',
       '<p id="projectArea"></p>':'<p id="projectArea">'+e(values.get('province',''))+' · '+e(values.get('city',''))+'</p>',
       '<span class="status" id="dataStatus"></span>':'<span class="status" id="dataStatus">국토교통부 공식 원본 · 2026-05-18 기준</span>',
       '<section class="alert" id="recordNotice"></section>':'<section class="alert" id="recordNotice">'+e(data.get('message',''))+'</section>',
       '<dl id="facts"></dl>':'<dl id="facts">'+facts+'</dl>',
       '<div id="projectRecordStatus" class="project-record-grid" aria-live="polite"></div>':'<div id="projectRecordStatus" class="project-record-grid" aria-live="polite">'+record_list+'</div>',
       '<div id="projectNotices" aria-live="polite"></div>':'<div id="projectNotices" aria-live="polite">'+links+'</div>',
       '<ul class="district-more-list" id="projectMissing"></ul>':'<ul class="district-more-list" id="projectMissing">'+missing+'</ul>',
       '<span id="projectSourceCount">확인 중</span>':'<span id="projectSourceCount">'+str(len(source_rows))+'건 확인</span>',
       '<span id="projectNoticeCount">확인 중</span>':'<span id="projectNoticeCount">'+str(len(notices))+'건 확인</span>',
       '<p id="sourceMethod"></p>':'<p id="sourceMethod">'+e(data.get('source',{}).get('method',''))+'</p>',
       '<p id="sourceDate"></p>':'<p id="sourceDate">국토교통부 원본 기준일 2026-05-18</p>',
       '<p id="locationNotice"></p>':'<p id="locationNotice">지도 핀은 시·도 대표점일 수 있습니다. 실제 사업지 경계가 아닙니다.</p>',
       }
    for original,new in replacements.items():
        if original not in template:
            raise ValueError('SEO template placeholder absent: '+original[:70])
        template=template.replace(original,new,1)
    return template
