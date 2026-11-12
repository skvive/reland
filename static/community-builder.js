/* RE:LAND Community Builder – native Blogger XML export, owner-proof registration. */
'use strict';
(() => {
  const $ = (id) => document.getElementById(id);
  const regionList = ['서울','경기','인천','부산','대구','대전','광주','울산','세종','충북','충남','전북','전남','경북','경남','강원','제주','전국'];
  const themes = {
    forest: {dark:'#19483a',mid:'#3f8564',light:'#e6f4e7'},
    navy: {dark:'#19314d',mid:'#4c779e',light:'#e7eef7'},
    warm: {dark:'#71432e',mid:'#bd8060',light:'#f8ece2'}
  };
  const state = {id:null, user:null, code:null};
  const escapeXml = (s) => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&apos;');
  const getVal = (id) => $(id).value.trim();
  const setStatus = (msg, isError = false) => { $('status').textContent = msg; $('status').classList.toggle('error', isError); };
  const selectedTheme = () => document.querySelector('input[name=theme]:checked')?.value || 'forest';
  const safeBand = () => {
    const raw = getVal('band-url');
    if (!raw) return '';
    let u;
    try { u = new URL(raw); } catch { throw new Error('네이버 BAND 주소를 확인해 주세요.'); }
    if (u.protocol !== 'https:' || !['band.us','www.band.us'].includes(u.hostname) || u.port || !/^\/[A-Za-z0-9@/_-]{1,140}$/.test(u.pathname) || u.pathname.includes('//')) {
      throw new Error('https://band.us/ 형태의 BAND 커뮤니티 링크만 사용해 주세요.');
    }
    return 'https://band.us' + u.pathname.replace(/\/$/,'');
  };
  const validate = (needBlog) => {
    const name = getVal('community-name'), description = getVal('community-description'), region = getVal('community-region'), theme_slug = getVal('community-theme');
    if (name.length < 3 || name.length > 60) throw new Error('사랑방 이름은 3~60자로 입력해 주세요.');
    if (description.length < 8 || description.length > 450) throw new Error('동네 소개는 8~450자로 입력해 주세요.');
    if (!regionList.includes(region)) throw new Error('지역을 선택해 주세요.');
    if (!['neighborhood','operations','moving','busan','seoul','qa','academy','law','chungcheong'].includes(theme_slug)) throw new Error('소속 테마판을 선택해 주세요.');
    const band = safeBand();
    const blogUrl = getVal('blog-url');
    if (needBlog && !/^https:\/\/[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.blogspot\.com\/?$/i.test(blogUrl)) {
      throw new Error('개설한 블로그 주소를 https://이름.blogspot.com/ 형식으로 입력해 주세요.');
    }
    return {name, description, region, theme_slug, band, blog_url:blogUrl};
  };
  const renderPreview = () => {
    $('preview-name').textContent = getVal('community-name') || '우리 동네 사랑방';
    $('preview-description').textContent = getVal('community-description') || '동네 이야기를 함께 만드는 공간';
    const colors = themes[selectedTheme()] || themes.forest;
    $('preview-hero').style.background = 'linear-gradient(120deg,'+colors.dark+','+colors.mid+')';
    $('band-sample').classList.toggle('hidden', !getVal('band-url'));
  };
  const buildXml = (v) => {
    const colors = themes[selectedTheme()] || themes.forest;
    const title = escapeXml(v.name);
    const intro = escapeXml(v.description);
    const band = v.band ? `<div class='band-link'><a href='${escapeXml(v.band)}' target='_blank' rel='noopener noreferrer'>네이버 BAND에서 이웃들과 더 소통하기 ↗</a></div>` : '';
    // Blogger's Blog widget owns actual posts and native Google comments.
    // Operators publish official notices as posts tagged "공지".
    return `<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html>
<html b:css='false' b:defaultwidgetversion='2' b:layoutsVersion='3' b:responsive='true' xmlns='http://www.w3.org/1999/xhtml' xmlns:b='http://www.google.com/2005/gml/b' xmlns:data='http://www.google.com/2005/gml/data' xmlns:expr='http://www.google.com/2005/gml/expr'>
<head>
<meta content='width=device-width, initial-scale=1' name='viewport'/>
<title><data:blog.pageTitle/></title>
<b:include data='blog' name='all-head-content'/>
<b:skin><![CDATA[
*{box-sizing:border-box}body{margin:0;background:#f7f9f6;color:#17372d;font-family:'Noto Sans KR','Malgun Gothic',sans-serif;line-height:1.85;word-break:keep-all}a{color:inherit}.top{background:${colors.dark};color:#fff;padding:62px max(22px,calc((100vw - 1000px)/2));}.top small{font-size:11px;letter-spacing:.24em;color:#d5eadc}.top h1{font-size:clamp(30px,5vw,53px);margin:9px 0;line-height:1.4}.top p{max-width:700px;font-size:14px;color:#e4eee8}.shell{width:min(1000px,calc(100% - 32px));margin:0 auto}.bar{background:white;border-bottom:1px solid #dfe9e1;padding:16px 0}.bar a{display:inline-block;text-decoration:none;font-size:13px;font-weight:bold;color:${colors.dark};margin-right:24px}.welcome{background:white;border:1px solid #e3ebe5;border-radius:14px;margin:28px 0;padding:22px 24px}.welcome strong{color:${colors.dark};font-size:15px}.welcome p{font-size:13px;color:#6b8375;margin:8px 0 0}.section-caption{font-size:12px;font-weight:bold;color:${colors.mid};margin-top:32px;letter-spacing:.06em}.blog-posts,.post-outer{background:#fff;border-radius:15px}.post-outer{margin:0 0 18px;padding:20px;border:1px solid #e5ede7}.post-title{font-size:23px;letter-spacing:-.03em}.post-body{font-size:14px;overflow-wrap:anywhere}.post-footer,.post-timestamp{font-size:12px;color:#728c7c}.comments{padding:18px;background:#f2f6f2;border-radius:12px}.band-link{margin:24px 0}.band-link a{display:block;text-align:center;background:#2fba56;color:#fff;font-size:14px;text-decoration:none;font-weight:bold;border-radius:12px;padding:16px}.foot{background:${colors.dark};color:#dbede1;font-size:11px;text-align:center;margin-top:70px;padding:27px 20px}.foot a{color:#d8f7df}@media(max-width:650px){.top{padding:42px 22px}.shell{width:calc(100% - 24px)}.post-outer{padding:17px}.bar a{margin-right:12px}.welcome{padding:20px}}
]]></b:skin>
</head>
<body>
<header class='top'><small>RE:LAND · OUR NEIGHBORHOOD</small><h1>${title}</h1><p>${intro}</p></header>
<div class='bar'><nav class='shell' aria-label='동네사랑방 메뉴'><a expr:href='data:blog.homepageUrl'>전체 소식</a><a href='/search/label/공지'>운영자 공지</a><a href='https://reland.lexid.site/community'>RE:LAND 동네사랑방</a></nav></div>
<main class='shell'>
<section class='welcome'><strong>동네 소식을 전하고 이웃의 이야기를 듣습니다.</strong><p>운영자 공지는 '공지' 라벨로 게시합니다. 각 글의 댓글을 이용하면 이웃들과 답글을 나눌 수 있습니다. 댓글 이용 여부는 블로그 관리자 설정을 따릅니다.</p></section>
${band}
<p class='section-caption'>LOCAL STORIES · 우리동네 게시판</p>
<b:section class='main' id='main' maxwidgets='1' showaddelement='no'>
<b:widget id='Blog1' locked='true' title='동네 소식' type='Blog' version='2' visible='true'/>
</b:section>
</main>
<footer class='foot'>${title} · Powered by Blogger · <a href='https://reland.lexid.site/'>RE:LAND</a></footer>
</body></html>`;
  };
  async function api(path, opts = {}) {
    const res = await fetch('/api'+path, {credentials:'same-origin',headers:{'Content-Type':'application/json'},...opts});
    let data;
    try { data=await res.json(); } catch {throw new Error('서버 응답을 확인할 수 없습니다.');}
    if (!res.ok) throw new Error(typeof data.detail==='string' ? data.detail : '요청에 실패했습니다. 다시 시도해 주세요.');
    return data;
  }
  const busy = (button, flag) => {button.disabled=flag;button.setAttribute('aria-busy',String(flag));};
  const downloadTheme = () => {
    try {
      const v=validate(false);
      const xml=buildXml(v);
      const fileName='RELAND-neighborhood-theme-'+selectedTheme()+'.xml';
      const blob = new Blob([xml],{type:'application/xml;charset=utf-8'});
      const url=URL.createObjectURL(blob);
      const anchor=document.createElement('a');anchor.href=url;anchor.download=fileName;document.body.appendChild(anchor);anchor.click();anchor.remove();
      setTimeout(()=>URL.revokeObjectURL(url),15000);
      setStatus('Blogger XML 템플릿을 생성했습니다. Blogger 테마 메뉴에서 설치해 주세요.');
    } catch(e) {setStatus(e.message,true);}
  };
  async function registerCommunity() {
    const btn=$('register-community');
    try {
      const v=validate(true);
      if (!state.user) throw new Error('RE:LAND 로그인 후 사랑방을 등록할 수 있습니다. 먼저 리랜드에서 로그인해 주세요.');
      busy(btn,true);setStatus('소유 확인 코드를 준비하고 있습니다.');
      if (!state.id) {
        const created=await api('/communities',{method:'POST',body:JSON.stringify({name:v.name,description:v.description,region:v.region,theme_slug:v.theme_slug})});
        state.id=created.id;
      }
      const claim=await api('/communities/'+state.id+'/blog/claim',{method:'POST',body:JSON.stringify({blog_url:v.blog_url})});
      state.code=claim.verification_code;
      $('verify-code').textContent=claim.verification_code;
      $('verify-input').value=claim.verification_code;
      $('verify-area').classList.remove('hidden');
      $('verify-area').scrollIntoView({behavior:'smooth',block:'center'});
      setStatus('확인 코드를 발급했습니다. Blogger 공개 게시글에 코드를 게시해 주세요.');
    } catch(e) { setStatus(e.message,true); }
    finally {busy(btn,false);}
  }
  async function verifyCommunity() {
    const btn=$('verify-community');
    try {
      if (!state.id) throw new Error('먼저 사랑방을 등록해 주세요.');
      const v=validate(true);
      const code=getVal('verify-input');
      if (!code) throw new Error('확인 코드를 입력해 주세요.');
      busy(btn,true);setStatus('Blogger의 공개 게시물에서 소유 확인 코드를 검사합니다.');
      await api('/communities/'+state.id+'/blog/verify',{method:'POST',body:JSON.stringify({verification_code:code})});
      if (v.band) await api('/communities/'+state.id+'/band',{method:'PUT',body:JSON.stringify({band_url:v.band})});
      $('verify-area').classList.add('hidden');
      $('register-community').disabled=true;
      $('finish-area').classList.remove('hidden');
      $('community-link').href='/community/'+state.id;
      setStatus('Google 블로그 소유 확인 및 동네사랑방 등록이 완료되었습니다.');
    } catch(e) {setStatus(e.message,true);}
    finally {busy(btn,false);}
  }
  async function boot() {
    for (const region of regionList) {
      const option=document.createElement('option');option.value=region;option.textContent=region;$('community-region').append(option);
    }
    for (const id of ['community-name','community-description','community-region','band-url'])
      $(id).addEventListener('input',renderPreview);
    document.querySelectorAll('input[name=theme]').forEach(el=>el.addEventListener('change',renderPreview));
    $('download-theme').addEventListener('click',downloadTheme);
    $('register-community').addEventListener('click',registerCommunity);
    $('verify-community').addEventListener('click',verifyCommunity);
    $('copy-code').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(state.code||'');setStatus('확인 코드를 복사했습니다.');}catch{setStatus('복사에 실패했습니다. 표시된 코드를 직접 복사하세요.',true);}});
    try {
      const data=await api('/auth/me');
      state.user=data.user;
      $('auth-state').textContent=state.user?'로그인 확인: '+state.user.nickname+' · Blogger 소유 확인 후 등록할 수 있습니다.':'로그인이 필요합니다. 리랜드로 돌아가 Google 계정으로 로그인하세요.';
      if (!state.user) $('auth-state').insertAdjacentHTML('beforeend',' <a href="/community">리랜드에서 로그인하기 ↗</a>');
    } catch { $('auth-state').textContent='RE:LAND 로그인 상태를 확인할 수 없습니다.'; }
    renderPreview();
  }
  document.addEventListener('DOMContentLoaded',boot);
})();
