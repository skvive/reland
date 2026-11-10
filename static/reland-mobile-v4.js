/* RE:LAND mobile visual reference implementation v4 — reuses existing SPA/API; no fabricated content. */
'use strict';
(() => {
  const original = window.relandHomeV2;
  if (typeof original !== 'function') return;
  const h = s => String(s ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const photo = (s, fallback) => typeof s === 'string' && /^\/(?:static|kang)\/[a-zA-Z0-9/_-]+\.(?:webp|jpg|png)$/.test(s) ? s : fallback;
  const icons = {
    map:'<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>',
    book:'<path d="M3 4h8l1 2 1-2h8v16h-8l-1 1-1-1H3z"/><path d="M12 6v14"/>',
    users:'<circle cx="8" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M2 20c0-5 12-5 12 0M14 17c3-1 7 0 8 3"/>',
    video:'<rect x="2" y="5" width="20" height="14" rx="4"/><path d="m10 9 5 3-5 3z"/>',
    law:'<path d="M12 3v16M6 7h12M5 8l-3 6h6zM19 8l-3 6h6zM8 21h8"/>',
    journal:'<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h6"/>',
    pin:'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0z"/><circle cx="12" cy="10" r="2.5"/>'
  };
  const icon = (key) => `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${icons[key]||icons.map}</svg>`;
  const api = async (endpoint) => {
    const r=await fetch('/api'+endpoint,{credentials:'same-origin',headers:{'Accept':'application/json'}});
    if(!r.ok)throw Error(`HTTP ${r.status}`);
    return r.json();
  };
  const homeOnly = () => ['/', ''].includes(location.pathname);
  const renderLectures = async () => {
    const box=document.getElementById('m-lesson-list');if(!box)return;
    try {
      const d=await api('/kang/lectures?limit=4');
      const entries=Array.isArray(d.items)?d.items.slice(0,4):[];
      if(!homeOnly() || !box.isConnected) return;
      box.innerHTML=entries.length?entries.map(x=>{
        const id=Number(x.id);if(!Number.isInteger(id)||id<1||id>999)return '';
        const n=String(id).padStart(3,'0');
        const cover=photo(x.cover,`/kang/assets/lessons/lesson-${n}.webp`);
        return `<a class="m-lesson" href="/kang/slides/lesson-${n}.html" aria-label="강의 ${h(x.title)} 자료 보기"><img src="${cover}" loading="lazy" alt="강의 관련 도시정비 이미지"><span><b>${h(x.title)}</b><small>${h(x.category||'강실장 클래스')} · 교육 원고</small></span><i aria-hidden="true">▶</i></a>`;
      }).join(''):'<a href="/kang/" class="m-text-link">강실장 60강 확인하기 →</a>';
    } catch {box.innerHTML='<a href="/kang/" class="m-text-link">강실장 강의실에서 전체 강의 보기 →</a>'}
  };
  const renderArticles = async () => {
    const box=document.getElementById('m-legal-list');if(!box)return;
    try {
      const d=await api('/studio/columns?limit=4&page=1');
      if(!homeOnly()||!box.isConnected)return;
      const items=(Array.isArray(d.items)?d.items:[]).slice(0,4);
      box.innerHTML=items.length?items.map(x=>{
        const id=Number(x.id);if(!Number.isInteger(id)||id<=0)return '';
        return `<a href="/column/${id}" data-nav="column"><span>${h(x.title)}</span><strong aria-hidden="true">›</strong></a>`;
      }).join(''):'<a href="/columns" data-nav="columns">재개발 법률 저널 전체 보기 <strong aria-hidden="true">›</strong></a>';
    }catch{box.innerHTML='<a href="/columns" data-nav="columns">법률 저널 원고 전체 보기 <strong aria-hidden="true">›</strong></a>'}
  };
  const renderAreas = async () => {
    const box=document.getElementById('m-areas-list');if(!box)return;
    try {
      const d=await api('/districts?limit=12');if(!homeOnly()||!box.isConnected)return;
      const rows=(Array.isArray(d.items)?d.items:[]).filter(x=>Number.isInteger(Number(x.id))&&Number(x.id)>0).slice(0,6);
      box.innerHTML=rows.length?rows.map((x,i)=>`<a href="/district/${Number(x.id)}" data-nav="district" class="m-area-card"><div class="m-area-photo"><img loading="lazy" src="${i%2?'/static/assets/reland-home-city-v2.webp':'/static/assets/reland-city.webp'}" alt="도시 전경 콘셉트 이미지, 해당 지역의 실제 현장 아님"><span>지도에서 보기 ↗</span></div><b>${h(x.name)}</b><small>${h(x.province||'지역 확인')} · ${h(x.stage||'진행 단계 확인')}</small></a>`).join(''):'<a class="m-text-link" href="/map">전체 정비구역 지도에서 보기 →</a>';
    }catch{box.innerHTML='<a class="m-text-link" href="/map">전국 정비구역 지도에서 확인하기 →</a>'}
  };
  const markup = () => `
  <section class="m-showcase m-kang" id="m-kang" aria-labelledby="m-kang-title"><div class="shell">
    <div class="m-heading"><div><span class="m-overline">KANG'S CLASS</span><h2 id="m-kang-title">강실장 클래스</h2><p>재개발, 어렵지 않습니다.<br>실전 절차를 이해하기 쉽게 알려드립니다.</p></div><a href="/kang/">전체보기 ›</a></div>
    <a href="/kang/" class="m-kang-hero"><img loading="lazy" src="/kang/assets/kang-hero-v1.webp" alt="석양 도시 전경과 강실장 AI 캐릭터"><span class="m-kang-overlay"><small>RE:LAND SPECIAL CLASS</small><strong>강실장<br>재개발 클래스</strong><em>▶ 강의실 입장하기</em></span></a>
    <div class="m-lessons" id="m-lesson-list" aria-live="polite"><p class="m-loading">강실장 강의를 불러오고 있습니다.</p></div>
    <p class="m-note">전문가 개별 감수 전 교육용 편집 원고이며 법률 자문이 아닙니다.</p>
  </div></section>
  <section class="m-showcase m-legal" id="m-legal" aria-labelledby="m-legal-title"><div class="shell">
    <div class="m-heading"><div><span class="m-overline">EDITORIAL</span><h2 id="m-legal-title">법률 저널 · 정책 이슈</h2><p>재개발·재건축의 법률, 판례, 정책 변화를<br>원문 자료와 함께 살펴보세요.</p></div><a href="/columns" data-nav="columns">전체보기 ›</a></div>
    <a class="m-legal-hero" href="/columns" data-nav="columns"><img src="/static/assets/legal-topic-01.webp" loading="lazy" alt="법률 주제 AI 콘셉트 이미지"><span>법률 저널</span></a>
    <div id="m-legal-list" class="m-legal-list" aria-live="polite"><a href="/columns" data-nav="columns">법률 저널 열기 →</a></div>
    <p class="m-note">실제 권리판단 전 최신 법령·고시 및 전문 자문 확인이 필요합니다.</p>
  </div></section>
  <section class="m-showcase m-areas" id="m-areas" aria-labelledby="m-areas-title"><div class="shell">
    <div class="m-heading"><div><h2 id="m-areas-title">인기 지역 · 주목 구역</h2><p>공공데이터 기반으로 등록된 구역을 살펴보세요.</p></div><a href="/map" data-nav="map">전체보기 ›</a></div>
    <div class="m-area-track" id="m-areas-list" aria-live="polite"><a href="/map" data-nav="map">전국 지도에서 구역 확인하기 →</a></div>
  </div></section>
  <section class="m-showcase m-blogger-cta" id="m-blogger-cta" aria-labelledby="m-blogger-title"><div class="shell"><div class="m-blogger-panel">
    <span class="m-overline">NEIGHBORHOOD STORIES</span><h2 id="m-blogger-title">지금, 우리 동네 이야기를<br>시작해보세요!</h2>
    <p>Google Blogger에서 동네사랑방을 만들고<br>이웃들과 소식과 경험을 나누세요.</p>
    <div class="m-blogger-illustration"><span aria-hidden="true">B</span><small>Google Blogger</small></div>
    <button class="r-section-button" data-action="create-community">동네사랑방 만들기　→</button>
  </div></div></section>`;
  window.relandHomeV2=async function(...args){
    await original.apply(this,args);
    const root=document.querySelector('#main');if(!root||!homeOnly()||root.querySelector('#m-kang'))return;
    const intro=root.querySelector('.r-video-section');if(!intro)return;
    intro.insertAdjacentHTML('beforebegin',markup());
    const heroTitle=root.querySelector('.r-hero h1');
    if(heroTitle){const originalTitle=heroTitle.innerHTML;heroTitle.innerHTML='<span class="m-desktop-text">'+originalTitle+'</span><span class="m-hero-text">우리 동네도<br><em>새로워질 수 있습니다.</em></span>';}
    const heroSub=root.querySelector('.r-hero-content>p');
    if(heroSub){const originalSub=heroSub.innerHTML;heroSub.innerHTML='<span class="m-desktop-text">'+originalSub+'</span><span class="m-hero-text">재개발·재건축·정비사업의 정보를<br>한곳에서, 더 쉽고 정확하게.</span>';}
    const quick=root.querySelector('.r-mobile-quick');
    if(quick){const keys=['pin','book','users','video','law','journal'];
      quick.querySelectorAll('a').forEach((el,i)=>{const old=el.querySelector('span');if(old&&keys[i])old.innerHTML=icon(keys[i]);});}
    const videoTitle=root.querySelector('.r-video-section .r-section-heading h2');if(videoTitle)videoTitle.textContent='재개발 실전 영상관';
    const videoDesc=root.querySelector('.r-video-section .r-section-heading p');if(videoDesc)videoDesc.textContent='재개발·재건축 관련 실제 공개 영상을 확인하세요.';
    const blogTitle=root.querySelector('.r-blog-section .r-section-heading h2');if(blogTitle)blogTitle.textContent='동네사랑방';
    const blogDesc=root.querySelector('.r-blog-section .r-section-heading p');if(blogDesc)blogDesc.textContent='공개 Blogger 글은 사진 앨범형·텍스트 목록형으로 구분됩니다.';
    void renderLectures();void renderArticles();void renderAreas();
  };
  // Fix mobile menu state on repeated SPA route changes and allow closing via Esc.
  document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelector('.header.menu-open .menu-button')?.click()});
})();
