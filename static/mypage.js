'use strict';
const $ = s => document.querySelector(s);
const safe = text => String(text ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&quot;'}[c]));
const titles=['권리분석의 역할과 판단 순서','물권과 채권의 기초','등기사항증명서 읽는 순서','권리순위와 기준권리','소유권·공유지분·상속','저당권과 근저당권','가압류·압류·가처분','주택임대차 대항력','소액임차인 최우선변제','상가건물 임대차 분석','법원경매 핵심 서류 3종','경매 절차와 입찰 준비','경매의 인수·소멸 위험','배당요구와 배당 계산 기초','점유·명도·인도 위험','유치권과 법정지상권','건축물·토지 공적장부 대조','토지이용계획과 공법상 제한','재개발·재건축 권리 분석','공매·체납처분의 구조','조세·법정기일과 우선순위','투자수익·입찰상한 계산','통합 권리분석 보고서 작성','종합 사례연습과 모의평가'];
let learning=null, activity=null, filter='all';
async function request(path,options={}){
  const method=(options.method||'GET').toUpperCase();
  const opts={credentials:'same-origin',cache:'no-store',...options};
  if (opts.body && typeof opts.body!=='string') opts.body=JSON.stringify(opts.body);
  if (method!=='GET') opts.headers={'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest',...(opts.headers||{})};
  const res=await fetch(path,opts);const value=await res.json().catch(()=>({}));
  if(!res.ok)throw Error(value.detail||'요청을 처리하지 못했습니다.');return value;
}
function announce(msg){$('#status').textContent=msg;}
function show(el){$(el).classList.remove('hidden')}
function timeLabel(v){if(!v)return '';const t=new Date(v);return isNaN(+t)?'':t.toLocaleDateString('ko-KR')}
function lessonState(number){const row=learning.lessons.find(x=>x.lesson_no===number);return row||{status:'not_started',saved:0}}
function render(){
  const user=learning.member;$('#memberName').textContent=user.nickname+'님, 안녕하세요.';$('#memberEmail').textContent=user.email||'연결된 계정';
  $('#avatar').textContent=user.nickname.slice(0,1)||'R';
  if(user.avatar){try{const u=new URL(user.avatar);if(u.protocol==='https:'&&/(^|\.)googleusercontent\.com$/.test(u.hostname)){const image=document.createElement('img');image.src=u.href;image.alt='';image.referrerPolicy='no-referrer';$('#avatar').replaceChildren(image)}}catch{}}
  $('#completedCount').innerHTML=learning.summary.completed+'<span>/24강</span>';$('#startedCount').innerHTML=learning.summary.in_progress+'<span>강</span>';$('#savedCount').innerHTML=learning.summary.saved_lessons+'<span>강</span>';$('#watchCount').innerHTML=(activity.watches||[]).length+'<span>곳</span>';
  $('#progressBar').style.width=Math.round(learning.summary.completed/24*100)+'%';$('#progressText').textContent=`${learning.summary.completed}강 완료 · 전체 24강`;
  const continuing=[...learning.lessons].filter(r=>r.status==='in_progress').sort((a,b)=>String(b.updated_at).localeCompare(String(a.updated_at)))[0];
  const next=continuing?.lesson_no||titles.findIndex((_,i)=>lessonState(i+1).status!=='completed')+1||24;
  $('#continueArea').innerHTML=`<a href="/rights-analysis/lesson-${String(next).padStart(2,'0')}" target="_blank" rel="noopener noreferrer"><span>${continuing?'이어서 학습하기':'다음 강의 학습하기'} · ${next}강 ${safe(titles[next-1])}</span><span aria-hidden="true">↗</span></a>`;
  $('#nickname').value=user.nickname;$('#bio').value=user.bio||'';$('#blog_url').value=user.blog_url||'';
  renderLessons();
  fillRows('#watchedAreas',(activity.watches||[]).slice(0,8).map(x=>({href:'/district/'+x.id,title:x.name,meta:`${x.province} ${x.city} · ${x.stage}`})),'관심등록한 정비구역이 없습니다.');
  fillRows('#savedArticles',(learning.saved_posts||[]).map(x=>({href:'/post/'+x.id,title:x.title,meta:timeLabel(x.created_at)})),'저장한 게시글이 없습니다.');
  fillRows('#myPosts',(learning.my_posts||[]).map(x=>({href:'/post/'+x.id,title:x.title,meta:timeLabel(x.created_at)})),'작성한 게시글이 없습니다.');
  fillRows('#consultations',(activity.consultations||[]).slice(0,8).map(x=>({href:'/profile',title:x.subject,meta:`${x.status} · ${timeLabel(x.created_at)}`})),'접수한 상담이 없습니다.');
}
function fillRows(sel,rows,empty){const element=$(sel);element.innerHTML=rows.length?rows.map(x=>`<a href="${safe(x.href)}">${safe(x.title)}<small>${safe(x.meta)}</small></a>`).join(''):`<p class="empty-message">${empty}</p>`;}
function renderLessons(){
 const items=titles.map((title,i)=>({title,num:i+1,row:lessonState(i+1)})).filter(x=>filter==='all'||(filter==='saved'&&x.row.saved)||(filter==='in_progress'&&x.row.status==='in_progress'));
 $('#lessons').innerHTML=items.length?items.map(({title,num,row})=>{
  const state=row.status==='completed'?'완료':row.status==='in_progress'?'학습 중':'미시작';
  return `<div class="lesson-row"><span class="lesson-index">${String(num).padStart(2,'0')}</span><div><a class="lesson-row-title" href="/rights-analysis/lesson-${String(num).padStart(2,'0')}" target="_blank" rel="noopener noreferrer">${safe(title)} ↗</a><p class="lesson-row-meta">${state}${row.updated_at?' · '+timeLabel(row.updated_at):''}</p></div><div class="lesson-actions"><button type="button" data-lesson="${num}" data-action="toggle-complete" class="${row.status==='completed'?'active':''}" aria-pressed="${row.status==='completed'}">${row.status==='completed'?'완료됨':'완료 표시'}</button><button type="button" data-lesson="${num}" data-action="toggle-save" class="bookmark ${row.saved?'active':''}" aria-pressed="${!!row.saved}" aria-label="${num}강 ${row.saved?'저장 해제':'저장'}">${row.saved?'★':'☆'}</button></div></div>`;
 }).join(''):`<p class="empty-message">이 조건에 해당하는 강의가 없습니다.</p>`;
}
async function refresh(){const [d,a]=await Promise.all([request('/api/member/learning'),request('/api/my/dashboard')]);learning=d;activity=a;render()}
async function boot(){
 try{const {user}=await request('/api/auth/me');$('#loading').classList.add('hidden');
  if(!user){show('#signedOut');const next=new URLSearchParams(location.search).get('next');if(next && /^\/rights-analysis\/(?:lesson-(?:0[1-9]|1[0-9]|2[0-4])|workbook|slides|instructor)$/.test(next))$('#loginLink').href='/?login=1&next='+encodeURIComponent(next);return}
  show('#dashboard');await refresh();
 }catch(err){$('#loading').textContent='회원 정보를 불러오지 못했습니다. '+err.message;$('#loading').classList.remove('hidden');announce(err.message)}
}
document.addEventListener('click',async e=>{
 const filterButton=e.target.closest('[data-filter]');if(filterButton){filter=filterButton.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>{b.classList.toggle('selected',b===filterButton);b.setAttribute('aria-pressed',String(b===filterButton))});renderLessons();return}
 const btn=e.target.closest('[data-lesson]');if(!btn)return;
 const n=Number(btn.dataset.lesson),row=lessonState(n);
 try{const update=btn.dataset.action==='toggle-save'?{saved:!row.saved}:{status:row.status==='completed'?'in_progress':'completed'};
 await request('/api/member/lessons/'+n,{method:'PUT',body:update});await refresh();announce(`${n}강 학습 상태가 저장됐습니다.`)}catch(err){announce(err.message)}
});
$('#profileForm').addEventListener('submit',async event=>{
 event.preventDefault();const form=event.currentTarget;const payload={nickname:form.elements.namedItem('nickname').value.trim(),bio:form.elements.namedItem('bio').value.trim(),blog_url:form.elements.namedItem('blog_url').value.trim()};
 if(payload.nickname.length<2){announce('닉네임은 두 글자 이상 입력하세요.');return}
 try{await request('/api/auth/profile',{method:'PUT',body:payload});await refresh();announce('회원 정보가 수정됐습니다.')}catch(err){announce(err.message)}
});
$('#logoutButton').addEventListener('click',async ()=>{
 try{const c=await request('/api/config');if(c.neon_auth_enabled){const base=c.neon_auth_public_url||c.neon_auth_url; if(base){try{await fetch(base.replace(/\/$/,'')+'/sign-out',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:'{}'})}catch{}}}await request('/api/auth/logout',{method:'POST'});location.href='/'}catch(e){announce(e.message)}
});
boot();
