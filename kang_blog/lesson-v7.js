'use strict';
/* Enriches all 60 existing RE:LAND lessons using their verified content data.
   Does not overwrite the 7 authored lesson pages, statutory citations or original images. */
(() => {
  const data=window.KANG_DATA;
  const id=Number(new URLSearchParams(location.search).get('id'));
  const item=data?.lectures?.find(x=>x.id===id);
  const container=document.querySelector('#lessonChapters');
  if(!item||!container)return;
  const e=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&quot;'}[c]));
  const byCategory={
   '분담금·감정평가':{steps:['평가 대상과 기준시점 식별','종전자산·권리가액 용어 구분','추정 사업비와 수입 가정 대조','관리처분 관련 변경 내역 확인'],questions:['서로 다른 분담금 수치의 기준일은 일치하는가?','평가대상과 분양면적이 동일한가?','증감분이 수입·비용·평가 중 어디에서 비롯됐는가?'],note:'산식과 비용 변동의 구조를 교육합니다. 개별 조합원의 확정 부담액을 계산하지 않습니다.'},
   '조합 갈등·총회':{steps:['정관 및 조합 규정 최신본 확인','소집통지·안건지 원본 수집','투표 방식·의결 기록 대조','관련 인가·공고·후속 처분 점검'],questions:['소집통지의 안건과 실제 의결사항은 같은가?','회의록에서 의결 주체와 내용이 확인되는가?','그 결의가 어느 후속 단계에 연결되는가?'],note:'결의의 유·무효를 임의 판단하지 않고 문서 간 차이와 쟁점을 학습합니다.'},
   '행정절차·정보공개':{steps:['정보 보유기관 확인','청구 자료와 목적 구분','공개·부분공개·비공개 사유 확인','결정 통지와 공식 근거 정리'],questions:['청구한 자료를 실제 보유한 기관은 어디인가?','비공개된 항목과 법적 근거는 무엇인가?','자료의 생성·변경 날짜를 구분했는가?'],note:'정보공개 범위와 개인정보 보호를 함께 고려하는 교육자료입니다.'},
   '행정심판·불복':{steps:['대상 행정행위·통지 확인','처분일·인지일 등 날짜 정리','불복 대상과 신청 취지 구분','공식 절차 및 증빙 비교'],questions:['어떤 처분을 대상으로 검토하는가?','통지문·처분서를 보유하고 있는가?','기한과 절차를 최신 원문에서 확인했는가?'],note:'심판 청구 가능성·기한은 개별 사안마다 달라질 수 있어 확정 답변을 하지 않습니다.'},
   '행정소송·인가취소':{steps:['인가 등 행정처분 식별','처분 전후 시간순 정리','소송 대상과 쟁점 분리','공식 판결·절차 원문 확인'],questions:['총회 결의와 행정처분의 법적 단계는 다른가?','어느 기관이 처분했고 고시일은 언제인가?','소송형태를 단정할 근거가 있는가?'],note:'원고 적격·제소기간·취소사유에 대한 사건별 판단은 제공하지 않습니다.'},
   '민사소송·소장 읽기':{steps:['청구 취지와 청구 원인 구분','주장 사실과 증거 자료 연결','상대방의 반대 자료 분류','소송 흐름과 서면 구조 학습'],questions:['청구가 요구하는 법률효과는 무엇인가?','사실 주장마다 근거 자료가 첨부됐는가?','확인되지 않은 추측이 사실처럼 서술됐는가?'],note:'소장·답변서를 대신 작성하거나 구체적 사건 대응전략을 제시하지 않습니다.'},
   '형사고소·사실 확인':{steps:['확인된 사실과 의혹 분리','날짜별 1차 증거·문서 확보','행위 주체·권한과 내용 구분','관련 법 조문과 반론 자료 학습'],questions:['직접 확인한 사실과 전언은 구분했는가?','해당 자료의 작성자·작성일을 확인했는가?','민사적 분쟁과 형사 범죄를 혼동하지 않는가?'],note:'범죄 성립·고소 가능성을 단정하거나 형사 문서를 대리 작성하지 않습니다.'},
   '사업단계·도면 읽기':{steps:['사업 유형과 정비구역 확인','고시·승인 단계 시간선 작성','도면 범례·축척·기준 확인','변경도와 최종 승인 원문 비교'],questions:['도면이 계획안·고시본·인가본 중 무엇인가?','사업구역과 건축대지 범위가 같은가?','승인 전후 변경사항을 구분했는가?'],note:'교육용 이미지·도식은 실제 인가도면이나 개별 사업지의 확정 계획이 아닙니다.'},
   '분양·관리처분':{steps:['분양 관련 공고 원문 확인','대상자·신청·시점 구분','관리처분계획의 항목 확인','통지와 인가 공고 비교'],questions:['분양 신청안내와 관리처분 인가 문서는 다른가?','면적·가격·권리 내용의 기준일을 확인했는가?','변경된 계획의 적용 범위는 무엇인가?'],note:'분양 자격·개별 권리·가격을 확정하거나 상담하는 자료가 아닙니다.'},
   '보상·이주·갈등관리':{steps:['보상 또는 이주 단계 확인','대상물·점유·등기 자료 구분','공고·통지와 협의 자료 대조','남은 이견과 공식 절차 정리'],questions:['보상 대상과 이주 대상은 동일한가?','어떤 공고·통지와 기준일이 적용되는가?','확인된 사실과 상대방의 주장을 분리했는가?'],note:'보상액 산정, 강제집행 여부, 분쟁 조정 등 개별 결론을 안내하지 않습니다.'}
  };
  const spec=byCategory[item.category]||byCategory['사업단계·도면 읽기'];
  const documents=String(item.documents||'원본 자료 및 법령').split(/[,，、]/).map(s=>s.trim()).filter(Boolean);
  const questionList=spec.questions.map((s,i)=>`<li><span>Q${i+1}</span>${e(s)}</li>`).join('');
  const steps=spec.steps.map((s,i)=>`<div class="deep-step"><span>${String(i+1).padStart(2,'0')}</span><strong>${e(s)}</strong></div>`).join('');
  const docRows=documents.map((s,i)=>`<tr><td><b>${e(s)}</b></td><td>작성기관·발행일·원본 URL</td><td>일치 / 차이 / 확인 필요</td></tr>`).join('');
  const html=`<section class="content-panel deep-module" id="topicDeepDive" aria-labelledby="deepTitle">
     <span class="chapter-eyebrow">03A / SUBJECT-BASED WORKSHOP · 제${id}강</span><h2 id="deepTitle">${e(item.category)}: ${e(item.title)}</h2>
     <p class="body-muted">이 단원은 기존 7단계 강의와 공식 출처를 보완하는 학습 도구입니다. 개인 사건의 판단을 대체하지 않습니다.</p>
     <div class="deep-summary"><div><span>핵심 설명</span><p>${e(item.summary)}</p></div><div><span>가상 실무 상황</span><p>${e(item.scenario||'공식 문서가 서로 다른 시점에 발행된 경우를 비교합니다.')}</p></div></div>
     <h3 class="deep-heading">학습 흐름도 · 문서를 읽는 네 단계</h3><div class="deep-flow" role="list">${steps}</div>
     <h3 class="deep-heading">원본 자료 대조 워크시트</h3><div class="deep-table-wrap"><table><thead><tr><th>검토할 문서</th><th>원본 확인</th><th>대조 결과 기록</th></tr></thead><tbody>${docRows}</tbody></table></div>
     <h3 class="deep-heading">실무 판단 전 스스로 묻는 질문</h3><ol class="deep-questions">${questionList}</ol>
     <div class="deep-caution"><strong>오해하기 쉬운 점</strong><p>${e(item.pitfall || '한 장의 문서만으로 법적 결론을 확정하지 않습니다.')}</p><small>${e(spec.note)}</small></div>
     <p class="deep-method">출처 표기 기준: 문서명 · 발행기관 · 발행일 · 공식 URL · 비교한 시점. 제공된 관련 법령 링크는 아래 원문 섹션에서 확인하세요.</p>
   </section>`;
  container.insertAdjacentHTML('afterend',html);
  const nav=document.querySelector('.course-side .side-block');
  if(nav){const link=document.createElement('a');link.href='#topicDeepDive';link.textContent='03A 분야별 실무 심화 학습';nav.querySelector('a[href="#worksheet"]')?.before(link);}
})();
