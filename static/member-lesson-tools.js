/* Integrated with RE:LAND's existing Google/Neon session and member progress API. */
(()=>{'use strict';
 const matched=location.pathname.match(/^\/rights-analysis\/lesson-(\d{1,2})\/?$/);
 if(!matched)return;
 const lesson=Number(matched[1]);if(!Number.isInteger(lesson)||lesson<1||lesson>24)return;
 const block=document.querySelector('.lead-card');if(!block)return;
 const panel=document.createElement('div');panel.className='member-learning-tools';
 panel.innerHTML='<span class="member-tools-note">이 강의 학습 기록</span><div class="member-tools-actions"><button type="button" id="lessonComplete" aria-pressed="false">학습 완료</button><button type="button" id="lessonSave" aria-pressed="false">☆ 강의 저장</button><a href="/mypage">마이페이지 ↗</a></div><p id="lessonState" role="status" aria-live="polite">기록을 확인하는 중입니다.</p>';
 block.appendChild(panel);
 const status=panel.querySelector('#lessonState');const completed=panel.querySelector('#lessonComplete');const saved=panel.querySelector('#lessonSave');
 let state={status:'not_started',saved:0};
 async function req(path,opts={}){const o={credentials:'same-origin',cache:'no-store',...opts};if(o.body&&typeof o.body!=='string')o.body=JSON.stringify(o.body);if(o.method){o.headers={'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest',...(o.headers||{})}}const resp=await fetch(path,o);const d=await resp.json().catch(()=>({}));if(!resp.ok)throw Error(d.detail||'학습 기록을 저장할 수 없습니다.');return d}
 function paint(){completed.setAttribute('aria-pressed',String(state.status==='completed'));completed.classList.toggle('on',state.status==='completed');completed.textContent=state.status==='completed'?'✓ 학습 완료됨':'학습 완료';saved.setAttribute('aria-pressed',String(!!state.saved));saved.classList.toggle('on',!!state.saved);saved.textContent=state.saved?'★ 저장됨':'☆ 강의 저장'}
 async function put(data){const resp=await req('/api/member/lessons/'+lesson,{method:'PUT',body:data});state=resp.lesson;paint();status.textContent='학습 기록을 저장했습니다.'}
 completed.addEventListener('click',()=>put({status:state.status==='completed'?'in_progress':'completed'}).catch(e=>status.textContent=e.message));
 saved.addEventListener('click',()=>put({saved:!state.saved}).catch(e=>status.textContent=e.message));
 (async()=>{try{const data=await req('/api/member/learning');const prev=data.lessons.find(l=>l.lesson_no===lesson);if(prev){state=prev;paint();status.textContent=state.status==='completed'?'완료한 강의입니다.':'학습 중인 강의입니다.'}else{await put({status:'in_progress'});status.textContent='학습을 시작했습니다.'}}catch(e){status.textContent='로그인한 회원만 학습 기록을 남길 수 있습니다.'}})();
})();
