/* RE:LAND 2026.11 — editorial homepage, verified-video gallery, Blogger albums. */
'use strict';
(() => {
  const $ = sel => document.querySelector(sel);
  const FEATURED_PUBLIC_VIDEOS=[{"video_id":"iCdL2XaXmpo","title":"현금청산자의 정비사업 정보공개 청구","creator":"법무법인 센트로","category":"도시정비 실무 · 2025"},{"video_id":"B4ztywXFWjU","title":"재개발·재건축 정비사업 일몰제 핵심 이해","creator":"법무법인 센트로","category":"정비사업 절차"},{"video_id":"TsLDwYrDpfA","title":"내 토지가 여러 필지라면? 보상금 평가 방식","creator":"법무법인 센트로","category":"감정평가·보상"},{"video_id":"N7WabZ41tsw","title":"투기과열지구 조합원 자격 승계와 2025 판례","creator":"법무법인 센트로","category":"조합원 자격"},{"video_id":"Mgl5dunkW8M","title":"재건축 현금청산금 평가시기의 쟁점","creator":"법무법인 센트로","category":"현금청산"},{"video_id":"w7hPdTuvjMk","title":"토지 수용과 근저당권자의 대응","creator":"법무법인 센트로","category":"수용·보상"},{"video_id":"mA1TvquRMT8","title":"현금청산자 이행제공 방법 Part.1","creator":"법무법인 센트로","category":"법률 실무"},{"video_id":"hmLoj9XH00w","title":"현금청산자 이행제공 방법 Part.2","creator":"법무법인 센트로","category":"법률 실무"}];
  const VIDEO_TOPICS = [
    {title:'재개발 첫걸음',desc:'정비구역 지정부터 사업시행까지',query:'재개발 정비사업 절차 강의',cover:'/static/assets/reland-home-city-v2.webp'},
    {title:'조합설립과 총회',desc:'조합원 권리와 의사결정 구조',query:'재개발 조합 설립 총회 정비사업 설명',cover:'/static/assets/legal-office-source.webp'},
    {title:'관리처분·분담금',desc:'평가, 분양신청, 사업비 이해',query:'재개발 관리처분 분담금 설명 강의',cover:'/kang/assets/lessons/lesson-001.webp'},
    {title:'이주·보상과 분쟁',desc:'보상 절차와 주의할 법률 쟁점',query:'재개발 이주 보상 절차 강의',cover:'/kang/assets/lessons/lesson-055.webp'}
  ];
  function youtubeSearchHref(query){return 'https://www.youtube.com/results?search_query='+encodeURIComponent(query)}
  function youtubeCard(video){
    const id=String(video.video_id||'');
    if(!/^[A-Za-z0-9_-]{11}$/.test(id))return '';
    const url='https://www.youtube.com/watch?v='+encodeURIComponent(id);
    return `<a class="r-video-card" href="${url}" target="_blank" rel="noopener noreferrer" aria-label="YouTube에서 ${E(video.title)} 시청하기"><div class="r-video-photo"><img loading="lazy" src="https://i.ytimg.com/vi/${id}/hqdefault.jpg" alt="${E(video.title)} 영상 썸네일"><span class="r-video-play">▶</span></div><div class="r-video-info"><span>${E(video.creator||'YouTube 원문')} · ${E(video.category||'재개발')}</span><h3>${E(video.title)}</h3><p>YouTube에서 보기 ↗</p></div></a>`;
  }
  function topicCard(topic){
    return `<a class="r-video-card topic-card" target="_blank" rel="noopener noreferrer" href="${youtubeSearchHref(topic.query)}"><div class="r-video-photo"><img loading="lazy" src="${topic.cover}" alt="재개발 교육 주제 관련 AI 제작 콘셉트 이미지"><span class="r-video-play">⌕</span><span class="r-video-source">YouTube 영상 검색</span></div><div class="r-video-info"><span>RELATED VIDEOS · 주제별 탐색</span><h3>${E(topic.title)}</h3><p>${E(topic.desc)} →</p></div></a>`;
  }
  async function verifiedVideos(){
    try{const result=await api('/studio/videos');const published=(Array.isArray(result.items)?result.items:[]).filter(v=>/^[A-Za-z0-9_-]{11}$/.test(String(v.video_id||''))).slice(0,8);return published.length?published:FEATURED_PUBLIC_VIDEOS}
    catch{return FEATURED_PUBLIC_VIDEOS}
  }
  function videoCards(videos, limit=4){
    if(videos.length)return videos.slice(0,limit).map(youtubeCard).join('');
    return VIDEO_TOPICS.slice(0,limit).map(topicCard).join('');
  }
  function postImage(url){
    try{const u=new URL(url);if(u.protocol!=='https:')return '';
      const h=u.hostname.toLowerCase();
      return (h.endsWith('.googleusercontent.com')||h==='blogger.googleusercontent.com'||h.endsWith('.bp.blogspot.com'))?u.href:'';
    }catch{return ''}
  }
  function postsMarkup(entries, withFallback=true){
    const photos=entries.filter(p=>postImage(p.image)).slice(0,6);
    const texts=entries.filter(p=>!postImage(p.image)).slice(0,7);
    if(!entries.length){
      return `<div class="r-blog-empty"><div class="r-blog-empty-intro"><span class="r-chip">공개 블로그 연결 준비</span><h3>지역의 이야기를 담을<br>동네사랑방을 기다립니다.</h3><p>연결된 Google Blogger에 공개 글이 등록되면 사진 글은 앨범형, 텍스트 글은 목록형으로 자동 분류됩니다.</p><button class="btn btn-primary" data-action="create-community">동네사랑방 만들기 ↗</button></div>${withFallback?`<div class="r-editorial-fallback"><span class="r-chip subtle">리랜드 내부 편집 원고 · Blogger 게시물이 아닙니다</span><a href="/column/1" data-nav="column">정비사업의 핵심 법률 안내 읽기 <span>↗</span></a><a href="/columns" data-nav="columns">재개발 법률 저널 전체 보기 <span>↗</span></a><a href="/kang/">강실장 60강 · 질의응답 30선 <span>↗</span></a></div>`:''}</div>`;
    }
    return `<div class="r-blog-album-group"><div class="r-blog-titleline"><h3>사진 있는 이야기 <small>${photos.length}건</small></h3><span>ALBUM</span></div>${photos.length?`<div class="r-blog-album">${photos.map(p=>`<a href="${A(p.url)}" target="_blank" rel="noopener noreferrer" class="r-blog-photo"><img loading="lazy" src="${E(postImage(p.image))}" alt="${E(p.title)} 게시물의 공개 대표 이미지"><div><span>${E(p.community_name||'공개 Blogger')}</span><strong>${E(p.title)}</strong></div></a>`).join('')}</div>`:`<p class="r-text-placeholder">사진이 포함된 공개 글은 아직 없습니다.</p>`}</div><div class="r-blog-list-group"><div class="r-blog-titleline"><h3>글로 읽는 동네 소식 <small>${texts.length}건</small></h3><span>LIST</span></div>${texts.length?`<div class="r-blog-list">${texts.map(p=>`<a href="${A(p.url)}" target="_blank" rel="noopener noreferrer"><span class="r-blog-list-mark">↗</span><div><strong>${E(p.title)}</strong><small>${E(p.community_name||'공개 Blogger')} · ${E((p.summary||'').slice(0,90))}</small></div></a>`).join('')}</div>`:`<p class="r-text-placeholder">텍스트 중심 공개 글은 아직 없습니다.</p>`}</div>`;
  }
  window.relandBloggerMarkup=(items)=>postsMarkup(Array.isArray(items)?items:[],false);
  async function connectedBloggerPosts(communities){
    const connected=communities.filter(x=>typeof x.blog_url==='string'&&/^https:\/\/[a-z0-9-]+\.blogspot\.com\/?$/i.test(x.blog_url)).slice(0,5);
    const responses=await Promise.allSettled(connected.map(c=>api('/communities/'+c.id+'/blog').then(r=>(r.items||[]).map(p=>({...p,community_name:c.name})))));
    const items=responses.filter(r=>r.status==='fulfilled').flatMap(r=>r.value).filter(p=>p.title&&p.url);
    const unique=new Map(items.map(p=>[p.url,p]));
    return [...unique.values()].slice(0,12);
  }
  const regionLinks=['서울','경기','인천','부산'];
  async function homePageV2(){
    const [statsData,districtData,communityData]=await Promise.all([
      api('/stats').catch(()=>({})),api('/districts?limit=12').catch(()=>({items:[],verified_data_rows:0})),api('/communities').catch(()=>({items:[]}))
    ]);
    const districts=Array.isArray(districtData.items)?districtData.items:[], communities=Array.isArray(communityData.items)?communityData.items:[];
    STATE.stats=statsData;STATE.districts=districts;STATE.communities=communities;
    const videoPromise=verifiedVideos(),blogPromise=connectedBloggerPosts(communities),newsPromise=api('/news?limit=4').catch(()=>({items:[]}));
    main.innerHTML=`
    <section class="r-hero" aria-labelledby="r-hero-heading"><div class="shell r-hero-content"><div class="r-hero-label">RE:LAND · THE CITY KNOWLEDGE PLATFORM</div><h1 id="r-hero-heading">도시의 변화,<br><em>삶의 가능성이 되다.</em></h1><p>우리 동네 정비사업의 현재, 법률의 맥락,<br>그리고 이웃의 이야기를 하나의 화면에서 발견하세요.</p><form id="hero-search" class="r-hero-search"><label for="r-hero-q" class="sr-only">지역·정비사업 검색</label><span aria-hidden="true">⌕</span><input id="r-hero-q" name="q" placeholder="궁금한 지역이나 재개발 구역을 검색해 보세요" autocomplete="off" maxlength="80"><button type="submit">지도에서 찾기 →</button></form><div class="r-hero-regions"><span>관심 지역</span>${regionLinks.map(x=>`<button data-action="search-region" data-value="${x}">${x}</button>`).join('')}</div></div><div class="r-hero-credit">AI CONCEPT IMAGE · 실제 확정 정비구역 조감도 아님</div></section>
    <div class="shell r-mobile-quick" aria-label="모바일 빠른 서비스">
<a href="/map" data-nav="map"><span aria-hidden="true">⌖</span>재개발 지도</a><a href="/kang/"><span aria-hidden="true">▧</span>강실장 클래스</a><a href="/community" data-nav="community"><span aria-hidden="true">♧</span>동네사랑방</a>
<a href="/youtube" data-nav="youtube"><span aria-hidden="true">▶</span>YouTube</a><a href="/guide" data-nav="guide"><span aria-hidden="true">⚖</span>법률·정책</a><a href="/columns" data-nav="columns"><span aria-hidden="true">▤</span>법률 저널</a>
</div>
     <section class="r-data-strip"><div class="shell r-data-items"><div><strong>1,566</strong><span>전국 공개 원본 행 · 2026.5</span></div><div><strong>${compact(statsData.districts)}</strong><span>가져온 실제 정비구역</span></div><div><strong>${compact(statsData.communities)}</strong><span>커뮤니티 · 시연 포함</span></div><div><strong>60 <small>강</small></strong><span>강실장 교육 콘텐츠</span></div></div></section>
    <section class="r-section r-editorial"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">STORIES BEHIND THE CITY</span><h2>도시를 읽는 두 가지 시선</h2><p>명료한 정보와 깊이 있는 해설을 모두 갖춘 재개발 플랫폼.</p></div><a href="/columns" data-nav="columns" class="r-section-more">콘텐츠 전체 보기 ↗</a></div><div class="r-editorial-grid"><a href="/kang/" class="r-editorial-card r-editorial-primary"><img loading="lazy" src="/static/assets/editorial-class-v5.webp" alt="강실장 클래스, 인물이 없는 실사형 재개발 도시 전경"><div class="r-editorial-info"><span>RE:LAND SPECIAL CLASS</span><h3>재개발 강실장 클래스</h3><p>분담금부터 조합총회까지, 60강으로 배우는 재개발의 실제 절차.</p><b>강의실로 이동 →</b></div></a><a href="/columns" data-nav="columns" class="r-editorial-card r-editorial-secondary"><img loading="lazy" src="/static/assets/editorial-journal-v5.webp" alt="강실장 실사형 인물이 문서를 검토하는 법률 저널 이미지"><div class="r-editorial-info"><span>RE:LAND LEGAL JOURNAL</span><h3>서류 한 장에서 시작하는 변화</h3><p>120편의 법률 편집 원고와 공식 법령 원문 연결.</p><b>법률 저널 읽기 →</b></div></a></div><p class="r-disclaimer">강실장·법률 저널의 원고는 법률전문가 개별 감수 전 교육용 자료입니다.</p></div></section>
    <section class="r-section r-map-section" id="map-feature"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">EXPLORE THE NEIGHBORHOOD</span><h2>지도 위에서 만나는 우리 동네</h2><p>Google 지도에서 위치를 살펴보고, 정확한 정비구역 정보는 상세 지도에서 확인하세요.</p></div><a class="r-section-more" data-nav="map" href="/map">전국 재개발 지도 ↗</a></div><div class="r-map-layout"><div class="r-map-panel"><div id="home-real-map" class="r-google-map" role="region" aria-label="우리 동네 정비사업 실제 지도"><div class="r-map-loading">지도를 불러오는 중입니다…</div></div><div class="r-map-caption"><span>● 검증되지 않은 좌표는 시·도 기준점으로 표시합니다. 실제 사업 구역의 정확한 경계가 아닙니다.</span><a href="/map" data-nav="map">상세 지도 열기 →</a></div></div><aside class="r-map-aside"><h3>지역 바로가기 <span>LOCATION</span></h3>${regionLinks.map((region,i)=>`<button class='place-row' data-action='search-region' data-value='${E(region)}'><span class='place-number'>${String(i+1).padStart(2,'0')}</span><span class='place-info'><strong>${E(region)}</strong><small>해당 권역의 지도와 정비사업 확인</small></span><span class='arrow'>↗</span></button>`).join('')}<div class="r-map-notice">국토부 공공데이터 원본과 구역 고시정보의 기준일을 반드시 대조하세요.</div></aside></div></div></section>
    <section class="r-section r-neighbors"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">PEOPLE & NEIGHBORHOODS</span><h2>이웃이 만들어 가는 동네사랑방</h2><p>실제 주민 커뮤니티를 발견하고, Google Blogger로 우리 지역의 소식을 기록하세요.</p></div><button class="r-section-button" data-action="create-community">+ 블로그 동네사랑방 만들기</button></div><div class="r-community-grid">${communities.slice(0,3).map(communityCard).join('')||'<div class="r-placeholder">등록된 주민모임이 없습니다. 첫 동네사랑방을 개설해보세요.</div>'}</div><a href="/community" data-nav="community" class="r-mobile-more">모든 동네사랑방 보기 →</a></div></section>
    <section class="r-section r-video-section" id="home-youtube"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">WATCH & UNDERSTAND</span><h2>영상으로 보는 재개발</h2><p>검증·등록된 영상이 있으면 바로 표시하고, 없으면 YouTube의 관련 주제를 탐색합니다.</p></div><a href="/youtube" data-nav="youtube" class="r-section-more">YouTube 영상관 ↗</a></div><div class="r-video-grid" id="r-home-videos">${VIDEO_TOPICS.map(topicCard).join('')}</div><div class="r-content-note" id="r-youtube-source">현재 등록·검수된 자체 큐레이션 영상이 없다면 YouTube 검색 결과를 연결합니다. 썸네일은 AI 콘셉트 이미지입니다.</div></div></section>
    <section class="r-section r-blog-section" id="home-blogger"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">GOOGLE BLOGGER · LOCAL VOICES</span><h2>동네가 기록하는 재개발 이야기</h2><p>연결된 공개 Blogger 글은 사진을 포함하면 앨범형, 글만 있으면 목록형으로 자동 분류합니다.</p></div><a href="/community" data-nav="community" class="r-section-more">동네 블로그 둘러보기 ↗</a></div><div id="r-blog-content" class="r-blog-content">${postsMarkup([],true)}</div></div></section>
    <section class="r-section r-news-section"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">THE REDEVELOPMENT BRIEF</span><h2>정책과 도시의 새로운 움직임</h2><p>뉴스 원문 링크와 출처를 함께 제공하는 정보 섹션입니다.</p></div><a class="r-section-more" href="/news" data-nav="news">뉴스룸 전체 보기 ↗</a></div><div class="r-news-layout"><a class="r-news-feature" href="/guide" data-nav="guide"><span>RE:LAND EXPLAINER</span><h3>정비구역 지정부터 준공까지<br>꼭 알아야 할 여섯 단계</h3><p>처음 시작하는 사람을 위한 도시정비사업 가이드.</p><b>재개발 기초 가이드 →</b></a><div id="r-home-news" class="r-news-items"><p class="r-placeholder">공개 뉴스 피드를 확인하고 있습니다.</p></div></div></div></section>
    <section class="r-last-cta"><div class="shell r-last-cta-inner"><div><span>RE:LAND COMMUNITY</span><h2>도시의 내일을, 이웃과 함께.</h2><p>지역 소식을 공유할 동네사랑방을 열어 보세요.</p></div><button class="r-section-button" data-action="create-community">Google 블로그 동네사랑방 만들기 ↗</button></div></section>`;
    // The map is real, using the existing Google Maps -> OpenStreetMap fallback.
    if(STATE.config?.google_maps_browser_key){
      showDistrictMap(districts,'home-real-map',9,[37.53,126.99]).catch(()=>{const el=$('#home-real-map');if(el)el.textContent='지도를 표시하지 못했습니다. 전국 지도에서 다시 확인해 주세요.'});
    }else{
      const mapTarget=$('#home-real-map');
      if(mapTarget)mapTarget.innerHTML='<iframe class="r-google-iframe" title="Google 지도: 서울 및 수도권 위치 참고용" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q=37.5665%2C126.9780&z=11&output=embed"></iframe><div class="map-top-label">Google 지도 · 위치 참고용 (구역별 마커 아님)</div><a class="r-map-open-google" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps?q=37.5665%2C126.9780">Google 지도에서 열기 ↗</a>';
    }
    videoPromise.then(videos=>{const n=$('#r-home-videos');if(n&&['/',''].includes(location.pathname)){n.innerHTML=videoCards(videos,4);const note=$('#r-youtube-source');if(note&&videos.length)note.textContent='외부 제작자의 실제 YouTube 썸네일과 원문 링크를 연결합니다. 개별 영상의 법률 의견은 해당 제작자의 것이며, 조회수는 추정하지 않습니다.'}}).catch(()=>{});
    blogPromise.then(items=>{const n=$('#r-blog-content');if(n&&['/',''].includes(location.pathname))n.innerHTML=postsMarkup(items,true)}).catch(()=>{});
    newsPromise.then(d=>{const n=$('#r-home-news');if(!n||!['/',''].includes(location.pathname))return;const items=Array.isArray(d.items)?d.items.slice(0,4):[];STATE.news=items;n.innerHTML=items.length?items.map((a,i)=>`<a href="${A(a.url)}" target="_blank" rel="noopener noreferrer"><span>${String(i+1).padStart(2,'0')}</span><div><strong>${E(a.title)}</strong><small>${E(a.source)} · ${E(a.published)}</small></div><b>↗</b></a>`).join(''):'<div class="r-news-empty">현재 확인된 새로운 뉴스 피드가 없습니다. <a href="/news" data-nav="news">뉴스룸 보기 →</a></div>'}).catch(()=>{});
  }
  async function youtubePageV2(){
    main.innerHTML=`<section class="r-youtube-hero"><div class="shell"><span class="r-overline">RE:LAND VIDEO LIBRARY</span><h1>도시를 이해하는 영상</h1><p>재개발·재건축 관련 영상과 해설 강의를 한눈에 만나보세요. 외부 영상은 YouTube의 원 게시자에게 연결됩니다.</p></div></section><section class="r-section"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">FEATURED TOPICS</span><h2>주제로 찾아보는 YouTube</h2><p>정비사업 절차, 조합 운영, 분담금, 보상·이주를 주제별로 탐색합니다.</p></div></div><div class="r-video-grid">${VIDEO_TOPICS.map(topicCard).join('')}</div></div></section><section class="r-section r-video-section"><div class="shell"><div class="r-section-heading"><div><span class="r-overline">EDITOR-REVIEWED YOUTUBE</span><h2>등록된 재개발 영상</h2><p>출처가 확인된 외부 공개 영상과 관리자가 등록한 영상을 함께 보여드립니다.</p></div></div><div id="r-youtube-verified" class="r-video-grid"><p class="r-placeholder">YouTube 콘텐츠를 확인 중입니다.</p></div></div></section>`;
    const list=await verifiedVideos();const target=$('#r-youtube-verified');if(target)target.innerHTML=list.length?list.map(youtubeCard).join(''):`<div class="r-youtube-empty"><h3>관리자 검수 영상은 아직 등록되지 않았습니다.</h3><p>위의 검색 카드에서 YouTube에 공개된 관련 영상을 살펴볼 수 있습니다. 허위 영상 ID나 가상의 조회수는 표시하지 않습니다.</p><a href="/kang/">강실장 교육자료 60강 보기 →</a></div>`;
  }
  window.relandHomeV2=homePageV2;
  window.relandYoutubeV2=youtubePageV2;
})();
