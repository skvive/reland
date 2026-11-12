/* RE:LAND theme board — parent editorial board → local communities → Blogger. */
'use strict';
(() => {
  const $ = (s) => document.querySelector(s);
  const themes = [
    ['neighborhood','우리동네 소식판'],
    ['operations','동네모임 운영판'],
    ['moving','입주·이주 정보판'],
    ['busan','부산·영남 동네판'],
    ['seoul','서울 정비사업판'],
    ['qa','재개발 질문·답변판'],
    ['academy','재개발 강실장 클래스'],
    ['law','RE:LAND 법률지식'],
    ['chungcheong','청주·충청 동네판']
  ];
  const page = decodeURIComponent(location.pathname.split('/').filter(Boolean).pop() || '');
  const state = {board:null, user:null, posts:[], filter:'all'};
  const regions = ['전국','서울','경기','인천','부산','대구','대전','광주','울산','세종','충북','충남','전북','전남','경북','경남','강원','제주'];
  const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  const photo = i => {
    return `style="--board-image:url('/static/assets/boards/cover-${String(i+1).padStart(2,'0')}.jpg')"`;
  };
  const msg = (s, bad=false) => {
    const n=$('#toast');n.textContent=s;n.className=bad?'show bad':'show';
    clearTimeout(msg.timeout);msg.timeout=setTimeout(()=>n.className='',4300);
  };
  const api=async(path,opts={})=>{
    const res=await fetch('/api'+path,{credentials:'same-origin',headers:{'Content-Type':'application/json'},...opts});
    let json;try{json=await res.json()}catch{throw Error('서버 응답을 읽을 수 없습니다.')};
    if(!res.ok)throw Error(typeof json.detail==='string'?json.detail:'다시 시도해 주세요.');
    return json;
  };
  const fmt = str => {
    const d=new Date(str);return isNaN(d.getTime())?'':d.toLocaleDateString('ko-KR');
  };
  const hasBlogger = c => Boolean(c.blog_url && /^https:\/\/[a-z0-9-]+\.blogspot\.com\/?$/i.test(c.blog_url));
  const memberCard = c => {
    const blog=hasBlogger(c), url=blog?c.blog_url:'/community/'+Number(c.id);
    return `<a class="member-card" href="${esc(url)}" target="_blank" rel="noopener noreferrer">
      <div class="member-cover" ${photo(state.board.image_index)}><span>${esc(c.region)}</span></div>
      <div class="member-content"><small>${blog?(c.blog_verified?'✓ Blogger 소유 확인':'공개 Blogger 링크'):'RE:LAND 지역 게시판'}</small>
      <h3>${esc(c.name)}</h3><p>${esc(c.description)}</p>
      <div class="member-footer"><span>이웃 ${Number(c.followers)||0}명</span><strong>${blog?'블로그 보기 ↗':'지역모임 보기 ↗'}</strong></div></div></a>`;
  };
  const postCard=p=>`<article class="post" data-kind="${esc(p.kind)}"><header>
    <span class="tag ${p.kind==='notice'?'notice':p.kind==='question'?'question':''}">${p.kind==='notice'?'운영자 공지':p.kind==='question'?'질문·답변':'이웃 이야기'}</span>
    <small>${esc(p.nickname||p.author_label||'이웃')} · ${fmt(p.created_at)}</small></header>
    <h3><button type="button" data-post="${Number(p.id)}">${esc(p.title)}</button></h3>
    <p>${esc(p.body).slice(0,250)}</p><footer><span>♡ ${Number(p.like_count)||0} · 댓글 ${Number(p.comment_count)||0}</span>
    <button data-post="${Number(p.id)}" class="read">이야기 읽기 ↗</button></footer></article>`;
  const featureLink=()=>{
    if(page==='qa')return '<a class="secondary" href="/kang/qa/" target="_blank" rel="noopener noreferrer">강실장 Q&A 30선 읽기 ↗</a>';
    if(page==='academy')return '<a class="secondary" href="/kang/" target="_blank" rel="noopener noreferrer">강실장 클래스 열기 ↗</a>';
    if(page==='law')return '<a class="secondary" href="/columns" target="_blank" rel="noopener noreferrer">법률 저널 120편 읽기 ↗</a>';
    if(page==='seoul')return '<a class="secondary" href="/map?region=%EC%84%9C%EC%9A%B8" target="_blank" rel="noopener noreferrer">서울 정비사업 지도 ↗</a>';
    return '';
  };
  const render=()=>{
    const b=state.board;
    document.title=b.title+' | RE:LAND 동네사랑방';
    $('#page').innerHTML=`<div class="app-shell">
      <aside class="sidebar"><div class="side-kicker">NEIGHBORHOOD CHANNELS</div><h2>테마별 본사판</h2>
      <nav class="side-nav" aria-label="테마판 이동">${themes.map(([slug,title],i)=>`<a href="/board/${slug}" target="_self" class="${slug===page?'active':''}"><span class="side-dot">${String(i+1).padStart(2,'0')}</span>${esc(title)}<span class="side-next">↗</span></a>`).join('')}</nav>
      <div class="sidebar-guide"><b>이 공간은 이렇게 운영됩니다</b><p>본사판에서 공지와 질문을 읽고, 지역모임으로 이동해 개별 Blogger와 연결됩니다. 법정 조합의 공식 통지 기능과는 다릅니다.</p></div></aside>
      <div class="main-panel">
        <section class="board-hero" ${photo(b.image_index)}>
          <div class="hero-overlay"><span class="eyebrow">RE:LAND EDITORIAL BOARD · ${esc(b.eyebrow)}</span><h1>${esc(b.title)}</h1>
          <p>${esc(b.description)}</p><div class="hero-actions"><button id="write-board" class="primary">＋ 이 판에 글 남기기</button>${featureLink()}</div>
          </div></section>
        <div class="stats"><span><b>${Number(b.local_count)||0}</b> 연결된 지역모임</span><span><b>${Number(b.post_count)||0}</b> 본사판 게시글</span><span><b>무료</b> 이웃 참여</span></div>
        <section class="area">
          <div class="area-head"><div><small>01 · LOCAL COMMUNITY NETWORK</small><h2>우리 지역 작은 사랑방</h2><p>지역별 커뮤니티로 이동해 동네 소식과 Blogger 글을 만나보세요.</p></div>
          <a class="add-link" href="/community/builder" target="_blank" rel="noopener noreferrer">＋ 우리 동네 사랑방 만들기 ↗</a></div>
          <form class="controls" id="search-local"><label class="visually-hidden" for="local-q">지역모임 검색</label><input id="local-q" placeholder="동네 이름이나 모임 검색" maxlength="80">
          <label class="visually-hidden" for="local-region">지역 선택</label><select id="local-region">${regions.map(x=>`<option>${x}</option>`).join('')}</select><button type="submit">검색</button></form>
          <div class="member-grid" id="local-list">${b.communities.length?b.communities.map(memberCard).join(''):'<div class="blank"><b>첫 번째 지역모임을 기다립니다</b><p>아직 이 테마에 등록된 지역 사랑방이 없습니다. 무료 Blogger 블로그를 만들고 연결할 수 있습니다.</p><a href="/community/builder" target="_blank" rel="noopener noreferrer">무료 사랑방 만들기 ↗</a></div>'}</div>
        </section>
        <section class="area area-feed">
          <div class="area-head"><div><small>02 · NOTICE & CONVERSATION</small><h2>본사판 공지 · 이웃 소통</h2><p>운영자가 공지를 전달하고 이웃들이 댓글로 소통합니다.</p></div><button id="write-board-secondary" class="outline">글쓰기 +</button></div>
          <div class="tabs" role="group" aria-label="게시글 분류"><button class="active" data-filter="all">전체</button><button data-filter="notice">운영자 공지</button><button data-filter="discussion">동네 이야기</button><button data-filter="question">질문·답변</button></div>
          <div id="posts-list">${state.posts.length?state.posts.map(postCard).join(''):'<div class="blank"><b>아직 등록된 게시글이 없습니다.</b><p>동네 이야기나 궁금한 점을 처음으로 남겨보세요.</p></div>'}</div>
        </section>
        <div class="end-cta"><div><small>OUR NEIGHBORHOOD, TOGETHER</small><h2>우리 동네에도 사랑방을 열어 보세요.</h2><p>동네 이름·색상만 정하면 Google Blogger 템플릿을 무료로 만들 수 있습니다.</p></div><a href="/community/builder" target="_blank" rel="noopener noreferrer">무료 템플릿 만들기 ↗</a></div>
      </div></div>`;
    $('#search-local').addEventListener('submit',searchLocal);
    $('#write-board').addEventListener('click',writeModal);
    $('#write-board-secondary').addEventListener('click',writeModal);
    document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',()=>{state.filter=el.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===el));renderPosts();}));
    document.querySelectorAll('[data-post]').forEach(el=>el.addEventListener('click',()=>postModal(Number(el.dataset.post))));
  };
  const renderPosts=()=>{
    const items=state.posts.filter(p=>state.filter==='all'||p.kind===state.filter);
    $('#posts-list').innerHTML=items.length?items.map(postCard).join(''):'<div class="blank">이 분류에는 아직 게시물이 없습니다.</div>';
    document.querySelectorAll('[data-post]').forEach(el=>el.addEventListener('click',()=>postModal(Number(el.dataset.post))));
  };
  const searchLocal=async(e)=>{
    e.preventDefault();
    const q=$('#local-q').value, region=$('#local-region').value;
    try {
      const r=await api('/boards/'+encodeURIComponent(page)+'?'+new URLSearchParams({q,region}));
      state.board.communities=r.item.communities;
      $('#local-list').innerHTML=r.item.communities.length?r.item.communities.map(memberCard).join(''):'<div class="blank">검색 조건에 맞는 지역모임이 없습니다.</div>';
    } catch(e) {msg(e.message,true);}
  };
  const openDialog=(title,html)=>{
    $('#dialog-title').textContent=title;$('#dialog-body').innerHTML=html;$('#layer').classList.remove('hidden');
    document.body.classList.add('modal-open');
    $('#close-dialog').focus();
  };
  const closeDialog=()=>{$('#layer').classList.add('hidden');document.body.classList.remove('modal-open');};
  const writeModal=()=>{
    if(!state.user){openDialog('로그인이 필요합니다','<p>RE:LAND Google 계정으로 로그인하면 동네판에 글을 쓸 수 있습니다.</p><p><a class="primary buttonish" href="/community" target="_blank" rel="noopener noreferrer">리랜드에서 로그인하기 ↗</a></p>');return}
    const admin=state.user.role==='admin';
    openDialog('이웃들과 이야기 나누기',`<form id="new-post">
      <label>글 유형<select name="kind"><option value="discussion">동네 이야기</option><option value="question">질문·답변</option>${admin?'<option value="notice">운영자 공지</option>':''}</select></label>
      <label>글 제목<input name="title" minlength="5" maxlength="120" required placeholder="동네 소식을 제목으로 적어주세요"></label>
      <label>내용<textarea name="body" minlength="10" maxlength="5000" rows="8" required placeholder="확인되지 않은 정보·다른 사람의 개인정보는 게시하지 마세요."></textarea></label>
      <p class="micro">운영자 공지는 관리자만 게시할 수 있습니다. 모든 글은 RE:LAND 본사판 DB에 저장되며 Blogger로 자동 발행되지 않습니다.</p>
      <button class="primary submit" type="submit">게시하기</button></form>`);
    $('#new-post').addEventListener('submit',async(e)=>{
      e.preventDefault();const f=e.currentTarget,b=f.querySelector('button[type=submit]');b.disabled=true;
      const data=Object.fromEntries(new FormData(f));
      try{await api('/posts',{method:'POST',body:JSON.stringify({...data,community_id:state.board.id})});closeDialog();msg('게시글이 등록되었습니다.');await reloadPosts();}catch(err){msg(err.message,true)}finally{b.disabled=false}
    });
  };
  const postModal=async(id)=>{
    try{
      const {item,comments}=await api('/posts/'+id);
      openDialog(item.title,`<div class="article"><p class="article-meta">${esc(item.nickname||item.author_label||'이웃')} · ${fmt(item.created_at)} · ${item.kind==='notice'?'운영자 공지':item.kind==='question'?'질문':'동네 이야기'}</p><div class="body">${esc(item.body)}</div></div><h3 class="comments-title">이웃 댓글 ${comments.length}</h3><div class="comments">${comments.length?comments.map(x=>`<div class="reply"><strong>${esc(x.nickname||'이웃')}</strong><small>${fmt(x.created_at)}</small><p>${esc(x.body)}</p></div>`).join(''):'<p class="micro">아직 등록된 댓글이 없습니다.</p>'}</div><form id="reply-form"><label>댓글<textarea name="body" rows="3" minlength="2" maxlength="1600" required placeholder="상대방을 존중하며 의견을 남겨 주세요."></textarea></label><button class="primary submit" type="submit">댓글 등록</button></form>`);
      $('#reply-form').addEventListener('submit',async(e)=>{
        e.preventDefault();
        if(!state.user){msg('먼저 RE:LAND에 로그인해 주세요.',true);return}
        const btn=e.currentTarget.querySelector('button');btn.disabled=true;
        try{await api('/posts/'+id+'/comments',{method:'POST',body:JSON.stringify({body:e.currentTarget.querySelector('textarea').value})});msg('댓글이 등록됐습니다.');await reloadPosts();await postModal(id);}
        catch(err){msg(err.message,true)}finally{btn.disabled=false}
      });
    }catch(e){msg(e.message,true)}
  };
  const reloadPosts=async()=>{
    const r=await api('/posts?community_id='+state.board.id+'&limit=100');
    state.posts=r.items;state.board.post_count=r.items.length;render();
    if(state.filter!=='all'){document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x.dataset.filter===state.filter));renderPosts()}
  };
  const start=async()=>{
    $('#close-dialog').addEventListener('click',closeDialog);
    $('#layer').addEventListener('click',e=>{if(e.target===$('#layer'))closeDialog()});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDialog()});
    if(!themes.some(x=>x[0]===page)){$('#page').innerHTML='<div class="loader">존재하지 않는 테마판입니다. <a href="/community">돌아가기</a></div>';return}
    try{
      const [board,auth]=await Promise.all([api('/boards/'+page),api('/auth/me').catch(()=>({user:null}))]);
      state.board=board.item;state.user=auth.user||null;
      const posts=await api('/posts?community_id='+board.item.id+'&limit=100');
      state.posts=posts.items;render();
    }catch(e){$('#page').innerHTML='<div class="loader">테마판을 불러오지 못했습니다. '+esc(e.message)+' <a href="/community">커뮤니티로 돌아가기</a></div>'}
  };
  document.addEventListener('DOMContentLoaded',start);
})();