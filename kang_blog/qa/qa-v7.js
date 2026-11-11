'use strict';
(() => {
  const data = window.KANG_DATA;
  const list = document.querySelector('#questionList');
  const search = document.querySelector('#query');
  const select = document.querySelector('#category');
  const esc = x => String(x ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&quot;'}[ch]));
  if (!data || !Array.isArray(data.qa)) { list.innerHTML='<p class="error">학습 자료를 읽지 못했습니다. <a href="/kang/">강의실에서 다시 확인</a>해주세요.</p>'; return; }
  const cats = [...new Set(data.qa.map(q=>q.category).filter(Boolean))];
  for(const c of cats) { const option=document.createElement('option');option.value=c;option.textContent=c;select.appendChild(option); }
  const officialLinks=(keys,dict)=>keys.map(k=>{const s=dict?.[k]; if(!s)return '';try{const u=new URL(s[1]);if(u.protocol!=='https:')return '';return `<li><a href="${esc(u.href)}" target="_blank" rel="noopener noreferrer">${esc(s[0])} ↗</a><span>${esc(s[2] || '시행일과 원문을 다시 확인하세요.')}</span></li>`}catch{return ''}}).join('');
  function draw(){
    const words=search.value.trim().toLocaleLowerCase('ko');
    const filtered=data.qa.filter(q=>(select.value==='all'||q.category===select.value)&&(!words||`${q.question} ${q.answer} ${q.category}`.toLocaleLowerCase('ko').includes(words)));
    list.innerHTML = filtered.map(q=>`<article class="question-card" id="q-${String(q.id).padStart(2,'0')}"><button class="question-button" type="button" aria-expanded="false" aria-controls="answer-${q.id}"><span class="number">Q${String(q.id).padStart(2,'0')}</span><span class="question-title"><small>${esc(q.category)}</small><strong>${esc(q.question)}</strong></span><span class="toggle" aria-hidden="true">+</span></button><div class="answer" id="answer-${q.id}" hidden><p>${esc(q.answer)}</p><h3>공식 자료 확인</h3><ul>${officialLinks(q.refs||[],data.sources?.law)}${officialLinks(q.cases||[],data.sources?.precedents)||''}</ul><p class="edu-note">해설은 교육 편집 초안입니다. 최신 시행일·관할 지자체 조례·적용대상을 확인하세요.</p><a class="share" href="#q-${String(q.id).padStart(2,'0')}">질문 링크 공유 · 주소 복사</a></div></article>`).join('') || '<p class="none">검색 결과가 없습니다. 다른 표현으로 검색해 주세요.</p>';
    for(const card of list.querySelectorAll('.question-card')){
      const button=card.querySelector('.question-button'),answer=card.querySelector('.answer');
      button.addEventListener('click',()=>{const expanded=button.getAttribute('aria-expanded')==='true';button.setAttribute('aria-expanded',String(!expanded));answer.hidden=expanded;card.classList.toggle('open',!expanded);card.querySelector('.toggle').textContent=expanded?'+':'−';});
      card.querySelector('.share').addEventListener('click', e=>{
        const link=location.origin+location.pathname+'#'+card.id;
        if(navigator.clipboard?.writeText)navigator.clipboard.writeText(link).catch(()=>{});
      });
    }
    const target=location.hash.replace('#','');if(target){const card=document.getElementById(target);if(card&&card.classList.contains('question-card')){card.querySelector('.question-button').click();}}
  }
  search.addEventListener('input',draw);select.addEventListener('change',draw);draw();
})();
