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
      $('dataStatus').textContent=d.demo?'시연용 지역 · 공식 사업 아님':d.source?.live_confirmed?'공공 API 대조 완료':'공공자료 기준일 표시';
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
      if(province.includes('서울'))sites.splice(1,0,['서울시 정비사업 정보몽땅','https://cleanup.seoul.go.kr/','서울시 사업장·공개자료 조회']);
      $('governmentLinks').innerHTML=sites.map(([name,url,description])=>'<a class="district-site-link" href="'+safeUrl(url)+'" target="_blank" rel="noopener noreferrer"><span><strong>'+esc(name)+'</strong><small>'+esc(description)+'</small></span><b aria-hidden="true">↗</b></a>').join('');
      const loc=d.location||{};
      $('locationNotice').textContent=loc.verified_boundary?'검증 등록된 경계 정보가 존재합니다. 원본과 최신 고시를 다시 확인하세요.':'지도 마커는 시·도 또는 행정구역 대표점일 수 있으며 실제 구역의 필지·경계를 의미하지 않습니다.';
      const districtQuery=(d.values||[]).filter(x=>['province','city','name'].includes(x.key)).map(x=>x.value).join(' ');
      $('googleLink').href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(districtQuery);
      document.title=(d.name||'정비사업')+' · 사업주체와 공공정보 | RE:LAND';
    }).catch(err=>fail(err.message));
})();