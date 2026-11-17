'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value == null ? '' : value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const id = Number(location.pathname.match(/^\/district-info\/(\d+)\/?$/)?.[1]);
  const safeUrl = url => {try{const u=new URL(url);const host=u.hostname.toLowerCase();return u.protocol==='https:' && (host==='go.kr'||host.endsWith('.go.kr')||host==='gov.kr'||host.endsWith('.gov.kr'))?u.href:''}catch{return ''}};
  const fail = message => {$('loading').hidden=true;$('record').hidden=true;$('error').hidden=false;$('errorMsg').textContent=message};
  if(!Number.isSafeInteger(id)||id<=0){fail('유효하지 않은 사업 번호입니다.');return;}
  fetch('/api/districts/'+id+'/public',{headers:{Accept:'application/json'}})
    .then(async res=>{if(!res.ok)throw new Error(res.status===404?'등록된 사업 정보를 찾지 못했습니다.':'공공데이터 서버 응답 오류 ('+res.status+')');return res.json()})
    .then(d=>{
      $('loading').hidden=true;$('record').hidden=false;
      $('projectName').textContent=d.name || '미등록 사업';
      $('projectArea').textContent=(d.values||[]).filter(x=>['province','city'].includes(x.key)).map(x=>x.value).join(' · ');
      $('dataStatus').textContent=d.demo?'시연용 지역 · 공식 사업 아님':d.source?.live_confirmed?'공공 API 대조 완료':d.source?.snapshot_verified?'국토부 CSV SHA256 검증':'공공자료 기준일 표시';
      $('recordNotice').textContent=d.message||'원문 최신 자료를 확인하세요.';
      $('facts').innerHTML=(d.values||[]).map(x=>'<div><dt>'+esc(x.label)+'</dt><dd'+(!x.value?' class="missing"':'')+'>'+esc(x.value||'자료 미제공')+'</dd></div>').join('');
      $('sourceMethod').textContent='확인 방식: '+(d.source?.method||'자료 상태 미확인');
      $('sourceDate').textContent='공개 데이터 기준일: '+(d.source?.snapshot_date||'미제공');
      const source = safeUrl(d.source?.url||'') || 'https://www.data.go.kr/data/15160169/fileData.do';
      $('sourceOfficial').href=source;$('sourcePrimary').href=source;
      const province=(d.values||[]).find(x=>x.key==='province')?.value||'';
      const sites=[
        ['국토교통부 공공데이터포털','https://www.data.go.kr/data/15160169/fileData.do','전국 정비사업 통합 공개 원문'],
        ['국토교통부 토지이음','https://www.eum.go.kr/web/am/amMain.jsp','토지이용계획·관련 고시 열람'],
        ['정부24 토지(임야)대장','https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000026','지번·면적과 토지기록 확인'],
        ['정부24 건축물대장','https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=15000000098','건축물 기본자료 확인'],
        ['국가법령정보센터','https://www.law.go.kr/법령/도시및주거환경정비법','적용 법률과 시행일 대조']
      ];
      if(province.includes('부산'))sites.splice(1,0,['부산시 정비사업별 정보공개','https://dynamice.busan.go.kr/view.do?no=279','부산시 공식 구역별 대표지번·추진단계·공개자료']);
      if(province.includes('서울'))sites.splice(1,0,['서울시 서울플랜+ 정비사업 현황','https://data.seoul.go.kr/dataList/OA-23112/S/1/datasetView.do','도시계획사업 정비사업 통계·원문 안내']);
      if(province.includes('인천'))sites.splice(1,0,['인천시 정비사업 정보공개','https://renewal.incheon.go.kr/','인천시 정비사업 현황·공개자료 조회']);
      if(province.includes('서울'))sites.splice(1,0,['서울시 정비사업 정보몽땅','https://cleanup.seoul.go.kr/','서울시 사업장·공개자료 조회']);
      $('governmentLinks').innerHTML=sites.map(([name,url,description])=>'<a class="district-site-link" href="'+safeUrl(url)+'" target="_blank" rel="noopener noreferrer"><span><strong>'+esc(name)+'</strong><small>'+esc(description)+'</small></span><b aria-hidden="true">↗</b></a>').join('');
      const officialVariants=Array.isArray(d.official_source_variants)?d.official_source_variants:[];
      const confirmed=Array.isArray(d.official_notices)?d.official_notices:[];
      $('projectSourceCount').textContent=officialVariants.length+'건 · '+(d.source?.snapshot_date||'기준일 미확인');
      if(d.demo){
        $('projectRecordStatus').innerHTML='<div class="project-empty">시연용 지역 허브이며 실제 정비사업 공식 기록이 아닙니다.</div>';
      }else if(!officialVariants.length){
        $('projectRecordStatus').innerHTML='<div class="project-empty">사업명과 시·군·구가 일치하는 원본 CSV 행을 확보하지 못했습니다. 기존 DB 정보만 표시합니다.</div>';
      }else{
        $('projectRecordStatus').innerHTML=(officialVariants.length>1?'<div class="project-match-warning">'+esc(d.official_same_name_warning||'동명이구역 공식 데이터가 여러 건입니다. 사업 동일성은 미확인입니다.')+'</div>':'')+
          officialVariants.map((r,i)=>'<article class="project-official-record"><div class="project-official-top"><b>공식 레코드 '+(i+1)+' / '+officialVariants.length+'</b><span>CSV '+Number(r.csv_line)+'행</span></div>'+
          '<dl>'+[['사업유형',r.kind],['공개 추진단계',r.stage],['사업시행자',r.operator],['공급 예정 세대 수',r.households]].map(([label,value])=>'<div><dt>'+esc(label)+'</dt><dd>'+esc(value||'자료 미제공')+'</dd></div>').join('')+'</dl></article>').join('')+
          '<p class="source-policy-note">출처: 국토교통부 전국 도시정비사업 통합 데이터 · 2026-05-18 기준. 동명이구역은 공식 원본 레코드를 임의로 통합하지 않습니다.</p>';
      }
      $('projectNoticeCount').textContent=confirmed.length+'건 확인';
      $('projectNotices').innerHTML=
        (d.official_parcel_address?'<p class="project-location-note">고시문 소재지: <strong>'+esc(d.official_parcel_address)+'</strong> (사업구역 경계·면적을 확정한 것은 아닙니다)</p>':'')+
        (d.official_portal_stage?.value?'<p class="project-location-note">지자체 포털 표기 단계: <strong>'+esc(d.official_portal_stage.value)+'</strong> (국토부 단계와 별도)</p>':'')+
        (confirmed.length?'<div class="district-site-grid">'+confirmed.map(n=>'<a class="district-site-link" href="'+safeUrl(n.source_url)+'" target="_blank" rel="noopener noreferrer"><span><strong>'+esc(n.title||'공식 고시·공고')+'</strong><small>'+esc(n.notice_number||'고시번호 미제공')+' · '+esc(n.notice_date||'일자 미제공')+' · '+esc(n.authority||'관할기관')+'</small></span><b aria-hidden="true">↗</b></a>').join('')+'</div><p class="source-policy-note">확인 기준일: '+esc(d.official_notice_verified_at||'미제공')+'</p>':
         '<p class="project-empty">이 사업지와 정확히 매칭해 검증한 고시·공고는 아직 없습니다. 인가번호·고시일은 임의로 만들지 않습니다. 아래 관할기관 링크에서 원문을 확인하세요.</p>');
      const municipal=d.municipal_reference&&typeof d.municipal_reference==='object'?d.municipal_reference:{};
      if(municipal.source_url){
        const source=document.createElement('section');
        source.className='card district-sites';
        source.innerHTML='<div class="section-head"><span>BUSAN / MUNICIPAL PUBLIC RECORD</span><h2>부산시 정비사업 포털 추가자료</h2><p>국토부 2026-05-18 원본과 별도로 조회된 지자체 포털 자료입니다. 최신 법적 인가 효력을 의미하지 않습니다.</p></div>'+
          '<p class="project-location-note">포털 표시 단계: <strong>'+esc(municipal.portal_stage||'미기재')+'</strong></p>'+
          (municipal.representative_parcel?'<p class="project-location-note">대표지번: '+esc(municipal.representative_parcel)+' (확정 정비구역 경계가 아님)</p>':'')+
          (municipal.milestone?.date?'<p class="project-location-note">포털 추진경과 '+esc(municipal.milestone.name)+': '+esc(municipal.milestone.date)+' · 고시번호 미확인</p>':'')+
          '<div class="district-site-grid"><a class="district-site-link" href="'+safeUrl(municipal.source_url)+'" target="_blank" rel="noopener noreferrer"><span><strong>부산시 공식 사업장 페이지</strong><small>원문 기준 단계·주요 추진경과·공개자료 확인</small></span><b aria-hidden="true">↗</b></a></div>';
        document.querySelector('.district-more')?.insertAdjacentElement('afterend',source);
      }
      const unknown=[
        ['총사업비·예상 공사비','국토부 기본 CSV에 없는 항목'],
        ['조합원 수·권리관계','사업별 원본 미확보'],
        ['정확한 필지·구역경계 및 면적',d.official_parcel_address?'고시 소재지만 확인 · 정비구역 경계는 미검증':'공식 GIS 경계 미등록'],
        ['사업시행·관리처분 인가 일자','고시별 원문 확인 필요'],
        ['분양·이주·착공·입주 일정','확정 일정 원문 미확보'],
        ['추가분담금','공식 산정자료 미확보']
      ];
      $('projectMissing').innerHTML=unknown.map(([title,note])=>'<li><b>'+esc(title)+'</b><span>미확인</span><small>'+esc(note)+'</small></li>').join('');
      const loc=d.location||{};
      $('locationNotice').textContent=loc.verified_boundary?'검증 등록된 경계 정보가 존재합니다. 원본과 최신 고시를 다시 확인하세요.':'지도 마커는 시·도 또는 행정구역 대표점일 수 있으며 실제 구역의 필지·경계를 의미하지 않습니다.';
      const districtQuery=(d.values||[]).filter(x=>['province','city','name'].includes(x.key)).map(x=>x.value).join(' ');
      $('googleLink').href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(districtQuery);
      document.title=(d.name||'정비사업')+' · 사업주체와 공공정보 | RE:LAND';
    }).catch(err=>fail(err.message));
})();