'use strict';
/* RE:LAND — original sixty lessons preserved; additive 2026-11-21 reader. */
(function(){
 const list=window.KANG_DATA&&window.KANG_DATA.lectures;
 const id=Number(new URLSearchParams(location.search).get('id'));
 const lesson=Array.isArray(list)&&list.find(x=>x.id===id);
 const meta=document.querySelector('.course-meta'),scene=document.querySelector('#episodeScene'),main=document.querySelector('.course-main');
 if(!lesson||!meta||!scene||!main)return;
 const $=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n};
 const link=(number,label)=>{const n=$('a','',label);n.href='/kang/lesson-v6.html?id='+number;n.target='_blank';n.rel='noopener noreferrer';return n};
 const tools=$('nav','rk-reader-tools');tools.setAttribute('aria-label','강의 탐색');
 const full=$('a','rk-reader-primary','전체 60강 목차');full.href='#rk-episode-index';tools.appendChild(full);
 if(id>1)tools.appendChild(link(id-1,'← 이전 강의'));
 if(id<60)tools.appendChild(link(id+1,'다음 강의 →'));
 const home=$('a','','전체 강의 홈');home.href='/kang/#allLessons';tools.appendChild(home);
 const panel=$('section','rk-reader-index');panel.id='rk-episode-index';
 const details=$('details');const summary=$('summary','','60강 목차에서 원하는 회차 선택하기');details.appendChild(summary);
 details.appendChild($('p','rk-reader-hint','제목·내용을 검색하거나 분야를 선택하세요. 회차 클릭 시 새 탭에서 열립니다.'));
 const controls=$('div','rk-reader-controls'),search=$('input'),cat=$('select');search.type='search';search.placeholder='분담금, 총회, 인가, 법원…';search.setAttribute('aria-label','강의 검색');
 cat.setAttribute('aria-label','분야별 필터');const opt=$('option','','모든 분야');opt.value='';cat.appendChild(opt);
 [...new Set(list.map(x=>x.category))].forEach(v=>{const o=$('option','',v);o.value=v;cat.appendChild(o)});
 controls.append(search,cat);details.appendChild(controls);
 const counter=$('p','rk-reader-count');counter.setAttribute('aria-live','polite');details.appendChild(counter);
 const rows=$('div','rk-reader-rows');rows.setAttribute('role','list');
 const anchors=[];
 list.slice().sort((a,b)=>a.id-b.id).forEach(v=>{
  const a=link(v.id,'');a.setAttribute('role','listitem');
  a.setAttribute('aria-label','제'+v.id+'강 '+v.title+' 새 탭 열기');
  if(v.id===id)a.setAttribute('aria-current','page');
  a.appendChild($('strong','',''+String(v.id).padStart(2,'0')+'강'));
  const label=$('span','',v.title),sub=$('small','',v.category);label.appendChild(sub);a.appendChild(label);
  rows.appendChild(a);anchors.push([v,a]);
 });
 details.appendChild(rows);const empty=$('p','rk-reader-hint','검색 결과가 없습니다.');empty.hidden=true;details.appendChild(empty);
 const filter=()=>{const q=search.value.trim().toLocaleLowerCase('ko'),c=cat.value;let count=0;
  anchors.forEach(([v,a])=>{const found=(!c||v.category===c)&&(!q||[v.title,v.summary,v.category,v.scenario,v.documents].join(' ').toLocaleLowerCase('ko').includes(q));a.hidden=!found;if(found)count++});
  counter.textContent='전체 '+list.length+'강 · '+count+'개 표시';empty.hidden=count!==0;
 };
 search.addEventListener('input',filter);cat.addEventListener('change',filter);filter();panel.appendChild(details);meta.after(tools,panel);
 full.addEventListener('click',()=>{details.open=true});document.querySelectorAll('[data-rk-open-index]').forEach(node=>node.addEventListener('click',()=>{details.open=true}));
 const aside=document.querySelector('.course-side .side-block');if(aside){const nav=$('a','','60강 회차 목차');nav.href='#rk-episode-index';nav.addEventListener('click',()=>details.open=true);aside.prepend(nav)}
 const dictionary={
 '추정분담금':'처음 계획을 세울 때 예상한 부담금입니다. 확정 청구금액은 아닙니다.',
 '확정분담금':'평가·설계·비용 등을 반영해 구체화한 부담액입니다. 이후 계획 변경이나 정산에 따라 달라질 수 있습니다.',
 '감정평가':'토지와 건물의 가치를 정해진 자료와 기준으로 살피는 것입니다.',
 '사업비':'정비사업을 진행하면서 드는 돈입니다. 공사비 외 금융비용 등도 살펴야 합니다.',
 '종전자산':'사업 전에 가지고 있던 토지·건물 등 평가 대상 자산입니다.',
 '권리가액':'종전자산의 평가와 사업 비례율 등을 반영한 권리 금액입니다.',
 '비례율':'전체 사업의 예상 수입·비용·종전자산 총액을 관계 지어 보는 비율입니다. 개인 수익률과는 다릅니다.',
 '조합':'법률상 요건에 따라 정비사업을 추진하는 조직입니다.',
 '총회':'조합원이 안건을 논의하고 의결하는 회의입니다.',
 '정족수':'회의나 의결에 필요하다고 정해진 인원 또는 의결권의 기준입니다.',
 '인가':'행정기관이 정해진 요건에 따라 계획이나 행위를 승인하는 처분을 뜻할 수 있습니다.',
 '고시':'기관이 정해진 내용을 공식적으로 알리는 것으로 날짜와 대상을 확인해야 합니다.',
 '정보공개':'법령에 따라 특정 자료의 열람·제공을 요구하는 절차입니다. 비공개 항목이 있을 수 있습니다.',
 '행정심판':'행정기관 처분에 대한 다툼을 행정심판기관에 제기하는 제도입니다.',
 '행정소송':'행정처분 등을 법원에서 다투는 재판 절차입니다.',
 '집행정지':'정해진 요건을 갖춘 경우 처분의 효력·집행 등을 잠시 정지하는 제도입니다.',
 '소장':'법원에 어떤 판단을 구하는지 이유와 함께 적어 내는 서류입니다.',
 '청구취지':'법원에 내려 달라고 요구하는 결론입니다.',
 '청구원인':'그러한 결론을 요구하는 사실 및 법률상 이유입니다.',
 '증거':'주장한 사실을 뒷받침하는 자료입니다. 출처와 원본이 중요합니다.',
 '고소':'고소권자가 수사기관에 범죄를 신고하고 처벌을 구하는 행위입니다.',
 '정비구역':'정비사업 시행을 위해 지정·고시한 구역입니다.',
 '사업시행계획':'어떤 범위와 조건으로 정비사업을 진행할지 정한 계획입니다.',
 '도면':'땅이나 건물 등의 구조·위치를 기호와 선으로 나타낸 그림입니다.',
 '관리처분계획':'분양과 권리 배분, 부담 등을 구체화하는 계획입니다.',
 '분양신청':'정해진 요건과 기한에 따라 주택 등의 공급을 신청하는 일입니다.',
 '보상':'법령이나 계약에 정해진 기준으로 손실 등을 보전하는 일입니다.',
 '이주비':'이주에 필요한 자금입니다. 대출이라면 나중에 상환해야 할 수 있습니다.',
 '합의서':'서로 합의한 내용을 기록한 문서입니다. 권한과 내용이 중요합니다.',
 '회의록':'회의에서 논의하거나 결정한 내용을 기록한 자료입니다. 계약서와 같지는 않습니다.'
 };
 const themes={
 '분담금·감정평가':['추정분담금','감정평가','사업비'],
 '조합 갈등·총회':['조합','총회','정족수'],
 '행정절차·정보공개':['고시','인가','정보공개'],
 '행정심판·불복':['행정심판','인가','증거'],
 '행정소송·인가취소':['행정소송','집행정지','인가'],
 '민사소송·소장 읽기':['소장','청구취지','청구원인'],
 '형사고소·사실 확인':['고소','증거','합의서'],
 '사업단계·도면 읽기':['정비구역','사업시행계획','도면'],
 '분양·관리처분':['관리처분계획','분양신청','권리가액'],
 '보상·이주·갈등관리':['보상','이주비','합의서']
 };
 let terms=Object.keys(dictionary).filter(t=>lesson.title.includes(t));
 (themes[lesson.category]||['고시','증거','도면']).forEach(t=>{if(!terms.includes(t))terms.push(t)});
 if(id===1)terms=['추정분담금','확정분담금','감정평가','사업비'];
 terms=terms.slice(0,5);
 const guide=$('section','rk-reader-guide');guide.id='rk-reader-guide';guide.appendChild($('span','rk-reader-overline','제'+id+'강 · 중학생도 이해하는 핵심 교재'));
 guide.appendChild($('h2','','오늘 무엇을 배우나요?'));
 guide.appendChild($('p','rk-reader-answer',id===1?'처음 안내받은 예상 금액과 다음 통지서 금액이 달라질 때, 날짜와 면적, 사업비를 비교하는 방법을 배웁니다.':lesson.summary));
 const three=$('div','rk-reader-triples');
 [['핵심 원리',lesson.summary],['생활 속 사례',lesson.scenario||'실제 확인할 자료를 생각해 봅니다.'],['찾아볼 문서',lesson.documents||'작성기관과 날짜가 있는 공식 문서']].forEach(v=>{const box=$('article');box.appendChild($('strong','',v[0]));box.appendChild($('p','',v[1]));three.appendChild(box)});
 guide.appendChild(three);guide.appendChild($('h3','','쉬운 용어 정리'));
 const cards=$('div','rk-reader-terms');terms.forEach(t=>{const card=$('article');card.appendChild($('strong','',t));card.appendChild($('p','',dictionary[t]));cards.appendChild(card)});guide.appendChild(cards);
 guide.appendChild($('p','rk-reader-warning','오해하지 마세요: '+(lesson.pitfall||'실제 판단은 공식 원문을 확인해야 합니다.')+' 개별 사건의 법률·투자 조언이 아닙니다.'));
 guide.appendChild($('h3','','읽고 확인하기'));
 const questions=$('ol','rk-reader-quiz');questions.id='rk-reader-quiz';
 (id===1?['예상 분담금이 그대로 최종 금액일까요?','서로 다른 통지서를 비교할 때 반드시 확인할 3가지는?','금액 차이만으로 위법이라고 할 수 있을까요?']:
 ['이번 강의에서 가장 중요한 개념은 무엇인가요?','예시 상황에서 어떤 자료를 먼저 확인하나요?','어떤 판단을 서둘러 단정하면 안 되나요?']).forEach(q=>questions.appendChild($('li','',q)));
 guide.appendChild(questions);scene.after(guide);
 const img=document.querySelector('#storySceneImage'),poster=window.KANG_MEDIA_V16&&window.KANG_MEDIA_V16.poster(id);
 if(img&&poster){img.removeAttribute('data-brand-hero');img.dataset.lessonMediaId=String(id);img.src=poster;img.alt='제'+id+'강 관련 가상 교육 삽화';
 const caption=document.querySelector('#storySceneCaption');if(caption)caption.textContent='제'+id+'강 주제별 교육 삽화 · 실제 사업장·당사자 사진이 아닙니다.'}
 const matches=terms.filter(t=>t.length>=2);
 const roots=document.querySelectorAll('#learning .serial-reading, #roadmap .serial-reading, #chapterList .chapter p');
 let marks=0;
 roots.forEach(root=>{const walk=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),nodes=[];
 while(walk.nextNode()){const n=walk.currentNode;if(n.parentElement&&!n.parentElement.closest('a,u,script,style,button')&&matches.some(t=>n.nodeValue.includes(t)))nodes.push(n)}
 nodes.forEach(n=>{if(marks>65)return;const v=n.nodeValue,part=document.createDocumentFragment();let start=0,changed=false;
 const hits=[];matches.forEach(t=>{let i=v.indexOf(t);while(i>=0){hits.push({i,t});i=v.indexOf(t,i+t.length)}});hits.sort((a,b)=>a.i-b.i||b.t.length-a.t.length);
 hits.forEach(h=>{if(h.i<start||marks>=65)return;part.appendChild(document.createTextNode(v.slice(start,h.i)));const u=$('u','rk-reader-keyword',h.t);u.title='오늘의 핵심 단어';part.appendChild(u);start=h.i+h.t.length;changed=true;marks++});
 if(changed){part.appendChild(document.createTextNode(v.slice(start)));n.replaceWith(part)}
 })});
 const end=$('nav','rk-reader-bottom');end.setAttribute('aria-label','연속 강의 보기');
 if(id>1)end.appendChild(link(id-1,'← 제'+(id-1)+'강 이전화'));else end.appendChild($('span','','첫 번째 강의'));
 if(id<60)end.appendChild(link(id+1,'제'+(id+1)+'강 다음화 →'));else end.appendChild($('span','','60강 마지막 회차'));
 main.appendChild(end);
})();
